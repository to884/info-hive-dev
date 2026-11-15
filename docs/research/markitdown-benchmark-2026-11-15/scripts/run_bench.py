# /// script
# requires-python = ">=3.12,<3.13"
# dependencies = ["markitdown[docx,pdf,pptx,xls,xlsx]==0.1.9", "pdfminer.six==20260107", "pdfplumber==0.11.10",
#                 "pypdfium2==5.15.2"]
# ///
"""今の取り込みの抽出と MarkItDown を、速度と機械的な指標で比べる。

使い方:
    uv run --script run_bench.py                 全部を計測し、outputs/ と results.json を書く
    uv run --script run_bench.py --metrics-only  保存した出力から指標だけを計算し直す
    uv run --script run_bench.py --startup       MarkItDown の起動の時間を段ごとに測り、results.json に足す
    uv run --script run_bench.py --one <方式> <ファイル>   1 回だけ変換する（起動を含めた時間の計測用）

方式:
    pdftotext   wiki の手順にある pdftotext。PATH の最初の pdftotext を使う（今回は Git for Windows の
                Xpdf 4.00 だった。Poppler ではない）。既定の読み順、UTF-8
    pdfminer    wiki の手順にある pdfminer.six の extract_text
    rag         rag 0.5.3 の rag_pdf.inspect_page（PDFium の文字の層。OCR はしない）と document.md の形
    wikifetch   wiki 0.18.0 の wiki_fetch.py --html-file（--no-images）
    text        wiki_encoding.py で文字コードを判定し、そのまま読む（CSV、JSON、XML の今の手順）
    markitdown  MarkItDown(enable_plugins=False).convert_local()
"""

from __future__ import annotations

import bisect
import importlib.metadata as md
import json
import os
import platform
import re
import shutil
import statistics
import subprocess
import sys
import tempfile
import time
import unicodedata
from contextlib import closing
from pathlib import Path

HERE = Path(__file__).resolve().parent
BENCH = HERE.parent
REPO = BENCH.parents[2]
CORPUS = BENCH / "corpus"
OUTPUTS = BENCH / "outputs"
WIKI_SCRIPTS = REPO / "info-hive-wiki" / "skills" / "info-hive" / "scripts"
RAG_SCRIPTS = REPO / "info-hive-rag" / "scripts"
sys.path.insert(0, str(HERE))
import content as C  # noqa: E402

WARM_RUNS = 5
COLD_RUNS = 3
PDF_METHODS = ["pdftotext", "pdfminer", "rag", "markitdown"]


def _json_values(value) -> list[str]:
    if isinstance(value, dict):
        return [s for k, v in value.items() for s in [str(k), *_json_values(v)]]
    if isinstance(value, list):
        return [s for v in value for s in _json_values(v)]
    return [str(value)]


def _xml_truth() -> list[str]:
    return ["在宅勤務の手引き", "2026.1", "在宅勤務は週に最大3日までとする。", "申請は前週の金曜日までに出す。",
            "通信費", "3000", "電気代", "1500", "情報システム部", "4021"]


def _epub_truth() -> list[str]:
    items = ["在宅の春（試料）"]
    for ch in C.EPUB_CHAPTERS:
        items += [ch["title"], *ch["paragraphs"]]
    return items


CSV_TRUTH = [c for row in C.CSV_ROWS for c in row]

DOC_TABLE = C.doc_rows()                 # 見出しの行と 4 つの行
SHEET_TABLES = [C.sheet_rows()[:5], C.sheet_rows()[5:]]  # 「経費」と「日別」。どちらも先頭が見出しの行

