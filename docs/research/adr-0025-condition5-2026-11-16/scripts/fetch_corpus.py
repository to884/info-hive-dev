"""条件 5 の公開の PDF を corpus/ にダウンロードする。

使い方: python -I scripts/fetch_corpus.py
URL と SHA-256 は sources.json から読む。SHA-256 が記録と違えば、書かずに止まる。
SHA-256 が記録されていない（null）PDF は、取得した値を sources.json に書く（最初の取得）。
"""

from __future__ import annotations

import hashlib
import json
import urllib.request
from pathlib import Path

BENCH = Path(__file__).resolve().parent.parent
SOURCES = BENCH / "sources.json"
CORPUS = BENCH / "corpus"


def main() -> None:
    recorded = json.loads(SOURCES.read_bytes().decode("utf-8"))
    changed = False
    for name, entry in recorded.items():
        target = CORPUS / name
        if target.exists() and hashlib.sha256(target.read_bytes()).hexdigest() == entry["sha256"]:
            print(name, "取得済み")
            continue
        request = urllib.request.Request(entry["url"], headers={"User-Agent": "Mozilla/5.0"})
        with urllib.request.urlopen(request, timeout=300) as response:
            data = response.read()
        digest = hashlib.sha256(data).hexdigest()
        if entry["sha256"] is None:
            entry["sha256"], entry["bytes"] = digest, len(data)
            changed = True
        elif digest != entry["sha256"]:
            raise SystemExit(f"{name}: SHA-256 が記録と違う（記録 {entry['sha256']}、取得 {digest}）。書かない")
        target.write_bytes(data)
        print(name, len(data), "bytes")
    if changed:
        SOURCES.write_bytes((json.dumps(recorded, ensure_ascii=False, indent=2) + "\n").encode("utf-8"))


if __name__ == "__main__":
    main()
