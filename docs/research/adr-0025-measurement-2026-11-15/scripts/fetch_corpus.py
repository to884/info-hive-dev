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
    record = BENCH / "sources.json"
    # 記録した SHA-256 があれば、取り直した PDF がそれと同じかを確かめる。配布元が差し替えていたら、
    # 結果の JSON と違う試料になるので、上書きせずに止まる。
    recorded = json.loads(record.read_bytes().decode("utf-8")) if record.exists() else {}
    found = {}
    for name, (url, note) in SOURCES.items():
        request = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
        with urllib.request.urlopen(request, timeout=300) as response:
            data = response.read()
        if not data.startswith(b"%PDF-"):
            raise SystemExit(f"{name}: PDF ではない応答が返った")
        digest = hashlib.sha256(data).hexdigest()
        if name in recorded and recorded[name]["sha256"] != digest:
            raise SystemExit(f"{name}: SHA-256 が記録と違う（記録 {recorded[name]['sha256']}、取得 {digest}）。"
                             "配布元が差し替えた可能性がある。結果は記録した試料のものなので、上書きしない")
        (corpus / name).write_bytes(data)
        found[name] = {"url": url, "note": note, "bytes": len(data), "sha256": digest}
        print(name, len(data), "bytes")
    record.write_bytes(json.dumps(found, ensure_ascii=False, indent=2).encode("utf-8"))


if __name__ == "__main__":
    main()
