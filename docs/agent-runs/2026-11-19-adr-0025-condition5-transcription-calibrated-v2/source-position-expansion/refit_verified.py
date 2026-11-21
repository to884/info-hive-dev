"""独立二読から照合した開発ラベルだけで、同じ設定の印を再学習する。"""

import hashlib
import importlib.util
import json
from pathlib import Path

HERE = Path(__file__).resolve().parent
SENSITIVITY = HERE.parent / "provisional-dot-transcriptions/sensitivity.py"
spec = importlib.util.spec_from_file_location("fixed", SENSITIVITY)
fixed = importlib.util.module_from_spec(spec)
spec.loader.exec_module(fixed)
score, sha, load, np = fixed.score, fixed.sha, fixed.load, fixed.np
V9, CORPUS, BENCH = fixed.V9, fixed.CORPUS, fixed.BENCH
DEVELOPMENT = CORPUS / "transcription-calibrated-v2-2026-11-19/source-position-verified-development"
RESULT = HERE / "verified-fixed-score.json"
OUT = DEVELOPMENT / "refit"


def checked():
    reported = load(RESULT)
    for name, digest in reported["artifacts"].items():
        if sha(DEVELOPMENT / name) != digest:
            raise ValueError("検証済みの開発ラベルと違う")
    plan = load(BENCH / "results/v9-revalidation-plan.json")
    cache = V9 / "cache.npz"
    if sha(cache) != plan["cache_sha256"] or score.versions() != plan["versions"]:
        raise ValueError("固定した特徴か学習器が異なる")
    with np.load(cache, allow_pickle=False) as f:
        X, base, publications = (f[k] for k in ("X", "y", "publications"))
    with np.load(DEVELOPMENT / "labels.npz", allow_pickle=False) as f:
        y = f["y"]
    data = score.unpack_scoring(load(DEVELOPMENT / "scoring.json"))
    derived = np.asarray([int(r["error"]) if r["rule"] == "exact" else np.nan
                          for sample in data.values() for r in sample["lines"]])
    exact_new = sum(v["body-position-plus-image-count-and-source"] for v in reported["updates"].values())
    old = np.isfinite(base)
    if (X.shape != (15658, 276) or len(set(publications)) != 42 or not np.array_equal(derived, y, equal_nan=True)
            or not np.array_equal(y[old], base[old]) or np.isfinite(y[~old]).sum() != exact_new
            or hashlib.sha256(X.tobytes()).hexdigest() != plan["X_sha256"]):
        raise ValueError("確認済みの行以外の教師、特徴、採点の並びを変えた")
    return data, X, y, publications


def main():
    report = HERE / "verified-refit-score.json"
    if report.exists() or OUT.exists():
        raise FileExistsError("同じ試験の結果を上書きしない")
    observed = sha(RESULT)
    data, X, y, publications = checked()
    OUT.mkdir()
    family, params = score.selected_configuration()

    def progress(i, total, publication):
        score.audit.save(OUT / f"fold-{i:02d}.json", {"index": i, "publication": publication})
        if i % 7 == 0:
            print("固定設定の再学習", i, "/", total, flush=True)

    prob, folds, warnings = score.training.oof_predictions(family, params, X, y, publications, progress)
    if sha(RESULT) != observed or prob.shape != y.shape or not np.isfinite(prob).all():
        raise ValueError("固定済みの設定か予測が変わった")
    checked()
    p = OUT / "predictions.npz"
    with p.open("xb") as stream:
        np.savez_compressed(stream, probabilities=prob)
    value = score.evaluate(data, prob)
    score.audit.save(report, {"scope": "development-only-verified-reference-refit", "label_report_sha256": observed,
                              "script_sha256": sha(Path(__file__)), "prediction_sha256": sha(p), "folds": folds,
                              "parameters": params, "warnings": warnings, "evaluation": value})
    print(json.dumps({k: v["pass"] for k, v in value["robust"].items()}), flush=True)


if __name__ == "__main__":
    main()
