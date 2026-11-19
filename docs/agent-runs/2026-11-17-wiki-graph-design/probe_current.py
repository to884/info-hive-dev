"""グラフ機能の現状を、実 wiki を変更せずに確認する。"""
from pathlib import Path
import collections
import hashlib
import json
import sqlite3
import subprocess
import sys
import tempfile
from unittest import mock

ROOT = Path(__file__).resolve().parents[3]
SCRIPTS = ROOT/'info-hive-wiki/skills/info-hive/scripts'
sys.path.insert(0, str(SCRIPTS))
import wiki_graph_extract as extract
import wiki_graph_lint as lint
import wiki_graph_query as query

OUT = Path(__file__).resolve().parent

def record(name):
    p=SCRIPTS/name
    return {'path':p.relative_to(ROOT).as_posix(),'sha256':hashlib.sha256(p.read_bytes()).hexdigest()}

observations={'scope':'0.30.0 を名乗る未コミット変更を含む作業ツリー。外部モデルは呼ばない。',
    'inputs':[record(n) for n in ['wiki_graph_extract.py','wiki_graph_lint.py','wiki_graph_query.py',
        'wiki_graph_common.py','wiki_pages.py','wiki_mcp_server.py','wiki_browse_core.py']],
    'head':subprocess.check_output(['git','-C',str(ROOT/'info-hive-wiki'),'rev-parse','HEAD'],text=True).strip()}

def page(wiki,rel,metadata,body=''):
    import yaml
    p=wiki/rel
    p.parent.mkdir(parents=True,exist_ok=True)
    p.write_text('---\n'+yaml.safe_dump(metadata,allow_unicode=True,sort_keys=False)+'---\n\n'+body+'\n',encoding='utf-8')

