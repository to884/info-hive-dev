"""正解を渡さず共通の固定画素から新しい監査票の表示を作る。"""

import argparse
from collections import defaultdict
import importlib.util
import math
from pathlib import Path
from random import SystemRandom
import tempfile

from PIL import Image, ImageDraw, ImageFont

HERE = Path(__file__).resolve().parent


def module(name, path):
    spec = importlib.util.spec_from_file_location(name, path)
    value = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(value)
    return value


population = module("v14_population", HERE / "selection.py")
trial = module("v13_layout", HERE.parent / "v13-layout-generalization/run.py")
old, slots = trial.cards, trial.slots
load, sha, OUT = population.load, population.sha, population.OUT
from readers import encoded, save_once

INTRO = trial.base.old.INTRO
FORMAT = trial.base.old.FORMAT
DOTS = (
    "小さくて字種を区別できない丸印は行頭にも行中にもあります。固定150 DPIで小さく丸いインクを確認し、"
    "字種が見えないものは全部、本文の当たる位置に ⟦round:X-X⟧ と書きます。点線は ⟦trail:X-Y⟧ とします。"
    "横座標の一目盛りは5画素で、XとYは最初と最後の点の中心です。"
    "字形が明らかな字や記号は普通に写します。色見本などの図形は本文に入れません。"
)
HORIZONTAL = (
    "450 DPIの筆画を確認し、正しいと思う別の語へ直さないでください。"
    "行頭・行末の字全体がどこまで入り、途中の括弧や小さな記号が何個あるかを確認します。"
)
SHORT = (
    "『行と列のつながり』を見ると、短い枠が横書きか、縦書きの複数列にかかるかを確認できます。"
    "横書きは通常の全文を返します。複数の縦書きの列の場合、textは V|A:甲|B:乙 の形式で、"
    "枠内に所属する全文を列の目印ごとに分けます。目印は左からA、Bの順です。"
    "空の列もA:と記録し、目印を全て各一度含めます。所属は元の枠内外のインクで判定します。"
)
VERTICAL = trial.old.Y_TEXT + (
    "短い枠や行端の『字形』で枠あり・なしを照合します。空欄と思ったときも、"
    "枠なしに文字として並ぶ円や孤立した一本の横画がないか確かめてください。"
)


def details(mapping, origin, ident, font):
    asset = mapping["source_view"]["views"][1]
    framed = slots.asset(asset, origin, "framed")
    plain = slots.asset(asset, origin, "plain")
    x, y, r, b = asset["target_rectangle"]
    left, top, right, bottom = math.floor(x), math.floor(y), math.ceil(r), math.ceil(b)
    vertical = mapping["axis"] == "y"
    along = bottom - top if vertical else right - left
    spans = list(trial.base.old.spans(along))
    if len(spans) > 8:
        spans = [spans[0], spans[-1]]
    images = {}
    for index, (start, end) in enumerate(spans, 1):
        if vertical:
            ax, ay, bx, by = left, top + start, right, top + end
        else:
            ax, ay, bx, by = left + start, top, left + end, bottom
        bounds = max(0, ax - 40), max(0, ay - 35), min(plain.width, bx + 40), min(plain.height, by + 35)
        parts = [pic.crop(bounds) for pic in (framed, plain)]
        width, height = parts[0].width, parts[0].height
        scale = 2 if max(width, height) < 500 else 1
        if vertical:
            size = (max(250, 2 * (width * scale + 12)), height * scale + 54)
        else:
            size = (max(250, width * scale + 12), 2 * (height * scale + 30) + 37)
        tile = Image.new("RGB", size, "white")
        draw = ImageDraw.Draw(tile)
        draw.text((6, 4), f"{ident}  固定450 DPI  細部 {index}", font=font, fill="#222222")
        for k, pic in enumerate(parts):
            left_top = (6 + k * (width * scale + 12), 26) if vertical else (6, 26 + k * (height * scale + 30))
            px, py = left_top
            draw.text(left_top, ("枠あり", "枠なし")[k], font=font, fill="#222222")
            tile.paste(pic.resize((width * scale, height * scale), Image.Resampling.NEAREST), (px, py + 25))
        images[f"{ident}-close-{index:02d}.png"] = slots.blob(tile)
    return images


def visual(row, reference, origin, ident, font):
    width, height = row["box"][2:]
    ref = {**reference, "axis": row["allocation_axis"]}
    extra = details(ref, origin, ident, font)
    names = []
    guide = VERTICAL if ref["axis"] == "y" else HORIZONTAL + DOTS
    if ref["axis"] == "y":
        extra.update(trial.old.end_context(row, ref, ident, font))
        extra.update(trial.profile(ref, origin, ident, font))
    elif 16 <= width <= 120 and 12 <= height <= 35:
        try:
            supplemental, names, _ = slots.aid(row, ref, origin, ident, font)
        except ValueError as error:
            if "目印を使える短い枠ではない" not in str(error):
                raise
        else:
            extra.update(supplemental)
            extra.update(trial.base.framed_context(row, ref, origin, ident, font))
            guide += SHORT
    return extra, guide, names


