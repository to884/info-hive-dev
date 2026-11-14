# -*- coding: utf-8 -*-
"""ブラウザで取った HTML を、wiki_fetch.py の変換にそのまま通して raw を作る。

使い方: python fetch_from_dom.py <wiki_fetch.py のあるフォルダー> <HTML のパス> <URL> --raw-root <RAW_ROOT> --slug <スラッグ> --json

ページの URL の取得だけを保存した HTML に差し替え、画像は通常どおり取得する。
保存したあと、frontmatter の source_sha256_of を "dom" にし、source_sha256 を本文のテキストの
SHA-256 にする（ingest の手順の「本文を取れないページ」に合わせる）。
"""
import hashlib
import re
import sys
from pathlib import Path

scripts, html_path, page_url = sys.argv[1], Path(sys.argv[2]), sys.argv[3]
sys.path.insert(0, scripts)
import wiki_fetch  # noqa: E402

html_bytes = html_path.read_bytes()
_orig_fetch = wiki_fetch.fetch


def fake_fetch(url, *args, **kwargs):
    if url == page_url:
        return html_bytes, page_url, "text/html; charset=utf-8"
    return _orig_fetch(url, *args, **kwargs)


wiki_fetch.fetch = fake_fetch
argv = [page_url] + sys.argv[4:]
code = wiki_fetch.main(argv)

# frontmatter を DOM の取得に合わせて直す
raw_root = Path(argv[argv.index("--raw-root") + 1])
slug = argv[argv.index("--slug") + 1]
target = raw_root / f"{slug}.md"
if code == 0 and target.exists():
    text = target.read_bytes().decode("utf-8")
    body = text.split("\n---\n", 1)[1] if text.startswith("---\n") else text
    sha = hashlib.sha256(body.encode("utf-8")).hexdigest()
    text = re.sub(r'^source_sha256: ".*"$', f'source_sha256: "{sha}"', text, count=1, flags=re.M)
    text = re.sub(r'^source_sha256_of: ".*"$', 'source_sha256_of: "dom"', text, count=1, flags=re.M)
    target.write_bytes(text.encode("utf-8"))
sys.exit(code)
