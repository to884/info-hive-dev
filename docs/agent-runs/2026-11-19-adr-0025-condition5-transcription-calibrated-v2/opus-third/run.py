"""固定済みの初回票にOpusの第三票を合成し、Astraの結果と比較する。"""

import argparse
import base64
from concurrent.futures import ThreadPoolExecutor
import hashlib
import importlib.util
import json
from pathlib import Path
import subprocess
import tempfile

HERE = Path(__file__).resolve().parent
SOURCE_LOCK = "7c3758c6f929b62471de6816ca494505a5764bf17d3354d719203888acf13f9c"
spec = importlib.util.spec_from_file_location("visible", HERE.parent / "visible.py")
visible = importlib.util.module_from_spec(spec)
spec.loader.exec_module(visible)
trial, base, rep = visible.trial, visible.base, visible.rep
ARMS = ("old", "new")
MODEL = "claude-opus-5-5"
OUT = trial.ROOT / "opus-third"


def digest(data):
    return hashlib.sha256(data).hexdigest()


def original():
    lock, rows, directory = trial.check("comparison", SOURCE_LOCK)
    result_file = HERE.parent / "comparison-result.json"
    result = base.load(result_file)
    if result["lock_sha256"] != SOURCE_LOCK or len(rows) != 32:
        raise ValueError("前回の固定記録を参照できない")
    ids = [r["id"] for r in rows]
    raw_votes = {arm: {} for arm in ARMS}
    requests = {arm: {} for arm in ARMS}
    raw_hashes = {}
    for receipt in result["receipts"]:
        arm, read, model = (receipt[k] for k in ("arm", "read", "model"))
        prefix = f"{arm}-read{read}-{model}"
        raw = directory / f"{prefix}-{receipt['attempt']}.jsonl"
        req_file = directory / f"{prefix}-request.json"
        req = base.load(req_file)
        raw_hashes[raw.name] = base.sha(raw)
        raw_hashes[req_file.name] = base.sha(req_file)
        if (raw_hashes[raw.name] != receipt["response_sha256"]
                or digest(req["prompt"].encode("utf-8")) != receipt["prompt_sha256"]
                or [lock["image_sha256"][name] for name in req["images"]] != receipt["image_sha256"]
                or req["image_sha256"] != receipt["image_sha256"]
                or req["prompt"] != trial.prompt(arm, req["ids"])):
            raise ValueError("受領と固定入力が一致しない")
        session, _, answers = base.parse_response(raw.read_text(encoding="utf-8"), req["ids"])
        if session != receipt["session"] or (read < 3 and req["ids"] != ids):
            raise ValueError("受領のセッションまたは対象IDが一致しない")
        raw_votes[arm][read] = answers
        requests[arm][read] = req
    targets = base.load(directory / "third-selection.json")
    packs = {}
    for arm in ARMS:
        pending = [i for i in ids if base.consensus([raw_votes[arm][j][i] for j in (1, 2)]) is None]
        req = requests[arm][3]
        if pending != targets[arm] or pending != req["ids"]:
            raise ValueError("第三読の対象を再現できない")
        sheets = dict.fromkeys(str(r["sheet"]) for r in rows if r["id"] in pending)
        if req["images"] != [name for s in sheets for name in lock["image_order_by_sheet"][s]]:
            raise ValueError("第三読に渡された画像の順序が異なる")
        packs[arm] = {key: req[key] for key in ("ids", "images", "image_sha256")}
        packs[arm]["prompt_sha256"] = digest(req["prompt"].encode("utf-8"))
    return rows, directory, result, raw_votes, requests, {
        "comparison_lock_sha256": SOURCE_LOCK, "comparison_result_sha256": base.sha(result_file),
        "original_input_sha256": raw_hashes, "script_sha256": base.sha(Path(__file__)),
        "model": MODEL, "effort": "medium", "packs": packs,
    }


