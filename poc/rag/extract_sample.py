"""参照だけで選んだ PDF の抽出量と速度を比較する。本文はローカルの派生領域だけに置く。"""
import hashlib
import json
import os
import sys
import time
import warnings
from contextlib import closing
from pathlib import Path

import fitz
import pypdfium2 as pdfium

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "info-hive-rag/scripts"))
from rag_pdf import inspect_page

work = Path(os.environ["LOCALAPPDATA"]) / "info-hive/rag-poc/2026-11-04"
manifest = json.loads((work / "sample-manifest.json").read_text(encoding="utf-8"))
results = []
with (work / "pages.jsonl").open("w", encoding="utf-8") as output:
    for number, entry in enumerate(manifest["files"]):
        path = Path(manifest["root"]) / entry["relative_path"]
        row = {"sample": number, "bytes": entry["size"]}
        start = time.perf_counter()
        data = path.read_bytes()
        row["read_seconds"] = time.perf_counter() - start
        row["sha256"] = hashlib.sha256(data).hexdigest()
        chars, bad, kinds = 0, 0, {}
        nonspace, text_bytes = 0, 0
        start = time.perf_counter()
        with warnings.catch_warnings():
            warnings.simplefilter("ignore")
            with pdfium.PdfDocument(data) as document:
                row["pages"] = len(document)
                for page_number in range(len(document)):
                    with closing(document[page_number]) as page, closing(page.get_textpage()) as textpage:
                        text = textpage.get_text_range()
                        chars += len(text)
                        nonspace += sum(not character.isspace() for character in text)
                        text_bytes += len(text.encode("utf-8"))
                        bad += text.count("\ufffd")
                        # ページの分類は検査コストを分けて後で代表ページに対して行う。
                        kind = "text" if len(text.strip()) >= 20 else "needs_inspection"
                        kinds[kind] = kinds.get(kind, 0) + 1
                        output.write(json.dumps({"sample": number, "page": page_number + 1, "text": text}, ensure_ascii=False) + "\n")
        row.update(pdfium_seconds=time.perf_counter() - start, pdfium_chars=chars, pdfium_nonspace=nonspace, pdfium_text_bytes=text_bytes, pdfium_replacement=bad, kinds=kinds)
        start = time.perf_counter()
        chars, bad, nonspace = 0, 0, 0
        with fitz.open(stream=data, filetype="pdf") as document:
            for page in document:
                text = page.get_text(sort=True)
                chars += len(text)
                nonspace += sum(not character.isspace() for character in text)
                bad += text.count("\ufffd")
        row.update(pymupdf_seconds=time.perf_counter() - start, pymupdf_chars=chars, pymupdf_nonspace=nonspace, pymupdf_replacement=bad)
        del data
        results.append(row)
        output.flush()
        (work / "extraction-progress.json").write_text(json.dumps(results, ensure_ascii=False, indent=2), encoding="utf-8")
        print(json.dumps(row, ensure_ascii=False), flush=True)
destination = ROOT / "docs/research/rag-poc-2026-11-04"
destination.mkdir(parents=True, exist_ok=True)
(destination / "extraction-results.json").write_text(json.dumps({"sample_manifest": str(work / "sample-manifest.json"), "files": results}, ensure_ascii=False, indent=2), encoding="utf-8")
