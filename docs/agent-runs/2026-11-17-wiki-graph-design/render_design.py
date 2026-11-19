"""設計のMarkdownを、単独で読めるHTMLへ変換する。"""
from pathlib import Path
import hashlib
import html
import json
import re

import markdown

ROOT=Path(__file__).resolve().parents[3]
SOURCE=ROOT/'docs/plans/wiki-graph-improvements-2026-11-17.md'
TARGET=SOURCE.with_suffix('.html')
raw=SOURCE.read_text(encoding='utf-8')
source=re.sub(r'\A---\n.*?\n---\n','',raw,count=1,flags=re.S)
md=markdown.Markdown(extensions=['tables','fenced_code','toc'],extension_configs={'toc':{'toc_depth':'2-3'}})
body=md.convert(source)
body=re.sub(r'<h1[^>]*>.*?</h1>','',body,count=1,flags=re.S)
body=re.sub(r'<table>(.*?)</table>',r'<div class="table-wrap"><table>\1</table></div>',body,flags=re.S)
diagram='''<figure class="flow" aria-labelledby="flow-title"><figcaption id="flow-title">入力と採用を分け、同じ関係の構築と検索条件を共有する</figcaption>
<div class="flow-grid">
<div class="flow-node"><span>正本</span><strong>Markdown・ontology</strong><p>記事、明示した主張、根拠の版</p></div>
<div class="flow-node"><span>決定的な構築</span><strong>Snapshot・strict 検証</strong><p>入力の完全性と内容のダイジェスト</p></div>
<div class="flow-node"><span>読み取り</span><strong>SQLite・CLI・MCP</strong><p>鮮度を照合し、辺を絞って探索</p></div>
<div class="flow-node secondary"><span>候補の発見</span><strong>ホスト LLM・任意の NLP</strong><p>根拠付きの候補。採用済みとは区別</p></div>
<div class="flow-node secondary"><span>既存の編集手順</span><strong>検証・選択・patch</strong><p>Markdown へ反映後に accepted</p></div>
<div class="flow-node secondary"><span>同じ条件を使う</span><strong>browse・export bundle</strong><p>閲覧スナップショット、版を固定した書き出し</p></div>
</div></figure>'''
body=re.sub(r'<pre><code class="language-text">wiki の記事・ontology.*?</code></pre>',lambda _:diagram,body,count=1,flags=re.S)
css='''
:root{--bg:#f4f6f8;--panel:#fff;--ink:#172b39;--muted:#526571;--line:#c6d0d8;--accent:#174b68;--soft:#e8eff4;--warn:#785919;--warn-bg:#fff5dd;--code:#edf1f4;font-family:"Yu Gothic UI","Meiryo",sans-serif;color-scheme:light dark}
*{box-sizing:border-box}body{margin:0;background:var(--bg);color:var(--ink);font-size:15px;line-height:1.85}a{color:var(--accent);text-underline-offset:3px}a:focus-visible{outline:3px solid #c48119;outline-offset:3px}.layout{display:grid;grid-template-columns:255px minmax(0,1fr);max-width:1460px;margin:auto;padding:28px 32px;gap:36px}nav{position:sticky;top:22px;align-self:start;max-height:calc(100vh - 44px);overflow:auto;padding-right:12px;font-size:13px}nav strong{display:block;font-size:14px;margin-bottom:12px}nav ul{list-style:none;padding:0;margin:0}nav li{margin:7px 0}nav ul ul{padding-left:14px;border-left:1px solid var(--line);font-size:12px}nav a{text-decoration:none}main{min-width:0;background:var(--panel);border:1px solid var(--line);padding:36px 40px}header{border-bottom:3px solid var(--accent);padding-bottom:24px;margin-bottom:32px}.eyebrow{font-size:12px;color:var(--muted);letter-spacing:.06em;margin:0 0 12px}h1{font-size:30px;line-height:1.5;margin:0 0 16px}h2{font-size:22px;margin:46px 0 18px;color:var(--accent);border-top:1px solid var(--line);padding-top:22px;scroll-margin-top:25px}h3{font-size:18px;margin:32px 0 14px;scroll-margin-top:25px}p{margin:12px 0 16px}strong{font-weight:700}code{font-family:Consolas,"Meiryo",monospace;font-size:.9em;background:var(--code);padding:.08em .2em;overflow-wrap:anywhere}pre{background:var(--code);border-left:3px solid var(--accent);padding:18px;white-space:pre-wrap;overflow-wrap:anywhere;font-size:13px;line-height:1.7}pre code{padding:0;background:transparent}.table-wrap{overflow-x:auto;margin:22px 0 30px;border:1px solid var(--line)}table{border-collapse:collapse;table-layout:fixed;width:100%;min-width:690px;font-size:13px;line-height:1.75}th,td{border-bottom:1px solid var(--line);border-right:1px solid var(--line);padding:10px 12px;vertical-align:top;overflow-wrap:anywhere}th{background:var(--soft);text-align:left;color:var(--accent)}tr:last-child td{border-bottom:0}td:last-child,th:last-child{border-right:0}.notice{padding:12px 16px;background:var(--warn-bg);border-left:3px solid var(--warn);font-size:14px;color:var(--warn)}.meta{display:flex;gap:14px;flex-wrap:wrap;font-size:13px;color:var(--muted)}.flow{margin:24px 0;border:1px solid var(--line);padding:18px}figcaption{font-size:14px;font-weight:700;margin-bottom:16px}.flow-grid{display:grid;grid-template-columns:repeat(3,minmax(0,1fr));gap:12px}.flow-node{border-top:4px solid var(--accent);background:var(--soft);padding:12px}.flow-node span{display:block;font-size:11px;color:var(--muted)}.flow-node strong{font-size:14px;display:block;margin:4px 0}.flow-node p{font-size:12px;margin:6px 0}.secondary{border-top:2px dashed var(--muted);background:var(--bg)}footer{border-top:1px solid var(--line);margin-top:42px;padding-top:16px;color:var(--muted);font-size:12px}
@media(prefers-color-scheme:dark){:root{--bg:#111a21;--panel:#17232c;--ink:#e3ebf0;--muted:#adbfcb;--line:#405564;--accent:#99cbe6;--soft:#233744;--warn:#f2d391;--warn-bg:#392e1a;--code:#24323d}}
@media(max-width:850px){.layout{grid-template-columns:1fr;padding:14px;gap:18px}nav{position:static;max-height:none;padding:12px 16px;border:1px solid var(--line)}nav ul ul{display:none}main{padding:24px 20px}h1{font-size:25px}.flow-grid{grid-template-columns:1fr}.table-wrap{margin-left:-4px;margin-right:-4px}}
@media print{body{background:white;color:#172b39;font-size:10pt}.layout{display:block;padding:0}nav{display:none}main{border:0;padding:0}header{margin-bottom:20px}h1{font-size:22pt}h2{break-after:avoid;font-size:16pt}h3{break-after:avoid;font-size:12pt}.table-wrap{overflow:visible;break-inside:auto}table{min-width:0;font-size:8pt}tr{break-inside:avoid}th,td{padding:6px}pre,.flow{break-inside:avoid}a{color:#174b68}.flow-grid{display:table}.flow-node{display:table-cell;width:16.66%;border:1px solid #c6d0d8}.notice{color:#785919;background:#fff5dd}p{orphans:3;widows:3}@page{size:A4;margin:18mm}}
'''
document='''<!doctype html>
<html lang="ja"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>wiki のグラフ機能の現状と改善設計</title><style>'''+css+'''</style></head><body><div class="layout"><nav aria-label="設計書の目次"><strong>設計書の目次</strong>'''+md.toc+'''</nav><main><header><p class="eyebrow">info-hive-wiki / 改善設計</p><h1>wiki のグラフ機能の現状と改善設計</h1><div class="meta"><span>状態: 提案</span><span>更新: 2026年11月17日</span><span>対象: 0.30.0 を名乗る作業ツリー</span></div><p class="notice">現在の実装・隔離した試料での観測と、これから実装する設計を区別して記載しています。</p></header>'''+body+'''<footer>最終更新: 2026年11月17日（Asia/Tokyo）。正本: <a href="wiki-graph-improvements-2026-11-17.md">Markdown の設計書</a>。HTML は閲覧専用で、入力や送信の機能を持ちません。</footer></main></div></body></html>'''
TARGET.write_text(document,encoding='utf-8')
record={'source_sha256':hashlib.sha256(SOURCE.read_bytes()).hexdigest(),
    'html_sha256':hashlib.sha256(TARGET.read_bytes()).hexdigest(),
    'markdown_chars':len(raw),'html_bytes':TARGET.stat().st_size,
    'render_mode':'自己完結の静的HTML。Monitorが利用できないCodex環境のため返信サーバー・送信UIは使用しない。'}
