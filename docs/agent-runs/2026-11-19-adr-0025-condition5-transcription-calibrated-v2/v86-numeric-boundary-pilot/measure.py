"""対象の小さい区切りの中心と固定枠の下端を二つの解像度で測る。"""

from hashlib import sha256
from importlib.util import module_from_spec, spec_from_file_location
import json
from math import ceil, floor
from pathlib import Path

import numpy as np
from PIL import Image
from scipy.ndimage import find_objects, label

HERE = Path(__file__).resolve().parent
CORPUS = Path("docs/research/adr-0025-condition5-2026-11-16/corpus").resolve()
LOCATION = {"pack-373": (21.5, 61.0), "pack-214": (29.5,)}
INK = CORPUS.parent / "scripts/measure_visual_ink.py"
spec = spec_from_file_location("existing_region_ink", INK)
existing = module_from_spec(spec)
spec.loader.exec_module(existing)


def read(path):
    return json.loads(path.read_text(encoding="utf-8"))


def sha(path):
    return sha256(path.read_bytes()).hexdigest()


def point(pixels, frame, candidates, cutoff):
    x,y,r,b=frame
    left,top=floor(x)-7,floor(y)-7
    right,bottom=ceil(r)+8,ceil(b)+15
    ink=pixels[top:bottom,left:right]<cutoff
    groups,_=label(ink,np.ones((3,3),dtype=bool))
    items=[]
    for rows,columns in find_objects(groups):
        bounds=(left+columns.start,top+rows.start,left+columns.stop,top+rows.stop)
        l,t,rt,d=bounds
        if not (.10*(b-y)<d-t<.45*(b-y) and b-.18*(b-y)<(t+d)/2<b+.15*(b-y)):
            continue
        items.append(bounds)
    output=[]
    for at in candidates:
        options=[v for v in items if abs((v[0]+v[2])/2-x-at) <= max(1.2,(b-y)*.065)]
        if len(options)!=1:
            output.append({"relative_x":at,"candidates":options,"status":"insufficient"})
            continue
        found,=options
        result=existing.span(found,frame,0)
        result["relative_vertical_center_to_bottom"]=round((found[1]+found[3])/2-b,8)
        result["included_by_existing_geometry"]=(result["axis_overlap"]*2>=result["axis_length"]
                                                and result["cross_axis_center_inside"])
        output.append(result)
    return output


def main():
    root=CORPUS/"reference-audit-v64"
    manifest,selection=root/"delivery/packages.json",root/"selection.json"
    bundles=read(manifest)
    rows=read(selection)["selected"]
    inputs={str(p):sha(p) for p in (manifest,selection,INK,Path(__file__))}
    result={}
    for pack,anchors in LOCATION.items():
        bind,=bundles["packs"][pack]["mapping"].values()
        row=rows[bind["entry"]]
        info=bind["image_reference"]
        high=info["source_view"]["views"][1]
        x,y,w,h=row["box"]
        hi=next(v["image"] for v in high["images"] if v["kind"]=="plain")
        lo_file=CORPUS/"probe-v4/png"/(row["key"]+".png")
        hi_file=root/"delivery/source-assets"/hi
        files={lo_file: info["sha"]["150_dpi"], hi_file: bundles["source_assets"][hi]}
        if any(sha(p)!=digest for p,digest in files.items()):
            raise ValueError("測る元の固定画像が異なる")
        inputs.update({str(p):v for p,v in files.items()})
        sizes={}
        for dpi,f,rect in ((150,lo_file,(x,y,x+w,y+h)),(450,hi_file,high["target_rectangle"])):
            with Image.open(f) as im:
                gray=np.array(im.convert("L"))
            mapped=[at*(rect[2]-rect[0])/w for at in anchors]
            # 背景255から64を引いた現行の比較と、濃さを変えたときの位置。
            sizes[dpi]={k:point(gray,rect,mapped,k) for k in (135,170,191,195)}
        result[pack]={"page":row["key"],"line_index":row["line_index"],"frame_150":[x,y,x+w,y+h],
                      "measurements":sizes}
    out=HERE/"physical.json"
    with out.open("x",encoding="utf-8",newline="\n") as f:
        json.dump({"scope":"development-only","rows":result,"inputs":inputs},f,ensure_ascii=False,indent=2)
        f.write("\n")
    for name,data in result.items():
        print(name,{dpi:[r.get("relative_vertical_center_to_bottom") for r in t[191]] for dpi,t in data["measurements"].items()})


if __name__=="__main__":
    main()
