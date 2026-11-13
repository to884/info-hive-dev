"""3 案の試作を見比べるページ（out/compare.html）を作る。画面の写しを並べ、動く試作へのリンクを置く。

使い方: python -X utf8 compare.py <写しのフォルダー>
写しは shots/<案>-<名前>.png の形で、out/shots/ に写す。配布対象ではない。
"""
from __future__ import annotations

import shutil
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
OUT = HERE / "out"

VARIANTS = [
    ("a", "A. 分類の木",
     "索引の構造をそのまま主役にする。サイドバーは検索欄と、件数つきで折りたためる木。今のページのグループだけを開き、"
     "今のページを強調する。索引のページは、グループごとの節に、題名、種類、更新日、要約、タグの行を並べ、先頭にグループへの目次を置く。",
     ["索引を書いた人の分類がそのまま見える", "今の画面からの変化が小さく、JavaScript なしでも同じ一覧が読める",
      "ページが多いと、索引のページが長い 1 枚になる"]),
    ("b", "B. 絞り込める一覧",
     "全ページを 1 つの一覧にし、種類、タグ、グループで絞り、索引の順、更新日、題名で並べ替える。"
     "サイドバーは、グループの名前と件数だけにして軽くする。記事のページでは、今のページのグループを強調する。",
     ["「最近更新したもの」「このタグのもの」を探すのに強い", "索引の分類は、行の上の小さな道としてだけ残る",
      "絞り込みの部品が多く、狭い幅では一覧の前に場所を取る"]),
    ("c", "C. 検索が主役",
     "索引のページの先頭に大きな検索欄を置き、打つたびに、当たった欄（題名、タグ、見出し、要約）と文字を示す。"
     "検索の前は、最近更新したページ、グループのカード、畳んだ全ページの一覧を出す。記事のページのサイドバーは、"
     "今のページの場所と、同じグループのページだけを出す。",
     ["名前やキーワードを覚えているときにいちばん速い", "サイドバーが短く、記事を読むときに邪魔にならない",
      "Wiki 全体の分類を見渡すには、索引のページに戻る"]),
    ("d", "D. 木と絞り込める一覧（A の左 + B の右）",
     "記事のページの左のペインは A の木（件数つき、折りたたみ、今のページの強調）。索引のページでは、左の木をグループの"
     "名前と件数までに畳み、名前を押すと右の B の一覧（種類、タグ、グループで絞り、並べ替える）をそのグループに絞る。"
     "記事のページの木の「一覧」からも、索引のページを絞った状態で開く。",
     ["分類をたどることと、条件で絞ることを、同じ画面でできる", "木と一覧が同じグループの ID を使うので、件数がそろう",
      "索引のページで、ページの名前が左右に二重に出ない"]),
]
SHOTS = [("large-index-1280", "索引（400 ページ、indexes/ に分割）"), ("large-search", "「形態素 検索」と打ったところ"),
         ("large-article-1280", "記事のページのサイドバー"), ("indexed-index-1280", "索引（索引が整った 27 ページ）"),
         ("noindex-index-1280", "索引（index.md のない Wiki）"), ("large-index-1280-dark", "暗い配色"),
         ("large-article-390", "狭い幅（記事）"), ("large-index-390", "狭い幅（索引）"),
         ("large-index-filtered", "木の「健康」から一覧を絞ったところ")]
WIKIS = [("large", "400 ページ"), ("indexed", "索引つき 27 ページ"), ("noindex", "索引なし 27 ページ")]

