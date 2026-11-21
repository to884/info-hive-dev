"""固定画像の横投影から区画を示す開発試験。"""

import argparse
import importlib.util
import io
import math
from pathlib import Path
import re

import numpy as np
from PIL import Image, ImageDraw, ImageFont

HERE = Path(__file__).resolve().parent
BASE = HERE.parent / "v11-ordered-image-pilot/run.py"
spec = importlib.util.spec_from_file_location("previous_order", BASE)
old = importlib.util.module_from_spec(spec)
spec.loader.exec_module(old)
cards, readers = old.cards, old.readers
LOCK = HERE / "lock.json"
OUT = cards.CORPUS / "reference-v11-column-slot-pilot"
GUIDE = (
    "『位置の目印』のA、B、Cなどは、固定150 DPIのインクの分かれ方から付けた番号です。"
    "紙面の行や表の見出しが分かる『広い周囲』も見て、枠内の字の並びが縦書きの複数列か横書きかを確認します。"
    "所属する字の全文を、目印の列ごとに分けます。各列の中では自然な読む順です。"
    "縦書きならtextを V|A:甲|B:乙、横書きなら H|A:甲|B:乙 の形式にします。列名は実際の画像のものを使ってください。"
    "入れる字がない目印はA:のように空にします。宣言した列をすべて一度ずつ含めます。"
    "番号を文字の所属の根拠にはせず、枠とインクを見ます。目印が本当の列と対応しないときは未決定にします。"
)


def intervals(ink):
    edges = np.flatnonzero(np.diff(np.r_[False, ink > 0, False]))
    bands = [(int(a), int(b)) for a,b in zip(edges[::2],edges[1::2],strict=True)]
    j = 0
    while j < len(bands):
        a,b = bands[j]
        if b-a <= 3 and int(ink[a:b].sum()) <= 6 and len(bands)>1:
            adjacent = []
            if j:
                adjacent.append((a-bands[j-1][1],j-1))
            if j+1 < len(bands):
                adjacent.append((bands[j+1][0]-b,j+1))
            distance,k = min(adjacent)
            if distance <= 4:
                first, last = sorted((j,k))
                bands[first:last+1] = [(bands[first][0],bands[last][1])]
                j = max(0,first-1)
                continue
        j+=1
    return bands


def blob(image):
    buffer = io.BytesIO()
    image.save(buffer,"PNG")
    return buffer.getvalue()


def asset(view, manifest, name):
    target = next(p for p in view["images"] if p["kind"] == name)
    p = cards.OUT / "source-assets" / target["image"]
    if old.SHA(p) != manifest["source_assets"][p.name]:
        raise ValueError("固定した元表示と異なる")
    with Image.open(p) as image:
        return image.convert("RGB")


