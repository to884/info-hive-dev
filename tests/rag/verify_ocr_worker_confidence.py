# 本物の rag_ocr.py --worker の応答を、extract_pages と OcrStore.save に通して確かめる
import functools
import json
import sys
import tempfile
from pathlib import Path

root = Path(sys.argv[1])
ocr_python = sys.argv[2]
sys.path.insert(0, str(root / "tests" / "contract"))
sys.path.insert(0, str(root / "info-hive-rag" / "scripts"))
import pdf_fixtures
import rag_pdf
from rag_config import OCR_CONFIDENCE_REVISION, Config
from rag_ocr_client import OcrClient

with tempfile.TemporaryDirectory() as folder:
    folder = Path(folder)
    pdf = folder / "kinds.pdf"
    pdf_fixtures.make_kinds_pdf(pdf)
    config = Config({"data_dir": str(folder / "data"), "ocr_mode": "auto", "ocr_dpi": 150,
                     "embedding_model": "cl-nagoya/ruri-v3-30m", "cpu_threads": 2})
    data = pdf.read_bytes()
    import hashlib
    doc_id = hashlib.sha256(data).hexdigest()
    command = [ocr_python, "-X", "utf8", str(root / "info-hive-rag" / "scripts" / "rag_ocr.py")]
    with OcrClient(config, command=command) as client:
        pages = rag_pdf.extract_pages(data, config, config.extraction_dir(doc_id), ocr_client=client)
    for page in pages:
        if page["ocr"]:
            stored = rag_pdf.OcrStore(config, doc_id).load(page["page"])
            record = stored["confidence"]
            lines = record["lines"] if record else None
            print(f"{page['page']} ページ（{page['kind']}）: confidence_min={page['confidence_min']}、"
                  f"confidence_revision={page['confidence_revision']}（今は {OCR_CONFIDENCE_REVISION}）、"
                  f"行 {len(lines) if lines is not None else '不明'}、本文 {page['text'][:30]!r}")
            assert page["confidence_revision"] == OCR_CONFIDENCE_REVISION, page
            assert lines is not None
            for line in lines:
                assert line["confidence"] is not None, line
                assert len(line["chars"]) == len(line["text"]), line
    print("本物の OCR のワーカーの応答を、確信度つきで保存できた")
