"""ADR-0024 の検証で Sol が判定した 10 ページの PDF を、corpus/judged/ にダウンロードする。

使い方: python -I fetch_judged.py
URL と SHA-256 は、ADR-0024 の検証の sources.json から読む。SHA-256 が記録と違えば、判定した試料と
違うので、書かずに止まる。PDF はリポジトリに入れない（.gitignore）。作者の承認を得てダウンロードした（2026-11-16）。
"""

from __future__ import annotations

import hashlib
import json
import urllib.request
from pathlib import Path

BENCH = Path(__file__).resolve().parent.parent
SOURCES = BENCH.parent / "adr-0024-verification-2026-11-15" / "sources.json"
# 判定した 10 ページを含む PDF だけを取る（官報の 3、4 ページ目は判定していない）
NAMES = ["bert.pdf", "whitepaper-point.pdf", "whitepaper-summary.pdf", "kanpo-p1.pdf", "kanpo-p2.pdf"]


def main() -> None:
    recorded = json.loads(SOURCES.read_bytes().decode("utf-8"))
    corpus = BENCH / "corpus" / "judged"
    corpus.mkdir(parents=True, exist_ok=True)
    for name in NAMES:
        entry = recorded[name]
        request = urllib.request.Request(entry["url"], headers={"User-Agent": "Mozilla/5.0"})
        with urllib.request.urlopen(request, timeout=120) as response:
            data = response.read()
        digest = hashlib.sha256(data).hexdigest()
        if digest != entry["sha256"]:
            raise SystemExit(f"{name}: SHA-256 が記録と違う（記録 {entry['sha256']}、取得 {digest}）。判定した試料ではないので、書かない")
        (corpus / name).write_bytes(data)
        print(name, len(data), "bytes", "SHA-256 一致")


if __name__ == "__main__":
    main()
