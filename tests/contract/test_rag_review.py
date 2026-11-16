"""OCR の確信度と確認の契約の試験（ADR-0025 の「wiki と rag のそろい方」の 8）。

rag の依存が要るので、rag の CI（.github/workflows/rag.yml）で流す。OCR と埋め込みはスタブである。
本物の NDLOCR-Lite で確率を受け取ることは、tests/rag/verify_ocr_confidence.py で手元で確かめる（CI では読み込めない）。
"""

from __future__ import annotations

import functools
import hashlib
import json
import os
import sqlite3
import sys
import tempfile
import unittest
from contextlib import closing
from pathlib import Path
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[2]
HERE = Path(__file__).resolve().parent
for folder in (HERE, ROOT / "info-hive-rag" / "scripts"):
    sys.path.insert(0, str(folder))

import pdf_fixtures  # noqa: E402
import rag_pdf  # noqa: E402
import rag_review  # noqa: E402
from rag_config import MODELS, OCR_CONFIDENCE_REVISION, OCR_REVISION, Config  # noqa: E402
from rag_index import Engine  # noqa: E402
from rag_jobs import Jobs  # noqa: E402
from rag_ocr_confidence import ProbStr, line_records  # noqa: E402
from rag_worker import process_job  # noqa: E402


class FakeEmbedder:
    def __init__(self, dimension):
        self.dimension = dimension

    def encode(self, texts, **_):
        import numpy as np
        return np.tile(np.asarray([1.] + [0.] * (self.dimension - 1), dtype=np.float32), (len(texts), 1))


def line(text: str, confidence: float) -> dict:
    return {"text": text, "box": [0, 0, 10, 10], "vertical": False, "detector_confidence": 0.9,
            "chars": [confidence] * len(text), "eos": [confidence], "confidence": 0.0 if not text else confidence}


class StubOcr:
    """OCR の代わり。呼ばれた順に、決めた本文と行の確信度を返す（kinds.pdf では 2、3、4 ページ目の順に呼ばれる）。"""

    def __init__(self, answers):
        self.answers = list(answers)
        self.calls = 0

    def recognize(self, image):
        text, lines = self.answers[self.calls % len(self.answers)]
        self.calls += 1
        return {"ok": True, "text": text, "line_count": len(lines), "lines": lines,
                "confidence_revision": OCR_CONFIDENCE_REVISION}


# 2 ページ目は確信度が高い、3 ページ目は低い行がある、4 ページ目は読めなかった行がある
ANSWERS = [("高い確信度の本文 二", [line("高い確信度の本文 二", 0.97)]),
           ("低い確信度の本文 三", [line("低い確信度の", 0.95), line("本文 三", 0.41)]),
           ("", [line("", 0.0)])]


class Base(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory(dir=os.environ.get("RAG_TEST_RUN_ROOT"), ignore_cleanup_errors=True)
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name).resolve()
        self.pdf = self.root / "refs" / "kinds.pdf"
        self.pdf.parent.mkdir()
        pdf_fixtures.make_kinds_pdf(self.pdf)
        self.wiki = self.make_wiki("wiki")
        self.values = {"data_dir": str(self.root / "data"), "embedding_model": "cl-nagoya/ruri-v3-30m",
                       "ocr_mode": "auto", "ocr_dpi": 150, "batch_size": 4, "ocr_confidence_threshold": 0.8}

    def make_wiki(self, name: str) -> Path:
        wiki = self.root / name
        (wiki / "sources").mkdir(parents=True)
        (wiki / "SCHEMA.md").write_text("# 試験\n", encoding="utf-8")
        return wiki

    @property
    def config(self) -> Config:
        return Config(self.values)

    def engine(self, answers=ANSWERS, embedder=None) -> Engine:
        self.ocr = StubOcr(answers)
        return Engine(self.config, embedder=embedder or FakeEmbedder(MODELS[self.config.model]),
                      extractor=functools.partial(rag_pdf.extract_pages, ocr_client=self.ocr))

    @property
    def doc_id(self) -> str:
        return hashlib.sha256(self.pdf.read_bytes()).hexdigest()

    def ingest_job(self, engine: Engine, wiki: Path | None = None) -> tuple[Jobs, str]:
        jobs = Jobs(self.config.data_dir)
        registered = jobs.register(self.config, str(wiki or self.wiki), str(self.pdf), "sources/kinds.md")
        job = jobs.claim("試験")
        process_job(jobs, "試験", job, engine)
        status = jobs.status(str(wiki or self.wiki), registered["job_id"])
        self.assertEqual(status["status"], "completed", status["error"])
        return jobs, registered["job_id"]

    def run_queued(self, jobs: Jobs, engine: Engine) -> list[dict]:
        done = []
        while (job := jobs.claim("試験")) is not None:
            process_job(jobs, "試験", job, engine)
            done.append(jobs.status(job["wiki"], job["id"]))
        return done

    def decide(self, wiki: Path, base: int, items: list[dict]) -> int:
        """MCP の decide_ocr_pages と同じに、台帳に書いてから作り直しのジョブを登録する。"""
        version = rag_review.decide(self.config, str(wiki), self.doc_id, base, items)
        Jobs(self.config.data_dir).register_rebuild(self.config, str(wiki), self.doc_id, version)
        return version

    def item(self, wiki: Path, page: int, action: str, text: str | None = None) -> dict:
        detail = rag_review.page_detail(self.config, str(wiki), self.doc_id, page)
        return {"page": page, "action": action, "text": text, "decided_by": "user", "ocr_sha256": detail["ocr_sha256"]}

    def ledger_version(self, wiki: Path | None = None) -> int:
        return rag_review.Ledger(self.config.workspace(str(wiki or self.wiki))).version(self.doc_id)

    def search_texts(self, engine: Engine, wiki: Path, query: str) -> list[dict]:
        return engine.search(str(wiki), query, limit=20)["results"]

    def report(self, jobs: Jobs, wiki: Path, job_id: str) -> dict:
        return jobs.status(str(wiki), job_id, threshold=self.config.ocr_confidence_threshold)["result"]["page_report"]


