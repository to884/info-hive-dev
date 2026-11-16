"""確かめる資料を数える前に、git に入れない入力（corpus/）の SHA-256 の一覧を results/ に書く（測り方を固めた証拠）。

使い方: python -X utf8 scripts/freeze_manifest.py
対象: 確かめる資料の正解（*.truth.json の side が evaluation）、目で作った正解（eyetruth/evaluation の index.json、
truth.json、leader-only.json）、目での確かめ（eyecheck.json）、確かめる資料の OCR の結果（ocr2/）。
"""

from __future__ import annotations

import hashlib
import json
from pathlib import Path

BENCH = Path(__file__).resolve().parent.parent
CORPUS = BENCH / "corpus"


def digest(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main() -> None:
    files = {}
    for path in sorted(CORPUS.glob("*/*.truth.json")):
        truth = json.loads(path.read_bytes().decode("utf-8"))
        if truth["side"] != "evaluation":
            continue
        files[path.relative_to(CORPUS).as_posix()] = digest(path)
        for page in truth["pages"]:
            ocr = CORPUS / "ocr2" / f"{truth['name']}-p{page['page']:04d}.json"
            files[ocr.relative_to(CORPUS).as_posix()] = digest(ocr)
    for name in ("index.json", "truth.json", "leader-only.json"):
        path = CORPUS / "public" / "eyetruth" / "evaluation" / name
        files[path.relative_to(CORPUS).as_posix()] = digest(path)
    files["public/eyecheck.json"] = digest(CORPUS / "public" / "eyecheck.json")
    out = BENCH / "results" / "v2-evaluation-inputs.json"
    out.write_bytes((json.dumps(files, ensure_ascii=False, indent=1) + "\n").encode("utf-8"))
    print(len(files), "ファイル")


if __name__ == "__main__":
    main()
