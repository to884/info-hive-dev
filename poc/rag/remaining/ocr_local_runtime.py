"""PoC 用の準備済みライブラリで、固定版 NDLOCR-Lite を実行する。"""
import os
import sys
from pathlib import Path

ROOT=Path(__file__).resolve().parents[3]
archives=ROOT/'.rag-poc-data/uv-cache-ocr/archive-v0'
required=['ocr.py','cv2','lxml','pypdf']
paths=[]
for module in required:
    matches=[p for p in archives.iterdir() if (p/module).exists()]
    if len(matches)!=1:
        raise RuntimeError(f'準備済みの {module} を一意に選べません: {matches}')
    paths.append(str(matches[0]))
sys.path.extend(paths)

if __name__=='__main__':
    import runpy
    runpy.run_path(str(ROOT/'info-hive-rag/scripts/rag_ocr.py'),run_name='__main__')
