"""列の先頭の筆画を、固定450 DPIから名称の続きなしで大きく示す。"""

import importlib.util
import io
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont

HERE = Path(__file__).resolve().parent
BASE = HERE.parent / "v34-glyph-part-pilot/prepare.py"
spec = importlib.util.spec_from_file_location("glyph_detail_transcription", BASE)
old = importlib.util.module_from_spec(spec)
spec.loader.exec_module(old)
pilot = old.pilot
pilot.HERE = HERE
pilot.OUT = pilot.OUT.with_name("reference-v36-glyph-detail-pilot")
pilot.LOCK, pilot.RESULT = HERE / "lock.json", HERE / "result.json"
PREVIOUS = HERE.parent / "v34-glyph-part-pilot"
old_root = pilot.OUT.with_name("reference-v34-glyph-part-pilot")
GUIDE = (
    "先頭の筆画を示す短い画像を先に見て、右半分の上部を拡大して確認します。"
    "斜線が交差する大の形と、短い縦画・横画が組み合わさる立の形を、下が「可」で共通する場合も分けます。"
    "山と可がある字は、上が立なら ⟦glyph:yama-ritsu-ka⟧、大なら ⟦glyph:yama-dai-ka⟧ を必ず使います。"
    "続けて全文を転記し、枠の下端で切れている場合は枠内の字だけを数えます。短い画像と全文に重なる字は一度だけ書きます。"
)


def enlarged(png, rectangle, label, font):
    x, y, r, b = map(round, rectangle)
    with Image.open(png) as im:
        crop = im.crop((max(0, x - 3), max(0, y - 4), min(im.width, r + 3), min(b, y + 127))).convert("RGB")
    mag = 4
    view = crop.resize((crop.width * mag, crop.height * mag), Image.Resampling.NEAREST)
    text = ImageFont.truetype(font, size=17)
    result = Image.new("RGB", (max(340, view.width + 24), view.height + 49), "white")
    draw = ImageDraw.Draw(result)
    draw.text((8, 5), f"{label}　先頭の筆画　固定450 DPI", fill="#222222", font=text)
    result.paste(view, (12, 33))
    stream = io.BytesIO()
    result.save(stream, "PNG")
    return stream.getvalue()


def snapshot():
    audit = pilot.audit
    manifest = PREVIOUS / "lock.json"
    plan = audit.load(manifest)
    if any(audit.sha(Path(key)) != h for key, h in plan["files"].items()):
        raise ValueError("前に固定した添付の来歴が異なる")
    display = pilot.OUT / "display"
    display.mkdir(parents=True)
    prior = old_root / "display/selection.json"
    selection = display / "selection.json"
    audit.save_once(selection, prior.read_bytes())
    font = audit.packets.old.base.FONTS / "meiryo.ttc"
    rows = audit.load(selection)["selected"]
    new, pinned = {}, {}
    for name, item in plan["jobs"].items():
        case = name.split("/")[0]
        row = rows[plan["mapping"][case]["entry"]]
        pkt = Path(item["cards"])
        src = pkt.parent.parent
        pack = src / "packages.json"
        stored = audit.load(pack)
        request = item["request"]
        label, = request["ids"]
        view = stored["packs"][pkt.name]["mapping"][label]["image_reference"]["source_view"]["views"][1]
        file = next(v["image"] for v in view["images"] if v["kind"] == "plain")
        raw = src / "source-assets" / file
        if audit.sha(raw) != stored["source_assets"][file] or row["allocation_axis"] != "y":
            raise ValueError("先頭の筆画を示す450 DPIの入力が固定枠と異なる")
        tile = enlarged(raw, view["target_rectangle"], label, font)
        if len(request["images"]) >= 24:
            raise ValueError("固定した画像と先頭の拡大を一束に収められない")
        prefix, sep, end = request["prompt"].partition(audit.packets.FORMAT)
        if not sep:
            raise ValueError("先に固定した回答形式が異なる")
        folder = display / "cards" / case
        folder.mkdir(parents=True)
        pic = label + "-head-strokes.png"
        audit.save_once(folder / pic, tile)
        for filename, digest in zip(request["images"], request["image_sha256"], strict=True):
            data = (pkt / filename).read_bytes()
            if audit.readers.sha(data) != digest:
                raise ValueError("全体を確認する添付に変化")
            audit.save_once(folder / filename, data)
        new[name] = {"cards": str(folder), "request": {**request,
                      "images": [pic] + request["images"], "image_sha256": [audit.readers.sha(tile)] + request["image_sha256"],
                      "prompt": prefix + GUIDE + sep + end}}
        pinned[str(raw)], pinned[str(pack)] = audit.sha(raw), audit.sha(pack)
    pilot.SAMPLES = rows
    methods = (Path(__file__), BASE, HERE / "protocol.md", manifest, font, selection, prior)
    pinned.update({str(f): audit.sha(f) for f in methods})
    return {"jobs": new, "mapping": plan["mapping"], "files": plan["files"] | pinned}


if __name__ == "__main__":
    pilot.reference.decoded = old.decoded
    pilot.snapshot = snapshot
    pilot.main()
