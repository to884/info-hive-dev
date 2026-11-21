"""周囲から読む方向が判断できる短い枠を固定して、旧・新の指示を比べる。"""

from importlib.util import module_from_spec, spec_from_file_location
from pathlib import Path
import sys

from PIL import Image, ImageDraw, ImageFont

HERE = Path(__file__).resolve().parent
BASE = HERE.parent / "v79-order-repeat-pilot/run.py"
spec = spec_from_file_location("compare_clear_orientation", BASE)
trial = module_from_spec(spec)
spec.loader.exec_module(trial)
core, launch, pilot, order = trial.core, trial.launch, trial.pilot, trial.order
pilot.HERE = HERE
pilot.OUT = core.CORPUS / "reference-v82-orientation-cues-pilot"
pilot.LOCK, pilot.RESULT = HERE / "lock.json", HERE / "result.json"
FONT = launch.render.typeface
CELLS = (("中央合同庁舎",2,"table"),("一般交通区分",2,"table"),("年度運用方針",2,"table"),
         ("情報資源管理",2,"caption"),("広域連携組織",2,"caption"),("改正規則概要",2,"caption"))
COLUMNS = (("情報連携","制度更新"),("内閣決定","政府広報"),("計画概要","政策評価"),("交通運用","施設案内"))


def scene(scale, index, group, contents, cut):
    surface=Image.new("RGB",(365*scale,220*scale),"white")
    draw=ImageDraw.Draw(surface)
    font=ImageFont.truetype(FONT,size=(17+index%2)*scale)
    small=ImageFont.truetype(FONT,size=16*scale)
    def line(coords, fill=(72,72,72)):
        draw.line(tuple(v*scale for v in coords),fill=fill,width=scale)
    def text_at(x,y,text,face=font):
        draw.text((x*scale,y*scale),text,font=face,fill=(25,25,25),anchor="lt")

    x,y=123,101
    if group in {"table","caption"}:
        spacing=21
        if group=="table":
            for yy in range(49,171,35):
                line((63,yy,298,yy))
            for xx in (63,298):
                line((xx,49,xx,154))
            for row,sample in zip((63,133),("管轄地域連絡先","実施年月日一覧"),strict=True):
                for g,c in enumerate(sample):
                    text_at(x+spacing*g,row,c)
        else:
            for yy in (87,125):
                line((94,yy,279,yy))
            for xx in (94,279):
                line((xx,87,xx,125))
            for col, sample in enumerate(("都道府県","調査結果","自治体等","関係部署","利用案内")):
                for k,c in enumerate(sample):
                    text_at(33+col*15,37+k*26,c,small)
            for col,sample in enumerate(("年度方針","改正対照","運営会議")):
                for k,c in enumerate(sample):
                    text_at(285+col*24,70+k*29,c,small)
        for j,char in enumerate(contents):
            text_at(x+spacing*j,y,char)
        left=x+spacing*cut
        right=left+spacing*2-1
        bbox=(left-1,y-2,right,y+20)
        answer=contents[cut:cut+2]
        group="horizontal-"+group
    else:
        left,right=144,170
        offset=index%3-1
        for col,(xx,source) in enumerate(zip((left,right),contents,strict=True)):
            for j,char in enumerate(source):
                text_at(xx, y-48+j*24+(offset if col else 0), char)
        for xx,source in ((86,"官報公告"),(119,"審議要旨"),(203,"施行状況"),(231,"附記参考")):
            for j,char in enumerate(source):
                text_at(xx,62+j*24,char,small)
        bbox=(left-2,y-4,right+17,y+19)
        answer=contents[1][2]+contents[0][2]
        group="vertical"
    return surface,bbox,answer,group


