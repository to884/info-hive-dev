"""開発用の既存結果について、候補選択につながる再試行がなかったことを検査する。"""

import base64
from collections import Counter
import hashlib
import inspect
import json
from pathlib import Path

from verify_and_score import CORPUS, HERE, confirmed, expansion, load, position, score, sha


def strict_pairs(items):
    result = dict(items)
    if len(result) != len(items):
        raise ValueError("JSONに重複したキー")
    return result


def response_object(raw, role):
    events = [json.loads(line, object_pairs_hook=strict_pairs) for line in raw.splitlines() if line.strip()]
    if role == "sol":
        message = [event["item"]["text"] for event in events
                   if event["type"] == "item.completed" and event["item"]["type"] == "agent_message"][-1]
    else:
        message, = (event["result"] for event in events if event["type"] == "result")
    body = message.strip()
    if body.startswith("```json\n") and body.endswith("\n```"):
        body = body[8:-4]
    return json.loads(body, object_pairs_hook=strict_pairs)


def check_files(root, receipt, pack, card_path, inventory):
    arm, role, model = (receipt[k] for k in ("arm", "role", "model"))
    path = root / "reads" / role / arm
    files = {d.name: sha(d) for d in path.iterdir() if d.is_file()}
    if any(not d.is_file() for d in path.iterdir()):
        raise ValueError("原票のディレクトリに未記録の項目")
    if role == "sol":
        prefix = f"{arm}-read1-{model}"
        raw_name = f"{prefix}-1.jsonl"
        request_name = f"{prefix}-request.json"
        expected = {raw_name, f"{prefix}-1.stderr", f"{prefix}-answers.json", f"{prefix}-receipt.json", request_name,
                    *pack["images"]}
        if set(files) != expected or receipt["attempt"] != 1 or receipt["failures"]:
            raise ValueError("Solが一度だけ読んだことを確認できない")
        request = load(path / request_name)
        if (request["model"] != model or any(request[k] != pack[k] for k in ("images", "ids", "image_sha256", "prompt"))
                or [files[name] for name in pack["images"]] != pack["image_sha256"]):
            raise ValueError("Solに送付した画像・指示が固定と異なる")
    else:
        raw_name = f"{arm}-response.jsonl"
        if set(files) != {raw_name, f"{arm}-stderr.txt", f"{arm}-answers.json", f"{arm}-receipt.json"}:
            raise ValueError("Opusが一度だけ読んだことを確認できない")
        content = [{"type": "text", "text": pack["prompt"]}]
        for name in pack["images"]:
            data = (card_path / name).read_bytes()
            content.append({"type": "image", "source": {
                "type": "base64", "media_type": "image/png", "data": base64.b64encode(data).decode("ascii")}})
        message = {"type": "user", "message": {"role": "user", "content": content}, "parent_tool_use_id": None}
        wire = (json.dumps(message, ensure_ascii=False) + "\n").encode()
        if hashlib.sha256(wire).hexdigest() != receipt["input_message_sha256"]:
            raise ValueError("Opusが受け取った文と添付の再現が違う")
    raw = path / raw_name
    answer = response_object(raw.read_text(encoding="utf-8"), role)
    if files[raw_name] != receipt["response_sha256"] or {r["id"] for r in answer["answers"]} != set(pack["ids"]):
        raise ValueError("原票の照合に失敗")
    inventory.update({(path / name).relative_to(CORPUS).as_posix(): digest for name, digest in files.items()})


def check_group(root, manifest, receipts, files):
    counts = Counter()
    for name, pack in manifest["packs"].items():
        for role in ("sol", "opus"):
            receipt = receipts[name, role]
            check_files(root, receipt, pack, root / "cards" / name, files)
            counts[role] += 1
    if set(receipts) != {(n, r) for n in manifest["packs"] for r in ("sol", "opus")}:
        raise ValueError("同じ段階の別の票が残っている")
    return dict(counts)


def main():
    archive = expansion.OUT.parent / "source-position-verified-development" / "first-attempt-files.json"
    output = HERE / "first-attempt-review-evidence.json"
    if archive.exists() or output.exists():
        raise FileExistsError("既存の追加証跡を上書きしない")
    files, counts = {}, {}
    for run in (position, confirmed, expansion):
        stage = run.HERE.name
        manifest = load(run.HERE / "lock.json")
        if run is expansion:
            root = run.OUT
            attempts = root / "receipts"
            receipts = {}
            for name in manifest["packs"]:
                for role in ("sol", "opus"):
                    directory = attempts / name / role
                    if {p.name for p in directory.iterdir()} != {"attempt-1-started.json", "attempt-1.json"}:
                        raise ValueError("第一試行以外または欠落した試行")
                    received = load(directory / "attempt-1.json")
                    launch = load(directory / "attempt-1-started.json")
                    if received["status"] != "received" or received["receipt"]["arm"] != name + "-a1" or launch["arm"] != name + "-a1":
                        raise ValueError("第一試行の起動、応答、受領が異なる")
                    receipts[name, role] = received["receipt"]
                    for path in directory.iterdir():
                        files[path.relative_to(CORPUS).as_posix()] = sha(path)
            for role in ("sol", "opus"):
                if {p.name for p in (root / "reads" / role).iterdir()} != {name + "-a1" for name in manifest["packs"]}:
                    raise ValueError("第一試行以外のディレクトリを検出")
        else:
            receipts = {(e["arm"], e["role"]): e for e in load(run.HERE / "result.json")["receipts"]}
        counts[stage] = check_group(run.OUT, manifest, receipts, files)
    paths = (Path(__file__), HERE / "verify_and_score.py", Path(expansion.base.__file__),
             Path(expansion.pilot.opus.__file__), Path(score.__file__), Path(score.training.__file__),
             Path(score.frozen.score_v4.__file__), Path(inspect.getfile(score.audit.normalize)))
    code = {p.relative_to(CORPUS.parents[3]).as_posix(): sha(p) for p in paths}
    with archive.open("x", encoding="utf-8") as stream:
        json.dump(files, stream, indent=2, sort_keys=True)
    with output.open("x", encoding="utf-8") as stream:
        json.dump({"scope": "development-only-preserved-original-first-attempts",
                   "first_attempts": counts, "archived_files": len(files), "archive_sha256": sha(archive),
                   "code": code}, stream, indent=2)
    print(json.dumps(counts, ensure_ascii=False), flush=True)


if __name__ == "__main__":
    main()
