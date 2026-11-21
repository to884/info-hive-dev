"""既存の開発画像で、画素と対象をそろえて所属を確認する指示を比べる。"""

import argparse
from collections import Counter
from concurrent.futures import ThreadPoolExecutor, as_completed
import hashlib
import importlib.util
import io
import json
from pathlib import Path
import random

from PIL import Image, ImageDraw, ImageFont

HERE = Path(__file__).resolve().parent
GEOMETRY = HERE.parent / "geometry-pilot/run.py"
spec = importlib.util.spec_from_file_location("geometry", GEOMETRY)
pilot = importlib.util.module_from_spec(spec)
spec.loader.exec_module(pilot)
base = pilot.base
REGION = base.BENCH / "corpus/region-visual-v9"
OUT = pilot.trial.ROOT / HERE.name
ASSETS = OUT / "cards"
LOCK = HERE / "lock.json"
SELECTION = "adr0025-condition5-actual-geometry-pilot-v1-20261119"
ARMS = ("control", "geometry")
SIDES = ("tuning", "evaluation", "evaluation3")
TYPES = ("x-short", "x-long", "y")
INTRO = (
    "各カードの上段は固定150 DPI（3倍表示）、下段は450 DPI、左は枠なし、右は枠ありです。"
    "カードに対象のIDと所属軸xまたはyを示します。"
    "枠の中または周りに見える字のうち、指定軸方向の字全体の長さの半分以上が枠と重なり、"
    "直交方向の字全体のインクの中心が枠内にある字だけを自然な読む順に書いてください。"
    "同じ字の枠外部分は見てよいですが、別の字や図形を加えないでください。"
    "150 DPIで所属を、450 DPIで字形を確認してください。OCRや既存本文は示しません。"
    "文字がなければempty、字種または所属が決められなければunreadableとしてください。\n"
)
GUIDE = (
    "まず450 DPIの枠なしで、隣の字の断片を分け、離れた点や線がどの字の一部かを確認してください。"
    "次に150 DPIの枠あり・枠なしを対照して、字形ごとに指定軸の重なりと直交方向の中心を確認してください。"
    "所属する字を選んでから、縦書きの複数列は右の列から、各列は上から下へ転記してください。"
    "所属する各字が確かなら、周囲の文脈が途中で切れていても、確認できた字だけを記してください。\n"
)


def canonical(row):
    return row["key"], row["line_index"]


def geometry_type(row):
    if row["allocation_axis"] == "y":
        return "y"
    return "x-short" if row["box"][2] - row["box"][0] <= 20 else "x-long"


def choose(rows):
    selected = []
    for side in SIDES:
        for bucket in TYPES:
            for unresolved in (False, True):
                eligible = [r for r in rows if r["side"] == side and geometry_type(r) == bucket
                            and (r["status"] == "unreadable") == unresolved]
                selected.append(min(eligible, key=lambda r: hashlib.sha256(
                    f"{SELECTION}/{r['key']}/{r['line_index']}".encode()).hexdigest()))
    random.Random(SELECTION).shuffle(selected)
    return selected


