"""より広い文脈と縦一列の字形を使う固定画像の開発試験。"""

import importlib.util
from pathlib import Path

from PIL import Image, ImageDraw

HERE = Path(__file__).resolve().parent
FILE = HERE.parent / "v11-guided-image-pilot/run.py"
spec = importlib.util.spec_from_file_location("guided_pilot", FILE)
base = importlib.util.module_from_spec(spec)
spec.loader.exec_module(base)
old, cards, slots = base.old, base.cards, base.slots
OUT = cards.CORPUS / "reference-v12-readable-regions-pilot"
BASE_SELECTION, BASE_MATERIAL = base.selection, base.material
PUNCTUATION = (
    "点線や丸い印が他の字から離れて見え、形だけでは符号を区別できないときは、本文のその箇所に位置を記録します。"
    "横座標の赤い目盛りは5画素ごとです。点線は ⟦trail:X-Y⟧、丸い印は ⟦round:X-X⟧ です。"
    "同じ行に小形の中点がいくつかあれば、字種が見分けられないものをそれぞれ記録します。"
    "大きくて黒丸と識別できる形や、字形を識別できる記号は、そのまま転記してください。図表の色見本などは文字から外します。"
)
Y_TEXT = (
    "枠あり・枠なしの450 DPIで、枠が示す列の画を上から順に一つずつ確かめてください。"
    "150 DPIの広い周囲は、行頭と行末が前後の列のどこに続くかを確かめるための画像です。"
    "枠内に見える円や独立した横画、違いが小さい仮名と漢字は、正しいと思う語や条番号に直さず、対象の画から読む文字を選びます。"
    "長い列の表示は重なります。一字の全部と隣の字の間隔を見て、表示中の同じ字を一度だけ書いてください。textは一つの全文です。"
)


def end_context(row, mapping, ident, font):
    path = cards.CORPUS / "probe-v4/png" / (row["key"] + ".png")
    if base.SHA(path) != mapping["sha"]["150_dpi"]:
        raise ValueError("固定150 DPIに一致しない")
    x, y, w, h = row["box"]
    views = {}
    with Image.open(path) as fixed:
        left, right = max(0, x - 116), min(fixed.width, x + w + 116)
        ends = (("head", y, "行頭"), ("tail", y + h, "行末")) if h > 160 else (("line", y + h // 2, "全体"),)
        for label, center, title in ends:
            top, bottom = max(0, center - 105), min(fixed.height, center + 105)
            piece = fixed.crop((left, top, right, bottom)).convert("RGB")
            panel = Image.new("RGB", (piece.width * 3 + 18, piece.height * 3 + 42), "white")
            panel.paste(piece.resize((3 * piece.width, 3 * piece.height), Image.Resampling.NEAREST), (8, 37))
            draw = ImageDraw.Draw(panel)
            draw.text((5, 5), f"{ident}  固定150 DPI  {title}の広い周囲", font=font, fill="#222222")
            lx, rx = 8 + 3 * (x - left), 8 + 3 * (x + w - left)
            ty, by = 37 + 3 * (max(y, top) - top), 37 + 3 * (min(y + h, bottom) - top)
            draw.line((lx - 1, ty, lx - 1, by), fill="#b80d18", width=1)
            draw.line((rx, ty, rx, by), fill="#b80d18", width=1)
            if top <= y < bottom:
                draw.line((lx - 1, ty - 1, rx, ty - 1), fill="#b80d18", width=1)
            if top < y + h <= bottom:
                draw.line((lx - 1, by, rx, by), fill="#b80d18", width=1)
            views[f"{ident}-{label}-context.png"] = slots.blob(panel)
    return views


def plan(row, mapping, origin, ident, font):
    width, height = row["box"][2:]
    asset = mapping["source_view"]
    vertical = row["allocation_axis"] == "y"
    details = old.details(asset, ident, vertical, font)
    if vertical:
        return "x-text", Y_TEXT, [], details | end_context(row, mapping, ident, font)
    if 16 <= width <= 120 and 12 <= height <= 35:
        extra, names, _ = slots.aid(row, mapping, origin, ident, font)
        guide = slots.GUIDE + ("『行と列のつながり』で前後のつながりを追います。"
                               "直交方向で枠からはみ出る画があれば字全体の上下中心を確認してください。")
        return "x-slots", guide, names, details | extra
    if width > 800 and len(details) > 2:
        first, last = list(details)[0], list(details)[-1]
        details = {first: details[first], last: details[last]}
    return "x-text", base.HORIZONTAL + PUNCTUATION, [], details


def selected(rows):
    choice = BASE_SELECTION(rows)
    extras = {("defense-p0107", 22), ("wp-summary-p0002", 13), ("wp-summary-p0010", 34)}
    choice.update({i: "circle" for i, row in enumerate(rows) if (row["key"], row["line_index"]) in extras})
    if sum(kind == "circle" for kind in choice.values()) != len(extras):
        raise ValueError("丸印の診断3例がそろわない")
    return choice


def make(rows, choice):
    manifest, images = BASE_MATERIAL(rows, choice)
    immutable = (Path(__file__), FILE, HERE / "protocol.md", FILE.parent / "lock.json", FILE.parent / "result.json")
    manifest["inputs"].update({str(path): base.SHA(path) for path in immutable})
    return manifest, images


if __name__ == "__main__":
    base.HERE, base.OUT, base.LOCK = HERE, OUT, HERE / "lock.json"
    base.visual_plan, base.selection, base.material = plan, selected, make
    base.main()
