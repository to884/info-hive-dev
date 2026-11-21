"""実資料のコンマを保存票・固定画素・実際のPDF文字描画で照合する。"""

import argparse
from collections import Counter
from contextlib import ExitStack, closing
from ctypes import c_float, c_int, c_uint, c_void_p, cast
from importlib.util import module_from_spec, spec_from_file_location
from math import ceil, floor
from pathlib import Path
import re

import numpy as np
from PIL import Image
from pypdfium2 import PdfDocument
from pypdfium2 import raw
from scipy.ndimage import find_objects, label


HERE = Path(__file__).resolve().parent
STUDY = HERE.parent/"v92-numbered-ink-membership"
RETRY = HERE.parent/"v93-development-transport-retry"/"recover-v92.json"
spec = spec_from_file_location("numbered_real_development", STUDY/"run.py")
numbered = module_from_spec(spec)
spec.loader.exec_module(numbered)
core = numbered.core
MOVETO, LINETO = raw.FPDF_SEGMENT_MOVETO, raw.FPDF_SEGMENT_LINETO
TEXT, PATH = raw.FPDF_PAGEOBJ_TEXT, raw.FPDF_PAGEOBJ_PATH
MODES = ("v92_150","v109_both_dpi")


class Unresolved(ValueError):
    """一対一の対応や同じ所属を確定できない。"""


def pointer(obj):
    return cast(obj,c_void_p).value


def close_boxes(a,b):
    return all(abs(x-y)<=1 for x,y in zip(a,b,strict=True))


def overlap(a,b):
    return all(max(a[i],b[i])<min(a[i+2],b[i+2]) for i in range(2))


def center_in(box, frame):
    return all(frame[i]<=(box[i]+box[i+2])/2<=frame[i+2] for i in range(2))


def box_pixels(box, origin, scale):
    x,y = origin
    l,b,r,t = box
    return ((l-x)*scale[0],(y-t)*scale[1],(r-x)*scale[0],(y-b)*scale[1])


def provenance(row, reference, manifest, pdf_catalog):
    bound = reference["sha"]
    lo = core.CORPUS/"probe-v4/png"/f"{row['key']}.png"
    high = reference["source_view"]["views"][1]
    name, = (i["image"] for i in high["images"] if i["kind"]=="plain")
    hi = core.CORPUS/"reference-audit-v64/delivery/source-assets"/name
    low_path, expected_page = pdf_catalog[row["key"]]
    if (core.sha(lo)!=bound["150_dpi"] or core.sha(hi)!=manifest["source_assets"][name]
            or core.sha(low_path)!=bound["pdf_sha256"]):
        raise ValueError("保存した元PDFか固定画像のハッシュが一致しない")
    with Image.open(lo) as image:
        low_size = image.size
    with Image.open(hi) as image:
        high_pixels = np.array(image.convert("L"))
    l,t,r,b = high["crop_rectangle"]
    if high_pixels.shape!=(b-t,r-l) or high["display_scale"]!=1:
        raise ValueError("固定450 DPIの切り出し座標が異なる")
    matrix = bound["150_matrix"]
    origin = bound["150_origin"]
    if matrix[0][1]!=0 or matrix[1][0]!=0 or not matrix[0][0]>0>matrix[1][1]:
        raise ValueError("保存された座標系が横向きの非回転ではない")
    low_scale = (matrix[0][0],-matrix[1][1])
    ratios = tuple(x/y for x,y in zip(bound["450_dpi_shape"],low_size,strict=True))
    high_scale = tuple(a*b for a,b in zip(low_scale,ratios,strict=True))
    crop = (l,t,l,t)
    fixed150 = reference["source_view"]["views"][0]
    ca,cb,_,_ = fixed150["crop_rectangle"]
    s = fixed150["display_scale"]
    original = [v/s+offset for v,offset in zip(fixed150["target_rectangle"],(ca,cb,ca,cb),strict=True)]
    projected = [value*ratios[i%2]-crop[i] for i,value in enumerate(original)]
    if any(abs(a-b)>.002 for a,b in zip(projected,high["target_rectangle"],strict=True)):
        raise ValueError("保存された二解像度の座標変換を再現できない")
    return low_path,expected_page,origin,low_scale,high_scale,crop,ratios,high_pixels


