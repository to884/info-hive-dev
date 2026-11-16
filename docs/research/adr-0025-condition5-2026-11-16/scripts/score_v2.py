"""条件 5 の 2 回目（行の印）を数える（測り方は ../../adr-0025-condition5-v2-2026-11-16.md）。

使い方（rag の依存の環境で動かす）:
    python -X utf8 scripts/score_v2.py tuning       # 選ぶ資料で、製品の印の値を確かめる（選ぶことはしない）
    python -X utf8 scripts/score_v2.py evaluation   # 確かめる資料で、1 回だけ合否を決める

印は製品のコードが付けた OCR の結果（corpus/ocr2/）から取る。正規化と読む順と行の対応は、製品の rag_ocr_flags を使う。
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
sys.path.insert(0, str(HERE.parents[3] / "info-hive-rag" / "scripts"))

import rag_ocr_flags  # noqa: E402
import score  # noqa: E402

# 製品と同じ比べ方にする（score.page_records は、この 3 つをモジュールの名前で引く）
score.SAME = rag_ocr_flags.SAME
score.reading_order = rag_ocr_flags.reading_order
score.joined = rag_ocr_flags.joined

from probe_analyze import apply_eye_truth, eye_truth  # noqa: E402
from rag_ocr_flags import OCR_FLAG_REVISION, reasons_for  # noqa: E402
from score import CORPUS, RESULTS, cluster_bound, load_truths, page_records  # noqa: E402

THRESHOLD = 0.3
MIN_UNITS = 10
MIN_COUNT = 20


def collect(side: str) -> dict:
    found = {"synthetic": {"lines": [], "missed": []}, "public": {"lines": [], "missed": []}}
    truths = eye_truth(side)
    for truth in load_truths():
        if truth["side"] != side:
            continue
        stratum = truth["stratum"]
        for page in truth["pages"]:
            key = f"{truth['name']}-p{page['page']:04d}"
            ocr = json.loads((CORPUS / "ocr2" / f"{key}.json").read_bytes().decode("utf-8"))
            if ocr["pdf_sha256"] != truth["pdf_sha256"]:
                raise SystemExit(f"OCR の結果の PDF が正解と違う: {key}")
            if ocr.get("flag_revision") != OCR_FLAG_REVISION:
                raise SystemExit(f"印のない OCR の結果: {key}")
            lines = [{**x, "box": rag_ocr_flags.corners(x["box"]), "source_box": x["box"]} for x in ocr["lines"]]
            records, missed = page_records(page["lines"], lines, stratum)
            if stratum == "public":
                apply_eye_truth(records, key, truths, lines)
            found[stratum]["truth_lines"] = found[stratum].get("truth_lines", 0) + sum(
                1 for x in page["lines"] if not x.get("excluded"))
            unit = truth["name"] if stratum == "synthetic" else key
            for r in records:
                line = lines[r["line_index"]]
                r.update(unit=unit, key=key, variant=page.get("variant"), reasons=reasons_for(line, THRESHOLD))
            found[stratum]["lines"] += records
            found[stratum]["missed"] += [{**m, "unit": unit, "key": key} for m in missed]
    return found


def measure(data: dict) -> dict:
    units: dict[str, dict] = {}
    totals = {"flagged": 0, "errors": 0, "correct": 0, "caught": 0, "false": 0, "pessimistic": 0, "eye": 0}
    for r in data["lines"]:
        # 目で正解を作れなかった行（除いた正解の行と直接つながる行で、読めなかったもの）も、落とさずに不利な側に数える
        flagged = bool(r["reasons"])
        error = r["error"] if r["rule"] == "exact" else not flagged
        u = units.setdefault(r["unit"], {"flagged": 0, "errors": 0, "correct": 0, "caught": 0, "false": 0})
        for name, value in (("flagged", flagged), ("errors", error), ("correct", not error),
                            ("caught", flagged and error), ("false", flagged and not error)):
            u[name] += value
            totals[name] += value
        totals["pessimistic"] += r["rule"] == "pessimistic"
        totals["eye"] += bool(r.get("eye"))
    for m in data["missed"]:
        units.setdefault(m["unit"], {"flagged": 0, "errors": 0, "correct": 0, "caught": 0, "false": 0})

    def ratio(k, n):
        return totals[k] / totals[n] if totals[n] else None

    def informative(n):
        return sum(1 for u in units.values() if u[n])

    return {**totals, "missed": len(data["missed"]), "units": len(units),
            "missed_share": len(data["missed"]) / data["truth_lines"] if data.get("truth_lines") else None,
            "a": ratio("caught", "flagged"), "b": ratio("caught", "errors"), "c": ratio("false", "correct"),
            "a_lower": cluster_bound([(u["caught"], u["flagged"]) for u in units.values()], "lower"),
            "b_lower": cluster_bound([(u["caught"], u["errors"]) for u in units.values()], "lower"),
            "c_upper": cluster_bound([(u["false"], u["correct"]) for u in units.values()], "upper"),
            "units_a": informative("flagged"), "units_b": informative("errors"), "units_c": informative("correct")}


def verdict(row: dict) -> dict:
    points = (row["a"] is not None and row["a"] >= 0.5 and row["b"] is not None and row["b"] >= 0.8
              and row["c"] is not None and row["c"] <= 0.15)
    bounds = (row["a_lower"] is not None and row["a_lower"] >= 0.5 and row["b_lower"] is not None
              and row["b_lower"] >= 0.8 and row["c_upper"] is not None and row["c_upper"] <= 0.15)
    units = min(row["units_a"], row["units_b"], row["units_c"]) >= MIN_UNITS
    enough = min(row["flagged"], row["errors"], row["correct"]) >= MIN_COUNT
    return {"points": points, "bounds": bounds, "units": units, "enough": enough,
            "pass": points and bounds and units and enough}


def show(stratum: str, row: dict, judged: dict) -> None:
    f = lambda v: "-" if v is None else f"{v:.3f}"  # noqa: E731
    print(f"{stratum}: 行 {row['errors'] + row['correct']} 印 {row['flagged']} 誤り {row['errors']}"
          f"（検出できなかった正解の行 {row['missed']}（{(row['missed_share'] or 0):.1%}）、不利な側 {row['pessimistic']}、目で作った正解 {row['eye']}）")
    print(f"  (a) {f(row['a'])}（下限 {f(row['a_lower'])}） (b) {f(row['b'])}（下限 {f(row['b_lower'])}）"
          f" (c) {f(row['c'])}（上限 {f(row['c_upper'])}） 単位 {row['units_a']}/{row['units_b']}/{row['units_c']}"
          f" → {json.dumps(judged, ensure_ascii=False)}")


def main() -> None:
    mode = sys.argv[1]
    if mode not in ("tuning", "evaluation"):
        raise SystemExit(f"不明なモード: {mode}")
    target = RESULTS / f"v2-{mode}.json"
    if mode == "evaluation" and target.exists():
        raise SystemExit("確かめる資料は、もう測った（1 回だけ）")
    if mode == "evaluation":
        check = RESULTS / "compare-flags.json"
        if not check.exists() or not json.loads(check.read_bytes().decode("utf-8")).get("all_equal"):
            raise SystemExit("製品の印と試した印の照合（compare_flags.py）が通っていない。確かめる資料は測らない")
    data = collect(mode)
    result = {}
    for stratum, d in data.items():
        row = measure(d)
        judged = verdict(row)
        result[stratum] = {"row": row, "verdict": judged}
        show(stratum, row, judged)
    RESULTS.mkdir(exist_ok=True)
    target.write_bytes((json.dumps(result, ensure_ascii=False, indent=1) + "\n").encode("utf-8"))


if __name__ == "__main__":
    main()
