"""固定画像と主OCRだけから点線の特徴を作り、1候補を仮ラベルで検証する。"""

import argparse
from concurrent.futures import ThreadPoolExecutor
import hashlib
import importlib.util
import json
from pathlib import Path

import numpy as np
from PIL import Image

HERE = Path(__file__).resolve().parent
SHADOW = HERE.parent / "provisional-dot-transcriptions/refit.py"
DETECTOR = HERE.parent / "dot-layout-v2/run.py"


def module(name, path):
    spec = importlib.util.spec_from_file_location(name, path)
    loaded = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(loaded)
    return loaded


refit = module("dot_shadow", SHADOW)
detector = module("dot_pixels", DETECTOR)
score, load, sha = refit.score, refit.load, refit.sha
BENCH, CORPUS, V9 = refit.BENCH, refit.CORPUS, refit.V9
OUT = CORPUS / HERE.name
PLAN = HERE / "lock.json"
CANDIDATE = "visual-dot-count-hgb@0.15"
FEATURES = ("horizontal_points_measured", "has_regular_visual_points", "has_ocr_points",
            "visual_point_total", "ocr_point_total", "point_shortage", "point_excess",
            "relative_point_difference", "equal_positive_points", "visual_run_fraction",
            "regular_run_count", "ambiguous_visual_runs")


def evidence(gray, box, text, vertical):
    """本文から点の個数を数え、独立に同じ画素から小成分の個数を測る。"""
    x, y, width, height = box
    h, w = gray.shape
    if vertical or width < 8 or height < 2 or not (0 <= x < x + width <= w and 0 <= y < y + height <= h):
        return [0.0] * len(FEATURES)
    target = x, y, x + width, y + height
    window = max(x - 12, 0), max(y - 12, 0), min(x + width + 12, w), min(y + height + 12, h)
    a, b, c, d = detector.ink.expanded_window(window, (w, h))
    l, t, r, bottom = window
    background = float(np.median(gray[b:d, a:c]))
    components = detector.ink.measure(gray[t:bottom, l:r], window, target, 0, background, ())["components"]
    points = []
    for part in components:
        left, top, right, last = part["bounds"]
        if (2 <= right - left <= 5 and 2 <= last - top <= 5 and part["pixels"] >= 4
                and part["cross_axis_center_inside"] and 2 * part["axis_overlap"] >= part["axis_length"]
                and not part["touches_window_edge"]):
            points.append(tuple(part["bounds"]))
    groups, competing = detector.regular_groups(points)
    picture_count = sum(len(items) for items in groups)
    ocr_count = sum(detector.reference_point_counts(score.audit.normalize(text)))
    longest = max((items[-1][2] - items[0][0] for items in groups), default=0)
    count_scale = lambda n: min(1.0, n / 100)
    return [1.0, bool(groups), bool(ocr_count), count_scale(picture_count), count_scale(ocr_count),
            count_scale(max(picture_count - ocr_count, 0)), count_scale(max(ocr_count - picture_count, 0)),
            abs(picture_count - ocr_count) / max(picture_count, ocr_count, 1),
            picture_count == ocr_count and picture_count > 0, min(1.0, longest / width),
            min(1.0, len(groups) / 5), bool(competing)]


def input_paths():
    paths = (Path(__file__), SHADOW, DETECTOR, HERE / "protocol.md",
             BENCH / "results/v9-revalidation-plan.json", V9 / "row-identities.json", V9 / "cache.npz",
             HERE.parent / "provisional-dot-transcriptions/refit-result.json")
    return {p.resolve().as_posix(): sha(p) for p in paths}


def page_features(key, rows, pins):
    png = CORPUS / "probe-v4/png" / (key + ".png")
    ocr = CORPUS / "ocr3" / (key + ".json")
    for path in (png, ocr):
        known = {pins[key] for key in (path.resolve().as_posix(), path.relative_to(score.audit.ROOT).as_posix()) if key in pins}
        if known != {sha(path)}:
            raise ValueError("固定画像または認識本文の元資料が異なる")
    with Image.open(png) as opened:
        gray = np.asarray(opened.convert("L"))
    recognized = load(ocr)["lines"]
    features = []
    for i, r in rows:
        line = recognized[r["line_index"]]
        text = line["text"]
        if line["box"] != r["box"] or hashlib.sha256(text.encode()).hexdigest() != r["ocr_text_sha256"]:
            raise ValueError("固定した認識行、枠と異なる")
        features.append((i, evidence(gray, line["box"], text, bool(line.get("vertical")))))
    return features