def visible_text(obj):
    r,g,b,a = (c_uint() for _ in range(4))
    active = c_int()
    return (obj.type==TEXT and raw.FPDFPageObj_GetIsActive(obj,active) and active.value
            and raw.FPDFTextObj_GetTextRenderMode(obj)==0 and not raw.FPDFPageObj_HasTransparency(obj)
            and raw.FPDFClipPath_CountPaths(raw.FPDFPageObj_GetClipPath(obj))==-1
            and raw.FPDFPageObj_GetFillColor(obj,r,g,b,a) and a.value==255
            and max(r.value,g.value,b.value)<128)


def page_glyphs(page, text, origin, low_scale):
    objects = list(page.get_objects(max_depth=1))
    by_ref = {pointer(obj.raw):i for i,obj in enumerate(objects)}
    glyphs = []
    for index in range(text.count_chars()):
        code = raw.FPDFText_GetUnicode(text,index)
        if raw.FPDFText_IsGenerated(text,index) or code and chr(code).isspace():
            continue
        owner = raw.FPDFText_GetTextObject(text,index)
        if not owner:
            continue
        bounds = text.get_charbox(index)
        if not bounds[0]<bounds[2] or not bounds[1]<bounds[3]:
            continue
        glyphs.append({"index":index,"object":by_ref.get(pointer(owner)),
                       "symbol":chr(code) if code else "?", "pdf_box":bounds,
                       "low":box_pixels(bounds,origin,low_scale),
                       "encoding_proven":not raw.FPDFText_HasUnicodeMapError(text,index),
                       "horizontal":abs(raw.FPDFText_GetCharAngle(text,index))<.001})
    return objects,glyphs


def source_number(frame,objects,glyphs):
    in_frame = [g for g in glyphs if center_in(g["low"],frame)]
    owners = {g["object"] for g in in_frame if re.fullmatch(r"[0-9]",g["symbol"])}
    if len(owners)!=1 or None in owners:
        raise Unresolved("数字列の文字描画を一つに特定できない")
    owner, = owners
    if not visible_text(objects[owner]):
        raise Unresolved("数字列の不透明な文字塗りつぶしを確認できない")
    line = [g for g in glyphs if g["object"]==owner]
    if (any(not g["encoding_proven"] or not g["horizontal"] for g in line)
            or any(g["object"]!=owner for g in in_frame)
            or not re.fullmatch(r"[0-9]+(?:,[0-9]+)*","".join(g["symbol"] for g in line))
            or any(a["low"][0]>=b["low"][0] for a,b in zip(line,line[1:]))):
        raise Unresolved("PDFの並びと文字描画を一つに特定できない")
    if any(not center_in(g["low"],frame) for g in line if g["symbol"]!=","):
        raise Unresolved("PDFの数字が保存枠と対応しない")
    return owner,line


def path_clear(obj, candidate):
    fill, stroke, width = c_int(), c_int(), c_float()
    if (obj.type!=PATH or not raw.FPDFPath_GetDrawMode(obj,fill,stroke)
            or fill.value!=0 or not stroke.value or not raw.FPDFPageObj_GetStrokeWidth(obj,width)):
        return False
    a,b,c,d,e,f = obj.get_matrix().get()
    if (a,b,c,d)!=(1,0,0,1):
        return False
    points = []
    margin = abs(width.value)+1
    for pos in range(raw.FPDFPath_CountSegments(obj)):
        segment = raw.FPDFPath_GetPathSegment(obj,pos)
        x,y = c_float(),c_float()
        if not raw.FPDFPathSegment_GetPoint(segment,x,y) or raw.FPDFPathSegment_GetClose(segment):
            return False
        tag = raw.FPDFPathSegment_GetType(segment)
        points.append((tag,x.value+e,y.value+f))
    if len(points)%2:
        return False
    for first,second in zip(points[::2],points[1::2],strict=True):
        if (first[0],second[0])!=(MOVETO,LINETO):
            return False
        _,x,y = first
        _,u,v = second
        if overlap(candidate,(min(x,u)-margin,min(y,v)-margin,max(x,u)+margin,max(y,v)+margin)):
            return False
    return True


