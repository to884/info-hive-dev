"""別のプロセスで PDF の文字の層を取り出し、ページごとの本文の SHA-256 を JSON で書く（試験 7 の子プロセス）。

使い方: python pdf_text_hashes.py <wiki|rag> <PDF>...
"""

from __future__ import annotations

import hashlib
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]


def main() -> None:
    side, paths = sys.argv[1], sys.argv[2:]
    if side == "wiki":
        sys.path.insert(0, str(ROOT / "info-hive-wiki" / "skills" / "info-hive" / "scripts"))
        import wiki_pdf_layer as layer
    else:
        sys.path.insert(0, str(ROOT / "info-hive-rag" / "scripts"))
        import rag_pdf_layer as layer
    found = {}
    for path in paths:
        data = Path(path).read_bytes()
        found[Path(path).name] = [hashlib.sha256(text.encode("utf-8")).hexdigest()
                                  for _, text in layer.pdfminer_pages(data)]
    sys.stdout.write(json.dumps(found))


if __name__ == "__main__":
    main()
