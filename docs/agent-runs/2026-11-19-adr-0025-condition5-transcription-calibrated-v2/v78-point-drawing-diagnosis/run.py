"""位置がそろった三つの丸印だけで、画素がどの種類の描画に依存するかを診断する。"""

from contextlib import closing
import ctypes
from importlib.util import module_from_spec, spec_from_file_location
from math import ceil, floor
from pathlib import Path

import numpy as np
from PIL import Image
from scipy.ndimage import find_objects, label

HERE = Path(__file__).resolve().parent
EFFORT = HERE.parent / "v71-audit-effort-pilot"
spec = spec_from_file_location("effort_for_point_drawing", EFFORT / "run.py")
fixed = module_from_spec(spec)
spec.loader.exec_module(fixed)
core, launch, previous = fixed.core, fixed.launch, fixed.previous


def localized(gray, frame, width, readings):
    left, top, right, bottom = frame
    sx=(right-left)/width
    l,r=max(0,floor(left+sx*(min(readings)-11))),min(gray.shape[1],ceil(left+sx*(max(readings)+11)))
    t,b=max(0,floor(top-4)),min(gray.shape[0],ceil(bottom+4))
    possible=[]
    for polarity, thresholds in (("dark",(140,185)),("light",(216,242))):
        det=[]
        for level in thresholds:
            patch=gray[t:b,l:r]
            ink=patch<level if polarity=="dark" else patch>level
            field,_=label(ink,np.ones((3,3),dtype=bool))
            matches=[]
            for index,(y,x) in enumerate(find_objects(field),1):
                w,h=x.stop-x.start,y.stop-y.start
                rel=(l+(x.start+x.stop)/2-left)/sx
                if (x.start==0 or y.start==0 or x.stop==r-l or y.stop==b-t
                        or not 5<=w<=38 or not 5<=h<=38 or abs(w-h)>6
                        or not top<=t+(y.start+y.stop)/2<bottom
                        or max(abs(n-rel) for n in readings)>5
                        or (field[y,x]==index).sum()<.48*w*h):
                    continue
                matches.append((l+x.start,t+y.start,l+x.stop,t+y.stop))
            det.append(matches)
        possible.extend((polarity,base) for base in det[0]
                        if sum(max(abs(a-b) for a,b in zip(base,other,strict=True))<=3 for other in det[1])==1)
    return possible[0] if len(possible)==1 else None


def diagnostic(trace, blob, number, fixed_png, bounds, asset):
    raw=trace.raw
    l,t,r,b=bounds
    roi=np.s_[t-1:b+1,l-1:r+1]
    pad=fixed_png[roi]
    with closing(trace.pypdfium2.PdfDocument(blob)) as doc, closing(doc[number-1]) as page:
        def render():
            with closing(page.render(scale=150/72)) as picture:
                return np.asarray(picture.to_pil().convert("RGB"))[roi].copy()

        if not np.array_equal(render(),pad):
            raise ValueError("元PDFの通常描画が固定150 DPIと異なる")
        text=[o for o in page.get_objects(filter=[raw.FPDF_PAGEOBJ_TEXT])]
        def visible(obj):
            active=ctypes.c_long()
            if not raw.FPDFPageObj_GetIsActive(obj,ctypes.byref(active)):
                raise ValueError("描画の活性を確認できない")
            return bool(active.value)
        def toggle(objs, active):
            for obj in objs:
                if not raw.FPDFPageObj_SetIsActive(obj,active):
                    raise ValueError("描画を切り分けられない")
        active=[o for o in text if visible(o)]
        try:
            toggle(active,False)
            absent=render()
        finally:
            toggle(active,True)
        delta=np.any(absent!=pad,axis=2)
        answer={"patch_pixels":delta.size,"changed_without_text":int(delta.sum())}
        if np.any(delta):
            return answer
        origin, matrix=np.asarray(asset["sha"]["150_origin"]), np.asarray(asset["sha"]["150_matrix"])
        contributors=[]
        for typ,name in ((raw.FPDF_PAGEOBJ_IMAGE,"image"),(raw.FPDF_PAGEOBJ_PATH,"path")):
            for obj in page.get_objects(filter=[typ]):
                if not visible(obj):
                    continue
                x,y,z,w=obj.get_bounds()
                points=np.array([matrix@(np.asarray(p)-origin) for p in ((x,y),(x,w),(z,y),(z,w))])
                xmin,ymin=points.min(axis=0)
                xmax,ymax=points.max(axis=0)
                if not (xmin<r+1 and xmax>l-1 and ymin<b+1 and ymax>t-1):
                    continue
                try:
                    toggle([obj],False)
                    changed=int(np.any(render()!=pad,axis=2).sum())
                finally:
                    toggle([obj],True)
                if changed:
                    contributors.append({"kind":name,"changed_pixels":changed})
        answer["other_objects"]=contributors
        return answer


