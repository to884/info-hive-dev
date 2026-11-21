"""固定画素を独立に読み、構造化された最終回答の受領を試す。"""

import argparse
from concurrent.futures import ThreadPoolExecutor
import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile

HERE = Path(__file__).resolve().parent
SCRIPTS = HERE.parent / "v10-reference-audit"
sys.path.insert(0, str(SCRIPTS))
import readers
from selection import CORPUS, load, sha

DEV = CORPUS / "reference-v13-layout-generalization"
OUT = CORPUS / "reference-v16-structured-readers-pilot"
MODELS = {"gpt": "gpt-6.2-sol", "claude": "claude-opus-5-5"}


def schema(ids):
    row = {"type": "object", "properties": {"id": {"type": "string", "enum": ids},
           "status": {"type": "string", "enum": ["readable", "unreadable", "empty"]}, "text": {"type": "string"}},
           "required": ["id", "status", "text"], "additionalProperties": False}
    return {"type": "object", "properties": {"answers": {"type": "array", "items": row}},
            "required": ["answers"], "additionalProperties": False}


def read(family, model, exe, request, cards, folder):
    folder.mkdir(parents=True, exist_ok=False)
    payload = readers.request_payload(request, cards, family)
    contract = readers.encoded(schema(request["ids"]))
    contract_file = folder / "schema.json"
    readers.save_once(contract_file, contract)
    env = os.environ.copy()
    for name in ("CODEX_WINDOWS_REGISTERED_CORE", "CODEX_WINDOWS_SANDBOX_PACKAGE_FAMILY"):
        env.pop(name, None)
    with tempfile.TemporaryDirectory(prefix="adr0025-structured-") as cwd:
        argv = readers.command(exe, cards, request["images"], model, family, cwd)
        last = folder / "last-message.json"
        if family == "gpt":
            argv[-1:-1] = ["--output-schema", str(contract_file), "--output-last-message", str(last)]
        else:
            argv.extend(["--json-schema", contract.decode("utf-8").strip()])
        readers.save_once(folder / "start.json", readers.encoded({"family": family, "model": model, "cwd": cwd,
            "packet_sha256": readers.sha(payload), "argv": argv, "executable_sha256": sha(exe),
            "image_sha256": request["image_sha256"], "schema_sha256": sha(contract_file)}))
        result = subprocess.run(argv, input=payload, capture_output=True, cwd=cwd, env=env, timeout=720)
    readers.save_once(folder / "response.jsonl", result.stdout)
    readers.save_once(folder / "stderr.txt", result.stderr)
    readers.save_once(folder / "process.json", readers.encoded({"returncode": result.returncode,
        "response_sha256": readers.sha(result.stdout), "stderr_sha256": readers.sha(result.stderr),
        "last_sha256": sha(last) if last.is_file() else None}))
    events = [json.loads(line, object_pairs_hook=readers.json_pairs) for line in result.stdout.splitlines() if line.strip()]
    observed = []
    if family == "gpt" and last.is_file():
        full = lambda e: e.get("item", {}).get("type") == "agent_message" and e.get("type") == "item.completed"
        final = [e["item"]["text"] for e in events if full(e)]
        if not final or final[-1].strip() != last.read_text(encoding="utf-8").strip():
            raise ValueError("終了時のJSONと最終応答のイベントが異なる")
        observed = [json.loads(final[-1], object_pairs_hook=readers.json_pairs)]
    elif family == "claude":
        observed = [e.get("structured_output") for e in events if e.get("type") == "result"]
    clean = bool(observed and all(isinstance(x, dict) and isinstance(x.get("answers"), list) for x in observed))
    return {"family": family, "returncode": result.returncode, "structured": clean,
            "events": [(e.get("type"), e.get("subtype") or e.get("item", {}).get("type")) for e in events],
            "status": [row["status"] for row in observed[0]["answers"]] if clean else []}


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--codex", type=Path, required=True)
    p.add_argument("--claude", type=Path, required=True)
    args = p.parse_args()
    lock = HERE.parent / "v13-layout-generalization/lock.json"
    if sha(lock) != "cf9821dbab5f3a9e1e6f9bcd3e17e7945ccc90a21bceb617d86f38d73890c69e":
        raise ValueError("以前の開発画像の固定が異なる")
    source = load(lock)["packs"]
    names = ("pack-08", "pack-13", "pack-16", "pack-17")
    OUT.mkdir()
    path = {"gpt": args.codex.resolve(strict=True), "claude": args.claude.resolve(strict=True)}
    with ThreadPoolExecutor(max_workers=3) as pool:
        results = []
        for name in names:
            for role, model in MODELS.items():
                results.append((name, pool.submit(read, role, model, path[role], source[name]["request"], DEV / "cards" / name,
                                                  OUT / name / role)))
        output = [{"pack": name, **task.result()} for name, task in results]
    readers.save_once(HERE / "result.json", readers.encoded({"scope": "development-only", "rows": output,
                                                              "code_sha256": sha(Path(__file__)), "images_job_sha256": sha(lock)}))
    print({role: sum(r["structured"] for r in output if r["family"] == role) for role in MODELS}, flush=True)


if __name__ == "__main__":
    main()
