"""調査の証拠台帳と、日本語レポートの配布物を組み立てる。"""
from pathlib import Path
import hashlib
import json
import re
import shutil
import sys
import urllib.parse
from datetime import datetime, timezone

ROOT = Path(__file__).resolve().parent
DATE = '2026-11-17'
NAME = 'research_report_20261117_llm_wiki_knowledge_graph'
OUT = Path('D:/Users/toshiki/OneDrive - Mokumoku.Net/Documents/LLM_Wiki_Knowledge_Graph_Research_20261117')
OUT.mkdir(parents=True, exist_ok=True)

KEYS = {
 'karpathy': 'https://gist.github.com/karpathy/442a6bf555914893e9891c11519de94f',
 'schema': 'local:wiki/SCHEMA.md',
 'extract': 'local:info-hive-wiki/skills/info-hive/scripts/wiki_graph_extract.py',
 'links': 'https://obsidian.md/help/links',
 'aliases': 'https://obsidian.md/help/aliases',
 'rules': 'https://spacy.io/usage/rule-based-matching/',
 'dep': 'https://spacy.io/api/dependencymatcher',
 'ginza': 'https://megagonlabs.github.io/ginza/',
 'sudachi': 'https://worksapplications.github.io/sudachi.rs/python/api/sudachipy.html',
 'openie': 'https://stanfordnlp.github.io/CoreNLP/openie.html',
 'corenlp': 'https://stanfordnlp.github.io/CoreNLP/',
 'pure': 'https://aclanthology.org/2021.naacl-main.5/',
 'rebel': 'https://aclanthology.org/2021.findings-emnlp.204/',
 'zero': 'https://www.jstage.jst.go.jp/article/jnlp/22/5/22_433/_article/-char/ja/',
 't2kg': 'https://cis.csuohio.edu/~sschung/cis612/KnowledgeGraphTextProcessing_IAAA2017.pdf',
 'graphrag': 'https://microsoft.github.io/graphrag/index/default_dataflow/',
 'graphragpaper': 'https://arxiv.org/abs/2404.16130',
 'neoextract': 'https://neo4j.com/docs/neo4j-graphrag-python/current/user_guide_kg_builder.html',
 'langchain': 'https://reference.langchain.com/python/langchain-neo4j/graph_transformers/llm/LLMGraphTransformer',
 'neoui': 'https://neo4j.com/developer/genai-ecosystem/llm-graph-builder-features/',
 'ntt': 'https://zenn.dev/nttdata_tech/articles/266a6692f85fee',
 'jpeval': 'https://www.jstage.jst.go.jp/article/jsaisigtwo/2025/SWO-067/2025_02/_article/-char/ja/',
 'bench': 'https://arxiv.org/abs/2308.02357',
 'tokyo': 'https://dss.i.u-tokyo.ac.jp/blog/practical-graph-rag-1/',
 'light': 'https://github.com/HKUDS/LightRAG',
 'lightdelete': 'https://github.com/HKUDS/LightRAG/blob/main/docs/ProgramingWithCore.md',
 'issue': 'https://github.com/microsoft/graphrag/issues/2590',
 'neodb': 'https://neo4j.com/docs/getting-started/appendix/graphdb-concepts/',
 'sqlite': 'https://www.sqlite.org/lang_with.html',
 'wal': 'https://www.sqlite.org/wal.html',
 'rdf': 'https://www.w3.org/TR/rdf11-concepts/',
 'prov': 'https://www.w3.org/TR/prov-o/',
 'shacl': 'https://www.w3.org/TR/shacl/',
 'nquads': 'https://www.w3.org/TR/n-quads/',
 'fuseki': 'https://jena.apache.org/documentation/fuseki2/index.html',
 'tdb2': 'https://jena.apache.org/documentation/tdb2/',
 'jsonl': 'https://jsonlines.org/',
 'parquet': 'https://parquet.apache.org/docs/overview/',
 'graphml': 'https://networkx.org/documentation/stable/reference/readwrite/generated/networkx.readwrite.graphml.write_graphml.html',
 'challenge': 'https://challenge.knowledge-graph.jp/2024/rdf.html',
 'outputs': 'https://microsoft.github.io/graphrag/index/outputs/',
}