# 試料ごとの、比べる方式、正解、正解の表（表ごとに、先頭が見出しの行）、雑音とみなす文字列。
CASES = {
    "handbook.docx": dict(methods=["markitdown"], truth=C.doc_truth(True), tables=[DOC_TABLE], noise=[C.HEADER]),
    "handbook.pdf": dict(methods=PDF_METHODS, truth=C.doc_truth(True), tables=[DOC_TABLE], noise=[C.HEADER]),
    "handbook-2col.pdf": dict(methods=PDF_METHODS, truth=C.doc_truth(True), tables=[DOC_TABLE], noise=[C.HEADER]),
    "slides.pptx": dict(methods=["markitdown"], truth=C.slide_truth(True), tables=[DOC_TABLE], noise=[]),
    "slides.pdf": dict(methods=PDF_METHODS, truth=C.slide_truth(False), tables=[DOC_TABLE], noise=[]),
    "expenses.xlsx": dict(methods=["markitdown"], truth=C.sheet_truth(), tables=SHEET_TABLES, noise=[]),
    "expenses.xls": dict(methods=["markitdown"], truth=C.sheet_truth(), tables=SHEET_TABLES, noise=[]),
    # PDF の上で日付が「########」と表示されている（列の幅が足りない）ので、日付は正解から外す。
    # 表の照合では、外した値のセルを、何が入っていてもよいセルとして扱う。
    "expenses.pdf": dict(methods=PDF_METHODS, truth=C.sheet_truth(), tables=SHEET_TABLES, noise=[],
                         exclude=["2026-04-06", "2026-04-07", "2026-04-08"]),
    "article.html": dict(methods=["wikifetch", "markitdown"], truth=C.doc_truth(False), tables=[DOC_TABLE],
                         noise=C.HTML_NOISE + ["広告", "dataLayer"]),
    "staff-utf8.csv": dict(methods=["text", "markitdown"], truth=CSV_TRUTH, tables=[C.CSV_ROWS], noise=[]),
    "staff-cp932.csv": dict(methods=["text", "markitdown"], truth=CSV_TRUTH, tables=[C.CSV_ROWS], noise=[]),
    "policy.json": dict(methods=["text", "markitdown"], truth=_json_values(C.JSON_DATA), tables=[], noise=[]),
    "policy.xml": dict(methods=["text", "markitdown"], truth=_xml_truth(), tables=[], noise=[]),
    "story.epub": dict(methods=["markitdown"], truth=_epub_truth(), tables=[], noise=[]),
    "bundle.zip": dict(methods=["markitdown"], truth=C.doc_truth(True) + CSV_TRUTH + _json_values(C.JSON_DATA),
                       tables=[DOC_TABLE, C.CSV_ROWS], noise=[C.HEADER]),
}

# ---------------------------------------------------------------- 方式


def _pdftotext(path: Path) -> str:
    done = subprocess.run(["pdftotext", "-enc", "UTF-8", str(path), "-"], capture_output=True, check=True)
    return done.stdout.decode("utf-8")


def _pdfminer(path: Path) -> str:
    from pdfminer.high_level import extract_text
    return extract_text(str(path))


def _rag(path: Path) -> str:
    sys.path.insert(0, str(RAG_SCRIPTS))
    import pypdfium2 as pdfium
    from rag_pdf import inspect_page
    pages = []
    with pdfium.PdfDocument(path.read_bytes()) as document:
        for number in range(len(document)):
            with closing(document[number]) as page:
                text, _quality = inspect_page(page)
            pages.append(f"## p. {number + 1}\n\n{text}")
    return "\n\n".join(pages)


_WIKI_TMP: Path | None = None


def _wikifetch(path: Path) -> str:
    global _WIKI_TMP
    if _WIKI_TMP is None:
        _WIKI_TMP = Path(tempfile.mkdtemp(prefix="bench-wiki-"))
        (_WIKI_TMP / "wiki").mkdir()
        (_WIKI_TMP / "wiki" / "SCHEMA.md").write_text("# SCHEMA\n", encoding="utf-8")
        (_WIKI_TMP / "raw").mkdir()
    url = "https://intranet.example.jp/handbook"
    done = subprocess.run([sys.executable, str(WIKI_SCRIPTS / "wiki_fetch.py"), url, "--wiki", str(_WIKI_TMP / "wiki"),
                           "--raw-root", str(_WIKI_TMP / "raw"), "--slug", "article", "--html-file", str(path),
                           "--page-url", url, "--no-images", "--force", "--json"],
                          capture_output=True, env={**os.environ, "PYTHONUTF8": "1"})
    if done.returncode != 0:
        raise RuntimeError(done.stderr.decode("utf-8", "replace"))
    text = (_WIKI_TMP / "raw" / "article.md").read_text(encoding="utf-8")
    return re.sub(r"\A---\n.*?\n---\n", "", text, flags=re.S)


