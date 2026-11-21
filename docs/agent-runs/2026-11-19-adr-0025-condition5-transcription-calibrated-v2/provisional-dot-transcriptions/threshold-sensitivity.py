"""仮転記の感度分析で、閾値だけで全開発群を通過し得るか調べる。"""

from decimal import Decimal
import importlib.util
import json
from pathlib import Path

import numpy as np

HERE = Path(__file__).resolve().parent
REFIT = HERE / "refit.py"
spec = importlib.util.spec_from_file_location("refit_shadow", REFIT)
refit = importlib.util.module_from_spec(spec)
spec.loader.exec_module(refit)
score, load, sha = refit.score, refit.load, refit.sha
THRESHOLDS = tuple(Decimal(n) / 1000 for n in range(75, 426, 25))


def main():
    output = HERE / "threshold-sensitivity.json"
    if output.exists():
        raise FileExistsError("閾値診断を上書きしない")
    data, _, _, _, _, _, locked = refit.data_with_provisional()
    baseline = refit.V9 / "predictions.npz"
    before = load(refit.BENCH / "results/v9-fixed-revalidation.json")
    new = refit.OUT / "predictions.npz"
    after = load(HERE / "refit-result.json")
    if sha(baseline) != before["prediction_sha256"] or sha(new) != after["predictions_sha256"]:
        raise ValueError("元の固定予測が異なる")
    results = {}
    for case, path in (("fixed", baseline), ("refit", new)):
        with np.load(path, allow_pickle=False) as saved:
            probabilities = saved["probabilities"]
        if probabilities.shape != (15658,) or not np.isfinite(probabilities).all():
            raise ValueError("固定した15,658行の全予測がそろわない")
        candidates = {}
        for cut in THRESHOLDS:
            sample = score.training.evaluate(data, probabilities >= float(cut), str(cut))
            necessary = sample["pass_count_at_reference"] == 6 and sample["public_margin_min"] >= .87
            candidates[str(cut)] = {
                "reference_passes": sample["pass_count_at_reference"], "reference_gate_possible": necessary,
                "public_margin_min_at_reference": sample["public_margin_min"],
                "groups": {g: {"pass": value["reference_verdict"]["pass"],
                               "a": value["row"]["a"], "b": value["row"]["b"], "c": value["row"]["c"],
                               "weighted_c_upper": value["row"]["c_upper"],
                               "macro_a_lower": value["row"]["a_mean_lower"],
                               "macro_b_lower": value["row"]["b_mean_lower"]}
                           for g, value in sample["groups"].items()}}
        results[case] = {"prediction_sha256": sha(path), "thresholds": candidates}
    if any(sha(Path(p)) != digest for p, digest in locked.items()):
        raise ValueError("閾値診断中に仮転記か固定資料が変化")
    with output.open("x", encoding="utf-8") as stream:
        json.dump({"scope": "necessary-reference-check-only", "settings": results}, stream, ensure_ascii=False, indent=2)
    print(json.dumps({case: [x for x, r in item["thresholds"].items() if r["reference_gate_possible"]]
                      for case, item in results.items()}, ensure_ascii=False), flush=True)


if __name__ == "__main__":
    main()
