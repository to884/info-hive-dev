"""黒い筆画を含む枠で転記と選んだ成分を照合する。"""

import argparse
from collections import Counter, defaultdict
from importlib.util import module_from_spec, spec_from_file_location
from pathlib import Path
import re
import sys

from PIL import Image, ImageFont

HERE=Path(__file__).resolve().parent
FAMILY=HERE.parent
BASE=FAMILY/"v95-controlled-numeric-boundary"
PREVIOUS=FAMILY/"v96-explicit-numeric-boundary"
spec=spec_from_file_location("black_stroke_baseline",BASE/"run.py")
base=module_from_spec(spec)
spec.loader.exec_module(base)
core,launch,pilot,prior,measure=base.core,base.launch,base.pilot,base.prior,base.measure
pilot.HERE=HERE
pilot.OUT=core.CORPUS/"reference-v97-black-punctuation-lookalikes"
pilot.LOCK,pilot.RESULT=HERE/"lock.json",HERE/"transport-pair.json"
KINDS=("inside","edge","outside","no-comma")
DELTA={"inside":-1,"edge":0,"outside":1}
OLD_TAIL=(
    "枠への所属は固定150 DPIで決め、450 DPIの図は字形の確認に使います。"
    "先に本文の転記を決めます。次に、転記した記号がどの筆画か調べるために、"
    "textの転記の後に || を書き、各記号について出現順に 直前までの数字の個数:成分番号:種類 を | で区切って付けます。"
    "種類はコンマ C、点 D、コロン T、横線 H、斜線 S、その他 U。成分番号が不明なら ?。"
    "本文に記号がないときは ||- を付けます。成分の番号が分からなくても本文はそのまま返します。"
)
NEW_TAIL=(
    "数字の所属は固定150 DPIで確かめ、450 DPIの図は字形の確認に使います。"
    "区切りだと読んだ記号は、下端のすぐ外側のものも成分番号を報告し、上下の所属は判断しません。"
)
TRACE=re.compile(r"([0-9]+):([0-9]+|\?):([CDTHSU])")


def reading_prompt(template, arm, label):
    r=template["prompt"]
    marker=("枠への所属は『固定150 DPI』" if arm=="old" else "数字の所属は『固定150 DPI』")
    if template["ids"]!=["Y005"] or r.count(marker)!=1:
        raise ValueError("v96の所属の補足を一意に確認できない")
    common=r.split(marker,1)[0].replace("Y005",label).replace("JSONは results","JSONは answers")
    return common+(OLD_TAIL if arm=="old" else NEW_TAIL)


