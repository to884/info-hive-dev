"""監査の既知事例を再利用した開発用の画像二読。"""

import argparse
from concurrent.futures import ThreadPoolExecutor, as_completed
import hashlib
import importlib.util
import json
from pathlib import Path

from PIL import ImageFont

HERE = Path(__file__).resolve().parent
FIGURE = HERE.parent / "raster-figure-pilot/run.py"
spec = importlib.util.spec_from_file_location("figure", FIGURE)
figure = importlib.util.module_from_spec(spec)
spec.loader.exec_module(figure)
base, pilot, v2 = figure.base, figure.pilot, figure.v2
AUDIT = base.BENCH / "corpus/reference-audit-v9"
ROOT = base.BENCH / "results/reference-audit-v9-rootcause-2026-11-19.json"
OUT, LOCK = figure.OUT.parent / HERE.name, HERE / "lock.json"
CASES = ("M01", "M02", "U12")
GUIDE = (
    "最初から最後の字まで写し、よく似た括弧や記号が並ぶ場合は実際に見える一つずつを残してください。"
    "行に所属する独立した丸い印が1個見えるが、中点か丸印かを画像で区別できないときは、その1字の場所を ⟦round⟧ としてください。"
    "行所属の点線で、点の列は見えるが符号や字と字の境界を画像で区別できないときは、その点線だけを ⟦trail⟧ に換えてください。"
    "はっきり区別できる記号は見えるまま写してください。枠への所属か周囲の本文が分からなければ行全体を未決定にします。\n"
)


def material():
    start_file = AUDIT / "start.json"
    start, causes = base.load(start_file), base.load(ROOT)
    bad = {r["entry"] for r in causes["cases"]}
    issues = {r["case"]: r["entry"] for r in causes["cases"] if r["case"] in CASES}
    used, pictures, groups, lookup = set(), {}, {}, {}
    font_path = base.FONTS / "meiryo.ttc"
    font = ImageFont.truetype(font_path, size=17)
    v2.v1.REGION = AUDIT
    for offset, case in enumerate(CASES):
        issue_n = issues[case]
        entries = start["entries"]
        target = entries[issue_n]
        category = target["key"].rsplit("-p", 1)[0]
        options = [(i, r) for i, r in enumerate(entries) if i not in bad and i not in used
                   and r["key"].startswith(category + "-p") and r["allocation_axis"] == target["allocation_axis"]
                   and 150 <= r["box"][2] <= 350 and any(t["known"] for t in r["targets"].values())]
        if not options:
            raise ValueError("応答を見せない短い対照がない")
        control, _ = min(options, key=lambda item: hashlib.sha256(f"adr0025/{case}/{item[0]}".encode()).digest())
        used.add(control)
        name = f"pack-{offset:02d}"
        cards, subjects = {}, {}
        for pos, i in enumerate(sorted((issue_n, control), reverse=offset % 2 == 1), 1):
            row, ident = entries[i], f"G{pos:02d}"
            rendered, _ = v2.make_cards(row, start["files"], ident, font)
            cards.update(rendered)
            subjects[ident] = {"case": case if i == issue_n else "control", "entry": i}
        order = sorted(cards)
        groups[name] = {"images": order, "ids": list(subjects),
                        "image_sha256": [hashlib.sha256(cards[i]).hexdigest() for i in order],
                        "prompt": v2.v1.INTRO + v2.NOTICE + figure.old.shared + GUIDE + base.FORMAT + "、".join(subjects) + "\n"}
        lookup[name], pictures[name] = subjects, cards
    src = HERE.parent / "dot-layout-v2"
    paths = (Path(__file__), HERE / "protocol.md", FIGURE, ROOT, start_file, Path(pilot.__file__),
             Path(pilot.opus.__file__), Path(base.__file__), Path(v2.__file__), Path(v2.v1.__file__),
             src / "round-mark-source.json", src / "independent-pdf-commands-v2.json", font_path)
    return {"packs": groups, "rows": lookup, "inputs": {str(f): base.sha(f) for f in paths}, "models": pilot.MODELS}, pictures


