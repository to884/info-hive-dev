"""別の開発用PDFから作った同じ画像で、v92の旧指示と新指示を比べる。"""

import argparse
from collections import Counter, defaultdict
from difflib import SequenceMatcher
from importlib.util import module_from_spec, spec_from_file_location
from pathlib import Path
import sys

from PIL import Image, ImageFont

HERE = Path(__file__).resolve().parent
STAGES = HERE.parent
V92 = STAGES / "v92-numbered-ink-membership"
spec = spec_from_file_location("numbered_membership_reference", V92 / "run.py")
prior = module_from_spec(spec)
spec.loader.exec_module(prior)
measure, core, launch, pilot = prior.measure, prior.core, prior.launch, prior.pilot
pilot.HERE = HERE
pilot.OUT = core.CORPUS / "reference-v95-controlled-numeric-boundary"
pilot.LOCK, pilot.RESULT = HERE / "lock.json", HERE / "transport-pair.json"
STYLES = ("inside", "edge", "outside", "no-comma")
GUIDE = (
    "枠への所属は『固定150 DPI』の図の枠の上下端を基準に判断し、450 DPIは字形の確認に使います。"
    "青い横線は表の目印です。本文の数字や記号には加えません。"
)


def snapshot():
    core.verify_methods()
    fixed = core.load(HERE / "physical-truth.json")
    if core.sha(HERE / "development-fixed-frames.pdf") != fixed["pdf_sha256"]:
        raise ValueError("事前固定の開発PDFと異なる")
    files = [Path(__file__), HERE/"protocol.md", HERE/"generate.py", HERE/"physical-truth.json",
             HERE/"development-fixed-frames.pdf", V92/"lock.json", Path(prior.__file__),
             Path(measure.__file__), Path(measure.ink.__file__), Path(pilot.__file__), launch.render.typeface]
    pages = HERE / "fixed-pages"
    for name, digest in fixed["page_png_sha256"].items():
        path = pages/name
        if core.sha(path) != digest:
            raise ValueError("固定済みのPDFの画素と異なる")
        files.append(path)
    template = core.load(V92/"lock.json")["jobs"]
    font = ImageFont.truetype(launch.render.typeface, size=16)
    rows, mappings, jobs = [], {}, {}
    display = pilot.OUT/"display"
    total_coverage = Counter()
    for item in fixed["rows"]:
        name, position = item["id"], item["position"]
        paths = tuple(pages/f"page-{item['page']}-{dpi}.png" for dpi in (150,450))
        row = {"key": f"development-fixed-frames-p{item['page']:02d}", "line_index": len(rows)+1,
               "box":item["box"], "allocation_axis":"x", "effective":item["expected"]}
        x,y,w,h = row["box"]
        for dpi in (150,450):
            scale=dpi//150
            digits=item[f"digits_{dpi}"]
            if not (x*scale<digits[0]<digits[2]<(x+w)*scale
                    and y*scale<=digits[1]<digits[3]<(y+h)*scale):
                raise ValueError(f"{name}: 数字が {dpi} DPI の固定枠に収まらない")
            drawn=item[f"comma_{dpi}"]
            if drawn and (drawn[1]+drawn[3])/2-(y+h)*scale!={"inside":-1,"edge":0,"outside":1}[position]*scale:
                raise ValueError(f"{name}: コンマ中心の測定が {dpi} DPI で固定と異なる")
        source = {"source_view":{"views":[{}, {"target_rectangle":[3*z for z in (x,y,x+w,y+h)]}]}}
        folder = display/"cards"/name
        folder.mkdir(parents=True)
        renders = {}
        with Image.open(paths[0]) as im:
            ink = measure.components(im, row)
            measured = {tuple(o["bounds"]):o for o in ink}
            for member in ("comma_150", "noise_150"):
                if item[member] is not None and tuple(item[member]) not in measured:
                    raise ValueError(f"{name}: {member} を独立した成分として確認できない")
            if item["comma_150"] is not None:
                comma = measured[tuple(item["comma_150"])]
                lower_delta = (comma["bounds"][1]+comma["bounds"][3])/2 - (y+h)
                if lower_delta != {"inside":-1,"edge":0,"outside":1}[position]:
                    raise ValueError(f"{name}: 下端と中心の差が事前の分類と違う")
                if comma["cross_axis_center_inside"] != (position!="outside") or comma["axis_overlap"]!=comma["axis_length"]:
                    raise ValueError(f"{name}: 所属が既存の式と違う")
            if item["noise_150"] is not None:
                noise = measured[tuple(item["noise_150"])]
                if not noise["cross_axis_center_inside"] or noise["axis_overlap"]!=noise["axis_length"]:
                    raise ValueError(f"{name}: 誤報対照の筆画は枠内が必要")
            expected_ink = int(item["comma_150"] is not None) + int(item["noise_150"] is not None)
            if len(ink) != expected_ink:
                raise ValueError(f"{name}: 設計したコンマと余分な筆画以外の追加成分がある")
            renders = {
                f"{name}-boundary.png":measure.numeric.view_pair(row,source,paths,name,font),
                f"{name}-axis.png":measure.ruler(im,row,name,font),
                f"{name}-component-numbers.png":prior.numbered(im,row,ink,name,font),
            }
        filenames = list(renders)
        for filename, content in renders.items():
            path=folder/filename
            core.save_once(path,content)
            files.append(path)
        hashes = [core.sha(folder/filename) for filename in filenames]
        for arm in ("old","new"):
            earlier = template[f"88-pack-373-outside/{arm}"]["request"]
            if earlier["ids"] != ["N006"] or earlier["prompt"].count("N006")!=2:
                raise ValueError("元の比較指示を確認できない")
            jobs[f"{name}/{arm}"]={"cards":str(folder), "request":{
                "ids":[name], "prompt":earlier["prompt"].replace("N006",name)+GUIDE,
                "images":filenames, "image_sha256":hashes,
            }}
        total_coverage[position,item["noise"]] += 1
        noise_label = "near-stroke" if item["noise"] else "clean"
        mappings[name] = {"entry":len(rows), "partitions":[], "category":f"{position}/{noise_label}",
                          "position":position, "noise":item["noise"], "ink":ink,
                          "comma_id":measured[tuple(item["comma_150"])]["id"] if item["comma_150"] else None,
                          "noise_id":measured[tuple(item["noise_150"])]["id"] if item["noise_150"] else None}
        rows.append(row)
    if total_coverage != {(position,noise):2 for position in STYLES for noise in (False,True)}:
        raise ValueError("4条件×筆画の有無を各2行固定できない")
    selection = display/"selection.json"
    core.save_once(selection, core.encoded({"selected":rows}))
    files.append(selection)
    pilot.SAMPLES=rows
    # 採点に使う前に、公式の固定済みコードと入力も検査する。
    return {"jobs":jobs, "mapping":mappings,"files":core.load(core.LOCK)["inputs"] |
            {str(path):core.sha(path) for path in files}}


