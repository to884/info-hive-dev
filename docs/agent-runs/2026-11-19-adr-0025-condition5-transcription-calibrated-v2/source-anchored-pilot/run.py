"""画像の二票から、独立に確認した点線符号を結合できるか測る。"""

import argparse
from collections import Counter
from concurrent.futures import ThreadPoolExecutor, as_completed
import hashlib
import importlib.util
import json
from pathlib import Path
import random
import re

from PIL import ImageFont

HERE = Path(__file__).resolve().parent
V3 = HERE.parent / "actual-geometry-pilot-v3/run.py"
spec = importlib.util.spec_from_file_location("v3", V3)
v3 = importlib.util.module_from_spec(spec)
spec.loader.exec_module(v3)
v2, base = v3.v2, v3.base
v1, pilot = v2.v1, v2.pilot
OUT = pilot.trial.ROOT / HERE.name
ASSETS = OUT / "cards"
LOCK = HERE / "lock.json"
PAGES = {"defense": ("defense-p0006", "defense-p0007"),
         "disaster": ("disaster-p0008", "disaster-p0015")}
SEED = "adr0025-source-anchored-image-pilot-20261119"
MARKER = re.compile(r"⟦dots:([1-9][0-9]{0,2})⟧")
INSTRUCTIONS = (
    "点線がある場合は各カードの前後と重なりを照合し、実際に見える点の数を数えてください。"
    "点線の符号を画像で区別できないが、同じ行に所属する点の個数と位置を確認できる場合、"
    "その点線だけを元の位置で ⟦dots:N⟧ に換えてください。Nは見えた点の合計を数字で書きます。"
    "点線の外の文字はすべて転記し、確かめられない場合は行全体を未決定にしてください。"
    "意味を推測して点や文字を補いません。明確に字形を識別した句読点や記号は実際の字を転記します。\n"
)


def identity(row):
    return row["key"], row["line_index"]


def scalar_proof(row, scan, render, mid, ground, geo, region):
    """暫定転記のうち、符号以外にも本文を拒否する根拠がないものを選ぶ。"""
    key, i = identity(row)
    if identity(row) not in scan or len(scan[key, i]["runs"]) != 1:
        return None
    is_defense = key.startswith("defense-")
    if not (key, i) in (render if is_defense else mid):
        return None
    matched = {m["native"]: m["line"] for m in geo["matches"]}
    used = {matched[n] for n in region["lines"][i]["certification"]["native_glyphs"] if n in matched}
    if len(used) != 1:
        return None
    li, = used
    excluded = ground[li]["excluded"]
    if excluded == "garbled" and is_defense:
        line = geo["source_lines"][li]
        if line["text"].count("\ufffd") != row["symbol_count"] or re.search("[\ue000-\uf8ff]|\\(cid:[0-9]+\\)", line["text"]):
            return None
    elif excluded is not None:
        return None
    symbol = "…" if is_defense else "・"
    expected = len(scan[key, i]["runs"][0])
    if expected != row["symbol_count"] * (3 if is_defense else 1):
        return None
    source_runs = [m for m in re.finditer(re.escape(symbol) + "+", row["text"])
                   if len(m.group()) == row["symbol_count"]]
    if len(source_runs) != 1:
        return None
    span, = source_runs
    signature = base.normalize(row["text"][:span.start()] + f"⟦dots:{expected}⟧" + row["text"][span.end():])
    return {"kind": "source-backed", "dots": expected, "signature": signature, "exact": base.normalize(row["text"])}


