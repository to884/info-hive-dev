"""rag の OCR の保存、page_report、古い rag との組み合わせの契約の試験（ADR-0025 の「wiki と rag のそろい方」の 3、4、5）。

rag の依存（lancedb、sudachipy など）が要るので、rag の CI（.github/workflows/rag.yml）で流す。

    uv run --python 3.12 <rag.yml の DEPS> python -X utf8 -m unittest tests/contract/test_rag_contract.py -v

OCR は、呼んだ回数を数えるスタブで置きかえる（ADR の試験 6 が認めている）。埋め込みも偽物を使う。
試験 5 の古い rag の応答は、info-hive-rag の v0.5.3 のタグの抽出をそのまま動かして作る。タグがないときは飛ばす。
"""

from __future__ import annotations

import functools
import hashlib
import json
import os
import shutil
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[2]
HERE = Path(__file__).resolve().parent
WIKI_SCRIPTS = ROOT / "info-hive-wiki" / "skills" / "info-hive" / "scripts"
RAG_SCRIPTS = ROOT / "info-hive-rag" / "scripts"
for folder in (HERE, RAG_SCRIPTS):
    sys.path.insert(0, str(folder))

import pdf_fixtures  # noqa: E402
import rag_config  # noqa: E402
import rag_pdf  # noqa: E402
from rag_config import MODELS, Config, OCR_REVISION  # noqa: E402
from rag_index import Engine  # noqa: E402
from rag_jobs import Jobs  # noqa: E402

ENV = {**os.environ, "PYTHONUTF8": "1", "PYTHONIOENCODING": "utf-8"}


class FakeEmbedder:
    def __init__(self, dimension):
        self.dimension = dimension

    def encode(self, texts, **_):
        import numpy as np
        return np.tile(np.asarray([1.] + [0.] * (self.dimension - 1), dtype=np.float32), (len(texts), 1))


class StubOcr:
    """OCR の代わり。呼ばれた回数を数え、決めた本文を返す。empty_calls の回目（1 から）は空の本文を返す。"""

    def __init__(self, text="OCR の本文", empty_calls=()):
        self.calls = 0
        self.text = text
        self.empty_calls = set(empty_calls)

    def recognize(self, image):
        self.calls += 1
        text = "" if self.calls in self.empty_calls else f"{self.text} {self.calls}"
        return {"ok": True, "text": text, "line_count": 0 if not text else 1}


class Base(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory(dir=os.environ.get("RAG_TEST_RUN_ROOT"), ignore_cleanup_errors=True)
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name).resolve()
        self.wiki = self.root / "wiki"
        (self.wiki / "sources").mkdir(parents=True)
        (self.wiki / "SCHEMA.md").write_text("# 試験\n", encoding="utf-8")
        self.pdf = self.root / "refs" / "kinds.pdf"
        self.pdf.parent.mkdir()
        pdf_fixtures.make_kinds_pdf(self.pdf)
        self.values = {"data_dir": str(self.root / "data"), "embedding_model": "cl-nagoya/ruri-v3-30m",
                       "ocr_mode": "auto", "ocr_dpi": 150, "batch_size": 8}

    def engine(self, ocr: StubOcr, **changes) -> Engine:
        config = Config({**self.values, **changes})
        extractor = functools.partial(rag_pdf.extract_pages, ocr_client=ocr)
        return Engine(config, embedder=FakeEmbedder(MODELS[config.model]), extractor=extractor)

    def ingest(self, engine: Engine, wiki: Path | None = None) -> dict:
        return engine.ingest_pdf(str(wiki or self.wiki), str(self.pdf), "sources/kinds.md")

    @property
    def doc_id(self) -> str:
        return hashlib.sha256(self.pdf.read_bytes()).hexdigest()

    def markdown_pages(self, result: dict) -> dict[int, str]:
        text = Path(result["extracted_markdown"]).read_text(encoding="utf-8")
        pages = {}
        for block in text.split("## p. ")[1:]:
            number, _, rest = block.partition("\n\n")
            pages[int(number)] = rest.rstrip("\n")
        return pages


