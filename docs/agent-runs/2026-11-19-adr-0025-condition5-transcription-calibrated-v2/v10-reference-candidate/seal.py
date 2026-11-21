"""監査の抽出より先に候補、予測、採点と個別の読取の来歴を封印する。"""

import hashlib
import inspect
import json
from pathlib import Path

from assemble import CANONICAL, CORPUS, HERE, OUT, PARENT, SHORT_PRIVATE, STUDY, load, score, sha
from verify_candidate_prediction import COMPARISON, CONTEXT, COUNTED, LOCK

RESULT = HERE / "candidate-score.json"
SEAL = HERE / "pre-audit-seal.json"
PREDICTION = CORPUS / "neighbor-orientation-flag/predictions.npz"
BASELINE_PLAN = score.audit.RESULTS / "v9-revalidation-plan.json"


def validated_inputs():
    fixed, reported = load(LOCK), load(RESULT)
    metadata, local_lock = CONTEXT / "result.json", CONTEXT / "lock.json"
    saved, chosen = load(metadata), load(local_lock)
    original = load(BASELINE_PLAN)
    candidate_code = HERE / "assemble.py"
    runtime = PARENT / "pixel-input-check/result.json"
    if (reported["label_lock_sha256"] != sha(LOCK) or reported["prediction_sha256"] != sha(PREDICTION)
            or saved["predictions_sha256"] != sha(PREDICTION) or saved["lock_sha256"] != sha(local_lock)
            or reported["candidate"] != saved["candidate"] or chosen["candidate"] != saved["candidate"]
            or chosen["threshold"] != reported["threshold"] or score.THRESHOLD != reported["threshold"]
            or not reported["evaluation"]["all_pass"] or not reported["evaluation"]["all_gates"]
            or not load(runtime)["all_equal"]):
        raise ValueError("固定した候補、採点、設定、OCR入力の照合がそろわない")
    artifacts = fixed["artifacts"]
    for name, digest in artifacts.items():
        if sha(OUT / name) != digest:
            raise ValueError("固定した正解の成果物が変わった")
    for key, digest in chosen["inputs"].items():
        if sha(Path(key)) != digest:
            raise ValueError("旧版の教師で学習した予測の入力が変わった")
    base_cache = CORPUS / "flag-revalidation-v9/cache.npz"
    if chosen["inputs"].get(str(base_cache)) != original["cache_sha256"] or sha(base_cache) != original["cache_sha256"]:
        raise ValueError("周辺枠の予測と旧版の特徴・教師の対応がない")
    provenance_summary = load(OUT / "candidate-proof.json")
    raw_scope = []
    for name in ("source-anchored-position-pilot", "source-position-batches", "source-position-expansion",
                 "raster-figure-pilot", "raster-figure-expansion", "short-mixed-axis-pilot",
                 "short-horizontal-followup", STUDY.name):
        path = PARENT / name / "lock.json"
        bind = load(path)
        for key in ("inputs", "dependencies", "sources"):
            if any("predictions" in member or "neighbor-orientation-flag" in member for member in bind.get(key, ())):
                raise ValueError("画像の読者側の固定に予測が入った")
        raw_scope.append(path)
    rows = {(r["key"], r["line_index"]): r for r in load(OUT / "public.json")}
    corrected = provenance_summary["corrections"]
    m = corrected["M01"]
    changed = (m["key"], m["line_index"])
    old_known_update = {a for a, v in rows.items() if v["development_proof"]
                        and v["development_proof"]["result"] == "verified-original-repeat"}
    if old_known_update != {changed} or sum(v["changed-body"] for v in fixed["transitions"].values()) != 1:
        raise ValueError("確認済みの括弧以外の既知本文が変わった")
    for code in ("M02", "U12"):
        a = corrected[code]
        r = rows[a["key"], a["line_index"]]
        if r["raw_region"] is None or CANONICAL(r["raw_region"]) != a["normalized"]:
            raise ValueError("出典を合わせた行の既存領域と本文が違う")
    exact_score = score.frozen.score_v4
    used_code = (Path(score.__file__), Path(score.training.__file__), Path(exact_score.__file__),
                 Path(exact_score.score_v2.__file__), Path(exact_score.score_v2.score.__file__),
                 Path(inspect.getfile(score.audit.normalize)), Path(inspect.getfile(CANONICAL)),
                 Path(inspect.getfile(load)))
    for path in (candidate_code, Path(score.__file__), Path(exact_score.__file__)):
        if provenance_summary["inputs"][str(path)] != sha(path):
            raise ValueError("候補を作ったプログラムが変わった")
    report_paths = tuple(Path(k) for k in reported["inputs"])
    if any(sha(path) != reported["inputs"][str(path)] for path in report_paths):
        raise ValueError("採点で確認した版が変わった")
    return (Path(__file__), LOCK, RESULT, metadata, local_lock, PREDICTION, BASELINE_PLAN, base_cache, runtime,
            candidate_code, COUNTED, COMPARISON, *report_paths, *used_code, *raw_scope, OUT / "public.json",
            OUT / "candidate-proof.json", SHORT_PRIVATE / "provenance.json")


def main():
    inputs = {str(p): sha(p) for p in validated_inputs()}
    archive = {"scope": "pre-audit-candidate-and-prediction-freeze", "label_sha256": sha(LOCK),
               "evaluation_sha256": sha(RESULT), "prediction_sha256": sha(PREDICTION),
               "threshold": score.THRESHOLD, "files": inputs,
               "data_dependency": {"prediction_training_labels": "frozen-v9",
                                   "reference_labels": "v9-with-separately-recorded-development-ballots",
                                   "construction_adapted_on_development_data": True}}
    with SEAL.open("x", encoding="utf-8") as stream:
        json.dump(archive, stream, ensure_ascii=False, indent=2)
    print(sha(SEAL), "候補、予測、採点器を固定", flush=True)


if __name__ == "__main__":
    main()
