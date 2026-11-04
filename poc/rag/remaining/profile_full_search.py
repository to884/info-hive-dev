"""検索の遅延を調べるため、製品 Engine の呼び出しを段階ごとに計時する。"""
import json
import os
import sys
import time
from collections import defaultdict
from pathlib import Path

ROOT=Path(__file__).resolve().parents[3]
sys.path.insert(0,str(ROOT/'info-hive-rag/scripts'))
from rag_config import Config,write_json
WORK=ROOT/'.rag-poc-data/full-20261104'
OUT=ROOT/'docs/research/rag-validation-remaining-2026-11-04'


class TimedQuery:
    def __init__(self,query,kind,elapsed):
        self.query,self.kind,self.elapsed=query,kind,elapsed

    def __getattr__(self,name):
        attribute=getattr(self.query,name)
        if not callable(attribute): return attribute
        def call(*args,**kwargs):
            if name=='to_list':
                started=time.perf_counter()
                try: return attribute(*args,**kwargs)
                finally: self.elapsed[self.kind]+=(time.perf_counter()-started)*1000
            result=attribute(*args,**kwargs)
            return TimedQuery(result,self.kind,self.elapsed) if hasattr(result,'to_list') else result
        return call


class TimedTable:
    def __init__(self,table,elapsed): self.table,self.elapsed=table,elapsed
    def __getattr__(self,name): return getattr(self.table,name)
    def search(self,*args,**kwargs):
        kind='fts_ms' if kwargs.get('query_type')=='fts' else 'dense_ms'
        return TimedQuery(self.table.search(*args,**kwargs),kind,self.elapsed)


def main():
    os.environ['RAYON_NUM_THREADS']='4'; os.environ['OMP_NUM_THREADS']='4'
    from rag_index import Engine
    cfg=Config(json.loads((WORK/'product-config.json').read_text(encoding='utf-8')))
    if cfg.reranker!='off': raise RuntimeError('内訳の点検ではリランカーなしの設定を使ってください。')
    engine=Engine(cfg); wiki=str(WORK/'product-wiki')
    queries=json.loads((WORK/'corpus.json').read_text(encoding='utf-8'))['queries']
    selected={}
    for query in queries:
        key=query['expected'][0].split(':p')[0] if query['expected'] else query['id']
        if query['expected'] or len([q for q in selected.values() if not q['expected']])<2:
            selected.setdefault(key,query)
    # モデル、辞書、索引を初期化する。初回準備を段階別の計時へ含めない。
    engine.search(wiki,'原本の参照と検索',30)
    elapsed=defaultdict(float)
    encode,tokenize,table=engine.embedder.encode,engine.tokenize,engine._table
    def timed(name,method):
        def call(*args,**kwargs):
            started=time.perf_counter()
            try: return method(*args,**kwargs)
            finally: elapsed[name]+=(time.perf_counter()-started)*1000
        return call
    engine.embedder.encode=timed('embedding_ms',encode)
    engine.tokenize=timed('tokenize_ms',tokenize)
    engine._table=lambda *args,**kwargs: TimedTable(table(*args,**kwargs),elapsed)
    results=[]
    for query in selected.values():
        elapsed.clear(); started=time.perf_counter()
        answer=engine.search(wiki,query['query'],30)
        total=(time.perf_counter()-started)*1000
        results.append({'id':query['id'],'total_ms':total,**dict(elapsed),'other_ms':total-sum(elapsed.values()),'result_count':len(answer['results'])})
    keys=['embedding_ms','tokenize_ms','dense_ms','fts_ms','other_ms','total_ms']
    write_json(OUT/'full-search-breakdown.json',{'queries':len(results),'nprobes':cfg.search_nprobes,'refine_factor':cfg.search_refine_factor,'mean_ms':{key:sum(row[key] for row in results)/len(results) for key in keys},'measurements':results,'scope':'各資料の最初の正例1問と負例2問の点検。既存の製品 Engine をラッパーで計時した直接呼び出しで、MCP 全体の72問の統計とは別。dense/FTSはto_listの実行時間、otherにはクエリ生成や順位融合と台帳照会などを含む。'})


if __name__=='__main__': main()
