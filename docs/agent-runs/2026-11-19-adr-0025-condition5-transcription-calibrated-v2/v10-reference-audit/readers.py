"""独立した画像の監査票を、一回だけの呼び出しと原票から受領する。"""

import base64
import hashlib
import json
import os
from pathlib import Path
import subprocess
import tempfile


def sha(blob):
    return hashlib.sha256(blob).hexdigest()


def json_pairs(pairs):
    obj = dict(pairs)
    if len(obj) != len(pairs):
        raise ValueError("原票に重複したJSONのキー")
    return obj


def encoded(value):
    return (json.dumps(value, ensure_ascii=False, sort_keys=True) + "\n").encode("utf-8")


def parse(raw, family, model, ids):
    events = [json.loads(line, object_pairs_hook=json_pairs) for line in raw.decode("utf-8").splitlines() if line.strip()]
    if not all(isinstance(e, dict) for e in events):
        raise ValueError("監査のイベントがオブジェクトでない")
    if family == "gpt":
        sessions = [x["thread_id"] for x in events if x["type"] == "thread.started"]
        count = sum(x["type"] == "turn.completed" for x in events)
        if len(sessions) != 1 or count != 1:
            raise ValueError("GPTの一意のセッションと正常終了がない")
        for event in events:
            if event["type"].startswith("item.") and event["item"]["type"] not in {"agent_message", "reasoning"}:
                raise ValueError("画像以外のツール操作")
        messages = [e["item"]["text"] for e in events if e["type"] == "item.completed"
                    and e["item"]["type"] == "agent_message"]
        if len(messages) != 1:
            raise ValueError("一つの最終応答を特定できない")
        session, text = sessions[0], messages[0]
    else:
        init, = (e for e in events if e.get("type") == "system" and e.get("subtype") == "init")
        result, = (e for e in events if e.get("type") == "result")
        if (init.get("model") != model or init.get("tools") or result.get("is_error")
                or result.get("subtype") != "success" or init["session_id"] != result["session_id"]):
            raise ValueError("Claudeのモデル、独立した起動、正常終了が異なる")
        for event in events:
            message = event.get("message", {})
            if not isinstance(message, dict):
                raise ValueError("監査のメッセージがオブジェクトでない")
            content = message.get("content")
            if isinstance(content, list) and any(not isinstance(c, dict) or c.get("type") in ("tool_use", "tool_result") for c in content):
                raise ValueError("画像以外のツール操作")
        session, text = result["session_id"], result["result"]
    content = text.strip()
    if content.startswith("```json\n") and content.endswith("\n```"):
        content = content[8:-4]
    result = json.loads(content, object_pairs_hook=json_pairs)
    if set(result) != {"answers"} or not isinstance(result["answers"], list):
        raise ValueError("監査の票の形式が違う")
    answers = {}
    for row in result["answers"]:
        if not isinstance(row, dict) or set(row) != {"id", "status", "text"}:
            raise ValueError("監査の行の形式が違う")
        ident, status, text = (row[k] for k in ("id", "status", "text"))
        if (ident in answers or not isinstance(text, str)
                or not ((status == "unreadable" and text == "?") or (status == "empty" and text == "")
                        or (status == "readable" and text.strip() and "\n" not in text and "\r" not in text and text != "?"))):
            raise ValueError("重複した行か本文と状態が矛盾")
        answers[ident] = {"status": status, "text": text}
    if set(answers) != set(ids):
        raise ValueError("監査した行に過不足")
    return session, answers


def save_once(path, content):
    with path.open("xb") as stream:
        stream.write(content)


def request_payload(pack, folder, family):
    names, fingerprints, prompt = pack["images"], pack["image_sha256"], pack["prompt"]
    forms = [{"type": "text", "text": prompt}]
    for name, digest in zip(names, fingerprints, strict=True):
        if Path(name).name != name or not name.endswith(".png"):
            raise ValueError("配布対象は固定PNG")
        image = (folder / name).read_bytes()
        if sha(image) != digest:
            raise ValueError("配る画像が固定と異なる")
        if family == "claude":
            forms.append({"type": "image", "source": {"type": "base64", "media_type": "image/png",
                                                       "data": base64.b64encode(image).decode("ascii")}})
    if family == "gpt":
        return prompt.encode("utf-8")
    return encoded({"type": "user", "message": {"role": "user", "content": forms}, "parent_tool_use_id": None})