def card(asset, index, given_id, font):
    tiles = []
    paths = {}
    for view in asset["views"]:
        for frame in view["images"]:
            if frame["kind"] not in ("plain", "framed"):
                continue
            name = frame["image"]
            path = REGION / "assets" / name
            digest = base.sha(path)
            if digest != index[path.resolve().as_posix()]:
                raise ValueError("v9の元画像が固定と異なる")
            paths[name] = digest
            with Image.open(path) as source:
                tiles.append((view["dpi"], frame["kind"], source.convert("RGB")))
    if [(dpi, kind) for dpi, kind, _ in tiles] != [(150, "plain"), (150, "framed"), (450, "plain"), (450, "framed")]:
        raise ValueError("元画像に4種類の表示がない")
    step = max(tile.width for _, _, tile in tiles) + 12
    height = max(tile.height for _, _, tile in tiles) + 27
    result = Image.new("RGB", (2 * step, 32 + 2 * height), "#ffffff")
    titles = ImageDraw.Draw(result)
    titles.text((5, 0), f"{given_id}   {asset['allocation_axis']}", font=font, fill="#151515")
    for i, (dpi, kind, tile) in enumerate(tiles):
        x, y = (i % 2) * step, 32 + (i // 2) * height
        titles.text((x + 5, y), f"{dpi} DPI {'枠なし' if kind == 'plain' else '枠あり'}",
                    font=font, fill="#151515")
        result.paste(tile, (x, y + 25))
        if result.crop((x, y + 25, x + tile.width, y + 25 + tile.height)).tobytes() != tile.tobytes():
            raise ValueError("表示用カードの画素が元画像と異なる")
    raw = io.BytesIO()
    result.save(raw, format="PNG")
    return raw.getvalue(), paths


def material():
    start_path, final_path = REGION / "start.json", REGION / "final.json"
    start, final = base.load(start_path), base.load(final_path)
    if final["start_sha256"] != base.sha(start_path):
        raise ValueError("v9の最終記録と固定がつながらない")
    source_rows = {canonical(r): r for r in start["entries"]}
    if len(source_rows) != 2865 or {canonical(r) for r in final["rows"]} != set(source_rows):
        raise ValueError("元の対象2865行がそろわない")
    font_path = base.FONTS / "meiryo.ttc"
    font = ImageFont.truetype(font_path, size=18)
    blobs, targets, sources = {}, {}, {}
    for i, row in enumerate(choose(final["rows"]), 1):
        ident = f"G{i:02d}"
        src = source_rows[canonical(row)]
        if any(row[k] != src[k] for k in ("box", "ocr_text_sha256", "allocation_axis")):
            raise ValueError("同じ行の固定条件が異なる")
        blobs[f"{ident}.png"], sources[ident] = card(src["asset"], start["assets"], ident, font)
        targets[ident] = row
    images = list(blobs)
    ids = list(targets)
    pack = {"images": images, "image_sha256": [hashlib.sha256(b).hexdigest() for b in blobs.values()], "ids": ids}
    packs = {arm: dict(pack, prompt=INTRO + extra + base.FORMAT + "、".join(ids) + "\n")
             for arm, extra in zip(ARMS, ("", GUIDE), strict=True)}
    deps = [GEOMETRY, Path(base.__file__), Path(pilot.opus.__file__), font_path]
    fixed = {"source_sha256": {"start": base.sha(start_path), "final": base.sha(final_path)},
             "script_sha256": base.sha(Path(__file__)), "protocol_sha256": base.sha(HERE / "protocol.md"),
             "dependency_sha256": {p.name: base.sha(p) for p in deps},
             "selection": SELECTION, "models": pilot.MODELS, "effort": "medium",
             "packs": packs, "source_images": sources,
             "targets": {i: {k: r[k] for k in ("key", "line_index", "side", "allocation_axis", "box", "status")}
                         for i, r in targets.items()}}
    return targets, blobs, fixed


def prepare(blobs, fixed):
    if LOCK.exists() or ASSETS.exists():
        raise FileExistsError("指定か派生画像がすでにある")
    ASSETS.mkdir(parents=True)
    for name, raw in blobs.items():
        (ASSETS / name).write_bytes(raw)
    base.write_json(LOCK, dict(fixed, fixed_at=base.utc_now()))
    print(base.sha(LOCK), flush=True)


def summarize(targets, votes):
    rows = {}
    for i, r in targets.items():
        group = "unresolved" if r["status"] == "unreadable" else "known"
        record = {"side": r["side"], "geometry": geometry_type(r), "previous": group}
        for arm in ARMS:
            consensus = base.consensus([votes[arm, who][i] for who in pilot.MODELS])
            if consensus is None:
                record[arm] = "unresolved"
            elif group == "unresolved":
                record[arm] = "candidate-agreement"
            else:
                record[arm] = "matches-previous" if consensus == base.normalize(r["text"]) else "differs-from-previous"
        rows[i] = record
    counts = {g: {a: dict(Counter(r[a] for r in rows.values() if r["previous"] == g))
                  for a in ARMS} for g in ("known", "unresolved")}
    a, b = [counts["unresolved"][arm].get("candidate-agreement", 0) for arm in ARMS]
    old, new = (counts["known"][arm] for arm in ARMS)
    advance = (b >= a + 2 and new.get("matches-previous", 0) >= old.get("matches-previous", 0)
               and new.get("differs-from-previous", 0) <= old.get("differs-from-previous", 0))
    return {"counts": counts, "rows": rows, "advance": advance}


def read_all(args, targets, blobs, fixed):
    if base.sha(LOCK) != args.lock_sha256 or {k: v for k, v in base.load(LOCK).items() if k != "fixed_at"} != fixed:
        raise ValueError("固定した入力が変わった")
    if any((ASSETS / n).read_bytes() != b for n, b in blobs.items()):
        raise ValueError("配布画像が変わった")
    # 既存のロックや原票を上書きする再実行を、CLI起動前に排他で止める。
    start = OUT / "started.json"
    with start.open("x", encoding="utf-8") as stream:
        json.dump({"fixed": args.lock_sha256, "started": base.utc_now()}, stream, ensure_ascii=False)
    if (HERE / "result.json").exists():
        raise FileExistsError("保存済みの結果がある")
    fake_rows = [{"id": i, "sheet": 1} for i in targets]
    pilot.OUT = OUT / "reads"
    executables = {"sol": args.codex.resolve(), "opus": args.claude.resolve()}
    records, failed = {}, {}
    with ThreadPoolExecutor(max_workers=4) as pool:
        jobs = {}
        for arm, pack in fixed["packs"].items():
            study = {"image_order_by_sheet": {"1": pack["images"]},
                     "image_sha256": dict(zip(pack["images"], pack["image_sha256"], strict=True))}
            for who, exe in executables.items():
                job = pool.submit(pilot.read, exe, who, arm, pack, fake_rows, ASSETS, study)
                jobs[job] = arm, who
        for job in as_completed(jobs):
            arm, who = jobs[job]
            try:
                records[arm, who] = job.result()
            except Exception as error:
                failed[f"{arm}/{who}"] = type(error).__name__
    receipts = [r for _, r in records.values()]
    base.write_json(OUT / "execution.json", {"receipts": receipts, "failed": failed})
    if failed:
        raise RuntimeError(f"転記を受領できない条件: {failed}")
    older = [GEOMETRY.parent / "result.json", GEOMETRY.parent.parent / "geometry-crops/result.json",
             pilot.PREVIOUS.parent / "result.json"]
    past = pilot.prior.original()[3] | {r["session"] for path in older for r in base.load(path)["receipts"]}
    sessions = {r["session"] for r in receipts}
    if len(sessions) != 4 or sessions & past or material()[-1] != fixed or base.sha(LOCK) != args.lock_sha256:
        raise ValueError("新規セッションと固定入力を再確認できない")
    results = summarize(targets, {key: vals for key, (vals, _) in records.items()})
    base.write_json(HERE / "result.json", dict(results, lock_sha256=args.lock_sha256, receipts=receipts))
    print(json.dumps({"counts": results["counts"], "advance": results["advance"]}, ensure_ascii=False), flush=True)


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("action", choices=("prepare", "run"))
    p.add_argument("--codex", type=Path)
    p.add_argument("--claude", type=Path)
    p.add_argument("--lock-sha256")
    args = p.parse_args()
    targets, blobs, fixed = material()
    if args.action == "prepare":
        prepare(blobs, fixed)
    else:
        read_all(args, targets, blobs, fixed)


if __name__ == "__main__":
    main()
