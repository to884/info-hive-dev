"""元PDFのパスをZ014・Z015の保存票と照合する。"""

from importlib.util import module_from_spec, spec_from_file_location
from pathlib import Path
import re

from pypdf import PdfReader


HERE = Path(__file__).resolve().parent
V97 = HERE.parent / "v97-black-punctuation-lookalikes"
V102 = HERE.parent / "v102-shape-position-separator-recheck"
V104 = HERE.parent / "v104-check-only-final-shapes"
spec = spec_from_file_location("saved_transcription_paths", V102 / "run.py")
previous = module_from_spec(spec)
spec.loader.exec_module(previous)
core = previous.core
TARGETS = ("Z014", "Z015")
PATTERNS = {
    ("m","c","c","c","c","f*"): "black-dot",
    ("m","l","c","c","l","l","c","l","l","h","f*"): "comma",
}
ALLOWED_PAGE = set("cm BT ET l Tm Tj T* c Tf TL rg n f* m h re".split())


def row_stream(document, row):
    possible = []
    for number, page in enumerate(document.pages,1):
        operations = [(op.decode("ascii"), values) for values,op in page.get_contents().operations]
        labels = [(i,str(values[0])) for i,(op,values) in enumerate(operations)
                  if op=="Tj" and re.fullmatch(r"Z[0-9]{3}",str(values[0]))]
        for j,(begin,tag) in enumerate(labels):
            if tag==row:
                end = labels[j+1][0] if j+1<len(labels) else len(operations)
                possible.append((number,page,operations,begin+1,end))
    (number,page,operations,begin,end), = possible
    if (page.rotation or list(page.mediabox) != list(page.cropbox)
            or tuple(page.mediabox[:2]) != (0,0) or page.get("/UserUnit",1) != 1
            or {op for op,_ in operations} - ALLOWED_PAGE
            or any(tuple(vals)!=(1,0,0,1,0,0) for op,vals in operations if op=="cm")):
        raise ValueError("固定開発PDFの座標変換または描画命令を確認できない")
    digits = [str(values[0]) for op,values in operations[begin:end]
              if op=="Tj" and re.fullmatch(r"[0-9]+",str(values[0]))]
    if len(digits)!=2:
        raise ValueError(f"保存行の数字列を元PDFと照合できない: {row}")
    paths, active = [], []
    for index in range(begin,end):
        op,values = operations[index]
        if op=="m" or active:
            active.append((index,op,[float(v) for v in values]))
        if active and op=="f*":
            paths.append(active)
            active = []
    if active or len(paths)!=2:
        raise ValueError(f"保存行の二つのパスを特定できない: {row}")
    return number, float(page.mediabox.top), digits, paths


def source_paths(document, row, geometry, source_meta):
    page, height, chunks, paths = row_stream(document,row)
    if page != source_meta["page"]:
        raise ValueError(f"保存画像とPDFのページが異なる: {row}")
    output = {}
    for path in paths:
        ops = tuple(command for _,command,_ in path)
        kind = PATTERNS.get(ops)
        if kind is None:
            raise ValueError(f"円またはコンマとして事前に確認した命令列と異なる: {row}")
        coords = [coords[i:i+2] for _,_,coords in path for i in range(0,len(coords),2)]
        pdf = [min(v[0] for v in coords),min(v[1] for v in coords),
               max(v[0] for v in coords),max(v[1] for v in coords)]
        # 曲線の制御点を含む外接範囲。端から1画素の差を許し、2解像度で照合する。
        raster_meta = "comma" if kind=="comma" else "noise"
        bounds_by_dpi = {}
        for dpi in (150,450):
            k = dpi/72
            positions = [pdf[0]*k,(height-pdf[3])*k,pdf[2]*k,(height-pdf[1])*k]
            raster = source_meta[f"{raster_meta}_{dpi}"]
            if any(abs(a-b)>1 for a,b in zip(positions,raster,strict=True)):
                raise ValueError(f"固定座標に対応するパスを確定できない: {row}/{dpi}")
            bounds_by_dpi[dpi] = raster
        component, = [item for item in geometry["ink"] if item["bounds"]==bounds_by_dpi[150]]
        ident = component["id"]
        if ident in output:
            raise ValueError(f"パスと保存成分が一対一でない: {row}")
        output[ident] = {
            "kind":kind, "page":page, "content_stream_index_range":[path[0][0],path[-1][0]],
            "commands":path, "control_bounds_pdf_pt":pdf, "saved_raster_bounds":bounds_by_dpi,
        }
    if {item["kind"] for item in output.values()} != {"black-dot","comma"}:
        raise ValueError(f"黒い点とコンマを分けられない: {row}")
    return chunks, output


