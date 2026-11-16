"""2 つ目の読みの食い違いが、行の誤りをどれだけ当てるかを、選ぶ資料だけで調べる（後から見た試し。合否には使わない）。

使い方（rag の依存の環境で動かす）: python -X utf8 scripts/probe_analyze.py
corpus/probe/reads/ の読みと、正解（corpus/*/*.truth.json の side が tuning）を突き合わせる。
印は「確信度が t より低い、または食い違いがある」行。(a)〜(c) は score.py と同じ数え方（不利な側の行は、
印があれば誤りでない、なければ誤り）で数える。結果を results/probe-tuning.json に書く。
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

from score import CORPUS, RESULTS, load_truths, normalize, page_records  # noqa: E402

THRESHOLDS = [0.0, 0.2, 0.3, 0.4, 0.5]


def differs(line: dict, key: str) -> bool:
    read = (line.get("reads") or {}).get(key)
    return read is not None and normalize(read["text"]) != normalize(line["text"])


SIGNALS = {
    "none": lambda line: False,
    "r100": lambda line: differs(line, "r100"),
    "r50": lambda line: len(line["text"]) < 45 and differs(line, "r50"),
    "pad": lambda line: differs(line, "pad100"),
    "blur": lambda line: differs(line, "blur100"),
    "models": lambda line: differs(line, "r100") or (len(line["text"]) < 45 and differs(line, "r50")),
    "any": lambda line: (differs(line, "r100") or (len(line["text"]) < 45 and differs(line, "r50"))
                         or differs(line, "pad100") or differs(line, "blur100")),
}


def collect() -> dict:
    found = {"synthetic": {"lines": [], "missed": 0, "pages": []}, "public": {"lines": [], "missed": 0, "pages": []}}
    for truth in load_truths():
        if truth["side"] != "tuning":
            continue
        stratum = truth["stratum"]
        for page in truth["pages"]:
            reads = json.loads((CORPUS / "probe" / "reads" / f"{truth['name']}-p{page['page']:04d}.json")
                               .read_bytes().decode("utf-8"))["lines"]
            ocr_lines = [{**line, "box": [line["box"][0], line["box"][1], line["box"][0] + line["box"][2],
                                          line["box"][1] + line["box"][3]]} for line in reads]
            records, missed = page_records(page["lines"], ocr_lines, stratum)
            for r in records:
                r["line"] = ocr_lines[r["line_index"]]
            found[stratum]["lines"] += records
            found[stratum]["missed"] += len(missed)
            found[stratum]["pages"].append(ocr_lines)
    return found


def measure(data: dict, signal, t: float) -> dict:
    def flagged(line):
        return (line["confidence"] is not None and line["confidence"] < t) or signal(line)

    counted = [r for r in data["lines"] if r["rule"] != "excluded"]
    flags = [r for r in counted if flagged(r["line"])]

    def error(r):
        return r["error"] if r["rule"] == "exact" else not flagged(r["line"])

    errors = sum(error(r) for r in counted) + data["missed"]
    caught = sum(error(r) for r in flags)
    pages = sum(any(flagged(line) for line in page) for page in data["pages"])
    exact = [r for r in counted if r["rule"] == "exact" and r["shape"] == "1:1"]
    exact_errors = [r for r in exact if r["error"]]
    exact_correct = [r for r in exact if not r["error"]]
    return {"flagged": len(flags), "errors": errors, "caught": caught,
            "a": round(caught / len(flags), 3) if flags else None, "b": round(caught / errors, 3) if errors else None,
            "c": round(pages / len(data["pages"]), 3),
            "exact_b": round(sum(flagged(r["line"]) for r in exact_errors) / len(exact_errors), 3) if exact_errors else None,
            "exact_false_flag": round(sum(flagged(r["line"]) for r in exact_correct) / len(exact_correct), 4)
            if exact_correct else None}


def main() -> None:
    data = collect()
    report = {}
    for stratum, d in data.items():
        report[stratum] = {}
        print(stratum, "行", len(d["lines"]), "ページ", len(d["pages"]))
        for name, signal in SIGNALS.items():
            report[stratum][name] = {}
            for t in THRESHOLDS:
                row = measure(d, signal, t)
                report[stratum][name][str(t)] = row
                print(f"  {name:7s} t={t:.1f} 印 {row['flagged']:4d} (a) {row['a']} (b) {row['b']} (c) {row['c']}"
                      f"  1:1 の (b) {row['exact_b']} 正しい行に印 {row['exact_false_flag']}")
    RESULTS.mkdir(exist_ok=True)
    (RESULTS / "probe-tuning.json").write_bytes((json.dumps(report, ensure_ascii=False, indent=1) + "\n").encode("utf-8"))


if __name__ == "__main__":
    main()