CSS = """
:root { color-scheme: light dark; font-family: system-ui, "Segoe UI", "Yu Gothic UI", "Meiryo", sans-serif;
  line-height: 1.7; --fg: #1f2328; --muted: #59636e; --bg: #fff; --sub: #f6f8fa; --border: #d0d7de; --accent: #0b57d0; }
@media (prefers-color-scheme: dark) { :root { --fg: #e6edf3; --muted: #9198a1; --bg: #0d1117; --sub: #161b22;
  --border: #30363d; --accent: #6cb6ff; } }
body { margin: 0; color: var(--fg); background: var(--bg); }
header { padding: 1.5rem 2rem 0.5rem; max-width: 90rem; margin: 0 auto; }
header h1 { margin: 0; font-size: 1.5rem; }
header p { color: var(--muted); margin: 0.25rem 0; }
.base { max-width: 90rem; margin: 0 auto; padding: 0 2rem; }
.grid { display: grid; grid-template-columns: repeat(auto-fit, minmax(22rem, 1fr)); gap: 1.25rem; padding: 1rem 2rem 3rem;
  max-width: 90rem; margin: 0 auto; }
.col { border: 1px solid var(--border); border-radius: 0.75rem; padding: 1rem; background: var(--sub); min-width: 0; }
.col h2 { margin: 0 0 0.25rem; font-size: 1.25rem; }
.col p { margin: 0.25rem 0 0.5rem; font-size: 0.9rem; }
.col ul { margin: 0 0 0.75rem; padding-left: 1.1rem; font-size: 0.875rem; }
.open { display: flex; flex-wrap: wrap; gap: 0.4rem; margin-bottom: 0.75rem; }
.open a { font-size: 0.8125rem; border: 1px solid var(--accent); color: var(--accent); border-radius: 1rem;
  padding: 0.1rem 0.6rem; text-decoration: none; }
figure { margin: 0 0 0.9rem; }
figcaption { font-size: 0.8rem; color: var(--muted); }
figure img { width: 100%; border: 1px solid var(--border); border-radius: 0.375rem; display: block; background: #fff; }
.narrow { display: grid; grid-template-columns: 1fr 1fr; gap: 0.5rem; }
@media (max-width: 64rem) { .grid { grid-template-columns: 1fr; } }
"""


def main() -> int:
    shots = Path(sys.argv[1])
    (OUT / "shots").mkdir(parents=True, exist_ok=True)
    for f in shots.glob("*.png"):
        shutil.copy2(f, OUT / "shots" / f.name)
    cols = []
    for v, name, desc, points in VARIANTS:
        links = "".join(f'<a href="{w}/{v}/index.html">{label}で開く</a>' for w, label in WIKIS)
        figs = []
        narrow = []
        for key, cap in SHOTS:
            if not (shots / f"{v}-{key}.png").exists():
                continue
            img = f'<figure><img src="shots/{v}-{key}.png" alt="{name}: {cap}" loading="lazy"><figcaption>{cap}</figcaption></figure>'
            (narrow if key.endswith("390") else figs).append(img)
        cols.append(f'<section class="col"><h2>{name}</h2><p>{desc}</p><ul>'
                    + "".join(f"<li>{p}</li>" for p in points) + f'</ul><div class="open">{links}</div>'
                    + "".join(figs) + f'<div class="narrow">{"".join(narrow)}</div></section>')
    base = "".join(f'<figure><img src="../../../docs/agent-runs/2026-11-13-wiki-browse-findability/baseline/{n}.png" '
                   f'alt="今の画面: {c}"><figcaption>今: {c}</figcaption></figure>'
                   for n, c in (("large-index-1280", "索引（400 ページ）"), ("large-article-390", "狭い幅（記事）")))
    page = (f'<!doctype html><html lang="ja"><head><meta charset="utf-8"><meta name="viewport" '
            f'content="width=device-width, initial-scale=1"><title>browse の索引とサイドバー: 3 案</title>'
            f"<style>{CSS}</style></head><body><header><h1>browse の索引とサイドバー: 3 案</h1>"
            f"<p>3 案とも、検索（題名、タグ、見出し、要約の部分一致。空白で区切ると AND）、今のページの強調、"
            f"狭い幅での「メニュー」への畳み込み、暗い配色を持つ。違うのは、何を主役にするかである。"
            f"組み合わせてもよい。</p><p>要約は、索引の行（<code>- [[ページ]]: 要約</code>）から取り、"
            f"なければ本文の最初の文を使っている。</p></header>"
            f'<details class="base"><summary>今の画面（比べる基準）</summary><div class="narrow">{base}</div></details>'
            f'<div class="grid">{"".join(cols)}</div></body></html>')
    (OUT / "compare.html").write_bytes(page.encode("utf-8"))
    print(OUT / "compare.html")
    return 0


if __name__ == "__main__":
    sys.exit(main())