def command(exe, folder, names, model, family, cwd):
    if family == "gpt":
        return [str(exe), "exec", "--json", "--ephemeral", "--skip-git-repo-check",
                "--ignore-user-config", "--disable", "memories", "--disable", "plugins",
                "--disable", "shell_tool", "-c", 'web_search="disabled"', "-s", "read-only",
                "-c", 'approval_policy="never"', "-c", 'model_reasoning_effort="medium"',
                "-m", model, "-C", cwd, *(f"--image={folder / n}" for n in names), "-"]
    return [str(exe), "-p", "--model", model, "--effort", "medium", "--permission-mode", "auto",
            "--restricted", "--safe-mode", "--strict-mcp-config", "--disable-slash-commands", "--tools", "",
            "--no-session-persistence", "--verbose", "--input-format", "stream-json", "--output-format", "stream-json"]


def receive(directory, family, model, pack, cards, runtime):
    start, done, raw, err = (directory / n for n in ("start.json", "process.json", "response.jsonl", "stderr.txt"))
    if not done.exists() or not raw.exists() or not err.exists():
        return {"availability": "technical-unresolved"}
    launch, end, answer = json.loads(start.read_bytes()), json.loads(done.read_bytes()), raw.read_bytes()
    expected = request_payload(pack, cards, family)
    recorded = {"family": family, "model": model, "request_sha256": sha(expected), "images": pack["images"],
                "image_sha256": pack["image_sha256"], "ids": pack["ids"], "runtime": runtime,
                "cwd": launch["cwd"], "argv": command(runtime["path"], cards, pack["images"], model, family, launch["cwd"])}
    if launch != recorded or end["response_sha256"] != sha(answer) or end["stderr_sha256"] != sha(err.read_bytes()):
        raise ValueError("原票の配布または受領の結び付きが違う")
    if end["status"] != "success":
        return {"availability": "failed-technical", "process": end["status"], "response_sha256": sha(answer)}
    try:
        session, verdict = parse(answer, family, model, pack["ids"])
    except (AttributeError, TypeError, ValueError, KeyError, UnicodeError):
        return {"availability": "invalid-technical", "response_sha256": sha(answer)}
    return {"availability": "received", "session": session, "answers": verdict, "response_sha256": sha(answer)}


def read(runtime, family, model, pack, cards, directory):
    directory.mkdir(parents=True, exist_ok=True)
    started = directory / "start.json"
    payload = request_payload(pack, cards, family)
    if not started.exists():
        with tempfile.TemporaryDirectory(prefix="adr0025-independent-study-") as cwd:
            argv = command(runtime["path"], cards, pack["images"], model, family, cwd)
            state = {"family": family, "model": model, "request_sha256": sha(payload), "images": pack["images"],
                     "image_sha256": pack["image_sha256"], "ids": pack["ids"], "runtime": runtime, "cwd": cwd, "argv": argv}
            env = os.environ.copy()
            for key in ("CODEX_WINDOWS_REGISTERED_CORE", "CODEX_WINDOWS_SANDBOX_PACKAGE_FAMILY"):
                env.pop(key, None)
            save_once(started, encoded(state))
            try:
                p = subprocess.run(argv, input=payload, capture_output=True, cwd=cwd, env=env, timeout=720)
                raw, err = p.stdout, p.stderr
                status = "success" if p.returncode == 0 else f"exit-{p.returncode}"
            except subprocess.TimeoutExpired as error:
                raw, err, status = error.stdout or b"", error.stderr or b"", "timeout"
            except OSError:
                raw, err, status = b"", b"", "launch-failed"
            save_once(directory / "response.jsonl", raw)
            save_once(directory / "stderr.txt", err)
            save_once(directory / "process.json", encoded({"status": status, "response_sha256": sha(raw), "stderr_sha256": sha(err)}))
    result = receive(directory, family, model, pack, cards, runtime)
    print(directory.parent.name, family, result["availability"], flush=True)
    return result
