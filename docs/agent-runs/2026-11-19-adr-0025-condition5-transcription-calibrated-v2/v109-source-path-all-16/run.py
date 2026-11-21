"""元PDFのパスと保存票の一対一の成分対応を開発16枠で照合する。"""

from collections import Counter, defaultdict
from importlib.util import module_from_spec, spec_from_file_location
from pathlib import Path
import re

from pypdf import PdfReader


HERE = Path(__file__).resolve().parent
V108 = HERE.parent / "v108-source-path-z014-z015"
spec = spec_from_file_location("two_frozen_source_paths", V108 / "run.py")
source = module_from_spec(spec)
spec.loader.exec_module(source)
core, previous = source.core, source.previous
PATTERNS = {**source.PATTERNS, ("m","l","l","l","h","f*"): "black-slash"}
TARGETS = tuple(f"Z{i:03d}" for i in range(1,17))
MATCH_TOLERANCE_PX = 1


class Unresolved(ValueError):
    """描画と保存票の対応を確定できない枠。"""


def page_rows(document):
    rows = {}
    for number, page in enumerate(document.pages,1):
        operations = [(op.decode("ascii"), values) for values,op in page.get_contents().operations]
        if (page.rotation or list(page.mediabox) != list(page.cropbox)
                or tuple(page.mediabox[:2]) != (0,0) or page.get("/UserUnit",1) != 1
                or {op for op,_ in operations} - source.ALLOWED_PAGE
                or any(tuple(vals)!=(1,0,0,1,0,0) for op,vals in operations if op=="cm")):
            raise ValueError("固定PDFの座標系または描画命令が異なる")
        labels = [(i,str(val[0])) for i,(op,val) in enumerate(operations)
                  if op=="Tj" and re.fullmatch(r"Z[0-9]{3}",str(val[0]))]
        if not labels:
            raise ValueError("開発PDFの行識別子を特定できない")
        boundaries = [i for i,_ in labels[1:]] + [len(operations)]
        for (index,row), end in zip(labels,boundaries,strict=True):
            if row in rows:
                raise ValueError("PDFの行識別子が重複した")
            rows[row] = number, float(page.mediabox.top), list(enumerate(operations[index+1:end],index+1))
    if set(rows) != set(TARGETS):
        raise ValueError("同じ開発16枠が揃わない")
    return rows


def path_segments(stream):
    digits = [str(vals[0]) for _,(op,vals) in stream
              if op=="Tj" and re.fullmatch(r"[0-9]+",str(vals[0]))]
    if list(map(len,digits)) != [2,3]:
        raise Unresolved("数字を描いた二つの命令を特定できない")
    paths, active = [], []
    for index,(op,args) in stream:
        if op=="m" or active:
            if op not in {"m","l","c","h","f*"} or active and op=="m":
                raise Unresolved("独立したパス命令を切り出せない")
            active.append((index,op,[float(v) for v in args]))
        if active and op=="f*":
            paths.append(active)
            active = []
    if active or len(paths) not in {1,2}:
        raise Unresolved("円・短い斜線・コンマのパス本数を確定できない")
    return digits,paths


def coordinates(path, height):
    points = [args[i:i+2] for _,_,args in path for i in range(0,len(args),2)]
    l,t,r,b = (min(x for x,_ in points), height-max(y for _,y in points),
               max(x for x,_ in points), height-min(y for _,y in points))
    return {dpi:[value*dpi/72 for value in (l,t,r,b)] for dpi in (150,450)}


