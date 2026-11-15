"""Sol の判定（judge/sol-result.md、judge/mapping.json）を、方式ごとの表にまとめる。summary.md と summary.json を書く。
--set 2 では、judge2/ を集計して summary2.md と summary2.json を書く。

使い方: python -I aggregate.py
集計の前に、判定の judge_digest、manifest.json、写し、対応表が一致することを確かめ、違えば止まる。
"""

from __future__ import annotations

import json
import re
import statistics
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from prepare_judge import SELECTED, digest_of, page_text, sha256  # noqa: E402

BENCH = Path(__file__).resolve().parent.parent
from prepare_judge import JUDGE_DIR, METHODS, SET  # noqa: E402  --set 2 で 2 回目の組を集計する

JUDGE = BENCH / JUDGE_DIR
SUFFIX = "" if SET == "1" else SET
AXES = ["coverage", "order", "table", "legibility", "usability"]
LABEL = {"wikipdf": "wiki_pdf（試作）", "poppler": "Poppler 26.09.0", "xpdf": "Xpdf 4.00", "pdfminer": "pdfminer",
         "pdfminer-vertical": "pdfminer（縦書きの検出）", "docling": "Docling", "ndlocr": "NDLOCR-Lite",
         "pdfoxide": "pdf_oxide", "pdfplumber": "pdfplumber"}


def check(sol: dict, mapping_bytes: bytes) -> dict:
    manifest = json.loads((JUDGE / "manifest.json").read_text(encoding="utf-8"))
    problems = []
    if sol.get("judge_digest") != manifest["digest"]:
        problems.append("judge_digest が manifest.json の digest と違う")
    if digest_of(manifest["files"], manifest["mapping_sha256"]) != manifest["digest"]:
        problems.append("manifest.json の digest が、書かれた SHA-256 と合わない")
    if sha256(mapping_bytes) != manifest["mapping_sha256"]:
        problems.append("judge/mapping.json が、写したときの対応表と違う")
    mapping = json.loads(mapping_bytes.decode("utf-8"))
    for stem, page in SELECTED:
        key = f"{stem}-p{page}"
        for letter, method in mapping[key].items():
            want = manifest["files"][f"{key}/{letter}.txt"]
            if sha256((JUDGE / key / f"{letter}.txt").read_bytes()) != want:
                problems.append(f"{key}/{letter}.txt: 写しが判定のときと違う")
            if sha256(page_text(stem, method, page).encode("utf-8")) != want:
                problems.append(f"{key} {method}: 出力が判定のときと違う")
    if problems:
        raise SystemExit("判定と出力が合わない:\n" + "\n".join(problems))
    return mapping


def main() -> None:
    sol = json.loads(re.search(r"```json\n(.*?)\n```", (JUDGE / "sol-result.md").read_text(encoding="utf-8"), re.S).group(1))
    mapping = check(sol, (JUDGE / "mapping.json").read_bytes())
    rows = []
    for stem, page in SELECTED:
        key = f"{stem}-p{page}"
        for letter, method in mapping[key].items():
            score = sol[key][letter]
            rows.append({"page": key, "method": method, **{a: score.get(a) for a in AXES},
                         "fatal": len(score.get("fatal", []))})
    (BENCH / f"summary{SUFFIX}.json").write_bytes(json.dumps(rows, ensure_ascii=False, indent=2).encode("utf-8"))

    def cell(v) -> str:
        return "－" if v is None else str(v)

    lines = ["## ページごと（Sol の点。網羅、読み順、表、文字の正しさ、総合、致命的）", "",
             "| ページ | " + " | ".join(LABEL[m] for m in METHODS) + " |", "| --- |" + " --- |" * len(METHODS)]
    for stem, page in SELECTED:
        key = f"{stem}-p{page}"
        by = {r["method"]: r for r in rows if r["page"] == key}
        lines.append(f"| {key} | " + " | ".join(
            "、".join(cell(by[m][a]) for a in AXES) + f"（{by[m]['fatal']}）" for m in METHODS) + " |")
    lines += ["", "## 方式ごとの平均（null を除く）", "", "| 方式 | " + " | ".join(AXES) + " | 致命的の合計 |",
              "| --- |" + " --: |" * (len(AXES) + 1)]
    for m in METHODS:
        mine = [r for r in rows if r["method"] == m]
        avg = [statistics.mean([r[a] for r in mine if r[a] is not None]) for a in AXES]
        lines.append(f"| {LABEL[m]} | " + " | ".join(f"{v:.2f}" for v in avg) + f" | {sum(r['fatal'] for r in mine)} |")
    (BENCH / f"summary{SUFFIX}.md").write_bytes(("\n".join(lines) + "\n").encode("utf-8"))
    print("\n".join(lines))


if __name__ == "__main__":
    main()
