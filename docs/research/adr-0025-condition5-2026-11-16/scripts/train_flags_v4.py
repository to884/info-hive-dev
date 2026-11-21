"""出版物を一つずつ外し、事前に指定した印の判定候補を開発用の資料で比べる。"""

from __future__ import annotations

import argparse
import hashlib
import importlib.metadata
import math
import os
import time
import warnings
from collections import Counter, defaultdict
from pathlib import Path

os.environ.setdefault("OMP_NUM_THREADS", "2")
os.environ.setdefault("OPENBLAS_NUM_THREADS", "2")

import numpy as np
from sklearn.ensemble import HistGradientBoostingClassifier
from sklearn.linear_model import LogisticRegression
from sklearn.pipeline import make_pipeline
from sklearn.preprocessing import StandardScaler
from sklearn.tree import DecisionTreeClassifier

import flag_development as development
import score_v2
import score_v4
from flag_development import CORPUS, RESULTS, dataset, feature_vector, load, save
from rag_ocr_flags import AMBIGUOUS, normalize, skeleton


SEED = 20261117
THRESHOLDS = [round(i / 20, 2) for i in range(1, 20)]
PRIVATE = CORPUS / "flag-development-v4"


def configurations(family):
    if family == "lr":
        return [(f"lr-c{c}-w{weight}", {"C": c, "class_weight": weight})
                for c in (0.1, 1.0, 10.0) for weight in (None, "balanced")]
    if family == "tree":
        return [(f"tree-d{depth}-n{leaf}", {"max_depth": depth, "min_samples_leaf": leaf})
                for depth in (2, 3, 4) for leaf in (20, 50)]
    if family == "hgb":
        return [(f"hgb-n{leaves}-l{l2}", {"max_leaf_nodes": leaves, "l2_regularization": l2})
                for leaves in (7, 15) for l2 in (1.0, 10.0)]
    raise ValueError(family)


def classifier(family, parameters):
    if family == "lr":
        return make_pipeline(StandardScaler(), LogisticRegression(**parameters, max_iter=2000, random_state=SEED))
    if family == "tree":
        return DecisionTreeClassifier(**parameters, class_weight="balanced", random_state=SEED)
    return HistGradientBoostingClassifier(**parameters, learning_rate=0.1, max_iter=100,
                                         min_samples_leaf=20, early_stopping=False, random_state=SEED)


def prepare():
    data = dataset()
    records = [r for sample in data.values() for r in sample["lines"]]
    features = [feature_vector(r["line"]) for r in records]
    names = list(features[0])
    assert all(list(row) == names for row in features)
    X = np.asarray([[row[name] for name in names] for row in features], dtype=np.float64)
    assert np.isfinite(X).all()
    y = np.asarray([int(r["error"]) if r["rule"] == "exact" else np.nan for r in records])
    publications = np.asarray([r["publication"] for r in records])
    ident = "\n".join(f"{r['group']}:{r['key']}:{r['line_index']}:{r['rule']}:{r.get('error')}" for r in records)
    return data, records, names, X, y, publications, hashlib.sha256(ident.encode("utf-8") + X.tobytes()).hexdigest()


def sample_weights(publications):
    counts = Counter(publications)
    return np.asarray([len(publications) / (len(counts) * counts[p]) for p in publications])


def oof_predictions(family, parameters, X, y, publications, progress=None):
    output = np.full(len(y), np.nan)
    known = np.isfinite(y)
    fold_records = []
    warnings_count = Counter()
    for number, held_out in enumerate(sorted(set(publications)), 1):
        training = known & (publications != held_out)
        testing = publications == held_out
        assert not set(publications[training]) & set(publications[testing])
        assert set(y[training]) == {0.0, 1.0}
        model = classifier(family, parameters)
        with warnings.catch_warnings(record=True) as notices:
            weights = sample_weights(publications[training])
            if family == "lr":
                model.fit(X[training], y[training].astype(int), logisticregression__sample_weight=weights)
            else:
                model.fit(X[training], y[training].astype(int), sample_weight=weights)
        warnings_count.update(type(notice.message).__name__ for notice in notices)
        output[testing] = model.predict_proba(X[testing])[:, list(model.classes_).index(1)]
        fold_records.append({"held_out": held_out, "training_known": int(training.sum()),
                             "predicted": int(testing.sum()), "training_publications": len(set(publications[training]))})
        if progress:
            progress(number, len(fold_records), held_out)
    assert np.isfinite(output).all()
    return output, fold_records, dict(warnings_count)


def predicted_samples(data, flags):
    position = 0
    samples = {}
    for group, sample in data.items():
        rows = []
        for record in sample["lines"]:
            row = {k: record[k] for k in ("unit", "key", "line_index", "rule", "error", "eye") if k in record}
            row["reasons"] = ["candidate"] if flags[position] else []
            rows.append(row)
            position += 1
        samples[group] = {**{k: v for k, v in sample.items() if k != "lines"}, "lines": rows}
    assert position == len(flags)
    return samples


def raw_b_mean(sample):
    counts = defaultdict(lambda: [0, 0])
    for r in sample["lines"]:
        flagged = bool(r["reasons"])
        error = r["error"] if r["rule"] == "exact" else not flagged
        counts[r["unit"]][0] += flagged and error
        counts[r["unit"]][1] += error
    values = [caught / errors for caught, errors in counts.values() if errors]
    return math.fsum(values) / len(values) if values else None