def prepare():
    *_, fixed = original()
    fixed["fixed_at"] = base.utc_now()
    base.write_json(HERE / "lock.json", fixed)
    print("固定", base.sha(HERE / "lock.json"),
          {a: len(p["ids"]) for a, p in fixed["packs"].items()}, flush=True)


def parse(raw, ids):
    events = [json.loads(line) for line in raw.splitlines() if line.strip()]
    inits = [e for e in events if e.get("type") == "system" and e.get("subtype") == "init"]
    results = [e for e in events if e.get("type") == "result"]
    if len(results) != 1 or results[0].get("is_error") or results[0].get("subtype") != "success":
        message = results[0].get("result", results[0].get("errors", "")) if results else ""
        raise ValueError(f"Opusの応答が正常終了していない: {str(message)[:500]}")
    if len(inits) != 1 or inits[0].get("model") != MODEL or inits[0].get("tools"):
        raise ValueError("Opusのモデルまたは利用可能なツールが固定と異なる")
    for event in events:
        content = event.get("message", {}).get("content", [])
        if isinstance(content, list) and any(c.get("type") in ("tool_use", "tool_result") for c in content):
            raise ValueError("画像の転記以外のツール操作を検出")
    result = results[0]
    if result["session_id"] != inits[0]["session_id"]:
        raise ValueError("セッションが一致しない")
    value = result["result"].strip()
    if value.startswith("```json\n") and value.endswith("\n```"):
        value = value.removeprefix("```json\n").removesuffix("\n```")
    obj = json.loads(value)
    if set(obj) != {"answers"} or not isinstance(obj["answers"], list):
        raise ValueError("回答形式が違う")
    answers = {}
    for row in obj["answers"]:
        if set(row) != {"id", "status", "text"} or not isinstance(row["text"], str):
            raise ValueError("1行の回答形式が違う")
        row_id, status, text = row["id"], row["status"], row["text"]
        if row_id in answers or not ((status == "unreadable" and text == "?")
                                     or (status == "empty" and text == "")
                                     or (status == "readable" and base.normalize(text) and "\n" not in text)):
            raise ValueError("重複または本文と状態の不整合")
        answers[row_id] = None if status == "unreadable" else base.normalize(text)
    if set(answers) != set(ids):
        raise ValueError("対象IDの抜けまたは対象外を検出")
    return answers, result


def read_opus(exe, arm, request, directory):
    cmd = [str(exe), "-p", "--model", MODEL, "--effort", "medium", "--permission-mode", "auto",
           "--restricted", "--strict-mcp-config", "--disable-slash-commands", "--tools", "",
           "--no-session-persistence", "--verbose", "--input-format", "stream-json",
           "--output-format", "stream-json"]
    items = [{"type": "text", "text": request["prompt"]}]
    for name, expected in zip(request["images"], request["image_sha256"], strict=True):
        data = (directory / name).read_bytes()
        if digest(data) != expected:
            raise ValueError("送信する画像のSHAが異なる")
        items.append({"type": "image", "source": {
            "type": "base64", "media_type": "image/png", "data": base64.b64encode(data).decode("ascii")}})
    message = {"type": "user", "message": {"role": "user", "content": items},
               "parent_tool_use_id": None}
    stdin = (json.dumps(message, ensure_ascii=False) + "\n").encode("utf-8")
    with tempfile.TemporaryDirectory(prefix="opus-vision-") as cwd:
        started = base.utc_now()
        proc = subprocess.run(cmd, input=stdin, capture_output=True, cwd=cwd, timeout=600)
    path = OUT / f"{arm}-response.jsonl"
    path.write_bytes(proc.stdout)
    (OUT / f"{arm}-stderr.txt").write_bytes(proc.stderr)
    try:
        answers, result = parse(proc.stdout.decode("utf-8"), request["ids"])
    except (ValueError, KeyError, TypeError, UnicodeDecodeError) as error:
        raise RuntimeError(f"{arm} Opus応答を採用できない。終了コード={proc.returncode}。{error}") from error
    if proc.returncode:
        raise RuntimeError(f"{arm} Opus CLIの終了コード={proc.returncode}")
    base.write_json(OUT / f"{arm}-answers.json", answers)
    receipt = {
        "arm": arm, "model": MODEL, "session": result["session_id"], "started": started,
        "finished": base.utc_now(), "rows": len(answers),
        "unreadable": sum(a is None for a in answers.values()),
        "input_message_sha256": digest(stdin), "images": request["images"],
        "image_sha256": request["image_sha256"],
        "prompt_sha256": digest(request["prompt"].encode("utf-8")),
        "response_sha256": base.sha(path),
    }
    base.write_json(OUT / f"{arm}-receipt.json", receipt)
    print(arm, "受領", len(answers), "判読不能", receipt["unreadable"], flush=True)
    return answers, receipt