def prepare():
    if OUT.exists() or PLAN.exists():
        raise FileExistsError("候補の固定は一度だけ")
    before = input_paths()
    original = load(BENCH / "results/v9-revalidation-plan.json")
    if sha(V9 / "row-identities.json") != original["identities_sha256"]:
        raise ValueError("固定の行対応と異なる")
    identities = load(V9 / "row-identities.json")
    pages = {}
    for i, row in enumerate(identities):
        pages.setdefault(row["key"], []).append((i, row))
    pool_inputs = list(pages.items())
    features = np.zeros((len(identities), len(FEATURES)), dtype=np.float64)
    with ThreadPoolExecutor(max_workers=4) as pool:
        tasks = [pool.submit(page_features, key, rows, original["inputs"]) for key, rows in pool_inputs]
        for task in tasks:
            for i, value in task.result():
                features[i] = value
    if features.shape != (15658, len(FEATURES)) or not np.isfinite(features).all() or input_paths() != before:
        raise ValueError("特徴か固定資料が変化")
    OUT.mkdir(parents=True)
    path = OUT / "extra.npy"
    with path.open("xb") as stream:
        np.save(stream, features, allow_pickle=False)
    manifest = {"scope": "development-provisional-labels", "inputs": before, "candidate": CANDIDATE,
                "names": list(FEATURES), "extra_sha256": sha(path), "threshold": score.THRESHOLD,
                "seed": score.training.SEED, "rows": len(identities), "parameters": score.PARAMETERS}
    score.audit.save(PLAN, manifest)
    print(sha(PLAN), len(identities), "行", int((features[:, 1] > 0).sum()), "行に点線候補", flush=True)


def train(expected):
    result_path = HERE / "result.json"
    predictions_path = OUT / "predictions.npz"
    if result_path.exists() or predictions_path.exists():
        raise FileExistsError("実行結果を上書きしない")
    lock = load(PLAN)
    extra = OUT / "extra.npy"
    if (sha(PLAN) != expected or lock["inputs"] != input_paths() or lock["extra_sha256"] != sha(extra)
            or lock["candidate"] != CANDIDATE or lock["names"] != list(FEATURES)):
        raise ValueError("事前登録した候補と入力が異なる")
    data, x, y, publications, model, params, refit_inputs = refit.data_with_provisional()
    added = np.load(extra, allow_pickle=False)
    matrix = np.concatenate((x, added), axis=1)

    def progress(i, unused_count, publication):
        score.audit.save(OUT / f"fold-{i:02d}.json", {"fold": i, "held_out": publication})
        if i % 7 == 0:
            print(CANDIDATE, i, "/42", flush=True)

    prob, folds, notices = score.training.oof_predictions(model, params, matrix, y, publications, progress)
    if (lock["inputs"] != input_paths() or lock["extra_sha256"] != sha(extra)
            or any(sha(Path(k)) != digest for k, digest in refit_inputs.items())):
        raise ValueError("学習中に入力か特徴が変化")
    with predictions_path.open("xb") as stream:
        np.savez_compressed(stream, probabilities=prob)
    value = score.evaluate(data, prob)
    score.audit.save(result_path, {"scope": "development-only-provisional-labels", "candidate": CANDIDATE,
                                   "lock_sha256": expected, "prediction_sha256": sha(predictions_path),
                                   "folds": folds, "warnings": notices, "evaluation": value})
    print(json.dumps({"all_pass": value["all_pass"], "all_gates": value["all_gates"],
                      "group_pass": {k: v["pass"] for k, v in value["robust"].items()}}, ensure_ascii=False), flush=True)


if __name__ == "__main__":
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("action", choices=("prepare", "train"))
    p.add_argument("--lock-sha256")
    args = p.parse_args()
    if args.action == "prepare":
        prepare()
    else:
        train(args.lock_sha256)
