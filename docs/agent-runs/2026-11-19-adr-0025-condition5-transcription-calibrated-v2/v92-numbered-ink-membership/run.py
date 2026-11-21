"""点の座標の目算を、固定画像から列挙した小さい成分の番号に置き換える。"""

import argparse
from importlib.util import module_from_spec, spec_from_file_location
from pathlib import Path
import re
import sys

from PIL import Image, ImageDraw, ImageFont

HERE = Path(__file__).resolve().parent
BASE = HERE.parent / "v90-numeric-ink-membership"
spec = spec_from_file_location("numeric_ink_membership", BASE / "run.py")
measure = module_from_spec(spec)
spec.loader.exec_module(measure)
core, launch, pilot = measure.core, measure.launch, measure.pilot
pilot.HERE = HERE
pilot.OUT = core.CORPUS / "reference-v92-numbered-ink-membership"
pilot.LOCK, pilot.RESULT = HERE / "lock.json", HERE / "pair.json"

NUMBERED = (
    "『小さい成分の番号』の下の横位置の目安と右の拡大図は、固定画素から機械的に分けた小さい部分です。"
    "番号は、見えた区切りのうちどの部分だったか示すために使えます。"
    "番号があるだけで記号だと決めず、数字の筆画や無関係の印には使いません。"
)
NUMBER_FORMAT = measure.FORMAT.replace(
    "|直前までの数字の個数:横位置:種類", "|直前までの数字の個数:成分番号:種類"
).replace(
    "横位置は『150 DPIの横座標』で見た記号のインクの中心を整数に丸めます。",
    "成分番号は『小さい成分の番号』でその記号を写した実際の番号です。"
)
TUPLE = re.compile(r"([0-9]+):([0-9]+):([CDTHS])")


def numbered(pixels, row, ink, label, font):
    x,y,w,h = row["box"]
    scale, left_margin, top = 4, 12, 29
    area = (max(x-6,0), max(y-6,0), min(x+w+6,pixels.width), min(y+h+8,pixels.height))
    photo = pixels.crop(area).convert("RGB")
    photo = photo.resize((photo.width*scale, photo.height*scale), Image.Resampling.NEAREST)
    diagram_x = left_margin + photo.width + 32
    height = max(top + photo.height + 55, 47 + 65*len(ink))
    canvas = Image.new("RGB", (diagram_x + 174,height), "white")
    draw = ImageDraw.Draw(canvas)
    draw.text((8,2), f"{label} 小さい成分の番号　固定150 DPI", font=font, fill="black")
    canvas.paste(photo, (left_margin,top))
    foot = top + photo.height
    for n, entry in enumerate(ink):
        l,t,r,b=entry["bounds"]
        marker = left_margin+round(((l+r)/2-area[0])*scale)
        bar_y = foot + 4 + 13*(n%3)
        draw.line((marker,foot,marker,bar_y+3),fill="#994037",width=2)
        draw.text((marker,bar_y+4),str(entry["id"]),anchor="mt",font=font,fill="#712714")
        clip = pixels.crop((max(l-3,0), max(t-3,0), min(r+3,pixels.width), min(b+3,pixels.height))).convert("RGB")
        zoom = clip.resize((clip.width*5,clip.height*5),Image.Resampling.NEAREST)
        pos_y = 30+n*65
        draw.text((diagram_x,pos_y),str(entry["id"]),font=font,fill="#712714")
        canvas.paste(zoom,(diagram_x+28,pos_y))
    return launch.render.orientation.blob(canvas)


def snapshot():
    core.verify_methods()
    previous = core.load(BASE/"lock.json")
    if any(core.sha(Path(path))!=digest for path,digest in previous["files"].items()):
        raise ValueError("固定済みの画素または測定の来歴が変わっている")
    detected = core.CORPUS/"reference-v90-numeric-ink-membership/display/selection.json"
    rows = core.load(detected)["selected"]
    display = pilot.OUT/"display"
    font = ImageFont.truetype(launch.render.typeface, size=16)
    mappings, jobs = previous["mapping"], {}
    files = previous["files"] | {str(p): core.sha(p) for p in (Path(__file__), HERE/"protocol.md", BASE/"lock.json")}
    for ref, current in previous["jobs"].items():
        case, arm = ref.split("/")
        bound = mappings[case]
        row = rows[bound["entry"]]
        req = current["request"]
        ident, = req["ids"]
        folder = display/"cards"/case
        folder.mkdir(parents=True, exist_ok=True)
        photo = folder/f"{ident}-component-numbers.png"
        if not photo.exists():
            for name, digest in zip(req["images"], req["image_sha256"], strict=True):
                origin = Path(current["cards"])/name
                if core.sha(origin) != digest:
                    raise ValueError("保存した添付の画素が異なる")
                cropped = folder/name
                core.save_once(cropped, origin.read_bytes())
                files[str(cropped)] = digest
            source = core.CORPUS/"probe-v4/png"/f"{row['key']}.png"
            with Image.open(source) as im:
                if measure.components(im,row)!=bound["ink"]:
                    raise ValueError("番号を付けた成分が保存されたものと異なる")
                core.save_once(photo, numbered(im,row,bound["ink"],ident,font))
            files[str(photo)] = core.sha(photo)
        prompt = req["prompt"]
        if arm == "new":
            if prompt.count(measure.FORMAT)!=1:
                raise ValueError("前の指示から成分番号を指定できない")
            prompt = prompt.replace(measure.FORMAT,NUMBER_FORMAT,1)
        jobs[ref] = {"cards":str(folder), "request":{**req,"prompt":prompt+NUMBERED,"images":[*req["images"],photo.name],
                                                      "image_sha256":[*req["image_sha256"],files[str(photo)]]}}
    output = display/"selection.json"
    core.save_once(output,core.encoded({"selected":rows}))
    files[str(output)] = core.sha(output)
    pilot.SAMPLES = rows
    return {"jobs":jobs,"mapping":mappings,"files":files}


def identify(vote, geometry, left, width):
    if vote["status"]!="readable":
        return None
    digits,*marks = vote["text"].split("|")
    if not re.fullmatch(r"[0-9]+",digits):
        return None
    known={x["id"]:(x["bounds"][0]+x["bounds"][2])/2-left for x in geometry}
    attached={}
    previous_x=-1
    for term in marks:
        match=TUPLE.fullmatch(term)
        if not match:
            return None
        after, ink_id = int(match[1]), int(match[2])
        x=known.get(ink_id,-1)
        if not (0<x<width and x>previous_x and 0<after<len(digits)) or (attached and after<=next(reversed(attached))):
            return None
        previous_x=x
        attached[after]=(measure.SYMBOL[match[3]],ink_id)
    return digits,attached


if __name__=="__main__":
    launch.configure()
    if len(sys.argv)>1 and sys.argv[1]=="compare":
        parser = argparse.ArgumentParser(description=__doc__)
        parser.add_argument("action", choices=("compare",))
        parser.add_argument("--sha256", required=True)
        parser.add_argument("--codex", required=True, type=Path)
        parser.add_argument("--claude", required=True, type=Path)
        measure.HERE=HERE
        measure.decompose=identify
        measure.score(parser.parse_args())
    else:
        pilot.snapshot=snapshot
        pilot.main()