def _text(path: Path) -> str:
    sys.path.insert(0, str(WIKI_SCRIPTS))
    from wiki_encoding import detect
    data = path.read_bytes()
    return data.decode(detect(data)["encoding"])


_MID = None


def _markitdown(path: Path) -> str:
    global _MID
    if _MID is None:
        from markitdown import MarkItDown
        _MID = MarkItDown(enable_plugins=False)
    return _MID.convert_local(str(path)).text_content


METHODS = {"pdftotext": _pdftotext, "pdfminer": _pdfminer, "rag": _rag, "wikifetch": _wikifetch,
           "text": _text, "markitdown": _markitdown}

# ---------------------------------------------------------------- 指標

_MARKUP = re.compile(r"[|*#_`>\\]")
_THOUSANDS = re.compile(r"(?<=\d),(?=\d{3}(?!\d))")
_SEPARATOR = re.compile(r"\|?\s*:?-{3,}:?\s*(?:\|\s*:?-{3,}:?\s*)*\|?")
FORM_FEED = chr(12)
REPLACEMENT = chr(0xFFFD)


def canon(text: str) -> str:
    """比べるための形にする。NFKC にそろえ、Markdown の記号を空白にし、桁区切りのコンマを除き、空白を 1 つにまとめる。
    空白は消さずに残す。数値どうしの境目（「3000 1500」）を保つためである。"""
    text = unicodedata.normalize("NFKC", text)
    text = _THOUSANDS.sub("", _MARKUP.sub(" ", text))
    return re.sub(r"\s+", " ", text).strip()


def item_pattern(item: str) -> re.Pattern:
    """正解の文字列を探す正規表現。文字のあいだに空白 1 つ（PDF の行の折り返しなど）を許す。
    数字で始まる（終わる）ときは、前（後ろ）に数字と小数点が続かないことを求める。3000 が 30000 に当たらないようにする。"""
    chars = canon(item).replace(" ", "")
    body = " ?".join(re.escape(c) for c in chars)
    before = r"(?<![0-9.])" if chars[0].isdigit() else ""
    after = r"(?![0-9.])" if chars[-1].isdigit() else ""
    return re.compile(before + body + after)


def _cell_key(cell: str) -> str:
    return canon(cell).replace(" ", "")


def _longest_increasing(values: list[int]) -> int:
    """values の、狭義に増える最長の部分列の長さ。"""
    tails: list[int] = []
    for value in values:
        i = bisect.bisect_left(tails, value)
        tails[i:i + 1] = [value]
    return len(tails)


def _row_on_line(line: str, row: list) -> bool:
    cursor = 0
    for pattern in row:
        if pattern is None:  # 正解から外した値のセル
            continue
        found = pattern.search(line, cursor)
        if not found:
            return False
        cursor = found.end()
    return True


def _rows_on_line(lines: list[str], tables: list) -> tuple[int, int]:
    """行のセルがすべて、同じ 1 行に、正解の順に、数値の境目を保って出てくる行の数（見出しの行を含む）。
    出力の 1 つの行は、正解の 1 つの行にしか数えない。"""
    used: set[int] = set()
    count = total = 0
    for table in tables:
        for row in table:
            total += 1
            for i, line in enumerate(lines):
                if i not in used and _row_on_line(line, row):
                    used.add(i)
                    count += 1
                    break
    return count, total


def _md_tables(output: str) -> list[list[list[str]]]:
    """Markdown の表を取り出す。続いた「|」の行のうち、2 行目が区切りの行（|---|）のものだけを表とみなす。
    表ごとに、見出しの行と本体の行のセルの並びを返す（区切りの行は除く）。"""
    blocks, current = [], []
    for line in output.splitlines() + [""]:
        if line.strip().startswith("|"):
            current.append(line.strip())
            continue
        if len(current) >= 2 and _SEPARATOR.fullmatch(current[1]):
            blocks.append([[_cell_key(c) for c in row.strip("|").split("|")] for row in current[:1] + current[2:]])
        current = []
    return blocks


