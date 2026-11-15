# /// script
# requires-python = ">=3.12,<3.13"
# dependencies = ["pypdfium2==5.15.2", "pdfminer.six==20260107", "psutil==7.1.3"]
# ///
"""ADR-0025 の承認の条件 1: 長い PDF で、ページごとの取り出しの時間とメモリを測る。

使い方: uv run --script measure_time.py <PDF> [結果の名前に付ける接尾辞]
結果を results/time-<PDF の名前><接尾辞>.json に書く。ほかの処理と CPU を取り合わないよう、1 つだけで走らせる。

測るもの:
- judge: rag 0.5.3 の rag_pdf.inspect_page（PDFium でページを判定する。ADR-0025 の判定）の 1 ページあたりの時間
- pdfminer_pass: pdfminer.six を LAParams(detect_vertical=True) で、文書を 1 回だけ読み、ページごとに
  本文を受け取る方法（製品で使う方法）の 1 ページあたりの時間
- naive_calls: extract_text(page_numbers=[i]) をページごとに呼び直す方法を、一部のページで測る
  （文書を毎回読み直すので、後ろのページほど遅くなるかを見る）
- peak_working_set: プロセスのメモリの最大（Windows の peak working set。ほかの OS では RSS の最大を数える）
- same_text: 1 回だけ読む方法のページごとの本文が、extract_text で文書全体を取り出して改ページの文字で
  分けたものと同じか（検証で品質を測った出力と、製品の方法の出力が同じかの確かめ）
"""

from __future__ import annotations

import io
import json
import platform
import statistics
import sys
import threading
import time
from contextlib import closing
from pathlib import Path

import psutil

BENCH = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(BENCH.parents[2] / "info-hive-rag" / "scripts"))
LAPARAMS_KW = {"detect_vertical": True}


class PeakMemory:
    """50 ms ごとに RSS を見て、最大を覚える。Windows では peak working set も読む。"""

    def __init__(self) -> None:
        self.process = psutil.Process()
        self.peak = 0
        self._stop = threading.Event()
        self._thread = threading.Thread(target=self._run, daemon=True)

    def _run(self) -> None:
        while not self._stop.is_set():
            self.peak = max(self.peak, self.process.memory_info().rss)
            time.sleep(0.05)

    def __enter__(self):
        self._thread.start()
        return self

    def __exit__(self, *exc):
        self._stop.set()
        self._thread.join()
        info = self.process.memory_info()
        self.peak = max(self.peak, getattr(info, "peak_wset", 0) or 0, info.rss)


