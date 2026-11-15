"""承認の条件 1 の測定に使う長い公開の PDF を corpus/ にダウンロードし、URL と SHA-256 を sources.json に書く。

使い方: python -I fetch_corpus.py
PDF はリポジトリに入れない（corpus/.gitignore）。作者の承認を得てダウンロードした（2026-11-15）。
"""

from __future__ import annotations

import hashlib
import json
import urllib.request
from pathlib import Path

BENCH = Path(__file__).resolve().parent.parent
SOURCES = {
    "defense-white-paper-2025.pdf": (
        "https://www.mod.go.jp/j/press/wp/wp2025/pdf/R07zenpen.pdf",
        "防衛省 令和7年版 防衛白書 全編（546 ページ）"),
}


def main() -> None:
    corpus = BENCH / "corpus"
    corpus.mkdir(exist_ok=True)
    found = {}
    for name, (url, note) in SOURCES.items():
        request = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
        with urllib.request.urlopen(request, timeout=300) as response:
            data = response.read()
        if not data.startswith(b"%PDF-"):
            raise SystemExit(f"{name}: PDF ではない応答が返った")
        (corpus / name).write_bytes(data)
        found[name] = {"url": url, "note": note, "bytes": len(data), "sha256": hashlib.sha256(data).hexdigest()}
        print(name, len(data), "bytes")
    (BENCH / "sources.json").write_bytes(json.dumps(found, ensure_ascii=False, indent=2).encode("utf-8"))


if __name__ == "__main__":
    main()
