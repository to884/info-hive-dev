"""設計書から外部依存のない閲覧用 HTML を作る。"""
from pathlib import Path
from html import escape
from html.parser import HTMLParser
from urllib.parse import quote, unquote, urlparse
import hashlib
import json
import re

import markdown

ROOT = Path(__file__).resolve().parents[3]
OUT = Path(__file__).resolve().parent
SOURCE = ROOT / "docs/plans/wiki-project-ontology-2026-11-18.md"
TARGET = SOURCE.with_suffix(".html")
text = SOURCE.read_text(encoding="utf-8")
inventory = json.loads((OUT / "corpus_inventory.json").read_text(encoding="utf-8"))
verification = json.loads((OUT / "verification.json").read_text(encoding="utf-8"))
pages = {p["slug"]: p["path"] for p in inventory["pages"]}

def wikilink(match):
    slug = match[1]
    assert slug in pages, slug
    return "[" + slug + "](" + quote("../../" + pages[slug], safe="/.-") + ")"

expanded = re.sub(r"\[\[([^\]]+)\]\]", wikilink, text)
md = markdown.Markdown(extensions=["tables", "fenced_code", "toc"], extension_configs={"toc": {"toc_depth": "2-2"}})
body = md.convert(expanded)
body = re.sub(r"<h1[^>]*>.*?</h1>", "", body, count=1, flags=re.S)
body = re.sub(r"<table>(.*?)</table>", r'<div class="table-wrap" tabindex="0"><table>\1</table></div>', body, flags=re.S)
positions = {
    "release": (20, 30, "リリース", "release"),
    "product": (400, 30, "製品", "product"),
    "component": (780, 30, "構成要素", "component"),
    "change": (20, 200, "変更", "change"),
    "issue": (400, 200, "問題", "issue"),
    "concept": (780, 370, "概念・手順", "concept"),
    "decision": (20, 370, "設計判断", "decision"),
    "evaluation": (400, 370, "評価", "evaluation"),
}
edges = [
    ("release", "product", "release_of", "right"),
    ("component", "product", "part_of", "left"),
    ("release", "change", "delivers", "down"),
    ("change", "issue", "fixes", "right"),
    ("change", "decision", "implements", "down"),
    ("decision", "evaluation", "motivated_by", "right"),
    ("concept", "component", "applies_to", "up_long"),
]
paths = []
labels = []
for subject, obj, predicate, direction in edges:
    if direction == "none":
        continue
    x, y, *_ = positions[subject]
    ox, oy, *_ = positions[obj]
    if direction in {"right", "left"}:
        sx, sy, ex, ey = (x + 180, y + 30, ox, oy + 30) if direction == "right" else (x, y + 30, ox + 180, oy + 30)
        paths.append(f'<path d="M{sx} {sy} L{ex} {ey}"/>')
        labels.append(f'<text x="{(sx+ex)/2}" y="{sy-12}">{predicate}</text>')
    else:
        sx, sy = x + 90, y + (60 if direction == "down" else 0)
        ex, ey = ox + 90, oy if direction == "down" else oy + 60
        paths.append(f'<path d="M{sx} {sy} L{ex} {ey}"/>')
        labels.append(f'<text x="{sx+12}" y="{(sy+ey)/2}" text-anchor="start">{predicate}</text>')
# 評価から変更への折れ線。評価は問題の修正を意味しない。
paths.append('<path d="M400 400 C230 400 220 295 160 260"/>')
labels.append('<text x="270" y="315">evaluates</text>')
# 変更から構成要素への折れ線。ラベルは中央の問題ノードから離す。
paths.append('<path d="M200 210 H250 V150 H825 V90"/>')
labels.append('<text x="600" y="137">changes</text>')
nodes = []
for key, (x, y, label, en) in positions.items():
    nodes.append(f'<g transform="translate({x} {y})"><rect width="180" height="60"/><text x="90" y="25">{label}</text><text class="en" x="90" y="45">{en}</text></g>')
