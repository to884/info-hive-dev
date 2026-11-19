"""登録の競合、キャンセル、公開境界と索引の再開、PDF の絶対パスの扱い（ADR-0013）の回帰試験。"""
import concurrent.futures
import hashlib
import json
import unicodedata
import os
import sys
import tempfile
import unittest
from unittest.mock import patch
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "poc"))
from poc_data import POC_DATA  # noqa: E402
sys.path.insert(0, str(ROOT / "info-hive-rag/scripts"))
from rag_config import Config
from rag_index import Engine,Embedder
from rag_jobs import Jobs, JobCancelled
from rag_config import write_json


class JobTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory(dir=os.environ.get("RAG_TEST_RUN_ROOT", str(POC_DATA)), ignore_cleanup_errors=True)
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name).resolve()
        self.refs = self.root / "refs"
        self.refs.mkdir()
        self.wiki = self.root / "wiki"
        (self.wiki / "sources").mkdir(parents=True)
        (self.wiki / "SCHEMA.md").write_text("# 検証\n", encoding="utf-8")
        self.source = self.refs / "資料.pdf"
        self.make_pdf(self.source, "Persistent indexing checkpoint")
        self.config = Config({"data_dir": str(self.root / "data"),
                              "embedding_model": "cl-nagoya/ruri-v3-30m", "ocr_mode": "off", "batch_size": 1})
        self.jobs = Jobs(self.config.data_dir)

    @staticmethod
    def make_pdf(path, text, pages=4):
        from reportlab.pdfgen import canvas
        pdf = canvas.Canvas(str(path))
        for number in range(pages):
            pdf.drawString(40, 700, text + " " + str(number))
            pdf.showPage()
        pdf.save()

    def engine(self):
        import numpy as np
        class Embedder:
            def encode(self, texts, **_):
                return np.tile(np.asarray([1.] + [0.] * 255, dtype=np.float32), (len(texts), 1))
        return Engine(self.config, embedder=Embedder())

    def register(self):
        return self.jobs.register(self.config, str(self.wiki), str(self.source), "sources/資料.md")

    def test_atomic_json_save_retries_temporary_sharing_violation(self):
        target=self.root/'saved.json'
        write_json(target,{'value':'before'})
        replace=Path.replace
        attempts=[]
        def transient(path,destination):
            attempts.append(path)
            if len(attempts)<3:
                self.assertEqual(json.loads(target.read_text(encoding='utf-8')),{'value':'before'})
                raise PermissionError('一時的な共有違反')
            return replace(path,destination)
        with patch.object(Path,'replace',transient),patch('rag_config.time.sleep'):
            write_json(target,{'value':'after'})
        self.assertEqual(len(attempts),3)
        self.assertEqual(json.loads(target.read_text(encoding='utf-8')),{'value':'after'})

    def test_long_embedding_input_is_preserved_and_batch_is_bounded(self):
        class Model:
            max_seq_length=8192
            def tokenizer(self,values,**kwargs):
                assert kwargs['truncation'] is False
                return {'input_ids':[list(range(len(value))) for value in values]}
            def encode(self,values,**kwargs):
                self.received=values; self.batch=kwargs['batch_size']
                return [[1,0] for _ in values]
        embedder=Embedder.__new__(Embedder); embedder.model=Model()
        texts=['長'*3000 for _ in range(12)]
        self.assertEqual(len(embedder.encode(texts)),12)
        self.assertTrue(all(value=='検索文書: '+texts[0] for value in embedder.model.received))
        self.assertTrue(1<=embedder.model.batch<12)
        with self.assertRaisesRegex(ValueError,'8192'):
            embedder.encode(['長'*9000])

    def test_concurrent_registration_and_wiki_isolation(self):
        with concurrent.futures.ThreadPoolExecutor(8) as pool:
            ids = list(pool.map(lambda _: self.register()["job_id"], range(32)))
        self.assertEqual(len(set(ids)), 1)
        other = self.root / "other"
        other.mkdir()
        (other / "SCHEMA.md").write_text("# 別の wiki\n", encoding="utf-8")
        with self.assertRaises(ValueError):
            self.jobs.status(str(other), ids[0])
        with self.assertRaises(ValueError):
            self.jobs.cancel(str(other), ids[0])

    def test_cancel_is_not_automatically_resumed_and_explicit_retry_is(self):
        job = self.register()
        self.jobs.claim("owner")
        self.jobs.cancel(str(self.wiki), job["job_id"])
        self.jobs.recover()
        self.assertIsNone(self.jobs.claim("next"))
        with self.assertRaises(JobCancelled):
            self.jobs.progress(job["job_id"], "owner", "埋め込み", 1, 4)
        self.jobs.retry(str(self.wiki), job["job_id"])
        self.assertEqual(self.jobs.claim("next")["id"], job["job_id"])

    def test_cancel_and_publication_have_an_order(self):
        job = self.register()
        self.jobs.claim("owner")
        self.jobs.begin_publication(job["job_id"], "owner")
        rejected = self.jobs.cancel(str(self.wiki), job["job_id"])
        self.assertFalse(rejected["cancellation_accepted"])
        self.jobs.finish(job["job_id"], "owner", result={"pages": 4})
        self.assertEqual(self.jobs.status(str(self.wiki), job["job_id"])["status"], "completed")

    def test_failed_jobs_require_explicit_retry(self):
        job = self.register()
        self.jobs.claim("owner")
        self.jobs.finish(job["job_id"], "owner", error="検証用の失敗")
        self.jobs.recover()
        self.assertIsNone(self.jobs.claim("next"))
        self.jobs.retry(str(self.wiki), job["job_id"])
        self.assertEqual(self.jobs.claim("next")["id"], job["job_id"])

    def test_publication_boundary_survives_worker_recovery(self):
        job=self.register()
        self.jobs.claim('owner'); self.jobs.begin_publication(job['job_id'],'owner')
        self.jobs.pause('owner'); self.jobs.recover(); self.jobs.claim('next')
        self.jobs.progress(job['job_id'],'next','索引の更新',0,1)
        self.assertFalse(self.jobs.cancel(str(self.wiki),job['job_id'])['cancellation_accepted'])
        self.jobs.finish(job['job_id'],'next',error='公開後の保守で中断')
        self.assertFalse(self.jobs.cancel(str(self.wiki),job['job_id'])['cancellation_accepted'])

    def test_source_page_cannot_escape_wiki(self):
        for page in ("../outside.md", "sources/../../outside.md", "sources/資料.pdf"):
            with self.assertRaises(ValueError):
                self.jobs.register(self.config, str(self.wiki), str(self.source), page)

    def test_index_resume_after_committed_batch_and_unpublished_rows(self):
        import numpy as np
        class Embedder:
            def __init__(self): self.batches = []
            def encode(self, texts, **_):
                self.batches.append(len(texts))
                return np.tile(np.asarray([1.] + [0.] * 255, dtype=np.float32), (len(texts), 1))
        fake = Embedder()
        engine = Engine(self.config, embedder=fake)
        def stop_after_checkpoint(phase, completed, total):
            if phase == "埋め込み" and completed == 1:
                raise RuntimeError("保存済みバッチの直後に中断")
        with self.assertRaisesRegex(RuntimeError, "中断"):
            engine.ingest_pdf(str(self.wiki), str(self.source), "sources/資料.md", progress=stop_after_checkpoint)
        self.assertEqual(engine.status(str(self.wiki))["documents"], 0)
        result = engine.ingest_pdf(str(self.wiki), str(self.source), "sources/資料.md")
        self.assertEqual(result["pages"], 4)
        self.assertEqual(len(fake.batches), 4)  # 保存した 1 件を再計算していない。
        table = engine._table(self.config.workspace(str(self.wiki)))
        self.assertEqual(table.count_rows(), result["chunks"])

    def test_reranking_orders_candidates_and_threshold_can_abstain(self):
        import numpy as np
        import re
        class Embedder:
            def encode(self, texts, **_):
                return np.tile(np.asarray([1.] + [0.] * 255, dtype=np.float32), (len(texts), 1))
        class Reranker:
            def score(self, pairs):
                return [float(re.search(r"checkpoint (\d+)", text).group(1)) for _,text in pairs]
        values = {**self.config.values,"reranker":"xsmall-int8","rerank_limit":4}
        config = Config(values)
        engine = Engine(config, embedder=Embedder(), reranker=Reranker())
        engine.ingest_pdf(str(self.wiki),str(self.source),"sources/資料.md")
        result = engine.search(str(self.wiki),"checkpoint",limit=4)
        self.assertEqual([row["page"] for row in result["results"]],[4,3,2,1])
        self.assertEqual([row["rerank_score"] for row in result["results"]],[3.,2.,1.,0.])
        filtered = Config({**values,"min_rerank_score":4})
        self.assertEqual(config.fingerprint,filtered.fingerprint)
        result = Engine(filtered,embedder=Embedder(),reranker=Reranker()).search(str(self.wiki),"checkpoint",limit=4)
        self.assertEqual(result["results"],[])
        self.assertTrue(result["abstained"])

    def test_reranker_rejects_invalid_output(self):
        import numpy as np
        class Embedder:
            def encode(self, texts, **_):
                return np.tile(np.asarray([1.] + [0.] * 255, dtype=np.float32), (len(texts), 1))
        class Invalid:
            def score(self, pairs): return []
        engine = Engine(Config({**self.config.values,"reranker":"xsmall-int8"}),embedder=Embedder(),reranker=Invalid())
        engine.ingest_pdf(str(self.wiki),str(self.source),"sources/資料.md")
        with self.assertRaisesRegex(ValueError,"リランカー"):
            engine.search(str(self.wiki),"checkpoint")

    def test_retrieval_configuration_is_validated(self):
        for values in [{"reranker":"other"},{"rerank_limit":0},{"min_rerank_score":0},
                       {"reranker":"tiny-int8","min_rerank_score":float("nan")},{"search_nprobes":0}]:
            with self.assertRaises(ValueError):
                Config({**self.config.values,**values})


    def test_registration_requires_an_absolute_pdf_path(self):
        (self.refs / "メモ.txt").write_text("PDF ではない", encoding="utf-8")
        (self.refs / "フォルダ.pdf").mkdir()
        inside = self.config.data_dir / "派生.pdf"
        inside.parent.mkdir(parents=True, exist_ok=True)
        self.make_pdf(inside, "derived data")
        for source in ("資料.pdf", "local:資料.pdf", str(self.refs / "ない.pdf"), str(self.refs / "メモ.txt"),
                       str(self.refs / "フォルダ.pdf"), r"\\server\share\資料.pdf", str(inside), ""):
            with self.subTest(source=source), self.assertRaises(ValueError):
                self.jobs.register(self.config, str(self.wiki), source, "sources/資料.md")
        if sys.platform == "win32":
            with self.assertRaises(ValueError):
                self.jobs.register(self.config, str(self.wiki), "//server/share/資料.pdf", "sources/資料.md")

    def test_pdf_anywhere_is_accepted_and_raw_is_posix_with_sha256(self):
        elsewhere = self.root / "別の場所" / "深い" / "本.pdf"
        elsewhere.parent.mkdir(parents=True)
        self.make_pdf(elsewhere, "Anywhere on the drive")
        job = self.jobs.register(self.config, str(self.wiki), str(elsewhere), "sources/本.md")
        self.assertEqual(job["source"], str(elsewhere.resolve()))
        result = self.engine().ingest_pdf(str(self.wiki), str(elsewhere), "sources/本.md")
        self.assertEqual(result["raw"], elsewhere.resolve().as_posix())
        self.assertNotIn("\\", result["raw"])
        self.assertEqual(result["sha256"], hashlib.sha256(elsewhere.read_bytes()).hexdigest())
        found = self.engine().search(str(self.wiki), "Anywhere", limit=1)["results"][0]
        self.assertEqual((found["raw"], found["sha256"]), (result["raw"], result["sha256"]))

    def test_file_that_is_not_a_pdf_is_rejected_when_read(self):
        fake = self.refs / "偽物.pdf"
        fake.write_bytes(b"not a pdf at all")
        self.jobs.register(self.config, str(self.wiki), str(fake), "sources/偽物.md")
        with self.assertRaisesRegex(ValueError, "%PDF- がないか、最初の %PDF- の前に 1024 バイトを超えるバイトがある"):
            self.engine().ingest_pdf(str(self.wiki), str(fake), "sources/偽物.md")

    def test_pdf_with_leading_newline_is_ingested(self):
        # 検証データに、先頭に改行 1 バイト（\n%PDF-1.5）がある PDF があった。PDFium は開けるので拒まない。
        leading = self.refs / "先頭に改行.pdf"
        self.make_pdf(leading, "Leading newline")
        leading.write_bytes(b"\n" + leading.read_bytes())
        self.jobs.register(self.config, str(self.wiki), str(leading), "sources/先頭に改行.md")
        result = self.engine().ingest_pdf(str(self.wiki), str(leading), "sources/先頭に改行.md")
        self.assertEqual(result["pages"], 4)
        # ハッシュと抽出は、前置きを含む読んだままのバイト列に対して行う。
        self.assertEqual(result["sha256"], hashlib.sha256(leading.read_bytes()).hexdigest())
        found = self.engine().search(str(self.wiki), "Leading newline", limit=1)["results"][0]
        self.assertEqual(found["sha256"], result["sha256"])

    def test_pdf_header_may_start_up_to_1024_bytes_in(self):
        import pypdfium2 as pdfium
        from rag_index import PDF_HEADER_OFFSET_LIMIT, read_pdf
        self.assertEqual(PDF_HEADER_OFFSET_LIMIT, 1024)
        original = self.refs / "元.pdf"
        self.make_pdf(original, "Offset", pages=1)
        body = original.read_bytes()
        for prefix in (b"\r\n", b" \t\n", b" " * 1024):
            with self.subTest(prefix=len(prefix)):
                path = self.refs / f"前置き{len(prefix)}.pdf"
                path.write_bytes(prefix + body)
                data, _ = read_pdf(path)
                self.assertEqual(data, prefix + body)
                # 受け付けたものは PDFium でも開ける（境界が PDFium とずれたら、ここで気づく）。
                with pdfium.PdfDocument(data) as document:
                    self.assertEqual(len(document), 1)
        too_far = self.refs / "前置き1025.pdf"
        too_far.write_bytes(b" " * 1025 + body)
        with self.assertRaisesRegex(ValueError, "%PDF- がないか、最初の %PDF- の前に 1024 バイトを超えるバイトがある"):
            read_pdf(too_far)
        # 拒むものは PDFium でも開けない。
        with self.assertRaises(pdfium.PdfiumError):
            pdfium.PdfDocument(too_far.read_bytes())

    def test_completed_job_is_not_reused_when_registered_again(self):
        first = self.register()
        self.assertEqual(self.register()["job_id"], first["job_id"])
        self.jobs.claim("owner")
        self.assertEqual(self.register()["job_id"], first["job_id"])
        self.jobs.finish(first["job_id"], "owner", result={"pages": 4})
        # 大きさと更新時刻を変えずに中身を差し替えても、取り込み直せる。
        second = self.register()
        self.assertNotEqual(second["job_id"], first["job_id"])
        self.assertEqual(second["status"], "queued")
        self.assertEqual(self.register()["job_id"], second["job_id"])
        self.assertEqual(self.jobs.claim("next")["id"], second["job_id"])

    def test_nfc_and_nfd_names_are_different_locations(self):
        nfc = self.refs / (unicodedata.normalize("NFC", "ガイド") + ".pdf")
        nfd = self.refs / (unicodedata.normalize("NFD", "ガイド") + ".pdf")
        self.make_pdf(nfc, "Composed name")
        self.make_pdf(nfd, "Decomposed name")
        if len([name for name in os.listdir(self.refs) if name.endswith(".pdf") and name != "資料.pdf"]) != 2:
            self.skipTest("このファイルシステムは NFC と NFD の名前を同じファイルとして扱う")
        engine = self.engine()
        first = engine.ingest_pdf(str(self.wiki), str(nfc), "sources/nfc.md")
        second = engine.ingest_pdf(str(self.wiki), str(nfd), "sources/nfd.md")
        self.assertNotEqual(first["sha256"], second["sha256"])
        self.assertEqual(second["review_pages"], [])
        self.assertEqual(engine.status(str(self.wiki))["documents"], 2)

    def test_old_version_points_to_the_copy_that_still_has_it(self):
        copy = self.refs / "写し.pdf"
        copy.write_bytes(self.source.read_bytes())
        engine = self.engine()
        original = engine.ingest_pdf(str(self.wiki), str(self.source), "sources/資料.md")
        engine.ingest_pdf(str(self.wiki), str(copy), "sources/写し.md")
        self.make_pdf(copy, "Rewritten edition")
        engine.ingest_pdf(str(self.wiki), str(copy), "sources/写し.md")
        results = engine.search(str(self.wiki), "checkpoint", limit=20)["results"]
        old = [row for row in results if row["sha256"] == original["sha256"]]
        self.assertTrue(old)
        self.assertTrue(all(row["raw"] == self.source.resolve().as_posix() for row in old))

    def test_data_from_version_0_3_is_not_opened(self):
        data_dir = self.root / "old-data"
        (data_dir / "wikis" / "abc").mkdir(parents=True)
        (data_dir / "jobs.sqlite").write_bytes(b"not a database of this version")
        jobs = Jobs(data_dir)
        self.assertEqual(sorted(Path(path).name for path in jobs.legacy_data()), ["jobs.sqlite", "wikis"])
        config = Config({**self.config.values, "data_dir": str(data_dir), "reference_roots": {"old": str(self.refs)}})
        self.assertNotIn("reference_roots", config.snapshot())
        self.assertFalse(jobs.unfinished())
        jobs.register(config, str(self.wiki), str(self.source), "sources/資料.md")
        self.assertEqual(config.workspace(str(self.wiki)).parent.name, "wikis-v2")


    def test_hard_link_alias_follows_the_new_version(self):
        alias = self.refs / "別名.pdf"
        try:
            os.link(self.source, alias)
        except OSError:
            self.skipTest("このファイルシステムはハードリンクを作れない")
        engine = self.engine()
        old = engine.ingest_pdf(str(self.wiki), str(self.source), "sources/資料.md")
        engine.ingest_pdf(str(self.wiki), str(alias), "sources/別名.md")
        self.make_pdf(alias, "Rewritten through alias")  # 同じファイルなので、資料.pdf も書き換わる
        new = engine.ingest_pdf(str(self.wiki), str(alias), "sources/別名.md")
        self.assertNotEqual(old["sha256"], new["sha256"])
        self.assertEqual(engine.status(str(self.wiki))["documents"], 1)
        results = engine.search(str(self.wiki), "Rewritten checkpoint", limit=20)["results"]
        self.assertTrue(results)
        self.assertTrue(all(row["sha256"] == new["sha256"] for row in results))

    def test_replacement_recovers_cleanup_after_catalog_publication(self):
        class AbruptStop(BaseException):
            pass

        engine = self.engine()
        old = engine.ingest_pdf(str(self.wiki), str(self.source), "sources/資料.md")
        folder = self.config.workspace(str(self.wiki))
        table = engine._table(folder)
        delete = type(table).delete

        def stop_before_delete(current, predicate):
            if old['sha256'] in predicate:
                with engine._catalog(folder) as catalog:
                    self.assertEqual(catalog.execute('SELECT COUNT(*) FROM documents WHERE doc_id=?', (old['sha256'],)).fetchone()[0], 0)
                raise AbruptStop('公開した台帳のコミット直後に停止')
            return delete(current, predicate)

        self.make_pdf(self.source, 'Replacement published before cleanup')
        with patch.object(type(table), 'delete', stop_before_delete):
            with self.assertRaises(AbruptStop):
                engine.ingest_pdf(str(self.wiki), str(self.source), "sources/資料.md")
        self.assertGreater(engine._table(folder).count_rows(f"doc_id = '{old['sha256']}'"), 0)
        with patch.object(engine.embedder, 'encode', side_effect=AssertionError('確定済みベクトルを再計算した')):
            result = engine.ingest_pdf(str(self.wiki), str(self.source), "sources/資料.md")
        self.assertEqual(result['status'], 'unchanged')
        self.assertIsNone(result['cleanup_error'])
        self.assertEqual(engine._table(folder).count_rows(f"doc_id = '{old['sha256']}'"), 0)
        self.assertEqual(engine._table(folder).count_rows(), result['chunks'])

    def test_maintenance_retries_retirement_after_cleanup_error(self):
        engine = self.engine()
        old = engine.ingest_pdf(str(self.wiki), str(self.source), "sources/資料.md")
        folder = self.config.workspace(str(self.wiki))
        table = engine._table(folder)
        self.make_pdf(self.source, 'Replacement with deferred cleanup')
        with patch.object(type(table), 'delete', side_effect=RuntimeError('後始末の一時的な失敗')):
            result = engine.ingest_pdf(str(self.wiki), str(self.source), "sources/資料.md")
        self.assertIn('一時的', result['cleanup_error'])
        engine.maintain_indexes(str(self.wiki))
        self.assertEqual(engine._table(folder).count_rows(f"doc_id = '{old['sha256']}'"), 0)
        with engine._catalog(folder) as catalog:
            self.assertEqual(catalog.execute('SELECT COUNT(*) FROM retired_documents').fetchone()[0], 0)

    def test_pending_retirement_keeps_reactivated_document(self):
        engine = self.engine()
        original = self.source.read_bytes()
        old = engine.ingest_pdf(str(self.wiki), str(self.source), "sources/資料.md")
        folder = self.config.workspace(str(self.wiki))
        table = engine._table(folder)
        self.make_pdf(self.source, 'Temporary replacement before returning to original')
        with patch.object(type(table), 'delete', side_effect=RuntimeError('後始末を保留')):
            replacement = engine.ingest_pdf(str(self.wiki), str(self.source), "sources/資料.md")
        self.source.write_bytes(original)
        restored = engine.ingest_pdf(str(self.wiki), str(self.source), "sources/資料.md")
        self.assertEqual(restored['sha256'], old['sha256'])
        self.assertIsNone(restored['cleanup_error'])
        self.assertEqual(engine._table(folder).count_rows(), restored['chunks'])
        self.assertEqual(engine._table(folder).count_rows(f"doc_id = '{replacement['sha256']}'"), 0)

    def test_retirement_does_not_invalidate_a_resumable_embedding_cursor(self):
        engine = self.engine()
        original = self.source.read_bytes()
        old = engine.ingest_pdf(str(self.wiki), str(self.source), "sources/資料.md")
        folder = self.config.workspace(str(self.wiki))
        table = engine._table(folder)
        self.make_pdf(self.source, 'Replacement leaving cleanup pending')
        with patch.object(type(table), 'delete', side_effect=RuntimeError('後始末を保留')):
            engine.ingest_pdf(str(self.wiki), str(self.source), "sources/資料.md")
        self.source.write_bytes(original)

        def interrupt_partial_embedding(phase, completed, total):
            if phase == '埋め込み' and completed == 1:
                raise RuntimeError('再取り込みの最初のバッチ後に停止')

        with self.assertRaisesRegex(RuntimeError, '最初のバッチ'):
            engine.ingest_pdf(str(self.wiki), str(self.source), "sources/資料.md", progress=interrupt_partial_embedding)
        other = self.refs / 'other.pdf'
        self.make_pdf(other, 'Unrelated document triggers deferred cleanup')
        engine.ingest_pdf(str(self.wiki), str(other), 'sources/other.md')
        resumed = engine.ingest_pdf(str(self.wiki), str(self.source), "sources/資料.md")
        self.assertEqual(resumed['sha256'], old['sha256'])
        self.assertEqual(engine._table(folder).count_rows(f"doc_id = '{old['sha256']}'"), resumed['chunks'])

    def test_index_reset_defers_only_cache_retirement(self):
        engine = self.engine()
        engine.ingest_pdf(str(self.wiki), str(self.source), "sources/資料.md")
        folder = self.config.workspace(str(self.wiki))
        table = engine._table(folder)
        self.make_pdf(self.source, 'Replacement with retirement across index reset')
        with patch.object(type(table), 'delete', side_effect=RuntimeError('後始末を保留')):
            engine.ingest_pdf(str(self.wiki), str(self.source), "sources/資料.md")
        changed = Config({**self.config.values, 'chunk_chars': 600})
        reset = Engine(changed, embedder=engine.embedder)
        with reset._catalog(folder) as catalog:
            self.assertEqual(catalog.execute('SELECT COUNT(*) FROM retired_documents').fetchone()[0], 1)
            reset._reset_index(folder, catalog, reset._stale_policy(folder))
            self.assertEqual(catalog.execute('SELECT rows_pending FROM retired_documents').fetchone()[0], 0)
        reset.maintain_indexes(str(self.wiki))
        with reset._catalog(folder) as catalog:
            self.assertEqual(catalog.execute('SELECT COUNT(*) FROM retired_documents').fetchone()[0], 0)

    def test_reactivation_reuses_saved_ocr_pages(self):
        cfg = Config({**self.config.values, 'ocr_mode': 'always'})
        engine = Engine(cfg, embedder=self.engine().embedder)
        original = self.source.read_bytes()
        with patch('rag_pdf.ocr_page', return_value='保存した OCR 本文。再登録でもこの結果を使う。') as ocr:
            old = engine.ingest_pdf(str(self.wiki), str(self.source), 'sources/資料.md')
            self.assertEqual(ocr.call_count, 4)
        cache = cfg.extraction_dir(old['sha256'])
        saved = {p.name: (p.read_bytes(), p.stat().st_mtime_ns) for p in cache.glob('page-*.json')}
        table = engine._table(cfg.workspace(str(self.wiki)))
        self.make_pdf(self.source, 'Replacement pending cleanup before OCR reuse')
        with patch.object(type(table), 'delete', side_effect=RuntimeError('後始末を保留')), \
                patch('rag_pdf.ocr_page', return_value='差し替えた資料の OCR 本文。'):
            engine.ingest_pdf(str(self.wiki), str(self.source), 'sources/資料.md')
        self.source.write_bytes(original)
        with patch('rag_pdf.ocr_page', side_effect=AssertionError('保存済み OCR を再実行した')):
            restored = engine.ingest_pdf(str(self.wiki), str(self.source), 'sources/資料.md')
        self.assertEqual(restored['sha256'], old['sha256'])
        self.assertEqual(saved, {p.name: (p.read_bytes(), p.stat().st_mtime_ns) for p in cache.glob('page-*.json')})

    def test_reset_reclaims_retired_extraction_cache(self):
        engine = self.engine()
        old = engine.ingest_pdf(str(self.wiki), str(self.source), 'sources/資料.md')
        cache = self.config.extraction_dir(old['sha256'])
        table = engine._table(self.config.workspace(str(self.wiki)))
        self.make_pdf(self.source, 'Replacement pending cleanup before model reset')
        with patch.object(type(table), 'delete', side_effect=RuntimeError('後始末を保留')):
            current = engine.ingest_pdf(str(self.wiki), str(self.source), 'sources/資料.md')
        self.assertTrue(cache.exists())
        changed = Config({**self.config.values, 'chunk_chars': 600})
        reset = Engine(changed, embedder=engine.embedder)
        result = reset.ingest_pdf(str(self.wiki), str(self.source), 'sources/資料.md')
        self.assertTrue(result['index_reset'])
        self.assertFalse(cache.exists())
        self.assertTrue(changed.extraction_dir(current['sha256']).exists())

    def test_retirement_migrates_an_existing_two_column_ledger(self):
        import sqlite3
        import threading
        engine = self.engine()
        folder = self.config.workspace(str(self.wiki))
        folder.mkdir(parents=True, exist_ok=True)
        with sqlite3.connect(folder / 'catalog.sqlite') as catalog:
            catalog.execute('CREATE TABLE retired_documents(doc_id TEXT PRIMARY KEY,legacy_generations TEXT NOT NULL)')
            catalog.execute('INSERT INTO retired_documents VALUES (?,?)', ('a' * 64, '["legacy-generation"]'))
        def read():
            with engine._catalog(folder) as catalog:
                return tuple(catalog.execute('SELECT * FROM retired_documents').fetchone())
        barrier = threading.Barrier(2)
        statements = []
        connect = sqlite3.connect
        def overlapping_migration(*args, **kwargs):
            catalog = connect(*args, **kwargs)
            def trace(sql):
                statements.append(sql)
                if sql == 'BEGIN IMMEDIATE':
                    barrier.wait(timeout=10)
            catalog.set_trace_callback(trace)
            return catalog
        with patch('rag_index.sqlite3.connect', overlapping_migration), concurrent.futures.ThreadPoolExecutor(2) as pool:
            rows = list(pool.map(lambda _: read(), range(2)))
        self.assertEqual(rows, [('a' * 64, '["legacy-generation"]', 1)] * 2)
        self.assertEqual(statements.count('BEGIN IMMEDIATE'), 2)
        self.assertEqual(sum(sql.startswith('ALTER TABLE retired_documents') for sql in statements), 1)

    def test_retired_cache_survives_other_wiki_and_is_reclaimed_after_last_reference(self):
        engine = self.engine()
        old = engine.ingest_pdf(str(self.wiki), str(self.source), 'sources/資料.md')
        other = self.root / 'other-wiki'
        other.mkdir()
        (other / 'SCHEMA.md').write_text('# 別の wiki\n', encoding='utf-8')
        engine.ingest_pdf(str(other), str(self.source), 'sources/資料.md')
        cache = self.config.extraction_dir(old['sha256'])
        saved = {p.name: p.read_bytes() for p in cache.glob('page-*.json')}
        self.make_pdf(self.source, 'Replacement still shared by another wiki')
        engine.ingest_pdf(str(self.wiki), str(self.source), 'sources/資料.md')
        changed = Config({**self.config.values, 'chunk_chars': 600})
        reset = Engine(changed, embedder=engine.embedder)
        reset.ingest_pdf(str(self.wiki), str(self.source), 'sources/資料.md')
        self.assertEqual(saved, {p.name: p.read_bytes() for p in cache.glob('page-*.json')})
        folder = changed.workspace(str(self.wiki))
        with reset._catalog(folder) as catalog:
            self.assertEqual(catalog.execute('SELECT rows_pending FROM retired_documents WHERE doc_id=?', (old['sha256'],)).fetchone()[0], 0)
        engine.ingest_pdf(str(other), str(self.source), 'sources/資料.md')
        self.assertFalse(cache.parent.exists())
        reset.maintain_indexes(str(self.wiki))
        with reset._catalog(folder) as catalog:
            self.assertEqual(catalog.execute('SELECT COUNT(*) FROM retired_documents').fetchone()[0], 0)

    def test_reset_retries_locked_cache_without_invalidating_new_rows_or_cursor(self):
        engine = self.engine()
        old = engine.ingest_pdf(str(self.wiki), str(self.source), 'sources/資料.md')
        cache = self.config.extraction_dir(old['sha256'])
        folder = self.config.workspace(str(self.wiki))
        table = engine._table(folder)
        row = table.search().where(f"doc_id = '{old['sha256']}'").limit(1).to_list()[0]
        self.make_pdf(self.source, 'Replacement before a locked cache reset')
        with patch.object(type(table), 'delete', side_effect=RuntimeError('後始末を保留')):
            engine.ingest_pdf(str(self.wiki), str(self.source), 'sources/資料.md')
        with engine._catalog(folder) as catalog:
            generations = json.loads(catalog.execute('SELECT legacy_generations FROM retired_documents').fetchone()[0])
        legacy = folder / 'extracted' / generations[0]
        legacy.mkdir(parents=True)
        (legacy / 'page-000001.json').write_bytes(b'{}')
        changed = Config({**self.config.values, 'chunk_chars': 600})
        reset = Engine(changed, embedder=engine.embedder)
        generation = changed.generation(old['sha256'])
        with engine._extraction_lock(old['sha256']):
            with reset._catalog(folder) as catalog:
                reset._reset_index(folder, catalog, reset._stale_policy(folder))
                catalog.execute('INSERT INTO jobs VALUES (?,1,?,NULL)', (generation, 'failed'))
            row.update(generation=generation, chunk_id=f'{generation}:0')
            reset._table(folder, create=True).add([row])
            reset.maintain_indexes(str(self.wiki))
            self.assertTrue(cache.exists())
            with reset._catalog(folder) as catalog:
                self.assertEqual(catalog.execute('SELECT rows_pending FROM retired_documents').fetchone()[0], 0)
        reset.maintain_indexes(str(self.wiki))
        # ロックがなくても、失敗したジョブが再開できる間は OCR を保持する。
        self.assertTrue(cache.exists())
        with reset._catalog(folder) as catalog:
            self.assertEqual(catalog.execute('SELECT completed FROM jobs WHERE generation=?', (generation,)).fetchone()[0], 1)
            catalog.execute("UPDATE jobs SET status='complete' WHERE generation=?", (generation,))
        reset.maintain_indexes(str(self.wiki))
        self.assertFalse(cache.parent.exists())
        self.assertFalse(legacy.exists())
        self.assertEqual(reset._table(folder).count_rows(), 1)
        with reset._catalog(folder) as catalog:
            self.assertEqual(catalog.execute('SELECT completed FROM jobs WHERE generation=?', (generation,)).fetchone()[0], 1)
            self.assertEqual(catalog.execute('SELECT COUNT(*) FROM retired_documents').fetchone()[0], 0)

    def test_reset_reuses_reactivated_ocr_after_a_partial_embedding_and_another_publication(self):
        cfg = Config({**self.config.values, 'ocr_mode': 'always'})
        engine = Engine(cfg, embedder=self.engine().embedder)
        original = self.source.read_bytes()
        with patch('rag_pdf.ocr_page', return_value='再登録と設定変更でも保存済みの OCR を使う。'):
            old = engine.ingest_pdf(str(self.wiki), str(self.source), 'sources/資料.md')
        cache = cfg.extraction_dir(old['sha256'])
        saved = {p.name: (p.read_bytes(), p.stat().st_mtime_ns) for p in cache.glob('page-*.json')}
        table = engine._table(cfg.workspace(str(self.wiki)))
        self.make_pdf(self.source, 'Replacement before restoring and changing the model')
        with patch.object(type(table), 'delete', side_effect=RuntimeError('後始末を保留')), \
                patch('rag_pdf.ocr_page', return_value='差し替え資料の OCR 本文。'):
            engine.ingest_pdf(str(self.wiki), str(self.source), 'sources/資料.md')
        self.source.write_bytes(original)
        changed = Config({**cfg.values, 'chunk_chars': 600})
        reset = Engine(changed, embedder=engine.embedder)
        def interrupt(phase, completed, total):
            if phase == '埋め込み' and completed == 1:
                raise RuntimeError('設定変更後の最初の保存で中断')
        with patch('rag_pdf.ocr_page', side_effect=AssertionError('保存済み OCR を再実行した')):
            with self.assertRaisesRegex(RuntimeError, '最初の保存'):
                reset.ingest_pdf(str(self.wiki), str(self.source), 'sources/資料.md', progress=interrupt)
        other = self.refs / 'unrelated.pdf'
        self.make_pdf(other, 'Another publication while OCR reingest is paused')
        with patch('rag_pdf.ocr_page', return_value='別の資料の OCR 本文。'):
            reset.ingest_pdf(str(self.wiki), str(other), 'sources/other.md')
        with patch('rag_pdf.ocr_page', side_effect=AssertionError('保存済み OCR を再実行した')):
            result = reset.ingest_pdf(str(self.wiki), str(self.source), 'sources/資料.md')
        self.assertEqual(saved, {p.name: (p.read_bytes(), p.stat().st_mtime_ns) for p in cache.glob('page-*.json')})
        self.assertEqual(reset._table(changed.workspace(str(self.wiki))).count_rows(f"doc_id = '{old['sha256']}'"), result['chunks'])

    def test_pruned_reingest_cache_is_retried_after_unlock(self):
        engine = self.engine()
        old = engine.ingest_pdf(str(self.wiki), str(self.source), 'sources/資料.md')
        cache = self.config.extraction_dir(old['sha256'])
        other = self.refs / 'other.pdf'
        self.make_pdf(other, 'Another document starts a new index')
        changed = Config({**self.config.values, 'chunk_chars': 600})
        reset = Engine(changed, embedder=engine.embedder)
        reset.ingest_pdf(str(self.wiki), str(other), 'sources/other.md')
        self.source.unlink()
        with engine._extraction_lock(old['sha256']):
            reset.ingest_pdf(str(self.wiki), str(other), 'sources/other.md')
            self.assertTrue(cache.exists())
        reset.maintain_indexes(str(self.wiki))
        self.assertFalse(cache.parent.exists())

    def test_other_wiki_keeps_ocr_for_an_interrupted_reactivation(self):
        cfg = Config({**self.config.values, 'ocr_mode': 'always'})
        engine = Engine(cfg, embedder=self.engine().embedder)
        original = self.source.read_bytes()
        foreign = self.root / 'other-wiki'
        foreign.mkdir()
        (foreign / 'SCHEMA.md').write_text('# 別の wiki\n', encoding='utf-8')
        foreign_cfg = Config({**cfg.values, 'chunk_chars': 600})
        other_engine = Engine(foreign_cfg, embedder=engine.embedder)
        with patch('rag_pdf.ocr_page', return_value='複数の wiki でも保存済み OCR を再利用する。'):
            old = engine.ingest_pdf(str(self.wiki), str(self.source), 'sources/資料.md')
            other_engine.ingest_pdf(str(foreign), str(self.source), 'sources/資料.md')
        cache = cfg.extraction_dir(old['sha256'])
        saved = {p.name: (p.read_bytes(), p.stat().st_mtime_ns) for p in cache.glob('page-*.json')}
        self.make_pdf(self.source, 'Replacement during multi-wiki OCR reuse')
        replacement = self.source.read_bytes()
        with patch('rag_pdf.ocr_page', return_value='差し替えた資料の OCR 本文。'):
            engine.ingest_pdf(str(self.wiki), str(self.source), 'sources/資料.md')
        self.source.write_bytes(original)
        def interrupt(phase, completed, total):
            if phase == '埋め込み' and completed == 1:
                raise RuntimeError('再登録の途中で停止')
        with self.assertRaisesRegex(RuntimeError, '途中で停止'):
            engine.ingest_pdf(str(self.wiki), str(self.source), 'sources/資料.md', progress=interrupt)
        self.source.write_bytes(replacement)
        with patch('rag_pdf.ocr_page', return_value='差し替えた資料の OCR 本文。'):
            other_engine.ingest_pdf(str(foreign), str(self.source), 'sources/資料.md')
        self.source.write_bytes(original)
        with patch('rag_pdf.ocr_page', side_effect=AssertionError('中断済みジョブの OCR を消した')):
            result = engine.ingest_pdf(str(self.wiki), str(self.source), 'sources/資料.md')
        self.assertEqual(saved, {p.name: (p.read_bytes(), p.stat().st_mtime_ns) for p in cache.glob('page-*.json')})
        self.assertEqual(engine._table(cfg.workspace(str(self.wiki))).count_rows(f"doc_id = '{old['sha256']}'"), result['chunks'])

    def test_cache_permission_errors_remain_retryable(self):
        engine = self.engine()
        old = engine.ingest_pdf(str(self.wiki), str(self.source), 'sources/資料.md')
        folder = self.config.workspace(str(self.wiki))
        table = engine._table(folder)
        self.make_pdf(self.source, 'Replacement before a temporary cache access error')
        with patch.object(type(table), 'delete', side_effect=RuntimeError('後始末を保留')):
            engine.ingest_pdf(str(self.wiki), str(self.source), 'sources/資料.md')
        with engine._catalog(folder) as catalog:
            generation = json.loads(catalog.execute('SELECT legacy_generations FROM retired_documents').fetchone()[0])[0]
        legacy = folder / 'extracted' / generation
        legacy.mkdir(parents=True)
        (legacy / 'page-000001.json').write_bytes(b'{}')
        cache = self.config.extraction_dir(old['sha256'])
        import shutil
        remove = shutil.rmtree
        def temporarily_denied(path, *args, **kwargs):
            if Path(path) in {cache.parent, legacy}:
                raise PermissionError('一時的なキャッシュの共有違反')
            return remove(path, *args, **kwargs)
        with patch('rag_index.shutil.rmtree', temporarily_denied):
            engine.maintain_indexes(str(self.wiki))
        self.assertTrue(cache.exists() and legacy.exists())
        engine.maintain_indexes(str(self.wiki))
        self.assertFalse(cache.parent.exists() or legacy.exists())
        with engine._catalog(folder) as catalog:
            self.assertEqual(catalog.execute('SELECT COUNT(*) FROM retired_documents').fetchone()[0], 0)

    def test_restoring_old_content_indexes_it_again(self):
        engine = self.engine()
        original_bytes = self.source.read_bytes()
        first = engine.ingest_pdf(str(self.wiki), str(self.source), "sources/資料.md")
        self.make_pdf(self.source, "Second edition")
        engine.ingest_pdf(str(self.wiki), str(self.source), "sources/資料.md")
        self.source.write_bytes(original_bytes)
        again = engine.ingest_pdf(str(self.wiki), str(self.source), "sources/資料.md")
        self.assertEqual(again["sha256"], first["sha256"])
        table = engine._table(self.config.workspace(str(self.wiki)))
        rows = table.search().where(f"doc_id = '{first['sha256']}'").limit(100).to_list()
        self.assertEqual(len(rows), again["chunks"])
        found = engine.search(str(self.wiki), "Persistent indexing checkpoint", limit=5)["results"]
        self.assertTrue(found and all(row["sha256"] == first["sha256"] for row in found))

    @unittest.skipUnless(sys.platform == "win32", "Windows のリンクの扱いの試験")
    def test_local_link_to_network_file_is_rejected(self):
        unc = Path(r"\\server\share\本.pdf")
        info = os.lstat(self.source)
        with patch.object(Path, "resolve", lambda self, strict=False: unc), \
                patch("rag_config.os.lstat", lambda path: info), \
                patch("rag_config._network_drive", lambda path: False):
            with self.assertRaisesRegex(ValueError, "ネットワーク"):
                self.config.pdf_path(str(self.refs / "リンク.pdf"))
        with patch.object(Path, "resolve", lambda self, strict=False: unc), \
                patch("rag_config.os.lstat", lambda path: info), \
                patch("rag_config._network_drive", lambda path: True):
            self.assertEqual(self.config.pdf_path("Z:/本.pdf"), unc)

    def test_file_swapped_after_registration_is_not_read(self):
        import sqlite3
        job = self.register()
        with sqlite3.connect(self.jobs.path) as db:
            dev, ino, size, mtime_ns = db.execute("SELECT dev,ino,size,mtime_ns FROM ingest_jobs WHERE id=?",
                                                  (job["job_id"],)).fetchone()
        if ino in (None, "", "0"):
            self.skipTest("このファイルシステムはファイルの識別子を返さない")
        # 同じ大きさと更新時刻の、別のファイルに差し替える。
        replacement = self.refs / "差し替え.tmp"
        replacement.write_bytes(self.source.read_bytes())
        os.utime(replacement, ns=(mtime_ns, mtime_ns))
        os.replace(replacement, self.source)
        calls, reads = [], []
        engine = self.engine()
        engine.extractor = lambda *args: calls.append(args)
        real_open = open
        def counting_open(*args, **kwargs):
            handle = real_open(*args, **kwargs)
            read = handle.read
            handle.read = lambda *a: reads.append(a) or read(*a)
            return handle
        with patch("rag_index.open", counting_open, create=True):
            with self.assertRaisesRegex(ValueError, "登録した PDF"):
                engine.ingest_pdf(str(self.wiki), str(self.source), "sources/資料.md", expected=(dev, ino, size, mtime_ns))
        self.assertEqual(reads, [])  # 本文を読む前に止まる
        self.assertEqual(calls, [])
        self.assertEqual(engine.status(str(self.wiki))["documents"], 0)

    def test_failed_job_after_publication_does_not_block_configuration(self):
        job = self.register()
        self.jobs.claim("owner")
        self.jobs.begin_publication(job["job_id"], "owner")
        self.jobs.finish(job["job_id"], "owner", error="要再確認の印を書けなかった")
        self.assertFalse(self.jobs.cancel(str(self.wiki), job["job_id"])["cancellation_accepted"])
        self.assertFalse(self.jobs.unfinished())


    def test_broken_hard_link_keeps_the_old_version(self):
        alias = self.refs / "別名.pdf"
        try:
            os.link(self.source, alias)
        except OSError:
            self.skipTest("このファイルシステムはハードリンクを作れない")
        engine = self.engine()
        old = engine.ingest_pdf(str(self.wiki), str(self.source), "sources/資料.md")
        engine.ingest_pdf(str(self.wiki), str(alias), "sources/別名.md")
        # 資料.pdf を、同じ中身の独立したファイルに置き換えて、リンクの関係を切る。
        copy = self.refs / "置き換え.tmp"
        copy.write_bytes(self.source.read_bytes())
        info = os.stat(self.source)
        os.utime(copy, ns=(info.st_atime_ns, info.st_mtime_ns))  # 台帳の大きさと更新時刻に合わせる
        os.replace(copy, self.source)
        self.make_pdf(alias, "Only the alias changes")
        engine.ingest_pdf(str(self.wiki), str(alias), "sources/別名.md")
        self.assertEqual(engine.status(str(self.wiki))["documents"], 2)
        results = engine.search(str(self.wiki), "Persistent indexing checkpoint", limit=20)["results"]
        kept = [row for row in results if row["sha256"] == old["sha256"]]
        self.assertTrue(kept)
        self.assertTrue(all(row["raw"] == self.source.resolve().as_posix() for row in kept))

    def test_job_records_the_path_as_given_and_it_can_be_ingested(self):
        given = str(self.refs / "下" / ".." / "資料.pdf")
        (self.refs / "下").mkdir()
        job = self.register_path(given)
        self.assertEqual(job["source"], given)
        result = self.engine().ingest_pdf(str(self.wiki), job["source"], "sources/資料.md")
        self.assertEqual(result["raw"], self.source.resolve().as_posix())

    def register_path(self, source):
        return self.jobs.register(self.config, str(self.wiki), source, "sources/資料.md")

    def test_paths_with_control_characters_are_rejected(self):
        for source in (str(self.refs) + "/改行\n.pdf", str(self.refs) + "/タブ\t.pdf", str(self.refs) + "/次行\x85.pdf"):
            with self.subTest(source=source), self.assertRaisesRegex(ValueError, "制御文字"):
                self.config.pdf_path(source)

    @unittest.skipUnless(sys.platform == "win32", "Windows の UNC の書き方の試験")
    def test_mixed_separator_unc_is_rejected_before_resolving(self):
        def resolve(self, strict=False):
            raise AssertionError("UNC を解決しようとした")
        with patch.object(Path, "resolve", resolve):
            for source in ("/\\server/share/本.pdf", "\\/server/share/本.pdf", "//server/share/本.pdf",
                           "\\\\?\\C:\\本.pdf", "\\\\.\\C:\\本.pdf"):
                with self.subTest(source=source), self.assertRaisesRegex(ValueError, "UNC"):
                    self.config.pdf_path(source)

    def test_same_size_and_time_with_new_content_is_indexed_again(self):
        import sqlite3
        other = self.refs / "第二版.tmp"
        self.make_pdf(other, "Persistent indexing different")
        first_bytes, second_bytes = self.source.read_bytes(), other.read_bytes()
        size = max(len(first_bytes), len(second_bytes))
        first_bytes, second_bytes = first_bytes.ljust(size, b"\n"), second_bytes.ljust(size, b"\n")
        self.source.write_bytes(first_bytes)
        engine = self.engine()
        job = self.register()
        self.jobs.claim("owner")
        first = engine.ingest_pdf(str(self.wiki), str(self.source), "sources/資料.md")
        self.jobs.finish(job["job_id"], "owner", result=first)
        info = os.stat(self.source)
        with open(self.source, "r+b") as handle:  # 同じファイルのまま中身を書き換える
            handle.write(second_bytes)
        os.utime(self.source, ns=(info.st_atime_ns, info.st_mtime_ns))
        again = self.register()
        self.assertNotEqual(again["job_id"], job["job_id"])
        with sqlite3.connect(self.jobs.path) as db:
            expected = db.execute("SELECT dev,ino,size,mtime_ns FROM ingest_jobs WHERE id=?", (again["job_id"],)).fetchone()
        second = engine.ingest_pdf(str(self.wiki), str(self.source), "sources/資料.md", expected=expected)
        self.assertNotEqual(second["sha256"], first["sha256"])
        self.assertEqual(second["sha256"], hashlib.sha256(second_bytes).hexdigest())
        self.assertEqual(engine.status(str(self.wiki))["documents"], 1)


    def test_deleted_hard_link_does_not_keep_the_old_version(self):
        alias = self.refs / "別名.pdf"
        try:
            os.link(self.source, alias)
        except OSError:
            self.skipTest("このファイルシステムはハードリンクを作れない")
        engine = self.engine()
        engine.ingest_pdf(str(self.wiki), str(self.source), "sources/資料.md")
        engine.ingest_pdf(str(self.wiki), str(alias), "sources/別名.md")
        self.source.unlink()
        self.make_pdf(alias, "Only one name is left")
        new = engine.ingest_pdf(str(self.wiki), str(alias), "sources/別名.md")
        self.assertEqual(engine.status(str(self.wiki))["documents"], 1)
        results = engine.search(str(self.wiki), "checkpoint", limit=20)["results"]
        self.assertTrue(results and all(row["sha256"] == new["sha256"] for row in results))

    def test_alias_swapped_during_ingest_keeps_the_old_version(self):
        alias = self.refs / "別名.pdf"
        try:
            os.link(self.source, alias)
        except OSError:
            self.skipTest("このファイルシステムはハードリンクを作れない")
        engine = self.engine()
        old = engine.ingest_pdf(str(self.wiki), str(self.source), "sources/資料.md")
        engine.ingest_pdf(str(self.wiki), str(alias), "sources/別名.md")
        saved = self.source.read_bytes()
        info = os.stat(self.source)
        self.make_pdf(alias, "Rewritten while ingesting")
        def swap_back(phase, completed, total):
            if phase == "埋め込み" and completed == 0:
                copy = self.refs / "戻し.tmp"
                copy.write_bytes(saved)
                os.utime(copy, ns=(info.st_atime_ns, info.st_mtime_ns))
                os.replace(copy, self.source)  # 取り込みの途中で、資料.pdf だけを古い版の独立したファイルに戻す
        engine.ingest_pdf(str(self.wiki), str(alias), "sources/別名.md", progress=swap_back)
        self.assertEqual(engine.status(str(self.wiki))["documents"], 2)
        kept = [row for row in engine.search(str(self.wiki), "Persistent indexing checkpoint", limit=20)["results"]
                if row["sha256"] == old["sha256"]]
        self.assertTrue(kept and all(row["raw"] == self.source.resolve().as_posix() for row in kept))


if __name__ == "__main__":
    unittest.main(verbosity=2)
