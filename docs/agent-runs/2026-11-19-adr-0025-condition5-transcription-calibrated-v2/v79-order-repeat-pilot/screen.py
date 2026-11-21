"""保存済みの監査・修復・試験を除き、短枠の形だけで開発用の候補を洗い出す。"""

from collections import Counter, defaultdict
from functools import lru_cache
from hashlib import sha256
from importlib.util import module_from_spec, spec_from_file_location
from pathlib import Path

import numpy as np
from PIL import Image, ImageDraw, ImageFont

HERE=Path(__file__).resolve().parent
ORDER=HERE.parent/"v72-short-frame-order-pilot/run.py"
spec=spec_from_file_location("fixed_order_comparison",ORDER)
order=module_from_spec(spec)
spec.loader.exec_module(order)
core, launch=order.core,order.launch
ROOT=core.CORPUS
REGION=(
    "region-audit-v6/diagnostic-cases.json",
    "region-audit-v6/start.json",
    "region-audit-v6-450/start.json",
    "region-repair-v8/new-manual-rows.json",
    "region-repair-v9/unresolved-rows.json",
)


def records(folder):
    if folder.is_relative_to(ROOT):
        value=core.load(folder)
    else:
        raise ValueError("開発資料の履歴の場所が異なる")
    def items(value):
        if isinstance(value,dict):
            page=value.get("key") or value.get("page")
            i=value.get("line_index")
            if isinstance(page,str) and type(i) is int:
                yield page,i
            for member in value.values():
                yield from items(member)
        elif isinstance(value,list):
            for member in value:
                yield from items(member)
    return set(items(value))


def history():
    earlier={tuple(x) for x in core.load(core.PLAN)["direct_intake"]}
    inputs=set(ROOT.glob("reference-*/selection.json")) | set(ROOT.glob("reference-*/display/selection.json"))
    inputs.update(ROOT/f for f in REGION)
    counts={}
    for f in sorted(inputs):
        selected=records(f)
        if not selected:
            raise ValueError(f"履歴から行を読めない {f}")
        earlier.update(selected)
        counts[str(f)]=len(selected)
    selected=ROOT/"region-visual-v9/third-selection.json"
    start=ROOT/"region-visual-v9/start.json"
    batch=core.load(start)["entries"]
    entries=core.load(selected)["entries"]
    if not entries or not all(type(i) is int and 0 <= i < len(batch) for i in entries):
        raise ValueError("領域の第三読の行番号が元の台帳と異なる")
    pinned={(batch[i]["key"],batch[i]["line_index"]) for i in entries}
    earlier.update(pinned)
    inputs.update((selected,start))
    counts[str(selected)]=len(pinned)
    return earlier, inputs, counts


@lru_cache(maxsize=8)
def gray(page):
    path=ROOT/"probe-v4/png"/f"{page}.png"
    with Image.open(path) as im:
        return np.array(im.convert("L"))


def runs(active):
    borders=np.flatnonzero(np.diff(np.pad(active,(1,1))))
    return [(int(a),int(b)) for a,b in zip(borders[::2],borders[1::2],strict=True)]


