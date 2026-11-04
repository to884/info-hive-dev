"""全量の生産側が完了したら、索引作成と実 MCP の評価へ順次進む。"""
import json
import os
import subprocess
import sys
import time
from pathlib import Path
from provenance import full_fingerprint

ROOT=Path(__file__).resolve().parents[3]
WORK=ROOT/'.rag-poc-data/full-20261104'


def main():
    markers=[WORK/'extraction-complete.json',WORK/'embeddings-130m/complete.json']
    while not all(p.exists() for p in markers):
        existing=[json.loads(p.read_text(encoding='utf-8')) for p in markers if p.exists()]
        if any(s['status']!='completed' for s in existing): raise RuntimeError('全量処理で失敗があります。出力を確認してください。')
        print(json.dumps({'phase':'waiting_for_extraction_and_embedding','ready_markers':sum(p.exists() for p in markers)}),flush=True)
        time.sleep(30)
    for p in markers:
        if json.loads(p.read_text(encoding='utf-8'))['status']!='completed': raise RuntimeError(f'{p} が正常終了していません。')
    fingerprint=full_fingerprint()
    index_marker=WORK/'product-index-complete.json'
    if index_marker.exists() and json.loads(index_marker.read_text(encoding='utf-8')).get('source_fingerprint')!=fingerprint:
        raise RuntimeError('完了済みの索引と現在のコーパスが異なります。')
    env={**os.environ,'PYTHONUTF8':'1','PYTHONIOENCODING':'utf-8','PYTHONDONTWRITEBYTECODE':'1'}
    for name,args in [('build_full_index',[]),('prepare_full_queries',[]),('evaluate_mcp',['--workspace',str(WORK),'--config',str(WORK/'product-config.json'),'--wiki',str(WORK/'product-wiki'),'--result-tag','full']),('full_ann_quality',[])]:
        if name=='build_full_index' and (WORK/'product-index-complete.json').exists(): continue
        print(json.dumps({'phase':name}),flush=True)
        with (WORK/f'{name}.log').open('w',encoding='utf-8') as log:
            subprocess.run([sys.executable,'-X','utf8',str(Path(__file__).with_name(name+'.py')),*args],stdout=log,stderr=log,env=env,check=True,cwd=ROOT)
    print(json.dumps({'phase':'finished'}),flush=True)


if __name__=='__main__': main()
