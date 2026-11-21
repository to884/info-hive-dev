"""行頭の色付き・黒の丸と本文中の小点を周囲の固定PNGで区別する。"""

import importlib.util
import io
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont

HERE = Path(__file__).resolve().parent
BASE = HERE.parent / "v24-physical-transcription-pilot/run.py"
spec = importlib.util.spec_from_file_location("paragraph_bullet_reader", BASE)
pilot = importlib.util.module_from_spec(spec)
spec.loader.exec_module(pilot)
pilot.HERE = HERE
pilot.OUT = pilot.OUT.with_name("reference-v41-paragraph-bullets-pilot")
pilot.LOCK, pilot.RESULT = HERE / "lock.json", HERE / "result.json"
SAMPLES = {
    ("wp-point-p0001", 15): "black-paragraph-bullet", ("defense-p0042", 11): "colored-paragraph-bullet",
    ("defense-p0107", 22): "small-leading-control", ("defense-p0453", 46): "repeated-colored-control",
    ("wp-summary-p0004", 8): "legend-control", ("wp-summary-p0010", 5): "square-control",
    ("defense-p0136", 79): "interior-small-control",
}
GUIDE = (
    "行頭の丸は周囲の150 DPIで、他の段落の項目丸と同じ位置に並ぶかを確認します。"
    "色付きの丸が同じ段落位置に繰り返し、直後に本文が始まる場合は欄の箇条書きです。"
    "黒い丸も、前後の項目とそろい、本文の字より間をあけて独立した同じ大きさの塗り丸なら「●」です。"
    "本文の文字と同じ並びに置かれた小さい丸や、見える形から字種が決まらない丸は、同じ中心を2回書く round とします。"
    "点だけの色見本は凡例の周囲を確認して除き、ありそうな箇条書き記号を補いません。"
)


def margin(png, box, label, font):
    x, y, w, h = box
    with Image.open(png) as im:
        l, t, r, b = max(0, x - 19), max(0, y - 98), min(im.width, x + 108), min(im.height, y + h + 98)
        raw = im.crop((l, t, r, b)).convert("RGB")
    scale = 3
    view = raw.resize((raw.width * scale, raw.height * scale), Image.Resampling.NEAREST)
    tile = Image.new("RGB", (max(290, view.width + 20), view.height + 43), "white")
    tile.paste(view, (8, 32))
    draw = ImageDraw.Draw(tile)
    draw.text((6, 4), f"{label}　行頭と近くの段落　固定150 DPI", fill="#222222", font=font)
    draw.rectangle((8 + (x - l) * scale, 32 + (y - t) * scale,
                    8 + (min(x+w, r) - l) * scale - 1, 32 + (y+h-t) * scale - 1), outline="#d11226")
    buf = io.BytesIO()
    tile.save(buf, "PNG")
    return buf.getvalue()


def snapshot():
    a = pilot.audit
    formal = a.OUT.with_name("reference-audit-v27")
    arc = formal / "delivery"
    packages = arc / "packages.json"
    manifest = a.load(packages)
    old = a.load(formal / "selection.json")["selected"]
    v37 = HERE.parent / "v37-transcription-final-pilot/lock.json"
    compare = a.load(v37)
    v37root = pilot.OUT.with_name("reference-v37-transcription-final-pilot")
    high = a.load(v37root / "display/selection.json")["selected"]
    labels = a.LABELS.with_name("v38-reference-candidate") / "public.json"
    known = {(r["key"], r["line_index"]): r for r in a.load(labels) if (r["key"], r["line_index"]) in SAMPLES}
    font_file = a.packets.old.base.FONTS / "meiryo.ttc"
    font = ImageFont.truetype(font_file, size=17)
    scans = {}
    for n, pack in manifest["packs"].items():
        ident, = pack["mapping"]
        model = pack["mapping"][ident]
        r = old[model["entry"]]
        k = r["key"], r["line_index"]
        if k in SAMPLES:
            scans[k] = (arc / "cards" / n, pack["request"], model)
    for name, item in compare["jobs"].items():
        hist = compare["mapping"][name.split("/")[0]]
        r = high[hist["entry"]]
        k = r["key"], r["line_index"]
        if k in SAMPLES and k not in scans:
            if "image_reference" not in hist:
                raise ValueError("開発画像の枠を確認できない")
            scans[k] = (Path(item["cards"]), item["request"], hist)
    if set(scans) != set(known) or set(scans) != SAMPLES.keys():
        raise ValueError("先に固定した試験の対象がそろわない")
    rows, mapping, jobs = [], {}, {}
    files = (Path(__file__), BASE, HERE / "protocol.md", packages, formal / "selection.json", v37,
             v37root / "display/selection.json", font_file, labels, HERE.parent / "v22-list-mark-pilot/recover.py")
    pins = {str(p): a.sha(p) for p in files}
    for k, (path, req, binding) in scans.items():
        row = known[k]
        index = f"case-{len(rows):02d}"
        ident, = req["ids"]
        image = a.packets.old.CORPUS / "probe-v4/png" / (k[0] + ".png")
        if a.sha(image) != binding["image_reference"]["sha"]["150_dpi"]:
            raise ValueError("周囲の固定画像が同じ頁と結び付かない")
        tile = margin(image, row["box"], ident, font)
        prefix, sep, end = req["prompt"].partition(a.packets.FORMAT)
        if not sep:
            raise ValueError("回答形式が確認できない")
        folder = pilot.OUT / "display/cards" / index
        folder.mkdir(parents=True)
        first = ident + "-paragraph-margin.png"
        assets = {first: tile}
        for f, digest in zip(req["images"], req["image_sha256"], strict=True):
            b = (path / f).read_bytes()
            if a.readers.sha(b) != digest:
                raise ValueError("同じ試験に添付した画像が変化")
            if f != ident + "-border-1.png":
                assets[f] = b
        if len(assets) > 24:
            raise ValueError("同じ枠の周囲を示す添付が収まらない")
        for f, raw in assets.items():
            a.save_once(folder / f, raw)
        jobs[index + "/new"] = {"cards": str(folder), "request": {**req, "prompt": prefix + GUIDE + sep + end,
            "images": list(assets), "image_sha256": [a.readers.sha(b) for b in assets.values()]}}
        mapping[index] = {**binding, "entry": len(rows), "category": SAMPLES[k]}
        rows.append(row)
        pins[str(image)] = a.sha(image)
    data = pilot.OUT / "display/selection.json"
    a.save_once(data, a.encoded({"selected": rows}))
    pins[str(data)] = a.sha(data)
    pilot.SAMPLES = rows
    return {"jobs": jobs, "mapping": mapping, "files": pins}


if __name__ == "__main__":
    pilot.snapshot = snapshot
    pilot.main()