def unique_drawer(glyph,objects,glyphs):
    candidate = glyph["pdf_box"]
    if any(other["index"]!=glyph["index"] and overlap(other["pdf_box"],candidate) for other in glyphs):
        raise Unresolved("同じコンマ位置に別の文字描画が重なる")
    for obj in objects:
        if obj.type!=TEXT and overlap(obj.get_bounds(),candidate) and not path_clear(obj,candidate):
            raise Unresolved("コンマ位置への他の描画の重なりを排除できない")


def high_component(pixels, projected, threshold):
    l,t,r,b = projected
    x,y = floor(l)-5,floor(t)-5
    u,v = ceil(r)+5,ceil(b)+5
    if not (0<=x<u<=pixels.shape[1] and 0<=y<v<=pixels.shape[0]):
        raise Unresolved("固定450 DPIのコンマ周辺を測れない")
    groups,_ = label(pixels[y:v,x:u]<threshold,np.ones((3,3),dtype=bool))
    bounds = [(x+c.start,y+rows.start,x+c.stop,y+rows.stop) for rows,c in find_objects(groups)]
    hits = [box for box in bounds if overlap(box,projected)]
    if len(hits)!=1 or not close_boxes(hits[0],projected):
        raise Unresolved("固定450 DPIのコンマの成分を一対一に絞れない")
    return hits[0]


def belongs(box,frame):
    left,top,right,bottom = frame
    l,t,r,b = box
    horizontal = max(0,min(right,r)-max(left,l))
    return top<=(t+b)/2<=bottom and 2*horizontal>=r-l


def replay_receipts(plan, saved, digest, runtimes):
    pilot = numbered.pilot
    retry = core.load(RETRY)
    if retry["fixed_lock_sha256"]!=digest:
        raise ValueError("保存していた開発票の復旧記録が別の版を指す")
    archive = pilot.OUT
    sessions = set()
    for task,job in plan["jobs"].items():
        if not task.endswith("/new"):
            continue
        prior = saved["cases"][task]
        row_id, = job["request"]["ids"]
        for model in ("gpt","claude"):
            try:
                if model=="gpt" and task in retry["receipt"]:
                    official_attempt = archive/"reads"/task/model/"attempt-001/raw/response.jsonl"
                    pilot.OUT = archive/"recovery-https-fallback"
                    retry_attempt = pilot.OUT/"reads"/task/model/"attempt-001/raw/process.json"
                    if (core.sha(official_attempt)!=retry["invalid_response_sha256"][task]
                            or core.sha(retry_attempt)!=retry["receipt"][task]["retry_process_sha256"]):
                        raise ValueError("保存した復旧票の来歴が異なる")
                history = pilot.outcome(digest,task,model,job,runtimes[model],send=False)
            finally:
                pilot.OUT = archive
            if not history or history[-1]["availability"]!="received":
                raise ValueError("保存画像票を受領できない")
            record = history[-1]
            if (record["session"] in sessions or record["session"]!=prior["sessions"][model]
                    or record["answers"][row_id]!=prior["votes"][model]):
                raise ValueError("保存画像票が前回の採点と合わない")
            if model=="gpt" and task in retry["receipt"] and record["session"]!=retry["receipt"][task]["session"]:
                raise ValueError("保存した復旧セッションが異なる")
            sessions.add(record["session"])
    if len(sessions)!=24:
        raise ValueError("開発12枠の保存24票がそろわない")


