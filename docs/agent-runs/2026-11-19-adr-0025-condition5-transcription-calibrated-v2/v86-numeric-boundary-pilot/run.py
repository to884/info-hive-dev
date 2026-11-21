"""同じ固定画像で数値の枠端の判定の説明だけを比べる。"""

from importlib.util import module_from_spec, spec_from_file_location
from math import ceil, floor
from pathlib import Path
import re
import sys

from PIL import Image, ImageDraw, ImageFont

HERE = Path(__file__).resolve().parent
STAGES = HERE.parent
EFFORT = STAGES / "v71-audit-effort-pilot/run.py"
spec = spec_from_file_location("fixed_effort_numeric_boundaries", EFFORT)
study = module_from_spec(spec)
spec.loader.exec_module(study)
core, launch, pilot, grade = study.core, study.launch, study.pilot, study.judge
pilot.HERE = HERE
pilot.OUT = core.CORPUS / "reference-v86-numeric-boundary-pilot"
pilot.LOCK, pilot.RESULT = HERE / "lock.json", HERE / "pair.json"
pilot.audit.readers.command = study.high
TARGETS = {("defense-p0525", 94), ("defense-p0525", 101)}
NUMBER = re.compile(r"[0-9]+(?:[,.\-:/][0-9]+)*")
NOTE = "『固定画素の上下の境界』の左右の線は、元の枠の上端と下端の位置です。本文は元の画素です。"
GUIDE = (
    "数値の間などの小さい字や記号は、枠から出た画も含めて全体を見ます。"
    "上下のインク中心が枠の上端または下端にちょうど一致する場合は、中心は枠内として扱います。"
    "字全体の横のインク長さの半分以上が入る条件もそのまま使います。"
    "字間が広いという理由だけで見えない記号を足しません。"
)


def view_pair(row, packet, asset_paths, ident, font):
    x, y, w, h = row["box"]
    old_view = packet["source_view"]["views"][1]["target_rectangle"]
    lines = []
    for path, rect, scale, dpi, pad in (
            (asset_paths[0], (x, y, x+w, y+h), 4, 150, 7),
            (asset_paths[1], old_view, 2, 450, 22)):
        with Image.open(path) as im:
            l, t, r, b = rect
            area = max(0, floor(l)-pad), max(0, floor(t)-pad), min(im.width, ceil(r)+pad), min(im.height, ceil(b)+pad)
            body = im.crop(area).convert("RGB")
        big = body.resize((body.width*scale, body.height*scale), Image.Resampling.NEAREST)
        lines.append((big, (round((t-area[1])*scale), round((b-area[1])*scale)), dpi))
    height = sum(im.height+29 for im, _, _ in lines)+36
    width = max(450, 52+max(im.width for im, _, _ in lines))
    canvas = Image.new("RGB", (width,height), "white")
    draw = ImageDraw.Draw(canvas)
    draw.text((7,4),f"{ident} 固定画素の上下の境界",font=font,fill="black")
    y = 29
    for photo, edges, dpi in lines:
        draw.text((7,y),f"固定{dpi} DPI",font=font,fill="black")
        y += 26
        canvas.paste(photo,(25,y))
        for mark in edges:
            draw.line((7,y+mark,22,y+mark),fill="#991c31",width=2)
            draw.line((27+photo.width,y+mark,43+photo.width,y+mark),fill="#991c31",width=2)
        y += photo.height+3
    return launch.render.orientation.blob(canvas)


def snapshot():
    core.verify_methods()
    old = study.delivery
    manifest = old / "packages.json"
    raw = launch.OUT / "selection.json"
    result = STAGES / "v64-reference-audit/result.json"
    reference = launch.OUT / "reference-evidence.json"
    if core.load(result)["reference_sha256"] != core.sha(reference):
        raise ValueError("保留の記録と正式監査の署名が異なる")
    batches, archived, rows = core.load(manifest), core.load(reference), core.load(raw)["selected"]
    display = pilot.OUT / "display"
    pins = [Path(__file__), HERE/"protocol.md", EFFORT, Path(pilot.__file__), Path(grade.__file__),
            launch.render.typeface, manifest, raw, result, reference]
    font = ImageFont.truetype(launch.render.typeface,size=16)
    work, links, entries = {}, {}, []
    seen = set()
    for pack,batch in batches["packs"].items():
        (ident, link), = batch["mapping"].items()
        row = rows[link["entry"]]
        key = row["key"], row["line_index"]
        w,h = row["box"][2:]
        if row["allocation_axis"]!="x" or w>=150 or h>35 or link["partitions"]:
            continue
        answer = {core.ref.NORMALIZE(t["text"]) for t in row["targets"].values() if t["known"]}
        if len(answer)!=1:
            continue
        known=answer.pop()
        proof=archived[f"{key[0]}/{key[1]}"]
        if key in TARGETS:
            group="boundary-target"
            seen.add(key)
        elif proof["evidence"]=="image-only" and proof["answer"]["text"]==known and NUMBER.fullmatch(known):
            group="numeric-punctuated-control" if any(ch in known for ch in ",.:-/") else "numeric-unpunctuated-control"
        else:
            continue
        assets = link["image_reference"]
        high_view = assets["source_view"]["views"][1]
        name = next(v["image"] for v in high_view["images"] if v["kind"]=="plain")
        high = old/"source-assets"/name
        low = core.CORPUS/"probe-v4/png"/(row["key"]+".png")
        if core.sha(low)!=assets["sha"]["150_dpi"] or core.sha(high)!=batches["source_assets"][name]:
            raise ValueError("枠端の固定された画素が一致しない")
        request=batch["request"]
        directory=old/"cards"/pack
        if ([core.sha(directory/f) for f in request["images"]]!=request["image_sha256"]
                or len(request["images"])>=launch.audit.LIMIT
                or request["prompt"].count(launch.neutral.HORIZONTAL)!=1):
            raise ValueError("保存済みの画像と新旧の依頼を同じ一束にできない")
        target_folder=display/"cards"/pack
        target_folder.mkdir(parents=True)
        for filename in request["images"]:
            core.save_once(target_folder/filename,(directory/filename).read_bytes())
        name=f"{ident}-numeric-boundary.png"
        core.save_once(target_folder/name,view_pair(row,assets,(low,high),ident,font))
        old_note=launch.neutral.HORIZONTAL+NOTE
        common={**request,"images":[*request["images"],name],
                "image_sha256":[*request["image_sha256"],core.sha(target_folder/name)]}
        for arm,extra in (("old",""),("new",GUIDE)):
            prompt=request["prompt"].replace(launch.neutral.HORIZONTAL,old_note+extra,1)
            work[f"{pack}/{arm}"]={"cards":str(target_folder),"request":{**common,"prompt":prompt}}
        mapped={**link,"entry":len(entries)}
        links[pack]={**mapped,"group":group,"category":group,"arms":{"old":mapped,"new":mapped}}
        entries.append({**row,"effective":known})
        pins.extend((low,high))
    if seen != TARGETS or len(entries) <= len(seen):
        raise ValueError("二つの枠端の対象と数値の対照を固定できない")
    selected=display/"selection.json"
    core.save_once(selected,core.encoded({"selected":entries}))
    pilot.SAMPLES=entries
    return {"jobs":work,"mapping":links,
            "files":core.load(core.LOCK)["inputs"]|{str(path):core.sha(path) for path in (*pins,selected)}}


if __name__=="__main__":
    launch.configure()
    if len(sys.argv)>1 and sys.argv[1]=="compare":
        grade.main(core,pilot)
    else:
        pilot.snapshot=snapshot
        pilot.main()
