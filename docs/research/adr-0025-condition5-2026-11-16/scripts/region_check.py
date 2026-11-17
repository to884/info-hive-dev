"""4 回目: 領域の正解（corpus/public/region/）の欠陥を、目の作業を増やさずに数える（数える前の確かめ）。

使い方（rag の依存の環境で動かす）: python -X utf8 scripts/region_check.py
公開の開発用の資料（tuning、evaluation、evaluation3）で、次を数える。印は見ない。
1. 決められる行で、領域の正解と、前の回に目で作った正解が食い違う行。
2. 今の作り方（score.page_records）で 1 対 1 に対応して正しかった行のうち、領域の正解で誤りになる行（決まりの欠陥の候補）。
   決められない行に変わった行は、欠陥ではなく手間として別に数える。
3. 今の作り方で 1 対 1 に対応して誤りだった行のうち、領域の正解で正しくなる行（文字の層にない字を見落としていないかを、
   目で確かめる対象）。一覧を corpus/public/region-check.json に書く（本文を含むので corpus/ の外に置かない）。
数だけを results/region-check.json に書く。
"""

from __future__ import annotations

import json
import sys
from collections import Counter
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
sys.path.insert(0, str(HERE.parents[3] / "info-hive-rag" / "scripts"))

import rag_ocr_flags  # noqa: E402
import score  # noqa: E402

score.SAME = rag_ocr_flags.SAME
score.reading_order = rag_ocr_flags.reading_order
score.joined = rag_ocr_flags.joined

from probe_analyze import eye_truth  # noqa: E402
from rag_ocr_flags import normalize  # noqa: E402
from score import CORPUS, RESULTS, load_truths, page_records  # noqa: E402


def load(path: Path):
    return json.loads(path.read_bytes().decode("utf-8"))


def main() -> None:
    counts: dict[str, Counter] = {}
    listing = {"eye_disagree": [], "old_correct_now_wrong": [], "old_wrong_now_correct": []}
    for side in ("tuning", "evaluation", "evaluation3"):
        c = counts.setdefault(side, Counter())
        eyes = eye_truth(side)
        for truth in load_truths():
            if truth["side"] != side or truth["stratum"] != "public":
                continue
            for page in truth["pages"]:
                key = f"{truth['name']}-p{page['page']:04d}"
                ocr = load(CORPUS / "ocr3" / f"{key}.json")["lines"]
                region = {r["line_index"]: r for r in load(CORPUS / "public" / "region" / f"{key}.json")["lines"]}
                lines = [{**x, "box": rag_ocr_flags.corners(x["box"])} for x in ocr]
                records, _ = page_records(page["lines"], lines, "public")
                old = {r["line_index"]: r for r in records}
                for j, line in enumerate(ocr):
                    r = region[j]
                    text = normalize(line["text"])
                    decided = "undecided" not in r
                    c["decided" if decided else "undecided"] += 1
                    eye = eyes.get((key, j))
                    if decided and eye is not None:
                        c["eye_compared"] += 1
                        if normalize(eye["text"]) != normalize(r["text"]):
                            c["eye_disagree"] += 1
                            listing["eye_disagree"].append({"key": key, "line_index": j, "region": r["text"],
                                                            "eye": eye["text"], "ocr": line["text"]})
                    o = old.get(j)
                    if not o or o["rule"] != "exact" or o["shape"] != "1:1":
                        continue
                    if not o["error"]:
                        c["old_correct"] += 1
                        if not decided:
                            c["old_correct_now_undecided"] += 1
                        elif normalize(r["text"]) != text:
                            c["old_correct_now_wrong"] += 1
                            listing["old_correct_now_wrong"].append({"key": key, "line_index": j, "region": r["text"],
                                                                     "old": o["truth_text"], "ocr": line["text"]})
                    else:
                        c["old_wrong"] += 1
                        if not decided:
                            c["old_wrong_now_undecided"] += 1
                        elif normalize(r["text"]) == text:
                            c["old_wrong_now_correct"] += 1
                            listing["old_wrong_now_correct"].append({"key": key, "line_index": j, "region": r["text"],
                                                                     "old": o["truth_text"], "ocr": line["text"],
                                                                     "box": line["box"]})
    for side, c in counts.items():
        print(side, json.dumps(dict(c), ensure_ascii=False))
    (CORPUS / "public" / "region-check.json").write_bytes(json.dumps(listing, ensure_ascii=False, indent=1).encode("utf-8"))
    RESULTS.mkdir(exist_ok=True)
    (RESULTS / "region-check.json").write_bytes(
        (json.dumps({s: dict(c) for s, c in counts.items()}, ensure_ascii=False, indent=1) + "\n").encode("utf-8"))


if __name__ == "__main__":
    main()