class ConfidenceTests(Base):
    def test_line_invariants(self):
        """文字の確率の数は本文の文字の数、終わりの記号の確率の数は読みの数以下。分けて読んだ行も同じ。"""
        left = ProbStr("あい", [0.9, 0.8], [0.7], 1)
        right = ProbStr("うえお", [0.6, 0.95, 0.9], [], 1)  # 最大の長さに達して終わりの記号がない読み
        joined = left + right
        self.assertEqual((str(joined), joined.reads, joined.eos), ("あいうえお", 2, [0.7]))
        box = [[0, 0], [0, 10], [50, 0], [50, 10]]
        records = line_records([{"text": joined, "boundingBox": box}, {"text": ProbStr("", [], [0.99], 1), "boundingBox": box},
                                {"text": "", "boundingBox": box}, {"text": ProbStr("か", [0.9, 0.9], [], 1), "boundingBox": box}])
        self.assertEqual(records[0]["confidence"], 0.6)
        self.assertEqual((records[1]["confidence"], records[1].get("unreadable")), (0.0, True))  # 読めなかった行
        self.assertIsNone(records[2]["confidence"])  # 確率のない行は不明
        self.assertEqual(records[3].get("invariant"), "broken")  # 不変条件を満たさない行は不明

    def test_only_pages_below_the_threshold_are_low(self):
        jobs, job_id = self.ingest_job(self.engine())
        lists = self.report(jobs, self.wiki, job_id)["lists"]
        self.assertEqual(lists["ocr_low_confidence"]["ranges"], "3-4")  # 3 は低い行、4 は読めなかった行
        self.assertEqual(lists["ocr_unknown_confidence"]["ranges"], "")
        self.assertEqual(lists["review:pending"]["ranges"], "3-4")
        report = self.report(jobs, self.wiki, job_id)
        self.assertEqual((report["confidence"]["threshold"], report["confidence"]["threshold_calibrated"]), (0.8, False))

    def test_adopted_ocr_without_probabilities_is_unknown(self):
        legacy = self.config.extraction_root / self.doc_id / f"auto-150-{OCR_REVISION[:12]}-extract-v1"
        legacy.mkdir(parents=True)
        for number in (2, 3, 4):
            (legacy / f"page-{number:06d}.json").write_text(json.dumps(
                {"page": number, "text": f"移した {number}", "quality": {}, "ocr": True, "ocr_empty": False},
                ensure_ascii=False), encoding="utf-8")
        jobs, job_id = self.ingest_job(self.engine())
        self.assertEqual(self.ocr.calls, 0)
        lists = self.report(jobs, self.wiki, job_id)["lists"]
        self.assertEqual(lists["ocr_unknown_confidence"]["ranges"], "2-4")
        self.assertEqual(lists["ocr_low_confidence"]["ranges"], "")
        self.assertEqual(lists["review:pending"]["ranges"], "")  # 不明は低いとも高いとも扱わない


