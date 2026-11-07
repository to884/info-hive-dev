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
sys.path.insert(0, str(ROOT / "info-hive-rag/scripts"))
from rag_config import Config
from rag_index import Engine,Embedder
from rag_jobs import Jobs, JobCancelled
from rag_config import write_json


class JobTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory(dir=os.environ.get("RAG_TEST_RUN_ROOT", str(ROOT / ".rag-poc-data")), ignore_cleanup_errors=True)
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
        with self.assertRaisesRegex(ValueError, "%PDF-"):
            self.engine().ingest_pdf(str(self.wiki), str(fake), "sources/偽物.md")

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
        with self.assertRaisesRegex(ValueError, "登録した PDF"):
            self.engine().ingest_pdf(str(self.wiki), str(self.source), "sources/資料.md",
                                     expected=(dev, ino, size, mtime_ns))

    def test_failed_job_after_publication_does_not_block_configuration(self):
        job = self.register()
        self.jobs.claim("owner")
        self.jobs.begin_publication(job["job_id"], "owner")
        self.jobs.finish(job["job_id"], "owner", error="要再確認の印を書けなかった")
        self.assertFalse(self.jobs.cancel(str(self.wiki), job["job_id"])["cancellation_accepted"])
        self.assertFalse(self.jobs.unfinished())


if __name__ == "__main__":
    unittest.main(verbosity=2)
