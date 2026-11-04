"""登録の競合、キャンセル、公開境界と索引の再開に対する回帰試験。"""
import concurrent.futures
import json
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
        from reportlab.pdfgen import canvas
        pdf = canvas.Canvas(str(self.source))
        for number in range(4):
            pdf.drawString(40, 700, "Persistent indexing checkpoint " + str(number))
            pdf.showPage()
        pdf.save()
        self.config = Config({"reference_roots": {"local": str(self.refs)}, "data_dir": str(self.root / "data"),
                              "embedding_model": "cl-nagoya/ruri-v3-30m", "ocr_mode": "off", "batch_size": 1})
        self.jobs = Jobs(self.config.data_dir)

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


if __name__ == "__main__":
    unittest.main(verbosity=2)
