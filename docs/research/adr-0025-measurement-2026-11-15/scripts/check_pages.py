# /// script
# requires-python = ">=3.12,<3.13"
# dependencies = ["pypdfium2==5.15.2", "pdfminer.six==20260107", "pypdf==6.1.3"]
# ///
"""ADR-0025 の承認の条件 2: ページの判定（PDFium）と本文（pdfminer）が同じページを指すかを確かめる。

使い方: uv run --script check_pages.py <PDF>...
結果を results/pages-<PDF の名前>.json に書く。

- 合成の PDF（corpus/expected-pages.json があるもの）: ページごとに、両方のエンジンの本文に、そのページの
  目印（MARKER-Pnn）が入り、ほかのページの目印が入らないかを確かめる。CropBox の外の文字と、注釈だけの
  ページの扱いが、2 つのエンジンで同じかも記録する。
- ほかの PDF: ページの数と、ページごとの本文の似かた（空白を除いた文字の 2 文字組の Jaccard 係数）を数える。
  同じページを指していれば、似かたは高くなる。0.5 未満のページを挙げる。すべてのページを前後 2 ページの
  pdfminer の本文とも比べ、もっとも似るずれ（best_offset）と、同じページとの差（margin）を記録する。
  best_offset が 0 以外なら、ページがずれている。margin が小さいページは、似た本文が続いていて、
  この方法では見分けにくい（似かたで分かるのは、ずれが見つからないことまでで、対応が一意であることではない）。
- ページツリーの形（入れ子の深さ、/Pages のノードの数、受け継いだ /Rotate のあるページ）を pypdf で数える。
"""

from __future__ import annotations

import io
import json
import re
import sys
from contextlib import closing
from pathlib import Path

BENCH = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(BENCH.parents[2] / "info-hive-rag" / "scripts"))


def pdfium_pages(path: Path) -> list[dict]:
    import pypdfium2 as pdfium
    from rag_pdf import inspect_page
    found = []
    with pdfium.PdfDocument(path.read_bytes()) as document:
        for number in range(len(document)):
            with closing(document[number]) as page:
                text, quality = inspect_page(page)
            found.append({"text": text, "kind": quality["kind"], "image_coverage": quality.get("image_coverage", 0.0)})
    return found


def pdfminer_pages(path: Path) -> list[str]:
    from pdfminer.converter import TextConverter
    from pdfminer.layout import LAParams
    from pdfminer.pdfinterp import PDFPageInterpreter, PDFResourceManager
    from pdfminer.pdfpage import PDFPage
    texts, output, manager = [], io.StringIO(), PDFResourceManager()
    with path.open("rb") as handle, TextConverter(manager, output, codec="utf-8",
                                                  laparams=LAParams(detect_vertical=True)) as device:
        interpreter = PDFPageInterpreter(manager, device)
        for page in PDFPage.get_pages(handle):
            interpreter.process_page(page)
            texts.append(output.getvalue().rstrip(chr(12)))
            output.seek(0)
            output.truncate(0)
    return texts


def tree_shape(path: Path) -> dict:
    from pypdf import PdfReader
    reader = PdfReader(str(path))
    root = reader.trailer["/Root"]["/Pages"]
    nodes, depth_max, leaf, inherited = 0, 0, 0, []

    # reader.pages を読むと、pypdf は親から受け継ぐ /Rotate をページの辞書に写す。受け継ぎを数えるため、
    # reader.pages より先に、ファイルのままのツリーをたどる。
    def walk(node, depth, parent_rotate):
        nonlocal nodes, depth_max, leaf
        node = node.get_object()
        if node.get("/Type") == "/Pages":
            nodes += 1
            depth_max = max(depth_max, depth)
            rotate = node.get("/Rotate", parent_rotate)
            for kid in node["/Kids"]:
                walk(kid, depth + 1, rotate)
        else:
            leaf += 1
            if "/Rotate" not in node and parent_rotate:
                inherited.append(leaf)

    walk(root, 0, None)
    return {"pages_nodes": nodes, "max_depth": depth_max, "inherited_rotate_pages": inherited[:50],
            "rotated_pages": sum(1 for p in reader.pages if p.rotation)}


def bigrams(text: str) -> set[str]:
    s = re.sub(r"\s+", "", text)
    return {s[i:i + 2] for i in range(len(s) - 1)}