class ReviewTests(Base):
    def test_two_wikis_keep_their_own_decisions(self):
        other = self.make_wiki("other")
        engine = self.engine()
        jobs, _ = self.ingest_job(engine)
        self.ingest_job(engine, other)
        shared = self.config.extraction_dir(self.doc_id)
        before = {path.name: path.read_bytes() for path in shared.iterdir() if path.is_file()}
        self.decide(self.wiki, 0, [self.item(self.wiki, 3, "fix", "直した本文 三")])
        self.decide(other, 0, [self.item(other, 3, "reject")])
        self.run_queued(jobs, engine)
        fixed = self.search_texts(engine, self.wiki, "直した本文")
        self.assertTrue(any(row["page"] == 3 and "直した本文" in row["text"] for row in fixed))
        self.assertFalse(any(row["page"] == 3 for row in self.search_texts(engine, other, "低い確信度の本文")))
        self.assertFalse(any(row["page"] == 3 for row in self.search_texts(engine, other, "却下")))
        # 返す本文は、その wiki の確認を当てた本文
        mine = engine.ingest_pdf(str(self.wiki), str(self.pdf), "sources/kinds.md")
        theirs = engine.ingest_pdf(str(other), str(self.pdf), "sources/kinds.md")
        self.assertIn("直した本文 三", Path(mine["extracted_markdown"]).read_text(encoding="utf-8"))
        self.assertIn(rag_review.REJECTED_LINE, Path(theirs["extracted_markdown"]).read_text(encoding="utf-8"))
        # 共有の抽出の結果は変わらない
        self.assertEqual({path.name: path.read_bytes() for path in shared.iterdir() if path.is_file()}, before)

    def test_stale_sha_or_version_is_refused(self):
        engine = self.engine()
        self.ingest_job(engine)
        stale = {**self.item(self.wiki, 3, "accept"), "ocr_sha256": "0" * 64}
        with self.assertRaisesRegex(ValueError, "確かめたときと違います"):
            self.decide(self.wiki, 0, [stale])
        self.decide(self.wiki, 0, [self.item(self.wiki, 3, "accept")])
        with self.assertRaisesRegex(ValueError, "台帳の版が 1"):
            self.decide(self.wiki, 0, [self.item(self.wiki, 4, "accept")])

    def test_interrupted_rebuild_keeps_the_previous_rows_and_retry_publishes(self):
        engine = self.engine()
        jobs, job_id = self.ingest_job(engine)
        self.decide(self.wiki, 0, [self.item(self.wiki, 3, "fix", "直した本文 三")])

        def stop(phase, completed, total):
            if phase == "埋め込み" and completed >= 1:
                raise RuntimeError("作り直しの途中で止まった")
        with self.assertRaisesRegex(RuntimeError, "途中で止まった"):
            engine.rebuild_reviewed(str(self.wiki), self.doc_id, progress=stop)
        self.assertTrue(any("低い確信度の本文" in row["text"] for row in self.search_texts(engine, self.wiki, "低い確信度")))
        report = self.report(jobs, self.wiki, job_id)
        self.assertEqual(report["lists"]["review:awaiting_publish"]["ranges"], "3")
        self.assertEqual((report["review"]["ledger_version"], report["review"]["published_version"]), (1, 0))
        results = self.search_texts(engine, self.wiki, "低い確信度")
        self.assertTrue(any((row["review"] or {}).get("awaiting_publish") for row in results if row["page"] == 3))
        engine.rebuild_reviewed(str(self.wiki), self.doc_id)  # 再試行すると新しい版が公開される
        self.assertTrue(any("直した本文" in row["text"] for row in self.search_texts(engine, self.wiki, "直した本文")))
        self.assertEqual(self.report(jobs, self.wiki, job_id)["review"]["published_version"], 1)
        # 前の版の行と途中経過は残らない
        folder = self.config.workspace(str(self.wiki))
        generations = {row["generation"] for row in engine._table(folder).search().where(f"doc_id = '{self.doc_id}'").limit(1000).to_list()}
        self.assertEqual(generations, {self.config.generation(self.doc_id, 1)})
        with closing(sqlite3.connect(folder / "catalog.sqlite")) as db:
            self.assertNotIn(self.config.generation(self.doc_id, 0), {row[0] for row in db.execute("SELECT generation FROM jobs")})

    def test_decision_accepted_while_rebuilding_is_published_too(self):
        engine = self.engine()
        jobs, _ = self.ingest_job(engine)
        self.decide(self.wiki, 0, [self.item(self.wiki, 3, "accept")])
        jobs.register_rebuild(self.config, str(self.wiki), self.doc_id, self.ledger_version())
        original = engine.rebuild_reviewed

        def rebuild_then_decide(*args, **kwargs):
            result = original(*args, **kwargs)
            # 作り直しが最後に台帳を読んだあと、終わりを書く前に、次の確認を受け付ける
            self.decide(self.wiki, 1, [self.item(self.wiki, 4, "fix", "直した本文 四")])
            jobs.register_rebuild(self.config, str(self.wiki), self.doc_id, self.ledger_version())
            engine.rebuild_reviewed = original
            return result
        engine.rebuild_reviewed = rebuild_then_decide
        self.run_queued(jobs, engine)
        state = engine.status(str(self.wiki))
        self.assertEqual(state["review"]["awaiting_publish_pages"], 0)
        with closing(sqlite3.connect(self.config.workspace(str(self.wiki)) / "catalog.sqlite")) as db:
            self.assertEqual(db.execute("SELECT review_version FROM documents").fetchone()[0], 2)

    def test_rejecting_the_only_page_publishes_an_empty_version(self):
        from reportlab.pdfgen import canvas
        c = canvas.Canvas(str(self.pdf), invariant=1)
        c.setFont("Helvetica", 12)
        c.drawString(60, 700, "only page")
        c.showPage()
        c.save()
        self.values["ocr_mode"] = "always"
        engine = self.engine(answers=[("唯一のページ", [line("唯一のページ", 0.3)])])
        jobs, job_id = self.ingest_job(engine)
        self.decide(self.wiki, 0, [self.item(self.wiki, 1, "reject")])
        done = self.run_queued(jobs, engine)
        self.assertEqual(done[-1]["status"], "completed", done[-1]["error"])
        self.assertEqual(self.search_texts(engine, self.wiki, "唯一のページ"), [])
        with closing(sqlite3.connect(self.config.workspace(str(self.wiki)) / "catalog.sqlite")) as db:
            self.assertEqual(db.execute("SELECT chunks, review_version FROM documents").fetchone(), (0, 1))

    def test_decisions_survive_reindexing_and_go_stale_when_the_ocr_changes(self):
        engine = self.engine()
        jobs, _ = self.ingest_job(engine)
        self.decide(self.wiki, 0, [self.item(self.wiki, 3, "fix", "直した本文 三")])
        self.run_queued(jobs, engine)
        with patch("rag_config.EXTRACT_REVISION", "extract-v3"):  # 抽出の版を上げて取り込み直す
            again = engine.ingest_pdf(str(self.wiki), str(self.pdf), "sources/kinds.md")
            self.assertTrue(again["index_reset"])
            self.assertIn("直した本文 三", Path(again["extracted_markdown"]).read_text(encoding="utf-8"))
        # OCR をやり直して本文が変わると、そのページは確認待ちに戻る
        changed = [ANSWERS[0], ("別の OCR の本文 三", [line("別の OCR の本文 三", 0.5)]), ANSWERS[2]]
        engine = self.engine(answers=changed)
        with patch("rag_config.render_identity", lambda dpi: {"pypdfium2": "9.9.9", "dpi": dpi}), \
                patch("rag_pdf.render_identity", lambda dpi: {"pypdfium2": "9.9.9", "dpi": dpi}), \
                patch("rag_config.EXTRACT_REVISION", "extract-v4"):
            third = engine.ingest_pdf(str(self.wiki), str(self.pdf), "sources/kinds.md")
            self.assertNotIn("直した本文 三", Path(third["extracted_markdown"]).read_text(encoding="utf-8"))
            detail = rag_review.page_detail(Config(self.values), str(self.wiki), self.doc_id, 3)
        self.assertEqual(detail["state"], "stale")

    def test_search_marks_pending_pages(self):
        engine = self.engine()
        self.ingest_job(engine)
        results = self.search_texts(engine, self.wiki, "低い確信度の本文")
        marks = {row["page"]: row["review"] for row in results}
        self.assertEqual(marks.get(3), {"state": "pending", "awaiting_publish": False})
        self.assertIsNone(marks.get(1))
        self.assertEqual(engine.status(str(self.wiki))["review"]["pending_pages"], 2)

    def test_tables_from_rag_0_5_3_get_the_new_columns(self):
        folder = self.config.workspace(str(self.wiki))
        folder.mkdir(parents=True)
        with closing(sqlite3.connect(folder / "catalog.sqlite")) as db:
            db.execute("""CREATE TABLE documents (doc_id TEXT PRIMARY KEY, generation TEXT NOT NULL, title TEXT NOT NULL,
                pages INTEGER, chunks INTEGER, fingerprint TEXT NOT NULL, ingested_at REAL NOT NULL)""")
            db.commit()
        data = self.config.data_dir
        data.mkdir(parents=True, exist_ok=True)
        with closing(sqlite3.connect(data / "jobs-v2.sqlite")) as db:
            db.execute("""CREATE TABLE ingest_jobs (id TEXT PRIMARY KEY, wiki TEXT NOT NULL, source TEXT NOT NULL,
                source_page TEXT NOT NULL, title TEXT NOT NULL, size INTEGER, mtime_ns INTEGER, config TEXT NOT NULL,
                status TEXT NOT NULL DEFAULT 'queued', phase TEXT NOT NULL DEFAULT '受付', completed INTEGER NOT NULL DEFAULT 0,
                total INTEGER NOT NULL DEFAULT 0, attempts INTEGER NOT NULL DEFAULT 0, owner TEXT, error TEXT, result TEXT,
                created_at REAL, updated_at REAL, publication_started INTEGER NOT NULL DEFAULT 0, request_key TEXT NOT NULL,
                dev TEXT, ino TEXT)""")
            db.commit()
        engine = self.engine()
        jobs, _ = self.ingest_job(engine)
        self.decide(self.wiki, 0, [self.item(self.wiki, 3, "accept")])
        jobs.register_rebuild(self.config, str(self.wiki), self.doc_id, self.ledger_version())
        self.assertEqual(self.run_queued(jobs, engine)[-1]["status"], "completed")



