"""選ぶ資料の、後から見た分析（測る前に決めたものではない）。results/tuning.json と tuning-lines-*.json を読む。

使い方: python -X utf8 scripts/posthoc_tuning.py
- 条件ごとの候補の集まり（(a)、(b)、(c) のそれぞれを満たす閾値）
- (b) の上限（t = 0.99 の (b) と、そのときの (c)）
- 合成の誤りの種類: 正解と OCR の違う文字に、英字と数字が入るか（後から見た分け方）
- 合成の画像の種類ごとの、行の誤りの割合と確信度の分布
結果を results/tuning-posthoc.json に書く。
"""

from __future__ import annotations

import difflib
import json
import statistics
from pathlib import Path

BENCH = Path(__file__).resolve().parent.parent
RESULTS = BENCH / "results"


def ranges(values: list[float]) -> str:
    if not values:
        return "なし"
    out, start, prev = [], values[0], values[0]
    for v in values[1:]:
        if round(v - prev, 2) > 0.01:
            out.append(f"{start:.2f}〜{prev:.2f}" if start != prev else f"{start:.2f}")
            start = v
        prev = v
    out.append(f"{start:.2f}〜{prev:.2f}" if start != prev else f"{start:.2f}")
    return "、".join(out)


def main() -> None:
    tuning = json.loads((RESULTS / "tuning.json").read_bytes().decode("utf-8"))
    report = {"per_condition": {}, "ceiling": {}}
    for s, rows in tuning["grid"].items():
        per = {}
        for margin in (0.05, 0.0):
            per[str(margin)] = {
                "a": ranges([r["threshold"] for r in rows if r["a"] is not None and r["a"] >= 0.5 + margin]),
                "b": ranges([r["threshold"] for r in rows if r["b"] is not None and r["b"] >= 0.8 + margin]),
                "c_always": ranges([r["threshold"] for r in rows if r["always"]["c"] is not None
                                    and r["always"]["c"] <= 0.2 - margin]),
                "c_auto": ranges([r["threshold"] for r in rows if r["auto"]["c"] is not None
                                  and r["auto"]["c"] <= 0.2 - margin]),
            }
        report["per_condition"][s] = per
        last = rows[-1]
        report["ceiling"][s] = {"threshold": last["threshold"], "b": last["b"], "c_always": last["always"]["c"],
                                "c_auto": last["auto"]["c"]}
        print(s, json.dumps(per, ensure_ascii=False))
        print("  t=0.99:", json.dumps(report["ceiling"][s], ensure_ascii=False))

    lines = json.loads((RESULTS / "tuning-lines-synthetic.json").read_bytes().decode("utf-8"))
    kinds = {"latin_or_digit": [], "other": []}
    for r in lines:
        if r["rule"] != "exact" or not r["error"]:
            continue
        changed = set()
        for tag, i1, i2, j1, j2 in difflib.SequenceMatcher(None, r["truth_text"], r["ocr_text"], autojunk=False).get_opcodes():
            if tag != "equal":
                changed.update(r["truth_text"][i1:i2] + r["ocr_text"][j1:j2])
        latin = any(c.isascii() and c.isalnum() for c in changed)
        kinds["latin_or_digit" if latin else "other"].append(r["confidence"])
    correct = [r["confidence"] for r in lines if r["rule"] == "exact" and not r["error"]]
    report["error_kinds"] = {k: {"lines": len(v), "median_confidence": statistics.median(v) if v else None,
                                 "share_at_or_above_0.9": sum(c >= 0.9 for c in v) / len(v) if v else None}
                             for k, v in kinds.items()}
    report["error_kinds"]["correct"] = {"lines": len(correct), "median_confidence": statistics.median(correct),
                                        "share_below_0.5": sum(c < 0.5 for c in correct) / len(correct)}
    by_variant = {}
    for r in lines:
        v = by_variant.setdefault(r["variant"], {"lines": 0, "errors": 0, "confidence": []})
        v["lines"] += 1
        v["errors"] += bool(r.get("error"))
        v["confidence"].append(r["confidence"])
    report["by_variant"] = {k: {"lines": v["lines"], "error_share": round(v["errors"] / v["lines"], 3),
                                "median_confidence": round(statistics.median(v["confidence"]), 3),
                                "min_confidence": min(v["confidence"])} for k, v in sorted(by_variant.items())}
    print("誤りの種類:", json.dumps(report["error_kinds"], ensure_ascii=False))
    print("画像の種類ごと:", json.dumps(report["by_variant"], ensure_ascii=False))
    (RESULTS / "tuning-posthoc.json").write_bytes((json.dumps(report, ensure_ascii=False, indent=1) + "\n").encode("utf-8"))


if __name__ == "__main__":
    main()