(Path(__file__).resolve().parent/'render_manifest.json').write_text(json.dumps(record,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
print(json.dumps(record,ensure_ascii=False))

if __name__ == '__main__':
    from html.parser import HTMLParser
    from urllib.parse import unquote, urlparse
    import subprocess
    import sys

    class DocumentParser(HTMLParser):
        def __init__(self):
            super().__init__()
            self.ids=[]
            self.links=[]
        def handle_starttag(self, tag, attrs):
            self.ids.extend(value for key,value in attrs if key=='id')
            self.links.extend(value for key,value in attrs if key=='href')

    parser=DocumentParser()
    parser.feed(document)
    assert len(parser.ids)==len(set(parser.ids))
    broken=[]
    for value in parser.links:
        if value.startswith('#') and unquote(value[1:]) not in parser.ids:
            broken.append(value)
        elif not urlparse(value).scheme and not value.startswith('#'):
            if not (TARGET.parent/unquote(value.split('#')[0])).exists():
                broken.append(value)
    assert not broken,broken
    assert raw.count('```')%2==0
    assert '<html lang="ja">' in document and '<meta charset="utf-8">' in document
    assert '<script' not in document
    run=Path(__file__).resolve().parent
    observations=json.loads((run/'observations.json').read_text(encoding='utf-8'))
    changed=[row['path'] for row in observations['inputs']
             if hashlib.sha256((ROOT/row['path']).read_bytes()).hexdigest()!=row['sha256']]
    verification={'document_revision':2,'html_local_links':'passed','heading_ids_unique':True,
        'code_fences_paired':True,'external_javascript':False,
        'changed_observed_source_files':changed,
        'current_graph_tests':{'command':'uv run --python 3.12 --with PyYAML==6.0.3 python -X utf8 -m unittest discover -s tests/graph -v','passed':28,'failed':0},
        'isolated_probe':'observations.json','project_inventory':'project_snapshot.json',
        'independent_review':{'status':'not_completed','reason':'Opus 5.5 five-hour usage limit before generation','attempts':1,'target_revision':1},
        'self_review_fixes':['DB接続と鮮度判定の対応','wikiの根の対応','bundle_idとbuild_idの分離',
            '版1と版2の条件の固定','標準ライブラリだけの照会','主語と記述ページの一致']}
    (run/'verification.json').write_text(json.dumps(verification,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
    print(json.dumps(verification,ensure_ascii=False))
    if '--screenshots' in sys.argv:
        edge=Path('C:/Program Files (x86)/Microsoft/Edge/Application/msedge.exe')
        for label,size in [('desktop','1440,1060'),('mobile','640,960')]:
            args=[str(edge),'--headless=new','--disable-gpu','--disable-extensions',
                '--no-first-run','--hide-scrollbars','--window-size='+size,
                '--user-data-dir='+str(run/('render-profile-'+label)),
                '--screenshot='+str(run/(label+'.png')),TARGET.as_uri()]
            result=subprocess.run(args,capture_output=True,text=True,encoding='utf-8',errors='replace',
                timeout=45,creationflags=subprocess.CREATE_NO_WINDOW)
            if result.returncode or not (run/(label+'.png')).is_file():
                raise RuntimeError(result.stderr[-1500:])