def snapshot():
    core.verify_methods()
    config=core.load(HERE/"physical-truth.json")
    truth=HERE/"development-fixed-frames.pdf"
    files=[Path(__file__),HERE/"protocol.md",HERE/"generate.py",HERE/"physical-truth.json",truth,
           BASE/"generate.py",BASE/"run.py",PREVIOUS/"lock.json",Path(prior.__file__),
           Path(measure.__file__),Path(measure.ink.__file__),Path(pilot.__file__),launch.render.typeface]
    if core.sha(truth)!=config["pdf_sha256"]:
        raise ValueError("新しい開発PDFと来歴が異なる")
    for name,digest in config["page_png_sha256"].items():
        p=HERE/"fixed-pages"/name
        if core.sha(p)!=digest:
            raise ValueError("固定した画素に違いがある")
        files.append(p)
    font=ImageFont.truetype(launch.render.typeface, size=16)
    template=core.load(PREVIOUS/"lock.json")["jobs"]
    display=pilot.OUT/"display"
    rows, links, jobs, coverage=[],{},{},Counter()
    for item in config["rows"]:
        tag, position=item["id"],item["position"]
        row={"key":f"development-black-strokes-p{item['page']:02d}","line_index":len(rows)+1,
             "box":item["box"],"allocation_axis":"x","effective":item["expected"]}
        x,y,w,h=row["box"]
        paths=tuple(HERE/"fixed-pages"/f"page-{item['page']}-{dpi}.png" for dpi in (150,450))
        for dpi in (150,450):
            k=dpi//150
            c=item[f"comma_{dpi}"]
            d=item[f"digits_{dpi}"]
            stroke=item[f"noise_{dpi}"]
            if not stroke or not y*k<(stroke[1]+stroke[3])/2<(y+h)*k:
                raise ValueError("黒い対照の筆画の中心が枠内にない")
            if not (x*k<d[0]<d[2]<(x+w)*k and y*k<=d[1]<d[3]<(y+h)*k):
                raise ValueError("数字の画素が切れている")
            if (c is None)!=(position=="no-comma") or (c and (c[1]+c[3])/2-(y+h)*k!=DELTA[position]*k):
                raise ValueError("両解像度で同じコンマ所属になっていない")
            if c and max(c[0]-stroke[2],stroke[0]-c[2])<=0:
                raise ValueError("コンマと対照の間に横の間隔がない")
        source={"source_view":{"views":[{},{"target_rectangle":[3*v for v in (x,y,x+w,y+h)]}]}}
        folder=display/"cards"/tag
        folder.mkdir(parents=True)
        with Image.open(paths[0]) as im:
            ink=measure.components(im,row)
            by_box={tuple(v["bounds"]):v["id"] for v in ink}
            targets=[item["noise_150"]]+([item["comma_150"]] if item["comma_150"] else [])
            if set(by_box)!=set(map(tuple,targets)):
                raise ValueError(f"{tag}: 成分と描画の対応が一対一にならない")
            attachments={
                f"{tag}-boundary.png":measure.numeric.view_pair(row,source,paths,tag,font),
                f"{tag}-axis.png":measure.ruler(im,row,tag,font),
                f"{tag}-component-numbers.png":prior.numbered(im,row,ink,tag,font),
            }
        for filename,content in attachments.items():
            path=folder/filename
            core.save_once(path,content)
            files.append(path)
        hashes=[core.sha(folder/name) for name in attachments]
        for arm in ("old","new"):
            prompt=reading_prompt(template[f"Y005/{arm}"]["request"],arm,tag)
            if item["digits"] in prompt or "青い" in prompt:
                raise ValueError("別試験の条件か正解が依頼に含まれる")
            jobs[f"{tag}/{arm}"]={"cards":str(folder),"request":{
                "ids":[tag],"prompt":prompt,"images":list(attachments),"image_sha256":hashes}}
        links[tag]={"entry":len(rows),"partitions":[],"category":position,"shape":item["shape"],"side":item["side"],
                    "ink":ink,"stroke_id":by_box[tuple(item["noise_150"])],
                    "comma_id":by_box[tuple(item["comma_150"])] if item["comma_150"] else None}
        coverage[position,item["shape"],item["side"]]+=1
        rows.append(row)
    if coverage!={(k,s,x):1 for k in KINDS for s in ("dot","short-slash") for x in ("left","right")}:
        raise ValueError("位置・筆画の形・左右の組合せがそろわない")
    selection=display/"selection.json"
    core.save_once(selection,core.encoded({"selected":rows}))
    files.append(selection)
    pilot.SAMPLES=rows
    return {"jobs":jobs,"mapping":links,
            "files":core.load(core.LOCK)["inputs"]|{str(p):core.sha(p) for p in files}}


def markers(text):
    count=0
    out=[]
    for char in core.ref.NORMALIZE(text):
        if char in "0123456789":
            count+=1
        else:
            out.append((count,char))
    return out


def trace_old(vote, known):
    if vote["status"]!="readable":
        return vote,None
    text, separator, suffix=vote["text"].partition("||")
    answer=core.ref.decoded({**vote,"text":text},[])
    marks=markers(answer["text"])
    if not marks:
        return answer,[] if not separator or suffix.strip()=="-" else None
    tags=[TRACE.fullmatch(v.strip()) for v in suffix.split("|")] if separator else []
    if len(tags)!=len(marks) or not all(tags):
        return answer,None
    built=[]
    for mark,tag in zip(marks,tags,strict=True):
        position,glyph=mark
        kind=tag[3]
        ident=None if tag[2]=="?" else int(tag[2])
        valid_glyph=kind=="U" and glyph not in measure.SYMBOL.values() or measure.SYMBOL.get(kind)==glyph
        if int(tag[1])!=position or not valid_glyph or (ident is not None and ident not in known):
            return answer,None
        built.append((position,glyph,ident))
    ids=[v[2] for v in built if v[2] is not None]
    return answer,built if len(set(ids))==len(ids) else None


def trace_new(vote, link, left, width):
    ink=link["ink"]
    chosen=prior.identify(vote,ink,left,width)
    answer=measure.transcribe(chosen,ink)
    if chosen is None:
        return answer,None,None
    by_id={v["id"]:v for v in ink}
    kept=[]
    for gap,(char,ident) in chosen[1].items():
        item=by_id[ident]
        if item["cross_axis_center_inside"] and item["axis_overlap"]*2>=item["axis_length"]:
            kept.append((gap,char,ident))
    return answer,kept,chosen


def attribution(answer, trace, link):
    if answer["status"]!="readable":
        return ["no-final-text"]
    if trace is None:
        return ["uncertain-source"]
    if not trace:
        return ["no-mark-in-text"]
    signals={"uncertain-source"} if any(item[2] is None for item in trace) else set()
    for _,char,ident in trace:
        if ident==link["stroke_id"]:
            signals.add("black-stroke-adopted")
            if char==",":
                signals.add("black-stroke-as-comma")
        elif ident is not None and ident==link["comma_id"] and char!=",":
            signals.add("comma-as-other-mark")
    return sorted(signals) or ["comma-source-correct"]


