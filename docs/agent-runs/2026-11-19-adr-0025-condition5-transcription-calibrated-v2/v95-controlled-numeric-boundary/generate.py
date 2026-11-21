"""同じ枠でコンマだけを上下し、二つの解像度の位置を確かめる開発PDF。"""

import argparse
from hashlib import sha256
from io import BytesIO
import json
import os
from pathlib import Path
import subprocess
from tempfile import TemporaryDirectory

import numpy as np
from PIL import Image
from reportlab.lib.colors import HexColor
from reportlab.pdfbase.pdfmetrics import registerFont, stringWidth
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.pdfgen.canvas import Canvas

HERE=Path(__file__).resolve().parent
PX=.48
PAGE=(360, 384)
FONTS=(("LabSans","arial.ttf"),("LabSerif","times.ttf"))
NUMBERS=(("92438","58174","36185","49726","67258","81954","24376","71485"),
         ("73856","62419","15942","28673","94183","47319","56824","91562"))
KINDS=("inside","edge","outside","no-comma")
DELTA={"inside":-1,"edge":0,"outside":1}


def sha(path):
    return sha256(path.read_bytes()).hexdigest()


def layouts():
    items=[]
    for page, numbers in enumerate(NUMBERS,1):
        for index,data in enumerate(numbers):
            baseline=161+72*index
            text_x=226
            dx=round(stringWidth(data[:2],FONTS[page-1][0],9)/PX)
            mark_x=text_x+dx+4
            right_x=mark_x+15
            right=round(right_x+stringWidth(data[2:],FONTS[page-1][0],9)/PX)+4
            items.append({"id":f"Y{len(items)+1:03d}","page":page,"digits":data,
                          "position":KINDS[index//2],"noise":bool((index+page)%2),
                          "box":[text_x-5,baseline-15,right-(text_x-5),17],
                          "baseline":baseline,"text_x":text_x,"mark_x":mark_x,"right_x":right_x})
    return items


def comma(doc,left,center):
    top=center-3
    def xy(x,y):
        return (left+x)*PX,PAGE[1]-(top+y)*PX
    p=doc.beginPath()
    p.moveTo(*xy(.8,0))
    p.lineTo(*xy(3.5,0))
    p.curveTo(*xy(4.1,0),*xy(4,1),*xy(4,2.4))
    p.curveTo(*xy(4,3.95),*xy(2.45,5.3),*xy(1.2,6))
    p.lineTo(*xy(0,6))
    p.lineTo(*xy(0,4.8))
    p.curveTo(*xy(1.1,4.4),*xy(1.6,3.5),*xy(1.75,3.05))
    p.lineTo(*xy(.45,3.05))
    p.lineTo(*xy(.45,.55))
    p.close()
    doc.drawPath(p,fill=1,stroke=0)


def pdf(rows,digits,separator,rule):
    output=BytesIO()
    doc=Canvas(output,pagesize=PAGE,invariant=True,pageCompression=1)
    doc.setTitle("Development numeric frames - laboratory measurements")
    for page,(font,_) in enumerate(FONTS,1):
        doc.setFillColor(HexColor("#16304b"))
        doc.setFont("Helvetica-Bold",14)
        doc.drawString(28,353,"Laboratory measurements")
        doc.setFont("Helvetica",8)
        doc.drawString(28,337,f"Development sample / Page {page}")
        doc.setFillColor(HexColor("#e6effa"))
        doc.rect(26,312,304,14,fill=1,stroke=0)
        doc.setFillColor(HexColor("#16304b"))
        for x,label in ((29,"Reference"),(108,"Observation"),(257,"Unit")):
            doc.drawString(x,316,label)
        for row in (r for r in rows if r["page"]==page):
            y=PAGE[1]-row["baseline"]*PX
            if int(row["id"][1:])%2==0:
                doc.setFillColor(HexColor("#f3f7fd"))
                doc.rect(26,y-11,304,27,fill=1,stroke=0)
            doc.setFillColor(HexColor("#24364d"))
            doc.setFont("Helvetica",8)
            doc.drawString(29,y,row["id"])
            doc.drawString(257,y,"counts")
            doc.setFillColor(HexColor("#181818"))
            if digits:
                doc.setFont(font,9)
                doc.drawString(row["text_x"]*PX,y,row["digits"][:2])
                doc.drawString(row["right_x"]*PX,y,row["digits"][2:])
            x=row["mark_x"]
            if separator and row["position"] in DELTA:
                comma(doc,x,row["baseline"]+2+DELTA[row["position"]])
            if rule and row["noise"]:
                doc.setFillColor(HexColor("#2076b2"))
                doc.rect((x+7)*PX,y-PX,6*PX,2*PX,stroke=0,fill=1)
        doc.showPage()
    doc.save()
    return output.getvalue()


def measure(full, omitted, row, k):
    x,y,w,h=[a*k for a in row["box"]]
    t,l,r,b=y-5*k,x-4*k,x+w+4*k,y+h+6*k
    source=full[row["page"]-1][t:b,l:r]
    control=omitted[row["page"]-1][t:b,l:r]
    threshold=int(np.median(source))-64
    ys,xs=np.nonzero((source<threshold)&(control>=threshold))
    if not len(xs):
        return None
    return [int(xs.min())+l,int(ys.min())+t,int(xs.max())+1+l,int(ys.max())+1+t]


def render(pop,path,tmp,dpi):
    subprocess.run([str(pop),"-png","-r",str(dpi),str(path),str(tmp)],check=True)
    paths=[tmp.with_name(f"{tmp.name}-{n}.png") for n in range(1,3)]
    arrays=[]
    for source in paths:
        with Image.open(source) as im:
            arrays.append(np.array(im.convert("L")))
    return paths,arrays


def main():
    cli=argparse.ArgumentParser(description=__doc__)
    cli.add_argument("--pdftoppm",required=True,type=Path)
    a=cli.parse_args()
    out=HERE/"development-fixed-frames.pdf"
    fixed=HERE/"fixed-pages"
    specification=HERE/"physical-truth.json"
    if any(p.exists() for p in (out,fixed,specification)):
        raise FileExistsError("固定した開発PDFを上書きしない")
    fonts={key:Path(os.environ["WINDIR"])/"Fonts"/name for key,name in FONTS}
    for key,path in fonts.items():
        registerFont(TTFont(key,str(path)))
    rows=layouts()
    with TemporaryDirectory(prefix="adr25-v95-") as temp:
        scratch=Path(temp)
        scenes={"full":(True,True,True),"no-comma":(True,False,True),
                "no-rule":(True,True,False),"no-digits":(False,True,True)}
        for key,layers in scenes.items():
            (scratch/f"{key}.pdf").write_bytes(pdf(rows,*layers))
        images={}
        for dpi in (150,450):
            renders={name:render(a.pdftoppm,scratch/f"{name}.pdf",scratch/f"{name}-{dpi}",dpi) for name in scenes}
            images[dpi]=renders["full"][0]
            for row in rows:
                k=dpi//150
                data=renders["full"][1]
                box=measure(data,renders["no-comma"][1],row,k)
                ink=measure(data,renders["no-rule"][1],row,k)
                digits=measure(data,renders["no-digits"][1],row,k)
                x,y,w,h=[i*k for i in row["box"]]
                if row["position"] in DELTA:
                    if box is None or (box[1]+box[3])/2-(y+h)!=DELTA[row["position"]]*k:
                        raise ValueError(f"{row['id']}: {dpi} DPIのコンマ中心が正解と異なる: {box}, {y+h}")
                elif box is not None:
                    raise ValueError("コンマなしの対照にコンマの画素がある")
                if (ink is not None)!=row["noise"] or (ink and not y<(ink[1]+ink[3])/2<y+h):
                    raise ValueError("青い罫線片の配置が正解と異なる")
                if digits is None or not (x<digits[0] and digits[2]<x+w and y<=digits[1] and digits[3]<y+h):
                    raise ValueError(f"{row['id']}: {dpi} DPIの数字の全画素が枠に収まらない {digits}")
                row[f"comma_{dpi}"],row[f"noise_{dpi}"],row[f"digits_{dpi}"]=box,ink,digits
                number=row["digits"]
                row["expected"]=number[:2]+","+number[2:] if row["position"] in ("inside","edge") else number
        fixed.mkdir()
        out.write_bytes((scratch/"full.pdf").read_bytes())
        hashes={}
        for dpi,paths in images.items():
            for i,source in enumerate(paths,1):
                saved=fixed/f"page-{i}-{dpi}.png"
                saved.write_bytes(source.read_bytes())
                hashes[saved.name]=sha(saved)
    report={"scope":"new-synthetic-development-pdf","pdf_sha256":sha(out),"page_png_sha256":hashes,
            "font_sha256":{k:sha(v) for k,v in fonts.items()},"rows":rows}
    specification.write_text(json.dumps(report,ensure_ascii=False,indent=2)+"\n",encoding="utf-8")
    print(len(rows), "枠、両解像度で中心差を確認、PDF SHA-256",sha(out))


if __name__=="__main__":
    main()