def _same(cells: list[str], want: list) -> bool:
    return len(cells) == len(want) and all(w is None or c == w for c, w in zip(cells, want))


def _rows_aligned(output: str, tables: list) -> tuple[int, int] | None:
    """正解の表ごとに、正解の見出しの行と同じセルが並ぶ行を Markdown の表の中から探す。その行より後ろで、
    本体の行のセルが、見出しと同じ列にそのまま入っている行の数を返す。見出しの行は、表の 1 行目でなくてよい
    （MarkItDown は DOCX の表の前に空の見出しの行を足す）。表を 1 つも出さない出力は None（列を確かめられない）。"""
    blocks = _md_tables(output)
    if not blocks:
        return None
    count = total = 0
    for header, *rows in tables:
        total += len(rows)
        places = [(block[r + 1:], h) for block in blocks for r, line in enumerate(block)
                  for h in range(len(line) - len(header) + 1) if _same(line[h:h + len(header)], header)]
        for row in rows:
            if any(_same(line[h:h + len(row)], row) for after, h in places for line in after):
                count += 1
    return count, total


def metrics(output: str, case: dict) -> dict:
    text = canon(output)
    exclude = set(case.get("exclude", []))
    truth = [t for t in case["truth"] if t not in exclude]
    # 正解ごとに、出力の中で当たったすべての位置。順に読めた割合では、正解ごとにどの位置を使ってもよい
    # （同じ値が何度も出てくる表やCSVで、最初の位置に縛られないため）。
    occurrences = [[m.start() for m in item_pattern(item).finditer(text)] for item in truth]
    positions = [occ[0] if occ else None for occ in occurrences]
    lines = [canon(line) for line in output.splitlines()]
    on_line = _rows_on_line(lines, [[[None if c in exclude else item_pattern(c) for c in row] for row in table]
                                    for table in case["tables"]])
    aligned = _rows_aligned(output, [[[None if c in exclude else _cell_key(c) for c in row] for row in table]
                                     for table in case["tables"]])
    has_tables = bool(case["tables"])
    return {
        "chars": len(output),
        "recall": round(sum(p is not None for p in positions) / len(truth), 3),
        "missing": [t for t, p in zip(truth, positions) if p is None],
        # 順に読めた割合: 正解の並びのうち、出力の中で原本の順に並べられる最長の部分列の長さを、正解の全体の数で
        # 割る。正解ごとに位置を 1 つ選ぶ（位置を大きい順に並べてつなぐと、狭義に増える部分列は、正解ごとに
        # 位置を 1 つしか含まない）。欠けた文も分母に入れる。前のほうの入れ替わり 1 つで、後ろを全部落とさない。
        "in_order": round(_longest_increasing([p for occ in occurrences for p in sorted(occ, reverse=True)])
                          / len(truth), 3),
        "rows_on_line": f"{on_line[0]}/{on_line[1]}" if has_tables else "-",
        "rows_aligned": (f"{aligned[0]}/{aligned[1]}" if aligned is not None else "表なし") if has_tables else "-",
        "headings": len(re.findall(r"^#{1,6} ", output, re.M)),
        "md_tables": len(_md_tables(output)),
        "list_items": len(re.findall(r"^\s*(?:[-*+]|\d+\.)\s", output, re.M)),
        "noise": {n: output.count(n) for n in case["noise"]},
        "location_markers": {
            "form_feed": output.count(FORM_FEED),
            "page_heading": len(re.findall(r"^## p\. \d+", output, re.M)),
            "slide_comment": len(re.findall(r"<!-- Slide number: \d+ -->", output)),
            "sheet_heading": len(re.findall(r"^## (経費|日別)$", output, re.M)),
            "file_heading": len(re.findall(r"^## File: ", output, re.M)),
        },
        "bad_chars": sum(ch == REPLACEMENT or 0xE000 <= ord(ch) <= 0xF8FF for ch in output),
    }