def evaluate(data, flags, ident):
    groups = {}
    for group, sample in predicted_samples(data, flags).items():
        row = score_v2.measure(sample)
        row["b_mean_raw"] = raw_b_mean(sample)
        groups[group] = {"row": row, "reference_verdict": score_v2.verdict(row)}
    public = [d["row"] for name, d in groups.items() if name.endswith("-public")]
    return {"candidate": ident, "pass_count_at_reference": sum(d["reference_verdict"]["pass"] for d in groups.values()),
            "public_bmean_min": min(r["b_mean_raw"] or 0 for r in public),
            "public_margin_min": min(min(r["b"] or 0, r["b_mean_raw"] or 0) for r in public),
            "false_total_at_reference": sum(d["row"]["false"] for d in groups.values()), "groups": groups}


def inputs():
    result = score_v4.input_hashes()
    root = score_v4.HERE.parents[3]
    for path in (Path(__file__).resolve(), Path(development.__file__).resolve()):
        result[path.relative_to(root).as_posix()] = hashlib.sha256(path.read_bytes()).hexdigest()
    return result


def train(family):
    before = inputs()
    data, records, names, X, y, publications, fingerprint = prepare()
    PRIVATE.mkdir(parents=True, exist_ok=True)
    predictions, configs, scores = {}, {}, []
    for ident, parameters in configurations(family):
        started = time.monotonic()
        def progress(number, _, held_out):
            save(PRIVATE / f"status-{family}.json", {"configuration": ident, "fold": number,
                 "folds": len(set(publications)), "held_out": held_out})
        probabilities, folds, notices = oof_predictions(family, parameters, X, y, publications, progress)
        predictions[ident] = probabilities
        configs[ident] = {"parameters": parameters, "folds": folds, "warnings": notices,
                          "seconds": round(time.monotonic() - started, 3)}
        for threshold in THRESHOLDS:
            scores.append(evaluate(data, probabilities >= threshold, f"{ident}@{threshold:.2f}"))
        print(ident, "完了", flush=True)
    if inputs() != before:
        raise SystemExit("比較中に固定した入力かコードが変わったので保存しない")
    np.savez_compressed(PRIVATE / f"predictions-{family}.npz", **predictions)
    result = {"family": family, "features": names, "fingerprint": fingerprint, "seed": SEED,
              "rows": len(records), "known": int(np.isfinite(y).sum()), "publications": len(set(publications)),
              "versions": {p: importlib.metadata.version(p) for p in ("numpy", "scipy", "scikit-learn")},
              "inputs": before, "configurations": configs, "candidates": scores}
    save(RESULTS / f"flag-development-v4-{family}.json", result)
    print(family, "候補", len(scores), flush=True)


def rules(data, records):
    baseline, unrestricted, symmetric = [], [], []
    for r in records:
        line = r["line"]
        base = bool(r["reasons"])
        baseline.append(base)
        unrestricted.append(base or (line.get("alt_text") is not None and normalize(line["alt_text"]) != normalize(line["text"])))
        counted = lambda text: Counter(AMBIGUOUS.get(c, c) for c in skeleton(text))
        symmetric.append(base or (line.get("rapid_text") is not None and counted(line["rapid_text"]) != counted(line["text"])))
    return [("baseline", np.asarray(baseline)), ("rule-alt-all", np.asarray(unrestricted)), ("rule-rapid-symmetric", np.asarray(symmetric))]


def combine():
    data, records, names, X, y, publications, fingerprint = prepare()
    candidates = []
    probabilities = {}
    for family in ("lr", "tree", "hgb"):
        result = load(RESULTS / f"flag-development-v4-{family}.json")
        if result["fingerprint"] != fingerprint or result["inputs"] != inputs():
            raise SystemExit("学習した入力かコードが今のものと違う")
        candidates.extend(result["candidates"])
        probabilities.update(dict(np.load(PRIVATE / f"predictions-{family}.npz")))
    rule_predictions = dict(rules(data, records))
    candidates.extend(evaluate(data, flags, name) for name, flags in rule_predictions.items())
    # 不利な正誤の割り当てが一つでも不合格なら全称の合格にはならない。
    ranked = sorted(candidates, key=lambda r: (-r["pass_count_at_reference"], -r["public_bmean_min"], r["false_total_at_reference"], r["candidate"]))
    qualify = [r for r in candidates if r["pass_count_at_reference"] == 6 and r["public_margin_min"] >= 0.87]
    selected = {r["candidate"]: r for r in [*ranked[:10], *qualify, next(r for r in candidates if r["candidate"] == "baseline")]}
    verified = []
    for ident, result in selected.items():
        if ident in rule_predictions:
            flags = rule_predictions[ident]
        else:
            name, threshold = ident.split("@")
            flags = probabilities[name] >= float(threshold)
        groups = {}
        for group, sample in predicted_samples(data, flags).items():
            groups[group] = score_v4.robust_verdict(sample, public_margin=group.endswith("-public"))
        verified.append({"candidate": ident, "groups": groups,
                         "all_pass": all(r["pass"] for r in groups.values()),
                         "all_gates": all(r["gate"] for r in groups.values())})
        print(ident, "正式な基準", sum(r["pass"] for r in groups.values()), "関門", all(r["gate"] for r in groups.values()), flush=True)
    save(RESULTS / "flag-development-v4-comparison.json", {"inputs": inputs(), "fingerprint": fingerprint,
         "new_candidates": len(candidates) - 1, "baseline": next(r for r in candidates if r["candidate"] == "baseline"),
         "ranking": ranked, "verified": verified})
    save(PRIVATE / "ranking-summary.json", [{k: v for k, v in r.items() if k != "groups"} for r in ranked])


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("family", choices=("lr", "tree", "hgb", "combine"))
    args = parser.parse_args()
    combine() if args.family == "combine" else train(args.family)
