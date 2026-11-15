# /// script
# requires-python = ">=3.12,<3.13"
# dependencies = ["pypdfium2==5.15.2", "pdfminer.six==20260107"]
# ///
"""試料の PDF を 4 つの方式で取り出し、outputs/ に書く。ページごとの判定と文字数を pages.json に書く。

使い方: uv run --script extract.py

方式:
    wikipdf   ADR-0024 の仕様どおりの試作。rag 0.5.3 の rag_pdf.inspect_page で取り出して判定し、
              判定が text のページは本文を、garbled、scan、vertical のページは本文の代わりに 1 行を、
              blank のページは見出しだけを出す。image_coverage が 0.5 以上のページを「確かめるべきページ」にする。
              つなぎ方は rag の _write_markdown と同じ。
    poppler   Poppler の pdftotext（scoop の poppler 26.09.0）。既定の読み順、UTF-8。日本語の CMap
              （poppler-data 0.4.12）を、scoop の apps\\poppler\\share\\poppler に置いて使う
    xpdf      Xpdf の pdftotext（Git for Windows の 4.00）。既定の読み順、UTF-8。日本語の追加のデータ
              （xpdf-japanese）を、環境変数 XPDFRC の指す設定のファイルで読み込ませる（-cfg）
    pdfminer  pdfminer.six の extract_text

日本語の CMap がないと、Poppler は官報のような CID フォントの文字をほとんど出さず、Xpdf は文字化けする
（2026-11-15 に確かめた）。そのため、設定のファイルがなければ止まる。
"""

from __future__ import annotations

import json
import os
import subprocess
import sys
from contextlib import closing
from pathlib import Path

BENCH = Path(__file__).resolve().parent.parent
REPO = BENCH.parents[2]
CORPUS = BENCH / "corpus"
OUTPUTS = BENCH / "outputs"
sys.path.insert(0, str(REPO / "info-hive-rag" / "scripts"))

POPPLER = Path(os.environ["USERPROFILE"]) / "scoop" / "apps" / "poppler" / "current" / "bin" / "pdftotext.exe"
XPDF = Path(r"C:\Program Files\Git\mingw64\bin\pdftotext.exe")
XPDFRC = Path(os.environ.get("XPDFRC", Path(os.environ["USERPROFILE"]) / "pdf-cjk-data" / "xpdfrc"))
POPPLER_DATA = POPPLER.resolve().parents[2] / "share" / "poppler"
REVIEW_COVERAGE = 0.5
OCR_KINDS = {"garbled", "scan", "vertical"}


def wikipdf(path: Path) -> tuple[str, list[dict]]:
    import pypdfium2 as pdfium
    from rag_pdf import inspect_page
    pages, chunks = [], []
    with pdfium.PdfDocument(path.read_bytes()) as document:
        for number in range(len(document)):
            with closing(document[number]) as page:
                text, quality = inspect_page(page)
            review = quality["image_coverage"] >= REVIEW_COVERAGE
            if quality["kind"] in OCR_KINDS:
                body = f"（このページは OCR が要る: {quality['kind']}）"
            elif quality["kind"] == "blank":
                body = ""
            else:
                body = text
            chunks.append(f"## p. {number + 1}\n\n{body}")
            pages.append({"page": number + 1, **quality, "review": review, "text_chars": len(text.strip())})
    return "\n\n".join(chunks), pages


def pdftotext(exe: Path, path: Path, extra: list[str] = ()) -> str:
    done = subprocess.run([str(exe), *extra, "-enc", "UTF-8", str(path), "-"], capture_output=True, check=True)
    warnings = done.stderr.decode("utf-8", "replace")
    if "Missing language pack" in warnings:
        raise SystemExit(f"{exe.name} に日本語の CMap がない: {path.name}")
    return done.stdout.decode("utf-8", "replace")


def pdfminer(path: Path) -> str:
    from pdfminer.high_level import extract_text
    return extract_text(str(path))


def main() -> None:
    for need in (XPDFRC, POPPLER_DATA / "cidToUnicode" / "Adobe-Japan1"):
        if not need.exists():
            raise SystemExit(f"日本語のデータがない: {need}")
    OUTPUTS.mkdir(exist_ok=True)
    report = {}
    for path in sorted(CORPUS.glob("*.pdf")):
        text, pages = wikipdf(path)
        outputs = {"wikipdf": text, "poppler": pdftotext(POPPLER, path),
                   "xpdf": pdftotext(XPDF, path, ["-cfg", str(XPDFRC)]),
                   "pdfminer": pdfminer(path)}
        for method, output in outputs.items():
            (OUTPUTS / f"{path.stem}__{method}.txt").write_bytes(output.encode("utf-8"))
        # pdftotext と pdfminer は、ページの区切りに改ページの文字（U+000C）を入れる
        per_page = {m: [len(p.strip()) for p in outputs[m].split(chr(12))][:len(pages)] for m in ("poppler", "xpdf", "pdfminer")}
        for i, page in enumerate(pages):
            page["chars_by_method"] = {m: (per_page[m][i] if i < len(per_page[m]) else None) for m in per_page}
        report[path.name] = pages
        kinds = {}
        for page in pages:
            kinds[page["kind"]] = kinds.get(page["kind"], 0) + 1
        print(path.name, kinds, "review:", [p["page"] for p in pages if p["review"]])
    (BENCH / "pages.json").write_bytes(json.dumps(report, ensure_ascii=False, indent=2).encode("utf-8"))


if __name__ == "__main__":
    main()
