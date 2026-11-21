"""固定した合成・既知の縦列を旧と新の指示で3回ずつ独立に読む。"""

from collections import Counter, defaultdict
from importlib.util import module_from_spec, spec_from_file_location
from pathlib import Path
import random
import sys

from PIL import Image, ImageDraw, ImageFont

HERE = Path(__file__).resolve().parent
ORDER = HERE.parent / "v72-short-frame-order-pilot"
spec = spec_from_file_location("order_before_repeats", ORDER / "run.py")
order = module_from_spec(spec)
spec.loader.exec_module(order)
core, launch, pilot, grade = order.core, order.launch, order.pilot, order.grade
pilot.HERE = HERE
pilot.OUT = core.CORPUS / "reference-v79-order-repeat-pilot"
pilot.LOCK, pilot.RESULT = HERE / "lock.json", HERE / "pair.json"
FONT = launch.render.typeface
TEMPLATES = (
    ("伸", "納"), ("節", "所"), ("録", "和"), ("列", "右"), ("会", "郡"), ("布", "物"),
    ("北", "潮"), ("門", "石"), ("小", "橋"),
    ("月", "村"), ("春", "風"), ("高", "田"),
)
CONTEXT = "北海道東京青空中央九州東西南県法条航空長崎番室雪年区第一届所北東"


def proof(tag, group, position, expected_pair):
    left, right = 125, 143
    top = (82, 94, 108)[position % 3]
    bbox = left - 2, top - 1, right + 15, top + 16
    horizontal = group != "synthetic-vertical"
    label = "T01"
    originals, display = {}, {}
    for scale, dpi in ((1, 150), (3, 450)):
        font = ImageFont.truetype(FONT, size=(15 + (position % 2))*scale)
        canvas = Image.new("RGB", (260*scale, 180*scale), (255, 255, 255))
        draw = ImageDraw.Draw(canvas)

        def glyph(x, y, char):
            draw.text((x*scale,y*scale),char,font=font,fill=(35,35,35),anchor="lt",stroke_width=0)

        context_rng = random.Random(5519 + position)
        if group != "horizontal-table":
            for column, x in enumerate((65, 84, 106, left, right, 165, 187)):
                for row, y in enumerate(range(top-60,top+64,18)):
                    if x in (left,right) and abs(y-top)<(32 if horizontal else 10):
                        continue
                    glyph(x,y,context_rng.choice(CONTEXT))
        if group == "horizontal-table":
            for x in (49,109,177,226):
                draw.line((x*scale,32*scale,x*scale,153*scale),fill=(81,81,81),width=scale)
            for y in range(top-50,top+67,19):
                for x in (61,80,125,143,194,211):
                    if x in (left,right) and abs(y-top)<17:
                        continue
                    glyph(x,y,context_rng.choice(CONTEXT))
            for y in (39,153):
                draw.line((50*scale,y*scale,225*scale,y*scale),fill=(81,81,81),width=scale)
        for x, char in zip((left,right),expected_pair,strict=True):
            glyph(x,top,char)
        x,y,r,b = (q*scale for q in bbox)
        frame=canvas.copy()
        ImageDraw.Draw(frame).rectangle((x,y,r,b),outline="#b01120",width=scale)
        originals[dpi]=(canvas,frame)
        if dpi == 150:
            header=40
            visible=frame.resize((520,360),Image.Resampling.NEAREST)
            card=Image.new("RGB",(540,400),"white")
            draw=ImageDraw.Draw(card)
            draw.text((12,6),f"{label}  行と列のつながり  固定150 DPI",font=ImageFont.truetype(FONT,size=16),fill="black")
            card.paste(visible,(8,header))
            display[f"{label}-layout.png"]=launch.render.orientation.blob(card)
        else:
            crop=(x-24,y-21,r+24,b+21)
            cuts=[image.crop(crop) for image in (frame,canvas)]
            result=Image.new("RGB",(2*cuts[0].width+24,cuts[0].height+45),"white")
            titles=ImageDraw.Draw(result)
            face=ImageFont.truetype(FONT,size=15)
            titles.text((8,6),f"{label}  固定450 DPI",font=face,fill="black")
            for i,(part,name) in enumerate(zip(cuts,("枠あり","枠なし"),strict=True)):
                offset=6+i*(part.width+10)
                titles.text((offset,25),name,font=face,fill="black")
                result.paste(part,(offset,44))
            display[f"{label}-close-01.png"]=launch.render.orientation.blob(result)
    output=pilot.OUT/"display/synthetic"/tag
    output.mkdir(parents=True)
    for dpi,(plain,framed) in originals.items():
        for image,kind in ((plain,"plain"),(framed,"framed")):
            core.save_once(output/f"fixed-{dpi}-{kind}.png",launch.render.orientation.blob(image))
    for name,data in display.items():
        core.save_once(output/name,data)
    intro=("固定150 DPIの赤い枠で所属を判定し、450 DPIの枠あり・なしで字形を確認してください。"
           "割当軸xは字全体の左右のインク長さの半分以上と上下のインク中心が枠内です。"
           "字の形を意味から補わず、元の紙面を見てください。")
    form=("分からない字・所属・列が残る場合はstatusをunreadable、textを?としてください。"
          "字が一つもなければstatusをempty、textを空文字にします。"
          "転記できたときはstatusをreadableにします。JSONだけを返してください。"
          '形式は {"answers":[{"id":"T01","status":"readable","text":"転記"}]} です。対象IDは T01。')
    req={"ids":[label],"images":list(display),"image_sha256":[core.sha(output/n) for n in display],
         "prompt": intro + launch.neutral.SHORT + form}
    a,b=expected_pair
    expected=a+b if horizontal else b+a
    return output, req, {"key":tag,"line_index":0,"box":[bbox[0],bbox[1],bbox[2]-bbox[0],bbox[3]-bbox[1]],
                         "allocation_axis":"x","effective":expected}, {
        "image_reference":{"sha":None}, "partitions":[], "design":group}


