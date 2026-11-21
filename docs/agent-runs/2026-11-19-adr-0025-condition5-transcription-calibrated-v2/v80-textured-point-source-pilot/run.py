"""一つの明るい点だけが背景を残して一つの埋め込み文字に結び付くかを確かめる。"""

from contextlib import closing
import ctypes
from importlib.util import module_from_spec, spec_from_file_location
from pathlib import Path

import numpy as np
from PIL import Image

HERE = Path(__file__).resolve().parent
STAGES = HERE.parent
effort = STAGES / "v71-audit-effort-pilot"
diag = STAGES / "v78-point-drawing-diagnosis/result.json"
spec = spec_from_file_location("effort_for_source_on_texture", effort / "run.py")
fixed = module_from_spec(spec)
spec.loader.exec_module(fixed)
core, launch, previous = fixed.core, fixed.launch, fixed.previous
trace = launch.source.verify_vertical.trace


def reproduce(page, fixed_region, area, objects):
    raw = trace.raw
    active = []
    for obj in objects:
        value = ctypes.c_long()
        if not raw.FPDFPageObj_GetIsActive(obj, ctypes.byref(value)):
            raise RuntimeError("文字描画の状態を確認できない")
        if value.value:
            active.append(obj)

    def set_active(group, yes):
        for obj in group:
            if not raw.FPDFPageObj_SetIsActive(obj, yes):
                raise RuntimeError("文字描画を切り分けられない")

    def show():
        with closing(page.render(scale=150/72)) as bitmap:
            return np.array(bitmap.to_pil().convert("RGB"))[area].copy()

    if not np.array_equal(show(), fixed_region):
        raise RuntimeError("通常の描画と固定150 DPIが異なる")
    try:
        set_active(active, False)
        background = show()
        change = np.any(fixed_region != background, axis=2)
        if not np.any(change):
            raise ValueError("文字描画を無効にしても点の画素がそのまま残る")
        if np.any(change[0]) or np.any(change[-1]) or np.any(change[:,0]) or np.any(change[:,-1]):
            raise ValueError("点の外側でも文字描画が変わる")
        delta = fixed_region.astype(np.int16) - background.astype(np.int16)
        if np.count_nonzero(np.mean(delta, axis=2) > 30) < .65*change.sum():
            raise ValueError("取り除いた画素が固定画像の明るい点と合わない")
        search, found = [active], []
        while search:
            group = search.pop()
            set_active(group, True)
            proof = show()
            set_active(group, False)
            if np.array_equal(proof, background):
                continue
            if len(group)==1:
                found.extend(group)
            else:
                mid=len(group)//2
                search.extend((group[:mid],group[mid:]))
        if len(found)!=1:
            raise ValueError("点を描いた文字オブジェクトが一つにならない")
        set_active(found,True)
        if not np.array_equal(show(), fixed_region):
            raise ValueError("一つの文字描画を戻しても固定した点の画素を再現できない")
        set_active(found,False)
        set_active([obj for obj in active if obj not in found],True)
        if not np.array_equal(show(),background):
            raise ValueError("別の文字描画が点の位置に寄与")
        return found
    finally:
        set_active(active,True)


def main():
    launch.configure()
    core.verify_methods()
    recorded=core.load(diag)
    if any(core.sha(Path(p))!=h for p,h in recorded["inputs"].items()):
        raise ValueError("点の描画の診断に使った証拠が異なる")
    lock=core.load(effort/"lock.json")
    selected=core.load(fixed.pilot.OUT/"display/selection.json")["selected"]
    comparison=core.load(effort/"comparison.json")
    catalog=previous.packets.old.lookup()[1]
    old=trace.reproduce
    outcomes={}
    for pack, case in recorded["cases"].items():
        if case["state"]!="recorded":
            continue
        item=lock["mapping"][pack]
        row=selected[item["entry"]]
        key=row["key"]
        image=item["image_reference"]
        flags=image["sha"]
        pdf_name, pdf_sha, num=catalog[key]
        pdf=(core.CORPUS/pdf_name).read_bytes()
        png=core.CORPUS/"probe-v4/png"/f"{key}.png"
        if trace.sha(pdf)!=pdf_sha or pdf_sha!=flags["pdf_sha256"] or core.sha(png)!=flags["150_dpi"]:
            raise RuntimeError("元PDFか固定画素の来歴が異なる")
        output={"page": key,"line_index": row["line_index"],"status":"insufficient"}
        with Image.open(png) as im:
            rgb=np.asarray(im.convert("RGB"))
        try:
            trace.reproduce=reproduce
            evidence=trace.trace(pdf,num,rgb,case["pixels_150"],flags)
        except ValueError as error:
            output["reason"]=str(error)
        finally:
            trace.reproduce=old
        if "reason" not in output:
            if case["polarity"]!="light" or not case["changed_without_text"]:
                raise ValueError("対象外の点を確定した")
            source=comparison["cases"][pack]["readings"]["high"]["pair"]["text"]
            mark=core.ref.MARK.findall(source)
            if len(mark)!=1 or mark[0][0]!="round":
                raise ValueError("曖昧な符号以外を置換しようとした")
            matched=core.ref.NORMALIZE(core.ref.MARK.sub(chr(int(evidence["codepoint"],16)),source))
            output.update(status="same" if matched==row["effective"] else "different",evidence=evidence)
        outcomes[pack]=output
    if len(outcomes)!=3:
        raise ValueError("診断した三行がそろわない")
    result={"scope":"development-only","outcomes":outcomes,"inputs":{str(p):core.sha(p) for p in
            (diag,Path(__file__),HERE/"protocol.md",effort/"lock.json",effort/"comparison.json",Path(trace.__file__))}}
    core.save_once(HERE/"result.json",core.encoded(result))
    print(outcomes,flush=True)


if __name__=="__main__":
    main()
