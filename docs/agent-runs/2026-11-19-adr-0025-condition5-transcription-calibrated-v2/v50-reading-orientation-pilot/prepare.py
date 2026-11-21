"""v47の保存済みの固定画素だけで、回転・字形・直交方向の開発表示を作る。"""

import importlib.util
import io
import math
from pathlib import Path
import sys

import numpy as np
from PIL import Image, ImageDraw, ImageFont

HERE = Path(__file__).resolve().parent
BASE = HERE.parent / "v24-physical-transcription-pilot/run.py"
spec = importlib.util.spec_from_file_location("orientation_and_cross_frame_development", BASE)
pilot = importlib.util.module_from_spec(spec)
spec.loader.exec_module(pilot)
pilot.HERE = HERE
pilot.OUT = pilot.OUT.with_name("reference-v50-reading-orientation-pilot")
pilot.LOCK, pilot.RESULT = HERE / "lock.json", HERE / "result.json"
SHAPES = {
    ("kanpo1828-p3-p0001", 74): "turned-short",
    ("kanpo1828-p3-p0001", 201): "name-mismatch",
    ("kanpo1826-p4-p0001", 67): "two-strokes-mismatch",
    ("defense-p0089", 40): "orthogonal-heading-mismatch",
    ("kanpo1828-p3-p0001", 144): "name-difference",
    ("kanpo1828-p3-p0001", 164): "name-difference",
    ("kanpo1828-p3-p0001", 190): "vertical-bars",
    ("kanpo1826-p4-p0001", 46): "kana-or-mouth",
    ("kanpo1827-p2-p0001", 51): "complex-component",
    ("disaster-p0107", 26): "zero-or-period",
    ("kanpo1826-p5-p0001", 284): "orthogonal-neighbor",
    ("kanpo1827-p2-p0001", 119): "short-unreadable",
    ("kanpo1826-p5-p0001", 259): "reading-order",
    ("kanpo1828-p3-p0001", 47): "control-vertical-punctuation",
    ("kanpo1828-p3-p0001", 52): "control-vertical-small-kana",
    ("wp-summary-p0004", 4): "control-horizontal-bullets",
}
VERTICAL = (
    "字が横倒しに印刷されている短い枠の場合だけ、固定画素を90度回した同じ像で字を確認します。"
    "元の枠への所属と読む順は元の位置で考え、回転した像から隣の列を追加しません。"
    "縦の字の拡大では、同じ列に似た字があれば各画の端・長さ・傾きを比較します。"
    "「ニ」と「二」、「ロ」と「口」などは、語に合うかだけで決めず、その字体の輪郭に従います。"
    "山偏の右上が立の形ならその形を確認し、大の形と取り違えません。"
    "異体字は画を確認し、現在よく見かける字体へ置き換えません。"
)
HORIZONTAL = (
    "上下の枠端の画像では、奥行きの位置は固定450 DPIの画素単位です。"
    "濃さの違う二つの計測に共通したインクの帯だけに範囲を表示します。"
    "枠内にわずかに帯が見えても、インク上下の中心が範囲外の字は写しません。"
    "帯の範囲は本文や文字数を示しません。枠端に複数の字がある場合は個々の字の中心を確認し、"
    "枠の外の画を隣の行から追加しません。"
)


def blob(image):
    buffer = io.BytesIO()
    image.save(buffer, "PNG")
    return buffer.getvalue()


def cropped(image, rectangle, horizontal_pad, vertical_pad):
    x, y, r, b = rectangle
    left = max(0, math.floor(x - horizontal_pad))
    top = max(0, math.floor(y - vertical_pad))
    right = min(image.width, math.ceil(r + horizontal_pad))
    bottom = min(image.height, math.ceil(b + vertical_pad))
    return image.crop((left, top, right, bottom)).convert("RGB"), (left, top)