def material():
    source_dir = HERE.parent / "provisional-dot-transcriptions"
    evidence_dir = HERE.parent / "dot-layout-v2"
    v9 = v1.REGION
    paths = {
        "provisional": source_dir / "result.json", "full_lines": base.BENCH / "corpus" / source_dir.name / "full-lines.json",
        "dot_scan": evidence_dir / "result.json", "object_raster": evidence_dir / "source-render-objects.json",
        "middle_dot": evidence_dir / "source-middle-dot-runs.json", "v9_start": v9 / "start.json",
        "v9_final": v9 / "final.json", "v3_lock": V3.parent / "lock.json",
    }
    before = {name: base.sha(path) for name, path in paths.items()}
    read = {name: base.load(path) for name, path in paths.items()}
    if (before["full_lines"] != read["provisional"]["private_full_lines_sha256"]
            or before["v9_start"] != read["v9_final"]["start_sha256"]):
        raise ValueError("仮転記か元の固定画像が変化")
    old_scan = {identity(r): r for r in read["dot_scan"]["geometries"]}
    render = {identity(r) for r in read["object_raster"]["rows"] if r["same_pixel_components"]}
    middle = {identity(r) for r in read["middle_dot"]["rows"] if r["covered"] or r["pairwise_covered"]}
    seen = {identity(r) for rows in read["v3_lock"]["targets"].values() for r in rows.values()}
    previous = {identity(r): r for r in read["v9_final"]["rows"]}
    start = read["v9_start"]
    entries = {identity(r): r for r in start["entries"]}
    targets, packages, images_by_pub, expected = {}, {}, {}, {}
    font_file = base.FONTS / "meiryo.ttc"
    font = ImageFont.truetype(font_file, size=17)
    for pub, pages in PAGES.items():
        truth_file = base.BENCH / "corpus/public" / (pub + ".truth.json")
        before[pub + "_truth"] = base.sha(truth_file)
        ground_pages = {f"{pub}-p{p['page']:04d}": p["lines"] for p in base.load(truth_file)["pages"]}
        selected = []
        for page in pages:
            dir_base = base.BENCH / "corpus"
            region_path = dir_base / "public/region-v9" / (page + ".json")
            geo_path = dir_base / "region-repair-v9/geometry" / (page + ".json")
            region = base.load(region_path)
            if base.sha(geo_path) != region["geometry_sha256"]:
                raise ValueError("保全した字形の幾何と異なる")
            before[page + "_region"], before[page + "_geometry"] = base.sha(region_path), base.sha(geo_path)
            geo = base.load(geo_path)
            potential = []
            for r in read["full_lines"]:
                if r["key"] != page or identity(r) in seen:
                    continue
                rec = scalar_proof(r, old_scan, render, middle, ground_pages[page], geo, region)
                if rec:
                    priority = hashlib.sha256(f"{SEED}/{page}/{r['line_index']}".encode()).hexdigest()
                    potential.append((priority, r, rec))
            selected.append(min(potential, key=lambda p: p[0])[1:])
        # 前の比較で両系統が既存全文と一致した点なしの対照を混ぜる。
        side, guard = ("evaluation", "G01") if pub == "defense" else ("evaluation3", "G06")
        control = read["v3_lock"]["targets"][side][guard]
        entry = previous[identity(control)]
        selected.append((entry, {"kind": "known-control", "exact": base.normalize(entry["text"])}))
        random.Random(SEED + pub).shuffle(selected)
        targets[pub], expected[pub], images, tiles = {}, {}, {}, {}
        for i, (row, gold) in enumerate(selected, 1):
            ident = f"V{i:02d}"
            original = entries[identity(row)]
            part, detail = v2.make_cards(original, start["assets"], ident, font)
            images.update(part)
            tiles.update(detail)
            targets[pub][ident] = {"key": row["key"], "line_index": row["line_index"], "kind": gold["kind"]}
            expected[pub][ident] = gold
        images_by_pub[pub] = images
        ids = list(targets[pub])
        packages[pub] = {"images": list(images), "ids": ids,
                         "image_sha256": [hashlib.sha256(data).hexdigest() for data in images.values()],
                         "prompt": v1.INTRO + v2.NOTICE + v3.shared + INSTRUCTIONS + base.FORMAT + "、".join(ids) + "\n",
                         "source_tiles": tiles}
    frozen = {"script_sha256": base.sha(Path(__file__)), "protocol_sha256": base.sha(HERE / "protocol.md"),
              "sources": before, "seed": SEED, "models": pilot.MODELS, "effort": "medium", "targets": targets, "packs": packages}
    return targets, expected, images_by_pub, frozen


