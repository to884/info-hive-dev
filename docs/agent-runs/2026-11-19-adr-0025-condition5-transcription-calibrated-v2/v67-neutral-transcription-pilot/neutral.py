"""固定画素を表示し、検証対象の字体や読みの候補を指示に含めない。"""

from contextlib import contextmanager
from io import BytesIO
from pathlib import Path
import sys

from PIL import Image

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parent / "v62-combined-reading-pilot"))
import render

core, audit, previous = render.core, render.audit, render.previous
VERTICAL = (
    "固定画素の縦の拡大から、一字ずつ筆画の数、接続、角、各部分の長さと位置を確認します。"
    "近い二つの字体が考えられる場合は、両方の違う画を比べ、見える形に従ってください。"
    "語の推測で文字や字体を補いません。文字の小ささや向きは元の位置と周囲で確認します。"
    "横倒しの短い枠では、画像に回転表示がある場合に照らします。所属は元の枠で判断します。"
)
SHORT = (
    "横書きの行では左から右へ写します。縦書きの複数列を横切る枠では右端の列から左へ進み、"
    "同じ列では上から下へ写します。紙面と枠なしの像で順序と字全体を確かめます。"
    "枠に所属する字を順に連結し、列の目印や区切りを加えません。"
)
HORIZONTAL = (
    "横書きでは本文の筆画と独立した記号を一度ずつ確認します。"
    "字と記号の間隔、周囲の文字に対する大きさと高さ、同じ紙面の記号の配置も見て、"
    "図形の見本、枠の外の筆画、独立して見えない記号を加えないでください。"
)
REMOVED = (
    "「ニ」と「二」", "「ロ」と「口」", "山偏の右上", "「っ」と「つ」", "上下の二本の横画が一字",
    render.horizontal.GUIDE,
)


def neutral_frame(row, original, origins, ident, font):
    images, guide, slots = render.display(row, original, origins, ident, font)
    if row["allocation_axis"] == "y":
        guide = guide.removesuffix(render.orientation.VERTICAL + render.instructions.VERTICAL) + VERTICAL
    else:
        guide = guide.replace(render.horizontal.GUIDE, HORIZONTAL)
        if render.short_frame(row):
            guide = guide.replace(render.short.GUIDE, SHORT)
            for kind in ("slots", "wide"):
                images.pop(f"{ident}-{kind}.png", None)
            if f"{ident}-layout.png" in images:
                guide += "『行と列のつながり』で周囲の並びと元の枠を照らします。"
    if any(mark in guide for mark in REMOVED):
        raise ValueError("本文にあり得る特定の字体の例が指示に残る")
    return images, guide, slots


def dimensions(images):
    sizes = {}
    for name, data in images.items():
        with Image.open(BytesIO(data)) as im:
            sizes[name] = list(im.size)
    return sizes


@contextmanager
def active(trace):
    current = {}

    def display(row, original, origins, ident, font):
        current[ident] = f"{row['key']}/{row['line_index']}"
        return neutral_frame(row, original, origins, ident, font)

    def fit(primary, extra, required):
        all_images = set(extra)
        close = sorted(name for name in extra if "-close-" in name)
        if not close:
            raise ValueError("枠あり・枠なしの細部がない")
        essential = {close[0], close[-1]} | {name for name in extra if name.endswith("-layout.png")}
        picked = render.fit(primary, extra, required | essential)
        omitted = all_images - set(picked)
        label = next(iter(primary)).split("-", 1)[0]
        trace[current.pop(label)] = {"sizes": dimensions(primary | picked),
                                     "required_close_or_layout": sorted(essential),
                                     "omitted_optional": sorted(name for name in omitted if "-coordinate-" not in name)}
        return picked

    with render.active():
        render.draft.frame, audit.fit = display, fit
        yield
