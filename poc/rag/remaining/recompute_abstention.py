"""保存済み検索結果から、資料内で層化した固定分割の棄却指標を計算する。"""
import json
import sys
import statistics
from pathlib import Path

ROOT=Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT / "poc"))
from poc_data import POC_DATA  # noqa: E402
sys.path.insert(0,str(ROOT/'info-hive-rag/scripts'))
from rag_config import write_json
WORK=POC_DATA/'natural-20261104'
OUT=ROOT/'docs/research/rag-validation-remaining-2026-11-04'
path=OUT/'natural-mcp-results.json'
data=json.loads(path.read_text(encoding='utf-8'))
for profile in data['profiles']:
    rows=json.loads((WORK/f"results-{profile['profile']}.json").read_text(encoding='utf-8'))
    profile['quality_by_source']={}
    for group,prefix in [('fixed_wiki','j'),('reviewed_pdf','p')]:
        subset=[r for r in rows if r['id'].startswith(prefix) and r['expected']]
        profile['quality_by_source'][group]={'queries':len(subset),'page_recall_in_top_30_chunks':statistics.mean(r['recall_at_30'] for r in subset),'ndcg_at_10_unique_pages':statistics.mean(r['ndcg_at_10'] for r in subset)}
    if profile['profile']=='off': continue
    grouped={}
    for r in rows:
        if r['id'].startswith('p'): grouped.setdefault(r['expected'][0].split(':p')[0],[]).append(r)
    negatives=[r for r in rows if not r['expected']]
    development=[r for group in grouped.values() for r in group[::2]]+negatives[::2]
    heldout=[r for group in grouped.values() for r in group[1::2]]+negatives[1::2]
    def score(subset,t):
        tp=sum(r['top_rerank_score']>=t and bool(r['expected']) for r in subset)
        fp=sum(r['top_rerank_score']>=t and not r['expected'] for r in subset)
        fn=sum(r['top_rerank_score']<t and bool(r['expected']) for r in subset)
        tn=len(subset)-tp-fp-fn
        return {'tp':tp,'fp':fp,'fn':fn,'tn':tn,'f1':2*tp/max(1,2*tp+fp+fn)}
    thresholds=sorted({r['top_rerank_score'] for r in development})
    t=max(thresholds,key=lambda t:(score(development,t)['f1'],-t))
    profile['abstention']={'threshold':t,'development':score(development,t),'heldout':score(heldout,t),'development_ids':[r['id'] for r in development],'heldout_ids':[r['id'] for r in heldout],'split':'資料ごとに ID 順で交互、負例も交互の固定分割','negative_kind':'absent_identifier','scope':'不在識別子12問のみ。一般的な正解なし質問へは一般化しない。'}
data['memory_measurement']='50ms 間隔の親子プロセス RSS 合計の最大標本値。共有ページの重複を含み、瞬間ピークは保証しない。'
data['metric_definition']='製品 search の limit=30 で返した上位30チャンク内の正解ページ再現率。nDCG はこの範囲でページを重複除去した上位10ページ。旧 PoC の200候補から30ページを選ぶ指標とは条件が異なる。'
data['human_approved_pdf_queries']=json.loads((OUT/'human-review.json').read_text(encoding='utf-8'))['questions']
write_json(path,data)
