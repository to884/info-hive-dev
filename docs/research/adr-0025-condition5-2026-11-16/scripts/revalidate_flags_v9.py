"""276特徴と選定済み設定を保ち、v9教師で一つの判定を再検証する。"""

import argparse
import hashlib
import importlib.metadata
import os
from pathlib import Path

os.environ["OMP_NUM_THREADS"] = "2"
os.environ["OPENBLAS_NUM_THREADS"] = "2"

import numpy as np

import labels_v9 as labels
import region_audit_v6 as audit
import region_visual_v9 as visual
import train_flags_v6 as frozen
import train_flags_v4 as training

OUT = audit.BENCH / "corpus/flag-revalidation-v9"
PLAN = audit.RESULTS / "v9-revalidation-plan.json"
METHOD = audit.BENCH.parent / "adr-0025-condition5-revalidation-v9-2026-11-18.md"
SELECTED = "v6-mineru-hgb@0.15"
PARAMETERS = {"max_leaf_nodes": 15, "l2_regularization": 1.0}
THRESHOLD = .15


def selected_configuration():
    selected = audit.load(audit.RESULTS / "v6-comparison.json")["selected_candidate"]
    if selected != SELECTED or training.SEED != 20261117:
        raise ValueError("選んだ候補か種が違う")
    values = [(family, parameters) for name, family, parameters in frozen.configurations() if name == SELECTED.split("@")[0]]
    if values != [("hgb", PARAMETERS)] or float(SELECTED.split("@")[1]) != THRESHOLD:
        raise ValueError("選んだ設定か閾値が違う")
    return values[0]


def versions():
    return {name: importlib.metadata.version(name) for name in ("numpy", "scipy", "scikit-learn")}


def inputs():
    selected_configuration()
    result = {**visual.check_start()["inputs"]}
    # collectの最終回答を、全担当の受領・現物・退避から再構成して照らす。
    labels.verify_visual()
    paths = [Path(__file__), Path(labels.__file__), audit.BENCH / "scripts/test_labels_v9.py",
             audit.BENCH / "scripts/test_revalidate_flags_v9.py", METHOD, visual.PLAN,
             visual.OUT / "start.json", visual.OUT / "final.json", visual.OUT / "reuse.json",
             audit.RESULTS / "region-visual-v9-result.json"]
    paths += list(visual.OUT.glob("receipt-*.json"))
    paths += list(audit.RESULTS.glob("region-visual-v9-receipt-*.json"))
    paths += list(visual.OUT.glob("round-*-batch-*.json"))
    paths += list(audit.RESULTS.glob("region-visual-v9-pack-*.json"))
    third = visual.OUT / "third-selection.json"
    if third.exists():
        paths.append(third)
    for path in paths:
        result[path.resolve().as_posix()] = audit.sha(path)
    for name in ("scipy", "scikit-learn"):
        distribution = importlib.metadata.distribution(name)
        for member in distribution.files or []:
            path = Path(distribution.locate_file(member)).resolve()
            if member.suffix != ".pyc" and path.is_file():
                result[path.as_posix()] = audit.sha(path)
    if versions() != audit.load(audit.RESULTS / "v6-candidates.json")["versions"]:
        raise ValueError("元v6の学習ライブラリの版と違う")
    return result


def row_identity(record):
    line = record["line"]
    return {k: record[k] for k in ("group", "stratum", "unit", "publication", "key", "line_index")} | {
        "box": line["box"], "ocr_text_sha256": hashlib.sha256(line["text"].encode("utf-8")).hexdigest()}


def scoring_data(data):
    """元の採点で読むフィールドと単位を保存し、OCR本文は渡さない。"""
    result = {}
    for name, sample in data.items():
        rows = [{k: row[k] for k in ("unit", "key", "line_index", "rule", "error", "eye", "group", "stratum", "publication", "label_source") if k in row}
                for row in sample["lines"]]
        result[name] = {"lines": rows, "missed": [{"unit": m["unit"]} for m in sample["missed"]]}
        if "truth_lines" in sample:
            result[name]["truth_lines"] = sample["truth_lines"]
    return result


def pack_scoring(data):
    # JSONをキーで整列しても、特徴・確率と照らす組の順序は配列で保持する。
    return {"group_order": list(data), "samples": scoring_data(data)}


def unpack_scoring(packed):
    order, samples = packed["group_order"], packed["samples"]
    if len(order) != len(set(order)) or set(order) != set(samples):
        raise ValueError("採点する組の順序の対応が違う")
    return {name: samples[name] for name in order}


