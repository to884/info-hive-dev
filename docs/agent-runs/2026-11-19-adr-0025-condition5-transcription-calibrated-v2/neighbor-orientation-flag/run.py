"""近傍のOCR枠の幾何だけを特徴に追加し、固定済みv9の教師で比較する。"""

import argparse
from collections import defaultdict
import hashlib
import importlib.util
import json
from pathlib import Path

HERE = Path(__file__).resolve().parent
SENSITIVITY = HERE.parent / "provisional-dot-transcriptions/sensitivity.py"
spec = importlib.util.spec_from_file_location("fixed_labels", SENSITIVITY)
fixed = importlib.util.module_from_spec(spec)
spec.loader.exec_module(fixed)
score, load, sha, np = fixed.score, fixed.load, fixed.sha, fixed.np
BENCH, CORPUS, V9 = fixed.BENCH, fixed.CORPUS, fixed.V9
BASE_PLAN, OUT = BENCH / "results/v9-revalidation-plan.json", CORPUS / HERE.name
LOCK = HERE / "lock.json"
CANDIDATE = "ocr-neighbor-orientation-hgb@0.15"
FEATURES = tuple(f"{side}_{metric}" for side in ("above", "below")
                 for metric in ("parallel_count", "perpendicular_count", "long_perpendicular_count",
                                "parallel_coverage", "perpendicular_coverage", "long_perpendicular_coverage"))


def relative_boxes(box, boxes, vertical):
    order = (1, 0, 3, 2) if vertical else (0, 1, 2, 3)
    x, y, span, height = box[list(order)]
    left, top, length, breadth = boxes[:, order].T
    right, bottom = left + length, top + breadth
    clipped_left, clipped_right = np.maximum(x, left), np.minimum(x + span, right)
    overlap = clipped_right > clipped_left
    center_y = top + breadth / 2
    gap = np.maximum(np.maximum(y - bottom, top - y - height), 0)
    near = overlap & (gap <= max(12, 2 * height))
    before = (center_y < y) | (top <= y - height)
    after = (center_y >= y + height) | (bottom >= y + 2 * height)
    return span, height, length, breadth, clipped_left, clipped_right, near, (before, after)


def union_width(left, right):
    total, end = 0, -1
    for start, stop in sorted(zip(left, right)):
        total += max(0, stop - max(start, end))
        end = max(end, stop)
    return total


def describe(boxes, vertical, index):
    direction = vertical[index]
    span, height, lengths, breadths, left, right, nearby, sides = relative_boxes(boxes[index], boxes, direction)
    perpendicular = direction != vertical
    long = perpendicular & (breadths >= 2 * np.maximum(lengths, height))
    measures = []
    for side in sides:
        selected = nearby & side
        variants = (selected & ~perpendicular, selected & perpendicular, selected & long)
        measures.extend(min(25, int(mask.sum())) / 25 for mask in variants)
        measures.extend(union_width(left[mask], right[mask]) / span for mask in variants)
    return measures


def inputs():
    files = (Path(__file__), HERE / "protocol.md", BASE_PLAN, SENSITIVITY, V9 / "row-identities.json",
             V9 / "cache.npz", V9 / "scoring-data.json", Path(score.__file__),
             Path(score.training.__file__), Path(score.frozen.score_v4.__file__))
    return {str(path): sha(path) for path in files}


def page_features(key, rows, original):
    source = CORPUS / "ocr3" / (key + ".json")
    digest = sha(source)
    known = {original["inputs"][k] for k in (source.resolve().as_posix(),
             source.relative_to(score.audit.ROOT).as_posix()) if k in original["inputs"]}
    if known != {digest}:
        raise ValueError("周辺に使う保存OCRが固定入力と違う")
    lines = load(source)["lines"]
    boxes = np.asarray([r["box"] for r in lines], dtype=np.int64)
    directions = np.asarray([bool(r.get("vertical")) for r in lines])
    if boxes.shape != (len(lines), 4) or (boxes[:, 2:] <= 0).any():
        raise ValueError("OCRの枠の寸法が無効")
    result = []
    for matrix_index, row in rows:
        index = row["line_index"]
        raw = lines[index]
        if row["box"] != raw["box"] or row["ocr_text_sha256"] != hashlib.sha256(raw["text"].encode()).hexdigest():
            raise ValueError("採点対象と認識行の固定が違う")
        result.append((matrix_index, describe(boxes, directions, index)))
    return result


