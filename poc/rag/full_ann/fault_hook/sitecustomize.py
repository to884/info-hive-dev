"""検証用 MCP 子プロセスだけで、公開のコミット後に待機する障害注入。"""
import json
import os
import sys
import time
from pathlib import Path

gate_name = os.environ.get('RAG_ANN_RETIREMENT_GATE')
forbid_document_embedding = os.environ.get('RAG_ANN_FORBID_DOCUMENT_EMBED') == '1'
if gate_name or forbid_document_embedding:
    sys.path.insert(0, os.environ['RAG_ANN_TEST_SCRIPTS'])
    from rag_index import Embedder, Engine
    from rag_config import write_json

if forbid_document_embedding:
    encode = Embedder.encode

    def query_only(self, texts, *, query=False):
        if not query:
            raise AssertionError('再開時に確定済みの文書ベクトルを再計算しました。')
        return encode(self, texts, query=True)

    Embedder.encode = query_only

if gate_name:
    gate = Path(gate_name)

    original = Engine._finish_retirements

    def wait_after_publication(self, folder, connection, only_doc_id=None):
        if only_doc_id is None and gate.exists():
            expected = json.loads(gate.read_text(encoding='utf-8'))
            if str(folder) == expected['folder']:
                retired = connection.execute('SELECT 1 FROM retired_documents WHERE doc_id=?', (expected['old_id'],)).fetchone()
                published = connection.execute('SELECT 1 FROM documents WHERE doc_id=?', (expected['new_id'],)).fetchone()
                if retired and published:
                    write_json(gate.with_suffix('.ready.json'), {'pid': os.getpid(), **expected})
                    while gate.exists():
                        time.sleep(0.01)
        return original(self, folder, connection, only_doc_id=only_doc_id)

    Engine._finish_retirements = wait_after_publication
