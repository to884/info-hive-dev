"""元の採点器で既存データと生成した配置を再計算する。"""

import json
from pathlib import Path
import random
import sys
import time

from counted import robust

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parent / "source-position-expansion"))
from refit_verified import CORPUS, load, np, score, sha

OLD = score.frozen.score_v4
V2 = OLD.score_v2
COMBINED = CORPUS / "transcription-calibrated-v2-2026-11-19/source-and-figure-development"


def check(data, cap, margin, totals):
    start = time.perf_counter()
    a = OLD.robust_verdict(data, max_assignments=cap, public_margin=margin)
    middle = time.perf_counter()
    b = robust(data, V2, max_assignments=cap, public_margin=margin)
    done = time.perf_counter()
    if a != b:
        raise ValueError(f"単位件数版と元の配置で差が出た: {a!r} != {b!r}")
    totals["old_seconds"] += middle - start
    totals["new_seconds"] += done - middle
    totals["placement_checks"] += a["checked"]
    totals["cases"] += 1


def generated():
    rng = random.Random(20261119)
    for number in range(120):
        size = rng.randint(0, 95)
        n_units = rng.randint(1, 24)
        unresolved = set(rng.sample(range(size), min(size, number % 5)))
        rows = [{"unit": f"unit-{rng.randrange(n_units):02d}", "key": "page", "line_index": i, "eye": rng.random() < .2,
                 "rule": rng.choice(("excluded", "unresolved", "pessimistic")) if i in unresolved else "exact",
                 "reasons": ["flag"] if rng.random() < .5 else [], "error": rng.random() < .55}
                for i in range(size)]
        data = {"lines": rows, "missed": [{"unit": f"unrecognized-{i:02d}"} for i in range(number % 3)]}
        if number % 2:
            data["truth_lines"] = size + len(data["missed"])
        yield data, 8 if number % 3 else OLD.MAX_ASSIGNMENTS, number % 2 == 0


def passing_cases():
    # 良否の境界を行き来する実例を含め、全配置を走り切るケースを検査する。
    for n in (9, 10, 11, 24):
        rows = []
        for u in range(n):
            for i in range(18):
                unknown = i == 9 and u < 6
                rows.append({"unit": f"p-{u}", "key": f"p-{u}", "line_index": i, "rule": "unresolved" if unknown else "exact",
                             "error": i < 7, "reasons": ["flag"] if i < 7 else [], "eye": unknown})
        yield {"lines": rows, "missed": []}, OLD.MAX_ASSIGNMENTS, True


def main():
    output = HERE / "crosscheck.json"
    if output.exists():
        raise FileExistsError("既存の照合結果がある")
    cases = {"old_seconds": 0.0, "new_seconds": 0.0, "cases": 0, "placement_checks": 0}
    for data, cap, margin in (*generated(), *passing_cases()):
        check(data, cap, margin, cases)
    s = COMBINED / "scoring.json"
    p = CORPUS / "neighbor-orientation-flag/predictions.npz"
    report = HERE.parent / "raster-figure-expansion/combined-fixed-scores.json"
    flags = HERE.parent / "neighbor-orientation-flag/result.json"
    if sha(s) != load(report)["artifacts"]["scoring.json"] or sha(p) != load(flags)["predictions_sha256"]:
        raise ValueError("比較に使う既存の正解か予測が違う")
    data = score.unpack_scoring(load(s))
    with np.load(p, allow_pickle=False) as file:
        probabilities = file["probabilities"]
    observed = {}
    for name, sample in score.training.predicted_samples(data, probabilities >= score.THRESHOLD).items():
        initial = cases["placement_checks"]
        check(sample, OLD.MAX_ASSIGNMENTS, name.endswith("-public"), cases)
        observed[name] = cases["placement_checks"] - initial
    dependencies = [s, p, report, flags, Path(__file__), HERE / "counted.py", Path(OLD.__file__),
                    Path(V2.__file__), Path(V2.score.__file__)]
    with output.open("x", encoding="utf-8") as stream:
        json.dump({"scope": "scorer-equivalence-development", "verification": cases,
                   "observed_placements": observed, "inputs": {str(p): sha(p) for p in dependencies}}, stream, indent=2)
    print(cases, observed, flush=True)


if __name__ == "__main__":
    main()
