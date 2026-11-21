"""固定画素の枠端を、内側と外側の位置が分かる二つの倍率で確認する。"""

import importlib.util
import io
import math
from pathlib import Path

import numpy as np
from PIL import Image, ImageDraw, ImageFont

HERE = Path(__file__).resolve().parent
BASE = HERE.parent / "v24-physical-transcription-pilot/run.py"
spec = importlib.util.spec_from_file_location("frame_edge_transcription_pilot", BASE)
pilot = importlib.util.module_from_spec(spec)
spec.loader.exec_module(pilot)
pilot.HERE = HERE
pilot.OUT = pilot.OUT.with_name("reference-v40-frame-edge-pilot")
pilot.LOCK, pilot.RESULT = HERE / "lock.json", HERE / "result.json"
SAMPLES = {
    ("defense-p0391", 52): "horizontal-comma", ("defense-p0269", 18): "horizontal-comma",
    ("kanpo1828-p2-p0001", 48): "vertical-punctuation", ("kanpo1828-p3-p0001", 47): "vertical-punctuation",
    ("kanpo1828-p3-p0001", 4): "vertical-punctuation", ("kanpo1827-p2-p0001", 12): "vertical-punctuation",
    ("kanpo1826-p5-p0001", 26): "neighbor", ("kanpo1826-p5-p0001", 284): "neighbor",
    ("kanpo1827-p2-p0001", 146): "control-vertical-word", ("kanpo1828-p3-p0001", 224): "control-neighbor",
    ("wp-summary-p0004", 4): "control-horizontal-punctuation",
}
GUIDE = (
    "最初に枠端の画像で、着色していない側に、字や句読点のインクの長さがどれだけ入るかを見ます。"
    "色を付けた外側との境目に点や読点がある場合、元画像の同じ字の両端を確認し、"
    "割当軸の全幅または全高に対して枠内の分が少なくとも半分あり、直交方向で中心が枠内にある字だけを写します。"
    "細い端がわずかに枠内にある読点も、元画像の字全体を基準にします。"
    "上の本文を読んで自然に思える句読点でも、画素と枠への所属を確かめた場合だけ写します。"
)


def crop_bounds(im, rect, axis, side, dpi):
    x, y, right, lower = rect
    scale = dpi / 150
    if axis == "x":
        end = x if side == "start" else right
        span = (end - (18 if side == "start" else 42) * scale, y - 4 * scale,
                end + (42 if side == "start" else 18) * scale, lower + 4 * scale)
    else:
        end = y if side == "start" else lower
        span = (x - 6 * scale, end - (18 if side == "start" else 42) * scale,
                right + 6 * scale, end + (42 if side == "start" else 18) * scale)
    return (max(0, math.floor(span[0])), max(0, math.floor(span[1])),
            min(im.width, math.ceil(span[2])), min(im.height, math.ceil(span[3])))


def panel(im, rect, axis, side, dpi, font):
    l, t, r, b = crop_bounds(im, rect, axis, side, dpi)
    raw = im.crop((l, t, r, b)).convert("RGB")
    magnification = 7 if dpi == 150 else 2
    pixels = raw.resize((raw.width * magnification, raw.height * magnification), Image.Resampling.NEAREST)
    expanded = np.array(pixels)
    height, width = expanded.shape[:2]
    x0, y0, x1, y1 = rect
    loc = np.arange(width if axis == "x" else height) + .5
    offset = l if axis == "x" else t
    first, last = (x0, x1) if axis == "x" else (y0, y1)
    inside = (first <= loc / magnification + offset) & (loc / magnification + offset < last)
    if axis == "x":
        expanded[:, ~inside] = expanded[:, ~inside] / 3 + np.array([255, 170, 128], dtype=float) * (2 / 3)
    else:
        expanded[~inside, :] = expanded[~inside, :] / 3 + np.array([255, 170, 128], dtype=float) * (2 / 3)
    tile = Image.new("RGB", (max(280, 2 * width + 22), height + 35), "white")
    draw = ImageDraw.Draw(tile)
    for x, label, image in ((5, f"{dpi} DPI 外側に色", Image.fromarray(expanded)),
                            (width + 16, "同じ元画像", pixels)):
        draw.text((x, 3), label, font=font, fill="#222222")
        tile.paste(image, (x, 28))
    return tile


