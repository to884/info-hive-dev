"""browse の探しやすさの試作に使う、3 つの形の Wiki を作る。

- indexed: 評価のコーパスに、索引の行（`- [[ページ]]: 要約`）つきの index.md を足した写し
- noindex: 評価のコーパスそのものの写し（index.md がない。全ページが「索引にないページ」に入る）
- large:   indexes/ に分割した、数百ページの合成 Wiki

使い方: python -X utf8 make_wikis.py <出力先のディレクトリ> [--pages 400]
出力先の下に indexed/、noindex/、large/ を作り直す。配布対象ではない。
"""
from __future__ import annotations

import argparse
import random
import re
import shutil
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
CORPUS = HERE.parents[2] / "info-hive-wiki" / "eval" / "retrieval" / "ja" / "corpus" / "wiki"

TYPE_HEADINGS = (("source", "ソース", "sources"), ("entity", "エンティティ", "entities"),
                 ("concept", "コンセプト", "concepts"), ("synthesis", "シンセシス", "synthesis"))


def write(path: Path, text: str) -> None:
    # Windows の write_text は CRLF にするので、バイト列で書く。
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes(text.encode("utf-8"))


def lead_sentence(text: str) -> str:
    """frontmatter と最初の見出しのあとの、最初の段落の最初の文を返す。"""
    text = text.lstrip("﻿").replace("\r\n", "\n")   # BOM と CRLF のページもある
    body = re.sub(r"\A---\n.*?\n---\n", "", text, flags=re.S)
    for para in re.split(r"\n\s*\n", body):
        para = para.strip()
        if not para or para.startswith("#"):
            continue
        para = re.sub(r"\[\[([^\]|#]+)(?:#[^\]|]*)?(?:\|([^\]]+))?\]\]", lambda m: m.group(2) or m.group(1), para)
        first = re.split(r"(?<=。)", para.replace("\n", ""))[0]
        return first.rstrip("。")
    return ""


def page_type(text: str) -> str:
    m = re.search(r'^type:\s*"?([a-z]+)"?', text, flags=re.M)
    return m.group(1) if m else ""


def make_indexed(out: Path) -> None:
    shutil.copytree(CORPUS, out)
    by_type: dict = {t: [] for t, _h, _d in TYPE_HEADINGS}
    for md in sorted(out.rglob("*.md")):
        if md.name == "SCHEMA.md":
            continue
        text = md.read_bytes().decode("utf-8-sig")
        by_type.setdefault(page_type(text), []).append((md.stem, lead_sentence(text)))
    lines = ["# Wiki のインデックス", "", "評価のコーパスに、試作のために足した索引である。", ""]
    for t, heading, _d in TYPE_HEADINGS:
        lines += [f"## {heading}", ""]
        lines += [f"- [[{slug}]]: {summary}" for slug, summary in by_type.get(t, [])]
        lines.append("")
    write(out / "index.md", "\n".join(lines))


def make_noindex(out: Path) -> None:
    shutil.copytree(CORPUS, out)


FIELDS = {
    "source": ("ソース", ["論文", "記事", "講演", "議事録", "書籍の章", "社内メモ"]),
    "entity": ("エンティティ", ["組織", "人物", "製品", "ライブラリ", "地域"]),
    "concept": ("コンセプト", ["検索", "自然言語処理", "データ構造", "税と制度", "健康", "文字コード"]),
    "synthesis": ("シンセシス", ["比較", "手順", "振り返り", "判断の記録"]),
}
WORDS = ["索引", "分かち書き", "正規化", "埋め込み", "再現率", "適合率", "形態素", "転置索引", "近似最近傍",
         "語彙", "表記ゆれ", "全角と半角", "異体字", "ルビ", "縦書き", "禁則", "改行", "要約", "引用",
         "出典", "版", "差分", "移行", "障害", "監視", "権限", "暗号", "署名", "課税", "控除", "申告",
         "熱中症", "水分", "睡眠", "鉄道", "地図", "気象", "観光", "会議", "記録"]
