"""四隅の対称な計測と、同じ大きさの丸の実対照を使う。"""

from importlib.util import module_from_spec, spec_from_file_location
from pathlib import Path
from collections import Counter

import numpy as np

HERE=Path(__file__).resolve().parent
STAGES=HERE.parent
BASE=STAGES/"v76-leading-shape-pilot/run.py"
spec=spec_from_file_location("matched_round_sizes",BASE)
old=module_from_spec(spec)
spec.loader.exec_module(old)
core, launch=old.core, old.launch
THRESHOLDS=(160,192)
TARGET=("defense-p0500",84)
MATCHES={
    ("wp-summary-p0009",0):((574,42,584,51),(778,42,787,51)),
    ("defense-p0134",25):((313,660,322,669),),
}


def valid_points(gray, rectangles):
    picks=[]
    masses=[]
    for rect, level in zip(rectangles,THRESHOLDS,strict=True):
        l,t,r,b=rect
        xc=(l+r)//2
        yc=(t+b)//2
        xright=xc+(r-l)%2
        ybottom=yc+(b-t)%2
        values=[float((gray[a:z,p:q]<level).mean()) for a,z in ((t,yc),(ybottom,b))
                for p,q in ((l,xc),(xright,r))]
        picks.append({i for i,v in enumerate(values) if v<=.28 and values[3-i]>=.58})
        masses.append([round(x,4) for x in values])
    return picks[0]&picks[1],masses


def judge(low, high, view, box, coarse):
    light, low_measure=valid_points(low,(coarse,coarse))
    fine=old.focused(high,view,box,coarse)
    dark, high_measure=valid_points(high,fine) if fine else (set(),[])
    isolated=False
    if fine:
        left=min(v[0] for v in fine)
        top=min(v[1] for v in fine)
        right=max(v[2] for v in fine)
        bottom=max(v[3] for v in fine)
        if min(left,top)>=2 and right+2<high.shape[1] and bottom+2<high.shape[0]:
            guard=high[top-2:bottom+2,left-2:right+2].copy()
            guard[2:-2,2:-2]=255
            isolated=bool(np.all(guard>=192))
    return {"coarse":coarse,"coarse_density":low_measure,"fine":fine,
            "fine_density":high_measure,"isolated_450":isolated,"non_round":bool(light&dark and isolated)}


def simulations():
    choices=Counter()
    Y,X=np.ogrid[:55,:55]
    y,x=np.ogrid[:165,:165]
    for diameter in (8.6,9.0,9.4,9.8,10.2):
        for dx,dy in ((0.1,.1),(.2,.7),(.5,.5),(.8,.4)):
            for tone in (34,89):
                d1=np.hypot(X+.5-(24+dx),Y+.5-(24+dy))
                d2=np.hypot(x+.5-(24+dx)*3,y+.5-(24+dy)*3)
                gray=np.rint(tone+np.clip(d1-diameter/2+.5,0,1)*(250-tone)).astype(np.uint8)
                high=np.rint(tone+np.clip(d2-1.5*diameter+.5,0,1)*(250-tone)).astype(np.uint8)
                box=(16,16,24,20)
                for coarse in old.guard.reference.small_round(gray,box):
                    l,t,r,b=coarse
                    if max(r-l,b-t) not in (9,10):
                        continue
                    record=judge(gray,high,(48,48,120,108),box,coarse)
                    choices["entered_150"]+=1
                    choices["entered_both"]+=bool(record["fine"])
                    if record["non_round"]:
                        raise ValueError("実際の候補経路で丸を除く合成反例")
                choices["generated"]+=1
    return choices


def main():
    launch.configure()
    core.verify_methods()
    evidence={}
    pins={}
    for version in (47,64):
        folder=core.CORPUS/f"reference-audit-v{version}"
        delivery=folder/"delivery"
        select, manifests, refs=folder/"selection.json",delivery/"packages.json",folder/"reference-evidence.json"
        recorded_input=next(STAGES.glob(f"v{version}-reference-audit"))/"result.json"
        grade=core.load(recorded_input)
        if core.sha(refs)!=grade["reference_sha256"]:
            raise ValueError("対照の出典が確定した読みから変化")
        selected, doc, stored=core.load(select)["selected"],core.load(manifests),core.load(refs)
        pins.update({str(p):core.sha(p) for p in (recorded_input,select,manifests,refs)})
        for batch in doc["packs"].values():
            for binding in batch["mapping"].values():
                row=selected[binding["entry"]]
                key=row["key"],row["line_index"]
                if key not in MATCHES.keys()|{TARGET} or key in evidence:
                    continue
                geometry=binding["image_reference"]
                view=geometry["source_view"]["views"][1]
                name=next(v["image"] for v in view["images"] if v["kind"]=="plain")
                png=delivery/"source-assets"/name
                low_path=core.CORPUS/"probe-v4/png"/f"{key[0]}.png"
                low=old.gray(low_path,geometry["sha"]["150_dpi"])
                high=old.gray(png,doc["source_assets"][name])
                box=row["box"]
                if key==TARGET:
                    x,y,w,h=box
                    value=stored[f"{key[0]}/{key[1]}"]
                    if value["evidence"]!="unverified-small-round":
                        raise ValueError("丸の判定で保留になった行が違う")
                    round_boxes=[v for v in old.guard.reference.small_round(low,(x,y,min(w,24),h))
                                 if max(v[2]-v[0],v[3]-v[1]) in (9,10)]
                    rectangles=round_boxes
                else:
                    source=stored[f"{key[0]}/{key[1]}"]["evidence"]
                    if "source-confirmed" not in source:
                        raise ValueError("丸の対照の出典を確認できない")
                    rectangles=MATCHES[key]
                    serialized=core.encoded(source).decode()
                    for rect in rectangles:
                        token=core.encoded(list(rect)).decode().strip()
                        if token not in serialized:
                            raise ValueError("丸の出典の位置が異なる")
                assessed=[]
                for coarse in rectangles:
                    result=judge(low,high,view["target_rectangle"],box,coarse)
                    l,t,r,b=coarse
                    lead=(max(l-4,0),max(t-4,0),24,max(17,b-t+8))
                    result["selected_as_leading_component"]=any(max(abs(v-w) for v,w in zip(coarse,found,strict=True))<=1
                        for found in old.guard.reference.small_round(low,lead))
                    assessed.append(result)
                evidence[key]={"page":key[0],"line_index":key[1],"version":version,"cases":assessed}
    if set(evidence)!=MATCHES.keys()|{TARGET}:
        raise ValueError("対象と同じ径の元の対照がそろわない")
    if any(c["non_round"] for key,value in evidence.items() if key!=TARGET for c in value["cases"]):
        raise ValueError("同じ径の元の丸が除かれた")
    result={"scope":"development-only","rows":list(evidence.values()),"synthetic":simulations(),
            "inputs":{**pins,str(BASE):core.sha(BASE),str(Path(__file__)):core.sha(Path(__file__)),
                      str(HERE/"protocol.md"):core.sha(HERE/"protocol.md")}}
    core.save_once(HERE/"result.json",core.encoded(result))
    print(result["rows"],result["synthetic"],flush=True)


if __name__=="__main__":
    main()