def inspect_row(row, link, structured, data, cache):
    pdf,page_num,origin,lo,hi,crop,ratios,pixels = data
    page_key = (pdf,page_num,tuple(origin),lo)
    if page_key not in cache:
        doc = cache["stack"].enter_context(closing(PdfDocument(pdf)))
        page = cache["stack"].enter_context(closing(doc[page_num-1]))
        text = cache["stack"].enter_context(closing(page.get_textpage()))
        if page.get_rotation()!=0 or any(abs(a-b)>.002 for a,b in zip(
                (page.get_bbox()[0],page.get_bbox()[3]),origin,strict=True)):
            raise ValueError("PDFのページ座標が固定画像と異なる")
        cache[page_key] = page_glyphs(page,text,origin,lo)
    objects,glyphs = cache[page_key]
    x,y,w,h = row["box"]
    frame = (x,y,x+w,y+h)
    frame_high = [v*ratios[i%2]-crop[i] for i,v in enumerate(frame)]
    owner,line = source_number(frame,objects,glyphs)
    digits,marks = structured
    source_digits = "".join(g["symbol"] for g in line if g["symbol"]!=",")
    if source_digits!=digits:
        raise Unresolved("PDFで描かれた数字と保存二票が一致しない")
    commas = [g for g in line if g["symbol"]==","]
    if len(commas)!=len(marks):
        raise Unresolved("PDFのコンマすべてに対応する保存成分がそろわない")
    ink = {v["id"]:v for v in link["ink"]}
    if len(ink)!=len(link["ink"]):
        raise Unresolved("保存成分番号が重複している")
    evidence, used_chars, used_high = [],set(),set()
    for gap,(sign,ident) in marks.items():
        options = [g for g in commas if close_boxes(g["low"],ink[ident]["bounds"])]
        if sign!="," or len(options)!=1 or options[0]["index"] in used_chars:
            raise Unresolved("文字描画と保存票のコンマを一対一に絞れない")
        glyph, = options
        if sum(close_boxes(glyph["low"],piece["bounds"]) for piece in ink.values())!=1:
            raise Unresolved("PDFのコンマに対応する保存成分が複数ある")
        unique_drawer(glyph,objects,glyphs)
        source_gap = sum(g["symbol"]!="," for g in line if g["index"]<glyph["index"])
        if source_gap!=gap:
            raise Unresolved("保存票とPDFのコンマの挿入位置が異なる")
        projected = tuple(a-b for a,b in zip(box_pixels(glyph["pdf_box"],origin,hi),crop,strict=True))
        high = {str(t):high_component(pixels,projected,t) for t in (170,191)}
        if any(any(overlap(v,other) for other in used_high) for v in high.values()):
            raise Unresolved("複数のコンマが固定450 DPIの同じ成分に対応した")
        used_high.update(high.values())
        used_chars.add(glyph["index"])
        belongs150 = belongs(ink[ident]["bounds"],frame)
        if belongs150 != (ink[ident]["cross_axis_center_inside"] and
                          2*ink[ident]["axis_overlap"]>=ink[ident]["axis_length"]):
            raise ValueError("固定150 DPIの所属を再現できない")
        high_roles = {k:belongs(value,frame_high) for k,value in high.items()}
        evidence.append({"id":ident,"gap":gap,"glyph":glyph,"glyph_box_450":projected,
                         "fixed_150":ink[ident]["bounds"],"fixed_450":high,
                         "inside_150":belongs150,"inside_450":high_roles,
                         "high_center_to_frame_bottom":round((high["191"][1]+high["191"][3])/2-frame_high[3],6)})
    return {"text_object_index":owner,"source_digits":source_digits,"punctuation":evidence,
            "pdf_sha256":core.sha(pdf),"pdf_page":page_num}


def verify_formal():
    pins = core.load(HERE.parent/"v100-separator-role-second-look"/"integrity.json")
    root = HERE.parents[3]
    for path, expected in pins["formal_hashes"].items():
        if core.sha(root/path)!=expected:
            raise ValueError("正式監査の台帳が固定と異なる")
    file = next(root/path for path in pins["formal_hashes"] if path.endswith("packages.json"))
    verified = 0
    for pack, info in core.load(file)["packs"].items():
        request = info["request"]
        for name,digest in zip(request["images"],request["image_sha256"],strict=True):
            if core.sha(file.parent/"cards"/pack/name)!=digest:
                raise ValueError("正式監査の固定画像が異なる")
            verified += 1
    if verified!=pins["formal_audit_attachments_verified"]:
        raise ValueError("正式監査の添付数が異なる")
    return verified