with tempfile.TemporaryDirectory(prefix='wiki-graph-design-') as temporary:
    sandbox=Path(temporary).resolve()
    wiki=sandbox/'wiki'
    (wiki/'graph').mkdir(parents=True)
    (wiki/'SCHEMA.md').write_text('# fixture\n',encoding='utf-8')
    (wiki/'graph/ontology.yaml').write_bytes((ROOT/'info-hive-wiki/skills/info-hive/assets/ontology.yaml.template').read_bytes())
    page(wiki,'sources/根拠.md',{'type':'source','title':'根拠','raw':'raw/根拠.md'},'A は C を利用する。C は B を利用する。')
    page(wiki,'concepts/A.md',{'type':'concept','title':'A','graph':{'node_id':'concept:a','aliases':['エー'],
        'relationships':[{'predicate':'depends_on','object':'concept:b','source':'根拠',
            'evidence':'本文にない引用','confidence':'high','status':'proposed'},
            {'predicate':'depends_on','object':'concept:c','source':'根拠','evidence':'A は C を利用する。',
             'confidence':'high','status':'current','valid_to':'2000-01-01'}]}},'[[C]]')
    page(wiki,'concepts/B.md',{'type':'concept','title':'B','graph':{'node_id':'concept:b'}})
    page(wiki,'concepts/C.md',{'type':'concept','title':'C','graph':{'node_id':'concept:c','relationships':[
        {'predicate':'depends_on','object':'concept:b','source':'根拠','evidence':'C は B を利用する。',
         'confidence':'high','status':'current'}]}})
    ontology=extract.read_ontology(wiki/'graph/ontology.yaml')
    pages=extract.collect_pages(wiki)
    diagnostics=[]
    nodes,pids,aliases=extract.build_nodes(pages,ontology,diagnostics)
    edges=extract.build_edges(pages,pids,diagnostics)
    extract.write_sqlite(wiki/'graph',nodes,aliases,edges)
    observations['queries']={
        'neighbors_statuses':[e['status'] for slot in query.run_query(wiki,'neighbors',node='concept:a')['neighbors'] for e in slot['out']],
        'path_statuses':[e['status'] for e in query.run_query(wiki,'path',start='concept:a',goal='concept:b')['path_edges']],
        'expired_edge_returned':any(e['metadata_json'].find('2000-01-01')>=0 for e in query.run_query(wiki,'edges',subject='concept:a')['edges']),
        'alias_as_node':'not_attempted'}
    try: query.run_query(wiki,'neighbors',node='エー')
    except Exception as exc: observations['queries']['alias_as_node']={'error':type(exc).__name__,'message':str(exc)}
    old_edge=next(e for e in edges if e['status']=='proposed')
    status_changed=dict(old_edge)
    candidate=next(p for p in pages if p['slug']=='A')['meta']['graph']['relationships'][0]
    candidate['status']='current'
    new_edges=extract.build_edges(pages,pids)
    observations['identity']={'id_before':old_edge['id'],'id_after_status_change':next(e for e in new_edges if e['evidence']=='本文にない引用')['id']}
    candidate['status']='proposed'

    missing={'predicate':'depends_on','object':'concept:b','source':'根拠','evidence':'本文にない引用','valid_from':'日付ではない'}
    candidate.clear();candidate.update(missing)
    findings=lint.lint(pages,ontology)
    observations['lint']={'missing_status_findings':findings['invalid_status'],
        'missing_confidence_findings':findings['invalid_confidence'],
        'missing_quote_findings':findings['missing_evidence'],
        'date_specific_categories':[k for k in findings if 'valid' in k or 'date' in k],
        'ordinary_lint_summary':findings['summary'],
        'optional_decide_exists':hasattr(lint,'decide_evidence')}

    page(wiki,'concepts/不正.md',{'type':'concept','title':'不正','graph':{'relationships':[
        {'predicate':'not_in_ontology','object':'concept:b'}]}})
    (wiki/'concepts/読めない.md').write_bytes(b'\xff\xfe\x80')
    cp=subprocess.run([sys.executable,'-X','utf8',str(SCRIPTS/'wiki_graph_extract.py'),str(wiki)],
        capture_output=True,text=True,encoding='utf-8')
    conn=sqlite3.connect((wiki/'graph/graph.sqlite').as_uri()+'?mode=ro',uri=True)
    observations['permissive_compile']={'exit_code':cp.returncode,'stderr':cp.stderr,
        'unknown_predicate_count':conn.execute("SELECT count(*) FROM edges WHERE predicate='not_in_ontology'").fetchone()[0],
        'unreadable_page_count':conn.execute("SELECT count(*) FROM nodes WHERE slug='読めない'").fetchone()[0],
        'tables':[r[0] for r in conn.execute("SELECT name FROM sqlite_master WHERE type='table'")]}
    conn.close()
    (wiki/'concepts/B.md').unlink()
    observations['deletion_before_rebuild']={'returned_node':query.run_query(wiki,'neighbors',node='concept:b')['node']['path']}

    target=sandbox/'publication';target.mkdir()
    for name in extract.PUBLISH_ORDER: (target/name).write_text('old',encoding='utf-8')
    stages={name:target/(name+'.staged') for name in extract.PUBLISH_ORDER}
    for p in stages.values(): p.write_text('new',encoding='utf-8')
    original=extract.common.replace_atomically
    def fail_second(temp,dest):
        if dest.name=='nodes.jsonl': raise PermissionError('injected failure')
        return original(temp,dest)
    with mock.patch.object(extract.common,'replace_atomically',side_effect=fail_second):
        try: extract.publish_outputs(target,stages)
        except PermissionError: pass
    observations['partial_publish']={name:(target/name).read_text(encoding='utf-8') for name in extract.PUBLISH_ORDER}

real=ROOT/'wiki/graph'
observations['project_jsonl_inventory']={}
for filename in ['nodes.jsonl','edges.jsonl']:
    p=real/filename
    rows=[json.loads(line) for line in p.read_text(encoding='utf-8').splitlines() if line.strip()]
    observations['project_jsonl_inventory'][filename]={'count':len(rows),'sha256':hashlib.sha256(p.read_bytes()).hexdigest()}
    if filename=='edges.jsonl':
        observations['project_jsonl_inventory'][filename]['predicates']=dict(collections.Counter(row['predicate'] for row in rows))
        observations['project_jsonl_inventory'][filename]['methods']=dict(collections.Counter(row['extraction_method'] for row in rows))
observations['source_files_unchanged_during_probe']=all(record(Path(v['path']).name)['sha256']==v['sha256'] for v in observations['inputs'])
(OUT/'observations.json').write_text(json.dumps(observations,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
print(json.dumps(observations,ensure_ascii=False,indent=2))
