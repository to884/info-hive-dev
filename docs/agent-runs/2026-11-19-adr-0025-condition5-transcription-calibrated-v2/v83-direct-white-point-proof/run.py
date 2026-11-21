"""白抜きの小点の二バイトと、その描画だけを消した差を確認する。"""

from contextlib import closing
import ctypes
import io
from importlib.util import module_from_spec, spec_from_file_location
from pathlib import Path

import numpy as np
from PIL import Image
from pypdf import PdfReader, PdfWriter
from pypdf.generic import ArrayObject, ByteStringObject, NumberObject

HERE = Path(__file__).resolve().parent
STAGES = HERE.parent
BASE = STAGES / "v80-textured-point-source-pilot/run.py"
spec = spec_from_file_location("inspected_white_mark", BASE)
prior = module_from_spec(spec)
spec.loader.exec_module(prior)
core, launch, trace = prior.core, prior.launch, prior.trace
allowed = {0x30FB: 638}


def font_ids(page, description):
    allowed_codes = []
    for key, record in page["/Resources"]["/Font"].items():
        font = record.get_object()
        children = font.get("/DescendantFonts")
        if font.get("/Encoding") != "/Identity-H" or not children:
            continue
        child = children[0].get_object()
        if str(child.get("/BaseFont")).lstrip("/") != description["pdfium_font"]:
            continue
        descriptor = child["/FontDescriptor"]
        programs = [descriptor[name].get_data() for name in ("/FontFile", "/FontFile2", "/FontFile3") if name in descriptor]
        ros = child["/CIDSystemInfo"]
        cid, code = description["cid"], int(description["codepoint"], 16)
        cmap = font["/ToUnicode"].get_data()
        if not any(trace.sha(stream)==description["font_data_sha256"] for stream in programs):
            continue
        if (str(ros["/Registry"]),str(ros["/Ordering"]))!=("Adobe","Japan1"):
            continue
        if allowed.get(code)!=cid or trace.embedded_map(cmap).get(cid)!=code:
            continue
        allowed_codes.append(str(key))
    return allowed_codes


def direct_commands(page, fonts, cid):
    state = (None,0)
    stack, matched = [], []
    encoded=cid.to_bytes(2,"big")
    for n,(args,op) in enumerate(page.get_contents().operations):
        f,mode=state
        if op==b"q":
            stack.append(state)
        elif op==b"Q":
            state=stack.pop()
        elif op==b"Tf":
            state=(str(args[0]),mode)
        elif op==b"Tr":
            state=(f,int(args[0]))
        elif op in (b"Tj",b"TJ") and f in fonts and mode==0:
            runs=args if op==b"Tj" else args[0]
            for i,token in enumerate(runs):
                if not hasattr(token,"original_bytes"):
                    continue
                raw=token.original_bytes
                if len(raw)%2:
                    raise ValueError("CIDが二バイト境界にそろわない")
                matched.extend((n,i,k,f,op) for k in range(0,len(raw),2) if raw[k:k+2]==encoded)
    if stack:
        raise ValueError("元PDFの描画状態がそろわない")
    return matched


def recreate(blob, number, command=None):
    writer=PdfWriter()
    page=writer.add_page(PdfReader(io.BytesIO(blob)).pages[number-1])
    if command:
        n,i,k,_font,operation=command
        contents=page.get_contents()
        commands=contents.operations
        args,op=commands[n]
        if op!=operation:
            raise ValueError("固定した文字の描画命令が変化")
        pieces=list(args if op==b"Tj" else args[0])
        raw=pieces[i].original_bytes
        before=pieces[:i]+([ByteStringObject(raw[:k])] if k else [])
        after=([ByteStringObject(raw[k+2:])] if k+2<len(raw) else [])+pieces[i+1:]
        shifted=[]
        if before:
            shifted.append(([ArrayObject(before)],b"TJ"))
        shifted+= [([NumberObject(3)],b"Tr"),([ByteStringObject(raw[k:k+2])],b"Tj"),([NumberObject(0)],b"Tr")]
        if after:
            shifted.append(([ArrayObject(after)],b"TJ"))
        commands[n:n+1]=shifted
        contents.operations=commands
        page.replace_contents(contents)
    buffer=io.BytesIO()
    writer.write(buffer)
    return buffer.getvalue()


