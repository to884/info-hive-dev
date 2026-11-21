"""図表の拡大試験を通過後、未読29行すべてに同じ方法を適用する。"""

import argparse
from collections import Counter
from concurrent.futures import ThreadPoolExecutor, as_completed
import hashlib
import importlib.util
import json
from pathlib import Path

from PIL import ImageFont

HERE = Path(__file__).resolve().parent
PILOT = HERE.parent / "raster-figure-pilot/run.py"
spec = importlib.util.spec_from_file_location("figure_pilot", PILOT)
old = importlib.util.module_from_spec(spec)
spec.loader.exec_module(old)
base, pilot = old.base, old.pilot
REGION, OUT = old.REGION, old.OUT.parent / HERE.name
LOCK = HERE / "lock.json"


def add_pack(packs, cards, buffer, targets):
    name = f"pack-{len(packs):02d}"
    images = sorted(k for k in buffer if "-focus-" not in k) + sorted(k for k in buffer if "-focus-" in k)
    ids = list(targets)
    packs[name] = {"request": {"images": images, "ids": ids,
                               "image_sha256": [hashlib.sha256(buffer[k]).hexdigest() for k in images],
                               "prompt": old.v2.v1.INTRO + old.v2.NOTICE + old.old.shared + old.GUIDE
                               + base.FORMAT + "、".join(ids) + "\n"}, "targets": targets}
    cards[name] = buffer


def material():
    initial, items, _ = old.material()
    old_lock, old_result = old.LOCK, PILOT.parent / "result.json"
    completed = base.load(old_result)
    if (initial != base.load(old_lock) or completed["lock_sha256"] != base.sha(old_lock) or not completed["advance"]
            or completed["counts"]["unreadable"].get("new-agreement", 0) < 6
            or completed["counts"]["readable"].get("differs-from-control", 0)):
        raise ValueError("先行試験の継続条件を確認できない")
    previous = {r["line_index"] for group in items.values() for r in group.values()}
    start_path, final_path = REGION / "start.json", REGION / "final.json"
    start, final = base.load(start_path), base.load(final_path)
    if final["start_sha256"] != base.sha(start_path):
        raise ValueError("固定画像の記録と異なる")
    pool = [r for r in final["rows"] if r["key"] == old.PAGE and r["status"] == "unreadable"
            and r["line_index"] not in previous and 138 <= r["box"][0] < 1102 and 209 <= r["box"][1] < 929]
    if len(pool) != 29 or any(r["allocation_axis"] != "x" for r in pool):
        raise ValueError("対象の未読29行が異なる")
    entries = {r["line_index"]: r for r in start["entries"] if r["key"] == old.PAGE}
    font_file = base.FONTS / "meiryo.ttc"
    font = ImageFont.truetype(font_file, size=17)
    packs, cards, buffer, targets = {}, {}, {}, {}
    for r in sorted(pool, key=lambda v: v["line_index"]):
        i = r["line_index"]
        entry = entries[i]
        ident = f"Z{len(targets) + 1:02d}"
        regular, _ = old.v2.make_cards(entry, start["assets"], ident, font)
        expanded, _ = old.detailed(entry, ident, start["assets"], font)
        shown = regular | expanded
        if len(shown) > 24:
            raise ValueError("1行の添付が24枚を超える")
        if targets and (len(targets) == 4 or len(buffer) + len(shown) > 24):
            add_pack(packs, cards, buffer, targets)
            buffer, targets = {}, {}
            ident = "Z01"
            regular, _ = old.v2.make_cards(entry, start["assets"], ident, font)
            expanded, _ = old.detailed(entry, ident, start["assets"], font)
            shown = regular | expanded
        buffer.update(shown)
        targets[ident] = i
    if targets:
        add_pack(packs, cards, buffer, targets)
    files = (Path(__file__), HERE / "protocol.md", PILOT, old_lock, old_result, start_path, final_path,
             Path(old.v2.__file__), Path(base.__file__), Path(pilot.opus.__file__), font_file)
    return {"packs": packs, "models": pilot.MODELS, "inputs": {p.parent.name + "/" + p.name: base.sha(p) for p in files}}, cards


