"""4 回目（開発の段階）: 公開の正解を領域の正解（corpus/public/region/）にして数え、今の正解からの変わり方を出す。

使い方（rag の依存の環境で動かす）: python -X utf8 scripts/score_v4.py
測り方は ../../adr-0025-condition5-v4-2026-11-17.md。合成は今までどおり（score_v2.collect）。公開は、決められる行は
領域の正解、決められない行は目で作った正解（前の回の正解と、4 回目に作った正解。箱と本文の SHA-256 を照らす）で数え、
目で作った正解のない行は、今までどおり不利な側に数える（仮の値。4 回目の目の正解がそろうまで）。
印は製品の印（corpus/ocr3/ の flags と確信度 0.3）。結果は results/v4-dev.json に書く（数だけ）。
"""

from __future__ import annotations

import hashlib
import json
import os
import sys
from collections import Counter
from pathlib import Path

os.environ.setdefault("SCORE_OCR_DIR", "ocr3")
HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))

import score_v2  # noqa: E402
from probe_analyze import eye_truth  # noqa: E402
from rag_ocr_flags import normalize  # noqa: E402
from score import CORPUS, RESULTS, load_truths  # noqa: E402


def load(path: Path):
    return json.loads(path.read_bytes().decode("utf-8"))


def region_eye(side: str) -> dict:
    """4 回目に目で作った正解（corpus/public/eyetruth/<side>-<版>/truth.json があれば）。"""
    found = {}
    for folder in sorted((CORPUS / "public" / "eyetruth").glob(f"{side}-region-v*")):
        if not (folder / "truth.json").exists():
            continue
        index = {x["file"]: x for x in load(folder / "index.json")}
        for name, text in load(folder / "truth.json").items():
            found[(index[name]["key"], index[name]["line_index"])] = {**index[name], "text": text}
    return found


def public_lines(side: str, reasons_for) -> tuple[list[dict], Counter]:
    eyes = {**eye_truth(side), **region_eye(side)}
    records, sources = [], Counter()
    for truth in load_truths():
        if truth["side"] != side or truth["stratum"] != "public":
            continue
        for page in truth["pages"]:
            key = f"{truth['name']}-p{page['page']:04d}"
            ocr = load(CORPUS / "ocr3" / f"{key}.json")
            region = load(CORPUS / "public" / "region" / f"{key}.json")
            if region["pdf_sha256"] != truth["pdf_sha256"] or ocr["pdf_sha256"] != truth["pdf_sha256"]:
                raise SystemExit(f"PDF が正解と違う: {key}")
            for r in region["lines"]:
                j = r["line_index"]
                line = ocr["lines"][j]
                if r["box"] != line["box"] or r["ocr_text_sha256"] != hashlib.sha256(line["text"].encode("utf-8")).hexdigest():
                    raise SystemExit(f"領域の正解が OCR の行と違う: {key} の {j}")
                text = normalize(line["text"])
                record = {"unit": key, "key": key, "line_index": j, "reasons": reasons_for(line, score_v2.THRESHOLD)}
                if "undecided" not in r:
                    record.update(rule="exact", error=normalize(r["text"]) != text, source="region")
                elif (key, j) in eyes:
                    eye = eyes[(key, j)]
                    if list(eye["box"]) != list(line["box"]) or eye["ocr_text_sha256"] != r["ocr_text_sha256"]:
                        raise SystemExit(f"目で作った正解の行が、OCR の行と違う: {key} の {j}")
                    record.update(rule="exact", error=normalize(eye["text"]) != text, source="eye", eye=True)
                else:
                    record.update(rule="pessimistic", source="unknown")
                sources[record["source"]] += 1
                records.append(record)
    return records, sources


def main() -> None:
    from rag_ocr_flags import reasons_for

    result = {}
    transitions = {}
    for side in ("tuning", "evaluation", "evaluation3"):
        old = score_v2.collect(side)
        new_public, sources = public_lines(side, reasons_for)
        # 今の正解からの変わり方（行ごと。印の有無で分ける）
        before = {(r["key"], r["line_index"]): r for r in old["public"]["lines"]}
        t = Counter()
        for r in new_public:
            o = before.get((r["key"], r["line_index"]))
            flag = "印あり" if r["reasons"] else "印なし"

            def state(x):
                if x is None:
                    return "対応なし"
                if x["rule"] != "exact":
                    return "不利な側"
                return "誤り" if x["error"] else "正しい"
            t[f"{flag}: {state(o)} → {state(r)}"] += 1
        transitions[side] = dict(sorted(t.items()))
        # 目で作った正解がまだない行に、前の正解の正誤を代わりに当てた値（目の正解がそろうまでの見込み。合否には使わない）
        proxy = []
        for r in new_public:
            o = before.get((r["key"], r["line_index"]))
            if r["source"] == "unknown" and o is not None and o["rule"] == "exact":
                r = {**r, "rule": "exact", "error": o["error"]}
            proxy.append(r)
        for stratum, data in (("synthetic", old["synthetic"]), ("public", {"lines": new_public, "missed": []}),
                              ("public-proxy", {"lines": proxy, "missed": []})):
            row = score_v2.measure(data)
            judged = score_v2.verdict(row)
            result[f"{side}-{stratum}"] = {"row": row, "verdict": judged,
                                           **({"sources": dict(sources)} if stratum == "public" else {})}
            print(f"{side} {stratum}", end=" ")
            score_v2.show(stratum, row, judged)
        print("  正解の出どころ:", dict(sources))
        for k, n in transitions[side].items():
            print("   ", k, n)
    RESULTS.mkdir(exist_ok=True)
    (RESULTS / "v4-dev.json").write_bytes((json.dumps({"scores": result, "transitions": transitions},
                                                      ensure_ascii=False, indent=1) + "\n").encode("utf-8"))


if __name__ == "__main__":
    main()
