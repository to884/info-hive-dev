"""文字層だけ違う開発用PDFに、同じ製品OCRが同じ結果を返すことを確かめる。"""

from contextlib import closing
import hashlib
import importlib.util
import io
import json
from pathlib import Path
import subprocess
import sys
import tempfile

from pdfminer.high_level import extract_text
from pypdfium2 import PdfDocument

HERE = Path(__file__).resolve().parent
GLYPH = HERE.parent / "dot-layout-v2/glyph-ambiguity.py"
SPEC = importlib.util.spec_from_file_location("fixture", GLYPH)
fixture = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(fixture)
ROOT = fixture.BENCH.parents[2]
sys.path.insert(0, str(ROOT / "info-hive-rag/scripts"))
import rag_pdf
from rag_config import Config
from rag_ocr_client import OcrClient


def pdf(mapping):
    # 同形の符号を通常のびっしりした文字列の中に置き、行検出も動かす。
    initial = fixture.pdf_with_mapping(mapping)
    stream_start = initial.index(b"5 0 obj\n")
    stream_end = initial.index(b"\nendobj", stream_start)
    stream = fixture.stream(b"BT /F1 16 Tf 8 80 Td (Alpha) Tj <85> Tj (Beta) Tj ET")
    replaced = initial[:stream_start] + b"5 0 obj\n" + stream + initial[stream_end:]
    begin_xref = replaced.index(b"xref\n")
    body = replaced[:begin_xref]
    xref = b"xref\n0 7\n0000000000 65535 f \n" + b"".join(
        f"{body.index(f'{i} 0 obj'.encode()):010} 00000 n \n".encode() for i in range(1, 7))
    trailer = f"trailer\n<< /Size 7 /Root 1 0 R >>\nstartxref\n{len(body)}\n%%EOF\n".encode()
    return body + xref + trailer


def sha(data):
    return hashlib.sha256(data).hexdigest()


def characterize(data, config, temporary, client):
    text = fixture.normalize(extract_text(io.BytesIO(data)))
    images = {}
    with closing(PdfDocument(data)) as document, closing(document[0]) as page:
        for dpi in (150, 450, rag_pdf.alt_dpi(config.ocr_dpi)):
            with closing(page.render(scale=dpi / 72)) as bitmap:
                images[str(dpi)] = sha(bitmap.to_pil().convert("RGB").tobytes())
        output = rag_pdf.ocr_page(page, config, temporary, client=client)
    if not output["lines"] or not output["flag_revision"]:
        raise ValueError("画像認識と製品の印が行単位で動いていない")
    return {"pdf_sha256": sha(data), "pixels": images, "source_codepoints": [ord(c) for c in text],
            "rows": len(output["lines"]), "output_sha256": sha(json.dumps(output, sort_keys=True).encode()),
            "flag_revision": output["flag_revision"]}, output


def main():
    target = HERE / "result.json"
    if target.exists():
        raise FileExistsError("開発用の検査を上書きしない")
    cache = subprocess.run(["uv", "cache", "dir"], check=True, capture_output=True, encoding="utf-8").stdout.strip()
    with tempfile.TemporaryDirectory(prefix="ocr-symbol-input-test-") as path:
        temporary = Path(path)
        configuration = Config({"data_dir": str(temporary / "data"), "uv_cache_dir": cache,
                                "ocr_mode": "always", "ocr_dpi": 150, "cpu_threads": 2})
        command = ["uv", "run", "--no-project", "--offline", "--script", str(ROOT / "info-hive-rag/scripts/rag_ocr.py")]
        with OcrClient(configuration, command=command) as client:
            a, result_a = characterize(pdf("2026"), configuration, temporary, client)
            b, result_b = characterize(pdf("30FB30FB30FB"), configuration, temporary, client)
    if (a["pdf_sha256"] == b["pdf_sha256"] or a["source_codepoints"] == b["source_codepoints"]
            or a["pixels"] != b["pixels"] or a["output_sha256"] != b["output_sha256"] or result_a != result_b):
        raise ValueError("文字層だけを差し替えたときに製品の画像認識や印が変わった")
    files = (GLYPH, Path(__file__), Path(rag_pdf.__file__), ROOT / "info-hive-rag/scripts/rag_ocr.py",
             ROOT / "info-hive-rag/scripts/rag_ocr_flags.py")
    report = {"scope": "development-existing-product-ocr-entrypoint", "all_equal": True, "fixtures": [a, b],
              "inputs": {p.relative_to(ROOT).as_posix(): sha(p.read_bytes()) for p in files}}
    with target.open("x", encoding="utf-8") as f:
        json.dump(report, f, ensure_ascii=False, indent=2)
    print(f"ToUnicodeだけ異なる2枚、製品OCR各{a['rows']}行。本文・行・印は一致。", flush=True)


if __name__ == "__main__":
    main()