def run(args, manifest, cards):
    if base.sha(LOCK) != args.lock_sha256 or base.load(LOCK) != manifest:
        raise ValueError("事前固定を再現できない")
    for name, images in cards.items():
        if any((OUT / "cards" / name / label).read_bytes() != v for label, v in images.items()):
            raise ValueError("固定画像が違う")
    with (OUT / "started.json").open("x", encoding="utf-8") as file:
        json.dump({"lock_sha256": args.lock_sha256, "started": base.utc_now()}, file)
    pilot.OUT = OUT / "reads"
    sessions, counts, receipts, outcomes = set(), Counter(), [], {}
    paths = {"sol": args.codex.resolve(), "opus": args.claude.resolve()}
    with ThreadPoolExecutor(max_workers=4) as threads:
        work = {}
        for name, data in manifest["packs"].items():
            pack = data["request"]
            info = {"image_order_by_sheet": {"1": pack["images"]},
                    "image_sha256": dict(zip(pack["images"], pack["image_sha256"], strict=True))}
            rows = [{"id": i, "sheet": 1} for i in pack["ids"]]
            for role, exe in paths.items():
                work[threads.submit(pilot.read, exe, role, name, pack, rows, OUT / "cards" / name, info)] = (name, role)
        votes, failures = {}, {}
        for task in as_completed(work):
            name, role = work[task]
            try:
                ballots, receipt = task.result()
            except (RuntimeError, OSError) as e:
                failures[f"{name}/{role}"] = type(e).__name__
                continue
            if receipt["session"] in sessions:
                raise ValueError("同じセッションを検出")
            sessions.add(receipt["session"])
            receipts.append(receipt)
            if receipt.get("attempt", 1) != 1:
                failures[f"{name}/{role}"] = "extra-technical-attempt"
            else:
                votes[name, role] = ballots
        private = []
        for name, pack in manifest["packs"].items():
            findings = {}
            for ident, index in pack["targets"].items():
                if any((name, role) not in votes for role in paths):
                    status, value = "technical-unresolved", None
                else:
                    a, b = (votes[name, role][ident] for role in paths)
                    value = a if a and a == b else None
                    if value is not None:
                        status = "new-agreement"
                    elif a is None or b is None:
                        status = "both-unknown" if a is b else "one-unknown"
                    else:
                        status = "disagreement" if a != b else "agreed-empty"
                findings[ident] = status
                private.append({"key": old.PAGE, "line_index": index, "normalized_text": value, "status": status})
                counts[status] += 1
            outcomes[name] = findings
    if material()[0] != manifest or sum(counts.values()) != 29:
        raise ValueError("固定前と終了後で対象が変化")
    private_file = OUT / "candidate-lines.json"
    base.write_json(private_file, private)
    base.write_json(HERE / "result.json", {"scope": "development-only", "lock_sha256": args.lock_sha256,
                                          "outcomes": outcomes, "counts": counts, "receipts": receipts,
                                          "failures": failures, "private_lines_sha256": base.sha(private_file)})
    print(json.dumps(dict(counts), ensure_ascii=False), flush=True)


if __name__ == "__main__":
    cli = argparse.ArgumentParser(description=__doc__)
    cli.add_argument("action", choices=("prepare", "run"))
    cli.add_argument("--codex", type=Path)
    cli.add_argument("--claude", type=Path)
    cli.add_argument("--lock-sha256")
    argv = cli.parse_args()
    manifest, cards = material()
    if argv.action == "prepare":
        if LOCK.exists() or OUT.exists():
            raise FileExistsError("事前固定済み")
        for name, items in cards.items():
            place = OUT / "cards" / name
            place.mkdir(parents=True)
            for image, raw in items.items():
                (place / image).write_bytes(raw)
        base.write_json(LOCK, manifest)
        print(base.sha(LOCK), len(manifest["packs"]), "束", flush=True)
    else:
        run(argv, manifest, cards)