TAGS = ["検索", "自然言語処理", "日本語", "税金", "健康", "交通", "文字コード", "設計", "運用", "比較",
        "AI", "データベース", "セキュリティ", "障害", "行政", "地域"]


def make_large(out: Path, pages: int, seed: int = 7) -> None:
    rnd = random.Random(seed)
    types = [t for t, _h, _d in TYPE_HEADINGS]
    weights = [3, 2, 4, 1]
    entries = []   # (type, field, slug, title, summary)
    for i in range(pages):
        t = rnd.choices(types, weights)[0]
        field = rnd.choice(FIELDS[t][1])
        a, b = rnd.sample(WORDS, 2)
        title = {"source": f"{a}についての{field}（{2020 + i % 7}）",
                 "entity": f"{a}{b}の{field}",
                 "concept": f"{a}と{b}",
                 "synthesis": f"{a}と{b}の{field}"}[t]
        slug = f"{t[:3]}-{i:04d}"
        summary = f"{a}を{b}の観点から整理した{FIELDS[t][0]}のページ"
        entries.append((t, field, slug, title, summary))
    slugs = [e[2] for e in entries]
    for t, field, slug, title, summary in entries:
        tags = rnd.sample(TAGS, rnd.randint(1, 3))
        y, m, d = 2025 + rnd.randint(0, 1), rnd.randint(1, 12), rnd.randint(1, 28)
        links = rnd.sample(slugs, 3)
        heads = rnd.sample(["概要", "背景", "仕組み", "使い方", "注意点", "比較", "関係するページ", "経緯", "例"],
                           rnd.randint(2, 4))
        body = [f"# {title}", "", f"{summary}である。[[{links[0]}]] と [[{links[1]}]] に関係する。", ""]
        for h in heads:
            body += [f"## {h}", "", f"{h}について書く。詳しくは [[{links[2]}]] を見る。", ""]
        fm = ["---", f'type: "{t}"', f'title: "{title}"', "tags: [" + ", ".join(f'"{x}"' for x in tags) + "]",
              "sources: []", f"created: {y}-{m:02d}-{d:02d}", f"updated: {y}-{m:02d}-{d:02d}", "---", ""]
        sub = dict((tt, dd) for tt, _h, dd in TYPE_HEADINGS)[t]
        write(out / sub / f"{slug}.md", "\n".join(fm + body))
    for t, heading, _d in TYPE_HEADINGS:
        lines = ["---", f'title: "{heading}の索引"', "---", "", f"# {heading}", ""]
        for field in FIELDS[t][1]:
            rows = [e for e in entries if e[0] == t and e[1] == field]
            if not rows:
                continue
            lines += [f"## {field}", ""]
            lines += [f"- [[{slug}]]: {summary}" for _t, _f, slug, _ti, summary in rows]
            lines.append("")
        write(out / "indexes" / f"{t}.md", "\n".join(lines))
    write(out / "index.md", "\n".join(
        ["# Wiki のインデックス", "", "分割した索引の一覧である。", "", "## 索引", ""]
        + [f"- [[indexes/{t}]]: {heading}の一覧" for t, heading, _d in TYPE_HEADINGS] + [""]))
    write(out / "SCHEMA.md", "# スキーマ\n\n試作の合成 Wiki。\n")


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("out")
    ap.add_argument("--pages", type=int, default=400)
    args = ap.parse_args()
    out = Path(args.out)
    for name in ("indexed", "noindex", "large"):
        if (out / name).exists():
            shutil.rmtree(out / name)
    out.mkdir(parents=True, exist_ok=True)
    make_indexed(out / "indexed")
    make_noindex(out / "noindex")
    make_large(out / "large", args.pages)
    for name in ("indexed", "noindex", "large"):
        n = sum(1 for p in (out / name).rglob("*.md"))
        print(f"{name}: {n} 個の .md")
    return 0


if __name__ == "__main__":
    sys.exit(main())
