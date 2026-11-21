"""同じ官報頁で繰り返された字の固定画素を位置だけそろえて比較する。"""

from itertools import combinations
from pathlib import Path

import numpy as np
from PIL import Image

from importlib.util import module_from_spec, spec_from_file_location

HERE=Path(__file__).resolve().parent
spec=spec_from_file_location("vertical_ink_shapes",HERE/"run.py")
stage=module_from_spec(spec)
spec.loader.exec_module(stage)
bands, core, fixed, launch=stage.bands, stage.core, stage.fixed, stage.launch


def tight(im, bounds, level):
    x,a,r,b=bounds
    gray = np.asarray(im.convert("L"))[a:b,x:r]
    shape = gray < level
    y,x=np.nonzero(shape)
    return shape[y.min():y.max()+1,x.min():x.max()+1]


def overlap(first, second):
    canvas=(max(first.shape[0],second.shape[0])+12,max(first.shape[1],second.shape[1])+12)
    baseline=np.zeros(canvas,dtype=bool)
    h,w=first.shape
    baseline[5:5+h,5:5+w]=first
    h,w=second.shape
    best=0
    for y in range(3,8):
        for x in range(3,8):
            moved=np.zeros(canvas,dtype=bool)
            moved[y:y+h,x:x+w]=second
            best=max(best,(moved&baseline).sum()/(moved|baseline).sum())
    return round(float(best),4)


def main():
    launch.configure()
    core.verify_methods()
    file=fixed.delivery/"packages.json"
    canonical=core.load(file)
    selection=launch.OUT/"selection.json"
    rows=core.load(selection)["selected"]
    picked={}
    input_hashes={str(file):core.sha(file),str(selection):core.sha(selection)}
    for item in canonical["packs"].values():
        entry,=item["mapping"].values()
        row=rows[entry["entry"]]
        line=row["line_index"]
        if row["key"]!="kanpo1828-p3-p0001" or line not in (144,164,180,201):
            continue
        bound=entry["image_reference"]
        v=bound["source_view"]["views"][1]
        asset=next(z["image"] for z in v["images"] if z["kind"]=="plain")
        photo=fixed.delivery/"source-assets"/asset
        digest=core.sha(photo)
        if digest!=canonical["source_assets"][asset]:
            raise ValueError("固定450 DPIの像が異なる")
        input_hashes[str(photo)]=digest
        with Image.open(photo) as image:
            rect,spans=bands(image,v["target_rectangle"])
            if len(spans)!=10:
                raise ValueError("事前に視認した十帯が検出されない")
            x,_,r,_=rect
            picked[line]={k:[tight(image,(x,a,r,b),level) for level in (140,185)]
                          for k,(a,b) in enumerate(spans,1)}
    results=[]
    for i,j in combinations(sorted(picked),2):
        by_position={n:[overlap(p,q) for p,q in zip(picked[i][n],picked[j][n],strict=True)] for n in range(1,11)}
        incompatible_examples={f"{m}/{n}":[overlap(p,q) for p,q in zip(picked[i][m],picked[j][n],strict=True)]
                               for m,n in ((2,3),(2,5),(6,7),(5,6))}
        results.append({"rows":[i,j],"same_band_indexes":by_position,"different_band_controls":incompatible_examples})
    if len(results)!=6:
        raise ValueError("四行の組がそろわない")
    out={"scope":"development-only","comparisons":results,"inputs":{**input_hashes,str(Path(__file__)):core.sha(Path(__file__))}}
    core.save_once(HERE/"printed-form-comparison.json",core.encoded(out))
    for item in results:
        print(item["rows"],item["same_band_indexes"][2],item["same_band_indexes"][6],
              max(r for p in item["different_band_controls"].values() for r in p),flush=True)


if __name__=="__main__":
    main()
