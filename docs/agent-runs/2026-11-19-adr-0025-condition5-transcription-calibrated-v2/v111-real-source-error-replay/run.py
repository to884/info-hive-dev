"""実資料の保存票の脱落・過剰転記・未決定を固定PDFで照合する。"""

from collections import Counter
from contextlib import ExitStack, closing
from ctypes import c_float, c_int, c_size_t, c_ubyte, c_uint
from hashlib import sha256
from importlib.util import module_from_spec, spec_from_file_location
from math import ceil, floor
from pathlib import Path
import json
import re

import numpy as np
from PIL import Image
from pypdfium2 import PdfDocument, raw
from scipy.ndimage import find_objects, label


HERE = Path(__file__).resolve().parent
V110 = HERE.parent/"v110-real-numeric-source-check"/"run.py"
spec = spec_from_file_location("real_image_source_check",V110)
source = module_from_spec(spec)
spec.loader.exec_module(source)
core = source.core
AUDIT = source.numbered.pilot.audit
MODELS = ("claude","gpt")
STUDIES = {
    "v22":("v22-list-mark-pilot","result.json"),
    "v88":("v88-numeric-outside-controls","comparison.json"),
    "v90":("v90-numeric-ink-membership","comparison.json"),
}
TARGETS = {
    "v22": ("case-01/old","case-03/old","case-04/old","case-05/old"),
    "v88": ("pack-214-outside/old","pack-373-outside/old"),
    "v90": ("88-pack-214-edge/new","88-pack-214-inside/new","88-pack-373-edge/new",
            "86-pack-073/new","86-pack-133/new","86-pack-211/new","86-pack-240/new",
            "86-pack-327/new","86-pack-365/new"),
}
ARROW, PRIVATE_ARROW = "➢", "\uf0d8"
ARROW_TOLERANCE = 2


def checked_study(trial):
    name, result = STUDIES[trial]
    folder = HERE.parent/name
    archive = core.CORPUS/f"reference-{name}"
    path = folder/"lock.json"
    plan, saved = core.load(path), core.load(folder/result)
    if (core.sha(path)!=saved["lock_sha256"] or
            any(core.sha(Path(p))!=digest for p,digest in plan["files"].items())):
        raise ValueError(f"固定の開発票が変化している: {trial}")
    rows = core.load(archive/"display/selection.json")["selected"]
    return archive,plan,saved,rows


def saved_votes(archive, plan, trial, task, digest, sessions):
    job = plan["tests" if trial=="v22" else "jobs"][task]
    ident, = job["request"]["ids"]
    if trial=="v22" and core.load(archive/"started.json")["lock_sha256"]!=digest:
        raise ValueError("v22の着手が別の固定を指す")
    recovery = core.load(HERE.parent/STUDIES["v22"][0]/"recovery-provenance.json") if trial=="v22" else None
    if recovery and recovery["lock_sha256"]!=digest:
        raise ValueError("v22の復旧記録が別の固定を指す")
    answers = {}
    for family in MODELS:
        folder = archive/"reads"/task/family
        selected = None
        if recovery:
            adopted = recovery["origins"][task][family]
            folder = Path(adopted["selected"])
            selected = adopted["attempts"][-1]
            if not folder.is_relative_to(archive) or selected["availability"]!="received":
                raise ValueError("v22の保存復旧票が見つからない")
        else:
            attempt, = folder.glob("attempt-*")
            claim = core.load(attempt/"claim.json")
            if claim["lock_sha256"]!=digest or claim["name"]!=task or claim["role"]!=family:
                raise ValueError("保存票の着手が別の固定を指す")
            folder = attempt/"raw"
        start, process = (core.load(folder/name) for name in ("start.json","process.json"))
        events = (folder/"response.jsonl").read_bytes()
        payload = AUDIT.readers.request_payload(job["request"],Path(job["cards"]),family)
        last = folder/"last-message.json"
        last_bytes = last.read_bytes() if last.exists() else None
        if (start["family"]!=family or start["image_sha256"]!=job["request"]["image_sha256"]
                or start["packet_sha256"]!=sha256(payload).hexdigest() or process["returncode"]
                or process["response_sha256"]!=sha256(events).hexdigest()
                or process["last_sha256"]!=(sha256(last_bytes).hexdigest() if last_bytes else None)):
            raise ValueError(f"保存原票と固定画像を照合できない: {trial} {task} {family}")
        logs = [json.loads(line,object_pairs_hook=AUDIT.readers.json_pairs)
                for line in events.splitlines() if line.strip()]
        session, response = AUDIT.frame.receipt.validated(
            logs,family,start["model"],last_bytes.decode("utf-8") if last_bytes else None)
        if selected and (session!=selected["session"]
                         or process["response_sha256"]!=selected["response_sha256"]):
            raise ValueError("v22の採用した復旧票と一致しない")
        if session in sessions:
            raise ValueError("保存セッションが重複した")
        sessions.add(session)
        answers[family] = AUDIT.frame.trial.entries(response,[ident])[ident],session
    return answers


