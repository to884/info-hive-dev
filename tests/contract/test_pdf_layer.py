"""wiki と rag の PDF の文字の層の契約の試験（ADR-0025 の「wiki と rag のそろい方」の 1、2、6、7）。

    uv run --python 3.12 --with pdfminer.six==20260107 --with pypdfium2==5.15.2 --with reportlab==4.4.4 \
        --with pillow==13.0.0 --with pypdf==6.1.3 python -X utf8 -m unittest tests/contract/test_pdf_layer.py -v

公開の PDF（試験 6）は tests/contract/corpus/ に置く（fetch_corpus.py）。ないときは、公開の PDF を使う部分を飛ばす。
試験 3〜5 と 8（OCR の保存、page_report、古い rag、OCR の確信度と確認）は、rag の実装の段階 2、3 で足す。
"""

from __future__ import annotations

import builtins
import hashlib
import io
import json
import os
import subprocess
import sys
import tempfile
import threading
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
HERE = Path(__file__).resolve().parent
WIKI_SCRIPTS = ROOT / "info-hive-wiki" / "skills" / "info-hive" / "scripts"
RAG_SCRIPTS = ROOT / "info-hive-rag" / "scripts"
CORPUS = HERE / "corpus"
for folder in (HERE, WIKI_SCRIPTS, RAG_SCRIPTS):
    sys.path.insert(0, str(folder))

import pdf_fixtures  # noqa: E402
import rag_pdf_layer  # noqa: E402
import wiki_pdf_layer  # noqa: E402

ENV = {**os.environ, "PYTHONUTF8": "1", "PYTHONIOENCODING": "utf-8"}


def corpus_pdfs() -> list[Path]:
    return sorted(CORPUS.glob("*.pdf")) if CORPUS.is_dir() else []