def geometry(im, box):
    x,y,w,h=box
    region=im[y:y+h,x:x+w]
    levels=[]
    for threshold in (145,185):
        spans=runs((region<threshold).sum(axis=0)>=2)
        levels.append([(a,b) for a,b in spans if b-a>=4])
    earlier,later=levels
    if len(earlier)!=2 or len(later)!=2 or any(max(abs(a-c),abs(b-d))>2 for (a,b),(c,d) in zip(earlier,later,strict=True)):
        return None
    if later[1][0]-later[0][1]<1:
        return None
    measures=[]
    for a,b in later:
        margin=max(3,(b-a)//2)
        nearby=im[max(0,y-75):min(im.shape[0],y+h+75),max(0,x+a-margin):min(im.shape[1],x+b+margin)]
        bands=runs((nearby<175).sum(axis=1)>=3)
        measures.append(sum(5<=d-c<=32 for c,d in bands))
    return {"within_box_spans":later,"nearby_ink_bands":measures} if min(measures)>=3 else None


def render(root, rows):
    font=ImageFont.truetype(launch.render.typeface,size=17)
    for batch in range(0,len(rows),12):
        shown=rows[batch:batch+12]
        out=Image.new("RGB",(3*385,4*295),"white")
        draw=ImageDraw.Draw(out)
        for i,item in enumerate(shown):
            a,c=(i%3)*385,(i//3)*295
            x,y,w,h=item["box"]
            im=gray(item["key"])
            l,t,r,b=max(0,x-87),max(0,y-60),min(im.shape[1],x+w+87),min(im.shape[0],y+h+60)
            raw=Image.fromarray(im[t:b,l:r]).convert("RGB")
            raw=raw.resize((int(raw.width*1.6),int(raw.height*1.6)),Image.Resampling.NEAREST)
            d=ImageDraw.Draw(raw)
            d.rectangle((int((x-l)*1.6),int((y-t)*1.6),int((x+w-l)*1.6),int((y+h-t)*1.6)),outline="red",width=2)
            draw.text((a+4,c+4),item["id"],font=font,fill="black")
            out.paste(raw,(a+5,c+24))
        out.save(root/f"geometry-{batch//12+1:02d}.png")


def main():
    launch.configure()
    core.verify_methods()
    previous, inputs, provenance=history()
    _,_,training=core.methods()
    labels=training/"public.json"
    _,flags=core.baseline.take_public_rows()
    found={}
    for source,entries in core.baseline.populations(core.load(labels),flags).items():
        for record in entries:
            key=record["key"],record["line_index"]
            if key in previous or record["development_intake"] or record["previously_audited"] or not launch.render.short_frame(record):
                continue
            target={k:record[k] for k in ("cohort","text","known","error")}
            entry=found.setdefault(key,{k:v for k,v in record.items() if k not in target})
            entry.setdefault("targets",{})[source]=target
    groups=defaultdict(list)
    stats=Counter()
    for (page,line),row in sorted(found.items()):
        known={core.ref.NORMALIZE(v["text"]) for v in row["targets"].values() if v["known"]}
        if len(known)!=1 or not all(v["known"] for v in row["targets"].values()):
            continue
        w,h=row["box"][2:]
        metric=geometry(gray(page),row["box"])
        if page.startswith("kanpo") and w<=35 and metric:
            group="kanpo-narrow"
        elif page.startswith("kanpo") and w>35:
            group="kanpo-medium"
        elif not page.startswith("kanpo") and w>=28:
            group="other"
        else:
            continue
        stats[group]+=1
        row={**row,"effective":known.pop(),"geometry":metric,"group":group}
        rank=sha256(f"adr0025-v79-geometry\0{page}\0{line}".encode()).hexdigest()
        groups[group].append((rank,row))
    private=ROOT/"reference-v79-order-repeat-pilot/screen"
    private.mkdir(parents=True)
    ready=[]
    for group in ("kanpo-narrow","kanpo-medium","other"):
        by_page=Counter()
        for _,row in sorted(groups[group],key=lambda v:v[0]):
            page=row["key"]
            if by_page[page]>=6 or sum(r["group"]==group for r in ready)>=24:
                continue
            by_page[page]+=1
            tag=f"L{len(ready)+1:03d}"
            ready.append({**row,"id":tag})
    if not ready:
        raise ValueError("固定画像で確認する短い枠がない")
    points={str(f):core.sha(f) for f in sorted(inputs | {labels,core.PLAN,Path(__file__)})}
    core.save_once(private/"candidates.json",core.encoded({"rows":ready,"counts":stats,"excluded":len(previous),
                   "history_rows":provenance,"inputs":points}))
    render(private,ready)
    print(len(ready),stats,private,flush=True)


if __name__=="__main__":
    main()