class OcrStoreTests(Base):
    """試験 3: rag の OCR の保存。"""

    OCR_PAGES = [2, 3, 4]  # kinds.pdf の vertical、garbled、scan

    def test_changing_only_the_text_layer_reuses_the_ocr(self):
        ocr = StubOcr()
        result = self.ingest(self.engine(ocr))
        self.assertEqual(ocr.calls, 3)
        first = self.markdown_pages(result)
        with patch("rag_config.EXTRACT_REVISION", "extract-v3"):
            again = self.ingest(self.engine(ocr))
            self.assertTrue(again["index_reset"])
            self.assertIn("extract-v3", again["extracted_markdown"])
        self.assertEqual(ocr.calls, 3)  # OCR を呼ばず、保存した結果を使った
        self.assertEqual({n: first[n] for n in self.OCR_PAGES}, {n: self.markdown_pages(again)[n] for n in self.OCR_PAGES})

    def test_changing_the_render_runs_the_ocr_again(self):
        ocr = StubOcr()
        self.ingest(self.engine(ocr))
        self.ingest(self.engine(ocr, ocr_dpi=200))  # 描画の dpi が変わる
        self.assertEqual(ocr.calls, 6)
        with patch("rag_config.render_identity", lambda dpi: {"pypdfium2": "9.9.9", "dpi": dpi}), \
                patch("rag_pdf.render_identity", lambda dpi: {"pypdfium2": "9.9.9", "dpi": dpi}):
            with patch("rag_config.EXTRACT_REVISION", "extract-v3"):  # 抽出の結果も作り直させる
                self.ingest(self.engine(ocr))  # pypdfium2 の版が変わった
        self.assertEqual(ocr.calls, 9)

    def legacy_cache(self, name: str, texts: dict[int, str | None]) -> Path:
        """rag 0.5.3 の形の抽出の結果を置く。texts の値が None のページは、OCR していないページにする。"""
        folder = Config(self.values).extraction_root / self.doc_id / name
        folder.mkdir(parents=True)
        for number, text in texts.items():
            entry = {"page": number, "text": text if text is not None else f"文字の層 {number}", "quality": {"kind": "text"},
                     "ocr": text is not None, "ocr_empty": text == ""}
            (folder / f"page-{number:06d}.json").write_text(json.dumps(entry, ensure_ascii=False), encoding="utf-8")
        return folder

    def test_legacy_ocr_is_adopted_only_when_the_conditions_match(self):
        same = f"auto-150-{OCR_REVISION[:12]}-extract-v1"
        self.legacy_cache(same, {1: None, 2: "移した 2", 3: "移した 3", 4: ""})
        self.legacy_cache(f"always-200-{OCR_REVISION[:12]}-extract-v1", {2: "dpi の違う 2"})
        self.legacy_cache(f"auto-150-{'0' * 12}-extract-v1", {3: "版の違う 3"})
        ocr = StubOcr()
        result = self.ingest(self.engine(ocr))
        self.assertEqual(ocr.calls, 0)  # 3 ページとも、移した結果を使った
        pages = self.markdown_pages(result)
        self.assertEqual((pages[2], pages[3], pages[4]), ("移した 2", "移した 3", ""))
        store = Config(self.values).ocr_dir(self.doc_id)
        for number in self.OCR_PAGES:
            entry = json.loads((store / f"page-{number:06d}.json").read_text(encoding="utf-8"))
            self.assertEqual(entry["render"], rag_pdf.UNKNOWN_RENDER)  # 描画の識別は「不明」と記録する
            self.assertEqual(entry["adopted_render"], rag_config.render_identity(150))
            self.assertEqual(entry["adopted_from"], same)
            self.assertIsNone(entry["confidence"])  # 確信度は不明（段階 3 で足す）
        self.assertFalse((store / "page-000001.json").exists())  # OCR していないページは移さない

    def test_adopted_ocr_is_reused_while_the_render_is_the_same_and_never_adopted_twice(self):
        self.legacy_cache(f"auto-150-{OCR_REVISION[:12]}-extract-v1", {2: "移した 2", 3: "移した 3", 4: "移した 4"})
        ocr = StubOcr()
        self.ingest(self.engine(ocr))
        with patch("rag_config.EXTRACT_REVISION", "extract-v3"):
            again = self.ingest(self.engine(ocr))
        self.assertEqual(ocr.calls, 0)  # 描画の識別が移したときと同じあいだは、移した結果を使い回す
        self.assertEqual(self.markdown_pages(again)[2], "移した 2")
        bumped = {"pypdfium2": "9.9.9", "dpi": 150}
        with patch("rag_config.render_identity", lambda dpi: bumped), patch("rag_pdf.render_identity", lambda dpi: bumped), \
                patch("rag_config.EXTRACT_REVISION", "extract-v4"):
            third = self.ingest(self.engine(ocr))
        self.assertEqual(ocr.calls, 3)  # 描画の識別が変わったあとは、移した結果も使わず OCR をやり直す
        self.assertTrue(self.markdown_pages(third)[2].startswith("OCR の本文"))  # もう一度は移さない
        marker = json.loads((Config(self.values).extraction_root / self.doc_id / "ocr" / "adopted.json").read_text(encoding="utf-8"))
        self.assertEqual(list(marker["sources"]), [f"auto-150-{OCR_REVISION[:12]}-extract-v1"])

    def interrupt_adoption(self, stop_at: int):
        """rag_pdf の write_json の stop_at 回目（1 から）で止める。"""
        original, calls = rag_pdf.write_json, []

        def stop(path, value):
            calls.append(path)
            if len(calls) == stop_at:
                raise RuntimeError("移す途中で止まった")
            return original(path, value)
        with patch("rag_pdf.write_json", stop), self.assertRaisesRegex(RuntimeError, "移す途中で止まった"):
            self.ingest(self.engine(StubOcr()))

    def one_source_interrupted(self):
        """元が 1 つ。書く順は、印（文書の描画の識別）、印（元の copying）、2 ページ目、3 ページ目。3 ページ目の前で止める。"""
        self.legacy_cache(f"auto-150-{OCR_REVISION[:12]}-extract-v1", {2: "移した 2", 3: "移した 3", 4: "移した 4"})
        self.interrupt_adoption(stop_at=4)

    def test_interrupted_adoption_resumes_with_the_same_render(self):
        self.one_source_interrupted()
        ocr = StubOcr()
        result = self.ingest(self.engine(ocr))
        self.assertEqual(ocr.calls, 0)  # 描画の識別が同じなので、続きを写した
        self.assertEqual([self.markdown_pages(result)[n] for n in (2, 3, 4)], ["移した 2", "移した 3", "移した 4"])
        marker = json.loads((Config(self.values).extraction_root / self.doc_id / "ocr" / "adopted.json").read_text(encoding="utf-8"))
        state = marker["sources"][f"auto-150-{OCR_REVISION[:12]}-extract-v1"]
        self.assertEqual((state["state"], state["pages"]), ("done", ["2-4"]))  # 止まる前に写した 2 ページ目も記録する

    def test_interrupted_adoption_is_not_resumed_after_the_render_changed(self):
        self.one_source_interrupted()
        bumped = {"pypdfium2": "9.9.9", "dpi": 150}
        ocr = StubOcr()
        with patch("rag_config.render_identity", lambda dpi: bumped), patch("rag_pdf.render_identity", lambda dpi: bumped):
            result = self.ingest(self.engine(ocr))
        self.assertEqual(ocr.calls, 3)  # 移し始めたときと描画の識別が違うので、写さずに OCR した
        self.assertTrue(all(self.markdown_pages(result)[n].startswith("OCR の本文") for n in (2, 3, 4)))
        marker = json.loads((Config(self.values).extraction_root / self.doc_id / "ocr" / "adopted.json").read_text(encoding="utf-8"))
        self.assertEqual(marker["sources"][f"auto-150-{OCR_REVISION[:12]}-extract-v1"]["state"], "copying")
        self.assertEqual(marker["render"], rag_config.render_identity(150))  # 移す描画の識別は、文書ごとに 1 つ

    def test_adoption_stopped_between_two_sources_is_not_continued_after_the_render_changed(self):
        """always の元を移し終え、auto の元を記録する前に止まったあと、描画の識別が変わっても、auto の元から移さない。"""
        self.legacy_cache(f"always-150-{OCR_REVISION[:12]}-extract-v1", {2: "always の 2"})
        self.legacy_cache(f"auto-150-{OCR_REVISION[:12]}-extract-v1", {2: "auto の 2", 3: "auto の 3"})
        # 書く順は、印（文書の描画の識別）、印（always の copying）、2 ページ目、印（always の done）、印（auto の copying）
        self.interrupt_adoption(stop_at=5)
        bumped = {"pypdfium2": "9.9.9", "dpi": 150}
        ocr = StubOcr()
        with patch("rag_config.render_identity", lambda dpi: bumped), patch("rag_pdf.render_identity", lambda dpi: bumped):
            result = self.ingest(self.engine(ocr))
        self.assertEqual(ocr.calls, 3)
        self.assertTrue(all(self.markdown_pages(result)[n].startswith("OCR の本文") for n in (2, 3, 4)))


