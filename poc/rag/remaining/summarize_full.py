"""全量抽出の範囲、重複、OCR 対象数と原本メタデータの一致を集計する。"""
import collections
import json
import os
import sqlite3
import sys
from pathlib import Path

ROOT=Path(__file__).resolve().parents[3]
sys.path.insert(0,str(ROOT/'info-hive-rag/scripts'))
from rag_config import write_json
WORK=ROOT/'.rag-poc-data/full-20261104'
OUT=ROOT/'docs/research/rag-validation-remaining-2026-11-04'


def main():
    state=json.loads((WORK/'extraction-complete.json').read_text(encoding='utf-8'))
    manifest=json.loads((WORK/'manifest.json').read_text(encoding='utf-8'))
    db=sqlite3.connect(WORK/'corpus.sqlite')
    totals=db.execute("SELECT COUNT(*),SUM(size),SUM(pages),SUM(text_bytes),SUM(chunks),SUM(read_seconds),SUM(extract_seconds) FROM documents WHERE status='completed'").fetchone()
    unique=db.execute("SELECT COUNT(*),SUM(size) FROM (SELECT doc_id,MAX(size) AS size FROM documents WHERE status='completed' GROUP BY doc_id)").fetchone()
    kinds=collections.Counter(json.loads(q)['kind'] for q, in db.execute('SELECT quality FROM pages'))
    chunks=db.execute('SELECT COUNT(*) FROM chunks').fetchone()[0]
    failed=[dict(zip(['relative_path','error'],row)) for row in db.execute("SELECT relative_path,error FROM documents WHERE status='failed'")]
    db.close()
    # Windows のディレクトリ列挙情報で照合し、クラウドのみの再解析ポイントを開かない。
    current={}; directories=[Path(manifest['root'])]
    while directories:
        directory=directories.pop()
        with os.scandir(directory) as entries:
            for entry in entries:
                if entry.is_dir(follow_symlinks=False):
                    if not os.path.isjunction(entry.path): directories.append(Path(entry.path))
                elif entry.name.lower().endswith('.pdf'):
                    stat=entry.stat(follow_symlinks=False)
                    current[Path(entry.path).relative_to(manifest['root']).as_posix()]=(stat.st_size,stat.st_mtime_ns)
    changed=[]
    for item in manifest['files']:
        if item['cloud_only']: continue
        if current.get(item['relative_path'])!=(item['bytes'],item['mtime_ns']): changed.append(item['relative_path'])
    write_json(WORK/'source-audit-details.json',{'changed_relative_paths':changed,'failed':failed})
    result={'status':state['status'],'files_completed':totals[0],'source_bytes':totals[1],'pages_including_duplicate_pdfs':totals[2],'text_bytes_including_duplicate_pdfs':totals[3],'chunks_before_pdf_deduplication':totals[4],'unique_pdf_contents':unique[0],'unique_pdf_bytes':unique[1],'unique_pages':sum(kinds.values()),'unique_chunks':chunks,'routing_counts':dict(kinds),'pages_routed_to_ocr':sum(kinds[k] for k in ['scan','vertical','garbled']),'ocr_executed_for_full_corpus':False,'routing_is_human_ground_truth':False,'cloud_only_files_excluded':sum(r['cloud_only'] for r in manifest['files']),'failed_files':len(failed),'source_metadata_changed_files':len(changed),'source_metadata_comparison':'初期一覧と全量抽出後のサイズ・mtime。全 PDF のハッシュを再読して比較したものではない。','successful_document_read_seconds_sum':totals[5],'successful_document_extract_seconds_sum':totals[6],'duration_scope':'各成功文書の時間の和。並列の壁時計時間や中断した処理の時間とは異なる。','corpus_sqlite_bytes':(WORK/'corpus.sqlite').stat().st_size}
    write_json(OUT/'full-extraction-summary.json',result)
    print(json.dumps(result,ensure_ascii=False),flush=True)


if __name__=='__main__': main()
