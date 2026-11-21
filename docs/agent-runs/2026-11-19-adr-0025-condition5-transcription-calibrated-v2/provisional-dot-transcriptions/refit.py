"""仮転記184行のラベルを加えたときの設定固定・出版物別再学習を診断する。"""

from collections import Counter
import importlib.util
import json
from pathlib import Path

import numpy as np

HERE = Path(__file__).resolve().parent
SENSITIVITY = HERE / "sensitivity.py"
spec = importlib.util.spec_from_file_location("sensitivity", SENSITIVITY)
fixed = importlib.util.module_from_spec(spec)
spec.loader.exec_module(fixed)
score, load, sha = fixed.score, fixed.load, fixed.sha
V9, BENCH, CORPUS = fixed.V9, fixed.BENCH, fixed.CORPUS
OUT = CORPUS / HERE.name / "fixed-configuration-refit"


def data_with_provisional():
    plan_path = BENCH / "results/v9-revalidation-plan.json"
    plan = load(plan_path)
    experiment = load(HERE / "sensitivity.json")
    paths = (plan_path, V9 / "cache.npz", V9 / "scoring-data.json", V9 / "row-identities.json",
             HERE / "result.json", HERE / "sensitivity.json", CORPUS / HERE.name / "full-lines.json",
             Path(__file__), Path(score.__file__), Path(score.training.__file__),
             Path(score.frozen.score_v4.__file__))
    inputs = {p.resolve().as_posix(): sha(p) for p in paths}
    if (sha(paths[1]) != plan["cache_sha256"] or sha(paths[2]) != plan["scoring_data_sha256"]
            or sha(paths[3]) != plan["identities_sha256"]
            or sha(paths[6]) != load(paths[4])["private_full_lines_sha256"]
            or sha(paths[6]) != experiment["inputs"]["full-lines.json"]
            or sha(paths[10]) != experiment["inputs"]["score_v4.py"]):
        raise ValueError("元の固定資料か仮転記が診断と異なる")
    choice, params = score.selected_configuration()
    if choice != "hgb" or params != plan["parameters"] or plan["candidate"] != score.SELECTED:
        raise ValueError("固定したモデルの設定が異なる")
    with np.load(paths[1], allow_pickle=False) as archive:
        x, previous, publications = (archive[name] for name in ("X", "y", "publications"))
    if plan["X_sha256"] != score.hashlib.sha256(x.tobytes()).hexdigest() or x.shape != (15658, 276):
        raise ValueError("全行の元特徴が固定と違う")
    if plan["y_sha256"] != score.hashlib.sha256(previous.tobytes()).hexdigest() or len(set(publications)) != 42:
        raise ValueError("元の教師と出版物の構成が違う")
    data = score.unpack_scoring(load(paths[2]))
    identities = load(paths[3])
    provisional = {fixed.identity(r): r for r in load(paths[6])}
    if len(provisional) != len(load(paths[6])):
        raise ValueError("仮転記に行の重複")
    primary = {}
    updated = previous.copy()
    seen, counts, errors = set(), Counter(), Counter()
    index = 0
    for group, sample in data.items():
        for row in sample["lines"]:
            key = fixed.identity(row)
            if fixed.identity(identities[index]) != key or publications[index] != row["publication"]:
                raise ValueError("採点、特徴、出版物の行順が異なる")
            if key in provisional:
                if row["rule"] != "unresolved" or np.isfinite(previous[index]) or key in seen:
                    raise ValueError("仮転記を元の未決定へ対応できない")
                name, line = key
                if name not in primary:
                    primary[name] = load(CORPUS / "ocr3" / (name + ".json"))["lines"]
                ocr, candidate = primary[name][line], provisional[key]
                digest = score.hashlib.sha256(ocr["text"].encode("utf-8")).hexdigest()
                if (digest != candidate["ocr_text_sha256"] or digest != identities[index]["ocr_text_sha256"]
                        or ocr["box"] != identities[index]["box"] or ocr["box"] != candidate["box"]):
                    raise ValueError("OCRの固定本文か箱が異なる")
                error = score.audit.normalize(ocr["text"]) != score.audit.normalize(candidate["text"])
                updated[index] = int(error)
                row.update(rule="exact", error=error)
                seen.add(key)
                counts[group] += 1
                errors[group] += error
            index += 1
    if index != len(previous) or seen != provisional.keys():
        raise ValueError("評価行をすべて照合できない")
    for group in counts:
        saved = experiment["updates"][group]
        if counts[group] != saved["rows"] or errors[group] != saved["errors_if_provisional"]:
            raise ValueError("仮ラベルを元の感度診断から再現できない")
    return data, x, updated, publications, choice, params, inputs


def main():
    destination = HERE / "refit-result.json"
    if destination.exists() or OUT.exists():
        raise FileExistsError("設定固定の再学習結果を上書きしない")
    data, x, y, publications, family, params, inputs = data_with_provisional()
    OUT.mkdir(parents=True)
    score.audit.save(OUT / "inputs.json", {"scope": "provisional-development-only", "inputs": inputs,
                      "candidate": score.SELECTED, "parameters": params, "threshold": score.THRESHOLD,
                      "learner_versions": score.versions(),
                      "label_array_sha256": score.hashlib.sha256(y.tobytes()).hexdigest()})

    def progress(number, unused_total, held_out):
        score.audit.save(OUT / f"progress-{number:02d}.json", {"fold": number, "held_out": held_out})
        print("仮転記の出版物LOPO", number, "/42", flush=True)

    probabilities, folds, notices = score.training.oof_predictions(family, params, x, y, publications, progress)
    if probabilities.shape != y.shape or not np.isfinite(probabilities).all():
        raise ValueError("全行の再学習予測がない")
    for p, digest in inputs.items():
        if sha(Path(p)) != digest:
            raise ValueError("再学習中に資料が変化")
    p = OUT / "predictions.npz"
    with p.open("xb") as stream:
        np.savez_compressed(stream, probabilities=probabilities)
    print("既存採点器で全配置を診断", flush=True)
    values = score.evaluate(data, probabilities)
    with destination.open("x", encoding="utf-8") as stream:
        json.dump({"scope": "hypothetical-refit-performance", "candidate": score.SELECTED,
                   "inputs_sha256": sha(OUT / "inputs.json"), "predictions_sha256": sha(p),
                   "folds": folds, "warnings": notices, "evaluation": values}, stream, ensure_ascii=False, indent=2)
    print(json.dumps({"pass": {k: v["pass"] for k, v in values["robust"].items()},
                      "all_pass": values["all_pass"], "all_gates": values["all_gates"]}, ensure_ascii=False), flush=True)


if __name__ == "__main__":
    main()
