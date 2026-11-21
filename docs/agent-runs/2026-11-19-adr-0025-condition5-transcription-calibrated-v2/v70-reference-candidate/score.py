"""四つの独立画像票と固定画素から、枠外の一字を除いた正解候補を再採点する。"""

from hashlib import sha256
import importlib.util
from pathlib import Path

import numpy as np
from PIL import Image
from scipy.ndimage import find_objects, label

HERE = Path(__file__).resolve().parent
TRIAL = HERE.parent / "v67-neutral-transcription-pilot"
PRIOR = HERE.parent / "v38-reference-candidate"
spec = importlib.util.spec_from_file_location("existing_candidate_scoring", PRIOR / "score.py")
prior = importlib.util.module_from_spec(spec)
spec.loader.exec_module(prior)
audit, evaluate = prior.audit, prior.evaluate
OUT = prior.OUT.with_name(HERE.name)
PRIVATE = audit.OUT.with_name("reference-v67-neutral-transcription-pilot")
TARGET = "kanpo1826-p3-p0001", 8


def row_proof(job, record):
    for role, proof in record["provenance"].items():
        if proof["availability"] != "received" or not proof["session"]:
            raise ValueError("該当する二系統の新規画像票が揃わない")
        directory = PRIVATE / "reads" / job / role
        if any(audit.sha(directory / f) != h for f, h in proof["attempt_sha256"].items()):
            raise ValueError("転記の元の原票が変わった")
        yield proof["session"]


def image_geometry(root, doc, binding):
    checks, files = {}, []
    for dpi, view in zip((150, 450), binding["image_reference"]["source_view"]["views"], strict=True):
        name = next(p["image"] for p in view["images"] if p["kind"] == "plain")
        path = root / "source-assets" / name
        if audit.sha(path) != doc["source_assets"][name]:
            raise ValueError("枠端の固定画素と来歴が異なる")
        files.append(path)
        left, top, right, bottom = view["target_rectangle"]
        x, y = int(left), int(top) - 19
        with Image.open(path) as image:
            gray = np.array(image.crop((x, y, int(right) + 1, int(top) + 13)).convert("L"))
        details = []
        for threshold in (105, 140, 158, 170, 186, 205, 225):
            marks, _ = label(gray < threshold, np.ones((3, 3), dtype=bool))
            candidates = [(r, c) for r, c in find_objects(marks)
                          if c.stop - c.start >= 5 and top - 4 <= y + r.stop <= top + 4]
            if len(candidates) != 1:
                raise ValueError("枠上端の横画をほかと一意に区別できない")
            r, c = candidates[0]
            t, b = y + r.start, y + r.stop
            l, rt = x + c.start, x + c.stop
            if (r.start <= 0 or r.stop >= gray.shape[0]
                    or not left <= (l + rt) / 2 < right):
                raise ValueError("一字の端または直交中心を元の枠で確認できない")
            part = max(0.0, min(bottom, b) - max(top, t)) / (b - t)
            if part >= .5:
                raise ValueError("既定の所属を満たす画素条件がある")
            details.append({"threshold": threshold, "box": [l, t, rt, b], "overlap_ratio": round(part, 6)})
        checks[dpi] = {"rectangle": view["target_rectangle"], "results": details, "source_file": str(path)}
    return checks, files