AUTHORS = {
 'karpathy':('Andrej Karpathy','2026'), 'schema':('to884 / info-hive','2026年11月17日の作業ツリー'),
 'extract':('to884 / info-hive','2026年11月17日の作業ツリー'),
 'links':('Obsidian','更新型資料'), 'aliases':('Obsidian','更新型資料'),
 'rules':('Explosion / spaCy','更新型資料'), 'dep':('Explosion / spaCy','更新型資料'),
 'ginza':('Megagon Labs','更新型資料'), 'sudachi':('Works Applications','更新型資料'),
 'openie':('Stanford NLP Group','更新型資料'), 'corenlp':('Stanford NLP Group','更新型資料'),
 'pure':('Zexuan Zhong・Danqi Chen','2021'),
 'rebel':('Pere-Lluís Huguet Cabot・Roberto Navigli','2021'),
 'zero':('松林優一郎・中山周・乾健太郎','2015'),
 't2kg':('Nattawut Kertkeidkachorn・Ryutaro Ichise','2017'),
 'graphrag':('Microsoft','更新型資料'), 'graphragpaper':('Darren Edge ほか','2024、v2: 2025'),
 'neoextract':('Neo4j','更新型資料'), 'langchain':('LangChain','更新型資料'), 'neoui':('Neo4j','更新型資料'),
 'ntt':('NTT DATA 技術広報','2026'), 'jpeval':('Victor Eiti Yamamoto ほか','2025'),
 'bench':('Nandana Mihindukulasooriya・Sanju Tiwari・Carlos F. Enguix・Kusum Lata','2023'),
 'tokyo':('東京大学DSS','公開年未確認'), 'light':('HKUDS','更新型資料'), 'lightdelete':('HKUDS','更新型資料'),
 'issue':('Pikachu707 / microsoft/graphrag Issue #2590','2026'), 'neodb':('Neo4j','更新型資料'),
 'sqlite':('SQLite','更新型資料'), 'wal':('SQLite','更新型資料'),
 'rdf':('W3C','2014'), 'prov':('W3C','2013'), 'shacl':('W3C','2017'), 'nquads':('W3C','2014'),
 'fuseki':('Apache Jena','更新型資料'), 'tdb2':('Apache Jena','更新型資料'),
 'jsonl':('JSON Lines','更新型資料'), 'parquet':('Apache Parquet','更新型資料'),
 'graphml':('NetworkX','更新型資料'), 'challenge':('ナレッジグラフ推論チャレンジ実行委員会','2024'),
 'outputs':('Microsoft','更新型資料')}

def save_json(path, data):
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2)+'\n', encoding='utf-8')

def write_jsonl(path, rows):
    path.write_text(''.join(json.dumps(r, ensure_ascii=False)+'\n' for r in rows), encoding='utf-8')

def stable(value):
    return hashlib.sha256(value.encode('utf-8')).hexdigest()[:16]

all_rows = []
for filename in ['core_evidence.json', 'context_evidence.json', 'non_llm_evidence.json', 'llm_evidence.json', 'storage_evidence.json', 'additional_evidence.json']:
    all_rows.extend(json.loads((ROOT/filename).read_text(encoding='utf-8-sig')))
