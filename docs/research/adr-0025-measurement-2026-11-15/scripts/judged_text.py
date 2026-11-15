# /// script
# requires-python = ">=3.12,<3.13"
# dependencies = ["pdfminer.six==20260107"]
# ///
"""Sol が判定した 10 ページで、直す前と直した pdfminer の本文を取り出し、判定に渡した本文と比べる。

使い方: uv run --script judged_text.py <plain|stable> <結果の名前に付ける接尾辞>
- plain: 直さない pdfminer。判定に渡した本文と同じ作り方（文書全体を extract_text で取り出し、改ページの文字で分ける）
- stable: stable_text.py の直しを入れた pdfminer。同じ作り方に加え、製品の方法（文書を 1 回だけ読み、
  ページごとに受け取る）の本文も取る
判定に渡した本文の SHA-256 は、ADR-0024 の検証の judge2/ と judge3/ の manifest.json にある。
結果（SHA-256 と一致したか）を results/judged-<plain|stable><接尾辞>.json に書く。
本文は corpus/judged/out-<plain|stable><接尾辞>/ に書き、リポジトリには入れない（.gitignore）。
"""

from __future__ import annotations

import hashlib
import json
import sys
from pathlib import Path

BENCH = Path(__file__).resolve().parent.parent
VERIFY = BENCH.parent / "adr-0024-verification-2026-11-15"
# 判定した 10 ページ（ADR-0024 の検証の prepare_judge.py の SELECTED と同じ）
SELECTED = [("bert", 1), ("bert", 6), ("bert", 7), ("whitepaper-point", 1), ("whitepaper-summary", 2),
            ("whitepaper-summary", 4), ("whitepaper-summary", 7), ("whitepaper-summary", 11),
            ("kanpo-p1", 1), ("kanpo-p2", 1)]


def judged_sha() -> dict[str, dict[str, str]]:
    """判定に渡した pdfminer（縦書きの検出あり）の本文の SHA-256 を、判定の組ごとに読む。"""
    found: dict[str, dict[str, str]] = {}
    for judge in ("judge2", "judge3"):
        mapping = json.loads((VERIFY / judge / "mapping.json").read_bytes().decode("utf-8"))
        manifest = json.loads((VERIFY / judge / "manifest.json").read_bytes().decode("utf-8"))
        for key, letters in mapping.items():
            for letter, method in letters.items():
                if method == "pdfminer-vertical":
                    found.setdefault(key, {})[judge] = manifest["files"][f"{key}/{letter}.txt"]
    return found


def whole_pages(path: Path) -> list[str]:
    from pdfminer.high_level import extract_text
    from pdfminer.layout import LAParams
    return extract_text(str(path), laparams=LAParams(detect_vertical=True)).split(chr(12))


def pass_pages(path: Path) -> list[str]:
    import stable_text  # 同じディレクトリにある
    return stable_text.pass_pages(path)


def main() -> None:
    mode, suffix = sys.argv[1], sys.argv[2]
    if mode not in ("plain", "stable"):
        raise SystemExit("plain か stable を指定する")
    if mode == "stable":
        import pdfminer.layout as layout
        import stable_text
        layout.LTLayoutContainer.group_textboxes = stable_text._stable_group
    expected = judged_sha()
    out_dir = BENCH / "corpus" / "judged" / f"out-{mode}{suffix}"
    out_dir.mkdir(parents=True, exist_ok=True)
    cache: dict[str, tuple[list[str], list[str] | None]] = {}
    rows = []
    for stem, page in SELECTED:
        if stem not in cache:
            path = BENCH / "corpus" / "judged" / f"{stem}.pdf"
            cache[stem] = (whole_pages(path), pass_pages(path) if mode == "stable" else None)
        whole, passed = cache[stem]
        key = f"{stem}-p{page}"
        text = whole[page - 1]
        (out_dir / f"{key}.txt").write_bytes(text.encode("utf-8"))
        sha = hashlib.sha256(text.encode("utf-8")).hexdigest()
        row = {"page": key, "sha256": sha,
               "same_as_judge2": sha == expected[key].get("judge2"),
               "same_as_judge3": sha == expected[key].get("judge3")}
        if passed is not None:
            row["pass_same_as_whole"] = passed[page - 1] == text
        rows.append(row)
    result = {"mode": mode, "pages": rows,
              "judge2_and_judge3_same_text": sum(1 for k in expected.values() if k.get("judge2") == k.get("judge3"))}
    out = BENCH / "results" / f"judged-{mode}{suffix}.json"
    out.write_bytes(json.dumps(result, ensure_ascii=False, indent=1).encode("utf-8"))
    print(mode, suffix, "判定と同じ:", sum(r["same_as_judge3"] for r in rows), "/", len(rows))


if __name__ == "__main__":
    main()
