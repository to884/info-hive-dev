# 実データの 2 件を、直した read_pdf と extract_pages（OCR なし）に通す。原本は読むだけ。
import sys
import tempfile
from pathlib import Path

sys.path.insert(0, sys.argv[1])
from rag_config import Config  # noqa: E402
from rag_index import read_pdf  # noqa: E402
from rag_pdf import extract_pages  # noqa: E402

ROOT = Path(r"D:\Users\toshiki\OneDrive - Mokumoku.Net\Documents\My eBooks\L4")
NAMES = [
    "Comprehensive-Formal-Verification-of-an-OS-Microkernel.pdf",
    "From-L3-to-seL4-What-Have-We-Learnt-in-20-Years-of-L4-Microkernels.pdf",
]
with tempfile.TemporaryDirectory() as work:
    config = Config({"data_dir": str(Path(work) / "data"), "ocr_mode": "off"})
    for name in NAMES:
        data, info = read_pdf(ROOT / name)
        pages = extract_pages(data, config, Path(work) / name, None)
        kinds = {}
        for page in pages:
            kinds[page["quality"]["kind"]] = kinds.get(page["quality"]["kind"], 0) + 1
        chars = sum(len(page["text"]) for page in pages)
        print(name, "bytes", len(data), "pages", len(pages), "kinds", kinds, "chars", chars)
