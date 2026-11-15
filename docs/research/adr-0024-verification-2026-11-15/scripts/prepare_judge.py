"""Sol の判定のために、選んだページの出力を方式の名前を伏せて judge/<ページ>/<記号>.txt に写し、ページの画像を添える。

使い方: python -I prepare_judge.py <対応表の書き出し先> [--discard-judgement] [--set 2]

- 判定の組は 2 つある。1 は ADR-0024 の承認の条件の検証（judge/、4 方式）。2 は書き直しの案の比較
  （judge2/、6 方式。pdfminer の縦書きの検出、Docling、NDLOCR-Lite を足した）。--set 2 で 2 を選ぶ。

- 対応表（記号と方式の対応）は、判定が終わるまで judge/ の外に置く。判定のあとで judge/mapping.json に写す。
- judge/manifest.json に、写したファイルごとの SHA-256、対応表の SHA-256、それらのダイジェストを書く。
  Sol には、読んだダイジェストを判定の JSON の judge_digest に書かせる。
- 前の判定（judge/sol-result.md）か対応表が残っているときは止まる。--discard-judgement で消してから写す。
"""

from __future__ import annotations

import hashlib
import json
import random
import re
import shutil
import sys
from pathlib import Path

BENCH = Path(__file__).resolve().parent.parent
SETS = {
    "1": ("judge", ["wikipdf", "poppler", "xpdf", "pdfminer"]),
    "2": ("judge2", ["wikipdf", "xpdf", "pdfminer", "pdfminer-vertical", "docling", "ndlocr"]),
    # 3 は、調査で挙がった pdf_oxide と pdfplumber を、2 の上位の方式と比べる
    "3": ("judge3", ["wikipdf", "pdfminer-vertical", "docling", "pdfoxide", "pdfplumber"]),
}
SET = sys.argv[sys.argv.index("--set") + 1] if "--set" in sys.argv else "1"
JUDGE_DIR, METHODS = SETS[SET]
LETTERS = "ABCDEF"
# 判定するページ: 2 段組み、表、日本語の組版、図と表の多いスライド、縦書き
SELECTED = [("bert", 1), ("bert", 6), ("bert", 7), ("whitepaper-point", 1), ("whitepaper-summary", 2),
            ("whitepaper-summary", 4), ("whitepaper-summary", 7), ("whitepaper-summary", 11),
            ("kanpo-p1", 1), ("kanpo-p2", 1)]


def sha256(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def digest_of(files: dict[str, str], mapping_sha256: str) -> str:
    canonical = json.dumps({"files": dict(sorted(files.items())), "mapping_sha256": mapping_sha256},
                           ensure_ascii=False, sort_keys=True)
    return sha256(canonical.encode("utf-8"))


def page_text(stem: str, method: str, page: int) -> str:
    text = (BENCH / "outputs" / f"{stem}__{method}.txt").read_bytes().decode("utf-8")
    if method == "wikipdf":
        parts = re.split(r"(?m)^## p\. (\d+)\n\n", text)
        pages = {int(parts[i]): parts[i + 1] for i in range(1, len(parts), 2)}
        return pages[page].rstrip("\n")
    return text.split(chr(12))[page - 1]


def main() -> None:
    judge = BENCH / JUDGE_DIR
    old = sorted(judge.glob("sol-result.md*")) + sorted(judge.glob("mapping.json"))
    if old:
        if "--discard-judgement" not in sys.argv[2:]:
            sys.exit("前の判定が残っている: " + ", ".join(p.name for p in old) + "。やり直すときは --discard-judgement を付ける")
        for path in old:
            path.unlink()
    judge.mkdir(exist_ok=True)
    for child in judge.iterdir():
        if child.is_dir():
            shutil.rmtree(child)
    rng = random.Random(20261115)
    mapping: dict[str, dict[str, str]] = {}
    files: dict[str, str] = {}
    for stem, page in SELECTED:
        key = f"{stem}-p{page}"
        folder = judge / key
        folder.mkdir()
        shutil.copyfile(BENCH / "pages" / f"{stem}-p{page}.png", folder / "page.png")
        methods = METHODS[:]
        rng.shuffle(methods)
        mapping[key] = {}
        for letter, method in zip(LETTERS, methods):
            data = page_text(stem, method, page).encode("utf-8")
            (folder / f"{letter}.txt").write_bytes(data)
            mapping[key][letter] = method
            files[f"{key}/{letter}.txt"] = sha256(data)
    mapping_bytes = json.dumps(mapping, ensure_ascii=False, indent=2).encode("utf-8")
    Path(sys.argv[1]).write_bytes(mapping_bytes)
    manifest = {"digest": digest_of(files, sha256(mapping_bytes)), "mapping_sha256": sha256(mapping_bytes), "files": files}
    (judge / "manifest.json").write_bytes(json.dumps(manifest, ensure_ascii=False, indent=2).encode("utf-8"))
    print("digest", manifest["digest"])


if __name__ == "__main__":
    main()
