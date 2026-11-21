"""監査候補の正解と、補充より前に固定した周辺枠モデルの予測を結ぶ。"""

import importlib.util
import json
from pathlib import Path

from assemble import HERE, OUT, PARENT, CORPUS, load, np, score, sha

LOCK = HERE / "candidate-lock.json"
CONTEXT = PARENT / "neighbor-orientation-flag"
COUNTED = PARENT / "counted-assignments/counted.py"
COMPARISON = COUNTED.parent / "crosscheck.json"


def evaluate(data, probabilities):
    spec = importlib.util.spec_from_file_location("counted", COUNTED)
    counting = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(counting)
    old = score.frozen.score_v4
    confirmed = load(COMPARISON)
    for path in (COUNTED, Path(old.__file__), Path(old.score_v2.__file__), Path(old.score_v2.score.__file__)):
        if confirmed["inputs"][str(path)] != sha(path):
            raise ValueError("件数版と比較した採点器に変更がある")
    flags = probabilities >= score.THRESHOLD
    robust = {}
    for name, sample in score.training.predicted_samples(data, flags).items():
        r = counting.robust(sample, old.score_v2, public_margin=name.endswith("-public"))
        robust[name] = r
        print(name, r["assignments"], r["checked"], r["pass"], r["gate"], flush=True)
    name = load(CONTEXT / "result.json")["candidate"]
    return {"points": score.training.evaluate(data, flags, name), "robust": robust,
            "all_pass": all(v["pass"] for v in robust.values()), "all_gates": all(v["gate"] for v in robust.values())}


def main():
    destination = HERE / "candidate-score.json"
    if destination.exists():
        raise FileExistsError("候補の採点結果を上書きしない")
    result = CONTEXT / "result.json"
    prediction = CORPUS / "neighbor-orientation-flag/predictions.npz"
    metadata = load(result)
    if sha(prediction) != metadata["predictions_sha256"] or sha(CONTEXT / "lock.json") != metadata["lock_sha256"]:
        raise ValueError("選んだ候補の予測は固定した版と異なる")
    files = load(LOCK)["artifacts"]
    for name, digest in files.items():
        if sha(OUT / name) != digest:
            raise ValueError("別版の正解が変わった")
    data = score.unpack_scoring(load(OUT / "scoring.json"))
    with np.load(prediction, allow_pickle=False) as f:
        probabilities = f["probabilities"]
    rows = sum(len(s["lines"]) for s in data.values())
    if probabilities.shape != (rows,) or rows != 15658 or not np.isfinite(probabilities).all():
        raise ValueError("固定の採点行と予測の対応がない")
    paths = (Path(__file__), LOCK, result, prediction, COUNTED, COMPARISON)
    inputs = {str(p): sha(p) for p in paths}
    observed = evaluate(data, probabilities)
    if inputs != {str(p): sha(p) for p in paths}:
        raise ValueError("採点中に入力が変わった")
    with destination.open("x", encoding="utf-8") as stream:
        json.dump({"scope": "frozen-development-reference-candidate-not-audited",
                   "candidate": metadata["candidate"], "threshold": score.THRESHOLD,
                   "label_lock_sha256": sha(LOCK), "prediction_sha256": sha(prediction),
                   "inputs": inputs, "evaluation": observed}, stream, ensure_ascii=False, indent=2)


if __name__ == "__main__":
    main()
