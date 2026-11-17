"""概要の表示の試作（S3）のサイトを組み立てる。配布対象ではない。

1. browse の build で、このリポジトリの wiki を site/ に書き出す（本物の記事のページを得る）。
2. overview/ のサイドカー（.overview.md と svg）を、browse と同じパーサーで描き、
   対象のページの h1 の直後に差し込む。
3. 図の表示の試作（poc/browse-figures の site/）から、Mermaid を描く部品を写す。

site/ は生成物なので、リポジトリに入れない。

使い方: uv run --python 3.12 --with pyyaml==6.0.3 python -X utf8 build.py <図の表示の試作の site/ のパス>
"""
from __future__ import annotations

import hashlib
import html
import os
import re
import shutil
import subprocess
import sys
import urllib.parse
from pathlib import Path

HERE = Path(__file__).resolve().parent
REPO = HERE.parents[1]
SCRIPTS = REPO / "info-hive-wiki" / "skills" / "info-hive" / "scripts"
WIKI = REPO / "wiki"
SITE = HERE / "site"
OVERVIEWS = HERE / "overview"

sys.path.insert(0, str(SCRIPTS))
import wiki_pages  # noqa: E402
from markdown_it.token import Token  # noqa: E402  wiki_pages が _vendor をパスに足す

CSP_FRAME_SRC = "img-src 'self' data:; frame-src 'self';"


def text_sha256(data: bytes) -> str:
    """BOM を除き、改行を LF にそろえた全文の SHA-256（計画の既定 3）。"""
    text = data.decode("utf-8-sig").replace("\r\n", "\n").replace("\r", "\n")
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def split_frontmatter(text: str) -> "tuple[dict, str]":
    meta: dict = {}
    if not text.startswith("---\n"):
        return meta, text
    end = text.index("\n---\n", 4)
    for line in text[4:end].splitlines():
        key, _, value = line.partition(":")
        meta[key.strip()] = value.strip().strip('"')
    return meta, text[end + 5:]


def svg_size(data: bytes) -> "tuple[str, str]":
    head = data[:600].decode("utf-8", "replace")
    w = re.search(r'<svg[^>]*\swidth="(\d+)"', head)
    h = re.search(r'<svg[^>]*\sheight="(\d+)"', head)
    return (w.group(1) if w else "", h.group(1) if h else "")


def render_overview(sidecar: Path, page_rel: str, page_bytes: bytes) -> str:
    meta, body = split_frontmatter(sidecar.read_bytes().decode("utf-8").replace("\r\n", "\n"))
    state = "fresh" if meta.get("page_sha256") == text_sha256(page_bytes) else "stale"
    parser = wiki_pages.new_parser()
    tokens = parser.parse(body)
    depth = page_rel.count("/")
    out = []
    i = 0
    while i < len(tokens):
        tok = tokens[i]
        nxt = tokens[i + 1] if i + 1 < len(tokens) else None
        # 画像だけの段落を、図の入れ物に替える。図は中身のハッシュの名前で figures/ に出す
        if tok.type == "paragraph_open" and nxt is not None and nxt.type == "inline" \
                and len(nxt.children or []) == 1 and nxt.children[0].type == "image":
            img = nxt.children[0]
            # markdown-it は src をパーセント符号化する。ファイル名に戻す
            src = sidecar.parent / urllib.parse.unquote(img.attrs["src"])
            data = src.read_bytes()
            name = hashlib.sha256(data).hexdigest()[:20] + ".svg"
            (SITE / "figures").mkdir(exist_ok=True)
            (SITE / "figures" / name).write_bytes(data)
            w, h = svg_size(data)
            out.append(Token("html_block", "", 0, content=(
                '<figure class="fui-Card fig" data-theme="light" data-fig="svg">'
                f'<img class="fui-Image fig-img" src="{"../" * depth}figures/{name}" '
                f'alt="{html.escape(img.content)}" width="{w}" height="{h}" loading="lazy" decoding="async">'
                '</figure>\n')))
            i += 3
            continue
        out.append(tok)
        i += 1
    rendered = parser.renderer.render(out, parser.options, {})
    note = f'このページをもとに {html.escape(meta.get("generator", ""))} が作成（{html.escape(meta.get("generated", ""))}）'
    stale = ('<p class="ov-stale">ページが、この概要を作ったあとで変わっている。概要は古いかもしれない。</p>'
             if state == "stale" else "")
    return (f'<details open class="ov" data-ov-state="{state}">'
            f'<summary class="ov-head"><span class="ov-title">概要</span>'
            f'<span class="ov-note">{note}</span></summary>\n'
            f'<div class="ov-body">{stale}\n{rendered}</div></details>\n')


def main() -> int:
    if len(sys.argv) != 2:
        print(__doc__)
        return 2
    parts = Path(sys.argv[1])
    if SITE.exists():
        shutil.rmtree(SITE)
    env = dict(os.environ, INFO_HIVE_DATA_DIR=str(HERE / ".data"), PYTHONUTF8="1")
    done = subprocess.run([sys.executable, "-X", "utf8", str(SCRIPTS / "wiki_browse.py"), "build", str(WIKI),
                           "--out", str(SITE)], env=env, capture_output=True, text=True, encoding="utf-8")
    if done.returncode != 0:
        print(done.stdout, done.stderr, file=sys.stderr)
        return 1

    # 図の表示の試作の部品を、書き換えずに写す。親の側は assets/ に、枠の側は配信元の根の _frame/ に置く
    # （試作の figures.js は、枠を location.origin + "/_frame/mermaid-frame.html" から読む。サーバーの方式でだけ動く）
    shutil.copyfile(parts / "figures.js", SITE / "assets" / "figures.js")
    shutil.copytree(parts / "_frame", SITE / "_frame")
    shutil.copyfile(HERE / "overview.css", SITE / "assets" / "overview.css")

    count = 0
    for sidecar in sorted(OVERVIEWS.rglob("*.overview.md")):
        page_rel = sidecar.relative_to(OVERVIEWS).as_posix()[:-len(".overview.md")]
        page_md = WIKI / (page_rel + ".md")
        page_html = SITE / (page_rel + ".html")
        if not page_md.is_file() or not page_html.is_file():
            print(f"元のページがない: {page_rel}", file=sys.stderr)
            return 1
        block = render_overview(sidecar, page_rel, page_md.read_bytes())
        text = page_html.read_bytes().decode("utf-8")
        body_at = text.index('<div id="_body">')
        h1_at = text.find("</h1>", body_at)
        at = h1_at + len("</h1>") if h1_at >= 0 else body_at + len('<div id="_body">')
        text = text[:at] + "\n" + block + text[at:]
        prefix = "../" * page_rel.count("/")
        if "img-src 'self' data:;" not in text:
            print("CSP の形が変わっている", file=sys.stderr)
            return 1
        text = text.replace("img-src 'self' data:;", CSP_FRAME_SRC, 1)
        text = text.replace("</head>", f'<link rel="stylesheet" href="{prefix}assets/overview.css">\n</head>', 1)
        text = text.replace("</body>", f'<script src="{prefix}assets/figures.js"></script>\n</body>', 1)
        page_html.write_bytes(text.encode("utf-8"))
        print(f"差し込んだ: {page_rel}（元のページの SHA-256 {text_sha256(page_md.read_bytes())}）")
        count += 1
    print(f"書いた: {SITE}（概要 {count} 件）")
    return 0


if __name__ == "__main__":
    sys.exit(main())
