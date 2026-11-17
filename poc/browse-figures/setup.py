"""図の描画の PoC のサイトを組み立てる。配布対象ではない。

site/ に、ページ、枠の文書、手書きの svg を書き、src/ の JS と CSS、同梱の fluent2.css と mermaid.tiny.js を写す。
site/ は生成物なので、リポジトリに入れない。
mermaid.tiny.js は npm の tarball から取り出したものを引数で渡す。SHA-256 を照らしてから写す。

使い方: python -X utf8 setup.py <mermaid.tiny.js のパス>
"""
from __future__ import annotations

import hashlib
import html
import shutil
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
SITE = HERE / "site"
FLUENT = HERE.parents[1] / "info-hive-wiki" / "skills" / "info-hive" / "scripts" / "browse_assets" / "fluent2.css"
TINY_SHA256 = "c41f5236091b83f524c4940f97a16b2b14a76f21ff84aea4fd6b66421d8a2a9a"  # @mermaid-js/tiny 12.3.0

CSP_PAGE = ("default-src 'none'; script-src 'self'; style-src 'self'; img-src 'self' data:; "
            "frame-src 'self'; base-uri 'none'; form-action 'none'")
CSP_FRAME_META = ("default-src 'none'; script-src 'self'; style-src 'unsafe-inline'; img-src data:; "
                  "base-uri 'none'; form-action 'none'")
# file:// で 'self' が一致しないときの代わり（門 1 の下がり方の 1）
CSP_FRAME_META_FILE = ("default-src 'none'; script-src 'self' file:; style-src 'unsafe-inline'; img-src data:; "
                       "base-uri 'none'; form-action 'none'")
CSP_FRAME_HEADER = CSP_FRAME_META + "; sandbox allow-scripts"
CSP_SVG = "default-src 'none'; style-src 'unsafe-inline'; sandbox"

# (id, 種類, ソース)。種類は試験が期待を決めるのに使う
DIAGRAMS = [
    ("flow", "ok", """flowchart LR
  予測["予測"] --> 更新["更新<br>（観測で直す）"]
  観測["観測値"] --> 更新
  更新 --> 予測"""),
    ("seq", "ok", """sequenceDiagram
  participant 利用者
  participant サーバー
  利用者->>サーバー: ページを要求する
  サーバー-->>利用者: HTML を返す
  Note over 利用者,サーバー: 127.0.0.1 だけで待ち受ける"""),
    ("state", "ok", """stateDiagram-v2
  [*] --> 待機
  待機 --> 組み立て中: 変更を見つけた
  組み立て中 --> 待機: 組み立てた
  組み立て中 --> 失敗: 読めない
  失敗 --> [*]"""),
    ("class", "ok", """classDiagram
  class 中核 {
    +写し snapshot
    +描く() HTML
  }
  class サーバー
  サーバー --> 中核 : 呼ぶ"""),
    ("er", "ok", """erDiagram
  ページ ||--o{ リンク : 持つ
  ページ {
    string スラッグ
    string 題名
  }"""),
    ("gantt", "ok", """gantt
  title 図の描画の段階
  dateFormat YYYY-MM-DD
  section 準備
  PoC :a1, 2026-11-17, 2d
  設計 :after a1, 2d
  section 実装
  SVG :2026-11-21, 3d
  Mermaid :2026-11-24, 4d"""),
    ("timeline", "ok", """timeline
  title browse の版
  0.18.0 : 探しやすさ
  0.19.0 : 記事のページを Fluent 2 に
  0.25.0 : タグの段と Tree"""),
    ("pie", "ok", """pie title 図の種類
  "流れ" : 5
  "表" : 3
  "svg" : 1"""),
    ("acc", "ok", """flowchart TD
  accTitle: 取り込みの流れ
  accDescr: raw を作り、ページを書き、索引を更新する
  raw --> ページ --> 索引"""),
    # 図の側の指定で、htmlLabels と見た目を変えようとする。通ってはならない
    ("override", "ok", """%%{init: {"htmlLabels": true, "flowchart": {"htmlLabels": true}, "theme": "forest", "themeCSS": ".node rect { fill: #ff0000 !important; }", "themeVariables": {"primaryColor": "#ff0000"}}}%%
flowchart LR
  甲["上書き<b>太字</b>"] --> 乙"""),
    # 外の画像とリンク。要求が出てはならない
    ("external", "ok", """flowchart LR
  A@{ img: "https://example.com/x.png", label: "画像", pos: "t", h: 40, constraint: "on" }
  A --> B["リンク"]
  click B href "https://example.com/" _blank"""),
    ("broken", "error", """flowchart LR
  A -->"""),
    ("mindmap", "error", """mindmap
  root((wiki))
    取り込み
    問い合わせ"""),
]