def self_test() -> None:
    """指標が、Sol の 1 回目と 2 回目のレビューで挙がった反例を見逃さないことを確かめる。"""
    csv_case = {"truth": CSV_TRUTH, "tables": [C.CSV_ROWS], "noise": []}
    one_line = " ".join(" ".join(row) for row in C.CSV_ROWS)
    got = metrics(one_line, csv_case)
    assert got["rows_on_line"] == "1/5", got  # 1 行につないだ出力は、1 つの正解の行にしか数えない
    assert got["rows_aligned"] == "表なし", got

    header = "| " + " | ".join(C.CSV_ROWS[0]) + " |\n| --- | --- | --- | --- |\n"
    good = header + "".join("| " + " | ".join(row) + " |\n" for row in C.CSV_ROWS[1:])
    assert metrics(good, csv_case)["rows_aligned"] == "4/4"
    shifted = header + "".join("| | " + " | ".join(row) + " |\n" for row in C.CSV_ROWS[1:])
    assert metrics(shifted, csv_case)["rows_aligned"] == "0/4"  # 見出しを残して本体を右へずらした表
    no_separator = good.replace("| --- | --- | --- | --- |\n", "")
    assert metrics(no_separator, csv_case)["rows_aligned"] == "表なし"  # 区切りの行のない「|」の行は表でない
    merged = header + "| A001 | 青木 遥 | | 営業部 3 |\n"
    assert metrics(merged, csv_case)["rows_aligned"] == "0/4"  # 値が隣の列に入った行
    blank_header = "|  |  |  |  |\n| --- | --- | --- | --- |\n" + good.replace("| --- | --- | --- | --- |\n", "")
    assert metrics(blank_header, csv_case)["rows_aligned"] == "4/4"  # 空の見出しの行のあとに、本当の見出しがある表
    assert metrics(good, csv_case)["in_order"] == 1.0  # 同じ値（在宅日数の 3）が何度も出ても、順は崩れていない

    sheet_case = {"truth": ["3000", "1500", "12"], "tables": [], "noise": []}
    assert metrics("30000 15000 120", sheet_case)["recall"] == 0.0  # 10 倍した値は、元の値に当たらない
    assert metrics("3000 1500 12", sheet_case)["recall"] == 1.0
    assert metrics("30001500 12", sheet_case)["recall"] == 0.333  # 区切りなしにつないだ数値は、元の値に当たらない

    order_case = {"truth": ["あいう", "かきく", "さしす", "たちつ", "なにぬ"], "tables": [], "noise": []}
    assert metrics("かきく さしす たちつ なにぬ あいう", order_case)["in_order"] == 0.8  # 先頭の 1 つが後ろへ移っただけ
    interleaved = "始業時に勤怠チャン 終業時にその日の作 ネルへ「開始」と書く 業を3行で報告する"
    got = metrics(interleaved, {"truth": ["始業時に勤怠チャンネルへ「開始」と書く", "終業時にその日の作業を3行で報告する"],
                                "tables": [], "noise": []})
    assert got["in_order"] == 0.0, got  # 混線して照合できない文は、順に読めた割合を下げる
    assert metrics("3,000円 と 1 . 目的", {"truth": ["3000円", "1. 目的"], "tables": [], "noise": []})["recall"] == 1.0
    print("指標の自己試験: 通った")


# ---------------------------------------------------------------- 計測

STARTUP_STEPS = {
    "python_only": "pass",
    "import_markitdown": "import markitdown",
    "construct": "from markitdown import MarkItDown; MarkItDown(enable_plugins=False)",
    "first_convert": ("from markitdown import MarkItDown; "
                      "MarkItDown(enable_plugins=False).convert_local(r'{path}')"),
}


def startup() -> dict:
    """MarkItDown の起動の時間を、段ごとに分けて測る（各段は前の段を含む）。"""
    path = CORPUS / "staff-utf8.csv"
    found = {}
    for step, code in STARTUP_STEPS.items():
        times = []
        for _ in range(COLD_RUNS):
            start = time.perf_counter()
            subprocess.run([sys.executable, "-c", code.format(path=path)], check=True, capture_output=True)
            times.append(time.perf_counter() - start)
        found[step] = round(statistics.median(times), 3)
    return found



def _cold(method: str, path: Path) -> float:
    times = []
    for _ in range(COLD_RUNS):
        start = time.perf_counter()
        subprocess.run([sys.executable, str(Path(__file__).resolve()), "--one", method, str(path)],
                       check=True, capture_output=True, env={**os.environ, "PYTHONUTF8": "1"})
        times.append(time.perf_counter() - start)
    return statistics.median(times)


