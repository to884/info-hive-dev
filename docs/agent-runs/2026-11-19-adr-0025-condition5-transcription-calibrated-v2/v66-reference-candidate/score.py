"""新しい二票と固定画素で確認した一字を別版に記録し、既定の採点を再実行する。"""

from hashlib import sha256
import importlib.util
from pathlib import Path
import sys

import numpy as np

from physical import agreement, glyphs

HERE = Path(__file__).resolve().parent
PRIOR = HERE.parent / "v38-reference-candidate"
TRIAL = HERE.parent / "v65-character-separation-pilot"
spec = importlib.util.spec_from_file_location("earlier_image_reference_scoring", PRIOR / "score.py")
prior = importlib.util.module_from_spec(spec)
spec.loader.exec_module(prior)
audit, evaluate = prior.audit, prior.evaluate
OUT = prior.OUT.with_name(HERE.name)
PAGE = "kanpo1828-p3-p0001"


def validated_score():
    old = audit.load(PRIOR / "result.json")
    if (not old["evaluation"]["all_pass"] or not old["evaluation"]["all_gates"]
            or any(audit.sha(prior.OUT / n) != h for n, h in old["artifacts"].items())
            or any(audit.sha(Path(f)) != h for f, h in old["inputs"].items())
            or old["same_predictions_sha256"] != audit.sha(audit.v14.old.PREDICTIONS)):
        raise ValueError("既存の固定正解または採点が異なる")
    return old


def examine():
    locked = TRIAL / "lock.json"
    votes_file = TRIAL / "result.json"
    result = audit.load(votes_file)
    plan = audit.load(locked)
    if (result["lock_sha256"] != audit.sha(locked) or result["scope"] != "development-only"
            or any(audit.sha(Path(p)) != digest for p, digest in plan["files"].items())):
        raise ValueError("同じ固定画像と転記指示の二票の来歴が異なる")
    review = {}
    for case, record in result["cases"].items():
        if record["page"] == PAGE and record["line_index"] in (164, 201):
            name = case.split("/")[0]
            votes = record["readings"]
            text = votes["pair"]["text"]
            if votes["coordinates"] or any(votes[role] != votes["pair"] for role in ("gpt", "claude")):
                raise ValueError("両画像票で本文全体が一致していない")
            review[record["line_index"]] = name, text, record["expected"]
    if set(review) != {164, 201}:
        raise ValueError("一字を照らす元の同じページの二行が不足")
    root = Path(plan["jobs"][review[164][0] + "/new"]["cards"]).parent.parent
    manifest = root / "packages.json"
    doc = audit.load(manifest)
    [depth, control] = [glyphs(root, doc["packs"], doc["source_assets"], review[i][0], audit.sha) for i in (164, 201)]
    shapes = {k: agreement(depth[0][k], control[0][k]) for k in depth[0]}
    observed = {"points_164": depth[1], "points_201": control[1], "overlaps": shapes}
    return review, observed, (locked, votes_file, manifest, depth[2], control[2])


def main():
    if OUT.exists() or (HERE / "result.json").exists():
        raise FileExistsError("この版の正解は採点済み")
    old = validated_score()
    review, observation, evidence = examine()
    before_rows = audit.load(prior.OUT / "public.json")
    row, = [r for r in before_rows if (r["key"], r["line_index"]) == (PAGE, 164)]
    check, = [r for r in before_rows if (r["key"], r["line_index"]) == (PAGE, 201)]
    _, now, before = review[164]
    if (before != row["effective"] or review[201][1] != check["effective"] or now != "野﨑" + before[2:]
            or not row["image_population"] or row["raw_region"] is not None):
        raise ValueError("画素で確認した二字目の一字以外に正解の違いがある")
    was = row["ocr_error"]
    error = sha256(now.encode("utf-8")).hexdigest() != row["ocr_normalized_sha256"]
    scoring = audit.v14.old.score.unpack_scoring(audit.load(prior.OUT / "scoring.json"))
    entry, = [r for r in scoring[row["group"]]["lines"] if (r["key"], r["line_index"]) == (PAGE, 164)]
    if entry["rule"] != "exact" or entry["error"] != was:
        raise ValueError("既定の評価と元の画像正解を照合できない")
    label = "image-only-kanpo-glyph-v66"
    entry.update(error=error, label_source=label)
    row.update(effective=now, source=label, ocr_error=error, development_proof={
        "stage": TRIAL.name, "lock_sha256": audit.sha(evidence[0]), "readings_sha256": audit.sha(evidence[1])
    })
    with np.load(audit.v14.old.PREDICTIONS, allow_pickle=False) as fixed:
        figures = evaluate(scoring, fixed["probabilities"])
    OUT.mkdir()
    audit.save_once(OUT / "public.json", audit.encoded(before_rows))
    audit.save_once(OUT / "scoring.json", audit.encoded(audit.v14.old.score.pack_scoring(scoring)))
    files = (*evidence, Path(__file__), HERE / "physical.py", HERE / "physical-review.md", PRIOR / "result.json",
             prior.OUT / "public.json", prior.OUT / "scoring.json", audit.v14.old.PREDICTIONS)
    audit.save_once(HERE / "result.json", audit.encoded({
        "scope": "development-only", "changed": old["changed"] + [
            {"page": PAGE, "line_index": 164, "before": before, "after": now, "before_error": was, "after_error": error}
        ], "evaluation": figures, "same_predictions_sha256": audit.sha(audit.v14.old.PREDICTIONS),
        "development_control_issues": old["development_control_issues"], "physical_confirmation": observation,
        "inputs": {str(p): audit.sha(p) for p in files},
        "artifacts": {f.name: audit.sha(f) for f in OUT.iterdir()},
    }))
    print("追加の一字", before, now, was, error, "開発6組", figures["all_pass"], "公開3組", figures["all_gates"], flush=True)


if __name__ == "__main__":
    main()
