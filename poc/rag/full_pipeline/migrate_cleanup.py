"""一時画像の後片付けだけを変えたことを AST で照合し、OCR を再開する。"""
import ast
import hashlib
import json
import sqlite3
from pathlib import Path
from full_ocr import ROOT,fingerprint
from rag_config import write_json
WORK=ROOT/'.rag-poc-data/full-ocr-gpu-20261104'
OUT=ROOT/'docs/research/rag-full-pipeline-2026-11-04'

def normalized(source):
    tree=ast.parse(source)
    for node in ast.walk(tree):
        if isinstance(node,ast.Call) and isinstance(node.func,ast.Attribute) and node.func.attr=='TemporaryDirectory':
            node.keywords=[keyword for keyword in node.keywords if keyword.arg!='ignore_cleanup_errors']
    return ast.dump(tree,include_attributes=False)

def main():
    import psutil
    for process in psutil.process_iter(['cmdline']):
        command=process.info['cmdline'] or []
        if any(arg.replace('\\','/').endswith('/full_ocr.py') for arg in command) and any(WORK.name in arg for arg in command):
            raise RuntimeError('OCR を停止してから方針を照合してください。')
    policy=json.loads((WORK/'ocr-policy.json').read_text(encoding='utf-8'))
    path=ROOT/'info-hive-rag/scripts/rag_pdf.py'; before=path.read_text(encoding='utf-8')
    assert hashlib.sha256(path.read_bytes()).hexdigest()==policy['rag_pdf.py']
    old='tempfile.TemporaryDirectory(prefix="ocr-", dir=work)'
    assert before.count(old)==1
    after=before.replace(old,'tempfile.TemporaryDirectory(prefix="ocr-", dir=work, ignore_cleanup_errors=True)')
    assert normalized(before)==normalized(after)
    write_json(WORK/'ocr-policy-before-cleanup.json',policy)
    (WORK/'rag_pdf-before-cleanup.py').write_text(before,encoding='utf-8')
    with sqlite3.connect(WORK/'ocr.sqlite') as db:
        failures=db.execute("SELECT doc_id,page,error FROM targets WHERE status='failed'").fetchall()
        preserved=db.execute("SELECT COUNT(*) FROM targets WHERE status IN ('completed','empty')").fetchone()[0]
    path.write_text(after,encoding='utf-8')
    identity,values=fingerprint('cuda',2)
    write_json(WORK/'ocr-policy.json',{'fingerprint':identity,**values})
    write_json(OUT/'ocr-cleanup-migration.json',{'recognized_computation_ast_unchanged':True,
        'changed_keyword':'TemporaryDirectory(ignore_cleanup_errors=True)','preserved_pages':preserved,
        'old_fingerprint':policy['fingerprint'],'new_fingerprint':identity,'failures_before_retry':failures,
        'scope':'変更は一時フォルダー削除の共有違反を抑制する引数だけ。認識、画像描画、入力、本文の処理を変えていないことをASTで照合。'})
    print('認識処理を変えず、保存済みページを再利用できることを照合しました。',flush=True)

if __name__=='__main__': main()