def evaluate(data, probabilities):
    flags = probabilities >= THRESHOLD
    points = training.evaluate(data, flags, SELECTED)
    samples = training.predicted_samples(data, flags)
    robust = {name: frozen.score_v4.robust_verdict(sample, public_margin=name.endswith("-public")) for name, sample in samples.items()}
    return {"points": points, "robust": robust,
            "all_pass": all(row["pass"] for row in robust.values()),
            "all_gates": all(row["gate"] for row in robust.values())}


def prepare():
    if OUT.exists() or PLAN.exists():
        raise FileExistsError("v9の再検証の指定を上書きしない")
    before = inputs()
    old_data, old_records, names, X, old_y, publications, feature_fingerprint = frozen.prepare()
    original = audit.load(audit.RESULTS / "v6-candidates.json")
    if feature_fingerprint != original["fingerprint"] or names != original["features"] or X.shape != (15658, 276) or len(set(publications)) != 42:
        raise ValueError("元v6の全特徴・行・出版物の同一性が違う")
    data, records, changes = labels.load_labels(old_data)
    if [row_identity(r) for r in old_records] != [row_identity(r) for r in records] or not all(a["line"] is b["line"] for a, b in zip(old_records, records)):
        raise ValueError("新旧の教師以外の評価行が変わった")
    y = np.asarray([int(r["error"]) if r["rule"] == "exact" else np.nan for r in records], dtype=np.float64)
    old_probabilities = frozen.predictions()[SELECTED.split("@")[0]]
    if old_probabilities.shape != y.shape or not np.isfinite(X).all() or not np.isfinite(old_probabilities).all():
        raise ValueError("特徴か旧予測の全行が一致しない")
    OUT.mkdir(parents=True)
    (OUT / "method-before-training.md").write_bytes(METHOD.read_bytes())
    with (OUT / "cache.npz").open("xb") as stream:
        np.savez_compressed(stream, X=X, y=y, old_y=old_y, publications=publications, old_probabilities=old_probabilities)
    audit.save(OUT / "scoring-data.json", pack_scoring(data))
    audit.save(OUT / "row-identities.json", [row_identity(r) for r in records])
    if before != inputs():
        raise ValueError("再検証の指定中に入力が変わった")
    audit.save(PLAN, {"inputs": before, "versions": versions(), "candidate": SELECTED, "parameters": PARAMETERS,
        "threads": {k: os.environ[k] for k in ("OMP_NUM_THREADS", "OPENBLAS_NUM_THREADS")},
        "threshold": THRESHOLD, "seed": training.SEED, "rows": len(y), "known": int(np.isfinite(y).sum()), "publications": 42,
        "features": names, "old_feature_fingerprint": feature_fingerprint,
        "X_sha256": hashlib.sha256(X.tobytes()).hexdigest(), "y_sha256": hashlib.sha256(y.tobytes()).hexdigest(),
        "cache_sha256": audit.sha(OUT / "cache.npz"), "scoring_data_sha256": audit.sha(OUT / "scoring-data.json"),
        "identities_sha256": audit.sha(OUT / "row-identities.json"), "snapshot_sha256": audit.sha(OUT / "method-before-training.md"),
        "label_changes": changes, "new_candidate_configurations": 0, "historical_candidate_configurations": 534,
        "scope": "adaptive-development-only", "runtime_enabled": False})
    print("v9の固定設定の再検証を指定", len(y), "行、既知", int(np.isfinite(y).sum()), "行")


