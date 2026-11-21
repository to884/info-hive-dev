"""行頭の形が他の項目とそろうか固定150 DPIの周囲を追加して比べる。"""

from collections import defaultdict
from hashlib import sha256
from importlib.util import module_from_spec, spec_from_file_location
from pathlib import Path
import sys

from PIL import ImageFont

HERE = Path(__file__).resolve().parent
BASE = HERE.parent / "v71-audit-effort-pilot"
spec = spec_from_file_location("effort_for_leading_mark", BASE / "run.py")
fixed = module_from_spec(spec)
spec.loader.exec_module(fixed)
core, launch, pilot, grade = fixed.core, fixed.launch, fixed.pilot, fixed.judge
pilot.HERE = HERE
pilot.OUT = core.CORPUS / "reference-v81-leading-item-context-pilot"
pilot.LOCK, pilot.RESULT = HERE / "lock.json", HERE / "pair.json"
pilot.audit.readers.command = fixed.high
TARGETS = {"pack-110": "point-and-body", "pack-171": "embedded-small-point", "pack-269": "section-item"}
GUIDE = (
    "『行と列のつながり』は固定150 DPIで、元の赤い枠の外も表示しています。"
    "先頭に丸がある場合、近い上下と左右の別の項目に、同じ高さ・大きさ・位置で本文から離れた丸が繰り返されるか確かめます。"
    "点の輪郭と本文の字との大きさは枠なしの450 DPIで確認します。"
    "字種が画像で区別できない小点は、形と位置を既定の方法で記録します。枠外は転記しません。"
)


def snapshot():
    core.verify_methods()
    archive, manifest = launch.OUT / "selection.json", fixed.delivery / "packages.json"
    formal = HERE.parent / "v64-reference-audit/result.json"
    references = launch.OUT / "reference-evidence.json"
    if core.load(formal)["reference_sha256"] != core.sha(references):
        raise ValueError("確定した二票と出典が異なる")
    rows, packages, refs = core.load(archive)["selected"], core.load(manifest)["packs"], core.load(references)
    opts, controls = {}, defaultdict(list)
    for pack,batch in packages.items():
        (label,binding), = batch["mapping"].items()
        row = rows[binding["entry"]]
        req = batch["request"]
        if row["allocation_axis"]!="x" or len(req["images"])>=launch.audit.LIMIT:
            continue
        known = {core.ref.NORMALIZE(t["text"]) for t in row["targets"].values() if t["known"]}
        if len(known)!=1:
            continue
        expected=known.pop()
        if not expected or req["prompt"].count(launch.neutral.HORIZONTAL)!=1:
            continue
        identity=f"{row['key']}/{row['line_index']}"
        evidence=refs[identity]
        opts[pack]=batch,label,binding,{**row,"effective":expected}
        if pack in TARGETS or evidence["answer"]["text"] != expected:
            continue
        if expected.startswith("●") and evidence["evidence"]=="image-only":
            group="control-item"
        elif expected.startswith(("・","•")) and isinstance(evidence["evidence"],dict):
            group="control-small-dot"
        elif expected[0].isalnum() and evidence["evidence"]=="image-only":
            group="control-no-leading-mark"
        else:
            continue
        rank=sha256(f"adr0025-v81-bullet-context\0{identity}".encode()).hexdigest()
        controls[group].append((rank,pack))
    required={"control-no-leading-mark":2, "control-small-dot":1, "control-item":1}
    if not TARGETS.keys()<=opts.keys() or any(len(controls[g])<n for g,n in required.items()):
        raise ValueError(f"対象と対照がそろわない { {k:len(v) for k,v in controls.items()} }")
    selected={**TARGETS,**{n:g for g,v in controls.items() for _,n in sorted(v)[:required[g]]}}
    layout=launch.audit.packets.trial.base
    font=ImageFont.truetype(launch.render.typeface,size=17)
    jobs,mapping,ready,points={}, {}, [], []
    for pack,group in sorted(selected.items()):
        batch,label,binding,row=opts[pack]
        old=fixed.delivery/"cards"/pack
        req=batch["request"]
        if [core.sha(old/n) for n in req["images"]]!=req["image_sha256"]:
            raise ValueError("固定の旧画像と異なる")
        low=core.CORPUS/"probe-v4/png"/f"{row['key']}.png"
        points.append(low)
        newer=pilot.OUT/"display/paired/cards"/pack
        newer.mkdir(parents=True)
        images={n:(old/n).read_bytes() for n in req["images"]}
        images.update(layout.framed_context(row,binding["image_reference"],{},label,font))
        for n,data in images.items():
            core.save_once(newer/n,data)
        altered={**req,"images":list(images),"image_sha256":[core.sha(newer/n) for n in images],
                 "prompt":req["prompt"].replace(launch.neutral.HORIZONTAL,launch.neutral.HORIZONTAL+GUIDE,1)}
        link={**binding,"entry":len(ready)}
        ready.append(row)
        mapping[pack]={**link,"category":group,"group":group,"arms":{"old":link,"new":link}}
        jobs[f"{pack}/old"]={"cards":str(old),"request":req}
        jobs[f"{pack}/new"]={"cards":str(newer),"request":altered}
    picked=pilot.OUT/"display/selection.json"
    core.save_once(picked,core.encoded({"selected":ready}))
    files=(Path(__file__),HERE/"protocol.md",BASE/"run.py",Path(grade.__file__),Path(pilot.__file__),
           archive,manifest,formal,references,picked,Path(layout.__file__),launch.render.typeface,*points)
    pilot.SAMPLES=ready
    return {"jobs":jobs,"mapping":mapping,"files":core.load(core.LOCK)["inputs"]|{str(p):core.sha(p) for p in files}}


if __name__=="__main__":
    launch.configure()
    if len(sys.argv)>1 and sys.argv[1]=="compare":
        grade.main(core,pilot)
    else:
        pilot.snapshot=snapshot
        pilot.main()
