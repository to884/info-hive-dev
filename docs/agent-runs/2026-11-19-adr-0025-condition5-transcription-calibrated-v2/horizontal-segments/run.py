"""行の幅が大きい画像を区画化し、二系統が同じ全文に到達できるか調べる。"""

import argparse
from collections import Counter
from concurrent.futures import ThreadPoolExecutor, as_completed
import hashlib
import importlib.util
import io
import json
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont

HERE = Path(__file__).resolve().parent
V3 = HERE.parent / "actual-geometry-pilot-v3/run.py"
spec = importlib.util.spec_from_file_location("actual_v3", V3)
v3 = importlib.util.module_from_spec(spec)
spec.loader.exec_module(v3)
v2 = v3.v2
v1, base, pilot = v2.v1, v2.base, v2.pilot
OUT = v3.new_out.parent / HERE.name
ASSETS = OUT / "cards"
LOCK = HERE / "lock.json"
ARMS = ("whole", "segments")
SHARED = (
    "対象は左から右へ読む一つの横行です。元の箱内でその条件を確認できなければ未決定としてください。"
    "各カードの青い目印は区画の左端と右端の位置を示します。元の赤枠と所属の規則はそのままです。\n"
)
TREATMENTS = {
    "whole": "区画の青い目印は行全体の転記には使いません。カード間の重なりで同じ字を二度書かず、行IDごとに一つの回答を返してください。\n",
    "segments": (
        "行全体の赤枠に所属する字を選んでから、その字全体の横方向のインクの中心で区画を1つだけ決めてください。"
        "左と右の青い目印の間の字をその区画のIDに答えてください。内部境界ちょうどなら右側、行の右端ちょうどなら最終区画です。"
        "各区画はその区画だけの文字を答え、別の区画の文を補わないでください。\n"
    ),
}