class PageReportTests(Base):
    """試験 4: rag の page_report。"""

    def wiki_json(self, path: Path, *args: str) -> dict:
        result = subprocess.run([sys.executable, "-X", "utf8", str(WIKI_SCRIPTS / "wiki_pdf.py"), str(path), "--json", *args],
                                capture_output=True, encoding="utf-8", env=ENV, timeout=600)
        self.assertEqual(result.returncode, 0, result.stderr)
        return json.loads(result.stdout)

    def run_job(self, engine: Engine) -> dict:
        """ジョブを登録し、ワーカーと同じ処理で 1 件動かして、job_status と同じ結果を返す。"""
        from rag_worker import process_job
        jobs = Jobs(engine.config.data_dir)
        registered = jobs.register(engine.config, str(self.wiki), str(self.pdf), "sources/kinds.md")
        job = jobs.claim("試験")
        self.assertEqual(job["id"], registered["job_id"])
        process_job(jobs, "試験", job, engine)
        return jobs

    def test_lists_match_wiki_and_the_ocr_stub(self):
        ocr = StubOcr(empty_calls={3})  # 3 回目（4 ページ目の scan）の OCR の結果が空
        jobs = self.run_job(self.engine(ocr))
        job = jobs.list(str(self.wiki))[0]
        self.assertEqual(job["status"], "completed", job["error"])
        report = job["result"]["page_report"]
        wiki = self.wiki_json(self.pdf)
        for kind in ("text", "vertical", "garbled", "scan", "blank"):
            self.assertEqual(report["lists"][f"kind:{kind}"], wiki["lists"][f"kind:{kind}"], kind)
        self.assertEqual(report["lists"]["needs_check"], wiki["lists"]["needs_check"])
        self.assertEqual(report["lists"]["empty_text"], wiki["lists"]["empty_text"])
        self.assertEqual(report["lists"]["ocr"], {"count": 3, "ranges": "2-4", "next": None})
        self.assertEqual(report["lists"]["ocr_empty"], {"count": 1, "ranges": "4", "next": None})
        self.assertEqual((report["pages"], report["processed"], report["complete"]), (7, 7, True))
        self.assertEqual(report["extraction"], {**wiki["extraction"]})
        self.assertEqual(job["result"]["extraction"], wiki["extraction"])

    def test_more_than_200_ranges_can_be_followed(self):
        from reportlab.pdfgen import canvas
        c = canvas.Canvas(str(self.pdf), invariant=1)
        for number in range(1, 404):
            if number % 2:
                c.setFont("Helvetica", 11)
                c.drawString(60, 700, f"page {number} has words in it for the text layer")
            c.showPage()
        c.save()
        engine = self.engine(StubOcr())
        jobs = self.run_job(engine)
        identity = jobs.list(str(self.wiki))[0]["job_id"]
        ranges, start = [], 0
        while start is not None:
            listed = jobs.status(str(self.wiki), identity, start)["result"]["page_report"]["lists"]["kind:text"]
            self.assertEqual(listed["count"], 202)
            ranges.extend(listed["ranges"].split(","))
            start = listed["next"]
        self.assertEqual(ranges, [str(number) for number in range(1, 404, 2)])
        wiki = self.wiki_json(self.pdf)
        self.assertEqual(wiki["lists"]["kind:text"]["next"], 200)
        rest = self.wiki_json(self.pdf, "--list-from", "200")["lists"]["kind:text"]["ranges"].split(",")
        self.assertEqual(wiki["lists"]["kind:text"]["ranges"].split(",") + rest, ranges)
        # status の一覧も、200 個で切って返す
        self.assertEqual(len(jobs.list(str(self.wiki))[0]["result"]["page_report"]["lists"]["kind:text"]["ranges"].split(",")), 200)

    def test_failed_job_reports_the_pages_so_far(self):
        jobs = self.run_job(self.engine(StubOcr(), ocr_mode="off"))  # 2 ページ目（vertical）に OCR が要る
        job = jobs.list(str(self.wiki))[0]
        self.assertEqual(job["status"], "failed")
        self.assertIn("2 ページ目に OCR が必要です", job["error"])
        report = job["result"]["page_report"]
        self.assertEqual((report["judged"], report["processed"], report["complete"]), (2, 1, False))
        self.assertEqual(report["lists"]["pending"]["ranges"], "2")
        self.assertEqual(report["lists"]["kind:vertical"]["ranges"], "2")
        self.assertEqual(report["ocr"]["mode"], "off")

    def test_unchanged_document_reports_the_same(self):
        engine = self.engine(StubOcr())
        first = self.ingest(engine)
        second = self.ingest(engine)
        self.assertEqual(second["status"], "unchanged")
        self.assertEqual(first["page_report"], second["page_report"])