def visual(index, classification, contents, cut, path):
    cards={}
    proof=[]
    for scale,dpi in ((1,150),(3,450)):
        image,box,answer,group=scene(scale,index,classification,contents,cut)
        framed=image.copy()
        bounds=tuple(x*scale for x in box)
        ImageDraw.Draw(framed).rectangle(bounds,outline="#bc1129",width=scale)
        for name,im in ((f"fixed-{dpi}-plain.png",image),(f"fixed-{dpi}-framed.png",framed)):
            target=path/name
            core.save_once(target,launch.render.orientation.blob(im))
            proof.append(target)
        small=ImageFont.truetype(FONT,size=16)
        if dpi==150:
            panel=Image.new("RGB",(750,490),"white")
            panel.paste(framed.resize((730,440),Image.Resampling.NEAREST),(8,38))
            ImageDraw.Draw(panel).text((8,8),"T01  行と列のつながり  固定150 DPI",font=small,fill="black")
            cards["T01-layout.png"]=launch.render.orientation.blob(panel)
        else:
            l,t,r,b=bounds
            area=(l-48,t-24,r+48,b+24)
            shots=[im.crop(area) for im in (framed,image)]
            pane=Image.new("RGB",(2*shots[0].width+22,shots[0].height+55),"white")
            painter=ImageDraw.Draw(pane)
            painter.text((6,2),"T01  固定450 DPI",font=small,fill="black")
            for j,(shot,caption) in enumerate(zip(shots,("枠あり","枠なし"),strict=True)):
                x=7+j*(shot.width+8)
                painter.text((x,26),caption,font=small,fill="black")
                pane.paste(shot,(x,49))
            cards["T01-close-01.png"]=launch.render.orientation.blob(pane)
    for name, data in cards.items():
        core.save_once(path/name,data)
    return cards,proof,box,answer,group


def snapshot():
    core.verify_methods()
    jobs,mapping,rows,physical={}, {}, [], []
    for n,(content,cut,group) in enumerate((*CELLS, *((entry,0,"vertical") for entry in COLUMNS))):
        name=f"fixture-{n+1:02d}"
        folder=pilot.OUT/"display/cards"/name
        folder.mkdir(parents=True)
        cards,proof,box,answer,group=visual(n,group,content,cut,folder)
        physical.extend(proof)
        prefix=("固定150 DPIの元の枠で所属を判定し、450 DPIの枠あり・なしで字形を確認します。"
                "割当軸xは字全体の左右のインク長さの半分以上と上下のインク中心が枠内です。"
                "字の形を意味から補いません。")
        suffix=("分からない字・所属・列が残る場合はstatusをunreadable、textを?としてください。"
                "字が一つもなければstatusをempty、textを空文字にします。JSONだけを返してください。"
                '形式は {"answers":[{"id":"T01","status":"readable","text":"転記"}]} です。対象IDは T01。')
        common={"ids":["T01"],"images":list(cards),"image_sha256":[core.sha(folder/i) for i in cards]}
        l,t,r,b=box
        binding={"entry":len(rows),"partitions":[],"category":group}
        rows.append({"key":name,"line_index":0,"box":[l,t,r-l,b-t],"effective":answer})
        for repeat in (1,2):
            tag=f"{name}-r{repeat}"
            mapping[tag]=binding
            for arm,guide in (("old",launch.neutral.SHORT),("new",order.GUIDE)):
                jobs[f"{tag}/{arm}"]={"cards":str(folder),"request":{**common,"prompt":prefix+guide+suffix}}
    selected=pilot.OUT/"display/selection.json"
    core.save_once(selected,core.encoded({"selected":rows}))
    files=(Path(__file__),Path(pilot.__file__),HERE/"protocol.md",BASE,Path(order.__file__),FONT,selected,*physical)
    pilot.SAMPLES=rows
    return {"jobs":jobs,"mapping":mapping,
            "files":core.load(core.LOCK)["inputs"]|{str(p):core.sha(p) for p in files}}


if __name__=="__main__":
    launch.configure()
    pilot.snapshot=snapshot
    pilot.main()
