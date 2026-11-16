"""選んだページを、製品の関数（rag_pdf.ocr_page、confidence_record、confidence_min）で OCR し、行の記録を保存する。

使い方（rag の依存の環境で動かす）:
    python -X utf8 scripts/run_ocr.py <rag-ocr の環境の python> <tag>=<PDF のパス>@<ページ,ページ,...> ...

ページを省くと（<tag>=<PDF のパス>）、すべてのページを OCR する。
結果は corpus/ocr/<tag>-p<ページ>.json に書く。同じ PDF（SHA-256）の結果があれば飛ばす（途中から再開できる）。
OCR の本文を含むので、corpus/ の外に置かない。
"""

from __future__ import annotations

import hashlib
import json
import sys
import tempfile
import time
from contextlib import closing
from pathlib import Path

BENCH = Path(__file__).resolve().parent.parent
ROOT = BENCH.parents[2]
sys.path.insert(0, str(ROOT / "info-hive-rag" / "scripts"))

import pypdfium2 as pdfium  # noqa: E402
import rag_pdf  # noqa: E402
from rag_config import OCR_CONFIDENCE_REVISION, Config  # noqa: E402
from rag_ocr_client import OcrClient  # noqa: E402

OUT = BENCH / "corpus" / "ocr"


def main() -> None:
    ocr_python, specs = sys.argv[1], sys.argv[2:]
    OUT.mkdir(parents=True, exist_ok=True)
    with tempfile.TemporaryDirectory() as folder:
        folder = Path(folder)
        config = Config({"data_dir": str(folder / "data"), "ocr_mode": "always", "ocr_dpi": 150,
                         "embedding_model": "cl-nagoya/ruri-v3-30m", "cpu_threads": 4})
        command = [ocr_python, "-X", "utf8", str(ROOT / "info-hive-rag" / "scripts" / "rag_ocr.py")]
        with OcrClient(config, command=command) as client:
            for spec in specs:
                tag, _, rest = spec.partition("=")
                path, _, pages = rest.partition("@")
                data = Path(path).read_bytes()
                sha = hashlib.sha256(data).hexdigest()
                with pdfium.PdfDocument(data) as document:
                    numbers = [int(n) for n in pages.split(",")] if pages else list(range(1, len(document) + 1))
                    for number in numbers:
                        target = OUT / f"{tag}-p{number:04d}.json"
                        # 同じ PDF（SHA-256 が同じ）の結果だけを使い回す。違えば OCR し直して上書きする
                        if target.exists() and json.loads(target.read_bytes().decode("utf-8"))["pdf_sha256"] == sha:
                            continue
                        started = time.perf_counter()
                        with closing(document[number - 1]) as page:
                            response = rag_pdf.ocr_page(page, config, folder, client=client)
                        record = rag_pdf.confidence_record(response)
                        entry = {"confidence": record}
                        result = {"tag": tag, "pdf_sha256": sha, "page": number, "text": response["text"],
                                  "confidence_revision": record["revision"] if record else None,
                                  "confidence_min": rag_pdf.confidence_min(entry),
                                  "lines": record["lines"] if record else None,
                                  "seconds": round(time.perf_counter() - started, 3)}
                        assert result["confidence_revision"] == OCR_CONFIDENCE_REVISION, result
                        target.write_bytes(json.dumps(result, ensure_ascii=False).encode("utf-8"))
                        print(tag, number, result["confidence_min"], len(result["lines"]), "行",
                              result["seconds"], "秒", flush=True)


if __name__ == "__main__":
    main()
