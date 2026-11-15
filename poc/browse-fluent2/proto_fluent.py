"""browse の画面を Fluent 2 にした試作を作る（配布対象ではない）。

探しやすさの設計（docs/plans/wiki-browse-findability-2026-11-13.md）の案 D の画面（左の木、索引の
絞り込める一覧、記事のページの検索）と、記事のページの部品（メタ欄、被リンク、関係表、診断、注意の帯）を、
Fluent 2 の部品のマークアップで描く。データは合成の Wiki で、実際の中核は使わない。

Fluent 2 の CSS は、プラグインに同梱した写し（info-hive-wiki の browse_assets/fluent2.css）から出力に写す。
スキル fluent2-html-replica の場所は読まない。

使い方: python -X utf8 proto_fluent.py [--assets <browse_assets のディレクトリ>] [--out <出力先>]
出力先の下に、スコープの表示の案ごとのフォルダー（project-green、project-neutral、user）を作り直す。
"""
from __future__ import annotations

import argparse
import hashlib
import html
import json
import shutil
from pathlib import Path

HERE = Path(__file__).resolve().parent
REPO = HERE.parent.parent
DEFAULT_ASSETS = REPO / "info-hive-wiki" / "skills" / "info-hive" / "scripts" / "browse_assets"
CSP = ("default-src 'none'; script-src 'self'; style-src 'self'; img-src 'self' data:; "
       "base-uri 'none'; form-action 'none'")
TYPE_LABELS = {"source": "ソース", "entity": "エンティティ", "concept": "コンセプト", "synthesis": "シンセシス"}
VARIANTS = {
    "project-green": ("project", "green"),
    "project-neutral": ("project", "neutral"),
    "user": ("user", "brand"),
}
SCOPE_HEADINGS = {"user": "ユーザースコープの wiki", "project": "プロジェクトの wiki"}

# 合成の Wiki。グループの入れ子は、木の深い段（6 段）を確かめるために深くしてある。
PAGES = [
    ("bm25", "BM25", "concept", ["検索", "ランキング"], "2026-04-18",
     "クエリの語が文書にどれだけ現れるかをもとに、文書の関連度を点数にする方法"),
    ("tfidf", "TF-IDF", "concept", ["検索"], "2026-03-02", "語の出現の頻度と、文書の集合での珍しさを掛け合わせた重み"),
    ("hybrid", "ハイブリッド検索", "concept", ["検索", "埋め込み"], "2026-05-10",
     "語の一致と埋め込みの近さの 2 つの順位を合わせて並べる検索"),
    ("rrf", "Reciprocal Rank Fusion", "concept", ["ランキング"], "2026-05-11", "複数の順位の逆数を足して 1 つの順位にする方法"),
    ("e5", "multilingual-e5", "entity", ["埋め込み", "モデル"], "2026-02-20", "多言語の文の埋め込みのモデル"),
    ("sudachi", "Sudachi", "entity", ["形態素解析"], "2026-01-15", "日本語の形態素解析器。分割の単位を 3 つから選べる"),
    ("karpathy-gist", "Karpathy の LLM Wiki", "source", ["LLM", "wiki"], "2026-04-01",
     "LLM が保守する Markdown の wiki という考え方を述べたメモ"),
    ("jlreq", "日本語組版処理の要件", "source", ["組版"], "2026-03-30", "W3C の、日本語の組版の要件をまとめた文書"),
    ("fluent2", "Fluent 2 のデザイン", "source", ["デザイン"], "2026-11-14", "Microsoft の Fluent 2 のデザインの考え方"),
    ("search-compare", "検索の方式の比較", "synthesis", ["検索", "評価"], "2026-06-01",
     "BM25、埋め込み、ハイブリッドを、日本語の 27 文書で比べた結果"),
    ("deep-leaf", "いちばん深い段のページで、名前がとても長くサイドバーの幅に収まらないときの折り返しを確かめる", "concept",
     ["試験"], "2026-11-14", "木の深い段と、長い名前の折り返しを確かめるためのページ"),
    ("kinsoku", "行頭の禁則", "concept", ["組版"], "2026-03-31", "句読点や閉じ括弧を行の頭に置かない規則"),
    ("long-values", "長い値のページ", "W" * 120, ["W" * 200, "とても長いタグの名前がサイドバーや一覧の幅を超えるときの確かめ"], "2026-11-14",
     "タグ、種類、グループの名前が長いときに、幅 320 でもはみ出さないことを確かめるページ"),
]
GROUPS = [
    {"id": "_g1", "title": "コンセプト", "items": [], "children": [
        {"id": "_g2", "title": "検索", "items": ["bm25", "tfidf", "hybrid"], "children": [
            {"id": "_g3", "title": "ランキング", "items": ["rrf"], "children": [
                {"id": "_g4", "title": "評価の指標", "items": [], "children": [
                    {"id": "_g5", "title": "深い段", "items": [], "children": [
                        {"id": "_g6", "title": "さらに深い段", "items": ["deep-leaf"], "children": []}]}]}]}]},
        {"id": "_g7", "title": "組版", "items": ["kinsoku"], "children": []},
        {"id": "_g11", "title": "名前がとても長いグループで、サイドバーの幅にも索引の階層の表示にも収まらないもの" + "X" * 80, "items": ["long-values"], "children": []}]},
    {"id": "_g8", "title": "エンティティ", "items": ["e5", "sudachi"], "children": []},
    {"id": "_g9", "title": "ソース", "items": ["karpathy-gist", "jlreq", "fluent2", "missing-page"], "children": []},
    {"id": "_g10", "title": "シンセシス", "items": ["search-compare"], "children": []},
]
BY_ID = {p[0]: p for p in PAGES}

