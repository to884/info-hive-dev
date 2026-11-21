"""OCR枠の向きを加えた候補を、二読で確認できた開発ラベルで再学習する。"""

import argparse
import json
from pathlib import Path
import sys

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parent / "source-position-expansion"))
from refit_verified import CORPUS, BENCH, V9, load, np, score, sha

NAME = "ocr-neighbor-orientation-hgb-confirmed@0.15"
ARCHIVE = CORPUS / "neighbor-orientation-flag"
SOURCE = ARCHIVE / "verified-refit"
COMBINED = CORPUS / "transcription-calibrated-v2-2026-11-19/source-and-figure-development"
RESULT = HERE.parent / "raster-figure-expansion/combined-fixed-scores.json"
LOCK = HERE / "verified-refit-lock.json"


def files():
    return (Path(__file__), HERE / "run.py", HERE / "protocol.md", HERE / "lock.json", HERE / "result.json",
            BENCH / "results/v9-revalidation-plan.json", V9 / "cache.npz", ARCHIVE / "features.npy", RESULT,
            COMBINED / "scoring.json", COMBINED / "labels.npz", COMBINED / "candidate-labels.json",
            Path(score.__file__), Path(score.training.__file__), Path(score.frozen.score_v4.__file__))


def prepare():
    plan = load(BENCH / "results/v9-revalidation-plan.json")
    summary, base = load(RESULT), load(HERE / "lock.json")
    if (sha(V9 / "cache.npz") != plan["cache_sha256"] or base["features_sha256"] != sha(ARCHIVE / "features.npy")
            or sha(HERE / "lock.json") != load(HERE / "result.json")["lock_sha256"]
            or any(sha(COMBINED / k) != summary["artifacts"][k] for k in ("scoring.json", "labels.npz", "candidate-labels.json"))):
        raise ValueError("固定済みの特徴か画像二読の開発ラベルが違う")
    if LOCK.exists() or SOURCE.exists():
        raise FileExistsError("再学習の指定を上書きしない")
    manifest = {"scope": "development-only-fixed-feature-retraining", "candidate": NAME, "threshold": score.THRESHOLD,
                "parameters": score.PARAMETERS, "versions": score.versions(), "inputs": {str(p): sha(p) for p in files()}}
    with LOCK.open("x", encoding="utf-8") as f:
        json.dump(manifest, f, ensure_ascii=False, indent=2)
    print(sha(LOCK), flush=True)


def run(expected):
    manifest = load(LOCK)
    if expected != sha(LOCK) or manifest["inputs"] != {str(p): sha(p) for p in files()}:
        raise ValueError("再学習の事前固定が変化")
    with np.load(V9 / "cache.npz", allow_pickle=False) as f:
        X, previous, pubs = (f[k] for k in ("X", "y", "publications"))
    with np.load(COMBINED / "labels.npz", allow_pickle=False) as f:
        y = f["y"]
    new = np.load(ARCHIVE / "features.npy", allow_pickle=False)
    scoring = score.unpack_scoring(load(COMBINED / "scoring.json"))
    existing = np.isfinite(previous)
    derived = np.asarray([int(r["error"]) if r["rule"] == "exact" else np.nan
                          for sample in scoring.values() for r in sample["lines"]])
    found = sum(r["text"] is not None for r in load(COMBINED / "candidate-labels.json"))
    if (X.shape != (15658, 276) or new.shape != (15658, 12) or len(set(pubs)) != 42
            or not np.array_equal(y[existing], previous[existing]) or np.isfinite(y[~existing]).sum() != found
            or not np.array_equal(y, derived, equal_nan=True) or score.versions() != manifest["versions"]):
        raise ValueError("特徴か以前の既知の教師が変わった")
    family, parameters = score.selected_configuration()
    SOURCE.mkdir()

    def progress(number, label_count, publication):
        score.audit.save(SOURCE / f"fold-{number:02d}.json", {"fold": number, "publication": publication})
        if number % 7 == 0:
            print(NAME, number, "/42", flush=True)

    probabilities, folds, warnings = score.training.oof_predictions(family, parameters, np.column_stack((X, new)), y, pubs, progress)
    if (expected != sha(LOCK) or manifest["inputs"] != {str(p): sha(p) for p in files()}
            or probabilities.shape != y.shape or not np.isfinite(probabilities).all()):
        raise ValueError("学習後に固定した条件か全行予測が違う")
    ps = SOURCE / "predictions.npz"
    with ps.open("xb") as f:
        np.savez_compressed(f, probabilities=probabilities)
    value = score.evaluate(scoring, probabilities)
    value["points"]["candidate"] = NAME
    result = HERE / "verified-refit-result.json"
    with result.open("x", encoding="utf-8") as f:
        json.dump({"scope": manifest["scope"], "candidate": NAME, "lock_sha256": expected,
                   "probabilities_sha256": sha(ps), "folds": folds, "warnings": warnings, "evaluation": value},
                  f, ensure_ascii=False, indent=2)
    print({k: (v["assignments"], v["pass"], v["gate"]) for k, v in value["robust"].items()}, flush=True)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("action", choices=("prepare", "run"))
    parser.add_argument("--lock-sha256")
    args = parser.parse_args()
    if args.action == "prepare":
        prepare()
    else:
        run(args.lock_sha256)