class ReviewRegressionTests(Base):
    """段階 3 の 1 回目のレビューで見つかった反例（docs/agent-runs/2026-11-16-adr-0025-stage3-review/review-1.md）。"""

    def stop_after_embedding(self, engine: Engine):
        def stop(phase, completed, total):
            if phase == "索引の公開" or (phase == "埋め込み" and completed and completed == total):
                raise RuntimeError("公開の前に止まった")
        with self.assertRaisesRegex(RuntimeError, "公開の前に止まった"):
            engine.rebuild_reviewed(str(self.wiki), self.doc_id, progress=stop)

    def test_unpublished_checkpoint_is_not_reused_after_replacing_and_restoring_the_pdf(self):
        """1. 公開の前に止まった確認の版の途中経過が、PDF を差しかえて戻したあとに使われない。"""
        engine = self.engine()
        self.ingest_job(engine)
        original = self.pdf.read_bytes()
        doc_a = self.doc_id
        self.decide(self.wiki, 0, [self.item(self.wiki, 3, "fix", "直した本文 三")])
        self.stop_after_embedding(engine)
        pdf_fixtures.make_ties_pdf(self.pdf, pages=1)  # 同じ場所の PDF を別のものに差しかえる
        engine.ingest_pdf(str(self.wiki), str(self.pdf), "sources/kinds.md")
        self.pdf.write_bytes(original)  # 元に戻す
        again = engine.ingest_pdf(str(self.wiki), str(self.pdf), "sources/kinds.md")
        self.assertEqual(again["sha256"], doc_a)
        folder = self.config.workspace(str(self.wiki))
        rows = engine._table(folder).search().where(f"doc_id = '{doc_a}'").limit(1000).to_list()
        self.assertEqual(len(rows), again["chunks"])  # 埋め込みを飛ばしていない
        self.assertTrue(rows)

    def test_empty_version_survives_a_policy_change(self):
        """2. すべてのページを却下した 0 行の版を、方針が変わった索引に取り込み直しても失敗しない。"""
        from reportlab.pdfgen import canvas
        c = canvas.Canvas(str(self.pdf), invariant=1)
        c.drawString(60, 700, "only page")
        c.showPage()
        c.save()
        self.values["ocr_mode"] = "always"
        engine = self.engine(answers=[("唯一のページ", [line("唯一のページ", 0.3)])])
        jobs, _ = self.ingest_job(engine)
        self.decide(self.wiki, 0, [self.item(self.wiki, 1, "reject")])
        self.run_queued(jobs, engine)
        with patch("rag_config.EXTRACT_REVISION", "extract-v3"):
            again = engine.ingest_pdf(str(self.wiki), str(self.pdf), "sources/kinds.md")
            self.assertEqual(engine.search(str(self.wiki), "唯一のページ", limit=5)["results"], [])  # 表がなくても落ちない
        self.assertEqual((again["status"], again["chunks"], again["index_reset"]), ("indexed", 0, True))
        self.assertIsNone(again["cleanup_error"])
        with closing(sqlite3.connect(self.config.workspace(str(self.wiki)) / "catalog.sqlite")) as db:
            self.assertEqual(db.execute("SELECT review_version FROM documents").fetchone()[0], 1)

    def test_lost_job_registration_is_recovered_from_the_state(self):
        """3. 台帳に書いたあと、作り直しのジョブを登録する前に止まっても、状態から登録し直す。"""
        from rag_worker import reconcile_rebuilds
        engine = self.engine()
        jobs, _ = self.ingest_job(engine)
        rag_review.decide(self.config, str(self.wiki), self.doc_id, 0, [self.item(self.wiki, 3, "accept")])  # 登録しない
        self.assertIsNone(jobs.claim("試験"))
        with patch.dict(os.environ, {"INFO_HIVE_RAG_CONFIG": str(self.root / "config.json")}):
            (self.root / "config.json").write_text(json.dumps(self.values), encoding="utf-8")
            registered = reconcile_rebuilds(jobs)
        self.assertEqual(len(registered), 1)
        self.run_queued(jobs, engine)
        with closing(sqlite3.connect(self.config.workspace(str(self.wiki)) / "catalog.sqlite")) as db:
            self.assertEqual(db.execute("SELECT review_version FROM documents").fetchone()[0], 1)

    def test_unpublished_build_does_not_overwrite_the_published_artifacts(self):
        """4. 公開の前に止まった作り直しが、公開している版の本文と確信度の要約を変えない。"""
        engine = self.engine()
        jobs, job_id = self.ingest_job(engine)
        self.decide(self.wiki, 0, [self.item(self.wiki, 3, "fix", "直した本文 三")])
        published = self.run_queued(jobs, engine)[-1]["result"]
        markdown = Path(published["extracted_markdown"])
        before = markdown.read_text(encoding="utf-8")
        changed = [ANSWERS[0], ("新しい OCR の本文 三", [line("新しい OCR の本文 三", 0.5)]), ANSWERS[2]]
        bumped = {"pypdfium2": "9.9.9", "dpi": 150}
        engine = self.engine(answers=changed)

        def fail(phase, completed, total):
            if phase == "埋め込み":
                raise RuntimeError("埋め込みで止まった")
        with patch("rag_config.render_identity", lambda dpi: bumped), patch("rag_pdf.render_identity", lambda dpi: bumped), \
                patch("rag_config.EXTRACT_REVISION", "extract-v3"), self.assertRaisesRegex(RuntimeError, "埋め込みで止まった"):
            engine.ingest_pdf(str(self.wiki), str(self.pdf), "sources/kinds.md", progress=fail)
        self.assertEqual(markdown.read_text(encoding="utf-8"), before)
        lists = self.report(jobs, self.wiki, job_id)["lists"]
        self.assertEqual(lists["review:fixed"]["ranges"], "3")  # 公開している版では、直した結果がそのまま当たっている
        self.assertEqual(lists["review:stale"]["ranges"], "")

    def test_detail_reads_one_snapshot(self):
        """5. ocr_page_detail の確認の結果と台帳の版は、同じ時点のもの。"""
        engine = self.engine()
        jobs, _ = self.ingest_job(engine)
        self.decide(self.wiki, 0, [self.item(self.wiki, 3, "accept")])
        self.decide(self.wiki, 1, [self.item(self.wiki, 3, "reject")])
        detail = rag_review.page_detail(self.config, str(self.wiki), self.doc_id, 3)
        self.assertEqual((detail["ledger_version"], detail["decision"]["version"], detail["decision"]["action"]), (2, 2, "reject"))
        self.assertEqual([item["version"] for item in detail["history"]], [1, 2])

    def test_old_job_reports_the_published_state(self):
        """6. 前のジョブの page_report も、今公開している版の状態を返す（OCR が変わったら stale）。"""
        engine = self.engine()
        jobs, first = self.ingest_job(engine)
        self.decide(self.wiki, 0, [self.item(self.wiki, 3, "fix", "直した本文 三")])
        self.run_queued(jobs, engine)
        changed = [ANSWERS[0], ("新しい OCR の本文 三", [line("新しい OCR の本文 三", 0.5)]), ANSWERS[2]]
        bumped = {"pypdfium2": "9.9.9", "dpi": 150}
        engine = self.engine(answers=changed)
        with patch("rag_config.render_identity", lambda dpi: bumped), patch("rag_pdf.render_identity", lambda dpi: bumped), \
                patch("rag_config.EXTRACT_REVISION", "extract-v3"):
            engine.ingest_pdf(str(self.wiki), str(self.pdf), "sources/kinds.md")
            lists = Jobs(self.config.data_dir).status(str(self.wiki), first, threshold=0.8)["result"]["page_report"]["lists"]
        self.assertEqual(lists["review:stale"]["ranges"], "3")
        self.assertEqual(lists["review:fixed"]["ranges"], "")

    def test_rerun_keeps_the_full_result(self):
        """7. 作り直しを、もう一度待ちに戻して動かしたあとも、ジョブの結果に本文と page_report が残る。"""
        engine = self.engine()
        jobs, _ = self.ingest_job(engine)
        self.decide(self.wiki, 0, [self.item(self.wiki, 3, "accept")])
        original = engine.rebuild_reviewed

        def rebuild_then_decide(*args, **kwargs):
            result = original(*args, **kwargs)
            engine.rebuild_reviewed = original
            self.decide(self.wiki, 1, [self.item(self.wiki, 4, "fix", "直した本文 四")])
            return result
        engine.rebuild_reviewed = rebuild_then_decide
        done = self.run_queued(jobs, engine)
        result = done[-1]["result"]
        self.assertTrue(Path(result["extracted_markdown"]).is_file())
        self.assertIn("直した本文 四", Path(result["extracted_markdown"]).read_text(encoding="utf-8"))
        self.assertIn("page_report", result)
        self.assertEqual(result["review"]["published_version"], 2)

    def reconcile(self, jobs: Jobs) -> list[dict]:
        from rag_worker import reconcile_rebuilds
        (self.root / "config.json").write_text(json.dumps(self.values), encoding="utf-8")
        with patch.dict(os.environ, {"INFO_HIVE_RAG_CONFIG": str(self.root / "config.json")}):
            return reconcile_rebuilds(jobs)

    def test_cancelled_or_failed_rebuild_is_not_registered_again(self):
        """取り消したか失敗した作り直しは、状態からの登録し直しで復活しない（明示的な再試行で動かす）。"""
        engine = self.engine()
        jobs, _ = self.ingest_job(engine)
        self.decide(self.wiki, 0, [self.item(self.wiki, 3, "accept")])
        job = [item for item in jobs.list(str(self.wiki)) if item["kind"] == "review"][0]
        jobs.cancel(str(self.wiki), job["job_id"])
        self.assertEqual(self.reconcile(jobs), [])
        self.assertIsNone(jobs.claim("試験"))

    def test_rerun_after_catching_up_inside_the_loop_keeps_the_result(self):
        """作り直しの内側の繰り返しで台帳に追いついたあと、もう一度動かしても（何もしない）結果が欠けない。"""
        engine = self.engine()
        jobs, _ = self.ingest_job(engine)
        self.decide(self.wiki, 0, [self.item(self.wiki, 3, "accept")])
        job = jobs.claim("試験")
        decided = []

        def publish():
            jobs.begin_publication(job["id"], "試験")
            if not decided:  # 1 回目の公開の直前に、次の確認を受け付ける（処理中なので rerun の印が付く）
                decided.append(self.decide(self.wiki, 1, [self.item(self.wiki, 4, "fix", "直した本文 四")]))
        result = engine.rebuild_reviewed(str(self.wiki), self.doc_id, before_publish=publish)
        self.assertEqual(result["review"]["published_version"], 2)  # 内側の繰り返しで、版 2 まで公開した
        jobs.finish(job["id"], "試験", result=result)
        self.assertEqual(jobs.status(str(self.wiki), job["id"])["status"], "queued")  # rerun で待ちに戻る
        final = self.run_queued(jobs, engine)[-1]
        self.assertEqual(final["status"], "completed")
        self.assertIn("直した本文 四", Path(final["result"]["extracted_markdown"]).read_text(encoding="utf-8"))
        self.assertIn("page_report", final["result"])

    def test_empty_published_summary_is_used(self):
        """公開している版に OCR したページがなくなっても、前のジョブの記録の確認の状態を返さない。"""
        from reportlab.pdfgen import canvas
        c = canvas.Canvas(str(self.pdf), invariant=1)
        c.drawString(60, 700, "a page with a text layer that is long enough to be judged as text")
        c.showPage()
        c.save()
        self.values["ocr_mode"] = "always"
        engine = self.engine(answers=[("OCR の本文", [line("OCR の本文", 0.3)])])
        jobs, first = self.ingest_job(engine)
        self.decide(self.wiki, 0, [self.item(self.wiki, 1, "reject")])
        self.run_queued(jobs, engine)
        self.values["ocr_mode"] = "auto"
        self.engine().ingest_pdf(str(self.wiki), str(self.pdf), "sources/kinds.md")
        lists = Jobs(self.config.data_dir).status(str(self.wiki), first, threshold=0.8)["result"]["page_report"]["lists"]
        self.assertEqual(lists["review:rejected"]["count"], 0)
        self.assertEqual(lists["ocr_low_confidence"]["count"], 0)

    def test_rebuild_uses_the_path_the_user_gave(self):
        """作り直しは、索引の台帳に残した、利用者が渡したままの PDF のパスで取り込み直す。"""
        engine = self.engine()
        jobs, _ = self.ingest_job(engine)
        self.decide(self.wiki, 0, [self.item(self.wiki, 3, "accept")])
        seen = []
        original = engine.ingest_pdf

        def record(wiki, source, *args, **kwargs):
            seen.append(source)
            return original(wiki, source, *args, **kwargs)
        engine.ingest_pdf = record
        self.run_queued(jobs, engine)
        self.assertEqual(seen, [str(self.pdf)])

    def test_later_decision_is_registered_after_the_covering_job_was_cancelled(self):
        """登録し直したジョブ（版 1）を取り消し、版 2 の確認の登録が失われても、版 2 は登録し直す。"""
        engine = self.engine()
        jobs, _ = self.ingest_job(engine)
        rag_review.decide(self.config, str(self.wiki), self.doc_id, 0, [self.item(self.wiki, 3, "accept")])
        first = self.reconcile(jobs)
        self.assertEqual(len(first), 1)
        jobs.cancel(str(self.wiki), first[0]["job_id"])
        rag_review.decide(self.config, str(self.wiki), self.doc_id, 1, [self.item(self.wiki, 4, "accept")])  # 登録しない
        second = self.reconcile(jobs)
        self.assertEqual(len(second), 1)
        self.assertNotEqual(second[0]["job_id"], first[0]["job_id"])
        self.run_queued(jobs, engine)
        with closing(sqlite3.connect(self.config.workspace(str(self.wiki)) / "catalog.sqlite")) as db:
            self.assertEqual(db.execute("SELECT review_version FROM documents").fetchone()[0], 2)

    def test_failed_rebuild_is_not_registered_again(self):
        """作り直しが失敗したら、状態からの登録し直しで復活しない（明示的な再試行で動かす）。"""
        engine = self.engine()
        jobs, _ = self.ingest_job(engine)
        self.decide(self.wiki, 0, [self.item(self.wiki, 3, "accept")])
        moved = self.pdf.with_name("moved.pdf")
        self.pdf.rename(moved)  # PDF を移したので、作り直しは失敗する
        done = self.run_queued(jobs, engine)
        self.assertEqual(done[-1]["status"], "failed")
        self.assertEqual(self.reconcile(jobs), [])
        self.assertIsNone(jobs.claim("試験"))

    def test_rebuild_uses_the_given_path_even_when_it_resolves_differently(self):
        """利用者が渡したパスと、解決したパスが違うとき（ネットワークドライブなど）も、渡したパスで作り直す。"""
        engine = self.engine()
        given = str(self.pdf.parent / ".." / "refs" / self.pdf.name)
        jobs = Jobs(self.config.data_dir)
        jobs.register(self.config, str(self.wiki), given, "sources/kinds.md")
        process_job(jobs, "試験", jobs.claim("試験"), engine)
        self.decide(self.wiki, 0, [self.item(self.wiki, 3, "accept")])
        seen = []
        original = engine.ingest_pdf

        def record(wiki, source, *args, **kwargs):
            seen.append(source)
            return original(wiki, source, *args, **kwargs)
        engine.ingest_pdf = record
        self.run_queued(jobs, engine)
        self.assertEqual(seen, [given])

    def test_retry_does_not_make_a_second_rebuild_job(self):
        engine = self.engine()
        jobs, _ = self.ingest_job(engine)
        self.decide(self.wiki, 0, [self.item(self.wiki, 3, "accept")])
        first = jobs.list(str(self.wiki))[0]
        jobs.cancel(str(self.wiki), first["job_id"])
        self.decide(self.wiki, 1, [self.item(self.wiki, 4, "accept")])
        jobs.retry(str(self.wiki), first["job_id"])
        active = [job for job in jobs.list(str(self.wiki)) if job["kind"] == "review" and job["status"] in ("queued", "running", "paused")]
        self.assertEqual(len(active), 1)

    def test_old_confidence_revision_is_unknown(self):
        engine = self.engine()
        jobs, job_id = self.ingest_job(engine)
        with patch("rag_config.OCR_CONFIDENCE_REVISION", "confidence-v2"):
            lists = self.report(jobs, self.wiki, job_id)["lists"]
        self.assertEqual(lists["ocr_low_confidence"]["ranges"], "")
        self.assertEqual(lists["ocr_unknown_confidence"]["ranges"], "2-4")

if __name__ == "__main__":
    unittest.main()
