"""現在のwikiの記事の見出し・出所・内容のハッシュを採取する。wikiは変更しない。"""
from pathlib import Path
import collections
import hashlib
import json
import re
import sys

ROOT=Path(__file__).resolve().parents[3]
WIKI=ROOT/'wiki'
OUT=Path(__file__).resolve().parent
sys.path.insert(0,str(ROOT/'info-hive-wiki/skills/info-hive/scripts'))
import wiki_pages
from wiki_text import parse_frontmatter_text, canonical_meta

rows=[]
walk=wiki_pages.walk_pages(WIKI)
assert not walk.unlistable and not walk.unknown,(walk.unlistable,walk.unknown)
for f in walk.files:
    p=WIKI/f.rel
    data=p.read_bytes()
    text=data.decode('utf-8-sig')
    match=re.match(r'\A---\s*\n(.*?)\n---(?:\r?\n|\Z)',text,re.S)
    assert match,f.rel
    meta=parse_frontmatter_text(match.group(1))
    meta,_=canonical_meta(meta)
    rows.append({'path':p.relative_to(ROOT).as_posix(),'slug':p.stem,
        'type':meta.get('type'),'title':meta.get('title'),'tags':meta.get('tags'),
        'sources':meta.get('sources'),'raw':meta.get('raw'),'sha256':hashlib.sha256(data).hexdigest(),
        'headings':[{'line':i+1,'text':line} for i,line in enumerate(text.splitlines()) if re.match(r'^#{1,3} ',line)],
        'lines':len(text.splitlines()),'chars':len(text)})
ontology=WIKI/'graph/ontology.yaml'
result={'date':'2026-11-18','pages':rows,'total_pages':len(rows),
    'page_types':dict(collections.Counter(r['type'] for r in rows)),
    'ontology_sha256':hashlib.sha256(ontology.read_bytes()).hexdigest(),
    'read_policy':'全記事のメタデータと見出しを走査。設計の根拠にする記事の本文は別途読む。'}
(OUT/'corpus_inventory.json').write_text(json.dumps(result,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
for row in rows:
    print(json.dumps({'path':row['path'],'title':row['title'],'lines':row['lines']},ensure_ascii=False))
print(json.dumps({'total':result['total_pages'],'types':result['page_types']},ensure_ascii=False))