def supplement(low, rectlow, high, recthigh, axis, label, font):
    out = {}
    for side, caption in (("start", "行頭"), ("end", "行末")):
        pieces = [panel(im, rect, axis, side, dpi, font)
                  for im, rect, dpi in ((low, rectlow, 150), (high, recthigh, 450))]
        width, height = max(p.width for p in pieces), sum(p.height for p in pieces)
        tile = Image.new("RGB", (width, height + 30), "white")
        ImageDraw.Draw(tile).text((7, 3), f"{label}　{caption}の枠端", font=font, fill="#222222")
        dy = 25
        for p in pieces:
            tile.paste(p, (0, dy))
            dy += p.height
        buf = io.BytesIO()
        tile.save(buf, "PNG")
        out[f"{label}-edge-{side}.png"] = buf.getvalue()
    return out


def snapshot():
    a = pilot.audit
    formal = a.OUT.with_name("reference-audit-v27")
    root = formal / "delivery"
    manifest = root / "packages.json"
    receipt = root / "received.json"
    score = HERE.parent / "v27-reference-audit/result.json"
    earlier = a.load(score)
    if earlier["receipts_sha256"] != a.sha(receipt) or a.load(receipt)["packages_sha256"] != a.sha(manifest):
        raise ValueError("確定した旧の監査と表示の来歴が一致しない")
    stored = a.load(manifest)
    selections = a.load(formal / "selection.json")["selected"]
    labels = a.LABELS.with_name("v38-reference-candidate") / "public.json"
    chosen = {k: r for r in a.load(labels)
              if (k := (r["key"], r["line_index"])) in SAMPLES}
    font_file = a.packets.old.base.FONTS / "meiryo.ttc"
    font = ImageFont.truetype(font_file, size=17)
    rows, mapping, jobs = [], {}, {}
    pins = {str(p): a.sha(p) for p in (manifest, receipt, score, formal / "selection.json", font_file, labels,
                                       Path(__file__), BASE, HERE / "protocol.md",
                                       HERE.parent / "v22-list-mark-pilot/recover.py")}
    for pack, item in stored["packs"].items():
        (label, info), = item["mapping"].items()
        row = selections[info["entry"]]
        key = row["key"], row["line_index"]
        if key not in chosen:
            continue
        row = chosen[key]
        if row["effective"] is None:
            raise ValueError("対照の既存正解がない")
        bound = info["image_reference"]["sha"]
        high = info["image_reference"]["source_view"]["views"][1]
        old_name = next(v["image"] for v in high["images"] if v["kind"] == "plain")
        raw_high = root / "source-assets" / old_name
        raw_low = a.packets.old.CORPUS / "probe-v4/png" / (row["key"] + ".png")
        if a.sha(raw_low) != bound["150_dpi"] or a.sha(raw_high) != stored["source_assets"][old_name]:
            raise ValueError("固定した枠の画像が変化")
        x, y, w, h = row["box"]
        with Image.open(raw_low) as low, Image.open(raw_high) as far:
            more = supplement(low, (x, y, x + w, y + h), far, high["target_rectangle"],
                              row["allocation_axis"], label, font)
        request = item["request"]
        note, sep, end = request["prompt"].partition(a.packets.FORMAT)
        if not sep:
            raise ValueError("正式な配布の回答形式が変化")
        tag = f"case-{len(rows):02d}"
        folder = pilot.OUT / "display/cards" / tag
        folder.mkdir(parents=True)
        for filename, h in zip(request["images"], request["image_sha256"], strict=True):
            earlier_path = root / "cards" / pack / filename
            asc = earlier_path.read_bytes()
            if a.readers.sha(asc) != h:
                raise ValueError("旧指示の表示と固定の違い")
            if "-border-" not in filename:
                more[filename] = asc
        if len(more) > 24:
            raise ValueError("枠端の表示と固定の添付が上限を超える")
        for name, blob in more.items():
            a.save_once(folder / name, blob)
        mapping[tag] = {**info, "entry": len(rows), "category": SAMPLES[key], "baseline_packet": pack}
        rows.append(row)
        jobs[tag + "/new"] = {"cards": str(folder), "request": {**request, "images": list(more),
            "image_sha256": [a.readers.sha(b) for b in more.values()], "prompt": note + GUIDE + sep + end}}
        pins.update({str(raw_low): a.sha(raw_low), str(raw_high): a.sha(raw_high)})
    if len(rows) != len(SAMPLES):
        raise ValueError("正式監査の旧票を持つ開発対象と対照に不足")
    document = pilot.OUT / "display/selection.json"
    a.save_once(document, a.encoded({"selected": rows}))
    pins[str(document)] = a.sha(document)
    pilot.SAMPLES = rows
    return {"jobs": jobs, "mapping": mapping, "files": pins}


if __name__ == "__main__":
    pilot.snapshot = snapshot
    pilot.main()