def main():
    cli = argparse.ArgumentParser(description=__doc__)
    cli.add_argument("--codex",required=True,type=Path)
    cli.add_argument("--claude",required=True,type=Path)
    args = cli.parse_args()
    numbered.launch.configure()
    plan_path = STUDY/"lock.json"
    saved = core.load(STUDY/"comparison.json")
    digest = core.sha(plan_path)
    plan = core.load(plan_path)
    if (digest!=saved["lock_sha256"] or any(core.sha(Path(path))!=h for path,h in plan["files"].items())):
        raise ValueError("保存対象の固定が異なる")
    runtimes = numbered.pilot.audit.delivery.runtime({"gpt":args.codex,"claude":args.claude})
    replay_receipts(plan,saved,digest,runtimes)
    attachments = verify_formal()
    manifest = core.load(core.CORPUS/"reference-audit-v64/delivery/packages.json")
    selected = core.load(numbered.pilot.OUT/"display/selection.json")["selected"]
    catalog = {}
    for author in ("defense","disaster"):
        entry = core.load(core.CORPUS/"public"/f"{author}.truth.json")
        path = core.CORPUS/entry["file"]
        if core.sha(path)!=entry["pdf_sha256"]:
            raise ValueError("公開資料の固定SHAと異なる")
        catalog.update({f"{entry['name']}-p{item['page']:04d}":(path,item["page"]) for item in entry["pages"]})
    counts = {mode:Counter() for mode in ("before",*MODES)}
    regressions = {mode:[] for mode in MODES}
    cases = {}
    with ExitStack() as stack:
        cache = {"stack":stack}
        for key,link in plan["mapping"].items():
            row = selected[link["entry"]]
            result = saved["cases"][key+"/new"]
            old = {model:numbered.identify(ballot,link["ink"],row["box"][0],row["box"][2])
                   for model,ballot in result["votes"].items()}
            first,second = old.values()
            before = numbered.measure.transcribe(first,link["ink"]) if first==second else core.ref.UNKNOWN
            target = result["expected"]
            if before!=core.ref.UNKNOWN and [numbered.measure.grade.verdict(core.ref,before,target)]!=[result["result"]["pair"]]:
                raise ValueError("保存済みv92の採点を再現できない")
            pack = re.fullmatch(r"8[68]-(pack-[0-9]+)(?:-[a-z]+)?",key).group(1)
            ref, = manifest["packs"][pack]["mapping"].values()
            data = provenance(row,ref["image_reference"],manifest,catalog)
            proof, issue = None,None
            try:
                if first is None or first!=second:
                    raise Unresolved("保存二票が同じ数字・成分番号で一致しない")
                proof = inspect_row(row,link,first,data,cache)
            except Unresolved as error:
                issue = str(error)
            after150 = before if proof else core.ref.UNKNOWN
            conflicts = [part["id"] for part in proof["punctuation"]
                         if any(flag!=part["inside_150"] for flag in part["inside_450"].values())] if proof else []
            # 厳密な照合では、成分は一意でも枠所属の解像度差があれば未決定にする。
            strict = after150 if not conflicts else core.ref.UNKNOWN
            interim = {"before":before,"v92_150":after150,"v109_both_dpi":strict}
            cls = {stage:[numbered.measure.grade.verdict(core.ref,value,target)]
                   for stage,value in interim.items()}
            if cls["before"]!=[result["result"]["pair"]]:
                raise ValueError("v92の二票一致の採点が異なる")
            for mode,categories in cls.items():
                counts[mode].update(categories)
            for mode in MODES:
                if cls["before"]==["same"] and interim[mode]!=before:
                    regressions[mode].append(key)
            cases[key] = {"page":row["key"],"line":row["line_index"],"group":link["category"],
                          "transcriptions":interim,"classification":cls,"source":proof,
                          "source_issue":issue,"dpi_membership_conflicts":conflicts,"target":target}
    output = {"cases":cases,"counts":counts,"regressions":regressions,"v92_lock_sha256":digest,
              "new_image_reads":0,"formal_attachments_verified":attachments,
              "saved_image_sessions_verified":24}
    payload = core.encoded(output)
    out = HERE/"comparison.json"
    if out.exists():
        if out.read_bytes()!=payload:
            raise ValueError("保存した集計と再実行が一致しない")
    else:
        core.save_once(out,payload)
    print({k:dict(v) for k,v in counts.items()},regressions)
    for key,row in cases.items():
        if row["source_issue"] or row["dpi_membership_conflicts"]:
            print(key,row["source_issue"],row["dpi_membership_conflicts"])


if __name__=="__main__":
    main()