def run(args, fixed, images):
    exe = {"sol": args.codex, "opus": args.claude}
    if any(e is None or not e.is_file() for e in exe.values()):
        raise ValueError("画像の二読に実行ファイルが必要")
    if base.load(LOCK) != fixed or base.sha(LOCK) != args.lock_sha256:
        raise ValueError("固定した配布が違う")
    if any((OUT / "cards" / n / i).read_bytes() != raw for n, group in images.items() for i, raw in group.items()):
        raise ValueError("配る固定画像を確認できない")
    destination = HERE / "result.json"
    with (OUT / "started.json").open("x", encoding="utf-8") as stream:
        json.dump({"lock_sha256": args.lock_sha256}, stream)
    pilot.OUT = OUT / "reads"
    ballots, receipts, sessions, problems = {}, [], set(), {}
    with ThreadPoolExecutor(max_workers=4) as threads:
        jobs = {}
        for name, pack in fixed["packs"].items():
            info = {"image_order_by_sheet": {"1": pack["images"]},
                    "image_sha256": dict(zip(pack["images"], pack["image_sha256"], strict=True))}
            rows = [{"id": i, "sheet": 1} for i in pack["ids"]]
            for role, command in exe.items():
                f = threads.submit(pilot.read, command.resolve(), role, name, pack, rows, OUT / "cards" / name, info)
                jobs[f] = name, role
        for pending in as_completed(jobs):
            label = jobs[pending]
            try:
                answer, receipt = pending.result()
                if receipt["session"] in sessions or receipt.get("attempt", 1) != 1:
                    raise ValueError("セッションの重複または技術再試行")
                sessions.add(receipt["session"])
                ballots[label] = answer
                receipts.append(receipt)
            except (RuntimeError, OSError, ValueError) as error:
                problems["/".join(label)] = type(error).__name__
    entries = base.load(AUDIT / "start.json")["entries"]
    public, private = {}, {}
    for name, r in fixed["rows"].items():
        public[name], private[name] = {}, {}
        for i, target in r.items():
            a, b = (ballots.get((name, reader), {}).get(i) for reader in exe)
            agreed = a is not None and a == b
            case = target["case"]
            if not agreed:
                outcome = "unknown" if a is None or b is None else "different"
            elif case == "M01":
                outcome = "two-visible-closing-parentheses" if "))" in a else "other-bracket"
            elif case == "M02":
                outcome = "same-round-position" if a.startswith("⟦round⟧") and a.count("⟦round⟧") == 1 else "no-leading-mark-certification"
            elif case == "U12":
                outcome = "same-trail-position" if a.count("⟦trail⟧") == 1 and not (a.startswith("⟦trail⟧") or a.endswith("⟦trail⟧")) else "no-trail-certification"
            else:
                previous = [base.normalize(z["text"]) for z in entries[target["entry"]]["targets"].values() if z["known"]]
                outcome = "matches-previous" if a in previous else "differs-from-previous"
            public[name][i] = {"case": case, "outcome": outcome}
            private[name][i] = {"sol": a, "opus": b}
    archive = OUT / "answers.json"
    base.write_json(archive, private)
    base.write_json(destination, {"scope": "development-only-prior-audit-diagnosis", "lock_sha256": args.lock_sha256,
                                  "results": public, "receipts": receipts, "failures": problems, "answers_sha256": base.sha(archive)})
    print(json.dumps(public, ensure_ascii=False), flush=True)


if __name__ == "__main__":
    cli = argparse.ArgumentParser(description=__doc__)
    cli.add_argument("action", choices=("prepare", "run"))
    cli.add_argument("--codex", type=Path)
    cli.add_argument("--claude", type=Path)
    cli.add_argument("--lock-sha256")
    args = cli.parse_args()
    manifest, cards = material()
    if args.action == "prepare":
        if OUT.exists() or LOCK.exists():
            raise FileExistsError("開発資料の固定は一度")
        for name, items in cards.items():
            dst = OUT / "cards" / name
            dst.mkdir(parents=True)
            for image, raw in items.items():
                (dst / image).write_bytes(raw)
        base.write_json(LOCK, manifest)
        print(base.sha(LOCK), {k: len(v) for k, v in cards.items()}, flush=True)
    else:
        run(args, manifest, cards)