def evidence():
    lock, compared = TRIAL / "lock.json", TRIAL / "comparison.json"
    plan, observations = audit.load(lock), audit.load(compared)
    if (observations["lock_sha256"] != audit.sha(lock)
            or any(audit.sha(Path(f)) != d for f, d in plan["files"].items())):
        raise ValueError("固定した画像、採点、出力の来歴が異なる")
    picks = {name: item for name, item in observations["cases"].items()
             if (item["page"], item["line_index"]) == TARGET}
    if len(picks) != 2 or {name.split("/")[1] for name in picks} != {"old", "new"}:
        raise ValueError("同じ行を両版で読んだ二組を確認できない")
    pairs = {item["answers"]["pair"]["text"] for item in picks.values()}
    refs = {item["expected"] for item in picks.values()}
    sessions = [sid for name, item in picks.items() for sid in row_proof(name, item)]
    if len(pairs) != 1 or len(refs) != 1 or len(sessions) != len(set(sessions)) or len(sessions) != 4:
        raise ValueError("新規の四票で同じ本文が揃わない")
    after, before = pairs.pop(), refs.pop()
    if not before.startswith("一") or after != before[1:]:
        raise ValueError("差が枠端の一字だけではない")
    new = next(n for n in picks if n.endswith("/new"))
    root = PRIVATE / "display/new/delivery"
    manifest = root / "packages.json"
    binding = plan["mapping"][new.split("/")[0]]["arms"]["new"]
    measured, proof_files = image_geometry(root, audit.load(manifest), binding)
    return before, after, measured, (lock, compared, manifest, *proof_files)


def main():
    if OUT.exists() or (HERE / "result.json").exists():
        raise FileExistsError("この候補の正解は採点済み")
    old = audit.load(PRIOR / "result.json")
    if (not old["evaluation"]["all_pass"] or not old["evaluation"]["all_gates"]
            or any(audit.sha(prior.OUT / n) != h for n, h in old["artifacts"].items())
            or any(audit.sha(Path(f)) != h for f, h in old["inputs"].items())
            or old["same_predictions_sha256"] != audit.sha(audit.v14.old.PREDICTIONS)):
        raise ValueError("既定の固定正解と採点を照合できない")
    before, after, geometry, inputs = evidence()
    rows = audit.load(prior.OUT / "public.json")
    row, = [r for r in rows if (r["key"], r["line_index"]) == TARGET]
    if row["raw_region"] is not None or not row["image_population"] or row["effective"] != before:
        raise ValueError("既定の画像補充正解を一行だけ照らせない")
    was = row["ocr_error"]
    new_error = sha256(after.encode("utf-8")).hexdigest() != row["ocr_normalized_sha256"]
    scoring = audit.v14.old.score.unpack_scoring(audit.load(prior.OUT / "scoring.json"))
    cell, = [r for r in scoring[row["group"]]["lines"] if (r["key"], r["line_index"]) == TARGET]
    if cell["rule"] != "exact" or cell["error"] != was:
        raise ValueError("既定の採点と保存済みの正誤が異なる")
    origin = "image-boundary-v70"
    cell.update(error=new_error, label_source=origin)
    row.update(effective=after, source=origin, ocr_error=new_error, development_proof={
        "stage": TRIAL.name, "lock_sha256": audit.sha(inputs[0]), "readings_sha256": audit.sha(inputs[1])
    })
    with np.load(audit.v14.old.PREDICTIONS, allow_pickle=False) as data:
        figures = evaluate(scoring, data["probabilities"])
    OUT.mkdir()
    audit.save_once(OUT / "public.json", audit.encoded(rows))
    audit.save_once(OUT / "scoring.json", audit.encoded(audit.v14.old.score.pack_scoring(scoring)))
    files = (*inputs, Path(__file__), HERE / "protocol.md", PRIOR / "result.json",
             prior.OUT / "public.json", prior.OUT / "scoring.json", audit.v14.old.PREDICTIONS)
    audit.save_once(HERE / "result.json", audit.encoded({
        "scope": "development-only", "changed": old["changed"] + [
            {"page": TARGET[0], "line_index": TARGET[1], "before": before, "after": after,
             "before_error": was, "after_error": new_error}
        ], "evaluation": figures, "same_predictions_sha256": audit.sha(audit.v14.old.PREDICTIONS),
        "development_control_issues": old["development_control_issues"], "physical_confirmation": geometry,
        "inputs": {str(f): audit.sha(f) for f in files},
        "artifacts": {f.name: audit.sha(f) for f in OUT.iterdir()},
    }))
    print(TARGET, "変更前と変更後の誤り", was, new_error, "開発6組", figures["all_pass"],
          "公開3組", figures["all_gates"], flush=True)


if __name__ == "__main__":
    main()