def num_votes(votes, trial, row, link):
    if trial not in {"v88","v90"} or set(votes)!=set(MODELS):
        raise source.Unresolved("対象の試験と保存二票がそろわない")
    parsed, coordinates = [],[]
    left,_,width,_ = row["box"]
    ink = sorted(link["ink"],key=lambda piece:piece["bounds"][0])
    for vote in votes.values():
        if vote["status"]!="readable":
            raise source.Unresolved("保存票の数字列が判読不能")
        if trial=="v88":
            text = core.ref.NORMALIZE(vote["text"])
            if not re.fullmatch(r"[0-9]+(?:,[0-9]+)*",text):
                raise source.Unresolved("数値に混じる記号を一対一に特定できない")
            digits,marks = "",{}
            for char in text:
                if char==",":
                    marks[len(digits)] = char
                else:
                    digits += char
        else:
            digits,*terms = vote["text"].split("|")
            if not digits.isascii() or not digits.isdecimal():
                raise source.Unresolved("保存票が数字列でない")
            marks = {}
            previous_gap, previous_position = 0,0
            for raw_mark in terms:
                match = source.numbered.measure.TOKEN.fullmatch(raw_mark)
                if not match:
                    raise source.Unresolved("保存した記号の形式が異なる")
                gap,at,symbol = int(match[1]),int(match[2]),match[3]
                if not (previous_gap<gap<len(digits) and previous_position<at<width) or symbol!="C":
                    raise source.Unresolved("保存票のコンマ位置が一意でない")
                marks[gap] = ","
                coordinates.append((gap,at))
                previous_gap,previous_position = gap,at
        parsed.append((digits,marks))
    first,second = parsed
    if first!=second:
        raise source.Unresolved("数字列かコンマの挿入位置が保存二票で一致しない")
    digits,marks = first
    if not marks:
        return digits,{}
    if len(ink)!=len(marks) or len({c["id"] for c in ink})!=len(ink):
        raise source.Unresolved("保存画素のコンマ候補が挿入位置ごとに一意でない")
    attached = {gap:(glyph,part["id"]) for (gap,glyph),part in zip(marks.items(),ink,strict=True)}
    for gap,at in coordinates:
        distances = [(abs((part["bounds"][0]+part["bounds"][2])/2-left-at),part["id"])
                     for part in ink]
        nearest = min(distance for distance,_ in distances)
        plausible = {ident for distance,ident in distances if distance<=3 or distance==nearest}
        if plausible!={attached[gap][1]}:
            raise source.Unresolved("保存票の座標が別の成分を指すか特定できない")
    return digits,attached


def normal_vote(raw):
    return core.ref.decoded(raw,[])


def one_pair(votes):
    left,right = map(normal_vote,votes.values())
    return left if left==right else core.ref.UNKNOWN


def classify(answer,target):
    return source.numbered.measure.grade.verdict(core.ref,answer,target)


def numeric_case(trial,task,votes,row,link,manifest,catalog,cache):
    key = task.split("/")[0]
    pack = re.search(r"pack-[0-9]+",key).group()
    reff, = manifest["packs"][pack]["mapping"].values()
    structured = num_votes(votes,trial,row,link)
    data = source.provenance(row,reff["image_reference"],manifest,catalog)
    proof = source.inspect_row(row,link,structured,data,cache)
    answer = source.numbered.measure.transcribe(structured,link["ink"])
    return answer,proof


