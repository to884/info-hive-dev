"""抽出と OCR の結果を、埋め込みと分割の方針から切り離して保存する（ADR-0014）回帰試験。"""
import hashlib
import json
import os
import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "info-hive-rag/scripts"))
import rag_pdf
from rag_config import MODELS, Config, write_json
from rag_index import Engine


class FakeEmbedder:
    def __init__(self, dimension):
        self.dimension = dimension

    def encode(self, texts, **_):
        import numpy as np
        return np.tile(np.asarray([1.] + [0.] * (self.dimension - 1), dtype=np.float32), (len(texts), 1))


class ExtractionTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory(dir=os.environ.get("RAG_TEST_RUN_ROOT", str(ROOT / ".rag-poc-data")),
                                                ignore_cleanup_errors=True)
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name).resolve()
        self.source = self.root / "refs" / "資料.pdf"
        self.source.parent.mkdir()
        self.make_pdf(self.source, "Extraction cache checkpoint")
        self.wiki = self.make_wiki("wiki")
        self.values = {"data_dir": str(self.root / "data"), "embedding_model": "cl-nagoya/ruri-v3-30m",
                       "ocr_mode": "off", "batch_size": 4}
        # 抽出（ページの判定）が呼ばれた回数を数える。キャッシュを使えば呼ばれない。
        self.inspected = 0
        original = rag_pdf.inspect_page

        def counting(page):
            self.inspected += 1
            return original(page)
        patcher = patch.object(rag_pdf, "inspect_page", counting)
        patcher.start()
        self.addCleanup(patcher.stop)

    def make_wiki(self, name):
        wiki = self.root / name
        (wiki / "sources").mkdir(parents=True)
        (wiki / "SCHEMA.md").write_text("# 検証\n", encoding="utf-8")
        return wiki

    @staticmethod
    def make_pdf(path, text, pages=3):
        from reportlab.pdfgen import canvas
        pdf = canvas.Canvas(str(path))
        for number in range(pages):
            pdf.drawString(40, 700, text + " " + str(number))
            pdf.showPage()
        pdf.save()

    def engine(self, **changes):
        config = Config({**self.values, **changes})
        return Engine(config, embedder=FakeEmbedder(MODELS[config.model]))

    def ingest(self, engine, wiki=None, source=None):
        return engine.ingest_pdf(str(wiki or self.wiki), str(source or self.source), "sources/資料.md")

    def pages(self, engine, doc_id):
        return sorted(engine.config.extraction_dir(doc_id).glob("page-*.json"))

    def test_fingerprint_is_unchanged_from_0_4_0(self):
        # 指紋の中身を変えると、すべての利用者の索引が方針の変わった索引になる（ADR-0014）。変えるときはこの値も直す。
        self.assertEqual(Config({"data_dir": str(self.root / "data")}).fingerprint,
                         "1c61f7d933f39d12ba198703de5b65c8a88110116a91f9b619395ce5cbdfc909")

    def test_cache_lives_in_data_dir_and_is_keyed_by_extraction_settings(self):
        engine = self.engine()
        result = self.ingest(engine)
        cache = engine.config.extraction_dir(result["sha256"])
        self.assertEqual(cache.parent.parent, engine.config.data_dir / "extracted")
        self.assertEqual(cache.parent.name, result["sha256"])
        self.assertEqual(len(self.pages(engine, result["sha256"])), 3)
        self.assertEqual(Path(result["extracted_markdown"]), cache / "document.md")
        # 埋め込みのモデルと分割は鍵に入らない。抽出の設定は入る。
        self.assertEqual(Config({**self.values, "embedding_model": "cl-nagoya/ruri-v3-70m", "chunk_chars": 500}).extraction_key,
                         engine.config.extraction_key)
        self.assertNotEqual(Config({**self.values, "ocr_dpi": 200}).extraction_key, engine.config.extraction_key)
        self.assertNotEqual(Config({**self.values, "ocr_mode": "auto"}).extraction_key, engine.config.extraction_key)

    def test_model_change_reuses_extraction_and_resets_the_index(self):
        first = self.engine()
        result = self.ingest(first)
        stamps = {page.name: page.stat().st_mtime_ns for page in self.pages(first, result["sha256"])}
        self.assertEqual(self.inspected, 3)
        second = self.engine(embedding_model="cl-nagoya/ruri-v3-70m")
        # 取り込み直す前は、方針が変わった索引で検索しない。status は取り込み直す PDF を返す。
        with self.assertRaisesRegex(ValueError, "取り込み直"):
            second.search(str(self.wiki), "Extraction cache", limit=3)
        state = second.status(str(self.wiki))
        self.assertTrue(state["reingest_required"])
        self.assertEqual([item["sha256"] for item in state["reingest"]], [result["sha256"]])
        self.assertEqual(state["reingest"][0]["paths"], [self.source.as_posix()])
        again = self.ingest(second)
        self.assertEqual(again["status"], "indexed")
        self.assertTrue(again["index_reset"])
        self.assertEqual(self.inspected, 3)  # 抽出し直していない
        self.assertEqual({page.name: page.stat().st_mtime_ns for page in self.pages(second, result["sha256"])}, stamps)
        found = second.search(str(self.wiki), "Extraction cache checkpoint", limit=3)["results"]
        self.assertTrue(found and all(row["sha256"] == result["sha256"] for row in found))
        state = second.status(str(self.wiki))
        self.assertFalse(state["reingest_required"])
        self.assertEqual(state["reingest"], [])
        self.assertEqual(state["documents"], 1)

    def test_reset_keeps_the_list_of_documents_to_reingest(self):
        other = self.root / "refs" / "別の資料.pdf"
        self.make_pdf(other, "Another document entirely")
        first = self.engine()
        kept = self.ingest(first)
        waiting = first.ingest_pdf(str(self.wiki), str(other), "sources/別の資料.md")
        second = self.engine(embedding_model="cl-nagoya/ruri-v3-70m")
        self.ingest(second)  # 索引を空にしてから、1 件目だけ取り込み直す
        state = second.status(str(self.wiki))
        self.assertTrue(state["reingest_required"])
        self.assertEqual([item["sha256"] for item in state["reingest"]], [waiting["sha256"]])
        self.assertEqual(state["reingest"][0]["source_pages"], ["sources/別の資料.md"])
        # 取り込み直しを待つ文書の抽出の結果は、残っている。
        self.assertTrue(self.pages(second, waiting["sha256"]))
        results = second.search(str(self.wiki), "Another document entirely", limit=5)["results"]
        self.assertTrue(all(row["sha256"] == kept["sha256"] for row in results))
        second.ingest_pdf(str(self.wiki), str(other), "sources/別の資料.md")
        self.assertEqual(second.status(str(self.wiki))["reingest"], [])
        self.assertFalse((second.config.workspace(str(self.wiki)) / "previous-index.json").exists())

    def test_ocr_setting_change_extracts_again_and_keeps_the_previous_result(self):
        first = self.engine()
        result = self.ingest(first)
        previous = first.config.extraction_dir(result["sha256"])
        second = self.engine(ocr_dpi=200)
        self.ingest(second)
        self.assertEqual(self.inspected, 6)
        current = second.config.extraction_dir(result["sha256"])
        self.assertNotEqual(previous, current)
        self.assertEqual(len(list(previous.glob("page-*.json"))), 3)
        self.assertEqual(len(list(current.glob("page-*.json"))), 3)

    def test_same_pdf_in_two_wikis_is_extracted_once(self):
        engine = self.engine()
        other = self.make_wiki("other")
        first = self.ingest(engine)
        second = self.ingest(engine, wiki=other)
        self.assertEqual(first["sha256"], second["sha256"])
        self.assertEqual(second["status"], "indexed")
        self.assertEqual(self.inspected, 3)
        self.assertEqual(first["extracted_markdown"], second["extracted_markdown"])

    def test_old_version_cache_is_removed_only_when_no_wiki_uses_it(self):
        engine = self.engine()
        other = self.make_wiki("other")
        copy = self.root / "refs" / "写し.pdf"
        copy.write_bytes(self.source.read_bytes())
        old = self.ingest(engine)
        engine.ingest_pdf(str(other), str(copy), "sources/資料.md")
        self.make_pdf(self.source, "Second edition")
        self.ingest(engine)  # wiki から古い版が消える。other はまだ使っている
        self.assertTrue(self.pages(engine, old["sha256"]))
        self.make_pdf(copy, "Third edition")
        engine.ingest_pdf(str(other), str(copy), "sources/資料.md")
        self.assertFalse(engine.config.extraction_dir(old["sha256"]).exists())
        self.assertFalse((engine.config.data_dir / "extracted" / old["sha256"]).exists())

    def test_cleanup_removes_caches_of_every_extraction_setting(self):
        first = self.engine()
        old = self.ingest(first)
        self.ingest(self.engine(ocr_dpi=200), wiki=self.make_wiki("other"))
        self.make_pdf(self.source, "Second edition")
        self.ingest(first)
        # other は ocr_dpi=200 の指紋で同じ版を使っているので、まだ残る。
        self.assertTrue((first.config.data_dir / "extracted" / old["sha256"]).exists())

    def test_extraction_from_0_4_0_is_moved_and_reused(self):
        engine = self.engine()
        data = self.source.read_bytes()
        doc_id = hashlib.sha256(data).hexdigest()
        generation = hashlib.sha256((doc_id + engine.config.fingerprint).encode("ascii")).hexdigest()
        legacy = engine.config.workspace(str(self.wiki)) / "extracted" / generation
        rag_pdf.extract_pages(data, engine.config, legacy)
        self.assertEqual(self.inspected, 3)
        result = self.ingest(engine)
        self.assertEqual(self.inspected, 3)
        self.assertEqual(len(self.pages(engine, doc_id)), 3)
        self.assertFalse(legacy.exists())
        self.assertEqual(result["pages"], 3)

    def test_failed_embedding_after_model_change_keeps_the_old_index(self):
        first = self.engine()
        result = self.ingest(first)
        second = self.engine(embedding_model="cl-nagoya/ruri-v3-70m")

        class Broken:
            def encode(self, texts, **_):
                raise RuntimeError("モデルを取得できない")
        second._embedder = Broken()
        with self.assertRaisesRegex(RuntimeError, "モデルを取得できない"):
            self.ingest(second)
        # 設定を戻せば、前の索引をそのまま使える。
        again = self.engine()
        self.assertEqual(again.status(str(self.wiki))["documents"], 1)
        self.assertFalse(again.status(str(self.wiki))["reingest_required"])
        found = again.search(str(self.wiki), "Extraction cache checkpoint", limit=3)["results"]
        self.assertTrue(found and all(row["sha256"] == result["sha256"] for row in found))

    def test_reingested_then_replaced_version_cache_is_removed(self):
        other = self.root / "refs" / "別の資料.pdf"
        self.make_pdf(other, "Another document entirely")
        first = self.engine()
        old = self.ingest(first)
        first.ingest_pdf(str(self.wiki), str(other), "sources/別の資料.md")
        second = self.engine(embedding_model="cl-nagoya/ruri-v3-70m")
        self.ingest(second)  # 空にして、1 件目を取り込み直す。別の資料は取り込み直しを待つ
        self.make_pdf(self.source, "Second edition")
        self.ingest(second)  # 取り込み直した版を置き換える
        self.assertFalse((second.config.extraction_root / old["sha256"]).exists())

    def test_version_replaced_after_reset_is_dropped_and_its_cache_removed(self):
        first = self.engine()
        old = self.ingest(first)
        self.make_pdf(self.source, "Edited while the model changed")
        second = self.engine(embedding_model="cl-nagoya/ruri-v3-70m")
        new = self.ingest(second)
        self.assertNotEqual(old["sha256"], new["sha256"])
        state = second.status(str(self.wiki))
        self.assertEqual(state["reingest"], [])
        self.assertFalse((second.config.workspace(str(self.wiki)) / "previous-index.json").exists())
        self.assertFalse((second.config.extraction_root / old["sha256"]).exists())

    def test_two_changes_in_a_row_keep_every_source_page(self):
        first = self.engine()
        first.ingest_pdf(str(self.wiki), str(self.source), "sources/資料.md")
        first.ingest_pdf(str(self.wiki), str(self.source), "sources/別のページ.md")
        other = self.root / "refs" / "別の資料.pdf"
        self.make_pdf(other, "Another document entirely")
        first.ingest_pdf(str(self.wiki), str(other), "sources/別の資料.md")
        second = self.engine(embedding_model="cl-nagoya/ruri-v3-70m")
        second.ingest_pdf(str(self.wiki), str(self.source), "sources/資料.md")  # 空にして 1 件だけ取り込み直す
        third = self.engine(embedding_model="cl-nagoya/ruri-v3-130m")
        state = third.status(str(self.wiki))
        pages = {item["sha256"]: item["source_pages"] for item in state["reingest"]}
        self.assertEqual(len(pages), 2)
        third.ingest_pdf(str(self.wiki), str(other), "sources/別の資料.md")  # もう一度空にする
        item = [item for item in third.status(str(self.wiki))["reingest"]][0]
        self.assertEqual(item["source_pages"], ["sources/別のページ.md", "sources/資料.md"])

    def test_extraction_from_0_4_0_is_reused_after_a_model_change(self):
        first = self.engine()
        data = self.source.read_bytes()
        doc_id = hashlib.sha256(data).hexdigest()
        result = self.ingest(first)
        # 0.4.0 の置き場所に戻す（0.4.0 で取り込んだ状態を作る）。
        generation = hashlib.sha256((doc_id + first.config.fingerprint).encode("ascii")).hexdigest()
        legacy = first.config.workspace(str(self.wiki)) / "extracted" / generation
        legacy.parent.mkdir(parents=True)
        os.replace(first.config.extraction_dir(doc_id), legacy)
        second = self.engine(embedding_model="cl-nagoya/ruri-v3-70m")
        self.ingest(second)
        self.assertEqual(self.inspected, 3)
        self.assertEqual(len(self.pages(second, result["sha256"])), 3)
        self.assertFalse(legacy.exists())

    def test_restoring_old_content_after_cleanup_extracts_again(self):
        engine = self.engine()
        original = self.source.read_bytes()
        first = self.ingest(engine)
        self.make_pdf(self.source, "Second edition")
        self.ingest(engine)
        self.source.write_bytes(original)
        again = self.ingest(engine)
        self.assertEqual(again["sha256"], first["sha256"])
        self.assertEqual(again["status"], "indexed")
        table = engine._table(engine.config.workspace(str(self.wiki)))
        rows = table.search().where(f"doc_id = '{first['sha256']}'").limit(100).to_list()
        self.assertEqual(len(rows), again["chunks"])


class ConfigureTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory(dir=os.environ.get("RAG_TEST_RUN_ROOT", str(ROOT / ".rag-poc-data")),
                                                ignore_cleanup_errors=True)
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name).resolve()
        self.config_file = self.root / "config.json"
        write_json(self.config_file, {"data_dir": str(self.root / "data"), "embedding_model": "cl-nagoya/ruri-v3-30m"})
        patcher = patch.dict(os.environ, {"INFO_HIVE_RAG_CONFIG": str(self.config_file)})
        patcher.start()
        self.addCleanup(patcher.stop)
        import rag_server
        self.server = rag_server
        # 試験ではワーカーを起動しない。
        host = patch.object(rag_server, "WorkerHost")
        host.start()
        self.addCleanup(host.stop)
        for name in ("_engine", "_config", "_jobs", "_host"):
            setattr(rag_server, name, None)

    def saved(self):
        return json.loads(self.config_file.read_text(encoding="utf-8"))

    def test_ocr_settings_can_be_changed(self):
        result = self.server.configure(ocr_mode="always", ocr_dpi=200)
        self.assertEqual(self.saved()["ocr_mode"], "always")
        self.assertEqual(self.saved()["ocr_dpi"], 200)
        self.assertEqual((result["ocr_mode"], result["ocr_dpi"]), ("always", 200))
        self.assertTrue(result["reingest_required"])
        self.assertTrue(result["extraction_changed"])

    def test_model_change_needs_reingest_but_not_extraction(self):
        result = self.server.configure(embedding_model="cl-nagoya/ruri-v3-70m")
        self.assertTrue(result["reingest_required"])
        self.assertFalse(result["extraction_changed"])

    def test_data_dir_change_needs_reingest(self):
        result = self.server.configure(data_dir=str(self.root / "elsewhere"))
        self.assertTrue(result["reingest_required"])
        self.assertTrue(result["extraction_changed"])

    def test_retrieval_change_needs_nothing(self):
        result = self.server.configure(retrieval={"search_nprobes": 30})
        self.assertFalse(result["reingest_required"])
        self.assertFalse(result["extraction_changed"])
        self.assertNotIn("ocr_mode", self.saved())

    def test_invalid_ocr_settings_are_rejected_and_not_saved(self):
        for values in ({"ocr_mode": "sometimes"}, {"ocr_dpi": 71}, {"ocr_dpi": 301}):
            with self.assertRaises(ValueError):
                self.server.configure(**values)
        self.assertNotIn("ocr_mode", self.saved())
        self.assertNotIn("ocr_dpi", self.saved())


if __name__ == "__main__":
    unittest.main()