class OldRagTests(Base):
    """試験 5: page_report を返さない古い rag（v0.5.3）の応答で、代わりの手順が働く。

    手順は info-hive-wiki の ingest-workflow.md の「rag で取り込んだとき」である。ocr_mode が always で、
    判定が text のページの OCR の結果が空になった応答を使う。
    """

    def old_rag_markdown(self) -> Path:
        """v0.5.3 の rag の抽出と document.md の書き方を、そのまま動かして作る。"""
        folder = self.root / "rag-0.5.3"
        folder.mkdir()
        for name in ("rag_pdf.py", "rag_config.py"):
            shown = subprocess.run(["git", "-C", str(ROOT / "info-hive-rag"), "show", f"v0.5.3:scripts/{name}"],
                                   capture_output=True)
            if shown.returncode:
                self.skipTest("info-hive-rag の v0.5.3 のタグがない（git fetch --tags）")
            (folder / name).write_bytes(shown.stdout)
        # OCR のスタブ。always のとき、最初に OCR する 1 ページ目（判定は text）の結果を空にする
        (folder / "rag_ocr_client.py").write_text(
            "class OcrClient:\n"
            "    calls = 0\n"
            "    def __init__(self, config): pass\n"
            "    def __enter__(self): return self\n"
            "    def __exit__(self, *_): pass\n"
            "    def recognize(self, image):\n"
            "        OcrClient.calls += 1\n"
            "        return {'text': '' if OcrClient.calls == 1 else f'OCR {OcrClient.calls}'}\n", encoding="utf-8")
        # rag 0.5.3 の rag_index.Engine._write_markdown と同じ書き方
        (folder / "run.py").write_text(
            "import sys\nfrom pathlib import Path\nfrom rag_config import Config\nfrom rag_pdf import extract_pages\n"
            "data = Path(sys.argv[1]).read_bytes()\n"
            "config = Config({'data_dir': sys.argv[3], 'ocr_mode': 'always'})\n"
            "pages = extract_pages(data, config, Path(sys.argv[3]) / 'cache')\n"
            "Path(sys.argv[2]).write_text('\\n\\n'.join(f\"## p. {page['page']}\\n\\n{page['text']}\" for page in pages), encoding='utf-8')\n",
            encoding="utf-8")
        markdown = folder / "document.md"
        done = subprocess.run([sys.executable, "-X", "utf8", str(folder / "run.py"), str(self.pdf), str(markdown),
                               str(folder / "data")], capture_output=True, encoding="utf-8", env=ENV, cwd=folder, timeout=600)
        self.assertEqual(done.returncode, 0, done.stderr)
        return markdown

    def test_fallback_finds_judgements_and_empty_rag_pages(self):
        markdown = self.old_rag_markdown()
        old_result = {"sha256": self.doc_id, "extracted_markdown": str(markdown)}  # page_report はない
        self.assertNotIn("page_report", old_result)
        # 手順: 同じ PDF に wiki_pdf.py --json を動かし、SHA-256 を照らす
        result = subprocess.run([sys.executable, "-X", "utf8", str(WIKI_SCRIPTS / "wiki_pdf.py"), str(self.pdf), "--json"],
                                capture_output=True, encoding="utf-8", env=ENV, timeout=600)
        self.assertEqual(result.returncode, 0, result.stderr)
        summary = json.loads(result.stdout)
        self.assertEqual(summary["sha256"], old_result["sha256"])
        # 判定と確かめるべきページが分かる
        self.assertEqual(summary["lists"]["kind:garbled"]["ranges"], "3")
        self.assertEqual(summary["lists"]["needs_check"]["ranges"], "4,7")
        # rag の本文が空のページを、判定によらずすべてのページで探し、文字の層が空のページを除く
        pages = self.markdown_pages(old_result)
        empty_in_rag = {number for number, text in pages.items() if not text.strip()}
        empty_layer = {int(n) for n in summary["lists"]["empty_text"]["ranges"].split(",") if n}
        self.assertEqual(empty_in_rag - empty_layer, {1})  # 判定が text の 1 ページ目の OCR の結果が空だった
        self.assertEqual(summary["lists"]["kind:text"]["ranges"].split(",")[0], "1")


if __name__ == "__main__":
    unittest.main()
