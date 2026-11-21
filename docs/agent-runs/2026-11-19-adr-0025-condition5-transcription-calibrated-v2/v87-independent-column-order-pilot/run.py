"""二系統が視認した書字の向きと位置順の転記を別々に照合する。"""

import argparse
from collections import Counter, defaultdict
from importlib.util import module_from_spec, spec_from_file_location
from pathlib import Path
import sys

HERE=Path(__file__).resolve().parent
STAGES=HERE.parent
BASE=STAGES/"v72-short-frame-order-pilot/run.py"
spec=spec_from_file_location("ordinary_short_order",BASE)
original=module_from_spec(spec)
spec.loader.exec_module(original)
core,launch,pilot,grade=original.core,original.launch,original.pilot,original.grade
pilot.HERE=HERE
pilot.OUT=core.CORPUS/"reference-v87-independent-column-order-pilot"
pilot.LOCK,pilot.RESULT=HERE/"lock.json",HERE/"pair.json"
GUIDE=(
    "『行と列のつながり』の元の配置から、枠が一つの横書き行、複数列の縦書き、単独一字のどれかを確認します。"
    "横書きならtextに H|全文 と書きます。全文は左端から右端へ読みます。"
    "縦書きの複数列なら、textは V|左端の列の本文|その右の列の本文 の形式です。"
    "列の中では上から下。列は画像上で左から右の順に記録し、枠に所属する字のある列を一度ずつ含めます。"
    "単独の一字なら S|一字 と書けます。枠の外は書きません。"
    "向きや列を決められないときは既定の判読不能の形式を使います。"
    "ここで説明した H、V、S と縦棒だけを本文に付け、見えない語や区切りは加えません。"
)


def snapshot():
    core.verify_methods()
    jobs,mappings,prepared={}, {}, []
    files=[Path(__file__),HERE/"protocol.md",BASE,Path(pilot.__file__),Path(grade.__file__)]
    for v, folder in (
            ("72", "short-frame-order-pilot"),
            ("82", "orientation-cues-pilot")):
        previous=STAGES/f"v{v}-{folder}"/"lock.json"
        selected=core.CORPUS/f"reference-v{v}-{folder}/display/selection.json"
        trial, rows = core.load(previous),core.load(selected)["selected"]
        if any(core.sha(Path(p))!=h for p,h in trial["files"].items()):
            raise ValueError("既に固定した対照画像の来歴が異なる")
        files.extend((previous,selected))
        for name,binding in trial["mapping"].items():
            if v=="82" and (not name.endswith("-r1") or not binding["category"].startswith("horizontal")):
                continue
            tag=f"{v}-{name}"
            entry=rows[binding["entry"]]
            saved=trial["jobs"][f"{name}/old"]
            req=saved["request"]
            cards=Path(saved["cards"])
            markers=launch.neutral.SHORT
            if req["prompt"].count(markers)!=1 or [core.sha(cards/f) for f in req["images"]]!=req["image_sha256"]:
                raise ValueError("元の旧指示と固定画像を一意に確認できない")
            group=binding["group"] if v=="72" else "synthetic-"+binding["category"]
            mappings[tag]={"entry":len(prepared),"partitions":[],"category":group}
            prepared.append(entry)
            jobs[f"{tag}/old"]=saved
            prompt=req["prompt"].replace(markers,GUIDE,1)
            jobs[f"{tag}/new"]={**saved,"request":{**req,"prompt":prompt}}
    if len(prepared)!=21:
        raise ValueError("既知の7行と14対照が揃わない")
    output=pilot.OUT/"display/selection.json"
    output.parent.mkdir(parents=True)
    core.save_once(output,core.encoded({"selected":prepared}))
    pilot.SAMPLES=prepared
    return {"jobs":jobs,"mapping":mappings,"files":core.load(core.LOCK)["inputs"]|
            {str(p):core.sha(p) for p in (*files,output)}}


def parts(vote):
    if vote["status"]!="readable":
        return None
    fields=vote["text"].split("|")
    mode,values=fields[0],tuple(core.ref.NORMALIZE(x) for x in fields[1:])
    if not all(values) or any(core.ref.MARK.search(x) or "⟦" in x or "⟧" in x for x in values):
        return None
    if (mode=="H" and len(values)==1) or (mode=="S" and len(values)==1 and len(values[0])==1):
        return mode,values
    if mode=="V" and len(values)>=2:
        return mode,values
    return None


def compiled(components):
    if components is None:
        return core.ref.UNKNOWN
    mode, values=components
    text="".join(reversed(values) if mode=="V" else values)
    return {"status":"readable","text":text}


def score(expected, codex, claude):
    plan=core.load(pilot.LOCK)
    if core.sha(pilot.LOCK)!=expected or any(core.sha(Path(p))!=h for p,h in plan["files"].items()):
        raise ValueError("画像と二票の固定記録が異なる")
    runtimes=pilot.audit.delivery.runtime({"gpt":codex,"claude":claude})
    rows=core.load(pilot.OUT/"display/selection.json")["selected"]
    output, seen={},set()
    totals=defaultdict(lambda:defaultdict(Counter))
    for task, job in plan["jobs"].items():
        name,arm=task.split("/")
        bound=plan["mapping"][name]
        row=rows[bound["entry"]]
        label,=job["request"]["ids"]
        votes={}
        for role in ("gpt","claude"):
            history=pilot.outcome(expected,task,role,job,runtimes[role])
            if not history or history[-1]["availability"]!="received" or history[-1]["session"] in seen:
                raise ValueError("両版の新規二票が独立してそろわない")
            last=history[-1]
            seen.add(last["session"])
            votes[role]=last["answers"][label]
        if arm=="new":
            gpt,opus=map(parts,votes.values())
            joint=compiled(gpt) if gpt==opus else core.ref.UNKNOWN
        else:
            gpt,opus=map(lambda v:core.ref.decoded(v,[]),votes.values())
            joint,_=core.ref.aligned(gpt,opus,row["box"][2])
        verdict=grade.verdict(core.ref,joint,core.ref.NORMALIZE(row["effective"]))
        totals[bound["category"]][arm][verdict]+=1
        output[task]={"group":bound["category"],"page":row["key"],"line_index":row["line_index"],"raw":votes,
                      "structure":[gpt,opus],"agreement":joint,"state":verdict}
    core.save_once(HERE/"comparison.json",core.encoded({"scope":"development-only","plan_sha256":expected,
                   "counts":totals,"cases":output}))
    print({g:{a:dict(v) for a,v in by_arm.items()} for g,by_arm in totals.items()},flush=True)


if __name__=="__main__":
    launch.configure()
    if len(sys.argv)>1 and sys.argv[1]=="compare":
        parser=argparse.ArgumentParser(description=__doc__)
        parser.add_argument("action",choices=("compare",))
        parser.add_argument("--sha256",required=True)
        parser.add_argument("--codex",required=True,type=Path)
        parser.add_argument("--claude",required=True,type=Path)
        a=parser.parse_args()
        score(a.sha256,a.codex,a.claude)
    else:
        pilot.snapshot=snapshot
        pilot.main()
