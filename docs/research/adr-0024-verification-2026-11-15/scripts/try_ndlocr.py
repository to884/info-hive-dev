# /// script
# requires-python = ">=3.12,<3.13"
# dependencies = ["pypdfium2==5.15.2", "filelock>=3,<5", "psutil>=7,<8", "pillow>=11,<14"]
# ///
"""rag 0.5.3 の OCR（NDLOCR-Lite）で、公開の試料の全ページを OCR し、時間を測る（書き直しの案の下調べ）。

使い方: uv run --script try_ndlocr.py <作業用のディレクトリ>
rag の ocr_mode が always のときと同じく、すべてのページを rag_pdf.ocr_page と OcrClient で OCR する。
rag の設定は、作業用のディレクトリを data_dir にした一時的なものを使い、rag の本当のデータの置き場所には触れない。
uv のキャッシュは、手元の既定のものを使う（環境変数 UV_CACHE_DIR があればそれ）。
outputs/<試料>__ndlocr.txt（ページを改ページの文字 U+000C でつないだもの）と outputs/ndlocr-times.json を書く。
"""

from __future__ import annotations

import json
import os
import subprocess
import sys
import time
from contextlib import closing
from pathlib import Path

BENCH = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(BENCH.parents[2] / "info-hive-rag" / "scripts"))
NAMES = ["whitepaper-point", "whitepaper-summary", "kanpo-p1", "kanpo-p2", "kanpo-p3", "kanpo-p4", "bert"]


def main() -> None:
    import pypdfium2 as pdfium
    from rag_config import Config
    from rag_ocr_client import OcrClient
    from rag_pdf import ocr_page

    work = Path(sys.argv[1]).resolve()
    work.mkdir(parents=True, exist_ok=True)
    uv_cache = os.environ.get("UV_CACHE_DIR") or subprocess.run(
        ["uv", "cache", "dir"], capture_output=True, text=True, check=True).stdout.strip()
    config = Config({"data_dir": str(work / "data"), "uv_cache_dir": uv_cache})
    times = {"ocr_dpi": config.ocr_dpi}
    start = time.perf_counter()
    with OcrClient(config) as client:
        times["client_start_s"] = round(time.perf_counter() - start, 2)
        for name in NAMES:
            t0 = time.perf_counter()
            pages = []
            with pdfium.PdfDocument((BENCH / "corpus" / f"{name}.pdf").read_bytes()) as document:
                for number in range(len(document)):
                    with closing(document[number]) as page:
                        pages.append(ocr_page(page, config, work, client=client))
            times[name] = {"seconds": round(time.perf_counter() - t0, 2), "pages": len(pages)}
            (BENCH / "outputs" / f"{name}__ndlocr.txt").write_bytes(chr(12).join(pages).encode("utf-8"))
            print(name, times[name], flush=True)
    (BENCH / "outputs" / "ndlocr-times.json").write_bytes(json.dumps(times, ensure_ascii=False, indent=2).encode("utf-8"))


if __name__ == "__main__":
    main()
