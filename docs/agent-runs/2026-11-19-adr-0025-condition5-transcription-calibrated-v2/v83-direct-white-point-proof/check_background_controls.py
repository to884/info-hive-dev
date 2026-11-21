"""白描画の合成対照で、広い画像と小さい図形を分けられるかを確かめる。"""

import io
from importlib.util import module_from_spec, spec_from_file_location
from pathlib import Path

import numpy as np
from pypdf import PdfWriter
from pypdf.generic import DecodedStreamObject, DictionaryObject, NameObject, NumberObject

HERE=Path(__file__).resolve().parent
spec=spec_from_file_location("exact_white_point_background",HERE/"run.py")
method=module_from_spec(spec)
spec.loader.exec_module(method)
KEY=NameObject
SCALE=150/72
POINT=(98,98,111,111)
FLAGS={"150_origin":[0,100],"150_matrix":[[SCALE,0],[0,-SCALE]]}


def make(shape):
    writer=PdfWriter()
    page=writer.add_blank_page(width=100,height=100)
    yy,xx=np.mgrid[:100,:100]
    blackish=((xx+yy)%23+28).astype(np.uint8)
    source=DecodedStreamObject()
    source.set_data(np.repeat(blackish[:,:,None],3,axis=2).tobytes())
    source.update({KEY("/Type"):KEY("/XObject"),KEY("/Subtype"):KEY("/Image"),
                   KEY("/Width"):NumberObject(100),KEY("/Height"):NumberObject(100),
                   KEY("/ColorSpace"):KEY("/DeviceRGB"),KEY("/BitsPerComponent"):NumberObject(8)})
    font=DictionaryObject({KEY("/Type"):KEY("/Font"),KEY("/Subtype"):KEY("/Type1"),KEY("/BaseFont"):KEY("/Helvetica")})
    page[KEY("/Resources")]=DictionaryObject({KEY("/XObject"):DictionaryObject({KEY("/Bg"):writer._add_object(source)}),
                                               KEY("/Font"):DictionaryObject({KEY("/Test"):writer._add_object(font)})})
    background=b"q 100 0 0 100 0 0 cm /Bg Do Q"
    small_shape=b"47 50 m 47 54 53 54 53 50 c 53 46 47 46 47 50 c f"
    white_letter=b"1 g BT /Test 7 Tf 48 48 Td (o) Tj ET"
    overlays={"wide-image":white_letter,
             "white-graphic":b"1 g "+small_shape,
             "letter-over-dark-graphic":b"0 g "+small_shape+b" "+white_letter}
    commands=DecodedStreamObject()
    commands.set_data(background+b" "+overlays[shape])
    page.replace_contents(commands)
    buffer=io.BytesIO()
    writer.write(buffer)
    return buffer.getvalue()


def main():
    controls={}
    for state in ("wide-image","white-graphic","letter-over-dark-graphic"):
        document=make(state)
        try:
            proof=method.dark_wide_background(document,1,POINT,FLAGS)
        except ValueError as e:
            proof={"held":str(e)}
        controls[state]=proof
    if ("held" in controls["wide-image"] or "held" not in controls["white-graphic"]
            or "held" not in controls["letter-over-dark-graphic"] or 0x2026 in method.allowed):
        raise ValueError("広い地色と、文字でない点か重なりの対照を区別できない")
    if method.inside((1,1,10,10),(2,2,9,9),4):
        raise ValueError("小図形の外接範囲を広い地色として許した")
    files=(Path(__file__),HERE/"run.py",HERE/"result.json")
    method.core.save_once(HERE/"background-controls.json",method.core.encoded({
        "scope":"development-only","cases":controls,"ellipsis_excluded":True,
        "inputs":{str(p):method.core.sha(p) for p in files}}))
    print(controls,flush=True)


if __name__=="__main__":
    main()
