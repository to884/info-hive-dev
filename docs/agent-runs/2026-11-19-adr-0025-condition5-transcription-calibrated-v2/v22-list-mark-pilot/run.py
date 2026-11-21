"""本文の箇条書きの符号と図表の見本を区別する開発試験。"""

import argparse
from collections import Counter, defaultdict
from concurrent.futures import ThreadPoolExecutor
import importlib.util
import json
from pathlib import Path

HERE = Path(__file__).resolve().parent
PREVIOUS = HERE.parent / "v19-reference-audit/run.py"
spec = importlib.util.spec_from_file_location("formal_v19_snapshot", PREVIOUS)
audit = importlib.util.module_from_spec(spec)
spec.loader.exec_module(audit)
frame, trial, structured = audit.frame, audit.frame.trial, audit.SCHEMA_READER
load, sha, save_once, encoded = audit.load, audit.sha, audit.save_once, audit.encoded
OUT = audit.packets.old.CORPUS / "reference-v22-list-mark-pilot"
LOCK = HERE / "lock.json"
SAMPLES = {
    ("wp-summary-p0003", 3): "arrow", ("wp-summary-p0004", 4): "arrow",
    ("wp-summary-p0005", 3): "arrow", ("wp-summary-p0011", 5): "arrow",
    ("wp-summary-p0010", 5): "square", ("wp-summary-p0004", 8): "legend",
    ("wp-summary-p0006", 8): "regular",
}
GUIDE = (
    "紙面の箇条書きで複数の本文行と位置がそろう先頭の記号は、文字の一部として枠への所属を確認します。"
    "そうした文字として入る矢じり、四角、星などを落としません。例えば右向き矢じりの上側が白く、下側が黒い形は「➢」です。"
    "▲・■などの単純な形は、本文の箇条書きに使われる場合と、色で系列を示す凡例の見本である場合を周囲の紙面で区別します。"
    "図表の見本、線、装飾は字に置き換えません。例を枠に足さず、見える記号だけをその位置に一度記録します。"
)


def new_cards():
    labels = load(audit.LABELS / "public.json")
    rows = [r for r in labels if (r["key"], r["line_index"]) in SAMPLES]
    if len(rows) != len(SAMPLES) or any(r["effective"] is None for r in rows):
        raise ValueError("開発対象の全文を確かめられない")
    folder = OUT / "display"
    folder.mkdir(parents=True)
    manifest = folder / "selection.json"
    source_lock = folder / "grid.json"
    save_once(source_lock, encoded({"inputs": {}}))
    save_once(manifest, encoded({"selected": rows, "population_lock_sha256": sha(source_lock)}))
    audit.OUT, audit.LOCK = folder, source_lock
    audit.package(sha(manifest))
    pack = folder / "delivery/packages.json"
    deliveries = load(pack)
    tests, review = {}, {}
    for name, batch in deliveries["packs"].items():
        for ident, destination in batch["mapping"].items():
            row = rows[destination["entry"]]
            category = SAMPLES[row["key"], row["line_index"]]
            if row["allocation_axis"] != "x":
                raise ValueError("開発対象の軸が計画と異なる")
            deck = batch["request"]
            receive = next(l for l in deck["prompt"].splitlines() if l.startswith(ident + "。"))
            base = audit.packets.INTRO + "\n" + receive
            bound = deck["images"]
            names = [f for f in bound if f.startswith(ident + "-")]
            hashes = [h for f, h in zip(bound, deck["image_sha256"], strict=True) if f in names]
            key = f"case-{len(review):02d}"
            review[key] = {"entry": destination["entry"], "purpose": category, "partitions": destination["partitions"]}
            cards = folder / "delivery/cards" / name
            for arm, text in (("old", ""), ("new", GUIDE)):
                tests[f"{key}/{arm}"] = {"cards": str(cards), "request": {"images": names, "image_sha256": hashes,
                            "prompt": base + text + audit.packets.FORMAT + ident + "。", "ids": [ident]}}
    paths = (Path(__file__), HERE / "protocol.md", PREVIOUS, pack, manifest, audit.LABELS / "public.json")
    return {"cases": review, "tests": tests, "files": {str(p): sha(p) for p in paths}}


def collect(plan):
    rows = load(OUT / "display/selection.json")["selected"]
    sessions, counts, combined = set(), defaultdict(Counter), {}
    for n, task in plan["tests"].items():
        arm, variant = n.split("/")
        scenario = plan["cases"][arm]
        row = rows[scenario["entry"]]
        request_id, = task["request"]["ids"]
        answers = []
        for role, model in trial.MODELS.items():
            folder = OUT / "reads" / n / role
            process = load(folder / "process.json")
            raw = (folder / "response.jsonl").read_bytes()
            if process["response_sha256"] != trial.readers.sha(raw) or process["returncode"]:
                raise ValueError("開発の原票を受領できない")
            events = [json.loads(line, object_pairs_hook=trial.readers.json_pairs) for line in raw.splitlines() if line.strip()]
            last = (folder / "last-message.json").read_text(encoding="utf-8") if role == "gpt" else None
            token, value = frame.receipt.validated(events, role, model, last)
            if token in sessions:
                raise ValueError("旧・新の間で同じ会話を再利用")
            sessions.add(token)
            answer = trial.entries(value, [request_id])[request_id]
            answers.append(audit.ref.decoded(answer, scenario["partitions"]))
        aligned, coords = audit.ref.aligned(*answers, row["box"][2])
        expected = audit.ref.NORMALIZE(row["effective"])
        if aligned["status"] == "unreadable":
            result = "unresolved"
        elif coords:
            result = "requires-source"
        elif aligned["text"] == expected:
            result = "agree"
        elif aligned["text"] and expected in aligned["text"]:
            result = "extra"
        elif aligned["text"] in expected:
            result = "omitted"
        else:
            result = "different"
        counts[f"{variant}/{scenario['purpose']}"][result] += 1
        combined[n] = {"page": row["key"], "line_index": row["line_index"], "result": result}
    save_once(HERE / "result.json", encoded({"scope": "development-only", "lock_sha256": sha(LOCK),
                                           "counts": counts, "cases": combined}))
    print(dict(counts), flush=True)


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("action", choices=("prepare", "run"))
    p.add_argument("--sha256")
    p.add_argument("--codex", type=Path)
    p.add_argument("--claude", type=Path)
    args = p.parse_args()
    if args.action == "prepare":
        if LOCK.exists() or OUT.exists():
            raise FileExistsError("既定の開発比較は固定済み")
        save_once(LOCK, encoded(new_cards()))
        print(sha(LOCK), len(SAMPLES), "行、旧新各二票", flush=True)
        return
    if sha(LOCK) != args.sha256:
        raise ValueError("先に固定した開発比較と異なる")
    plan = load(LOCK)
    if any(sha(Path(n)) != h for n, h in plan["files"].items()):
        raise ValueError("開発比較の入力が変化")
    exe = {"gpt": args.codex.resolve(strict=True), "claude": args.claude.resolve(strict=True)}
    save_once(OUT / "started.json", encoded({"lock_sha256": args.sha256}))
    with ThreadPoolExecutor(max_workers=5) as worker:
        pending = [worker.submit(structured.read, role, model, exe[role], task["request"], Path(task["cards"]),
                                 OUT / "reads" / name / role)
                   for name, task in plan["tests"].items() for role, model in trial.MODELS.items()]
        for job in pending:
            job.result()
    collect(plan)


if __name__ == "__main__":
    main()