def aid(row, entry, origin, ident, font):
    x,y,w,h = row["box"]
    p = cards.CORPUS / "probe-v4/png" / (row["key"]+".png")
    if old.SHA(p) != entry["sha"]["150_dpi"]:
        raise ValueError("元の固定150 DPIと違う")
    with Image.open(p) as fixed:
        pix = np.asarray(fixed.convert("L"))
    dark = (pix[y:y+h,x:x+w] < 170).sum(axis=0)
    slots = intervals(dark)
    if not 2 <= len(slots) <= 9:
        raise ValueError(f"目印を使える短い枠ではない: {len(slots)} 区画")
    labels = [chr(ord("A")+i) for i in range(len(slots))]
    low, high = entry["source_view"]["views"]
    before = asset(low,origin,"framed")
    left,top,right,bottom = low["target_rectangle"]
    box = (max(0,left-42), max(0,top-33), min(before.width,right+42), min(before.height,bottom+33))
    photo = before.crop(box)
    panel = Image.new("RGB",(max(210,photo.width+16),photo.height+53),"white")
    panel.paste(photo,(8,47))
    draw = ImageDraw.Draw(panel)
    draw.text((4,2),f"{ident}  位置の目印  固定150 DPI",font=font,fill="#222222")
    boundaries = [0,*[(b+c)//2 for (_,b),(c,_) in zip(slots,slots[1:])],w]
    for a in boundaries:
        loc=8+left-box[0]+3*a
        draw.line((loc,31,loc,46),fill="#b80d18",width=1)
    for label,(a,b) in zip(labels,slots,strict=True):
        loc=8+left-box[0]+3*(a+b)/2
        draw.text((int(loc)-5,26),label,font=font,fill="#16345a")
    context = asset(high,origin,"framed")
    l,t,r,b = high["target_rectangle"]
    frame = (max(0,math.floor(l)-100),max(0,math.floor(t)-105),
             min(context.width,math.ceil(r)+100),min(context.height,math.ceil(b)+105))
    shown = context.crop(frame)
    wide = Image.new("RGB",(max(240,shown.width+16),shown.height+42),"white")
    ImageDraw.Draw(wide).text((4,3),f"{ident}  広い周囲  固定450 DPI",font=font,fill="#222222")
    wide.paste(shown,(8,39))
    return {f"{ident}-slots.png":blob(panel),f"{ident}-wide.png":blob(wide)},labels,slots


def material():
    prior, visuals = old.material()
    if prior != old.LOAD(old.LOCK):
        raise ValueError("先行試験の固定が異なる")
    pages=old.LOAD(cards.SOURCE)["selected"]
    origin=old.LOAD(cards.PACKS)
    assets={m["entry"]:m["image_reference"] for p in origin["packs"].values() for m in p["mapping"].values()}
    font_file=cards.base.FONTS/"meiryo.ttc"
    font=ImageFont.truetype(font_file, size=17)
    packs, output={},{}
    for name,meta in prior["packs"].items():
        if not meta["kind"].startswith("columns"):
            continue
        i=meta["entry"]
        ident,=meta["request"]["ids"]
        supplements, labels, spans=aid(pages[i],assets[i],origin,ident,font)
        images=visuals[name]|supplements
        if not pages[i]["targets"]["image"]["known"]:
            raise ValueError("正解の既知の対照と開発行だけを集計する")
        packs[name]={"entry":i,"kind":meta["kind"],"slots":labels,"spans":[list(span) for span in spans],
                     "request":{"images":list(images),"ids":[ident],"image_sha256":[readers.sha(b) for b in images.values()],
                                "prompt":old.INTRO+GUIDE+old.FORMAT+ident+"。目印は "+ "、".join(labels)+"。"}}
        output[name]=images
    pins=(BASE,old.HERE/"lock.json",old.HERE/"result.json",Path(__file__),HERE/"protocol.md",cards.PACKS,font_file)
    return {"models":old.MODELS,"inputs":{str(p):old.SHA(p) for p in pins},"packs":packs},output


def decode(answer, kind, width, counts):
    if answer is None or answer["status"]=="unreadable":
        return None
    if answer["status"]=="empty":
        return "empty",(),""
    style,*slots=answer["text"].split("|")
    if style not in {"H","V"} or len(slots)<2:
        return None
    by_label={}
    for slot in slots:
        token=re.fullmatch(r"([A-I]):(.*)",slot.strip())
        if not token or token[1] in by_label:
            return None
        by_label[token[1]]=old.NORMALIZE(token[2])
    expected=tuple(range(counts[width]))
    if tuple(ord(k)-ord("A") for k in sorted(by_label)) != expected:
        return None
    ordered=sorted(by_label,reverse=style=="V")
    body="".join(by_label[k] for k in ordered)
    return (style+"|"+"|".join(by_label[k] for k in ordered),expected,body) if body else None


if __name__=="__main__":
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument("action",choices=("prepare","run"))
    parser.add_argument("--codex",type=Path)
    parser.add_argument("--claude",type=Path)
    parser.add_argument("--lock-sha256")
    args=parser.parse_args()
    manifest,images=material()
    if args.action=="prepare":
        if LOCK.exists() or OUT.exists():
            raise FileExistsError("開発用の固定を上書きしない")
        for arm,meta in manifest["packs"].items():
            target=OUT/"cards"/arm
            target.mkdir(parents=True)
            for name,b in images[arm].items():
                (target/name).write_bytes(b)
        readers.save_once(LOCK,readers.encoded(manifest))
        print(old.SHA(LOCK),len(images),"行",flush=True)
    else:
        rows=old.LOAD(cards.SOURCE)["selected"]
        counts={}
        for pack in manifest["packs"].values():
            width=rows[pack["entry"]]["box"][2]
            if counts.setdefault(width,len(pack["slots"]))!=len(pack["slots"]):
                raise ValueError("同じ幅の試料で目印の数が異なる")
        old.HERE,old.OUT,old.LOCK=HERE,OUT,LOCK
        old.decode=lambda answer,kind,width:decode(answer,kind,width,counts)
        old.execute(args,manifest,images)
