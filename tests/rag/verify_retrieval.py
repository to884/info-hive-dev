"""MCP から検索設定だけを変更したときのモデル維持と空結果を確認する。"""
import asyncio
import json
import time
from verify_pipeline import ROOT,POC_DATA,connect,call
from rag_config import Config,write_json


async def main():
    run=POC_DATA/f'retrieval-{int(time.time())}'
    wiki=run/'wiki'; (wiki/'sources').mkdir(parents=True)
    (wiki/'SCHEMA.md').write_text('# 検索設定の検証\n',encoding='utf-8')
    references=run/'references'; references.mkdir()
    values={'data_dir':str(run/'data'),'embedding_model':'cl-nagoya/ruri-v3-30m'}
    path=run/'config.json'; write_json(path,values)
    before=Config(values).fingerprint; checks=[]
    def record(name,passed):
        checks.append({'name':name,'passed':bool(passed)})
        print(json.dumps(checks[-1]),flush=True)
        assert passed,name
    try:
        async with connect(path) as (session,_):
            await call(session,'configure',retrieval={'reranker':'tiny-int8','rerank_limit':8,'min_rerank_score':0})
            after=Config(json.loads(path.read_text(encoding='utf-8')))
            record('retrieval_only_configuration_preserves_model_and_fingerprint',after.model=='cl-nagoya/ruri-v3-30m' and after.fingerprint==before)
            unknown=await session.call_tool('configure',{'retrieval':{'unknown_key':1}})
            record('unknown_retrieval_setting_is_rejected',unknown.isError)
            incompatible=await session.call_tool('configure',{'retrieval':{'reranker':'off'}})
            record('threshold_requires_active_reranker',incompatible.isError)
            answer=await call(session,'search',wiki_root=str(wiki),query='保存された資料の検索',limit=3)
            record('empty_index_returns_abstention_metadata',answer['results']==[] and answer['abstained'] and answer['reranker']=='tiny-int8')
    finally:
        write_json(ROOT/'docs/research/rag-validation-remaining-2026-11-04/retrieval-config-results.json',{'run_dir':str(run),'checks':checks})


if __name__=='__main__': asyncio.run(main())