def main():
    launch.configure()
    core.verify_methods()
    comparison=EFFORT/"comparison.json"
    followup=EFFORT/"source-followup.json"
    lock=EFFORT/"lock.json"
    summary,source,plan=(core.load(p) for p in (comparison,followup,lock))
    if summary["lock_sha256"]!=core.sha(lock) or source["inputs"].get(str(comparison))!=core.sha(comparison):
        raise ValueError("開発の出典確認と二票の記録が異なる")
    data=core.load(fixed.pilot.OUT/"display/selection.json")["selected"]
    manifest=fixed.delivery/"packages.json"
    assets=core.load(manifest)["source_assets"]
    catalog=previous.packets.old.lookup()[1]
    trace=launch.source.verify_vertical.trace
    cases={}
    for pack,item in source["cases"].items():
        if item["outcome"]!="unresolved":
            continue
        binding=plan["mapping"][pack]
        row=data[binding["entry"]]
        readings=summary["cases"][pack]["readings"]["high"]
        pairs=readings["coordinates"]
        if len(pairs)!=1 or not core.ref.MARK.search(readings["pair"]["text"]):
            raise ValueError("二つの画像票で位置がそろう一つの印が必要")
        page=row["key"]
        base, sha, number=catalog[page]
        bound=binding["image_reference"]
        view=bound["source_view"]["views"][1]
        png=next(v["image"] for v in view["images"] if v["kind"]=="plain")
        fine=fixed.delivery/"source-assets"/png
        coarse=core.CORPUS/"probe-v4/png"/f"{page}.png"
        if (core.sha(fine)!=assets[png] or core.sha(coarse)!=bound["sha"]["150_dpi"]):
            raise ValueError("固定した150・450 DPIの画素が異なる")
        result={"page":page,"line_index":row["line_index"]}
        cases[pack]=result
        with Image.open(fine) as picture:
            point=localized(np.asarray(picture.convert("L")),view["target_rectangle"],row["box"][2],pairs[0])
        if point is None:
            result["state"]="unresolved-location"
            continue
        polarity,(l,t,r,b)=point
        x,y,w,h=row["box"]
        a,s,z,k=view["target_rectangle"]
        sx,sy=(z-a)/w,(k-s)/h
        roi=(floor(x+(l-a)/sx),floor(y+(t-s)/sy),ceil(x+(r-a)/sx),ceil(y+(b-s)/sy))
        result.update(polarity=polarity,pixels_450=[l,t,r,b],pixels_150=roi)
        blob=(core.CORPUS/base).read_bytes()
        if trace.sha(blob)!=sha or bound["sha"]["pdf_sha256"]!=sha:
            raise ValueError("元PDFの来歴が異なる")
        with Image.open(coarse) as picture:
            result.update(diagnostic(trace,blob,number,np.asarray(picture.convert("RGB")),roi,bound))
        result["state"]="recorded"
    if len(cases)!=3:
        raise ValueError("開発で出典不足の三行がそろわない")
    refs={str(p):core.sha(p) for p in (Path(__file__),HERE/"protocol.md",comparison,followup,lock,manifest)}
    core.save_once(HERE/"result.json",core.encoded({"scope":"development-only","cases":cases,"inputs":refs}))
    print(cases,flush=True)


if __name__=="__main__":
    main()