def arrow_images(row, reference, archive, manifest, pdf):
    shade = reference["sha"]
    low_path = core.CORPUS/"probe-v4/png"/f"{row['key']}.png"
    view = reference["source_view"]["views"][1]
    name, = (asset["image"] for asset in view["images"] if asset["kind"]=="plain")
    high_path = archive/"display/delivery/source-assets"/name
    if (core.sha(pdf)!=shade["pdf_sha256"] or core.sha(low_path)!=shade["150_dpi"]
            or core.sha(high_path)!=manifest["source_assets"][name]):
        raise ValueError("矢じりの固定画像または元PDFと一致しない")
    with Image.open(low_path) as im:
        low_size = im.size
        low = np.array(im.convert("L"))
    with Image.open(high_path) as im:
        high = np.array(im.convert("L"))
    a,b,c,d = view["crop_rectangle"]
    matrix = shade["150_matrix"]
    if matrix[0][1]!=0 or matrix[1][0]!=0 or high.shape!=(d-b,c-a) or view["display_scale"]!=1:
        raise ValueError("矢じりの固定画像の座標系が異なる")
    lo = matrix[0][0],-matrix[1][1]
    ratios = tuple(end/start for end,start in zip(shade["450_dpi_shape"],low_size,strict=True))
    hi = tuple(s*ratio for s,ratio in zip(lo,ratios,strict=True))
    x,y,w,h = row["box"]
    projection = [v*ratios[i%2]-offset for i,(v,offset) in enumerate(
        zip((x,y,x+w,y+h),(a,b,a,b),strict=True))]
    if any(abs(r-t)>.002 for r,t in zip(projection,view["target_rectangle"],strict=True)):
        raise ValueError("矢じりの両解像度の固定座標が一致しない")
    return shade["150_origin"],lo,hi,(a,b,a,b),low,high


def rectangle_segments(obj):
    if raw.FPDFPath_CountSegments(obj)!=5:
        return None
    matrix = obj.get_matrix()
    points = []
    for i in range(5):
        seg = raw.FPDFPath_GetPathSegment(obj,i)
        x,y = c_float(),c_float()
        if (raw.FPDFPathSegment_GetType(seg)!=(source.MOVETO if i==0 else source.LINETO)
                or bool(raw.FPDFPathSegment_GetClose(seg))!=(i==4)
                or not raw.FPDFPathSegment_GetPoint(seg,x,y)):
            return None
        points.append(matrix.on_point(x.value,y.value))
    if (points[0]!=points[-1] or len(set(points[:-1]))!=4 or
            any((a[0]==b[0])==(a[1]==b[1]) for a,b in zip(points,points[1:]))):
        return None
    return points


def separated_graphic(obj,index,owner,box):
    if source.path_clear(obj,box):
        return True
    mode,stroke = c_int(),c_int()
    if obj.type!=source.PATH or not raw.FPDFPath_GetDrawMode(obj,mode,stroke):
        return False
    corners = rectangle_segments(obj)
    if corners is None:
        return False
    if mode.value==0 and stroke.value:
        width = c_float()
        if not raw.FPDFPageObj_GetStrokeWidth(obj,width):
            return False
        a,b,c,d,_,_ = obj.get_matrix().get()
        margin = abs(width.value)*2*max(abs(a)+abs(c),abs(b)+abs(d))+1
        return not any(source.overlap(box,(min(x,a)-margin,min(y,b)-margin,max(x,a)+margin,max(y,b)+margin))
                       for (x,y),(a,b) in zip(corners,corners[1:]))
    rgba = [c_uint() for _ in range(4)]
    return (index<owner and not stroke.value and mode.value in (1,2)
            and not raw.FPDFPageObj_HasTransparency(obj)
            and raw.FPDFPageObj_GetFillColor(obj,*rgba) and all(v.value==255 for v in rgba))


def arrow_pixels(pixels, projected):
    l,t,r,b = projected
    x,y,u,v = floor(l)-5,floor(t)-5,ceil(r)+5,ceil(b)+5
    if not (0<=x<u<=pixels.shape[1] and 0<=y<v<=pixels.shape[0]):
        raise source.Unresolved("矢じりの周囲が保存画像から欠ける")
    result = {}
    for threshold in (170,191):
        groups,_ = label(pixels[y:v,x:u]<threshold,np.ones((3,3),dtype=bool))
        found = [(x+c.start,y+rr.start,x+c.stop,y+rr.stop) for rr,c in find_objects(groups)]
        hits = [box for box in found if source.overlap(box,projected)]
        if len(hits)!=1 or any(abs(a-b)>ARROW_TOLERANCE for a,b in zip(hits[0],projected,strict=True)):
            raise source.Unresolved("矢じりの描画と画素の成分が一対一に対応しない")
        result[str(threshold)] = hits[0]
    return result