def snapshot():
    core.verify_methods()
    previous=core.load(ORDER/"lock.json")
    if any(core.sha(Path(p))!=h for p,h in previous["files"].items()):
        raise ValueError("既知の列順試験に固定した依頼が異なる")
    root=core.CORPUS/"reference-v72-short-frame-order-pilot/display/selection.json"
    old_rows=core.load(root)["selected"]
    cases=[]
    for key,data in previous["mapping"].items():
        if data["group"]=="reading-order":
            req=previous["jobs"][f"{key}/old"]
            cases.append((key,Path(req["cards"]),req["request"],old_rows[data["entry"]],data,"known-vertical"))
    for i,pair in enumerate(TEMPLATES):
        group="synthetic-vertical" if i<6 else "horizontal-table" if i<9 else "horizontal-in-vertical"
        tag=f"fixture-{i+1:02d}"
        cards, req, row, mapping=proof(tag,group,i,pair)
        cases.append((tag,cards,req,row,mapping,group))
    if len(cases)!=19:
        raise ValueError("既知の列順7行と合成12行を固定できない")
    jobs, mappings, rows = {}, {}, []
    for tag, cards, req, row, mapping, group in cases:
        if [core.sha(cards/n) for n in req["images"]]!=req["image_sha256"] or req["prompt"].count(launch.neutral.SHORT)!=1:
            raise ValueError("旧と新の同じ固定画像を確認できない")
        newer={**req,"prompt":req["prompt"].replace(launch.neutral.SHORT,order.GUIDE,1)}
        binding={**mapping,"entry":len(rows)}
        rows.append(row)
        for repeat in range(1,4):
            name=f"{tag}-r{repeat}"
            mappings[name]={**binding,"group":group,"category":group,
                            "arms":{"old":binding,"new":binding}}
            jobs[f"{name}/old"]={"cards":str(cards),"request":req}
            jobs[f"{name}/new"]={"cards":str(cards),"request":newer}
    selection=pilot.OUT/"display/selection.json"
    core.save_once(selection,core.encoded({"selected":rows}))
    screen=pilot.OUT/"screen/candidates.json"
    pinned=(Path(__file__),HERE/"protocol.md",HERE/"screen.py",Path(grade.__file__),Path(pilot.__file__),
            ORDER/"lock.json",ORDER/"run.py",root,selection,screen,FONT)
    pilot.SAMPLES=rows
    return {"jobs":jobs,"mapping":mappings,"files":core.load(core.LOCK)["inputs"]|
            {str(p):core.sha(p) for p in pinned}}