def checked():
    plan = audit.load(PLAN)
    if plan["inputs"] != inputs() or plan["versions"] != versions():
        raise ValueError("再検証前の固定と違う")
    if plan["threads"] != {k: os.environ.get(k) for k in ("OMP_NUM_THREADS", "OPENBLAS_NUM_THREADS")} or set(plan["threads"].values()) != {"2"}:
        raise ValueError("再学習の並列度が固定の2と違う")
    original = audit.load(audit.RESULTS / "v6-candidates.json")
    if any(plan[k] != value for k, value in (("candidate", SELECTED), ("parameters", PARAMETERS), ("threshold", THRESHOLD),
           ("seed", training.SEED), ("rows", 15658), ("publications", 42), ("features", original["features"]),
           ("old_feature_fingerprint", original["fingerprint"]))):
        raise ValueError("指定の設定・特徴・行数が元の固定と違う")
    for name, field in (("cache.npz", "cache_sha256"), ("scoring-data.json", "scoring_data_sha256"),
                        ("row-identities.json", "identities_sha256"), ("method-before-training.md", "snapshot_sha256")):
        if audit.sha(OUT / name) != plan[field]:
            raise ValueError("固定した教師・特徴・採点・行の対応が違う")
    with np.load(OUT / "cache.npz", allow_pickle=False) as raw:
        cache = {name: raw[name] for name in raw.files}
    if cache["X"].shape != (15658, 276) or hashlib.sha256(cache["X"].tobytes()).hexdigest() != plan["X_sha256"] or hashlib.sha256(cache["y"].tobytes()).hexdigest() != plan["y_sha256"]:
        raise ValueError("元の特徴または指定した教師と違う")
    data = unpack_scoring(audit.load(OUT / "scoring-data.json"))
    rows = [row for sample in data.values() for row in sample["lines"]]
    identities = audit.load(OUT / "row-identities.json")
    fields = ("group", "stratum", "unit", "publication", "key", "line_index")
    if len(rows) != 15658 or [{k: row[k] for k in fields} for row in rows] != [{k: row[k] for k in fields} for row in identities]:
        raise ValueError("教師・特徴の順序と採点する全行の順序が違う")
    y = np.asarray([int(r["error"]) if r["rule"] == "exact" else np.nan for r in rows], dtype=np.float64)
    if not np.array_equal(y, cache["y"], equal_nan=True) or not np.array_equal(np.asarray([r["publication"] for r in rows]), cache["publications"]):
        raise ValueError("採点する教師や出版物と学習配列の対応が違う")
    if cache["old_probabilities"].shape != y.shape or not np.isfinite(cache["old_probabilities"]).all() or ((cache["old_probabilities"] < 0) | (cache["old_probabilities"] > 1)).any():
        raise ValueError("旧予測の全行の確率が違う")
    return plan, cache, data


def train():
    target, raw_path = audit.RESULTS / "v9-fixed-revalidation.json", OUT / "predictions.npz"
    if target.exists() or raw_path.exists():
        raise FileExistsError("再検証の結果を上書きしない")
    plan, cache, data = checked()
    old_diagnostic = evaluate(data, cache["old_probabilities"])
    def progress(number, _, held_out):
        audit.save(OUT / f"progress-{number:02d}.json", {"fold": number, "held_out": held_out})
        print("固定設定の出版物LOPO", number, "/42", flush=True)
    probabilities, folds, notices = training.oof_predictions("hgb", PARAMETERS, cache["X"], cache["y"], cache["publications"], progress)
    result = evaluate(data, probabilities)
    if plan != checked()[0]:
        raise ValueError("再学習中に入力が変わった")
    with raw_path.open("xb") as stream:
        np.savez_compressed(stream, probabilities=probabilities)
    audit.save(target, {"plan_sha256": audit.sha(PLAN), "prediction_sha256": audit.sha(raw_path),
        "old_fixed_prediction_with_new_truth": old_diagnostic, "refitted_fixed_configuration": result,
        "folds": folds, "warnings": notices, "candidate": SELECTED, "runtime_enabled": False,
        "region_audit_complete": False, "image_truth_audit_complete": False, "independent_validation_complete": False})
    print("固定設定の再検証", {"all_pass": result["all_pass"], "all_gates": result["all_gates"]})


def verify():
    plan, cache, data = checked()
    result = audit.load(audit.RESULTS / "v9-fixed-revalidation.json")
    if result["plan_sha256"] != audit.sha(PLAN) or result["prediction_sha256"] != audit.sha(OUT / "predictions.npz"):
        raise ValueError("予測が再検証の指定に結び付かない")
    with np.load(OUT / "predictions.npz", allow_pickle=False) as raw:
        probabilities = raw["probabilities"]
    if probabilities.shape != cache["y"].shape or not np.isfinite(probabilities).all() or ((probabilities < 0) | (probabilities > 1)).any():
        raise ValueError("全行の確率でない")
    if evaluate(data, cache["old_probabilities"]) != result["old_fixed_prediction_with_new_truth"] or evaluate(data, probabilities) != result["refitted_fixed_configuration"]:
        raise ValueError("保存した予測から再構成した全配置の結果と違う")
    audit.save(audit.RESULTS / "v9-fixed-prediction-integrity.json", {"plan_sha256": audit.sha(PLAN),
        "result_sha256": audit.sha(audit.RESULTS / "v9-fixed-revalidation.json"), "rows": len(probabilities),
        "both_results_reproduced": True, "features_and_truth_preserved": True})
    print("全予測から二つの検証結果を再構成し、一致")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("mode", choices=("prepare", "train", "verify"))
    args = parser.parse_args()
    {"prepare": prepare, "train": train, "verify": verify}[args.mode]()