def arrow_font(obj):
    font = raw.FPDFTextObj_GetFont(obj)
    if not font or raw.FPDFFont_GetIsEmbedded(font)!=1:
        raise source.Unresolved("矢じりの埋め込み書体を特定できない")
    length = c_size_t()
    if not raw.FPDFFont_GetFontData(font,None,0,length) or not length.value:
        raise source.Unresolved("矢じりの書体の指紋を確認できない")
    buf = (c_ubyte * length.value)()
    if not raw.FPDFFont_GetFontData(font,buf,length.value,length):
        raise source.Unresolved("矢じりの書体を保存PDFから取得できない")
    return sha256(bytes(buf)).hexdigest()


def arrow_case(row, before, ref, archive, manifest, proof_ballots, pdf):
    origin,lo,hi,crop,low,high = arrow_images(row,ref,archive,manifest,pdf)
    num = int(row["key"].rsplit("p",1)[1])
    with closing(PdfDocument(pdf)) as doc, closing(doc[num-1]) as page, closing(page.get_textpage()) as text:
        if page.get_rotation()!=0 or any(abs(a-b)>.002 for a,b in zip(
                (page.get_bbox()[0],page.get_bbox()[3]),origin,strict=True)):
            raise ValueError("矢じりのPDFページ座標が固定と異なる")
        objs,glyphs = source.page_glyphs(page,text,origin,lo)
        x,y,w,h = row["box"]
        frame = (x,y,x+w,y+h)
        line = sorted((g for g in glyphs if source.belongs(g["low"],frame)),key=lambda g:g["low"][0])
        if not line or any(not g["encoding_proven"] or not g["horizontal"] for g in line):
            raise source.Unresolved("PDFの横書き本文の描画を特定できない")
        head,*body = line
        if proof_ballots is None:
            drawing = core.ref.NORMALIZE("".join(g["symbol"] for g in line))
            if before["text"]!=drawing:
                raise source.Unresolved("対照の文字列とPDFの文字描画が一致しない")
            return before,{"pdf_page":num,"kind":"unchanged-text"}
        witness = one_pair(proof_ballots)
        if (witness["text"]!=ARROW+before["text"] or head["symbol"]!=PRIVATE_ARROW
                or any(g["symbol"]==PRIVATE_ARROW for g in body)
                or core.ref.NORMALIZE("".join(g["symbol"] for g in body))!=before["text"]
                or head["object"] is None or not source.visible_text(objs[head["object"]])):
            raise source.Unresolved("矢じりと本文を保存票・PDFの双方で分離できない")
        box = head["pdf_box"]
        if (any(g["index"]!=head["index"] and source.overlap(g["pdf_box"],box) for g in glyphs)
                or any(obj.type!=source.TEXT and source.overlap(obj.get_bounds(),box)
                       and not separated_graphic(obj,i,head["object"],box)
                       for i,obj in enumerate(objs))):
            raise source.Unresolved("矢じりに重なる別の描画を排除できない")
        low_parts = arrow_pixels(low,head["low"])
        projected = tuple(a-b for a,b in zip(source.box_pixels(box,origin,hi),crop,strict=True))
        high_parts = arrow_pixels(high,projected)
        if not all(source.belongs(bounds,frame) for bounds in low_parts.values()):
            raise source.Unresolved("矢じりの150 DPIの枠所属が定まらない")
        return witness,{"pdf_page":num,"kind":"leading-arrow","glyph":head,"fixed_150":low_parts,
                        "fixed_450":high_parts,"embedded_font_sha256":arrow_font(objs[head["object"]])}


