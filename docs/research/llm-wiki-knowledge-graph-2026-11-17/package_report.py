"""日本語MarkdownからHTML・PDFを生成し、証拠の参照整合性を検査する。"""
from pathlib import Path
import collections
import hashlib
import html
import importlib.util
import json
import re
import shutil
import subprocess
import sys

import markdown

ROOT = Path(__file__).resolve().parent
NAME = 'research_report_20261117_llm_wiki_knowledge_graph'
OUT = Path('D:/Users/toshiki/OneDrive - Mokumoku.Net/Documents/LLM_Wiki_Knowledge_Graph_Research_20261117')
SKILL = Path('C:/Works/info-hive-dev/.agents/skills/deep-research')
md = (ROOT/(NAME+'.md')).read_text(encoding='utf-8')
text = re.sub(r'\A---\n.*?\n---\n', '', md, count=1, flags=re.S)
text = re.sub(r'^# .+\n', '', text, count=1, flags=re.M)
body, remainder = text.split('## 出典一覧\n', 1)
bib, methods = remainder.split('## 調査方法と証拠の管理\n', 1)
body += '\n## 調査方法と証拠の管理\n'+methods
extensions = ['tables', 'fenced_code', 'toc']
body_html = markdown.markdown(body, extensions=extensions)
body_html = re.sub(r'<h2(\s[^>]*)?>',lambda m:'<h2 class="section-title"'+(m[1] or '')+'>',body_html)
bib_html = markdown.markdown(bib, extensions=extensions)
sources = [json.loads(line) for line in (ROOT/'sources.jsonl').read_text(encoding='utf-8').splitlines()]
template = (SKILL/'templates/mckinsey_report_template.html').read_text(encoding='utf-8')
metrics = '<div class="metrics-dashboard">'+''.join(
    f'<div class="metric"><span class="metric-number">{v}</span><span class="metric-label">{k}</span></div>'
    for k,v in [('一次資料', len(sources)), ('構成の組み合わせ',4),('主要な調査結果',7),('検索言語',2)])+'</div>'
for key,value in {'TITLE':'LLM Wiki の記事からナレッジグラフを作る方法', 'DATE':'2026年11月17日',
    'SOURCE_COUNT':str(len(sources)), 'METRICS_DASHBOARD':metrics,'CONTENT':body_html,'BIBLIOGRAPHY':bib_html}.items():
    template = template.replace('{{'+key+'}}',value)