def decision(left, right, entry):
    if left is None or left != right:
        return "unresolved"
    if entry["kind"] == "known-control":
        return "matches-control" if left == entry["exact"] else "differs-from-control"
    if left == entry["exact"] and not MARKER.search(left):
        return "agreed-source-spelling"
    tokens = MARKER.findall(left)
    if len(tokens) == 1 and int(tokens[0]) == entry["dots"] and left == entry["signature"]:
        return "physical-agreement-plus-source"
    return "agreement-insufficient"


def execute(args, expected, images, fixed):
    if base.sha(LOCK) != args.lock_sha256 or {k: v for k, v in base.load(LOCK).items() if k != "fixed_at"} != fixed:
        raise ValueError("事前固定の入力と異なる")
    for pub, cards in images.items():
        if any((ASSETS / pub / n).read_bytes() != data for n, data in cards.items()):
            raise ValueError("受領者に出す画像が変化")
    with (OUT / "started.json").open("x", encoding="utf-8") as stream:
        json.dump({"lock_sha256": args.lock_sha256, "started": base.utc_now()}, stream)
    pilot.OUT = OUT / "reads"
    paths = {"sol": args.codex.resolve(), "opus": args.claude.resolve()}
    votes, receipts, failures = {}, [], []
    with ThreadPoolExecutor(max_workers=4) as pool:
        jobs = {}
        for pub, full in fixed["packs"].items():
            pack = {k: full[k] for k in ("images", "ids", "image_sha256", "prompt")}
            fake_rows = [{"id": i, "sheet": 1} for i in pack["ids"]]
            study = {"image_order_by_sheet": {"1": pack["images"]},
                     "image_sha256": dict(zip(pack["images"], pack["image_sha256"], strict=True))}
            for who, exe in paths.items():
                jobs[pool.submit(pilot.read, exe, who, pub, pack, fake_rows, ASSETS / pub, study)] = (pub, who)
        for job in as_completed(jobs):
            pub, who = jobs[job]
            try:
                value, receipt = job.result()
                votes[pub, who] = value
                receipts.append(dict(receipt, publication=pub))
            except Exception as error:
                failures.append({"publication": pub, "reader": who, "error": type(error).__name__})
    base.write_json(OUT / "execution.json", {"receipts": receipts, "failures": failures})
    if failures or len({r["session"] for r in receipts}) != 4:
        raise ValueError("新規の4セッションを受領できない")
    if material()[-1] != fixed or base.sha(LOCK) != args.lock_sha256:
        raise ValueError("読取の前後で固定が違う")
    outcomes = {pub: {i: {"kind": e["kind"], "result": decision(votes[pub, "sol"][i], votes[pub, "opus"][i], e)}
                      for i, e in known.items()} for pub, known in expected.items()}
    counts = {pub: Counter(r["result"] for r in rs.values()) for pub, rs in outcomes.items()}
    with (HERE / "result.json").open("x", encoding="utf-8") as stream:
        json.dump({"lock_sha256": args.lock_sha256, "outcomes": outcomes, "counts": counts, "receipts": receipts},
                  stream, ensure_ascii=False, indent=2)
    print(json.dumps(counts, ensure_ascii=False), flush=True)


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("action", choices=("prepare", "run"))
    p.add_argument("--codex", type=Path)
    p.add_argument("--claude", type=Path)
    p.add_argument("--lock-sha256")
    args = p.parse_args()
    _, expected, images, fixed = material()
    if args.action == "prepare":
        if LOCK.exists() or ASSETS.exists():
            raise FileExistsError("固定済みの画像と手順を上書きしない")
        for pub, cards in images.items():
            dst = ASSETS / pub
            dst.mkdir(parents=True)
            for name, content in cards.items():
                (dst / name).write_bytes(content)
        base.write_json(LOCK, dict(fixed, fixed_at=base.utc_now()))
        print(base.sha(LOCK), {pub: len(pics) for pub, pics in images.items()}, flush=True)
    else:
        execute(args, expected, images, fixed)


if __name__ == "__main__":
    main()
