"""似た字の見本を別に示し、固定画像の筆画を全文の転記に結び付ける。"""

import importlib.util
import io
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont

HERE = Path(__file__).resolve().parent
BASE = HERE.parent / "v24-physical-transcription-pilot/run.py"
spec = importlib.util.spec_from_file_location("glyph_reference_pilot", BASE)
pilot = importlib.util.module_from_spec(spec)
spec.loader.exec_module(pilot)
pilot.HERE = HERE
pilot.OUT = pilot.OUT.with_name("reference-v42-glyph-reference-pilot")
pilot.LOCK, pilot.RESULT = HERE / "lock.json", HERE / "result.json"
SAMPLES = {
    ("kanpo1828-p3-p0001", 225): "bar", ("kanpo1827-p2-p0001", 48): "bar",
    ("kanpo1826-p5-p0001", 245): "top-bars", ("kanpo1826-p4-p0001", 46): "kana-or-box",
    ("kanpo1828-p3-p0001", 52): "small-kana", ("kanpo1828-p3-p0001", 144): "name",
    ("kanpo1828-p3-p0001", 164): "name", ("kanpo1828-p3-p0001", 201): "name",
    ("disaster-p0173", 27): "blade-dot", ("kanpo1827-p2-p0001", 407): "control-numbers",
    ("kanpo1828-p3-p0001", 202): "control-short", ("kanpo1828-p3-p0001", 122): "control-code",
}
EXAMPLES = (
    (("未", "上の横画が短い"), ("末", "上の横画が長い")),
    (("口", "漢字のくち"), ("ロ", "仮名のロ")),
    (("つ", "通常のかな"), ("っ", "小さいかな")),
    (("崎", "右に大と可"), ("﨑", "右に立の形と可")),
    (("迨", "しんにょうに台"), ("追", "しんにょうに𠂤")),
    (("靱", "刃の点の位置"), ("靭", "刄の点の位置")),
    (("―", "横の区切り線"), ("ー", "仮名の長音")),
    (("治", "三水に台"), ("逌", "しんにょうに卣")),
)
GUIDE = (
    "『字形の対照』は、本文に含まれない部品の見本です。長い全文を確認するときも、"
    "見分けにくい字は固定450 DPIの筆画を拡大し、横画の長さ、斜線の交差、点の位置、仮名の大きさを一つずつ照らします。"
    "漢数字の間などの区切りに置かれた線と、仮名に続く長音は、画素の形と縦列の位置を確かめて区別します。"
    "どちらかの形が見えた場合だけその字を写します。対照の文字を自然な語へ書き換えるために使いません。"
)


def example_card(typeface):
    primary = ImageFont.truetype(typeface, size=49)
    legend = ImageFont.truetype(typeface, size=15)
    tile = Image.new("RGB", (920, 424), "white")
    draw = ImageDraw.Draw(tile)
    draw.text((9, 7), "字形の対照　見本", font=legend, fill="#222222")
    for i, pair in enumerate(EXAMPLES):
        x, y = (i % 2) * 460, (i // 2) * 96 + 28
        for j, (char, cue) in enumerate(pair):
            left = x + j * 225 + 9
            draw.rectangle((left, y, left + 218, y + 87), outline="#757575", fill="#fafafa")
            draw.text((left + 6, y + 7), char, font=primary, fill="#171717")
            draw.text((left + 70, y + 25), cue, font=legend, fill="#171717")
    stream = io.BytesIO()
    tile.save(stream, "PNG")
    return stream.getvalue()


def snapshot():
    a = pilot.audit
    root = a.OUT.with_name("reference-audit-v27") / "delivery"
    packages = root / "packages.json"
    archive = root / "received.json"
    score = HERE.parent / "v27-reference-audit/result.json"
    if a.load(score)["receipts_sha256"] != a.sha(archive) or a.load(archive)["packages_sha256"] != a.sha(packages):
        raise ValueError("比較元の正式監査の原票と配布を確認できない")
    selection = root.parent / "selection.json"
    original = a.load(selection)["selected"]
    labels = a.LABELS.with_name("v38-reference-candidate") / "public.json"
    known = {k: r for r in a.load(labels) if (k := (r["key"], r["line_index"])) in SAMPLES}
    font_file = a.packets.old.base.FONTS / "meiryo.ttc"
    chart = example_card(font_file)
    labels_ref, jobs, rows = {}, {}, []
    for pack, record in a.load(packages)["packs"].items():
        ident, = record["mapping"]
        detail = record["mapping"][ident]
        r = original[detail["entry"]]
        key = r["key"], r["line_index"]
        if key not in SAMPLES:
            continue
        request = record["request"]
        prefix, sep, end = request["prompt"].partition(a.packets.FORMAT)
        if not sep or len(request["images"]) >= 24:
            raise ValueError("既定の回答と対照の画像を一緒に渡せない")
        tag = f"case-{len(rows):02d}"
        cards = pilot.OUT / "display/cards" / tag
        cards.mkdir(parents=True)
        name = ident + "-glyph-examples.png"
        a.save_once(cards / name, chart)
        for keyname, digest in zip(request["images"], request["image_sha256"], strict=True):
            blob = (root / "cards" / pack / keyname).read_bytes()
            if a.readers.sha(blob) != digest:
                raise ValueError("元の監査に添付した画像が変化")
            a.save_once(cards / keyname, blob)
        jobs[tag + "/new"] = {"cards": str(cards), "request": {**request, "prompt": prefix + GUIDE + sep + end,
                "images": [name] + request["images"], "image_sha256": [a.readers.sha(chart)] + request["image_sha256"]}}
        labels_ref[tag] = {**detail, "entry": len(rows), "category": SAMPLES[key], "prior_pack": pack}
        rows.append(known[key])
    if len(rows) != len(SAMPLES):
        raise ValueError("既存の固定画像を用意できなかった字がある")
    selected = pilot.OUT / "display/selection.json"
    a.save_once(selected, a.encoded({"selected": rows}))
    files = (Path(__file__), BASE, HERE / "protocol.md", packages, archive, score, selection, labels, selected,
             font_file, HERE.parent / "v22-list-mark-pilot/recover.py")
    pilot.SAMPLES = rows
    return {"jobs": jobs, "mapping": labels_ref, "files": {str(f): a.sha(f) for f in files}}


if __name__ == "__main__":
    pilot.snapshot = snapshot
    pilot.main()