def render(blob, leaf, dpi):
    with closing(trace.pypdfium2.PdfDocument(blob)) as document, closing(document[leaf-1]) as page:
        with closing(page.render(scale=dpi/72)) as image:
            return np.asarray(image.to_pil().convert("RGB")).copy()


def inside(outer, inner, margin=0):
    x,y,r,b=outer
    a,c,s,d=inner
    return x+margin<=a and y+margin<=c and r-margin>=s and b-margin>=d


def dark_wide_background(blob, number, rect, flags):
    raw=trace.raw
    left,top,right,bottom=rect
    width,height=right-left,bottom-top
    area=np.s_[top-height:bottom+height,left-width:right+width]
    origin, matrix=np.asarray(flags["150_origin"]), np.asarray(flags["150_matrix"])
    with closing(trace.pypdfium2.PdfDocument(blob)) as doc, closing(doc[number-1]) as page:
        def show():
            with closing(page.render(scale=150/72)) as img:
                return np.asarray(img.to_pil().convert("RGB"))[area].copy()
        def toggle(obj, visible):
            if not raw.FPDFPageObj_SetIsActive(obj,visible):
                raise RuntimeError("頁の描画を切り分けられない")
        active=[]
        for obj in page.get_objects():
            value=ctypes.c_long()
            if not raw.FPDFPageObj_GetIsActive(obj,ctypes.byref(value)):
                raise RuntimeError("頁の描画の表示状態を確かめられない")
            if value.value:
                active.append(obj)
        for obj in active:
            if obj.type == raw.FPDF_PAGEOBJ_TEXT:
                toggle(obj,False)
        dark=show()
        if dark.shape!=(3*height,3*width,3) or dark.max()>=150:
            raise ValueError("点を囲む範囲で広く続く暗い背景がない")
        sources=[]
        candidates=[]
        kinds={raw.FPDF_PAGEOBJ_IMAGE:"image",raw.FPDF_PAGEOBJ_SHADING:"shading"}
        for obj in active:
            if obj.type in (raw.FPDF_PAGEOBJ_TEXT, raw.FPDF_PAGEOBJ_FORM):
                continue
            x,y,r,b=obj.get_bounds()
            points=np.asarray([matrix@(np.asarray(p)-origin) for p in ((x,y),(x,b),(r,y),(r,b))])
            a,c=points.min(axis=0); s,d=points.max(axis=0)
            if a>=right+width or s<=left-width or c>=bottom+height or d<=top-height:
                continue
            toggle(obj,False)
            try:
                difference=np.any(show()!=dark,axis=2)
            finally:
                toggle(obj,True)
            if np.any(difference):
                bounds=tuple(float(v) for v in (a,c,s,d))
                context=(left-width,top-height,right+width,bottom+height)
                if (obj.type not in kinds or not inside(bounds,context,max(width,height))
                        or difference.mean()<.90):
                    raise ValueError(f"点の近くに独立した図形の背景がある {obj.type} {bounds} {difference.mean():.3f}")
                sources.append({"type":kinds[obj.type],"bounds_150":bounds,"changed_pixels":int(difference.sum())})
                candidates.append(trace.pointer(obj.raw))
        if not sources:
            raise ValueError("広い背景に点を結び付けられない")
        for obj in active:
            if obj.type != raw.FPDF_PAGEOBJ_FORM and trace.pointer(obj.raw) not in candidates:
                toggle(obj, False)
        if not np.array_equal(show(), dark):
            raise ValueError("記録した背景の描画だけでは点の周囲の固定画素を再現できない")
    return {"background_peak":int(dark.max()),"context_150":[left-width,top-height,right+width,bottom+height],
            "drawn_objects":sources}