def main():
    archives = {trial:checked_study(trial) for trial in TARGETS}
    formal = source.verify_formal()
    manifest = core.load(core.CORPUS/"reference-audit-v64/delivery/packages.json")
    arrow_manifest = core.load(archives["v22"][0]/"display/delivery/packages.json")
    numeric_links = archives["v90"][1]["mapping"]
    numeric_rows = archives["v90"][3]
    catalog = {}
    for author in ("defense","disaster"):
        entry = core.load(core.CORPUS/"public"/f"{author}.truth.json")
        file = core.CORPUS/entry["file"]
        if core.sha(file)!=entry["pdf_sha256"]:
            raise ValueError("公開資料の固定SHAと異なる")
        catalog.update({f"{entry['name']}-p{i['page']:04d}":(file,i["page"]) for i in entry["pages"]})
    arrow_pdf = core.CORPUS/"whitepaper-summary.pdf"
    sessions = set()
    counts = {"before":Counter(),"after":Counter()}
    cases, regressions = {},[]
    with ExitStack() as stack:
        cache = {"stack":stack}
        for trial, tasks in TARGETS.items():
            archive,plan,table,rows = archives[trial]
            for task in tasks:
                prior = table["cases"][task]
                original = saved_votes(archive,plan,trial,task,table["lock_sha256"],sessions)
                votes = {m:entry[0] for m,entry in original.items()}
                issue,proof = None,None
                if trial=="v22":
                    key = task.split("/")[0]
                    bind = plan["cases"][key]
                    row = rows[bind["entry"]]
                    target = core.ref.NORMALIZE(row["effective"])
                    before = one_pair(votes)
                    expected = {"agree":"same"}.get(prior["result"],prior["result"])
                    ref, = (link["image_reference"] for pack in arrow_manifest["packs"].values()
                            for link in pack["mapping"].values() if link["entry"]==bind["entry"])
                    witnesses = None
                    if bind["purpose"]=="arrow":
                        witness = saved_votes(archive,plan,trial,key+"/new",table["lock_sha256"],sessions)
                        witnesses = {m:entry[0] for m,entry in witness.items()}
                    try:
                        result,proof = arrow_case(row,before,ref,archive,arrow_manifest,witnesses,arrow_pdf)
                    except source.Unresolved as error:
                        result,issue = core.ref.UNKNOWN,str(error)
                else:
                    key = task.split("/")[0]
                    link = numeric_links[key if trial=="v90" else "88-"+key]
                    row = numeric_rows[link["entry"]]
                    target = prior["expected"]
                    if trial=="v88":
                        expected = prior["outcomes"]["pair"]
                        before = one_pair(votes)
                        if {m:normal_vote(v) for m,v in votes.items()}!={m:prior["answers"][m] for m in MODELS}:
                            raise ValueError("v88の保存票と前の集計が異なる")
                    else:
                        expected = prior["result"]["pair"]
                        if votes!=prior["votes"] or any(original[m][1]!=prior["sessions"][m] for m in MODELS):
                            raise ValueError("v90の保存票と前の集計が異なる")
                        forms = [source.numbered.measure.decompose(v,link["ink"],row["box"][0],row["box"][2])
                                 for v in votes.values()]
                        before = source.numbered.measure.transcribe(forms[0],link["ink"]) if forms[0]==forms[1] else core.ref.UNKNOWN
                    try:
                        result,proof = numeric_case(trial,task,votes,row,link,manifest,catalog,cache)
                    except source.Unresolved as error:
                        result,issue = core.ref.UNKNOWN,str(error)
                previous,after = classify(before,target),classify(result,target)
                if previous!=expected:
                    raise ValueError(f"保存結果を再現できない: {trial}/{task} {previous} {expected}")
                case_id = trial+"/"+task
                if previous=="same" and result!=before:
                    regressions.append(case_id)
                counts["before"][previous] += 1
                counts["after"][after] += 1
                cases[case_id] = {"page":row["key"],"line":row["line_index"],"frame_150":row["box"],
                                  "before":before,"after":result,"counts_as":[previous,after],
                                  "source":proof,"source_issue":issue}
                print(case_id,row["key"],row["line_index"],previous,"→",after,issue)
    if len(cases)!=15 or len(sessions)!=36:
        raise ValueError("予定した15枠・保存36票が揃わない")
    output = {"cases":cases,"counts":counts,"regressions":regressions,"saved_votes":len(sessions),
              "new_image_reads":0,"formal_attachments_verified":formal}
    raw_json = core.encoded(output)
    path = HERE/"comparison.json"
    if path.exists():
        if path.read_bytes()!=raw_json:
            raise ValueError("再実行の集計が異なる")
    else:
        core.save_once(path,raw_json)
    print({stage:dict(stats) for stage,stats in counts.items()},regressions)


if __name__=="__main__":
    main()

