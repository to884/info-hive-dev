"""固定画素から目盛りだけを変更し、同じ符号を指す座標の一致を比べる。"""

import importlib.util
from pathlib import Path

from ruler import cards

HERE = Path(__file__).resolve().parent
BASE = HERE.parent / "v24-physical-transcription-pilot/run.py"
BEFORE = HERE.parent / "v33-horizontal-guide-pilot"
spec = importlib.util.spec_from_file_location("ruler_transcription_pilot", BASE)
pilot = importlib.util.module_from_spec(spec)
spec.loader.exec_module(pilot)
pilot.HERE = HERE
old = pilot.OUT.with_name("reference-v33-horizontal-guide-pilot")
pilot.OUT = pilot.OUT.with_name("reference-v35-coordinate-pilot")
pilot.LOCK, pilot.RESULT = HERE / "lock.json", HERE / "result.json"
GROUPS = {"square", "body-and-round", "trails", "round", "small-mark", "arrow-and-small-mark", "legend", "colored-bullet"}
GUIDE = (
    "横座標の拡大では大目盛りの各数字が枠の左からの座標です。数字の間隔は10画素、番号のない小目盛りは中間の5画素です。"
    "点と同じ縦線に来る目盛りを上下で見比べ、数字は印の座標欄だけに書きます。"
)


def snapshot():
    a = pilot.audit
    previous = BEFORE / "lock.json"
    plan = a.load(previous)
    if any(a.sha(Path(p)) != h for p, h in plan["files"].items()):
        raise ValueError("前の比較で固定した方法が違う")
    old_rows = a.load(old / "display/selection.json")["selected"]
    font = a.packets.old.base.FONTS / "meiryo.ttc"
    segments = a.packets.old.original.segments
    anchors, rows, jobs, entries = {}, [], {}, {}
    for name, task in plan["jobs"].items():
        tag = name.split("/")[0]
        rowinfo = plan["mapping"][tag]
        if rowinfo["category"] not in GROUPS:
            continue
        row = old_rows[rowinfo["entry"]]
        request = task["request"]
        ident, = request["ids"]
        original_cards = Path(task["cards"])
        bins = original_cards.parent.parent / "packages.json"
        image_reference = a.load(bins)["packs"][original_cards.name]["mapping"][ident]["image_reference"]
        source = image_reference["sha"]
        png = a.packets.old.CORPUS / "probe-v4/png" / (row["key"] + ".png")
        if a.sha(png) != source["150_dpi"]:
            raise ValueError("横座標を描く150 DPIが固定画像と違う")
        keep = {f: (original_cards / f).read_bytes() for f in request["images"]}
        if any(a.readers.sha(keep[n]) != h for n, h in zip(request["images"], request["image_sha256"], strict=True)):
            raise ValueError("前に固定した添付が変化")
        replacements = cards(row, png, ident, segments, font)
        used = {f for f in keep if "-coordinate-" in f}
        if used != replacements.keys():
            raise ValueError("横座標以外の添付を変更せずに置き換えられない")
        keep.update(replacements)
        prefix, format_text, end = request["prompt"].partition(a.packets.FORMAT)
        if not format_text:
            raise ValueError("回答形式を見つけられない")
        packet = pilot.OUT / "display" / "cards" / tag
        packet.mkdir(parents=True)
        for filename, blob in keep.items():
            a.save_once(packet / filename, blob)
        entries[tag] = {**rowinfo, "entry": len(rows), "image_reference": image_reference}
        rows.append(row)
        jobs[name] = {**task, "cards": str(packet), "request": {**request,
                     "image_sha256": [a.readers.sha(keep[f]) for f in request["images"]],
                     "prompt": prefix + GUIDE + format_text + end}}
        for item in (bins, png):
            anchors[str(item)] = a.sha(item)
    file = pilot.OUT / "display" / "selection.json"
    a.save_once(file, a.encoded({"selected": rows}))
    pins = (Path(__file__), HERE / "ruler.py", HERE / "protocol.md", previous, file, font)
    anchors.update({str(p): a.sha(p) for p in pins})
    pilot.SAMPLES = rows
    return {"jobs": jobs, "mapping": entries, "files": plan["files"] | anchors}


if __name__ == "__main__":
    pilot.snapshot = snapshot
    pilot.main()