def fold(ids, prior, third):
    return {i: base.consensus([prior[1][i], prior[2][i], third.get(i)]) for i in ids}


def run(exe, expected):
    lock_path = HERE / "lock.json"
    if base.sha(lock_path) != expected:
        raise ValueError("指定された固定SHAと異なる")
    L = base.load(lock_path)
    rows, directory, baseline, votes, requests, fixed = original()
    if {k: v for k, v in L.items() if k != "fixed_at"} != fixed:
        raise ValueError("固定後に画像、初回票または指示が変化")
    OUT.mkdir(parents=True)
    with ThreadPoolExecutor(max_workers=2) as pool:
        jobs = {a: pool.submit(read_opus, exe, a, requests[a][3], directory) for a in ARMS}
        returned = {a: jobs[a].result() for a in ARMS}
    if original()[-1] != fixed or base.sha(lock_path) != expected:
        raise ValueError("読みの前後で固定記録が変化")
    receipts = [returned[a][1] for a in ARMS]
    sessions = {r["session"] for r in receipts}
    if len(sessions) != 2 or sessions & {r["session"] for r in baseline["receipts"]}:
        raise ValueError("読取セッションが重複")
    ids = [r["id"] for r in rows]
    base.metrics = rep.metrics
    astra = {a: fold(ids, votes[a], votes[a][3]) for a in ARMS}
    opus = {a: fold(ids, votes[a], returned[a][0]) for a in ARMS}
    previous = base.paired(rows, astra["old"], astra["new"])
    if any(previous[k] != baseline[k] for k in ("all", "joint_known", "transitions")):
        raise ValueError("前回のAstra結果が原票から再現しない")
    result = {
        "finished": base.utc_now(), "lock_sha256": expected, "receipts": receipts,
        "astra_third_old_vs_new": previous,
        "opus_third_old_vs_new": base.paired(rows, opus["old"], opus["new"]),
        "by_arm": {a: base.paired(rows, astra[a], opus[a]) for a in ARMS},
        "raw_opus_votes": {
            a: {
                "targets": len(returned[a][0]),
                "both_initial_unreadable": sum(votes[a][1][i] is None and votes[a][2][i] is None
                                               for i in returned[a][0]),
                "agree_known_sol": sum(v is not None and v == votes[a][1][i] for i, v in returned[a][0].items()),
                "agree_known_astra": sum(v is not None and v == votes[a][2][i] for i, v in returned[a][0].items()),
                "unreadable": receipts[j]["unreadable"],
            } for j, a in enumerate(ARMS)
        },
        "row_outcomes": [
            {"id": r["id"], "case": r["case"],
             **{a: {"astra": rep.metrics([r], astra[a]), "opus": rep.metrics([r], opus[a])}
                for a in ARMS}} for r in rows
        ],
    }
    base.write_json(HERE / "result.json", result)
    print(json.dumps({k: result[k] for k in ("opus_third_old_vs_new", "raw_opus_votes")}, ensure_ascii=False))


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("action", choices=("prepare", "run"))
    parser.add_argument("--claude", type=Path)
    parser.add_argument("--lock-sha256")
    args = parser.parse_args()
    if args.action == "prepare":
        prepare()
    else:
        run(args.claude.resolve(), args.lock_sha256)