def marked_cards(entry, index, ident, font):
    blobs, sources = v2.make_cards(entry, index, ident, font)
    width, height = [3 * n for n in entry["box"][2:]]
    windows = v2.segments(width)
    if entry["allocation_axis"] != "x" or len(windows) < 2 or height > v2.SPAN:
        raise ValueError("横1列の区画にできない")
    cuts = [0] + [(right + following) // 2 for (_, right), (following, _) in zip(windows, windows[1:])] + [width]
    cards = {}
    for index, (name, raw) in enumerate(blobs.items()):
        low, high = v2.source_views(entry)
        guides = []
        with Image.open(io.BytesIO(raw)) as opened:
            card = opened.copy()
        draw = ImageDraw.Draw(card)
        w, h = card.width // 2, (card.height - 27) // 2
        for tile, part in enumerate(sources[name]):
            view = (low, high)[tile // 2]
            left, _, right, _ = view["target_rectangle"]
            tile_left, y = (tile % 2) * w, 27 + (tile // 2) * h
            rectangle = part["rectangle"]
            marks = []
            for cut in cuts[index:index+2]:
                x = round(left + (right - left) * cut / width) - rectangle[0]
                if not 0 <= x < rectangle[2] - rectangle[0]:
                    raise ValueError("区画境界がカードの外にある")
                draw.line((tile_left + x, y + 18, tile_left + x, y + 22), fill="#0052d4", width=2)
                marks.append(x)
            guides.append(marks)
        out = io.BytesIO()
        card.save(out, format="PNG")
        cards[name] = out.getvalue()
        sources[name] = {"tiles": sources[name], "guides": guides, "fixed_display_range": cuts[index:index+2]}
    return cards, sources


def material():
    stage = base.load(V3.parent / "lock.json")
    start = base.load(v1.REGION / "start.json")
    final = base.load(v1.REGION / "final.json")
    if stage["source_sha256"] != {"start": base.sha(v1.REGION / "start.json"), "final": base.sha(v1.REGION / "final.json")}:
        raise ValueError("前版の開発資料が固定と異なる")
    entries = {v1.canonical(r): r for r in start["entries"]}
    existing = {v1.canonical(r): r for r in final["rows"]}
    targets, cards, sources = {}, {}, {}
    font_file = base.FONTS / "meiryo.ttc"
    font = ImageFont.truetype(font_file, size=17)
    for side in v2.SIDES:
        cohort = [r for r in stage["targets"][side].values() if v2.stratum(r, entries[v1.canonical(r)]) == "x-detail"]
        if Counter(r["status"] == "unreadable" for r in cohort) != {False: 1, True: 1}:
            raise ValueError("固定済みの詳細分割の4行と異なる")
        for row in sorted(cohort, key=v1.canonical):
            ident = f"X{len(targets)+1:02d}"
            key = v1.canonical(row)
            images, marks = marked_cards(entries[key], start["assets"], ident, font)
            cards.update(images)
            sources.update(marks)
            targets[ident] = existing[key]
    ids = {"whole": list(targets), "segments": [Path(n).stem for n in cards]}
    options = {arm: {"images": list(cards), "image_sha256": [hashlib.sha256(raw).hexdigest() for raw in cards.values()],
                     "ids": ids[arm], "prompt": v1.INTRO + v2.NOTICE + v3.shared + SHARED +
                     TREATMENTS[arm] + base.FORMAT + "、".join(ids[arm]) + "\n"} for arm in ARMS}
    deps = (V3, v3.V2, v2.V1, v1.GEOMETRY, Path(base.__file__), Path(pilot.opus.__file__), font_file)
    fixed = {"script_sha256": base.sha(Path(__file__)), "method_sha256": base.sha(HERE / "protocol.md"),
             "prior_sha256": base.sha(V3.parent / "lock.json"), "models": pilot.MODELS, "effort": "medium",
             "dependencies": {path.parent.name + "/" + path.name: base.sha(path) for path in deps},
             "sources": sources, "packs": options,
             "targets": {i: {k: r[k] for k in ("side", "key", "line_index", "box", "status")} for i, r in targets.items()}}
    return targets, cards, fixed


def merged_line(vote, ident, pack):
    parts = [vote[i] for i in pack["ids"] if i.startswith(ident + "-")]
    if not parts:
        raise ValueError("行の区画がない")
    return None if any(part is None for part in parts) else base.normalize("".join(parts))


def summarize(targets, packs, votes):
    rows = {}
    counts = {g: {arm: Counter() for arm in ARMS} for g in ("known", "unresolved")}
    for ident, row in targets.items():
        group = "unresolved" if row["status"] == "unreadable" else "known"
        rows[ident] = {"side": row["side"], "previous": group}
        for arm in ARMS:
            ballots = [votes[arm, m][ident] if arm == "whole" else merged_line(votes[arm, m], ident, packs[arm])
                       for m in pilot.MODELS]
            result = base.consensus(ballots)
            label = ("unresolved" if result is None else
                     ("agreed-text" if result else "agreed-empty") if group == "unresolved" else
                     "matches-previous" if result == base.normalize(row["text"]) else "differs-from-previous")
            rows[ident][arm] = label
            counts[group][arm][label] += 1
    old, new = (counts["known"][a] for a in ARMS)
    advance = (counts["unresolved"]["segments"]["agreed-text"] > counts["unresolved"]["whole"]["agreed-text"]
               and new["matches-previous"] >= old["matches-previous"]
               and new["differs-from-previous"] <= old["differs-from-previous"])
    return {"counts": counts, "rows": rows, "advance": advance}


def prepare(cards, fixed):
    if LOCK.exists() or ASSETS.exists():
        raise FileExistsError("事前固定を上書きしない")
    ASSETS.mkdir(parents=True)
    for name, content in cards.items():
        (ASSETS / name).write_bytes(content)
    base.write_json(LOCK, dict(fixed, fixed_at=base.utc_now()))
    print(base.sha(LOCK), len(cards), flush=True)


def run(args, targets, cards, fixed):
    if args.lock_sha256 != base.sha(LOCK) or {k: v for k, v in base.load(LOCK).items() if k != "fixed_at"} != fixed:
        raise ValueError("事前固定の入力が異なる")
    if any((ASSETS / name).read_bytes() != content for name, content in cards.items()):
        raise ValueError("配布画像が固定と異なる")
    with (OUT / "started.json").open("x", encoding="utf-8") as stream:
        json.dump({"lock_sha256": args.lock_sha256, "started": base.utc_now()}, stream)
    pilot.OUT = OUT / "reads"
    votes, receipts, failures = {}, [], []
    executables = {"sol": args.codex.resolve(), "opus": args.claude.resolve()}
    with ThreadPoolExecutor(max_workers=4) as pool:
        jobs = {}
        for arm, pack in fixed["packs"].items():
            fake_rows = [{"id": i, "sheet": 1} for i in pack["ids"]]
            study = {"image_order_by_sheet": {"1": pack["images"]},
                     "image_sha256": dict(zip(pack["images"], pack["image_sha256"], strict=True))}
            for model, exe in executables.items():
                jobs[pool.submit(pilot.read, exe, model, arm, pack, fake_rows, ASSETS, study)] = arm, model
        for job in as_completed(jobs):
            arm, model = jobs[job]
            try:
                vote, receipt = job.result()
                votes[arm, model] = vote
                receipts.append(receipt)
            except Exception as error:
                failures.append({"arm": arm, "model": model, "error": type(error).__name__})
    base.write_json(OUT / "execution.json", {"receipts": receipts, "failures": failures})
    if failures or len({r["session"] for r in receipts}) != 4 or material()[-1] != fixed or base.sha(LOCK) != args.lock_sha256:
        raise ValueError("受領または事前固定の照合が完了しない")
    result = summarize(targets, fixed["packs"], votes)
    with (HERE / "result.json").open("x", encoding="utf-8") as stream:
        json.dump(dict(result, lock_sha256=args.lock_sha256, receipts=receipts), stream, ensure_ascii=False, indent=2)
    print(json.dumps(result, ensure_ascii=False), flush=True)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("action", choices=("prepare", "run"))
    parser.add_argument("--codex", type=Path)
    parser.add_argument("--claude", type=Path)
    parser.add_argument("--lock-sha256")
    args = parser.parse_args()
    targets, cards, fixed = material()
    if args.action == "prepare":
        prepare(cards, fixed)
    else:
        run(args, targets, cards, fixed)


if __name__ == "__main__":
    main()