def changes(reference, answer, target):
    if answer["status"] != "readable" or reference.MARK.search(answer["text"]):
        return ["unresolved"]
    read = reference.NORMALIZE(answer["text"])
    if read == target:
        return ["same"]
    operations = SequenceMatcher(None,target,read,autojunk=False).get_opcodes()
    result=[]
    if any(kind in ("delete","replace") for kind,*_ in operations):
        result.append("omitted")
    if any(kind in ("insert","replace") for kind,*_ in operations):
        result.append("extra")
    return result


def score(args, receive=None):
    plan=core.load(pilot.LOCK)
    if core.sha(pilot.LOCK)!=args.sha256 or any(core.sha(Path(path))!=digest for path,digest in plan["files"].items()):
        raise ValueError("事前固定した画像・正解または手順が変わっている")
    source = core.load(pilot.OUT/"display/selection.json")["selected"]
    runtime = pilot.audit.delivery.runtime({"gpt":args.codex,"claude":args.claude})
    get_attempt = receive or pilot.outcome
    counts = defaultdict(lambda: defaultdict(lambda: defaultdict(Counter)))
    cases, sessions, diagnostics = {}, set(), Counter()
    for job_name, job in plan["jobs"].items():
        name,arm=job_name.split("/")
        link=plan["mapping"][name]
        row=source[link["entry"]]
        x,_,w,_=row["box"]
        votes, receipt={},{}
        for model in ("gpt","claude"):
            history=get_attempt(args.sha256,job_name,model,job,runtime[model])
            if not history or history[-1]["availability"]!="received" or history[-1]["session"] in sessions:
                raise ValueError(f"独立した原票が揃っていない {job_name} {model}")
            record=history[-1]
            votes[model]=record["answers"][name]
            receipt[model]=record["session"]
            sessions.add(record["session"])
        ink=link["ink"]
        if arm=="old":
            compatible={m:core.ref.decoded(v,[]) for m,v in votes.items()}
            pair,_=core.ref.aligned(*compatible.values(),w)
            structured={}
        else:
            structured={m:prior.identify(v,ink,x,w) for m,v in votes.items()}
            compatible={m:measure.transcribe(v,ink) for m,v in structured.items()}
            pair=compatible["gpt"] if structured["gpt"]==structured["claude"] else core.ref.UNKNOWN
        source_check={}
        if arm=="new":
            for model, vote in votes.items():
                tags=[prior.TUPLE.fullmatch(term) for term in vote["text"].split("|")[1:]]
                ids=[int(term[2]) for term in tags if term]
                noise=link["noise_id"] is not None and link["noise_id"] in ids
                comma=link["comma_id"] is not None and link["comma_id"] in ids
                wrong_but_same=noise and compatible[model]=={"status":"readable","text":row["effective"]}
                source_check[model]={"picked_blue_rule":noise,"picked_comma":comma,"wrong_component_but_same":wrong_but_same}
                for event, present in source_check[model].items():
                    if present:
                        diagnostics[f"{model}/{event}"]+=1
        answers={**compatible,"pair":pair}
        target=core.ref.NORMALIZE(row["effective"])
        events={m:changes(core.ref,v,target) for m,v in answers.items()}
        group=link["category"]
        noise_label="near-stroke" if link["noise"] else "clean"
        for model, marks in events.items():
            for category in ("total", group, link["position"], noise_label):
                counts[category][arm][model].update(marks)
        cases[job_name]={"target":target,"group":group,"votes":votes,"decoded":answers,"structure":structured,
                         "classification":events,"v92_verdict":{m:measure.grade.verdict(core.ref,v,target) for m,v in answers.items()},
                         "sessions":receipt,"source_check":source_check}
    core.save_once(HERE/"comparison.json",core.encoded({"scope":"development-only", "lock_sha256":args.sha256,
                  "counts":counts,"cases":cases, "sessions":len(sessions),"component_diagnostics":diagnostics}))
    for group in ("total",*STYLES,"near-stroke","clean"):
        print(group,{arm:dict(model["pair"]) for arm,model in counts[group].items()},flush=True)


if __name__=="__main__":
    launch.configure()
    if len(sys.argv)>1 and sys.argv[1]=="compare":
        parser=argparse.ArgumentParser(description=__doc__)
        parser.add_argument("command",choices=("compare",))
        parser.add_argument("--sha256",required=True)
        parser.add_argument("--codex",required=True,type=Path)
        parser.add_argument("--claude",required=True,type=Path)
        score(parser.parse_args())
    else:
        pilot.snapshot=snapshot
        pilot.main()
