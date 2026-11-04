"""実 MCP の通信、CPU 埋め込み、分かち書き、検索、リランクをまとめて測る。"""
from __future__ import annotations

import asyncio
import argparse
import hashlib
import json
import math
import os
import statistics
import sys
import threading
import time
from pathlib import Path

import psutil

ROOT=Path(__file__).resolve().parents[3]
sys.path.insert(0,str(ROOT/'tests/rag'))
from verify_pipeline import connect,call
from rag_config import Config,write_json
from provenance import digest,approved_queries

WORK=ROOT/'.rag-poc-data/natural-20261104'
OUT=ROOT/'docs/research/rag-validation-remaining-2026-11-04'
WIKI=WORK/'wiki'
CONFIG=WORK/'config.json'
TAG='natural'
CORPUS_META=OUT/'natural-corpus.json'


def metric(labels,expected):
    relevant=set(expected)
    unique=list(dict.fromkeys(labels))
    recall=len(set(unique[:30])&relevant)/len(relevant)
    dcg=sum((label in relevant)/math.log2(i+2) for i,label in enumerate(unique[:10]))
    ideal=sum(1/math.log2(i+2) for i in range(min(len(relevant),10)))
    return recall,dcg/ideal


def p95(values):
    ordered=sorted(values)
    p=(len(ordered)-1)*.95
    i=int(p)
    return ordered[i]+(ordered[min(i+1,len(ordered)-1)]-ordered[i])*(p-i)