SVG_TEXT = """<svg xmlns="http://www.w3.org/2000/svg" width="240" height="120" viewBox="0 0 240 120" onload="document.documentElement.setAttribute('data-pwned','onload')">
<style>.box{fill:#0f6cbd}.t{fill:#ffffff;font:16px sans-serif}</style>
<rect class="box" x="10" y="10" width="220" height="100" rx="8"/>
<text class="t" x="120" y="66" text-anchor="middle">手書きの図</text>
<image href="https://example.com/x.png" x="0" y="0" width="10" height="10"/>
<script>document.documentElement.setAttribute('data-pwned','script');fetch('https://example.com/pwn').catch(function(){});</script>
</svg>
"""


def page(title: str, body: str) -> str:
    return ('<!doctype html>\n<html lang="ja" data-theme="light"><head><meta charset="utf-8">'
            f'<meta http-equiv="Content-Security-Policy" content="{html.escape(CSP_PAGE)}">'
            f'<title>{html.escape(title)}</title><link rel="icon" href="data:,">'
            '<link rel="stylesheet" href="fluent2.css"><link rel="stylesheet" href="poc.css"></head>'
            f'<body class="fui-FluentProvider"><main id="_body">{body}</main>'
            '<script src="figures.js"></script></body></html>\n')


def frame(meta: "str | None") -> str:
    csp = f'<meta http-equiv="Content-Security-Policy" content="{html.escape(meta)}">' if meta else ""
    return ('<!doctype html>\n<html lang="ja"><head><meta charset="utf-8">'
            f'{csp}'
            '<title>図の描画</title></head><body>'
            '<script src="mermaid.tiny.js"></script><script src="mermaid-frame.js"></script></body></html>\n')


def main() -> int:
    if len(sys.argv) != 2:
        print(__doc__)
        return 2
    tiny = Path(sys.argv[1])
    data = tiny.read_bytes()
    digest = hashlib.sha256(data).hexdigest()
    print(f"mermaid.tiny.js: {len(data)} バイト、SHA-256 {digest}")
    if digest != TINY_SHA256:
        print("SHA-256 が記録と違う", file=sys.stderr)
        return 1
    (SITE / "_frame").mkdir(parents=True, exist_ok=True)
    (SITE / "mermaid.tiny.js").write_bytes(data)
    (SITE / "_frame" / "mermaid.tiny.js").write_bytes(data)
    shutil.copyfile(FLUENT, SITE / "fluent2.css")

    blocks = []
    for ident, kind, src in DIAGRAMS:
        blocks.append(f'<h2 id="h-{ident}">{ident}（{kind}）</h2>\n'
                      f'<pre data-poc-id="{ident}" data-poc-kind="{kind}"><code class="language-mermaid">'
                      f'{html.escape(src)}\n</code></pre>')
    blocks.append('<h2 id="h-svg">svg</h2>\n'
                  '<figure class="fui-Card fig" data-theme="light" data-fig="svg">'
                  '<img class="fui-Image fig-img" src="fig.svg" alt="手書きの図" width="240" height="120"></figure>')
    blocks.append('<h2 id="h-code">ふつうのコード</h2>\n<pre><code class="language-python">print("mermaid ではない")\n</code></pre>')
    out = {
        "page.html": page("図の PoC", "\n".join(blocks)),
        "page-empty.html": page("図のない PoC", '<p>図はない。</p><pre><code class="language-text">mermaid ではない\n</code></pre>'),
        "mermaid-frame.html": frame(CSP_FRAME_META),
        "mermaid-frame-file.html": frame(CSP_FRAME_META_FILE),
        # <meta> の CSP を持たない枠。サーバーのヘッダーの CSP だけで守る（WebKit の 'self' のため）
        "mermaid-frame-nometa.html": frame(None),
        # 2 回目の PoC: トークンのない /_frame/ の下に置く枠（_frame/ に書く）
        "_frame/mermaid-frame.html": frame(None),
        "secret.js": "window.SECRET = 'wiki の中身';\n",
        "fig.svg": SVG_TEXT,
    }
    for name, text in out.items():
        (SITE / name).write_bytes(text.encode("utf-8"))
    for src in sorted((HERE / "src").iterdir()):
        shutil.copyfile(src, SITE / src.name)
    shutil.copyfile(HERE / "src" / "mermaid-frame.js", SITE / "_frame" / "mermaid-frame.js")
    print(f"書いた: {SITE}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
