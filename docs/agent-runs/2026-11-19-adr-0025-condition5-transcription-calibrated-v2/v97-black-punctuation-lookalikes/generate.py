"""黒いコンマとよく似た別の筆画を独立して描く開発用PDF。"""

from importlib.util import module_from_spec, spec_from_file_location
from io import BytesIO
from pathlib import Path

HERE=Path(__file__).resolve().parent
PARENT=HERE.parent/"v95-controlled-numeric-boundary/generate.py"
spec=spec_from_file_location("aligned_boundary_pdf",PARENT)
base=module_from_spec(spec)
spec.loader.exec_module(base)

# 各ページに位置4通りを2回ずつ配置。位置とページ上の順を離す。
ORDER=(("inside","outside","edge","no-comma","outside","inside","no-comma","edge"),
       ("edge","no-comma","inside","outside","no-comma","edge","outside","inside"))
base.NUMBERS=(("74652","28437","63841","39572","47286","91643","52867","81395"),
              ("97264","38162","58927","51638","73951","82469","65183","25749"))
PX=base.PX
WIDTH,HEIGHT=base.PAGE
original_layouts=base.layouts


def layouts():
    items=original_layouts()
    seen={}
    for row in items:
        page=row["page"]
        index=(int(row["id"][1:])-1)%8
        position=ORDER[page-1][index]
        key=(page,position)
        ordinal=seen.get(key,0)
        seen[key]=ordinal+1
        row["id"]="Z"+row["id"][1:]
        row["position"]=position
        row["noise"]=True
        row["shape"]=("short-slash","dot")[ordinal]
        row["side"]=("left","right")[(ordinal+page)%2]
        row["baseline"]+=13
        row["box"][1]+=13
        row["mark_x"]+=4
        row["right_x"]+=4
        row["box"][2]+=4
    return items


def black_stroke(doc,row):
    x=row["mark_x"]+(-5 if row["side"]=="left" else 7)
    # 字形を区別する手掛かりが少ない黒を用いる。位置と形は元PDFでのみ記録する。
    y=HEIGHT-(row["baseline"]-1)*PX
    if row["shape"]=="dot":
        doc.circle((x+1.35)*PX,y,1.28*PX,fill=1,stroke=0)
    else:
        mark=doc.beginPath()
        mark.moveTo(x*PX,y-PX)
        mark.lineTo((x+1.15)*PX,y-PX)
        mark.lineTo((x+2.6)*PX,y+1.95*PX)
        mark.lineTo((x+1.35)*PX,y+1.95*PX)
        mark.close()
        doc.drawPath(mark,fill=1,stroke=0)


def pdf(rows,digits,separator,rule):
    output=BytesIO()
    doc=base.Canvas(output,pagesize=base.PAGE,invariant=True,pageCompression=1)
    doc.setTitle("Numeric boundary development sample - black strokes")
    for page,(font,_) in enumerate(base.FONTS,1):
        doc.setFillColor(base.HexColor("#263449"))
        doc.setFont("Helvetica-Bold",14)
        doc.drawString(28,355,"Instrument summary")
        doc.setFont("Helvetica",8)
        doc.drawString(28,339,f"Development table / Page {page}")
        doc.setFillColor(base.HexColor("#e9edf3"))
        doc.rect(26,317,304,13,fill=1,stroke=0)
        doc.setFillColor(base.HexColor("#263449"))
        for x,label in ((29,"Reference"),(108,"Measurement"),(257,"Unit")):
            doc.drawString(x,321,label)
        for row in (r for r in rows if r["page"]==page):
            y=HEIGHT-row["baseline"]*PX
            if int(row["id"][1:])%2==0:
                doc.setFillColor(base.HexColor("#f2f5f8"))
                doc.rect(26,y-10,304,25,fill=1,stroke=0)
            doc.setFillColor(base.HexColor("#263449"))
            doc.setFont("Helvetica",8)
            doc.drawString(29,y,row["id"])
            doc.drawString(257,y,"counts")
            doc.setFillColor(base.HexColor("#181818"))
            if digits:
                doc.setFont(font,9)
                doc.drawString(row["text_x"]*PX,y,row["digits"][:2])
                doc.drawString(row["right_x"]*PX,y,row["digits"][2:])
            if separator and row["position"] in base.DELTA:
                base.comma(doc,row["mark_x"],row["baseline"]+2+base.DELTA[row["position"]])
            if rule:
                black_stroke(doc,row)
        doc.showPage()
    doc.save()
    return output.getvalue()


if __name__=="__main__":
    base.HERE=HERE
    base.layouts=layouts
    base.pdf=pdf
    base.main()