def prepare():
    if LOCK.exists() or OUT.exists():
        raise FileExistsError("実験の指定はすでに固定済み")
    before, original = inputs(), load(BASE_PLAN)
    page_rows = defaultdict(list)
    path = V9 / "row-identities.json"
    if sha(path) != original["identities_sha256"]:
        raise ValueError("全行の対応が固定と違う")
    for index, row in enumerate(load(path)):
        page_rows[row["key"]].append((index, row))
    extra = np.full((15658, len(FEATURES)), np.nan)
    for key, rows in sorted(page_rows.items()):
        for index, features in page_features(key, rows, original):
            extra[index] = features
    if not np.isfinite(extra).all() or before != inputs():
        raise ValueError("特徴が欠けるか固定入力が変化")
    OUT.mkdir()
    p = OUT / "features.npy"
    with p.open("xb") as stream:
        np.save(stream, extra, allow_pickle=False)
    score.audit.save(LOCK, {"inputs": before, "candidate": CANDIDATE, "feature_names": FEATURES,
                            "features_sha256": sha(p), "scope": "v9-trusted-labels-development",
                            "threshold": score.THRESHOLD, "parameters": score.PARAMETERS,
                            "seed": score.training.SEED, "publications": 42})
    print(sha(LOCK), len(extra), "行", len(FEATURES), "特徴", flush=True)


def train(expected):
    p, dest = OUT / "features.npy", OUT / "predictions.npz"
    report = HERE / "result.json"
    if dest.exists() or report.exists():
        raise FileExistsError("実験はすでに実行済み")
    lock, original = load(LOCK), load(BASE_PLAN)
    if (sha(LOCK) != expected or lock["inputs"] != inputs()
            or sha(p) != lock["features_sha256"] or sha(V9 / "cache.npz") != original["cache_sha256"]
            or sha(V9 / "scoring-data.json") != original["scoring_data_sha256"]):
        raise ValueError("固定した特徴・教師・採点の対応が違う")
    data = score.unpack_scoring(load(V9 / "scoring-data.json"))
    with np.load(V9 / "cache.npz", allow_pickle=False) as archive:
        X, y, pub = (archive[k] for k in ("X", "y", "publications"))
    if X.shape != (15658, 276) or len(set(pub)) != 42 or score.versions() != original["versions"]:
        raise ValueError("元の全行と学習条件が違う")
    family, params = score.selected_configuration()
    added = np.load(p, allow_pickle=False)
    matrix = np.column_stack((X, added))

    def progress(i, total, publication):
        if i % 7 == 0:
            print(CANDIDATE, i, "/", total, flush=True)

    prob, folds, warnings = score.training.oof_predictions(family, params, matrix, y, pub, progress)
    if lock["inputs"] != inputs() or sha(LOCK) != expected or sha(p) != lock["features_sha256"]:
        raise ValueError("実行中に固定が変わった")
    with dest.open("xb") as stream:
        np.savez_compressed(stream, probabilities=prob)
    result = score.evaluate(data, prob)
    score.audit.save(report, {"scope": lock["scope"], "candidate": CANDIDATE, "lock_sha256": expected,
                              "predictions_sha256": sha(dest), "folds": folds, "warnings": warnings,
                              "evaluation": result})
    print(json.dumps({k: v["pass"] for k, v in result["robust"].items()}), flush=True)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("action", choices=("prepare", "train"))
    parser.add_argument("--lock-sha256")
    args = parser.parse_args()
    if args.action == "prepare":
        prepare()
    else:
        train(args.lock_sha256)