ICON_SEARCH = ('<svg class="fui-Icon" width="1em" height="1em" viewBox="0 0 20 20" fill="currentColor" aria-hidden="true">'
               '<path d="M13.73 14.44a6.5 6.5 0 1 1 .7-.7l3.42 3.4a.5.5 0 0 1-.63.77l-.07-.06zm-.71-.71A5.5 5.5 0 0 0 15 9.5a5.5 '
               '5.5 0 1 0-1.98 4.23"/></svg>')
ICON_WARNING = ('<svg class="fui-Icon" width="20" height="20" viewBox="0 0 20 20" fill="currentColor" aria-hidden="true">'
                '<path d="M7.37 3.56a3 3 0 0 1 5.26 0l5.5 10A3 3 0 0 1 15.5 18h-11a3 3 0 0 1-2.63-4.44zM10 12.75a.75.75 0 1 0 '
                '0 1.5.75.75 0 0 0 0-1.5m0-6.25a.5.5 0 0 0-.5.5v4a.5.5 0 0 0 1 0V7a.5.5 0 0 0-.5-.5"/></svg>')


def esc(s) -> str:
    return html.escape(str(s), quote=True)


def write(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes(text.encode("utf-8"))


def js_data(name: str, value) -> str:
    text = json.dumps(value, ensure_ascii=False, separators=(",", ":"))
    return f"window.{name}={text.replace('</', '<' + chr(92) + '/')};\n"


def group_path(gid: str) -> list:
    def walk(groups, trail):
        for g in groups:
            here = trail + [g]
            if g["id"] == gid:
                return here
            found = walk(g["children"], here)
            if found:
                return found
        return None
    return walk(GROUPS, []) or []


def first_group(pid: str) -> "str | None":
    def walk(groups):
        for g in groups:
            if pid in g["items"]:
                return g["id"]
            r = walk(g["children"])
            if r:
                return r
        return None
    return walk(GROUPS)


def groups_of(pid: str) -> list:
    out = []

    def walk(groups, trail):
        for g in groups:
            here = trail + [g["id"]]
            if pid in g["items"]:
                out.extend(i for i in here if i not in out)
            walk(g["children"], here)
    walk(GROUPS, [])
    return out


def count(g) -> int:
    return len([i for i in g["items"] if i in BY_ID]) + sum(count(c) for c in g["children"])


def head(root: str, title: str, scope: str, extra_class: str = "") -> str:
    return (f'<!doctype html>\n<html lang="ja" data-theme="auto" data-root="{root}">\n<head>\n<meta charset="utf-8">\n'
            f'<meta http-equiv="Content-Security-Policy" content="{CSP}">\n'
            f'<meta name="referrer" content="no-referrer">\n'
            f'<meta name="viewport" content="width=device-width, initial-scale=1">\n'
            f'<title>{esc(title)} · {"ユーザースコープ" if scope == "user" else "プロジェクト"}</title>\n'
            f'<link rel="stylesheet" href="{root}assets/fluent2.css">\n'
            f'<link rel="stylesheet" href="{root}assets/style.css">\n'
            f'<script src="{root}assets/theme.js"></script>\n</head>\n'
            f'<body class="fui-FluentProvider{extra_class}">\n')


def nav_html(root: str, scope: str, color: str) -> str:
    badge_color = {"brand": "brand", "green": "brand", "neutral": "informative"}[color]
    cls = " scope-green" if color == "green" else ""
    return (f'<nav id="_nav" class="fui-NavDrawer" aria-label="wiki のナビゲーション">\n'
            f'<div class="fui-NavDrawerHeader nav-head">\n'
            f'<p id="_scope" class="scope scope-{scope}"><span class="fui-Badge{cls}" data-appearance="tint" '
            f'data-color="{badge_color}" data-size="large" data-shape="rounded">{SCOPE_HEADINGS[scope]}</span></p>\n'
            f'<a class="fui-NavItem nav-home" href="{root}index.html">索引</a>\n'
            f'</div>\n<div class="fui-NavDrawerBody" id="_navbody">'
            f'<noscript><a class="fui-Link" href="{root}index.html">索引へ</a></noscript></div>\n</nav>\n')


def tail(root: str, page_id: str = "") -> str:
    return (f'<script src="{root}nav.js"></script>\n'
            f'<script src="{root}assets/app.js"></script>\n</body>\n</html>\n')


def type_badge(t: str) -> str:
    cls = t if t in TYPE_LABELS else "other"
    return (f'<span class="fui-Badge badge t-{cls}" data-appearance="tint" data-size="small" data-shape="rounded">'
            f'{esc(TYPE_LABELS.get(t, t or "種類なし"))}</span>')


def tag_html(t: str) -> str:
    return (f'<span class="tag fui-Tag" data-appearance="outline" data-size="extra-small">'
            f'<span class="fui-Tag__primaryText">{esc(t)}</span></span>')


def render_index(scope: str, color: str) -> str:
    root = ""
    rows = []
    order = 0
    seen = set()

    def walk(groups):
        nonlocal order
        for g in groups:
            for pid in g["items"]:
                if pid in BY_ID and pid not in seen:
                    seen.add(pid)
                    order += 1
                    p = BY_ID[pid]
                    path = " › ".join(x["title"] for x in group_path(g["id"]))
                    rows.append(
                        f'<li class="fx-row" data-type="{p[2]}" data-updated="{p[4]}" data-title="{esc(p[1])}" '
                        f'data-order="{order}" data-groups="{" ".join(groups_of(pid))}">'
                        f'<div class="fx-path fui-Caption1">{esc(path)}</div>'
                        f'<div class="ix-line"><a class="ix-title" href="pages/{pid}.html">{esc(p[1])}</a>'
                        f'{type_badge(p[2])}<time class="fui-Caption1" datetime="{p[4]}">{p[4]}</time></div>'
                        f'<p class="ix-summary">{esc(p[5])}</p>'
                        f'<div class="ix-tags">{"".join(tag_html(t) for t in p[3])}</div></li>')
            walk(g["children"])
    walk(GROUPS)
    return (head(root, "索引", scope, " page-index") + nav_html(root, scope, color)
            + '<main id="_main">\n'
            + f'<header id="_ixhead"><h1 class="fui-Title2">索引</h1>'
              f'<p class="ix-stats fui-Caption1">{len(rows)} ページ</p></header>\n'
            + '<div id="_filters" class="fx-bar"><noscript><p class="state fui-Caption1">絞り込みと検索には JavaScript が要る。'
              '一覧は索引の順に並んでいる。</p></noscript></div>\n'
            + f'<p id="_count" class="fx-count fui-Caption1" aria-live="polite">{len(rows)} 件</p>\n'
            + f'<ul id="_index" class="fx-list">{"".join(rows)}</ul>\n'
            + '<section id="_index_unresolved"><h2 class="fui-Subtitle2">ページに決まらない索引の行</h2>'
              '<ul><li><span class="wl wl-unresolved" title="ページがない">missing-page</span>'
              '<span class="fui-Caption1 state"> ソース（index.md の 12 行目）</span></li></ul></section>\n'
            + '</main>\n' + tail(root))


def stale_bar() -> str:
    return ('<div id="_stale" class="stale fui-MessageBar" role="group" aria-labelledby="_stale_title" '
            'data-intent="warning" data-layout="multiline">'
            f'<div class="fui-MessageBar__icon" aria-hidden="true">{ICON_WARNING}</div>'
            '<div class="fui-MessageBarBody"><span class="fui-MessageBarTitle" id="_stale_title">前の内容を表示している</span>'
            'Wiki の最新の内容を表示できていない（index.md を読めない）。</div>'
            '<div class="fui-MessageBarActions"></div><div class="fui-MessageBar__bottomReflowSpacer"></div></div>\n')


def render_page(pid: str, scope: str, color: str) -> str:
    root = "../"
    p = BY_ID[pid]
    meta = [("種類", TYPE_LABELS.get(p[2], p[2])), ("タグ", "、".join(p[3])), ("更新", p[4]),
            ("出典", '<a href="karpathy-gist.html">Karpathy の LLM Wiki</a>、'
                     '<span class="wl wl-unresolved" title="ページがない">sources/missing</span>'),
            ("原本", "<code>raw/karpathy-gist.md</code>")]
    meta_rows = "".join(f'<tr class="fui-TableRow"><th class="fui-TableHeaderCell" scope="row">{k}</th>'
                        f'<td class="fui-TableCell">{v if k in ("出典", "原本") else esc(v)}</td></tr>' for k, v in meta)
    body = f"""<h1>{esc(p[1])}</h1>
<p>{esc(p[5])}。[[wikilink]] は、<a class="wl" href="tfidf.html">TF-IDF</a> のように本文の中のリンクになる。
行き先のないリンクは <span class="wl wl-unresolved" title="ページがない">未作成のページ</span>、行き先を 1 つに決められないリンクは
<span class="wl wl-ambiguous" title="行き先を 1 つに決められない">検索</span> のように出る。外部のリンクは
<a class="ext" href="https://example.com/" rel="noopener noreferrer">example.com</a> のように印が付く。</p>
<h2>定義</h2>
<p>文書 D とクエリ Q の点数は、クエリの語ごとの点数の和である。語の頻度が大きいほど点数は上がるが、上がり方は飽和する。
長い URL（https://example.com/a/very/long/path/that/should/wrap/inside/the/column/without/overflowing）も、本文の幅で折り返す。</p>
<pre><code>score(D, Q) = Σ IDF(q) · f(q, D) · (k1 + 1) / (f(q, D) + k1 · (1 − b + b · |D| / avgdl))</code></pre>
<h3>パラメーター</h3>
<table><thead><tr><th class="ta-left">名前</th><th class="ta-right">既定値</th><th>意味</th></tr></thead>
<tbody><tr><td class="ta-left"><code>k1</code></td><td class="ta-right">1.2</td><td>語の頻度の飽和の速さ</td></tr>
<tr><td class="ta-left"><code>b</code></td><td class="ta-right">0.75</td><td>文書の長さで正規化する強さ</td></tr></tbody></table>
<blockquote><p>引用の段落。語の重みは、文書の集合の中での珍しさで決まる。</p></blockquote>
<ul><li>句読点が行の頭に来ないことを、狭い幅で確かめる文。</li><li>2 つ目の項目。</li></ul>
"""
    rel_head = "".join(f'<th class="fui-TableHeaderCell" scope="col"><div class="fui-TableHeaderCell__button">{h}</div></th>'
                       for h in ("向き", "述語", "相手", "状態", "開始", "終了", "確からしさ", "出典", "証拠"))
    rel_rows = "".join(
        '<tr class="fui-TableRow">' + "".join(f'<td class="fui-TableCell">{c}</td>' for c in r) + "</tr>"
        for r in [("→", "uses", '<a href="tfidf.html">TF-IDF</a>', "active", "2026-01", "", "0.9",
                   '<a href="karpathy-gist.html">Karpathy の LLM Wiki</a>', "本文の 2 節"),
                  ("←", "compares", '<a href="search-compare.html">検索の方式の比較</a>', "active", "", "", "0.8", "", "")])
    stale = stale_bar() if pid == "bm25" else ""
    return (head(root, p[1], scope, " page-article") + nav_html(root, scope, color)
            + f'<main id="_main">\n{stale}'
            + f'<article id="_article" data-page-id="{pid}">\n'
            + f'<table id="_meta" class="meta fui-Table" data-size="small" aria-label="ページの情報"><tbody class="fui-TableBody">'
              f'{meta_rows}</tbody></table>\n'
            + f'<div id="_body">\n{body}</div>\n</article>\n'
            + '<section id="_backlinks"><h2 class="fui-Subtitle2">被リンク</h2><ul class="fui-List" role="list">'
              '<li class="fui-ListItem"><a class="fui-Link" href="hybrid.html">ハイブリッド検索</a></li>'
              '<li class="fui-ListItem"><a class="fui-Link" href="search-compare.html">検索の方式の比較</a></li></ul></section>\n'
            + '<section id="_relations"><h2 class="fui-Subtitle2">関係</h2><div class="table-scroll">'
              f'<table class="relations fui-Table" data-size="small" aria-label="関係"><thead class="fui-TableHeader">'
              f'<tr class="fui-TableRow">{rel_head}</tr></thead><tbody class="fui-TableBody">{rel_rows}</tbody></table>'
              '</div></section>\n'
            + '<section id="_diagnostics"><h2 class="fui-Subtitle2">診断</h2><ul class="diag-list">'
              '<li>unresolved_link / target: 未作成のページ</li><li>ambiguous_link / target: 検索</li></ul></section>\n'
            + '</main>\n' + tail(root))


def nav_data() -> dict:
    def conv(groups):
        out = []
        for g in groups:
            items = []
            for pid in g["items"]:
                if pid in BY_ID:
                    items.append({"state": "resolved", "label": BY_ID[pid][1], "path": f"pages/{pid}.html", "id": pid})
                else:
                    items.append({"state": "unresolved", "label": pid})
            out.append({"id": g["id"], "title": g["title"], "count": count(g), "items": items,
                        "children": conv(g["children"])})
        return out
    return {"protocol_version": 2, "generation": "proto", "groups": conv(GROUPS)}


def search_data() -> dict:
    return {"protocol_version": 2, "generation": "proto",
            "rows": [{"id": p[0], "title": p[1], "type": p[2], "tags": p[3], "summary": p[5],
                      "path": f"pages/{p[0]}.html",
                      "group": " › ".join(x["title"] for x in group_path(first_group(p[0]) or ""))} for p in PAGES]}


def build(variant: str, out: Path, assets: Path) -> None:
    scope, color = VARIANTS[variant]
    d = out / variant
    if d.exists():
        shutil.rmtree(d)
    (d / "assets").mkdir(parents=True)
    shutil.copyfile(assets / "fluent2.css", d / "assets" / "fluent2.css")
    for name in ("style.css", "theme.js", "app.js"):
        shutil.copyfile(HERE / "assets" / name, d / "assets" / name)
    write(d / "index.html", render_index(scope, color))
    for p in PAGES:
        write(d / "pages" / f"{p[0]}.html", render_page(p[0], scope, color))
    write(d / "nav.js", js_data("WIKI_NAV", nav_data()))
    write(d / "data" / "search.js", js_data("WIKI_SEARCH", search_data()))


def main() -> int:
    ap = argparse.ArgumentParser(description="browse の Fluent 2 の試作を作る")
    ap.add_argument("--assets", type=Path, default=DEFAULT_ASSETS,
                    help="fluent2.css のあるディレクトリ（既定はプラグインの browse_assets）")
    ap.add_argument("--out", type=Path, default=HERE / "out")
    args = ap.parse_args()
    src = args.assets / "fluent2.css"
    if not src.is_file():
        raise SystemExit(f"fluent2.css がない: {src}（info-hive-wiki の feature/browse-fluent2 を取り出す）")
    for v in VARIANTS:
        build(v, args.out, args.assets)
    digest = hashlib.sha256(src.read_bytes()).hexdigest()
    print(json.dumps({"out": args.out.as_posix(), "variants": list(VARIANTS), "fluent2_sha256": digest},
                     ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
