"""wiki の MCP サーバーの検索の基盤（wiki_index）の試験。ADR-0011 の書き込みの規則と、index_chunks の世代。

埋め込みはテスト用のもの（INFO_HIVE_TEST_EMBEDDER=hash）を使い、モデルを読み込まない。

    uv run --python 3.12 --with numpy==2.5.4 --with usearch==2.26.6 --with tantivy==0.27.0 --with fastembed==0.8.0 ^
        --with onnxruntime==1.31.1 --with psutil==7.2.2 python -X utf8 -m unittest tests/wiki/test_wiki_index.py -v
"""
from __future__ import annotations

import base64
import os
import shutil
import sqlite3
import sys
import tempfile
import unittest
from pathlib import Path
from unittest import mock

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "info-hive-wiki/skills/info-hive/scripts"))
os.environ["INFO_HIVE_TEST_EMBEDDER"] = "hash"
import numpy as np  # noqa: E402
import wiki_index  # noqa: E402
import wiki_mcp_common  # noqa: E402

CORPUS = ROOT / "info-hive-wiki/eval/retrieval/ja/corpus/wiki"


class Base(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory(ignore_cleanup_errors=True)
        self.addCleanup(self.temp.cleanup)
        root = Path(self.temp.name)
        patcher = mock.patch.dict(os.environ, {"INFO_HIVE_DATA_DIR": str(root / "data")})
        patcher.start()
        self.addCleanup(patcher.stop)
        self.wiki = root / "wiki"
        shutil.copytree(CORPUS, self.wiki)
        self.root = wiki_mcp_common.normalize_wiki_root(self.wiki)
        self.embedder = wiki_index.get_embedder()

    def open_index(self) -> wiki_index.WikiIndex:
        index = wiki_index.WikiIndex(self.root)
        self.addCleanup(index.close)
        return index


class WikiIndexTests(Base):
    def test_index_lives_outside_the_wiki(self):
        index = self.open_index()
        index.refresh()
        self.assertFalse((self.wiki / ".wiki-cache").exists())
        self.assertTrue(index.dir.is_relative_to(Path(os.environ["INFO_HIVE_DATA_DIR"]) / "index"))

    def test_incremental_refresh(self):
        index = self.open_index()
        first = index.refresh()
        self.assertGreater(first["added"], 100)
        self.assertEqual(index.refresh(), {"changed": False})
        page = self.wiki / "concepts" / "heatstroke.md"
        page.write_text(page.read_text(encoding="utf-8") + "\n追記した一文。\n", encoding="utf-8")
        second = index.refresh()
        self.assertEqual((second["added"], second["removed"]), (1, 1))
        page.unlink()
        third = index.refresh()
        self.assertEqual(third["added"], 0)
        self.assertGreater(third["removed"], 0)
        hits = index.search("熱中症", top=20, embedder=None)["results"]
        self.assertNotIn("concepts/heatstroke.md", {h["rel_path"] for h in hits})

    def test_search_modes_and_filters(self):
        index = self.open_index()
        index.refresh()
        wiki_index.embed_pending(index.collection, self.embedder)
        hybrid = index.search("熱中症の予防", embedder=self.embedder)
        self.assertEqual(hybrid["mode"], "hybrid")
        self.assertEqual(hybrid["index"]["state"], "ready")
        lexical = index.search("熱中症の予防", embedder=None)
        self.assertEqual(lexical["mode"], "lexical")
        concept = index.search("税", type="概念", embedder=self.embedder)["results"]
        self.assertTrue(concept)
        self.assertEqual({row["type"] for row in concept}, {"concept"})
        per_page = index.search("熱中症", top=20, per_page=1, embedder=self.embedder)["results"]
        self.assertEqual(len({r["rel_path"] for r in per_page}), len(per_page))

    def test_reconcile_after_interrupted_write(self):
        index = self.open_index()
        index.refresh()
        wiki_index.embed_pending(index.collection, self.embedder)
        rows = index.collection.stats()["rows"]
        index.close()
        folder = wiki_mcp_common.wiki_index_dir(self.root)
        # 途中で止まった状態を作る: dirty の印を立て、usearch のファイルを消し、Tantivy から 1 件消す。
        db = sqlite3.connect(folder / "ledger.sqlite")
        with db:
            db.execute("UPDATE meta SET value = '1' WHERE key = 'dirty'")
            some_key = db.execute("SELECT key FROM rows LIMIT 1").fetchone()[0]
        db.close()
        (folder / "vectors.usearch").unlink()
        import tantivy
        lexical = tantivy.Index.open(str(folder / "lexical"))  # encoding: default-ok（Tantivy の索引を開く。テキストではない）
        writer = lexical.writer(heap_size=15_000_000, num_threads=1)
        writer.delete_documents_by_term("key", some_key)
        writer.commit()
        del writer
        reopened = self.open_index()
        self.assertEqual(reopened.collection.stats(), {"rows": rows, "embedded": 0})
        self.assertEqual(reopened.collection.lexical.searcher().num_docs, rows)
        wiki_index.embed_pending(reopened.collection, self.embedder)
        self.assertEqual(reopened.collection.stats()["embedded"], rows)

    def test_tantivy_commit_failure_is_retried(self):
        index = self.open_index()
        collection = index.collection
        real_writer = collection.lexical.writer
        calls = {"n": 0}

        class Flaky:
            def __init__(self, writer):
                self._writer = writer

            def __getattr__(self, name):
                return getattr(self._writer, name)

            def commit(self):
                calls["n"] += 1
                if calls["n"] == 1:
                    raise OSError("アクセスが拒否されました。 (os error 5)")
                return self._writer.commit()

        class Proxy:
            def __init__(self, index):
                self._index = index

            def __getattr__(self, name):
                return getattr(self._index, name)

            def writer(self, *a, **k):
                return Flaky(real_writer(*a, **k))

        collection.lexical = Proxy(collection.lexical)
        result = index.refresh()
        self.assertGreater(calls["n"], 1)
        self.assertEqual(collection.lexical.searcher().num_docs, result["added"])

    def test_fingerprint_change_rebuilds(self):
        index = self.open_index()
        index.refresh()
        index.close()
        with mock.patch.object(wiki_index, "WIKI_TOKENIZER", "wiki-bigram-v2"):
            rebuilt = wiki_index.WikiIndex(self.root)
            try:
                self.assertEqual(rebuilt.collection.stats()["rows"], 0)
                self.assertGreater(rebuilt.refresh()["added"], 100)
            finally:
                rebuilt.close()

    def test_single_writer_per_index(self):
        self.open_index()
        with mock.patch.object(wiki_index, "WRITER_LOCK_TIMEOUT", 0.3):
            with self.assertRaises(RuntimeError):
                wiki_index.WikiIndex(self.root)

    def test_get_page_and_list_index(self):
        index = self.open_index()
        index.refresh()
        page = index.get_page("heatstroke")
        self.assertEqual(page["rel_path"], "concepts/heatstroke.md")
        self.assertEqual(page["meta"]["title"], "熱中症")
        self.assertEqual(index.get_page("concepts/heatstroke.md")["slug"], "heatstroke")
        self.assertEqual(index.get_page("[[熱中症予防ガイド要約]]")["rel_path"], "sources/熱中症予防ガイド要約.md")
        self.assertIsNone(index.get_page("../SCHEMA"))
        self.assertIsNone(index.get_page("index"))
        listing = wiki_index.list_index(self.root)
        self.assertIn("indexes", listing)
        with self.assertRaises(FileNotFoundError):
            wiki_index.list_index(self.root, "../SCHEMA")

    def test_wiki_key_is_case_insensitive_on_windows(self):
        if os.name != "nt":
            self.skipTest("Windows だけ")
        upper = wiki_mcp_common.normalize_wiki_root(str(self.wiki).upper())
        self.assertEqual(wiki_mcp_common.wiki_key(upper), wiki_mcp_common.wiki_key(self.root))


class ChunkTests(Base):
    def chunk(self, ident, doc, text, vector=True):
        item = {"id": ident, "doc": doc, "text": text, "tokens": text.split(), "metadata": {"page": 1}}
        if vector:
            item["vector_b64"] = base64.b64encode(
                np.asarray(self.embedder.passages([text])[0], dtype="<f4").tobytes()).decode()
        return item

    def test_generations_and_deletes(self):
        store = wiki_index.ChunkStore("rag-test")
        self.addCleanup(store.close)
        first = store.index([self.chunk("a#1", "a.pdf", "所得 税 申告"), self.chunk("a#2", "a.pdf", "消費 税"),
                             self.chunk("b#1", "b.pdf", "熱中症 予防", vector=False)],
                            generation=1, tokenizer="sudachi-c-normalized-v1", embedder=self.embedder)
        self.assertEqual((first["accepted"], first["rows"], first["embedded"]), (3, 3, 3))
        found = store.search("所得税", ["所得", "税"], embedder=self.embedder)
        self.assertEqual(found["results"][0]["id"], "a#1")
        self.assertEqual(found["results"][0]["metadata"], {"page": 1})
        # a.pdf を世代 2 で入れ直す。a#2 は新しい世代にないので消える。
        second = store.index([self.chunk("a#1", "a.pdf", "所得 税 確定 申告")], generation=2,
                             tokenizer="sudachi-c-normalized-v1", embedder=self.embedder)
        self.assertEqual((second["replaced"], second["retired"], second["rows"]), (1, 1, 2))
        ids = {r["id"] for r in store.search("税", ["税"], top=10, embedder=None)["results"]}
        self.assertEqual(ids, {"a#1"})
        third = store.index([], generation=3, tokenizer="sudachi-c-normalized-v1", delete_docs=["b.pdf"])
        self.assertEqual(third["rows"], 1)
        only_b = store.search("熱中症", ["熱中症"], docs=["b.pdf"], embedder=self.embedder)
        self.assertEqual(only_b["results"], [])

    def test_tokenizer_mismatch_needs_reset(self):
        store = wiki_index.ChunkStore("rag-test2")
        self.addCleanup(store.close)
        store.index([self.chunk("x", "x.pdf", "税")], 1, "sudachi-c-normalized-v1")
        with self.assertRaises(ValueError):
            store.index([self.chunk("y", "y.pdf", "税")], 1, "bigram")
        result = store.index([self.chunk("y", "y.pdf", "税")], 1, "bigram", reset=True)
        self.assertEqual((result["reset"], result["rows"]), (True, 1))

    def test_rejects_bad_chunks(self):
        store = wiki_index.ChunkStore("rag-test3")
        self.addCleanup(store.close)
        with self.assertRaises(ValueError):
            store.index([{"id": "x", "text": "税"}], 1, "t")
        with self.assertRaises(ValueError):
            store.index([{"id": "x", "text": "税", "tokens": ["税"], "vector": [1.0, 2.0]}], 1, "t")
        with self.assertRaises(ValueError):
            wiki_index.ChunkStore("../escape")


class FusionTests(unittest.TestCase):
    def test_rrf_follows_adr_0011(self):
        self.assertEqual(wiki_index.FUSION, {"k": 30, "lexical_weight": 0.5, "candidates": 200})
        ranked = wiki_index.fuse(dense=[1, 2], lexical=[2, 3])
        scores = {key: score for key, score, _ in ranked}
        self.assertAlmostEqual(scores[2], 0.5 / 31 + 1 / 32)
        self.assertAlmostEqual(scores[1], 1 / 31)
        self.assertAlmostEqual(scores[3], 0.5 / 32)
        self.assertEqual([key for key, _, _ in ranked], [2, 1, 3])


if __name__ == "__main__":
    unittest.main()