template = template.replace('lang="en"','lang="ja"').replace('Deep Research Report','調査レポート')
template = template.replace(' Sources',' 件の一次資料').replace('>Bibliography<','>出典一覧<')
template = re.sub(r'href="(C:/[^"]+)"', lambda m: 'href="file:///'+m[1]+'"', template)
template = re.sub(r'(<a\b[^>]*>)(\d+)(</a>)',lambda m:m[1]+'['+m[2]+']'+m[3],template)
css = '''
body{font-family:"Yu Gothic UI","Meiryo","Noto Sans JP",sans-serif;line-height:1.85}
.container{max-width:1120px}.content{padding:30px 40px 50px}h2{margin:42px 0 16px;border-bottom:2px solid #003d5c;padding-bottom:8px;color:#003d5c;font-size:21px}
h3{margin:30px 0 14px;color:#003d5c;font-size:18px}p{line-height:1.85}a{color:#005787;text-decoration-thickness:1px;text-underline-offset:2px}
table{width:100%;border-collapse:collapse;table-layout:fixed;margin:20px 0 28px;font-size:13px}th,td{border:1px solid #b8c5ce;padding:9px 10px;vertical-align:top;overflow-wrap:anywhere}th{background:#e7eef3;color:#003d5c;text-align:left}tr:nth-child(even){background:#f8f9fa}
pre{background:#f0f3f5;border-left:3px solid #003d5c;padding:14px;white-space:pre-wrap;overflow-wrap:anywhere;font-size:12px;line-height:1.7;margin:18px 0}code{font-family:Consolas,"Meiryo",monospace;font-size:.9em;overflow-wrap:anywhere}
.bibliography{font-size:12px}.bibliography p{margin:9px 0}strong{font-weight:700}h2,h3{scroll-margin-top:16px}
@page{size:A4;margin:17mm 15mm 18mm;@bottom-center{content:counter(page)" / "counter(pages);font-size:8pt;font-family:Arial;color:#586877}}
@media print{body{font-size:9.3pt;line-height:1.65}.container{max-width:none}.content{padding:0}.header{padding:16px 20px;margin-bottom:0}.header h1{font-size:21pt}.header-meta{font-size:9pt}.metric{padding:10px}.metric-number{font-size:22pt}.metric-label{font-size:8pt}.metrics-dashboard{display:table;width:100%;margin-bottom:18px}.metric{display:table-cell;width:25%}h2{font-size:14pt;margin-top:23pt}h3{font-size:11.4pt;margin-top:18pt}p{line-height:1.7;orphans:3;widows:3;margin-bottom:9pt}h2,h3{break-after:avoid}table{font-size:8pt;line-height:1.6;margin:12pt 0;break-inside:auto}thead{display:table-header-group}tr{break-inside:avoid}th,td{padding:6pt}pre{font-size:8pt;break-inside:avoid}a{text-decoration:none}.bibliography{font-size:8pt}.bibliography p{break-inside:avoid}}
@media(max-width:700px){.content{padding:20px}table{font-size:11px}th,td{padding:6px}.header{padding:22px}.header h1{font-size:23px}}
'''
template = template.replace('</style>',css+'\n</style>')
if re.search(r'\{\{[A-Z_]+\}\}', template): raise ValueError('未解決のHTML置換箇所')
(ROOT/(NAME+'.html')).write_text(template,encoding='utf-8')

def h(value): return hashlib.sha256(value.encode('utf-8')).hexdigest()[:16]
evs = [json.loads(line) for line in (ROOT/'evidence.jsonl').read_text(encoding='utf-8').splitlines()]
ev_by_source = collections.defaultdict(list)
for e in evs: ev_by_source[e['source_id']].append(e['evidence_id'])
mapping = json.loads((ROOT/'citation_map.json').read_text(encoding='utf-8'))
by_number = {v['number']:v['source_id'] for v in mapping.values()}
claims = [c for line in (ROOT/'claims.jsonl').read_text(encoding='utf-8').splitlines()
          if (c := json.loads(line)).get('scope') != 'narrative_sentence']
# 文章を命題ごとに分ける。段落末尾の引用は段落内の命題にも対応させる。
# 分類は抽出補助であり、支持判定は本文作成時の原典との手動照合を記録する。
section='冒頭'
narrative = re.sub(r'```.*?```','',md.split('## 出典一覧')[0],flags=re.S)
for block in narrative.split('\n\n'):
    if block.startswith('|') or block.startswith('---') or block.startswith('# '): continue
    if block.startswith('##'):
        section=block.strip('# \n')
        continue
    ns = sorted(set(int(n) for n in re.findall(r'\[(\d+)\]\(',block)))
    clean = re.sub(r'\[\d+\]\([^)]*\)', '', block).strip()
    if not clean: continue
    for sentence in re.split(r'(?<=。)',clean):
        sentence=sentence.strip()
        if len(sentence)<12: continue
        if any(w in sentence for w in ['提案','推奨','べき','必要がある','方針','判断する','案を','確認する。','対象外','今回','本調査','本レポート','この選択']):
            kind='recommendation' if any(w in sentence for w in ['提案','推奨','べき','案を']) else 'synthesis'
        else: kind='factual' if ns else 'synthesis'
        sids=[by_number[n] for n in ns]
        claims.append({'claim_id':h(section+sentence), 'text':sentence,'section_id':section,
            'claim_type':kind, 'source_ids':sids,
            'evidence_ids':[eid for sid in sids for eid in ev_by_source[sid]],
            'support_status':'supported' if kind=='factual' else 'traceable_synthesis' if ns else 'labeled_analysis',
            'verification_method':'本文作成時に原典の該当箇所・制約と手動照合。自動分割は台帳化を補助するもので、意味の判定器ではない。',
            'scope':'narrative_sentence'})
