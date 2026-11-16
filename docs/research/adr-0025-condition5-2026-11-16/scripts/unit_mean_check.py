"""単位ごとの比の平均（単位の大きさによらない数え方）と、その片側 95% の限界を、選ぶ資料で見る（後から見た試し）。

使い方（rag の依存の環境で動かす）: python -X utf8 scripts/unit_mean_check.py tuning
6 回目のレビューの指摘（行で重みを付けた比の限界は、単位の大きさの偏りに弱い）を受けて、直し方を決めるために使う。
"""

from __future__ import annotations

import math
import statistics
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

import score_v2  # noqa: E402


def t_bound(values: list[float], side: str) -> float | None:
    from scipy.stats import t as student

    if len(values) < 2:
        return None
    mean = statistics.fmean(values)
    half = float(student.ppf(0.95, len(values) - 1)) * statistics.stdev(values) / math.sqrt(len(values))
    return round(mean - half if side == "lower" else mean + half, 4)


def main() -> None:
    data = score_v2.collect(sys.argv[1])
    for stratum, d in data.items():
        units: dict[str, dict] = {}
        for r in d["lines"]:
            flagged = bool(r["reasons"])
            error = r["error"] if r["rule"] == "exact" else not flagged
            u = units.setdefault(r["unit"], {"flagged": 0, "errors": 0, "correct": 0, "caught": 0, "false": 0})
            u["flagged"] += flagged
            u["errors"] += error
            u["correct"] += not error
            u["caught"] += flagged and error
            u["false"] += flagged and not error
        a = [u["caught"] / u["flagged"] for u in units.values() if u["flagged"]]
        b = [u["caught"] / u["errors"] for u in units.values() if u["errors"]]
        c = [u["false"] / u["correct"] for u in units.values() if u["correct"]]
        print(stratum, "単位", len(units))
        for name, values, side in (("a", a, "lower"), ("b", b, "lower"), ("c", c, "upper")):
            print(f"  ({name}) 単位の平均 {statistics.fmean(values):.3f}（{len(values)} 単位）、片側 95% の限界 {t_bound(values, side)}")


if __name__ == "__main__":
    main()
