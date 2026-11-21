"""固定画素で同じ帯を検出できる縦枠だけに、番号付きの拡大を付ける。"""

from hashlib import sha256
from importlib.util import module_from_spec, spec_from_file_location
from math import ceil, floor
from pathlib import Path
import sys

import numpy as np
from PIL import Image, ImageDraw, ImageFont

HERE = Path(__file__).resolve().parent
EFFORT = HERE.parent / "v71-audit-effort-pilot"
spec = spec_from_file_location("effort_for_separated_ink", EFFORT / "run.py")
fixed = module_from_spec(spec)
spec.loader.exec_module(fixed)
core, launch, pilot, grade = fixed.core, fixed.launch, fixed.pilot, fixed.judge
pilot.HERE = HERE
pilot.OUT = core.CORPUS / "reference-v77-vertical-separated-ink-pilot"
pilot.LOCK, pilot.RESULT = HERE / "lock.json", HERE / "pair.json"
pilot.audit.readers.command = fixed.high
PAGE = "kanpo1828-p3-p0001"
TARGETS = {144, 164, 180, 201}
GUIDE = (
    "『縦列の帯の拡大』は元と同じ450 DPIを上から順に分けたものです。"
    "元の枠で所属と本文を確かめ、拡大した各帯で画の接続、角、画が伸びる方向を個別に確認してください。"
    "帯は文字数、候補の字、語の区切りを示しません。番号や空白を転記に加えません。"
)