diagram = '''<figure class="model" aria-labelledby="model-title"><figcaption id="model-title">中心となる関係をたどる</figcaption><div class="model-scroll">
<svg viewBox="0 0 1000 555" role="img" aria-labelledby="graph-title graph-desc"><title id="graph-title">出荷・変更・問題・判断・評価の関係</title><desc id="graph-desc">リリースは製品に属し、変更を出荷する。変更は問題を修正し、構成要素を変更し、判断を実装する。判断は評価を理由とし、評価は変更を評価する。概念は構成要素に適用する。各関係は出典で裏づける。</desc><defs><marker id="arrow" markerWidth="8" markerHeight="8" refX="7" refY="4" orient="auto"><path d="M0,0 L8,4 L0,8 Z"/></marker></defs>
<g class="edges" marker-end="url(#arrow)">''' + "".join(paths) + '</g><g class="labels">' + "".join(labels) + '</g><g class="nodes">' + "".join(nodes) + '''</g><g class="source"><rect x="20" y="480" width="940" height="60"/><text x="490" y="505">出典記事 source → 原本のパス raw</text><text class="en" x="490" y="525">型付きの関係ごとに source・evidence・版と条件を持つ</text></g></svg>
</div><p>図は主要な関係の抜粋です。選択の selects、影響の affects、依存の depends_on と、許容する型の全体は 5 節と YAML に定義しています。</p></figure>'''
body = re.sub(r'<pre><code class="language-text">.*?</code></pre>', lambda _: diagram, body, count=1, flags=re.S)
css = '''
:root{font-family:"Yu Gothic UI","Meiryo",sans-serif;color-scheme:light;--bg:#f1f5f6;--panel:#fff;--ink:#142c36;--muted:#516974;--line:#c9d8df;--accent:#096c73;--soft:#e8f3f3;--code:#eef3f5}
*{box-sizing:border-box}body{margin:0;background:var(--bg);color:var(--ink);font-size:15px;line-height:1.95}a{color:#08616d;text-underline-offset:3px}a:focus-visible,.table-wrap:focus-visible{outline:3px solid #ce9a21;outline-offset:3px}.layout{max-width:1500px;display:grid;grid-template-columns:230px minmax(0,1fr);gap:28px;margin:auto;padding:28px}nav{position:sticky;top:24px;max-height:90vh;overflow:auto;align-self:start;font-size:13px}nav strong{display:block;margin:8px 0 16px}nav ul{padding:0;list-style:none}nav li{margin:10px 0}nav a{text-decoration:none}main{min-width:0;background:var(--panel);border:1px solid var(--line);padding:32px 38px}header{border-bottom:4px solid var(--accent);padding-bottom:25px;margin-bottom:24px}.eyebrow{color:var(--accent);font-size:12px;font-weight:700;letter-spacing:.08em}h1{font-size:31px;line-height:1.6;margin:10px 0 16px}h2{font-size:22px;color:#075c62;border-top:1px solid var(--line);padding-top:25px;margin:44px 0 20px;scroll-margin-top:20px}p{margin:14px 0}code{font-family:Consolas,"Meiryo",monospace;font-size:.88em;background:var(--code);padding:.1em .23em;overflow-wrap:anywhere}pre{white-space:pre-wrap;overflow-wrap:anywhere;background:var(--code);padding:20px;border-left:3px solid var(--accent);font-size:13px;line-height:1.85}pre code{padding:0}.table-wrap{overflow:auto;margin:20px 0 30px;border:1px solid var(--line)}table{width:100%;min-width:780px;border-collapse:collapse;table-layout:fixed;font-size:13px;line-height:1.85}th,td{padding:13px 12px;vertical-align:top;border-bottom:1px solid var(--line);border-right:1px solid var(--line);overflow-wrap:anywhere}th{background:var(--soft);text-align:left;color:#075c62}td:last-child,th:last-child{border-right:0}tr:last-child td{border-bottom:0}.stats{display:grid;grid-template-columns:repeat(4,minmax(0,1fr));gap:12px;margin:24px 0}.stat{padding:14px 16px;background:var(--soft);border-top:3px solid var(--accent)}.stat b{display:block;font-size:28px;line-height:1.3}.stat span{font-size:12px;color:var(--muted)}.notice{padding:13px 17px;background:#fff5dc;border-left:3px solid #ac7b13;color:#674b12;font-size:14px}.model{margin:24px 0;border:1px solid var(--line);padding:18px;background:#fbfdfd}.model figcaption{font-weight:700;margin-bottom:15px}.model-scroll{overflow:auto}.model svg{display:block;width:100%;min-width:780px;height:auto}.model p{font-size:12px;color:var(--muted)}svg text{font-family:"Yu Gothic UI","Meiryo",sans-serif;fill:var(--ink);font-size:17px;text-anchor:middle}.nodes rect{fill:var(--soft);stroke:#4c8991;stroke-width:1.5;rx:5}.nodes .en,.source .en{font-size:13px;fill:var(--muted)}.source rect{fill:#f2f4f6;stroke:var(--line);rx:5}.edges path{stroke:#397a83;stroke-width:1.7;fill:none}marker path{fill:#397a83}.labels text{fill:#245d65;font-size:13px;paint-order:stroke;stroke:#fbfdfd;stroke-width:5px;stroke-linejoin:round}footer{font-size:12px;color:var(--muted);border-top:1px solid var(--line);margin-top:42px;padding-top:16px}li{margin:9px 0}
@media(max-width:900px){.layout{grid-template-columns:1fr;padding:12px;gap:14px}nav{position:static;max-height:none;border:1px solid var(--line);padding:12px 18px}nav strong{margin:0}nav ul{columns:2;margin:8px 0;font-size:12px}nav li{break-inside:avoid;margin:6px 0}main{padding:22px 18px}h1{font-size:25px}h2{font-size:20px}.stats{grid-template-columns:repeat(2,minmax(0,1fr))}.model{padding:12px}}
@media print{body{background:white;font-size:10pt}.layout{display:block;padding:0}nav{display:none}main{border:0;padding:0}h1{font-size:22pt}h2{font-size:15pt;break-after:avoid}.table-wrap{overflow:visible}table{min-width:0;font-size:8pt}th,td{padding:6px}tr{break-inside:avoid}.model{break-inside:avoid}.model svg{min-width:0}.model-scroll{overflow:visible}pre{font-size:8pt;break-inside:avoid}.stats{gap:8px}.stat b{font-size:20pt}p{orphans:3;widows:3}@page{size:A4;margin:17mm}}
'''
document = '''<!doctype html><html lang="ja"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>info-hive のプロジェクト用オントロジー</title><style>''' + css + '''</style></head><body><div class="layout"><nav aria-label="設計書の目次"><strong>設計書の目次</strong>''' + md.toc + '''</nav><main><header><p class="eyebrow">INFO-HIVE / ONTOLOGY DESIGN</p><h1>記事からたどる<br>変更・判断・評価のつながり</h1><p>「何を作り、なぜ選び、どの版で直し、どこまで確かめたか」を、出典と結び付ける設計。</p><div class="stats"><div class="stat"><b>91</b><span>対象記事 / 2026-11-18</span></div><div class="stat"><b>5</b><span>追加する対象の種類</span></div><div class="stat"><b>11</b><span>追加する関係</span></div><div class="stat"><b>23</b><span>試料で検査した関係</span></div></div><p class="notice">状態: 提案。既存の wiki と本番の ontology は未変更です。候補の形式を検査済みであり、関係の真実性・評価の成功を自動で保証する設計ではありません。</p></header>''' + body + '''<footer>最終更新: 2026-11-18（Asia/Tokyo）。<a href="wiki-project-ontology-2026-11-18.md">Markdown</a> / <a href="wiki-project-ontology-2026-11-18.yaml">完全な候補 YAML</a>。この HTML は閲覧用で、外部 JavaScript・送信機能を使用しません。</footer></main></div></body></html>'''
document = document.replace('<b>91</b>', f'<b>{inventory["total_pages"]}</b>')
document = document.replace('<b>5</b>', '<b>6</b>')
document = document.replace('<b>23</b>', f'<b>{verification["pilot"]["typed_edges"]}</b>')
document = document.replace('選択の selects、影響の affects、依存の depends_on と、許容する型の全体は 5 節と YAML に定義しています。', '文書・設定の変更先 artifact、選択 selects、版を特定した影響 affects・依存 depends_on を含む全体の定義は、5 節と YAML に記載しています。')
TARGET.write_text(document, encoding="utf-8")

