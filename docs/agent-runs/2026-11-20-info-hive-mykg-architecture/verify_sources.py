import hashlib,json,subprocess,sys
from pathlib import Path
root=Path('C:/Works/info-hive-dev');out=Path(__file__).parent
sys.path.insert(0,'C:/UserData/toshiki/.codex/plugins/cache/info-hive/wiki/0.39.0/skills/info-hive/scripts')
import wiki_apply as published
minimal={key:'0'*64 for key in ('SCHEMA.md','index.md','log.md','graph/ontology.yaml','graph/graph.sqlite','ontology/definition.json')}
try:published.verify_files(minimal)
except published.PublicationError:rejected=True
else:rejected=False
assert rejected,'Ossie なしの候補が拒まれない'
assert len([key for key in published.REQUIRED if key.startswith('ontology/ossie/')])==6
manifest=json.loads((root/'docs/research/info-hive-mykg-architecture-sources-2026-11-20.json').read_text(encoding='utf-8'))
for row in manifest['files']:
    family,name=row['path'].split('/',1)
    repo=root/f'info-hive-{family}' if family in ('wiki','rag') else root
    commit=manifest[family+'_commit'] if family in ('wiki','rag') else manifest['parent_head']
    blob=subprocess.check_output(['git','show',commit+':'+name],cwd=repo)
    assert hashlib.sha256(blob).hexdigest()==row['sha256'],row['path']
for linked in manifest['related_manifests']:
    assert hashlib.sha256((root/linked['path']).read_bytes()).hexdigest()==linked['sha256']
html=(root/'docs/research/info-hive-mykg-architecture-visual-2026-11-20.html').read_text(encoding='utf-8')
assert '公開版の入口に必要なもの' in html and '6つの Ossie 成果物が必須' in html
assert '問い合わせごとにライブと公開版を選ぶ仕組みではない' in html
assert '準備済みの Ossie 成果物があれば' not in html
result={'required_ossie_files':6,'candidate_without_ossie':'rejected_as_expected','committed_source_hashes_verified':len(manifest['files']),'linked_manifest_hashes_verified':len(manifest['related_manifests']),'publication_setup_and_state_explanation':'verified'}
(out/'source-verification.json').write_text(json.dumps(result,ensure_ascii=False,indent=2),encoding='utf-8')
print(json.dumps(result,ensure_ascii=False))