def bands(image, rect):
    x,y,z,b = rect
    l,t,r,end = max(0,ceil(x)), max(0,ceil(y)), min(image.width,floor(z)), min(image.height,floor(b))
    if not (20 <= r-l <= 125 and 95 <= end-t <= 720):
        return None
    gray = np.asarray(image.convert("L"))[t:end,l:r]
    seen = []
    for cutoff in (140, 185):
        used = np.count_nonzero(gray < cutoff, axis=1) >= 2
        sides = np.flatnonzero(np.diff(np.pad(used, (1, 1)))) + t
        seen.append(list(zip(sides[::2], sides[1::2], strict=True)))
    earlier, later = seen
    if not (4 <= len(later) <= 14 and len(earlier) == len(later)):
        return None
    if any(max(abs(a-c), abs(b-d)) > 1 for (a,b),(c,d) in zip(earlier,later,strict=True)):
        return None
    heights = [b-a for a,b in later]
    if min(heights) < 24 or max(heights) > 1.3*min(heights):
        return None
    if any(not 3 <= c-b <= 14 for (_,b),(c,_) in zip(later,later[1:])):
        return None
    markers = [t, *((b+c)//2 for (_,b),(c,_) in zip(later,later[1:])), end]
    return (l,t,r,end), [(int(a),int(b)) for a,b in zip(markers,markers[1:])]


def panel(image, label, bounds, parts, font):
    l,top,r,bottom = bounds
    if parts[0][0] != top or parts[-1][1] != bottom:
        raise ValueError("固定枠の上下の範囲が異なる")
    width = max(125, (r-l)*2+15)
    tile = 32+2*max(z-a for a,z in parts)
    sheet = Image.new("RGB", (5*width, 46+tile*((len(parts)+4)//5)), "white")
    draw = ImageDraw.Draw(sheet)
    draw.text((5,5),f"{label}　縦列の帯の拡大　固定450 DPI（上から番号順）",font=font,fill="black")
    for i, (a,z) in enumerate(parts):
        x,y=(i%5)*width+4, (i//5)*tile+36
        draw.text((x,y),str(i+1),font=font,fill="black")
        raw=image.crop((l,a,r,z)).convert("RGB")
        pix=raw.resize((2*raw.width,2*raw.height),Image.Resampling.NEAREST)
        sheet.paste(pix,(x,y+20))
        if sheet.crop((x,y+20,x+pix.width,y+20+pix.height)).resize(raw.size,Image.Resampling.NEAREST).tobytes()!=raw.tobytes():
            raise ValueError("分けた帯の画素が元の画素と違う")
    return launch.render.orientation.blob(sheet)


def snapshot():
    core.verify_methods()
    selection, manifest = launch.OUT / "selection.json", fixed.delivery / "packages.json"
    reference = launch.OUT / "reference-evidence.json"
    result_path = HERE.parent / "v64-reference-audit/result.json"
    if core.load(result_path)["reference_sha256"] != core.sha(reference):
        raise ValueError("対照の正式な来歴が異なる")
    rows, packed = core.load(selection)["selected"], core.load(manifest)
    refs = core.load(reference)
    assets, matched, controls = [], {}, []
    targets={(PAGE,line) for line in TARGETS}
    for pack, batch in packed["packs"].items():
        (label, link), = batch["mapping"].items()
        row = rows[link["entry"]]
        if not row["key"].startswith("kanpo") or row["allocation_axis"]!="y":
            continue
        page,line=fixed.key(row)
        identity=page,line
        known={core.ref.NORMALIZE(t["text"]) for t in row["targets"].values() if t["known"]}
        if len(known)!=1:
            continue
        expected=known.pop()
        proof=refs[f"{page}/{line}"]
        control=identity not in targets and proof["evidence"]=="image-only" and proof["answer"]["text"]==expected
        if identity not in targets and not control:
            continue
        view=link["image_reference"]["source_view"]["views"][1]
        image=next(v["image"] for v in view["images"] if v["kind"]=="plain")
        path=fixed.delivery/"source-assets"/image
        if core.sha(path)!=packed["source_assets"][image]:
            raise ValueError("元の固定450 DPIが異なる")
        assets.append(path)
        with Image.open(path) as bitmap:
            split=bands(bitmap,view["target_rectangle"])
        if split is None:
            continue
        matched[identity]=(pack,batch,label,link,{**row,"effective":expected},path,split)
        if control:
            digest=sha256(f"adr0025-v77-control\0{page}\0{line}".encode()).hexdigest()
            controls.append((page!=PAGE,digest,identity))
    if not targets <= matched.keys() or len(controls)<3:
        raise ValueError(f"分離できる対象か対照が不足: {sorted(targets & matched.keys())} 対照{len(controls)}")
    chosen=targets | {identity for *_,identity in sorted(controls)[:3]}
    jobs,mapping,ready={}, {}, []
    font_path=launch.render.typeface
    font=ImageFont.truetype(font_path,size=16)
    for identity in sorted(chosen):
        pack,batch,label,link,row,source,(rect,parts)=matched[identity]
        cards,request=fixed.delivery/"cards"/pack,batch["request"]
        if [core.sha(cards/n) for n in request["images"]]!=request["image_sha256"]:
            raise ValueError("元の監査の固定画像が異なる")
        newer=pilot.OUT/"display/paired/cards"/pack
        newer.mkdir(parents=True)
        for name in request["images"]:
            core.save_once(newer/name,(cards/name).read_bytes())
        name=f"{label}-separated-ink.png"
        with Image.open(source) as bitmap:
            core.save_once(newer/name,panel(bitmap,label,rect,parts,font))
        guide=launch.neutral.VERTICAL
        if request["prompt"].count(guide)!=1 or len(request["images"])>=launch.audit.LIMIT:
            raise ValueError("拡大の画像や説明を一か所だけ追加できない")
        display={**request,"images":[*request["images"],name],
                 "image_sha256":[*request["image_sha256"],core.sha(newer/name)],
                 "prompt":request["prompt"].replace(guide,guide+GUIDE,1)}
        binding={**link,"entry":len(ready)}
        group="typeform" if identity in targets else "control"
        mapping[pack]={**binding,"group":group,"category":group,"arms":{"old":binding,"new":binding}}
        ready.append(row)
        jobs[f"{pack}/old"]={"cards":str(cards),"request":request}
        jobs[f"{pack}/new"]={"cards":str(newer),"request":display}
    selected=pilot.OUT/"display/selection.json"
    core.save_once(selected,core.encoded({"selected":ready}))
    pins=(Path(__file__),HERE/"protocol.md",Path(grade.__file__),Path(pilot.__file__),EFFORT/"run.py",
          selection,manifest,reference,result_path,selected,font_path,*assets)
    pilot.SAMPLES=ready
    return {"jobs":jobs,"mapping":mapping,"files":core.load(core.LOCK)["inputs"]|{str(p):core.sha(p) for p in pins}}


if __name__=="__main__":
    launch.configure()
    if len(sys.argv)>1 and sys.argv[1]=="compare":
        grade.main(core,pilot)
    else:
        pilot.snapshot=snapshot
        pilot.main()