rows_by_url = {r['source_url']:r for r in all_rows}
numbers = {k:i+1 for i,k in enumerate(KEYS)}
sources, evidence, claims = [], [], []
for key, url in KEYS.items():
    row = rows_by_url[url]
    sid = stable(url.rstrip('/'))
    if url.startswith('local:'):
        path = Path('C:/Works/info-hive-dev')/url[6:]
        target = path.as_posix()
        digest = hashlib.sha256(path.read_bytes()).hexdigest()
        family = 'info-hive'
    else:
        target, digest = url, None
        family = urllib.parse.urlparse(url).netloc
        if 'microsoft' in url or '2404.16130' in url: family = 'microsoft-graphrag'
        if 'HKUDS/LightRAG' in url: family = 'HKUDS-LightRAG'
        if 'neo4j.com' in url: family = 'neo4j'
    sources.append({'source_id':sid, 'key':key, 'canonical_locator':url.rstrip('/'), 'raw_url':url,
        'url':target, 'title':row['source_title'], 'source_type':row['source_type'],
        'language':row['language'], 'source_family':family, 'accessed_at':DATE,
        'credibility': '原典・仕様・実装の一次資料。性能の一般化は制約欄に従う。',
        'limitations':row['limitations'], 'sha256':digest,
        'author_or_publisher':AUTHORS[key][0], 'publication':AUTHORS[key][1]})
    quote = row['evidence_quote']
    # 同一資料の引用は1箇所のみ保存し、英語は25語以内に収める。
    if row['language'] == 'en' and len(quote.split()) > 25:
        quote = ' '.join(quote.split()[:25])
    eid = stable(sid+quote+row['locator'])
    evidence.append({'evidence_id':eid, 'source_id':sid, 'quote':quote,
        'evidence_type':'direct_quote', 'locator':row['locator'],
        'captured_at':DATE, 'reviewed_paraphrase':row['claim'], 'limitations':row['limitations']})
    claims.append({'claim_id':stable(row['claim']), 'text':row['claim'], 'claim_type':'factual',
        'source_ids':[sid], 'evidence_ids':[eid], 'support_status':'supported',
        'verification_method':'原典の該当箇所を読んだ上での手動照合。短い引用だけではなくlocatorと留保を含めて判定。',
        'qualifiers':row['limitations'], 'report_key':key})

write_jsonl(ROOT/'sources.jsonl', sources)
# 証拠は追記専用。再組み立て時は既存の同一IDを変更しない。
epath = ROOT/'evidence.jsonl'
old_evidence = [json.loads(line) for line in epath.read_text(encoding='utf-8').splitlines()] if epath.exists() else []
old_ids = {row['evidence_id'] for row in old_evidence}
with epath.open('a', encoding='utf-8', newline='\n') as stream:
    for row in evidence:
        if row['evidence_id'] not in old_ids:
            stream.write(json.dumps(row, ensure_ascii=False)+'\n')
write_jsonl(ROOT/'claims.jsonl', claims)
save_json(ROOT/'citation_map.json', {k:{'number':numbers[k], 'source_id':sources[i]['source_id']} for i,k in enumerate(KEYS)})
manifest = {'query':'LLM Wiki の記事からナレッジグラフを作成する方法。日英検索、LLM有無、グラフDB有無。',
    'mode':'standard', 'date_jst':DATE, 'timezone':'Asia/Tokyo',
    'assumptions':['Markdown・frontmatter・wikilinkを持つLLM Wikiを対象とする。',
      'LLM不使用を、完全なモデル不使用・従来NLP・汎用生成LLM不使用に分ける。',
      '今回は調査と設計上の提案のみ。プラグインの実装・リリース・wikiへの取り込みは行わない。'],
    'provider_config':{'primary':'search_service.web_run', 'fallback_reason':'search CLI がPATHに存在しない',
      'github_read':'GitHub MCP fetch', 'parallel_retrieval_agents':3},
    'scope_changes':['リンク、実体、主張のグラフを分ける観点を追加。',
       '削除伝播と出所の維持を保存方式の比較軸に追加。',
       '日本語で書かれた論文と日本語データでの評価を区別。'],
    'limitations':['性能・費用のベンチマークは未実施。','ローカル調査対象は未コミット変更を含む作業ツリー。'],
    'queries_ja':['ナレッジグラフ 構築 LLM 使わない GiNZA 固有表現 関係抽出',
      'ナレッジグラフ 保存 RDF プロパティグラフ 国立国会図書館',
      'site.megagonlabs.github.io ginza 固有表現 係り受け Sudachi',
      'site.anlp.jp ゼロ照応解析 日本語 省略 項構造解析',
      'site.github.com WorksApplications SudachiPy normalized form 辞書',
      'site.neo4j.com LLM Graph Builder schema extraction 日本語',
      'site.neo4j.com/developer "日本語" "グラフ" "LLM"',
      'site.microsoft.com/ja-jp "GraphRAG" "ナレッジ"'],
    'queries_en':['Karpathy LLM Wiki markdown knowledge graph links gist',
      'site.w3.org RDF 1.1 Concepts named graphs provenance PROV SHACL',
      'site.sqlite.org lang_with recursive graph queries WAL one writer',
      'site.w3.org RDF 1.1 concepts dataset named graphs Turtle N Quads',
      'site.jena.apache.org documentation fuseki2 transaction database TDB2',
      'site.spacy.io usage rule based matching entityruler dependency matcher',
      'site.aclanthology.org A Frustratingly Easy Approach for Entity and Relation Extraction',
      '"T2KG" "An End-to-End System" knowledge graph',
      'site.microsoft.github.io/graphrag indexing default dataflow entity relationship extraction provenance',
      'site.github.com HKUDS LightRAG document deletion provenance graph extraction',
      'Text2KGBench benchmark ontology knowledge graph generation large language models hallucination precision recall paper'],
    'source_count':len(sources), 'documents_output':str(OUT), 'repository_output':str(ROOT),
    'skill_validation_note':'付属バリデーターは英語見出し・空白単語数を前提とするため、検証用コピーの見出しだけを変換。日本語の長さは別途文字数を記録する。',
    'citation_verification_note':'URL到達性と意味的支持は別。後者は手動で原典と留保を照合した。',
    'independent_review':{'model':'Claude Opus 5.5','status':'not_completed','reason':'5-hour usage limit before generation','attempts':1}}
