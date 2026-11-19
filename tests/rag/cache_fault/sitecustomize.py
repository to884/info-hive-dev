"""この試験の MCP 子プロセスだけで、OCR の再実行と後始末の保留を観測する。"""
import json
import os
import sys
from pathlib import Path

target = next((Path(arg).name for arg in sys.argv if Path(arg).name in {'rag_server.py', 'rag_worker.py'}), None)
trace_path = os.environ.get('RAG_CACHE_TEST_TRACE')
if target and trace_path:
    sys.path.insert(0, os.environ['RAG_CACHE_TEST_SCRIPTS'])
    from rag_index import Engine
    import rag_pdf

    forbidden = os.environ.get('RAG_CACHE_TEST_FORBID_OCR') == '1'
    deferred = os.environ.get('RAG_CACHE_TEST_DEFER_DOC')

    def trace(kind, **values):
        with Path(trace_path).open('a', encoding='utf-8', newline='\n') as stream:
            stream.write(json.dumps({'kind': kind, 'pid': os.getpid(), 'target': target, **values}) + '\n')

    trace('hook_loaded', forbid_ocr=forbidden)
    original_ocr = rag_pdf.ocr_page

    def observe_ocr(*args, **kwargs):
        trace('ocr_called', forbidden=forbidden)
        if forbidden:
            raise AssertionError('保存済み OCR がある経路で OCR を再実行しました。')
        return original_ocr(*args, **kwargs)

    rag_pdf.ocr_page = observe_ocr
    original_retire = Engine._finish_retirements

    def defer_retirement(self, folder, connection, only_doc_id=None, keep_extraction=False):
        if deferred and only_doc_id is None and connection.execute(
                'SELECT 1 FROM retired_documents WHERE doc_id=?', (deferred,)).fetchone():
            trace('cleanup_deferred', doc_id=deferred)
            raise RuntimeError('検証用に公開後の後始末を保留しました。')
        return original_retire(self, folder, connection, only_doc_id=only_doc_id, keep_extraction=keep_extraction)

    Engine._finish_retirements = defer_retirement

    original_reset = Engine._reset_index
    def observe_reset(self, folder, connection, stale, preserve_doc_id=None):
        trace('index_reset', preserve_doc_id=preserve_doc_id)
        return original_reset(self, folder, connection, stale, preserve_doc_id=preserve_doc_id)
    Engine._reset_index = observe_reset

    gate_name = os.environ.get('RAG_CACHE_TEST_EMBED_GATE')
    original_ingest = Engine.ingest_pdf
    def interrupt_after_saved_embedding(self, *args, progress=None, **kwargs):
        def checked(phase, completed, total):
            if progress:
                progress(phase, completed, total)
            if gate_name and phase == '埋め込み' and completed > 0 and Path(gate_name).is_file():
                Path(gate_name).unlink()
                trace('embedding_interrupted', completed=completed, total=total)
                raise RuntimeError('検証用に埋め込み保存後に中断しました。')
        return original_ingest(self, *args, progress=checked, **kwargs)
    Engine.ingest_pdf = interrupt_after_saved_embedding
