"""確かめる資料を数える前に、git に入れない入力（corpus/）の SHA-256 の一覧を results/ に書く（測り方を固めた証拠）。

使い方: python -X utf8 scripts/freeze_manifest.py [evaluation3]
対象: 確かめる資料の正解（*.truth.json の side が evaluation か evaluation3）、目で作った正解（eyetruth/<side> の index.json、
truth.json、leader-only.json）、目での確かめ（eyecheck.json）、確かめる資料の OCR の結果（2 回目は ocr2/、3 回目は ocr3/）。
3 回目は results/v3-evaluation3-inputs.json に書く。数えた結果（v3-evaluation3.json）があれば書かない。
"""

from __future__ import annotations

import hashlib
import json
import sys
from pathlib import Path

BENCH = Path(__file__).resolve().parent.parent
CORPUS = BENCH / "corpus"


def digest(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main() -> None:
    side = sys.argv[1] if len(sys.argv) > 1 else "evaluation"
    if side not in ("evaluation", "evaluation3"):
        raise SystemExit(f"不明な資料: {side}")
    ocr_dir, tag = ("ocr3", "v3") if side == "evaluation3" else ("ocr2", "v2")
    if (BENCH / "results" / f"{tag}-{side}.json").exists():
        raise SystemExit("もう数えた資料の一覧は書き直さない")
    files = {}
    for path in sorted(CORPUS.glob("*/*.truth.json")):
        truth = json.loads(path.read_bytes().decode("utf-8"))
        if truth["side"] != side:
            continue
        files[path.relative_to(CORPUS).as_posix()] = digest(path)
        for page in truth["pages"]:
            ocr = CORPUS / ocr_dir / f"{truth['name']}-p{page['page']:04d}.json"
            files[ocr.relative_to(CORPUS).as_posix()] = digest(ocr)
    for name in ("index.json", "truth.json", "leader-only.json"):
        path = CORPUS / "public" / "eyetruth" / side / name
        files[path.relative_to(CORPUS).as_posix()] = digest(path)
    files["public/eyecheck.json"] = digest(CORPUS / "public" / "eyecheck.json")
    out = BENCH / "results" / f"{tag}-{side}-inputs.json"
    out.write_bytes((json.dumps(files, ensure_ascii=False, indent=1) + "\n").encode("utf-8"))
    print(len(files), "ファイル")


if __name__ == "__main__":
    main()