class CheckHTML(HTMLParser):
    def __init__(self):
        super().__init__()
        self.ids = []
        self.links = []
    def handle_starttag(self, tag, attrs):
        self.ids.extend(v for k, v in attrs if k == "id")
        self.links.extend(v for k, v in attrs if k == "href")

parsed = CheckHTML()
parsed.feed(document)
assert len(parsed.ids) == len(set(parsed.ids))
for link in parsed.links:
    if link.startswith("#"):
        assert unquote(link[1:]) in parsed.ids, link
    elif not urlparse(link).scheme:
        assert (TARGET.parent / unquote(link.split("#")[0])).is_file(), link
assert "<script" not in document
assert text.count("```") % 2 == 0
record = {"date": "2026-11-18", "source_sha256": hashlib.sha256(SOURCE.read_bytes()).hexdigest(),
    "html_sha256": hashlib.sha256(TARGET.read_bytes()).hexdigest(), "html_bytes": TARGET.stat().st_size,
    "local_links": "全件存在", "heading_ids": "重複なし", "code_fences": "対応あり",
    "render_mode": "外部依存なしの静的 HTML。Codex に Monitor がないため返信サーバーや送信 UI は使用しない。"}
(OUT / "render_manifest.json").write_text(json.dumps(record, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
print(json.dumps(record, ensure_ascii=False))
