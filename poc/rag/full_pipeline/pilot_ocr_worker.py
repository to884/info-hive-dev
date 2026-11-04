"""実モデルで OCR の再利用、空白画像、従来の出力との一致を確認する。"""
import hashlib
import json
import sys
import time
from pathlib import Path
ROOT=Path(__file__).resolve().parents[3]
sys.path.insert(0,str(ROOT/'info-hive-rag/scripts'))
from rag_config import Config,write_json
from rag_ocr_client import OcrClient

def main():
    work=ROOT/'.rag-poc-data/full-ocr-20261104'
    out=ROOT/'docs/research/rag-full-pipeline-2026-11-04'
    image=ROOT/'.rag-poc-data/ocr-remaining-20261104/low_resolution.png'
    expected=(work/'pilot/cli/low_resolution.txt').read_text(encoding='utf-8-sig').strip()
    from PIL import Image
    blank=work/'pilot/blank.png'; Image.new('RGB',(500,700),'white').save(blank)
    cfg=Config({'data_dir':str(work/'pilot/data'),'cpu_threads':1})
    command=[sys.executable,str(ROOT/'poc/rag/remaining/ocr_local_runtime.py')]
    rows=[]
    with OcrClient(cfg,command=command) as client:
        for path in [image,blank,image]:
            started=time.perf_counter(); result=client.recognize(path)
            rows.append({'image':path.name,'seconds':time.perf_counter()-started,**result})
    assert rows[0]['text']==rows[2]['text']==expected
    assert len({row['pid'] for row in rows})==1
    assert rows[1]['text']=='' and rows[1]['line_count']==0
    write_json(out/'ocr-worker-pilot.json',{'passed':True,'rows':rows,'same_pid':True,'legacy_cli_text_sha256':hashlib.sha256(expected.encode('utf-8')).hexdigest()})
    print('実 OCR の出力一致、同一プロセスの再利用、空白画像からの復帰を確認しました。',flush=True)

if __name__=='__main__': main()
