# /// script
# requires-python = ">=3.10"
# dependencies = ["markdown-it-py==3.0.0"]
# ///
"""PR #41 の GitHub の Codex のレビューが挙げた 4 つの場面で、gen.py を確かめる。配布対象ではない。

1. 再生成すると、消えたページと、前の --raw full で書いた PDF の絶対パスが残らない
2. 生成器のファイル（style.css、nav.js、data/ など）とページ用のディレクトリが衝突しない
3. 見出しの ID が、連番を付けた結果どうしでも重ならない
4. コードスパンとコードブロックの中の [[...]] をリンクにしない

使い方: uv run --script review_checks.py
"""
import json
import re
import shutil
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import gen  # noqa: E402

WORK = HERE / "out" / "review"


def write(root: Path, rel: str, text: str) -> None:
    path = root / rel
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8", newline="\n")


def main() -> int:
    if WORK.exists():
        shutil.rmtree(WORK)
    wiki = WORK / "wiki"
    out = WORK / "static"
    pdf = (WORK / "raw" / "原本.pdf")
    pdf.parent.mkdir(parents=True)
    pdf.write_bytes(b"%PDF-1.4\n")
    write(wiki, "concepts/対象.md", "# 対象\n\n## 例\n\n一つ目。\n\n## 例\n\n二つ目。\n\n## 例-1\n\n三つ目。\n")
    write(wiki, "concepts/参照.md",
          "# 参照\n\n本文のリンク [[対象]]、最後の見出しへ [[対象#例-1]]。\n\n"
          "コードスパン `[[対象]]` はそのまま。\n\n```\n[[対象]] もそのまま\n```\n")
    write(wiki, "sources/出典.md", f'---\ntype: "source"\nraw: "{pdf.resolve().as_posix()}"\n---\n\n# 出典\n')
    write(wiki, "style.css/メモ.md", "# style.css の下のメモ\n")
    write(wiki, "nav.js/メモ.md", "# nav.js の下のメモ\n")
    write(wiki, "data/メモ.md", "# data の下のメモ\n")
    results = {}

    # 1. 再生成
    gen.build(wiki.resolve(), out.resolve(), "full", 200)
    had_pdf = any("raw/原本.pdf" in p.read_text(encoding="utf-8", errors="replace")
                  for p in out.rglob("*.html"))
    (wiki / "sources" / "出典.md").unlink()
    gen.build(wiki.resolve(), out.resolve(), "basename", 200)
    left = [p.relative_to(out).as_posix() for p in out.rglob("*") if p.is_file()
            and ("出典" in p.name or "raw/原本.pdf" in p.read_text(encoding="utf-8", errors="replace"))]
    results["regenerate"] = {"first_had_pdf_path": had_pdf, "left_after_regenerate": left,
                             "temp_dirs": [p.name for p in WORK.iterdir() if ".tmp-" in p.name or ".old-" in p.name]}

    # 2. 生成器のファイルとの衝突
    names = json.loads((Path(str(out) + ".build-report.json")).read_text(encoding="utf-8"))["renamed"]
    results["assets"] = {"renamed": names, "style_css_is_file": (out / "style.css").is_file(),
                         "nav_js_is_file": (out / "nav.js").is_file(), "search_js_is_file": (out / "data" / "search.js").is_file()}

    # 3. 見出しの ID
    target = (out / "concepts" / "対象.html").read_text(encoding="utf-8")
    ids = re.findall(r'<h2 id="([^"]+)">', target)
    ref = (out / "concepts" / "参照.html").read_text(encoding="utf-8")
    anchor = re.search(r'href="([^"]*#[^"]+)"', ref).group(1)
    results["headings"] = {"ids": ids, "unique": len(ids) == len(set(ids)), "link_to_last": anchor}

    # 4. コードの中の [[...]]
    code_spans = re.findall(r"<code>(.*?)</code>", ref, flags=re.S)
    links = re.findall(r'<a class="wl[^"]*" href="[^"]+">([^<]+)</a>', ref)
    results["code"] = {"code_contents": code_spans, "links": links}

    ok = (results["regenerate"]["first_had_pdf_path"] and not left and not results["regenerate"]["temp_dirs"]
          and all(v for k, v in results["assets"].items() if k != "renamed")
          and results["headings"]["unique"]
          and results["headings"]["link_to_last"].endswith("#" + __import__("urllib.parse").parse.quote(ids[-1]))
          and all("[[対象]]" in c for c in code_spans) and len(code_spans) == 2 and len(links) == 2)
    print(json.dumps(results, ensure_ascii=False, indent=2))
    print("OK" if ok else "NG")
    return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(main())