def turned(image, rect, ident, font):
    body, _ = cropped(image, rect, 8, 8)
    variants = (("元の向き", body), ("左に90度", body.transpose(Image.Transpose.ROTATE_90)),
                ("右に90度", body.transpose(Image.Transpose.ROTATE_270)))
    width = sum(p.width * 2 + 10 for _, p in variants)
    height = 53 + max(p.height * 2 for _, p in variants)
    result = Image.new("RGB", (max(360, width), height), "white")
    draw = ImageDraw.Draw(result)
    draw.text((4, 4), f"{ident}　固定450 DPI　短い枠の字の向き", font=font, fill="#202020")
    x = 5
    for label, tile in variants:
        draw.text((x, 27), label, font=font, fill="#202020")
        result.paste(tile.resize((2 * tile.width, 2 * tile.height), Image.Resampling.NEAREST), (x, 48))
        x += 2 * tile.width + 10
    return blob(result)


def vertical(image, rect, ident, font):
    body, _ = cropped(image, rect, 7, 9)
    spans = []
    for start in range(0, body.height, 220):
        if spans and spans[-1][1] == body.height:
            break
        spans.append((max(0, start - 10), min(body.height, start + 230)))
    cells, panel = 5, {}
    column_width = max(120, body.width * 2 + 9)
    for n, first in enumerate(range(0, len(spans), cells), 1):
        window = spans[first:first + cells]
        result = Image.new("RGB", (column_width * len(window), 55 + max(b - a for a, b in window) * 2), "white")
        draw = ImageDraw.Draw(result)
        draw.text((4, 3), f"{ident}　固定450 DPI　列の字形 {n}", font=font, fill="#202020")
        for i, (top, bottom) in enumerate(window):
            offset = column_width * i + 4
            draw.text((offset, 26), f"区間 {first + i + 1}", font=font, fill="#202020")
            segment = body.crop((0, top, body.width, bottom))
            result.paste(segment.resize((segment.width * 2, segment.height * 2), Image.Resampling.NEAREST), (offset, 50))
        panel[f"{ident}-column-shapes-{n:02d}.png"] = blob(result)
    return panel


def ink_bands(gray, x, y, end, bottom):
    l, r = max(0, math.ceil(x)), min(gray.shape[1], math.floor(end))
    t, b = max(0, math.floor(y - 48)), min(gray.shape[0], math.ceil(bottom + 48))
    raw = gray[t:b, l:r]
    bands = []
    if not raw.size:
        return bands
    for cutoff in (140, 186):
        dark = raw < cutoff
        # 縦罫のように計測の高さの大半を通る列は、文字の帯の計測から外す。
        use = dark[:, dark.mean(axis=0) < .70]
        active = use.sum(axis=1) >= max(2, math.ceil(use.shape[1] * .011))
        hits = np.flatnonzero(active)
        groups = np.split(hits, np.where(np.diff(hits) > 3)[0] + 1)
        current = [(int(a[0]) + t, int(a[-1]) + t + 1) for a in groups if len(a) >= 5]
        bands.append(current)
    stable = []
    for curr in bands[1]:
        overlap = [prior for prior in bands[0] if max(abs(a - b) for a, b in zip(curr, prior, strict=True)) <= 2]
        if len(overlap) == 1 and curr[0] < bottom + 25 and curr[1] > y - 25:
            stable.append(curr)
    return stable


def cross_frame(image, rect, ident, font):
    x, y, r, b = rect
    center = (x + r) / 2
    window = (max(x, center - 248), y, min(r, center + 248), b)
    body, (_, top) = cropped(image, window, 11, 44)
    factor = 2
    width, height = body.width * factor, body.height * factor
    gray = np.array(image.convert("L"))
    bands = ink_bands(gray, x, y, r, b)
    result = Image.new("RGB", (max(465, width + 30), height + 88 + 23 * len(bands)), "white")
    draw = ImageDraw.Draw(result)
    draw.text((4, 3), f"{ident}　固定450 DPI　枠の上下端と中央の像", font=font, fill="#202020")
    draw.text((4, 26), "上下の位置は元の枠の上端を0とする450 DPIの画素", font=font, fill="#202020")
    result.paste(body.resize((width, height), Image.Resampling.NEAREST), (13, 54))
    for edge in (y, b):
        pos = 54 + round((edge - top) * factor)
        draw.line((3, pos, 12, pos), fill="#ad271f", width=2)
        draw.line((width + 13, pos, width + 23, pos), fill="#ad271f", width=2)
    draw.text((4, height + 58), f"枠の上下範囲  0.0 から {b-y:.1f}", font=font, fill="#802821")
    for k, (a, z) in enumerate(bands):
        center = (a + z) / 2 - y
        draw.text((4, height + 83 + k * 23), f"帯  {a-y:+.1f} から {z-y:+.1f}　中心 {center:+.1f}",
                  font=font, fill="#20447a")
    return blob(result)