def _warm(fn, path: Path) -> tuple[str, float]:
    output = fn(path)  # 準備（import、MarkItDown の初期化）を除くための 1 回目
    times = []
    for _ in range(WARM_RUNS):
        start = time.perf_counter()
        output = fn(path)
        times.append(time.perf_counter() - start)
    return output, statistics.median(times)


def _versions() -> dict:
    names = ["markitdown", "pdfminer.six", "pdfplumber", "pypdfium2", "mammoth", "python-pptx", "openpyxl",
             "xlrd", "pandas", "magika"]
    found = {}
    for name in names:
        try:
            found[name] = md.version(name)
        except md.PackageNotFoundError:
            found[name] = None
    # 手元の pdftotext が Poppler か Xpdf かは、版の表示の著作権の行で見分ける。
    exe = shutil.which("pdftotext")
    shown = subprocess.run(["pdftotext", "-v"], capture_output=True).stderr.decode("utf-8", "replace").splitlines()
    found["pdftotext"] = {"path": exe, "version": shown[:2]}
    found["python"] = platform.python_version()
    return found


def _print(record: dict) -> None:
    print(f"{record['file']:20} {record['method']:11} recall={record.get('recall')} in_order={record.get('in_order')} "
          f"line={record.get('rows_on_line')} aligned={record.get('rows_aligned')} warm={record.get('warm_s')} "
          f"cold={record.get('cold_s')}" + (f" ERROR {record['error'][:80]}" if "error" in record else ""), flush=True)


def _write(payload: dict) -> None:
    (BENCH / "results.json").write_bytes(json.dumps(payload, ensure_ascii=False, indent=2).encode("utf-8"))


def recompute() -> None:
    """保存した出力から指標だけを計算し直す。速度、出力、計測したときの版の記録（versions）は変えない。
    計算し直した環境は metrics_env に別に残す。"""
    payload = json.loads((BENCH / "results.json").read_text(encoding="utf-8"))
    payload["metrics_env"] = {"python": platform.python_version(), "machine": platform.platform(),
                              "at": time.strftime("%Y-%m-%dT%H:%M:%S%z")}
    for record in payload["results"]:
        if "output" not in record:
            continue
        output = (BENCH / record["output"]).read_bytes().decode("utf-8")
        keep = {k: record[k] for k in ["file", "method", "bytes", "warm_s", "cold_s", "output"]}
        record.clear()
        record.update(keep | metrics(output, CASES[keep["file"]]))
        _print(record)
    _write(payload)


def main() -> None:
    if len(sys.argv) == 4 and sys.argv[1] == "--one":
        METHODS[sys.argv[2]](Path(sys.argv[3]))
        return
    self_test()
    if sys.argv[1:] == ["--metrics-only"]:
        recompute()
        return
    if sys.argv[1:] == ["--startup"]:
        payload = json.loads((BENCH / "results.json").read_text(encoding="utf-8"))
        payload["startup_s"] = startup()
        print(payload["startup_s"])
        _write(payload)
        return
    OUTPUTS.mkdir(exist_ok=True)
    results = []
    for name, case in CASES.items():
        path = CORPUS / name
        for method in case["methods"]:
            record = {"file": name, "method": method, "bytes": path.stat().st_size}
            try:
                output, warm = _warm(METHODS[method], path)
                record["warm_s"] = round(warm, 4)
                record["cold_s"] = round(_cold(method, path), 3)
                out = OUTPUTS / f"{name}__{method}.md"
                out.write_bytes(output.encode("utf-8"))
                record["output"] = out.relative_to(BENCH).as_posix()
                record.update(metrics(output, case))
            except Exception as error:  # noqa: BLE001 - 失敗も結果として残す
                record["error"] = f"{type(error).__name__}: {error}"[:500]
            results.append(record)
            _print(record)
    _write({"versions": _versions(), "machine": platform.platform(), "warm_runs": WARM_RUNS,
            "cold_runs": COLD_RUNS, "startup_s": startup(), "results": results})


if __name__ == "__main__":
    main()