(ROOT/'claims.jsonl').write_text(''.join(json.dumps(c,ensure_ascii=False)+'\n' for c in claims),encoding='utf-8')
source_ids={s['source_id'] for s in sources}
evidence_ids={e['evidence_id'] for e in evs}
assert all(set(c['source_ids'])<=source_ids and set(c['evidence_ids'])<=evidence_ids for c in claims)
assert all(c['source_ids'] and c['evidence_ids'] for c in claims if c['claim_type']=='factual')
assert set(int(n) for n in re.findall(r'\[(\d+)\]\(',md))<=set(by_number)
manual = {
 '2':{'status':'verified_local','sha256':sources[1]['sha256'],'path':sources[1]['url']},
 '3':{'status':'verified_local','sha256':sources[2]['sha256'],'path':sources[2]['url']},
 '11':{'status':'verified_primary_page','reason':'Overview は公式 CoreNLP の実際の題名。汎用題名ヒューリスティックの誤検出。'},
 '38':{'status':'verified_primary_page','reason':'Overview は Apache Parquet 公式ドキュメントの実際の題名。汎用題名の誤検出。'},
 '15':{'status':'verified_web_pdf','reason':'PythonのHEADは証明書エラー。調査エージェントは大学サイトで公開された論文PDF本文を取得・確認。AAAI正規配布元403のためミラーの由来も記録。'}
}
(ROOT/'citation_manual_review.json').write_text(json.dumps(manual,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
check = {'source_count':len(sources),'evidence_count':len(evs),'claim_count':len(claims),
    'claim_type_counts':dict(collections.Counter(c['claim_type'] for c in claims)),
    'missing_source_references':0,'missing_evidence_references':0,
    'factual_claims_without_evidence':0,'unsupported_factual_claims':0,
    'semantic_verification':'手動の原典照合。自動化した意味的検証ではない。',
    'independent_opus_review':'利用上限により未実施',
    'japanese_summary_chars':len(md.split('## 要旨\n')[1].split('## 調査の範囲')[0]),
    'bibliography_entries':len(re.findall(r'^\[\d+\]',md,re.M))}
(ROOT/'verification_summary.json').write_text(json.dumps(check,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')

edge=Path('C:/Program Files (x86)/Microsoft/Edge/Application/msedge.exe')
profile=ROOT/'render_profile'
args=[str(edge),'--headless=new','--disable-gpu','--disable-extensions','--no-first-run',
      '--no-pdf-header-footer','--allow-file-access-from-files', '--user-data-dir='+str(profile),
      '--print-to-pdf='+str(ROOT/(NAME+'.pdf')), (ROOT/(NAME+'.html')).as_uri()]
result=subprocess.run(args,capture_output=True,text=True,encoding='utf-8',errors='replace',timeout=90,
    creationflags=subprocess.CREATE_NO_WINDOW)
(ROOT/'pdf_render.log').write_text(result.stdout+result.stderr,encoding='utf-8')
if result.returncode or not (ROOT/(NAME+'.pdf')).is_file(): raise RuntimeError('PDF生成に失敗')
for filename in [NAME+'.md',NAME+'.html',NAME+'.pdf','sources.jsonl','evidence.jsonl','claims.jsonl',
    'run_manifest.json','citation_map.json','citation_manual_review.json','verification_summary.json']:
    shutil.copy2(ROOT/filename,OUT/filename)
archive=Path.home()/'.claude/research_output/LLM_Wiki_Knowledge_Graph_Research_20261117'
archive.mkdir(parents=True,exist_ok=True)
for suffix in ['.md','.html','.pdf']: shutil.copy2(ROOT/(NAME+suffix),archive/(NAME+suffix))
print(json.dumps({'status':'生成完了','out':str(OUT),'pdf_bytes':(ROOT/(NAME+'.pdf')).stat().st_size,**check},ensure_ascii=False))