async def main():
    os.environ['RAYON_NUM_THREADS']='4'
    os.environ['OMP_NUM_THREADS']='4'
    os.environ['OPENBLAS_NUM_THREADS']='4'
    approved_queries()
    data=json.loads((WORK/'corpus.json').read_text(encoding='utf-8'))
    config_file=CONFIG
    original=json.loads(config_file.read_text(encoding='utf-8'))
    queries=data['queries']
    previous=OUT/f'{TAG}-mcp-results.json'
    results=json.loads(previous.read_text(encoding='utf-8'))['profiles'] if previous.exists() else []
    source_identity=digest(WORK/'vectors.npy') if (WORK/'vectors.npy').exists() else json.loads((WORK/'product-index-complete.json').read_text(encoding='utf-8'))['source_fingerprint']
    from rag_index import Engine
    cfg=Config(original); table=Engine(cfg)._table(cfg.workspace(str(WIKI)))
    version=table.version
    index_state={'table_version':version() if callable(version) else version,'indices':sorted([{'name':index.name,'type':index.index_type,'columns':index.columns} for index in table.list_indices()],key=lambda index:index['name'])}
    binding=hashlib.sha256((digest(WORK/'corpus.json')+source_identity+json.dumps(original,sort_keys=True)+json.dumps(index_state,sort_keys=True)).encode()).hexdigest()
    if previous.exists() and json.loads(previous.read_text(encoding='utf-8')).get('run_fingerprint')!=binding:
        raise RuntimeError('既存の評価と質問または設定が異なります。新しい result-tag で計測してください。')
    stopped=threading.Event()
    phase={'peak':0}
    parent=psutil.Process()
    def monitor():
        while not stopped.wait(.05):
            total=0
            for proc in [parent]+parent.children(recursive=True):
                try: total+=proc.memory_info().rss
                except psutil.NoSuchProcess: pass
            phase['peak']=max(phase['peak'],total)
    threading.Thread(target=monitor,daemon=True).start()
    # GPU 文書構築と全量抽出による CPU 競合を検索時間に混ぜない。
    suspended=[]
    try:
        for process in psutil.process_iter(['pid','name','cmdline']):
            cmd=process.info['cmdline'] or []
            if process.pid!=os.getpid() and any(arg.replace('\\','/').endswith(('remaining/embed_full.py','remaining/full_extract.py')) for arg in cmd):
                if process.memory_info().rss>20_000_000:
                    process.suspend(); suspended.append(process)
        for profile in ['off','tiny-int8','xsmall-int8']:
            if any(row['profile']==profile for row in results):
                continue
            values={**original,'reranker':profile,'rerank_limit':8,'min_rerank_score':None}
            write_json(config_file,values)
            phase['peak']=0
            profile_rows=[]
            cold=time.perf_counter()
            async with connect(config_file) as (session,server):
                first=await call(session,'search',wiki_root=str(WIKI),query='進捗を保存して再開する方法',limit=30)
                cold=time.perf_counter()-cold
                for q in queries:
                    start=time.perf_counter()
                    answer=await call(session,'search',wiki_root=str(WIKI),query=q['query'],limit=30)
                    elapsed=(time.perf_counter()-start)*1000
                    rows=answer['results']
                    labels=[(r['doc_id'][5:] if r['doc_id'].startswith('wiki:') else f"{r['doc_id']}:p{r['page']}") for r in rows]
                    row={'id':q['id'],'milliseconds':elapsed,'expected':q['expected'],'labels':list(dict.fromkeys(labels)),'top_rerank_score':rows[0].get('rerank_score') if rows else None,'returned_chunks':len(rows)}
                    if q['expected']:
                        row['recall_at_30'],row['ndcg_at_10']=metric(labels,q['expected'])
                    profile_rows.append(row)
                    write_json(WORK/f'results-{TAG}-{profile}.json',profile_rows)
                    print(json.dumps({'profile':profile,'id':q['id'],'milliseconds':elapsed}),flush=True)
            positives=[r for r in profile_rows if r['expected']]
            timings=[r['milliseconds'] for r in profile_rows]
            result={'profile':profile,'rerank_limit':8,'queries':len(profile_rows),'positive_queries':len(positives),'negative_queries':len(profile_rows)-len(positives),'cold_start_seconds':cold,'warm_p50_ms':statistics.median(timings),'warm_p95_ms':p95(timings),'warm_max_ms':max(timings),'recall_at_30':statistics.mean(r['recall_at_30'] for r in positives),'ndcg_at_10':statistics.mean(r['ndcg_at_10'] for r in positives),'aggregate_peak_rss_bytes':phase['peak'],'cpu_threads':4,'rayon_threads':4,'search_device':'cpu','mcp_transport_included':True,'query_tokenization_included':True,'generation_included':False}
            # PDF 正例と不在識別子の負例を半分ずつに分ける。評価側で閾値を再調整しない。
            if profile!='off':
                pdf=[r for r in profile_rows if r['id'].startswith('p')]
                negatives=[r for r in profile_rows if not r['expected']]
                # 資料・トピック順に偏らないよう各資料内で交互に固定分割する。
                grouped={}
                for row in pdf:
                    sample=row['expected'][0].split(':p')[0]
                    grouped.setdefault(sample,[]).append(row)
                development=[r for group in grouped.values() for r in group[::2]]+negatives[::2]
                heldout=[r for group in grouped.values() for r in group[1::2]]+negatives[1::2]
                thresholds=sorted({r['top_rerank_score'] for r in development})
                def score(rows,t):
                    tp=sum(r['top_rerank_score']>=t and bool(r['expected']) for r in rows)
                    fp=sum(r['top_rerank_score']>=t and not r['expected'] for r in rows)
                    fn=sum(r['top_rerank_score']<t and bool(r['expected']) for r in rows)
                    tn=len(rows)-tp-fp-fn
                    return {'tp':tp,'fp':fp,'fn':fn,'tn':tn,'f1':2*tp/max(1,2*tp+fp+fn)}
                threshold=max(thresholds,key=lambda t:(score(development,t)['f1'],-t))
                result['abstention']={'threshold':threshold,'development':score(development,threshold),'heldout':score(heldout,threshold),'negative_kind':'absent_identifier','scope':'不在識別子12問のみ。一般的な正解なし質問へは一般化しない。'}
            results.append(result)
            review=json.loads((OUT/'human-review.json').read_text(encoding='utf-8'))
            write_json(previous,{'run_fingerprint':binding,'index_state':index_state,'corpus':json.loads(CORPUS_META.read_text(encoding='utf-8')),'profiles':results,'builder_processes_suspended_during_timing':len(suspended),'human_approved_pdf_queries':review['questions'],'memory_measurement':'50ms 間隔の親子プロセス RSS 合計の最大標本値。共有ページの重複を含み、瞬間ピークは保証しない。','metric_definition':'上位30チャンク内の正解ページ再現率、およびページ重複除去後の上位10ページ nDCG。'})
    finally:
        write_json(config_file,original)
        stopped.set()
        for process in suspended:
            try: process.resume()
            except psutil.NoSuchProcess: pass


if __name__=='__main__':
    parser=argparse.ArgumentParser()
    parser.add_argument('--workspace',type=Path,default=WORK)
    parser.add_argument('--wiki',type=Path)
    parser.add_argument('--config',type=Path)
    parser.add_argument('--result-tag',default='natural')
    parser.add_argument('--corpus-metadata',type=Path)
    args=parser.parse_args()
    WORK=args.workspace.resolve(); WIKI=(args.wiki or WORK/'wiki').resolve(); CONFIG=(args.config or WORK/'config.json').resolve(); TAG=args.result_tag
    CORPUS_META=(args.corpus_metadata or OUT/('full-corpus.json' if (WORK/'product-index-complete.json').exists() else 'natural-corpus.json')).resolve()
    asyncio.run(main())