def match_paths(paths, height, geometry, physical):
    references = {
        tuple(physical[f"{label}_150"]): physical[f"{label}_450"]
        for label in ("comma","noise") if physical[f"{label}_150"] is not None}
    candidates = {part["id"]:{150:part["bounds"],450:references.get(tuple(part["bounds"]))}
                  for part in geometry["ink"]}
    if len(candidates)!=len(references) or any(not box[450] for box in candidates.values()):
        raise Unresolved("保存座標を両解像度で対応付けられない")
    matched = {}
    for path in paths:
        shape = PATTERNS.get(tuple(op for _,op,_ in path))
        if shape is None:
            raise Unresolved("既知の描画命令列に一致しない")
        predicted = coordinates(path,height)
        fit = [ident for ident,boxes in candidates.items() if all(
            abs(a-b)<=MATCH_TOLERANCE_PX for dpi in (150,450)
            for a,b in zip(predicted[dpi],boxes[dpi],strict=True))]
        if len(fit)!=1 or fit[0] in matched:
            raise Unresolved("描画命令と保存成分が一対一に対応しない")
        ident, = fit
        matched[ident] = {"kind":shape, "saved_raster_bounds":candidates[ident],
                          "commands":path, "vector_bounds_px":predicted}
    if matched.keys()!=candidates.keys():
        raise Unresolved("対応する描画命令がない保存成分がある")
    kinds = Counter(part["kind"] for part in matched.values())
    if kinds["black-dot"]+kinds["black-slash"]!=1 or kinds["comma"]>1:
        raise Unresolved("この開発PDFの黒い筆画とコンマを区別できない")
    return matched


def verify_votes(row, context, paths, box, chunks, kept):
    name = row+"/new"
    geometry = context["lock"]["mapping"][row]
    try:
        frame_membership = {ident:source.membership(path,box) for ident,path in paths.items()}
    except ValueError as error:
        raise Unresolved(str(error)) from error
    votes, digit_votes = {}, {}
    for model in previous.MODELS:
        raw = context["original"]["cases"][name]["votes"][model]
        parsed = previous.previous.saved.candidates(raw,geometry["ink"],box[0],box[2])
        if parsed is None or parsed[0] != "".join(chunks):
            raise Unresolved("保存票とPDFの数字列が一致しない")
        digits, marks = parsed
        if len({ident for _,_,ident,_ in marks})!=len(marks) or any(
                ident not in paths or frame_membership[ident][150]!=inside or gap!=len(chunks[0])
                for gap,_,ident,inside in marks):
            raise Unresolved("保存票の成分番号・座標・挿入位置を一対一に照合できない")
        saved = context["replay"]["cases"][name]["votes"][model]
        if ([list(item[:3]) for item in marks if item[3]]!=kept[model]
                or [list(item[:3]) for item in marks if not item[3]]!=saved["outside"]):
            raise ValueError("保存票と前の所属判定を再現できない")
        votes[model] = marks
        digit_votes[model] = digits
    for ident, part in paths.items():
        seen = {model:{mark[1] for mark in marks if mark[2]==ident} for model,marks in votes.items()}
        if part["kind"]=="comma" and frame_membership[ident][150] and any(
                reported != {","} for reported in seen.values()):
            raise Unresolved("枠内の実コンマに合う字形が保存二票で一致しない")
    return frame_membership,digit_votes


def unchanged_baseline(row, context, box, kept, geometry, raw):
    old_roles = {int(i):value for i,value in context["role"]["cases"][row]["agreed_roles"].items()}
    rebuilt = previous.evaluate(row,old_roles,kept,raw,geometry,box)
    saved = context["v104"]["rows"].get(row)
    if saved is not None:
        if core.encoded(rebuilt)!=core.encoded(saved["before"]):
            raise ValueError("v104に記録した保留の適用前を再現できない")
        return saved["after"]
    baseline = context["base"]["rows"][row]
    if any(rebuilt[rule]["classification"]!=baseline[rule] or
           rebuilt[rule]["held_commas"]!=baseline["blocked"][rule] for rule in previous.RULES):
        raise ValueError("v104が引き継いだv101の結果を再現できない")
    return rebuilt


def source_transcription(paths, kept, digits, geometry, target):
    roles = {i:("S" if part["kind"]=="comma" else "X") for i,part in paths.items()}
    first, second = (previous.previous.apply_roles(digits[model],kept[model],roles,geometry["ink"])
                     for model in previous.MODELS)
    if first[2] != second[2]:
        raise Unresolved("出典照合後の数字・字形・成分番号が二票で一致しない")
    answer, trace, structure = first
    if structure is None:
        raise Unresolved("出典照合後も転記を確定できない")
    classification = previous.previous.trial.base.changes(core.ref,answer,target)
    return {"classification":classification, "answer":answer, "trace":trace, "held_commas":[]}