def main():
    launch.configure()
    core.verify_methods()
    work=core.load(prior.diag)
    archived=core.load(BASE.parent/"result.json")
    item=work["cases"]["pack-364"]
    evidence=archived["outcomes"]["pack-364"]["evidence"]
    if archived["outcomes"]["pack-364"]["status"]!="same" or evidence["codepoint"]!="30FB" or item["polarity"]!="light":
        raise ValueError("一つの明るい丸と来歴が異なる")
    manifest=prior.fixed.delivery/"packages.json"
    document=core.load(manifest)
    binding,=document["packs"]["pack-364"]["mapping"].values()
    assets=binding["image_reference"]
    flags=assets["sha"]
    fine=assets["source_view"]["views"][1]
    name=next(v["image"] for v in fine["images"] if v["kind"]=="plain")
    original=prior.fixed.delivery/"source-assets"/name
    filename,digest,number=prior.previous.packets.old.lookup()[1][item["page"]]
    pdf=(core.CORPUS/filename).read_bytes()
    coarse=core.CORPUS/"probe-v4/png"/f"{item['page']}.png"
    if (trace.sha(pdf)!=digest or digest!=flags["pdf_sha256"] or core.sha(coarse)!=flags["150_dpi"]
            or core.sha(original)!=document["source_assets"][name]):
        raise ValueError("元PDFと固定した二つの解像度が異なる")
    actual=PdfReader(io.BytesIO(pdf)).pages[number-1]
    matched=direct_commands(actual,font_ids(actual,evidence),evidence["cid"])
    if len(matched)!=1:
        raise ValueError("公刊資料の一つの文字描画を原文から決められない")
    command,=matched
    blank=recreate(pdf,number)
    removed=recreate(pdf,number,command)
    shades=dark_wide_background(pdf,number,item["pixels_150"],flags)
    checks={}
    for dpi,png in ((150,coarse),(450,original)):
        data=render(pdf,number,dpi)
        native=render(blank,1,dpi)
        off=render(removed,1,dpi)
        if not np.array_equal(native,data):
            raise ValueError("変更しない再描画が元の頁と異なる")
        with Image.open(png) as im:
            raster=np.array(im.convert("RGB"))
        if dpi==450:
            l,t,r,b=fine["crop_rectangle"]
            view=data[t:b,l:r]
            a,c,z,d=item["pixels_450"]
            focus=(l+a-3,t+c-3,l+z+3,t+d+3)
        else:
            view=data
            focus=item["pixels_150"]
        if not np.array_equal(view,raster):
            raise ValueError("比較に使ったPDFの描画と固定画素が異なる")
        deltas=np.max(abs(native.astype("int16")-off.astype("int16")),axis=2)
        x,y,r,b=focus
        near=deltas[y:b,x:r].copy()
        deltas[y:b,x:r]=0
        other=int(np.count_nonzero(deltas))
        outside=int(deltas.max())
        if (dpi==150 and other) or outside>5 or (near>30).sum() < near.size*.25:
            raise ValueError("一つの符号の消失と、範囲外の描画を分けられない")
        checks[str(dpi)]={"area":focus,"local_painted_pixels":int(np.count_nonzero(near)),
                          "outside_changed":other,"outside_max_channel_delta":outside}
    n,i,k,font,op=command
    if 0x2026 in allowed or inside((1,1,10,10),(2,2,9,9),4):
        raise ValueError("丸のCIDまたは小さい背景を許してしまう")
    out={"scope":"development-only","page":item["page"],"line_index":item["line_index"],"checks":checks,
         "background":shades,"command":{"operator":op.decode(),"index":n,"array_index":i,"byte_offset":k,
         "font":font,"ros":"Adobe-Japan1","cid":evidence["cid"],"codepoint":evidence["codepoint"]},
         "inputs":{str(p):core.sha(p) for p in (Path(__file__),HERE/"protocol.md",prior.diag,BASE.parent/"result.json",
                   BASE,manifest,coarse,original)}}
    core.save_once(HERE/"result.json",core.encoded(out))
    print(out["command"],checks,shades,flush=True)


if __name__=="__main__":
    main()