def stage_pack(folder, name, values, archive):
    destination = folder / "cards" / name
    destination.mkdir(parents=True)
    mapping, names, hashes, row_guides = {}, [], [], []
    for ident, index, ref, guide, partitions, images in values:
        mapping[ident] = {"entry": index, "image_reference": ref, "partitions": partitions}
        row_guides.append(f"{ident}。{guide}" + (f"目印は{'、'.join(partitions)}。" if partitions else ""))
        for filename, picture in images.items():
            save_once(destination / filename, picture)
            names.append(filename)
            hashes.append(old.hashlib.sha256(picture).hexdigest())
    prompt = INTRO + "\n" + "\n".join(row_guides) + "\n" + FORMAT + "、".join(mapping) + "。"
    archive[name] = {"mapping": mapping, "request": {"images": names, "image_sha256": hashes, "ids": list(mapping), "prompt": prompt}}


def prepare(expected):
    source, selection_lock = OUT / "selection.json", population.LOCK
    selected, frozen = load(source), load(selection_lock)
    if expected != sha(source) or selected["population_lock_sha256"] != sha(selection_lock):
        raise ValueError("一度だけ抽出した結果と異なる")
    if any(sha(Path(k)) != h for k, h in frozen["inputs"].items()):
        raise ValueError("抽出前に固定した方法が変わった")
    delivery = OUT / "delivery"
    if delivery.exists():
        raise FileExistsError("同じ版に固定した配布がある")
    index, catalog = old.lookup()
    rows = list(enumerate(selected["selected"]))
    SystemRandom().shuffle(rows)
    pages = defaultdict(list)
    for i, row in rows:
        pages[row["key"]].append((i, row))
    font = old.base.FONTS / "meiryo.ttc"
    typeset = ImageFont.truetype(font, size=17)
    methods = (Path(__file__), Path(old.__file__), Path(old.layout.__file__), Path(old.original.__file__),
               trial.PREVIOUS, Path(trial.__file__), trial.base.__file__, slots.__file__, Path(trial.base.old.__file__),
               Path(old.glyph_geometry_v9.__file__), Path(old.region_images_v9.__file__), Path(old.original.v1.__file__),
               Path(old.base.__file__), source, selection_lock, font, old.CORPUS / "probe-v4/manifest.json")
    fingerprints = {str(k): sha(Path(k)) for k in methods} | frozen["inputs"]
    with tempfile.TemporaryDirectory(dir=OUT, prefix="views-") as temp:
        root = Path(temp)
        staging = root / "prepared"
        staging.mkdir()
        shadow = root / "assets"
        shadow.mkdir()
        old.original.v1.REGION = root
        old.layout.REGION = root
        old.layout.figure.REGION = root
        points, pin = {}, {}
        for key, group in pages.items():
            rendered, pinned = old.render(shadow, [(f"Z{i:04d}", row) for i, row in group], index, catalog)
            points.update(rendered)
            pin[key] = pinned
        assets = {f.resolve().as_posix(): sha(f) for f in shadow.iterdir()}
        names = {Path(f).name: digest for f, digest in assets.items()}

        def verified_asset(view, origin, kind):
            fname = next(item["image"] for item in view["images"] if item["kind"] == kind)
            path = shadow / fname
            if sha(path) != names[fname]:
                raise ValueError("作成中の確認画像が変わった")
            with Image.open(path) as image:
                return image.convert("RGB")

        slots.asset = verified_asset
        archive, buffer, count = {}, [], 0
        for i, row in rows:
            entry = points[f"Z{i:04d}"]
            ref = {"source_view": entry["asset"], "sha": pin[row["key"]]}
            for retry in range(2):
                ident = f"G{len(buffer) + 1:02d}"
                first, *_ = old.made(entry, ident, assets, typeset)
                extra, guide, parts = visual(row, ref, {"source_assets": names}, ident, typeset)
                images = first | extra
                if buffer and (len(buffer) >= 4 or count + len(images) > 24):
                    stage_pack(staging, f"pack-{len(archive):03d}", buffer, archive)
                    buffer, count = [], 0
                    continue
                if len(images) > 24:
                    name_list = list(extra)
                    discarded = max(0, len(images) - 24)
                    for remove in name_list[1:1 + discarded]:
                        del images[remove]
                    if len(images) > 24:
                        raise ValueError("一行の画像枚数が過大")
                buffer.append((ident, i, ref, guide, parts, images))
                count += len(images)
                break
            else:
                raise ValueError("空の束にも画像が入らない")
        if buffer:
            stage_pack(staging, f"pack-{len(archive):03d}", buffer, archive)
        shadow.rename(staging / "source-assets")
        if sum(len(value["mapping"]) for value in archive.values()) != len(rows):
            raise ValueError("抽出した各行の画像がそろわない")
        if any(sha(Path(k)) != h for k, h in fingerprints.items()):
            raise ValueError("配布の作成中に固定の方法が異なった")
        save_once(staging / "packages.json", encoded({"scope": "independent-audit-image-requests", "source_sha256": expected,
                  "inputs": fingerprints, "models": old.MODELS, "packs": archive, "source_assets": names}))
        staging.rename(delivery)
    print(sha(delivery / "packages.json"), len(archive), "束、", len(rows), "行を固定", flush=True)


if __name__ == "__main__":
    cli = argparse.ArgumentParser(description=__doc__)
    cli.add_argument("--selection", required=True)
    prepare(cli.parse_args().selection)
