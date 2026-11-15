"""results.json と Sol の判定（judge/sol-result.md、judge/mapping.json）を、1 つの表にまとめる。

使い方: python aggregate.py   summary.md と summary.json を書く

集計の前に、判定がいまの出力を採点したものかを確かめ、違えば止まる（prepare_judge.py の説明を参照）。
"""

from __future__ import annotations

import json
import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from prepare_judge import digest_of, sha256  # noqa: E402

BENCH = Path(__file__).resolve().parent.parent
JUDGE = BENCH / "judge"
AXES = ["coverage", "order", "structure", "noise", "location", "usability"]
LABEL = {"pdftotext": "pdftotext", "pdfminer": "pdfminer", "rag": "rag（PDFium）", "wikifetch": "wiki_fetch",
         "text": "そのまま読む", "markitdown": "MarkItDown"}


def _check_judged(results: list[dict], mapping_bytes: bytes, sol: dict) -> None:
    """判定（judge_digest）、写しの一覧（manifest.json）、写し、出力、対応表が、すべて同じものを指しているかを
    確かめる。1 つでも食い違えば止まる。"""
    manifest = json.loads((JUDGE / "manifest.json").read_text(encoding="utf-8"))
    problems = []
    if sol.get("judge_digest") != manifest["digest"]:
        problems.append(f"判定の judge_digest（{sol.get('judge_digest')}）が manifest.json の digest と違う")
    if digest_of(manifest["files"], manifest["mapping_sha256"]) != manifest["digest"]:
        problems.append("manifest.json の digest が、書かれた SHA-256 から計算した値と違う")
    if sha256(mapping_bytes) != manifest["mapping_sha256"]:
        problems.append("judge/mapping.json が、写したときの対応表と違う")
    mapping = json.loads(mapping_bytes.decode("utf-8"))
    for record in results:
        letters = {method: letter for letter, method in mapping.get(record["file"], {}).items()}
        if record["method"] not in letters:
            problems.append(f"{record['file']} {record['method']}: 判定がない")
            continue
        name = f"{record['file'].replace('.', '_')}/{letters[record['method']]}.md"
        want = manifest["files"].get(name)
        judged = JUDGE / name
        if want is None or not judged.exists() or sha256(judged.read_bytes()) != want:
            problems.append(f"{name}: 写しが、判定のときの写しと違う")
        if sha256((BENCH / record["output"]).read_bytes()) != want:
            problems.append(f"{record['file']} {record['method']}: 出力が、判定のときの写しと違う")
    if problems:
        raise SystemExit("判定と出力が合わない。prepare_judge.py --discard-judgement で写し直し、Sol の判定を"
                         "やり直す:\n" + "\n".join(problems))


def main() -> None:
    results = [r for r in json.loads((BENCH / "results.json").read_text(encoding="utf-8"))["results"] if "output" in r]
    mapping_bytes = (JUDGE / "mapping.json").read_bytes()
    sol_text = (JUDGE / "sol-result.md").read_text(encoding="utf-8")
    sol = json.loads(re.search(r"```json\n(.*?)\n```", sol_text, re.S).group(1))
    _check_judged(results, mapping_bytes, sol)
    mapping = json.loads(mapping_bytes.decode("utf-8"))
    rows = []
    for record in results:
        letters = {method: letter for letter, method in mapping[record["file"]].items()}
        score = sol[record["file"].replace(".", "_")][letters[record["method"]]]
        rows.append({**{k: record.get(k) for k in ["file", "method", "recall", "in_order", "rows_on_line",
                                                   "rows_aligned", "location_markers", "warm_s", "cold_s"]},
                     "sol": {axis: score.get(axis) for axis in AXES}, "fatal": len(score.get("fatal", []))})
    (BENCH / "summary.json").write_bytes(json.dumps(rows, ensure_ascii=False, indent=2).encode("utf-8"))

    def cell(value) -> str:
        return "－" if value is None else str(value)

    def marks(found: dict) -> str:
        names = {"form_feed": "改ページ", "page_heading": "p. N", "slide_comment": "スライド",
                 "sheet_heading": "シート", "file_heading": "ファイル"}
        return "、".join(f"{names[k]} {v}" for k, v in found.items() if v) or "なし"

    lines = ["| 試料 | 方式 | 網羅率 | 順に読めた割合 | 1 行に残った表の行 | 列のそろった表の行 | 位置の目印 | 変換（秒） | 起動込み（秒） | Sol 網羅 | 読み順 | 構造 | 雑音 | 位置 | 総合 | 致命的 |",
             "| --- | --- | --: | --: | --: | --: | --- | --: | --: | --: | --: | --: | --: | --: | --: | --: |"]
    for r in rows:
        s = r["sol"]
        lines.append(f"| {r['file']} | {LABEL[r['method']]} | {r['recall']} | {r['in_order']} | {r['rows_on_line']} | "
                     f"{r['rows_aligned']} | {marks(r['location_markers'])} | {r['warm_s']} | {r['cold_s']} | "
                     + " | ".join(cell(s[a]) for a in AXES) + f" | {r['fatal']} |")
    (BENCH / "summary.md").write_bytes(("\n".join(lines) + "\n").encode("utf-8"))
    print("\n".join(lines))


if __name__ == "__main__":
    main()