def score_row(row, pdf_row, physical, selected, context):
    name = row+"/new"
    geometry = context["lock"]["mapping"][row]
    box = selected[geometry["entry"]]["box"]
    raw = context["original"]["cases"][name]
    kept = {m:context["replay"]["cases"][name]["votes"][m]["kept"] for m in previous.MODELS}
    before = unchanged_baseline(row,context,box,kept,geometry,raw)
    page, height, stream = pdf_row
    matched, inside, issue = {}, {}, None
    try:
        if page!=physical["page"] or box!=physical["box"]:
            raise Unresolved("固定画像とPDFのページ・枠が異なる")
        chunks, paths = path_segments(stream)
        matched = match_paths(paths,height,geometry,physical)
        inside, digits = verify_votes(row,context,matched,box,chunks,kept)
        resolved = source_transcription(matched,kept,digits,geometry,raw["target"])
        after = dict.fromkeys(previous.RULES,resolved)
    except Unresolved as error:
        issue = str(error)
        after = {rule: {"classification":["unresolved"], "answer":core.ref.UNKNOWN,
                        "trace":None, "held_commas":[]} for rule in previous.RULES}
    return {"group":geometry["category"], "page":page, "before":before, "after":after, "issue":issue,
            "box":box, "paths_by_component":matched,"inside_by_dpi":inside}


def main():
    role, base, replay, original, lock, formal_images = previous.prior_data()
    pdf = source.V97/"development-fixed-frames.pdf"
    physical = core.load(source.V97/"physical-truth.json")
    pdf_hash = core.sha(pdf)
    if pdf_hash!=physical["pdf_sha256"] or lock["files"][str(pdf)]!=pdf_hash:
        raise ValueError("事前固定の元PDFと異なる")
    meta = {item["id"]:item for item in physical["rows"]}
    context = {"role":role, "base":base, "replay":replay, "original":original, "lock":lock,
               "v104":core.load(source.V104/"comparison.json")}
    selected = core.load(previous.previous.archive/"display/selection.json")["selected"]
    streams = page_rows(PdfReader(pdf))
    rows = {row:score_row(row,streams[row],meta[row],selected,context) for row in TARGETS}
    counts = defaultdict(lambda:defaultdict(lambda:defaultdict(Counter)))
    regressions, preserved = defaultdict(list), defaultdict(list)
    for row, result in rows.items():
        for rule in previous.RULES:
            before,after = (result[stage][rule] for stage in ("before","after"))
            for group in ("all",result["group"]):
                counts[group][rule]["before"].update(before["classification"])
                counts[group][rule]["after"].update(after["classification"])
            if before["classification"]==["same"]:
                if after["classification"]==["same"] and before["answer"]==after["answer"]:
                    preserved[rule].append(row)
                else:
                    regressions[rule].append(row)
    v108 = core.load(V108/"comparison.json")
    for row in source.TARGETS:
        for mode in ("before","after"):
            if core.encoded(rows[row][mode])!=core.encoded(v108["cases"][row][mode]):
                raise ValueError("Z014・Z015の出典照合を再現できない")
    result = {"rows":rows, "counts":counts, "pdf_sha256":pdf_hash, "new_image_reads":0,
              "formal_attachments_verified":formal_images,
              "preserved":{r:preserved[r] for r in previous.RULES},
              "regressions":{r:regressions[r] for r in previous.RULES}}
    data = core.encoded(result)
    out = HERE/"comparison.json"
    if out.exists():
        if out.read_bytes()!=data:
            raise ValueError("前回の集計と再実行が一致しない")
    else:
        core.save_once(out,data)
    for group, rules in counts.items():
        print(group,{rule:{stage:dict(v) for stage,v in compare.items()} for rule,compare in rules.items()})
    print(result["preserved"],result["regressions"])


if __name__=="__main__":
    main()