def summary(values: list[float]) -> dict:
    ordered = sorted(values)
    return {"n": len(values), "mean": round(statistics.mean(values), 4), "p50": round(ordered[len(ordered) // 2], 4),
            "p95": round(ordered[int(len(ordered) * 0.95) - 1], 4), "max": round(ordered[-1], 4),
            "total": round(sum(values), 2)}


def judge_pages(path: Path) -> tuple[list[float], int]:
    import pypdfium2 as pdfium
    from rag_pdf import inspect_page
    times = []
    with pdfium.PdfDocument(path.read_bytes()) as document:
        for number in range(len(document)):
            t0 = time.perf_counter()
            with closing(document[number]) as page:
                inspect_page(page)
            times.append(time.perf_counter() - t0)
        return times, len(document)


def pdfminer_pass(path: Path) -> tuple[list[str], list[float]]:
    """文書を 1 回だけ読み、ページごとに本文を受け取る。extract_text と同じ TextConverter を使う。"""
    from pdfminer.converter import TextConverter
    from pdfminer.layout import LAParams
    from pdfminer.pdfinterp import PDFPageInterpreter, PDFResourceManager
    from pdfminer.pdfpage import PDFPage

    texts, times = [], []
    output = io.StringIO()
    manager = PDFResourceManager()
    with path.open("rb") as handle:
        with TextConverter(manager, output, codec="utf-8", laparams=LAParams(**LAPARAMS_KW)) as device:
            interpreter = PDFPageInterpreter(manager, device)
            pages = PDFPage.get_pages(handle)
            while True:
                t0 = time.perf_counter()
                page = next(pages, None)
                if page is None:
                    break
                interpreter.process_page(page)
                times.append(time.perf_counter() - t0)
                texts.append(output.getvalue())
                output.seek(0)
                output.truncate(0)
    return texts, times


def naive_calls(path: Path, count: int, sample: int = 12) -> list[dict]:
    from pdfminer.high_level import extract_text
    from pdfminer.layout import LAParams
    picks = sorted({round(i * (count - 1) / (sample - 1)) for i in range(sample)})
    found = []
    for index in picks:
        t0 = time.perf_counter()
        extract_text(str(path), page_numbers=[index], laparams=LAParams(**LAPARAMS_KW))
        found.append({"page": index + 1, "seconds": round(time.perf_counter() - t0, 3)})
    return found


def main() -> None:
    path = Path(sys.argv[1]).resolve()
    from pdfminer.high_level import extract_text
    from pdfminer.layout import LAParams
    import importlib.metadata as md

    result = {"pdf": path.name, "bytes": path.stat().st_size, "machine": platform.platform(),
              "cpu": platform.processor(), "logical_cpus": psutil.cpu_count(),
              "ram_gb": round(psutil.virtual_memory().total / 2**30, 1),
              "python": platform.python_version(),
              "versions": {name: md.version(name) for name in ("pdfminer.six", "pypdfium2", "psutil")},
              "laparams": LAPARAMS_KW}
    with PeakMemory() as memory:
        t0 = time.perf_counter()
        judge_times, pages = judge_pages(path)
        result["judge_total_s"] = round(time.perf_counter() - t0, 2)
        t0 = time.perf_counter()
        texts, pass_times = pdfminer_pass(path)
        result["pdfminer_pass_total_s"] = round(time.perf_counter() - t0, 2)
    result["peak_memory_mb"] = round(memory.peak / 2**20, 1)
    result["pages_pdfium"] = pages
    result["pages_pdfminer"] = len(texts)
    result["judge_per_page_s"] = summary(judge_times)
    result["pdfminer_per_page_s"] = summary(pass_times)
    combined = [a + b for a, b in zip(judge_times, pass_times)]
    result["both_per_page_s"] = summary(combined)
    result["pages_over_0_5_s"] = sum(1 for s in combined if s > 0.5)
    result["pages_over_1_s"] = sum(1 for s in combined if s > 1.0)
    # ページごとの時間（数だけ。本文は書かない）
    result["judge_times_s"] = [round(s, 4) for s in judge_times]
    result["pdfminer_times_s"] = [round(s, 4) for s in pass_times]
    result["slowest_pages"] = sorted(({"page": i + 1, "seconds": round(s, 3)} for i, s in enumerate(pass_times)),
                                     key=lambda r: -r["seconds"])[:10]
    # 品質を測った出力（extract_text で文書全体）と、製品の方法（1 回だけ読む）の本文が同じかを確かめる
    whole = extract_text(str(path), laparams=LAParams(**LAPARAMS_KW)).split(chr(12))
    pass_pages = [t.rstrip(chr(12)) for t in texts]
    result["same_text_pages"] = sum(1 for a, b in zip(whole, pass_pages) if a == b)
    result["naive_calls"] = naive_calls(path, pages)
    out = BENCH / "results" / f"time-{path.stem}{sys.argv[2] if len(sys.argv) > 2 else ''}.json"
    out.parent.mkdir(exist_ok=True)
    out.write_bytes(json.dumps(result, ensure_ascii=False, indent=2).encode("utf-8"))
    print(json.dumps({k: v for k, v in result.items()
                      if k not in ("slowest_pages", "judge_times_s", "pdfminer_times_s")}, ensure_ascii=False, indent=1))


if __name__ == "__main__":
    main()
