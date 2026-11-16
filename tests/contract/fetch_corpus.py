"""契約の試験（ADR-0025）の公開の PDF を、tests/contract/corpus/ にダウンロードする。

使い方: python -I tests/contract/fetch_corpus.py
試料は、ADR-0024 の検証で使った 7 つの PDF である。URL と SHA-256 は
docs/research/adr-0024-verification-2026-11-15/sources.json から読み、SHA-256 が記録と違えば書かずに止まる。
PDF はリポジトリに入れない（tests/contract/.gitignore）。ネットにつながるので、CI では動かさない。
corpus/ がないときは、公開の PDF を使う試験を飛ばす。
"""

from __future__ import annotations

import hashlib
import json
import urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
SOURCES = ROOT / "docs" / "research" / "adr-0024-verification-2026-11-15" / "sources.json"
CORPUS = Path(__file__).resolve().parent / "corpus"


def main() -> None:
    recorded = json.loads(SOURCES.read_bytes().decode("utf-8"))
    CORPUS.mkdir(exist_ok=True)
    for name, entry in recorded.items():
        target = CORPUS / name
        if target.exists() and hashlib.sha256(target.read_bytes()).hexdigest() == entry["sha256"]:
            print(name, "取得済み")
            continue
        request = urllib.request.Request(entry["url"], headers={"User-Agent": "Mozilla/5.0"})
        with urllib.request.urlopen(request, timeout=120) as response:
            data = response.read()
        digest = hashlib.sha256(data).hexdigest()
        if digest != entry["sha256"]:
            raise SystemExit(f"{name}: SHA-256 が記録と違う（記録 {entry['sha256']}、取得 {digest}）。書かない")
        target.write_bytes(data)
        print(name, len(data), "bytes")


if __name__ == "__main__":
    main()