def observed_candidates(vote):
    if vote["status"]!="readable":
        return []
    return [(int(m[2]),measure.SYMBOL[m[3]]) for term in vote["text"].split("|")[1:]
            if (m:=prior.TUPLE.fullmatch(term))]


def score(args, receive=None):
    plan=core.load(pilot.LOCK)
    if core.sha(pilot.LOCK)!=args.sha256 or any(core.sha(Path(p))!=h for p,h in plan["files"].items()):
        raise ValueError("固定された画像・採点が変わっている")
    rows=core.load(pilot.OUT/"display/selection.json")["selected"]
    runtimes=pilot.audit.delivery.runtime({"gpt":args.codex,"claude":args.claude})
    accept=receive or pilot.outcome
    sessions,cases=set(),{}
    counts=defaultdict(lambda:defaultdict(lambda:defaultdict(Counter)))
    sources=defaultdict(lambda:defaultdict(lambda:defaultdict(Counter)))
    candidates=Counter()
    for job_name,job in plan["jobs"].items():
        name,arm=job_name.split("/")
        link=plan["mapping"][name]
        row=rows[link["entry"]]
        left,_,width,_=row["box"]
        votes,answers,traces,structures,receipt={},{},{},{},{}
        known={r["id"] for r in link["ink"]}
        for model in ("gpt","claude"):
            attempts=accept(args.sha256,job_name,model,job,runtimes[model])
            if not attempts or attempts[-1]["availability"]!="received" or attempts[-1]["session"] in sessions:
                raise ValueError(f"独立した原票が不足 {job_name} {model}")
            last=attempts[-1]
            receipt[model]=last["session"]
            sessions.add(last["session"])
            ballot=last["answers"][name]
            votes[model]=ballot
            if arm=="old":
                answers[model],traces[model]=trace_old(ballot,known)
            else:
                answers[model],traces[model],structures[model]=trace_new(ballot,link,left,width)
                reported=observed_candidates(ballot)
                ids={ident for ident,_ in reported}
                if link["stroke_id"] in ids:
                    candidates[f"{model}/black-stroke-candidate"]+=1
                if (link["stroke_id"],",") in reported:
                    candidates[f"{model}/black-stroke-candidate-as-comma"]+=1
                if link["comma_id"] in ids:
                    candidates[f"{model}/comma-candidate"]+=1
                if any(ident==link["comma_id"] and mark!="," for ident,mark in reported):
                    candidates[f"{model}/comma-candidate-as-other-mark"]+=1
                if len(reported)>1 and structures[model] is None:
                    candidates[f"{model}/unresolved-with-multiple-candidates"]+=1
        if arm=="old":
            pair,_=core.ref.aligned(answers["gpt"],answers["claude"],width)
        else:
            pair=answers["gpt"] if structures["gpt"]==structures["claude"] else core.ref.UNKNOWN
        answers["pair"]=pair
        traces["pair"]=traces["gpt"] if traces["gpt"]==traces["claude"] else None
        target=core.ref.NORMALIZE(row["effective"])
        events={m:base.changes(core.ref,a,target) for m,a in answers.items()}
        measurements={m:attribution(a,traces[m],link) for m,a in answers.items()}
        for scope in ("all",link["category"],link["shape"],link["side"]):
            for model,labels in events.items():
                counts[scope][arm][model].update(labels)
                sources[scope][arm][model].update(measurements[model])
        cases[job_name]={"target":target,"category":link["category"],"shape":link["shape"],"side":link["side"],
                         "component_ids":{"comma":link["comma_id"],"black-stroke":link["stroke_id"]},
                         "votes":votes,"final":answers,"classification":events,"source":measurements,
                         "traces":traces,"session_ids":receipt}
    core.save_once(HERE/"comparison.json",core.encoded({"scope":"development-only","lock_sha256":args.sha256,
                   "sessions":len(sessions),"counts":counts,"adopted_components":sources,
                   "new_reported_candidates":candidates,"cases":cases}))
    print("最終転記", {k:dict(v["pair"]) for k,v in counts["all"].items()},flush=True)
    print("成分", {k:dict(v["pair"]) for k,v in sources["all"].items()},flush=True)


if __name__=="__main__":
    launch.configure()
    if len(sys.argv)>1 and sys.argv[1]=="compare":
        cli=argparse.ArgumentParser(description=__doc__)
        cli.add_argument("command",choices=("compare",))
        cli.add_argument("--sha256",required=True)
        cli.add_argument("--codex",required=True,type=Path)
        cli.add_argument("--claude",required=True,type=Path)
        score(cli.parse_args())
    else:
        pilot.snapshot=snapshot
        pilot.main()