save_json(ROOT/'run_manifest.json', manifest)

def cite(match):
    key = match.group(1)
    return f'[{numbers[key]}]({sources[numbers[key]-1]["url"]})'

if (ROOT/'report_draft.md').exists():
    report = (ROOT/'report_draft.md').read_text(encoding='utf-8')
    report = re.sub(r'\{@([a-z0-9_]+)\}', cite, report)
    bib = []
    for source in sources:
        n = numbers[source['key']]
        author = source['author_or_publisher']
        publication = source['publication']
        bib.append(f'[{n}] {author} ({publication}). "{source["title"]}". 一次資料・{source["source_type"]}。 [原典]({source["url"]}) （参照日: {DATE}、言語: {source["language"]}）。')
    report = report.replace('{BIBLIOGRAPHY}', '\n\n'.join(bib))
    if re.search(r'\{@|\{BIBLIOGRAPHY\}', report): raise ValueError('未解決の参照')
    (ROOT/(NAME+'.md')).write_text(report, encoding='utf-8')
    # 英語見出しを前提とする付属チェック専用。配布物は日本語版。
    aliases = {'要旨':'Executive Summary','調査の範囲と前提':'Introduction', '主要な調査結果':'Main Analysis',
      '方式を組み合わせるときの判断':'Synthesis', '反証・注意点':'Counterevidence Register',
      '限界と未確認事項':'Limitations', 'info-hive への提案':'Recommendations',
      '出典一覧':'Bibliography', '調査方法と証拠の管理':'Methodology', '主要主張と根拠の対応':'Claims-Evidence Table'}
    validation = report
    for jp,en in aliases.items(): validation = validation.replace('## '+jp+'\n', '## '+en+'\n')
    (ROOT/'validation_report.md').write_text(validation, encoding='utf-8')
    cited = set(re.findall(r'\[(\d+)\]\(', report.split('## 出典一覧')[0]))
    missing = set(str(n) for n in numbers.values())-cited
    print(json.dumps({'report_chars':len(report),'body_chars':len(report.split('## 出典一覧')[0]),'sources':len(sources),'unused_sources':sorted(missing)},ensure_ascii=False))
    for filename in [NAME+'.md','sources.jsonl','evidence.jsonl','claims.jsonl','run_manifest.json','citation_map.json']:
        shutil.copy2(ROOT/filename, OUT/filename)
else:
    print(json.dumps({'sources':len(sources),'evidence':len(evidence),'status':'証拠台帳を初期化'},ensure_ascii=False))