def snapshot():
    audit = pilot.audit
    sys.path.insert(0, str(HERE.parent / "v47-reference-audit"))
    import official
    core = official.core
    core.verify_methods()
    path = core.OUT / "delivery"
    package_file, selection = path / "packages.json", core.OUT / "selection.json"
    data, rows = core.load(package_file), core.load(selection)["selected"]
    preview = official.audit.verify_delivery(core.sha(package_file))
    if preview["rows"] != 376:
        raise ValueError("開発元の固定配布が異なる")
    font_file = core.previous.packets.old.base.FONTS / "meiryo.ttc"
    font = ImageFont.truetype(font_file, size=17)
    refs, mapping, jobs = [], {}, {}
    pins = {str(f): audit.sha(f) for f in (Path(__file__), BASE, HERE / "protocol.md", package_file, selection, font_file,
                                          HERE.parent / "v47-reference-audit/provisional-before-last-vote.json",
                                          Path(official.__file__))}
    display = pilot.OUT / "display"
    for name, packet in data["packs"].items():
        (ident, item), = packet["mapping"].items()
        row = rows[item["entry"]]
        key = (row["key"], row["line_index"])
        if key not in SHAPES:
            continue
        targets = {value["text"] for value in row["targets"].values() if value["known"]}
        if len(targets) != 1:
            raise ValueError("開発の比較に一意な既存正解がない")
        ref = {**row, "effective": targets.pop()}
        high = item["image_reference"]["source_view"]["views"][1]
        f = next(v["image"] for v in high["images"] if v["kind"] == "plain")
        fixed = path / "source-assets" / f
        if audit.sha(fixed) != data["source_assets"][f]:
            raise ValueError("開発元の固定450 DPIの画像が異なる")
        original = packet["request"]
        guide, split, close = original["prompt"].partition(audit.packets.FORMAT)
        if not split:
            raise ValueError("既存の回答形式が異なる")
        with Image.open(fixed) as image:
            rect = high["target_rectangle"]
            if row["allocation_axis"] == "x":
                extra, instructions = {f"{ident}-cross-frame.png": cross_frame(image, rect, ident, font)}, HORIZONTAL
            else:
                extra, instructions = vertical(image, rect, ident, font), VERTICAL
                if row["box"][3] <= 120:
                    extra = {f"{ident}-turn-preview.png": turned(image, rect, ident, font)} | extra

        tag = f"case-{len(mapping):02d}"
        base_cards = path / "cards" / name
        saved = {
            label: (base_cards / label).read_bytes()
            for label in original["images"]
        }
        if [audit.readers.sha(img) for img in saved.values()] != original["image_sha256"]:
            raise ValueError("画像二票で実際に確認した同じ表示を再現できない")
        all_cards = saved | extra
        if len(all_cards) > 24:
            raise ValueError("比較のため既存画像と追加表示を全て添付する")
        cards = display / "cards" / tag
        cards.mkdir(parents=True)
        for label, img in all_cards.items():
            audit.save_once(cards / label, img)
        mapping[tag] = {**item, "entry": len(refs), "category": SHAPES[key], "baseline_packet": name}
        jobs[tag + "/new"] = {"cards": str(cards), "request": {**original, "images": list(all_cards),
            "image_sha256": [audit.readers.sha(img) for img in all_cards.values()],
            "prompt": guide + instructions + split + close}}
        refs.append(ref)
        pins.update({str(fixed): audit.sha(fixed)})
    if len(refs) != len(SHAPES):
        raise ValueError("固定した開発試験の対象が揃わない")
    out = display / "selection.json"
    audit.save_once(out, audit.encoded({"selected": refs}))
    pins[str(out)] = audit.sha(out)
    pilot.SAMPLES = refs
    return {"jobs": jobs, "mapping": mapping, "files": pins}


if __name__ == "__main__":
    pilot.snapshot = snapshot
    pilot.main()
