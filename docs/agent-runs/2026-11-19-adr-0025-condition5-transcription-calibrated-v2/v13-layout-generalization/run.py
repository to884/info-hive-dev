"""未着手だった監査行を使った開発専用の一般化試験。"""

from collections import defaultdict
import hashlib
import importlib.util
import math
from pathlib import Path

from PIL import Image, ImageDraw

HERE = Path(__file__).resolve().parent
PREVIOUS = HERE.parent / "v12-readable-regions-pilot/run.py"
spec = importlib.util.spec_from_file_location("entire_text_pilot", PREVIOUS)
old = importlib.util.module_from_spec(spec)
spec.loader.exec_module(old)
base, cards, slots = old.base, old.cards, old.slots
OUT = cards.CORPUS / "reference-v13-layout-generalization"
SEED = "adr0025-v13-layout-generalization-20261120"


def geometry(row):
    width, height = row["box"][2:]
    if row["allocation_axis"] == "y":
        return "vertical"
    return "short-x" if 16 <= width <= 120 and 12 <= height <= 35 else "other-x"


def selection(rows):
    receipt = base.LOAD(cards.HERE / "received.json")
    packages = base.LOAD(cards.PACKS)
    if receipt["packages_sha256"] != base.SHA(cards.PACKS):
        raise ValueError("元の監査の受領が異なる")
    pools = defaultdict(lambda: defaultdict(list))
    for name, pack in packages["packs"].items():
        if any(case["availability"] == "received" for case in receipt["votes"][name].values()):
            continue
        for mapping in pack["mapping"].values():
            i = mapping["entry"]
            row = rows[i]
            if any(not item["known"] for item in row["targets"].values()):
                continue
            family = row["key"].split("-", 1)[0].rstrip("0123456789")
            rank = hashlib.sha256(f"{SEED}/{i}".encode()).hexdigest()
            pools[geometry(row)][row["side"], family].append((rank, i))
    chosen = {}
    for category, strata in pools.items():
        ranked = sorted((depth, rank, i) for items in strata.values() for depth, (rank, i) in enumerate(sorted(items)))
        unique = ranked[:4]
        if len(unique) != 4:
            raise ValueError(f"寸法帯の新しい検証行が不足: {category}")
        for _, _, i in unique:
            chosen[i] = "fresh-" + category
    if len(chosen) != 12:
        raise ValueError("未着手行を寸法帯ごとに4行選べない")
    new = base.LOAD(PREVIOUS.parent / "result.json")
    indices = {(v["key"], v["line_index"]): i for i, v in enumerate(rows)}
    for r in new["rows"].values():
        if r["outcome"] == "unresolved":
            chosen[indices[r["key"], r["line_index"]]] = "repeat-unresolved"
    if len(chosen) != 20:
        raise ValueError("先行試験の未決定8行が異なる")
    return chosen


def profile(mapping, origin, ident, font):
    """同じ450画素の範囲で、枠なしと枠ありの両方を縦のまま表示する。"""
    view = mapping["source_view"]["views"][1]
    x0, y0, x1, y1 = view["target_rectangle"]
    l, r = max(0, math.floor(x0) - 14), math.ceil(x1) + 14
    frame = slots.asset(view, origin, "framed")
    raw = slots.asset(view, origin, "plain")
    r = min(frame.width, r)
    total = math.ceil(y1) - math.floor(y0)
    c = 315
    # 中間は既存の細部で確認し、字の所属が難しい行端を大きく見せる。
    parts = [("全体", math.floor(y0) - 41, math.ceil(y1) + 41)] if total <= c else [
        ("行頭", math.floor(y0) - 38, math.floor(y0) + c),
        ("行末", math.ceil(y1) - c, math.ceil(y1) + 38)]
    result = {}
    for n, (name, t, b) in enumerate(parts, 1):
        t, b = max(0, t), min(frame.height, b)
        tile = Image.new("RGB", (4 * (r - l) + 24, 2 * (b - t) + 58), "white")
        draw = ImageDraw.Draw(tile)
        draw.text((8, 4), f"{ident}  {name}の字形  固定450 DPI", font=font, fill="#222222")
        for j, (label, source) in enumerate((("枠あり", frame), ("枠なし", raw))):
            pic = source.crop((l, t, r, b))
            x = 5 + j * (2 * pic.width + 13)
            draw.text((x, 29), label, font=font, fill="#222222")
            tile.paste(pic.resize((2 * pic.width, 2 * pic.height), Image.Resampling.NEAREST), (x, 54))
        result[f"{ident}-profile-{n:02d}.png"] = slots.blob(tile)
    return result


def plan(row, mapping, origin, ident, font):
    if row["allocation_axis"] == "y":
        mode, instructions, names, views = old.plan(row, mapping, origin, ident, font)
        guide = (
            "『行頭・行末の字形』または『全体の字形』で、字形と枠を見比べます。"
            "空欄と思う場合も、枠ありで輪郭を確かめ、枠なしに同じインクがあるか見直します。"
            "字が一つの短い枠でも、見える文字や文字として並ぶ円は記録します。"
        )
        return mode, instructions + guide, names, views | profile(mapping, origin, ident, font)
    try:
        mode, instructions, names, views = old.plan(row, mapping, origin, ident, font)
    except ValueError as error:
        if geometry(row) != "short-x" or "目印を使える短い枠ではない" not in str(error):
            raise
        return "x-text", base.HORIZONTAL + old.PUNCTUATION, [], old.old.details(mapping["source_view"], ident, False, font)
    if mode == "x-text":
        instructions += (
            "句読点や点の一つ一つの位置も見直します。形を見分けられない小さい丸は行の中でも印を使います。"
            "隣の字を受けて自然に見える別の語へ直す前に、同じ場所の450 DPIの画を確かめます。"
        )
    return mode, instructions, names, views


def make(rows, choice):
    value, images = old.BASE_MATERIAL(rows, choice)
    pins = Path(__file__), HERE / "protocol.md", PREVIOUS, PREVIOUS.parent / "result.json", cards.HERE / "received.json"
    value["inputs"].update({str(p): base.SHA(p) for p in pins})
    return value, images


if __name__ == "__main__":
    base.HERE, base.OUT, base.LOCK = HERE, OUT, HERE / "lock.json"
    base.visual_plan, base.selection, base.material = plan, selection, make
    base.main()
