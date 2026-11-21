"""小点に重なる別の文字描画を再レビュー後に再検査する。"""

from contextlib import closing
import ctypes
from importlib.util import module_from_spec, spec_from_file_location
from pathlib import Path

import numpy as np
from pypdf import PdfReader

HERE=Path(__file__).resolve().parent
spec=spec_from_file_location("background_graphic_controls",HERE/"check_background_controls.py")
controls=module_from_spec(spec)
spec.loader.exec_module(controls)
method=controls.method
core,trace=method.core,method.trace


def remove_text_inside(blob, index, area, isolate=None):
    raw=trace.raw
    with closing(trace.pypdfium2.PdfDocument(blob)) as doc, closing(doc[index-1]) as page:
        found=[]
        for obj in page.get_objects(filter=[raw.FPDF_PAGEOBJ_TEXT]):
            enabled=ctypes.c_long()
            if not raw.FPDFPageObj_GetIsActive(obj,ctypes.byref(enabled)):
                raise RuntimeError("描画状態を取得できない")
            if enabled.value:
                found.append(obj)
        select=found if isolate is None else [found[isolate]]
        for obj in select:
            if not raw.FPDFPageObj_SetIsActive(obj,False):
                raise RuntimeError("文字を非表示にできない")
        with closing(page.render(scale=150/72)) as image:
            return np.asarray(image.to_pil().convert("RGB"))[area].copy()


def main():
    method.launch.configure()
    core.verify_methods()
    prooffile=HERE/"result.json"
    result=core.load(prooffile)
    candidate=result["command"]
    x,y,r,b=result["background"]["context_150"]
    area=np.s_[y:b,x:r]
    filename,hash_pdf,number=method.prior.previous.packets.old.lookup()[1][result["page"]]
    src=core.CORPUS/filename
    blob=src.read_bytes()
    if trace.sha(blob)!=hash_pdf:
        raise ValueError("元のPDFと異なる")
    page=PdfReader(src).pages[number-1]
    f=page["/Resources"]["/Font"][candidate["font"]]
    child=f["/DescendantFonts"][0].get_object()
    descriptor=child["/FontDescriptor"]
    if child.get("/Subtype")!="/CIDFontType0" or "/CIDToGIDMap" in child:
        raise ValueError("Adobe-Japan1のCIDを別のグリフ番号に置き換えるフォント")
    if descriptor["/FontFile3"].get("/Subtype")!="/CIDFontType0C":
        raise ValueError("埋め込まれたCFFのCIDフォントを確認できない")
    removed=method.recreate(blob,number,(candidate["index"],candidate["array_index"],candidate["byte_offset"],
                                          candidate["font"],candidate["operator"].encode()))
    isolated=method.render(removed,1,150)[area]
    underlay=remove_text_inside(blob,number,area)
    affected=int(np.any(underlay!=isolated,axis=2).sum())
    if affected:
        raise ValueError("点を消した周囲の画素に別の文字の重なりがある")
    simple=controls.make("wide-image")
    from pypdf import PdfWriter
    from pypdf.generic import DecodedStreamObject
    from io import BytesIO
    writer=PdfWriter()
    page=writer.add_page(PdfReader(BytesIO(simple)).pages[0])
    source=page.get_contents().get_data()
    source=source.replace(b"1 g BT /Test 7 Tf",b"0.45 g BT /Test 16 Tf 45.5 45 Td (o) Tj ET 1 g BT /Test 7 Tf")
    stream=DecodedStreamObject()
    stream.set_data(source)
    page.replace_contents(stream)
    out=BytesIO()
    writer.write(out)
    fixture=out.getvalue()
    context=np.s_[85:124,85:124]
    one=remove_text_inside(fixture,1,context,isolate=-1)
    all_removed=remove_text_inside(fixture,1,context)
    shadow=int(np.any(one!=all_removed,axis=2).sum())
    if not shadow:
        raise ValueError("暗い別の文字の重なりを対照で検出できない")
    response={"scope":"development-only","same_context_when_all_text_is_hidden":affected==0,
              "dark_underlaid_text_control_changed_pixels":shadow,"font_subtype":"CIDFontType0",
              "font_program_subtype":"CIDFontType0C","cid_to_gid_map":False,
              "inputs":{str(p):core.sha(p) for p in (Path(__file__),prooffile,HERE/"run.py",
                      HERE/"check_background_controls.py",src)}}
    core.save_once(HERE/"text-underlay-control.json",core.encoded(response))
    print(affected,shadow,flush=True)


if __name__=="__main__":
    main()
