"""検証の試料（公開の PDF）を corpus/ にダウンロードし、SHA-256 を sources.json に書く。

使い方: python -I fetch_corpus.py
PDF はリポジトリに入れない（corpus/.gitignore）。sources.json の URL と SHA-256 で、同じものを取り直せる。
"""

from __future__ import annotations

import hashlib
import json
import urllib.request
from pathlib import Path

BENCH = Path(__file__).resolve().parent.parent
CORPUS = BENCH / "corpus"
KANPO = "https://www.kanpo.go.jp/20261113/20261113h01828/pdf/20261113h0182800{:02d}.pdf"
SOURCES = {
    "bert.pdf": ("https://arxiv.org/pdf/1810.04805v2",
                 "arXiv 1810.04805v2（BERT）。LaTeX、2 段組み、英語、表あり"),
    "whitepaper-point.pdf": ("https://www.soumu.go.jp/johotsusintokei/whitepaper/ja/r07/pdf/01point.pdf",
                             "総務省 令和7年版 情報通信白書「ポイント」。組版のソフト、日本語"),
    "whitepaper-summary.pdf": ("https://www.soumu.go.jp/main_content/001019264.pdf",
                               "総務省 令和7年版 情報通信白書 概要。日本語、図と表が多い"),
    **{f"kanpo-p{n}.pdf": (KANPO.format(n), f"官報 令和8年11月13日 本紙第1828号 {n} ページ目。縦書き、段組み")
       for n in range(1, 5)},
}


def main() -> None:
    CORPUS.mkdir(parents=True, exist_ok=True)
    (CORPUS / ".gitignore").write_bytes(b"*.pdf\n*.png\n")
    found = {}
    for name, (url, note) in SOURCES.items():
        request = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
        with urllib.request.urlopen(request, timeout=60) as response:
            data = response.read()
        if not data.startswith(b"%PDF-"):
            raise SystemExit(f"{name}: PDF ではない応答が返った")
        (CORPUS / name).write_bytes(data)
        found[name] = {"url": url, "note": note, "bytes": len(data), "sha256": hashlib.sha256(data).hexdigest()}
        print(f"{name}: {len(data)} bytes")
    (BENCH / "sources.json").write_bytes(json.dumps(found, ensure_ascii=False, indent=2).encode("utf-8"))


if __name__ == "__main__":
    main()