def judge_cases(args):
    digest,plan=core.sha(pilot.LOCK),core.load(pilot.LOCK)
    if args.sha256!=digest or any(core.sha(Path(p))!=h for p,h in plan["files"].items()):
        raise ValueError("固定した試験の入力が異なる")
    runtime=pilot.audit.delivery.runtime({"gpt":args.codex,"claude":args.claude})
    rows=core.load(pilot.OUT/"display/selection.json")["selected"]
    seen,cases=set(),{}
    counts=defaultdict(lambda:defaultdict(Counter))
    reverse_rows=defaultdict(set)
    for name, job in plan["jobs"].items():
        tag,arm=name.split("/")
        group=plan["mapping"][tag]["group"]
        entry=plan["mapping"][tag]["arms"][arm]
        row=rows[entry["entry"]]
        known=core.ref.NORMALIZE(row["effective"])
        label,=job["request"]["ids"]
        choices={}
        for role in ("gpt","claude"):
            attempts=pilot.outcome(digest,name,role,job,runtime[role])
            if not attempts or attempts[-1]["availability"]!="received":
                raise ValueError(f"画像の票を受領できていない {name} {role}")
            last=attempts[-1]
            if last["session"] in seen:
                raise ValueError("独立した新規セッションが重複")
            seen.add(last["session"])
            choices[role]=core.ref.decoded(last["answers"][label],entry["partitions"])
        pair,points=core.ref.aligned(choices["gpt"],choices["claude"],row["box"][2])
        outcomes={k:grade.verdict(core.ref,v,known) for k,v in {**choices,"pair":pair}.items()}
        for role, outcome in outcomes.items():
            counts[group][arm][role+"-"+outcome]+=1
        inverse=(len(known)>1 and known!=known[::-1] and core.ref.NORMALIZE(choices["claude"]["text"])==known[::-1])
        if inverse:
            counts[group][arm]["opus-reverse"]+=1
            reverse_rows[(group,arm)].add(row["key"]+"/"+str(row["line_index"]))
        cases[name]={"row":row["key"],"line_index":row["line_index"],"group":group,"expected":known,
                     "outcomes":outcomes,"votes":choices,"two_vote":pair,"coordinates":points}
    relevant=counts["synthetic-vertical"]
    established=relevant["old"]["opus-reverse"]>=4 and len(reverse_rows[("synthetic-vertical","old")])>=2
    change=relevant["old"]["opus-reverse"]-relevant["new"]["opus-reverse"]>=4
    known=counts["known-vertical"]
    no_regression=known["new"]["opus-reverse"]<=known["old"]["opus-reverse"]
    for group in ("horizontal-table","horizontal-in-vertical"):
        for outcome in ("different","omitted","extra","unresolved","source-pending"):
            no_regression &= counts[group]["new"]["pair-"+outcome]<=counts[group]["old"]["pair-"+outcome]
    result={"scope":"development-only","counts":counts,"cases":cases,"lock_sha256":digest,
            "criterion":{"baseline_difficulty":established,"reduction":change,"no_regression":no_regression,
                         "passes_development_selection":established and change and no_regression}}
    core.save_once(HERE/"comparison.json",core.encoded(result))
    print(result["criterion"],flush=True)


if __name__=="__main__":
    launch.configure()
    if len(sys.argv)>1 and sys.argv[1]=="freeze":
        if pilot.LOCK.exists():
            raise FileExistsError("開発の反復比較は固定済み")
        core.save_once(pilot.LOCK,core.encoded(snapshot()))
        print(core.sha(pilot.LOCK),len(pilot.SAMPLES),"行、旧・新それぞれ3回",flush=True)
    elif len(sys.argv)>1 and sys.argv[1]=="compare":
        import argparse
        cli=argparse.ArgumentParser(description=__doc__)
        cli.add_argument("action",choices=("compare",))
        cli.add_argument("--sha256",required=True)
        cli.add_argument("--codex",type=Path,required=True)
        cli.add_argument("--claude",type=Path,required=True)
        judge_cases(cli.parse_args())
    else:
        pilot.main()