def main() -> None:
    for arg in sys.argv[1:]:
        path = Path(arg).resolve()
        a, b = pdfium_pages(path), pdfminer_pages(path)
        result = {"pdf": path.name, "pages_pdfium": len(a), "pages_pdfminer": len(b), "tree": tree_shape(path)}
        expected_file = path.with_name("expected-pages.json")
        if path.name == "synthetic-pages.pdf" and expected_file.exists():
            expected = json.loads(expected_file.read_text(encoding="utf-8"))
            rows = []
            for i in range(len(a)):
                want = expected["markers"][str(i + 1)]
                found = {"pdfium": re.findall(r"MARKER-P\d\d", a[i]["text"]),
                         "pdfminer": re.findall(r"MARKER-P\d\d", b[i] if i < len(b) else "")}
                ok = all(m == ([want] if want else []) for m in found.values())
                rows.append({"page": i + 1, "kind": a[i]["kind"], "expected": want, **found, "ok": ok,
                             "hidden_pdfium": "HIDDEN-P09" in a[i]["text"],
                             "hidden_pdfminer": "HIDDEN-P09" in (b[i] if i < len(b) else ""),
                             "annot_pdfium": "ANNOT-P07" in a[i]["text"],
                             "annot_pdfminer": "ANNOT-P07" in (b[i] if i < len(b) else "")})
            result["pages"] = rows
            result["all_ok"] = all(r["ok"] for r in rows) and len(a) == len(b) == expected["pages"]
        else:
            sims = []
            for i in range(min(len(a), len(b))):
                x, y = bigrams(a[i]["text"]), bigrams(b[i])
                sim = len(x & y) / len(x | y) if (x | y) else 1.0
                sims.append({"page": i + 1, "kind": a[i]["kind"], "jaccard": round(sim, 3),
                             "pdfium_chars": len(a[i]["text"].strip()), "pdfminer_chars": len(b[i].strip())})
            low = [s for s in sims if s["jaccard"] < 0.5]
            # すべてのページを、前後 2 ページの pdfminer の本文とも比べる。ページがずれていれば、
            # ずれた先のほうが似る。同じページとの似かたと、前後のページのもっとも高い似かたの差
            # （margin）が小さいページは、似た本文が続いていて、この方法ではずれを見分けにくい。
            bmaps = [bigrams(t) for t in b]
            for s in sims:
                i = s["page"] - 1
                x = bigrams(a[i]["text"])
                near = {}
                for d in range(-2, 3):
                    if 0 <= i + d < len(b):
                        y = bmaps[i + d]
                        near[d] = round(len(x & y) / len(x | y), 3) if (x | y) else 1.0
                s["best_offset"] = max(near, key=lambda d: (near[d], d == 0))
                others = [v for d, v in near.items() if d != 0]
                s["margin"] = round(near[0] - max(others), 3) if others else None
                if s["best_offset"] != 0:
                    s["neighbours"] = near
            result["shifted_pages"] = [s["page"] for s in sims if s["best_offset"] != 0]
            margins = sorted(s["margin"] for s in sims if s["margin"] is not None)
            result["margin_min"] = margins[0] if margins else None
            result["margin_median"] = margins[len(margins) // 2] if margins else None
            result["pages_margin_below_0_1"] = [s["page"] for s in sims if s["margin"] is not None and s["margin"] < 0.1]
            result["pages_both_blank"] = [s["page"] for s in sims if s["pdfium_chars"] == 0 and s["pdfminer_chars"] == 0]
            result["jaccard_median"] = sorted(s["jaccard"] for s in sims)[len(sims) // 2] if sims else None
            result["jaccard_min"] = min((s["jaccard"] for s in sims), default=None)
            result["kinds"] = dict(sorted({k: sum(1 for p in a if p["kind"] == k) for k in {p["kind"] for p in a}}.items()))
            # ADR-0025 の「確かめるべきページ」の印: 画像が半分以上か、pdfminer の本文に (cid:N) か U+FFFD がある
            flagged = [i + 1 for i in range(min(len(a), len(b)))
                       if a[i]["image_coverage"] >= 0.5 or re.search(r"\(cid:\d+\)", b[i]) or "\ufffd" in b[i]]
            result["review_flag_pages"] = len(flagged)
            result["review_flag_ratio"] = round(len(flagged) / len(a), 3) if a else None
            result["review_flag_by_cause"] = {
                "image": sum(1 for i in range(len(a)) if a[i]["image_coverage"] >= 0.5),
                "cid": sum(1 for t in b if re.search(r"\(cid:\d+\)", t)),
                "fffd": sum(1 for t in b if "\ufffd" in t)}
            result["low_pages"] = low
            result["low_count"] = len(low)
        out = BENCH / "results" / f"pages-{path.stem}.json"
        out.parent.mkdir(exist_ok=True)
        out.write_bytes(json.dumps(result, ensure_ascii=False, indent=2).encode("utf-8"))
        brief = {k: v for k, v in result.items() if k not in ("pages", "low_pages", "pages_margin_below_0_1")}
        brief["pages_margin_below_0_1_count"] = len(result.get("pages_margin_below_0_1", []))
        print(json.dumps(brief, ensure_ascii=False))


if __name__ == "__main__":
    main()