class Fixtures(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.temp = tempfile.TemporaryDirectory(ignore_cleanup_errors=True)
        folder = Path(cls.temp.name)
        cls.kinds = folder / "kinds.pdf"
        cls.ties = folder / "ties.pdf"
        pdf_fixtures.make_kinds_pdf(cls.kinds)
        pdf_fixtures.make_ties_pdf(cls.ties)

    @classmethod
    def tearDownClass(cls):
        cls.temp.cleanup()

    def all_pdfs(self) -> list[Path]:
        return [self.kinds, self.ties, *corpus_pdfs()]


class SameModuleTests(unittest.TestCase):
    def test_wiki_and_rag_hold_the_same_bytes(self):
        """wiki と rag は、同じ中身のファイルを持つ（片方だけを直すと、ここで止まる）。"""
        wiki = (WIKI_SCRIPTS / "wiki_pdf_layer.py").read_bytes()
        rag = (RAG_SCRIPTS / "rag_pdf_layer.py").read_bytes()
        self.assertEqual(hashlib.sha256(wiki).hexdigest(), hashlib.sha256(rag).hexdigest())

    def test_rag_judges_pages_with_the_shared_function(self):
        import rag_pdf
        self.assertIs(rag_pdf.inspect_page, rag_pdf_layer.inspect_page)

    def test_extraction_identity(self):
        identity = wiki_pdf_layer.extraction_identity()
        self.assertEqual(identity, rag_pdf_layer.extraction_identity())
        self.assertEqual(identity["laparams"], {"detect_vertical": True})
        self.assertEqual(identity["order_revision"], "stable-order-v1")


class AgreementTests(Fixtures):
    """試験 1: 同じ PDF を wiki と rag の関数に通し、すべてのページで結果が同じ。"""

    def test_every_page_agrees(self):
        for path in self.all_pdfs():
            with self.subTest(pdf=path.name):
                data = path.read_bytes()
                wiki = list(wiki_pdf_layer.analyze_pages(data))
                rag = list(rag_pdf_layer.analyze_pages(data))
                self.assertEqual(len(wiki), wiki_pdf_layer.pdfium_page_count(data))
                for a, b in zip(wiki, rag, strict=True):
                    for key in ("page", "kind", "quality", "text", "text_sha256", "garble", "needs_check"):
                        self.assertEqual(a[key], b[key], f"{path.name} の {a['page']} ページの {key}")

    def test_synthetic_pages_have_the_intended_judgements(self):
        pages = list(wiki_pdf_layer.analyze_pages(self.kinds.read_bytes()))
        self.assertEqual([p["kind"] for p in pages], pdf_fixtures.KINDS_PDF + ["text"])
        self.assertEqual([p["page"] for p in pages if p["needs_check"]], pdf_fixtures.CHECK_PAGES)
        self.assertGreater(pages[6]["garble"]["cid"], 0)

    def test_public_cid_page_needs_check(self):
        bert = CORPUS / "bert.pdf"
        if not bert.exists():
            self.skipTest("公開の PDF がない（tests/contract/fetch_corpus.py）")
        pages = list(wiki_pdf_layer.analyze_pages(bert.read_bytes(), start=6, stop=6))
        self.assertTrue(pages[0]["needs_check"])
        self.assertGreater(pages[0]["garble"]["cid"], 0)

    def test_partial_range_matches_the_whole(self):
        data = self.kinds.read_bytes()
        whole = list(wiki_pdf_layer.analyze_pages(data))
        part = list(wiki_pdf_layer.analyze_pages(data, start=3, stop=5))
        self.assertEqual([p["page"] for p in part], [3, 4, 5])
        self.assertEqual(part, whole[2:5])

    def test_page_list_shape(self):
        numbers = list(range(1, 402, 2)) + [403, 404, 405]
        first = wiki_pdf_layer.page_list(numbers)
        self.assertEqual(first["count"], len(numbers))
        self.assertEqual(len(first["ranges"].split(",")), 200)
        self.assertEqual(first["next"], 200)
        rest = wiki_pdf_layer.page_list(numbers, first["next"])
        self.assertIsNone(rest["next"])
        self.assertEqual(first["ranges"].split(",") + rest["ranges"].split(","), wiki_pdf_layer.page_ranges(numbers))
        self.assertEqual(wiki_pdf_layer.page_ranges([1, 2, 3, 5, 901]), ["1-3", "5", "901"])
        self.assertEqual(wiki_pdf_layer.page_list([]), {"count": 0, "ranges": "", "next": None})


class WikiOutputTests(Fixtures):
    """試験 2: wiki の出力そのもの。"""

    def run_cli(self, *args: str) -> subprocess.CompletedProcess:
        return subprocess.run([sys.executable, "-X", "utf8", str(WIKI_SCRIPTS / "wiki_pdf.py"), *args],
                              capture_output=True, encoding="utf-8", env=ENV, timeout=600)

    def full(self, path: Path) -> str:
        result = self.run_cli(str(path), "--max-chars", "100000000")
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertNotIn("--from", result.stderr)
        return result.stdout

    def read_in_parts(self, path: Path, max_chars: int) -> tuple[str, list[str]]:
        parts, tokens = [], []
        args = [str(path), "--max-chars", str(max_chars)]
        while True:
            result = self.run_cli(*args)
            self.assertEqual(result.returncode, 0, result.stderr)
            parts.append(result.stdout)
            if "--from " not in result.stderr:
                return "".join(parts), tokens
            token = result.stderr.split("--from ", 1)[1].split()[0]
            tokens.append(token)
            args = [str(path), "--max-chars", str(max_chars), "--from", token]

    def test_pages_by_judgement(self):
        text = self.full(self.kinds)
        pages = {}
        for block in text.split("## p. ")[1:]:
            number, _, rest = block.partition("\n\n")
            pages[int(number)] = rest.rstrip("\n")
        import wiki_pdf
        # vertical のページの本文の前に、1 行の注意が付く
        self.assertTrue(pages[2].startswith(wiki_pdf.NOTES["vertical"] + "\n"))
        self.assertIn("vertical column 0", pages[2])
        # garbled と scan のページは、本文を出さず、1 行の説明だけを出す
        self.assertEqual(pages[3], wiki_pdf.NOTES["garbled"])
        self.assertNotIn("\ue041", text)
        self.assertEqual(pages[4], wiki_pdf.NOTES["scan"])
        # blank のページは見出しだけ
        self.assertEqual(pages[5], "")
        # text のページは pdfminer の本文そのもの
        layer_pages = list(wiki_pdf_layer.analyze_pages(self.kinds.read_bytes()))
        self.assertEqual(pages[1], layer_pages[0]["text"])
        self.assertEqual(pages[7], layer_pages[6]["text"])
        self.assertTrue(text.startswith("## p. 1\n\n"))

    def read_in_parts_directly(self, path: Path, max_chars: int) -> tuple[str, list[str]]:
        """CLI と同じ render を同じプロセスで呼ぶ（小さな上限でも速く確かめる）。"""
        import wiki_pdf
        data = path.read_bytes()
        digest = hashlib.sha256(data).hexdigest()
        parts, tokens, page, offset = [], [], 1, 0
        while True:
            text, following = wiki_pdf.render(wiki_pdf_layer, data, digest, max_chars, page, offset)
            parts.append(text)
            if following is None:
                return "".join(parts), tokens
            tokens.append(following)
            page, offset = wiki_pdf.parse_token(following, digest)

    def test_parts_join_to_the_whole(self):
        for path in (self.kinds, self.ties):
            whole = self.full(path)
            for max_chars in (1, 9, 40, 137, 600, 2500):
                if max_chars == 1 and path == self.kinds:
                    continue  # 6,000 回あまり呼ぶことになるので、短い ties.pdf だけで確かめる
                with self.subTest(pdf=path.name, max_chars=max_chars):
                    joined, tokens = self.read_in_parts_directly(path, max_chars)
                    self.assertEqual(joined, whole)
                    if max_chars < len(whole):
                        self.assertTrue(tokens)
                    self.assertTrue(all(len(t) for t in tokens))
        # CLI を通しても同じ（続きの位置は標準エラーから読む）
        joined, tokens = self.read_in_parts(self.kinds, 600)
        self.assertEqual(joined, self.full(self.kinds))
        # ページの途中で分けた場合と、ページの境目で分けた場合の両方を含む
        offsets = [int(t.rsplit(":", 1)[1]) for t in tokens]
        self.assertTrue(any(o > 0 for o in offsets))
        _, tokens = self.read_in_parts_directly(self.kinds, 137)
        self.assertTrue(any(t.endswith(":0") for t in tokens))

    def test_continuation_stops_when_the_pdf_changed(self):
        _, tokens = self.read_in_parts(self.kinds, 600)
        result = self.run_cli(str(self.ties), "--from", tokens[0])
        self.assertEqual(result.returncode, 2)
        self.assertIn("PDF が、続きの位置を出したときと違う", result.stderr)
        self.assertEqual(result.stdout, "")

    def test_bad_continuation_is_rejected(self):
        digest = hashlib.sha256(self.kinds.read_bytes()).hexdigest()[:12]
        for token in (f"{digest}:99:0", f"{digest}:1:999999", "garbage"):
            with self.subTest(token=token):
                result = self.run_cli(str(self.kinds), "--from", token)
                self.assertEqual(result.returncode, 2, result.stderr)

    def test_json_summary(self):
        result = self.run_cli(str(self.kinds), "--json", "--pages", "2-3,7")
        self.assertEqual(result.returncode, 0, result.stderr)
        summary = json.loads(result.stdout)
        data = self.kinds.read_bytes()
        self.assertEqual(summary["sha256"], hashlib.sha256(data).hexdigest())
        self.assertEqual(summary["pages"], 7)
        self.assertEqual(summary["kinds"], {"text": 3, "vertical": 1, "garbled": 1, "scan": 1, "blank": 1})
        self.assertEqual(summary["needs_check"], 2)
        self.assertEqual(summary["lists"]["needs_check"], {"count": 2, "ranges": "4,7", "next": None})
        self.assertEqual(summary["lists"]["kind:text"]["ranges"], "1,6-7")
        self.assertEqual(summary["extraction"], wiki_pdf_layer.extraction_identity())
        details = summary["page_details"]
        self.assertEqual([d["page"] for d in details], [2, 3, 7])
        layer_pages = list(wiki_pdf_layer.analyze_pages(data))
        self.assertEqual(details[2]["text_sha256"], layer_pages[6]["text_sha256"])
        self.assertEqual(details[1]["kind"], "garbled")

    def test_arguments(self):
        for args in (["--json", "--from", "x:1:0"], ["--pages", "1"], ["--max-chars", "0"], ["--json", "--pages", "9"]):
            with self.subTest(args=args):
                self.assertEqual(self.run_cli(str(self.kinds), *args).returncode, 2)


class StableOrderTests(Fixtures):
    """試験 7: 本文が毎回同じになる。決め方を外すと違いが出ることも確かめる。"""

    def hashes_in_process(self, side: str, paths: list[Path]) -> dict:
        result = subprocess.run([sys.executable, "-X", "utf8", str(HERE / "pdf_text_hashes.py"), side,
                                 *[str(p) for p in paths]],
                                capture_output=True, encoding="utf-8", env=ENV, timeout=1800)
        self.assertEqual(result.returncode, 0, result.stderr)
        return json.loads(result.stdout)

    def test_same_text_across_processes(self):
        paths = self.all_pdfs()
        runs = [self.hashes_in_process(side, paths) for side in ("wiki", "rag", "wiki", "rag")]
        for run in runs[1:]:
            self.assertEqual(run, runs[0])

    def plain_pdfminer(self, data: bytes, numbering=None) -> list[str]:
        """元の pdfminer で取り出す。numbering を渡すと、id(obj) の代わりにその番号で組の順を決める。"""
        import pdfminer.layout as layout
        from pdfminer.converter import TextConverter
        from pdfminer.layout import LAParams
        from pdfminer.pdfinterp import PDFPageInterpreter, PDFResourceManager
        from pdfminer.pdfpage import PDFPage

        original = layout.LTLayoutContainer.group_textboxes

        def patched(container, laparams, boxes):
            seen = {builtins.id(box): (box, n) for n, box in enumerate(numbering(boxes))}

            def fake_id(obj):
                key = builtins.id(obj)
                if key not in seen:
                    seen[key] = (obj, len(seen))
                return seen[key][1]

            layout.id = fake_id
            try:
                return original(container, laparams, boxes)
            finally:
                del layout.id

        texts, output, manager = [], io.StringIO(), PDFResourceManager()
        if numbering is not None:
            layout.LTLayoutContainer.group_textboxes = patched
        try:
            with TextConverter(manager, output, codec="utf-8", laparams=LAParams(**wiki_pdf_layer.LAPARAMS)) as device:
                interpreter = PDFPageInterpreter(manager, device)
                for page in PDFPage.get_pages(io.BytesIO(data)):
                    interpreter.process_page(page)
                    texts.append(wiki_pdf_layer.normalize_newlines(output.getvalue()).replace("\f", "").strip())
                    output.seek(0)
                    output.truncate(0)
        finally:
            layout.LTLayoutContainer.group_textboxes = original
        return texts

    def test_order_decides_the_text(self):
        """距離の同じ組の順を変えると、本文が変わる（試料が原因を捉えている）。"""
        data = self.ties.read_bytes()
        stable = [text for _, text in wiki_pdf_layer.pdfminer_pages(data)]
        columns_first = self.plain_pdfminer(data, lambda boxes: sorted(boxes, key=lambda b: (b.x0, -b.y0)))
        self.assertTrue(all(a != b for a, b in zip(stable, columns_first, strict=True)))
        self.assertTrue(stable[0].startswith("P0G0R0C0\n\nP0G0R0C1\n\nP0G0R1C0"))
        self.assertTrue(columns_first[0].startswith("P0G0R0C0\n\nP0G0R1C0\n\nP0G0R0C1"))

    def test_same_as_the_measured_prototype(self):
        """製品の関数は、測定で使った置きかえ（初めて見た順の番号）と同じ本文を返す。"""
        for path in self.all_pdfs():
            with self.subTest(pdf=path.name):
                data = path.read_bytes()
                stable = [text for _, text in wiki_pdf_layer.pdfminer_pages(data)]
                self.assertEqual(stable, self.plain_pdfminer(data, lambda boxes: list(boxes)))

    def test_threads_do_not_disturb_each_other(self):
        data = self.ties.read_bytes()
        expected = [text for _, text in wiki_pdf_layer.pdfminer_pages(data)]
        found, errors = [], []

        def work():
            try:
                for _ in range(5):
                    found.append([text for _, text in wiki_pdf_layer.pdfminer_pages(data)])
            except Exception as error:  # noqa: BLE001
                errors.append(error)

        threads = [threading.Thread(target=work) for _ in range(4)]
        for thread in threads:
            thread.start()
        for thread in threads:
            thread.join()
        self.assertEqual(errors, [])
        self.assertTrue(all(result == expected for result in found))


if __name__ == "__main__":
    unittest.main()