def membership(part, box):
    left,top,width,height = box
    right,bottom = left+width,top+height
    result = {}
    for dpi,bounds in part["saved_raster_bounds"].items():
        scale = dpi/150
        l,t,r,b = bounds
        overlap = min(r,right*scale)-max(l,left*scale)
        result[dpi] = top*scale <= (t+b)/2 <= bottom*scale and 2*overlap >= r-l
    if result[150] != result[450]:
        raise ValueError("両解像度で元の所属判定がそろわない")
    return result


def main():
    role, baseline, replay, original, old_lock, formal_images = previous.prior_data()
    pdf_file = V97/"development-fixed-frames.pdf"
    metadata = V97/"physical-truth.json"
    physical = core.load(metadata)
    pdf_hash = core.sha(pdf_file)
    if pdf_hash != physical["pdf_sha256"] or old_lock["files"][str(pdf_file)] != pdf_hash:
        raise ValueError("元PDFが事前固定した版と異なる")
    document = PdfReader(pdf_file)
    selected = core.load(previous.previous.archive/"display/selection.json")["selected"]
    last = core.load(V104/"comparison.json")
    cases = {}
    for row in TARGETS:
        source_meta, = [item for item in physical["rows"] if item["id"]==row]
        name = row+"/new"
        geometry = old_lock["mapping"][row]
        box = selected[geometry["entry"]]["box"]
        chunks, paths = source_paths(document,row,geometry,source_meta)
        inside = {ident:membership(part,box) for ident,part in paths.items()}
        candidate_roles = {ident:("S" if part["kind"]=="comma" else "X") for ident,part in paths.items()}
        kept = {}
        for model in previous.MODELS:
            saved = replay["cases"][name]["votes"][model]
            kept[model] = saved["kept"]
            digits, parsed = previous.previous.saved.candidates(
                original["cases"][name]["votes"][model],geometry["ink"],box[0],box[2])
            if digits!="".join(chunks) or [len(chunks[0]),len(chunks[1])]!=[2,3]:
                raise ValueError(f"元PDFと保存票の数字列が異なる: {row}/{model}")
            if {ident for _,_,ident,_ in parsed} != paths.keys():
                raise ValueError(f"両パスを保存票で照合できない: {row}/{model}")
            for source, expected in (("kept",True),("outside",False)):
                candidates = [list(item[:3]) for item in parsed if item[3]==expected]
                if candidates != saved[source] or any(
                    ident not in paths or inside[ident][150]!=expected or gap!=len(chunks[0])
                    or glyph!=("," if paths[ident]["kind"]=="comma" else ".")
                    for gap,glyph,ident in candidates):
                    raise ValueError(f"元PDFと保存成分に不一致: {row}/{model}/{source}")
        old_roles = {int(ident):value for ident,value in role["cases"][row]["agreed_roles"].items()}
        before = previous.evaluate(row,old_roles,kept,original["cases"][name],geometry,box)
        for rule in previous.RULES:
            prior = last["rows"].get(row)
            if prior:
                expected_before = prior["after"][rule]
            else:
                inherited = baseline["rows"][row]
                if inherited[rule] != ["unresolved"]:
                    raise ValueError(f"引き継いだv101の分類が変化した: {row}/{rule}")
                expected_before = {"classification": inherited[rule], "answer": core.ref.UNKNOWN,
                                   "trace": None, "held_commas": inherited["blocked"][rule]}
            if core.encoded(expected_before)!=core.encoded(before[rule]):
                raise ValueError(f"v104の結果を再現できない: {row}/{rule}")
        after = previous.evaluate(row,candidate_roles,kept,original["cases"][name],geometry,box)
        cases[row] = {
            "source_text_chunks":chunks, "saved_box":box, "pdf_paths_by_component":paths,
            "inside_by_dpi":inside, "before":before, "after":after, "saved_in_frame":kept,
        }
        print(row,{rule:(before[rule]["answer"],after[rule]["answer"]) for rule in previous.RULES})
    data = core.encoded({"cases":cases,"pdf_sha256":pdf_hash,"new_image_reads":0,
                         "formal_attachments_verified":formal_images})
    out = HERE/"comparison.json"
    if out.exists():
        if out.read_bytes()!=data:
            raise ValueError("保存した結果と再集計が一致しない")
    else:
        core.save_once(out,data)


if __name__=="__main__":
    main()

