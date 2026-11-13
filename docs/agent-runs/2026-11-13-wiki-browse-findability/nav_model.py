"""browse の索引の木の規則（設計書 2.1）の参照の実装。

1 つ目の段（N1。索引の解析、項目の決め方、リンクの解決、グループの ID）は、今の中核の
`Core._nav()` をそのまま使う。設計は 1 つ目の段を変えないので、別に書き直すと、コードの中の
`[[…]]`、Setext の見出し、`[[a.md]]` のようなリンクで、今の実装と食い違う（4 回目のレビュー）。
この参照の実装が持つのは、新しく足す 2 つ目の段（N2 の `index.md` の名前、N3〜N8）と、グループの
要約（N5。4.2 の 2 と同じ取り方）だけである。

設計書の「当てはめの例」の表は、この実装の出力から写す。手で書いた期待は使わない。
実装（wiki_browse_core.py）の試験は、このファイルの CASES を入力にし、同じ木になることを確かめる。

使い方（info-hive-dev のルートで）:
  uv run --with pyyaml==6.0.3 python -X utf8 -B docs/agent-runs/2026-11-13-wiki-browse-findability/nav_model.py [--markdown]
"""
from __future__ import annotations

import shutil
import sys
import tempfile
from pathlib import Path

HERE = Path(__file__).resolve().parent
SCRIPTS = HERE.parents[2] / "info-hive-wiki" / "skills" / "info-hive" / "scripts"
sys.path.insert(0, str(SCRIPTS))

import wiki_browse_core as core  # noqa: E402
import wiki_pages  # noqa: E402

TYPE_LABELS = {"source": "ソース", "entity": "エンティティ", "concept": "コンセプト", "synthesis": "シンセシス"}
SEPARATORS = ":：—–-"


class StageOneCore(core.Core):
    """今の Core そのもの。項目に、4.2 の 2 の取り方で、最初の wikilink より後ろの表示の文字を足すだけ。"""

    def _nav_item(self, inline_tok, group_of_file):
        item = super()._nav_item(inline_tok, group_of_file)
        if item is not None:
            item["after"] = after_first_link(inline_tok)
        return item


def after_first_link(inline_tok) -> str:
    """段落の最初の wikilink（`_nav_item()` が項目に選ぶもの）より後ろを、inline_text() で表示の文字にする。"""
    children = inline_tok.children or []
    for i, child in enumerate(children):
        if child.type == "text" and "[[" in child.content:
            m = wiki_pages.WIKILINK_FULL_RE.search(child.content)
            if not m:
                continue
            rest = child.copy()
            rest.content = child.content[m.end():]
            text = core.inline_text([rest] + list(children[i + 1:]))
            return text.strip().lstrip(SEPARATORS).strip()
    return ""


def stage_one(root: Path) -> tuple:
    """今の Core で 1 つ目の段を作る。ファイルのグループ（読めた索引のファイルの数だけ、先頭に並ぶ）と Core を返す。"""
    c = StageOneCore(core.take_snapshot(root), record=False)
    readable = [f for f in c.snapshot.by_kind("index") if f.text is not None]
    files = {}
    for f, g in zip(readable, c.nav_groups):
        assert g["id"] == "_g" + core.short_hash(f.disk_rel, 10), "ファイルのグループの並びが想定と違う"
        files[f.rel] = g
    return files, c


def walk(groups):
    for g in groups:
        yield g
        yield from walk(g["children"])


def build(root: Path) -> list:
    files, c = stage_one(root)
    id_to_rel = {g["id"]: rel for rel, g in files.items()}
    for rel, g in files.items():
        g["origin"] = rel
        for x in walk(g["children"]):
            x["origin"] = rel
        g["summary"] = ""
        if rel == "index.md":
            g["title"] = "索引"                      # N2
        # N3: 1 度だけ畳む
        if not g["items"] and len(g["children"]) == 1:
            child = g["children"][0]
            g["items"], g["children"] = child["items"], child["children"]
    top = []
    index_top = files.get("index.md")
    if index_top is not None:                       # N4
        if index_top["items"]:
            top.append({**index_top, "title": "索引", "children": []})
        top.extend(index_top["children"])
    order, summaries = [], {}                       # N5
    if index_top is not None:
        for g in walk([index_top]):
            for it in g["items"]:
                if it["state"] == "group":
                    rel = id_to_rel[it["group"]]
                    if rel not in summaries:
                        order.append(rel)
                        summaries[rel] = it.get("after", "")
    for rel in sorted(files):
        if rel != "index.md" and rel not in order:
            order.append(rel)
    for rel in order:
        files[rel]["summary"] = summaries.get(rel, "")
        top.append(files[rel])

    def only_group_items(g):
        return all(it["state"] == "group" for x in walk([g]) for it in x["items"])

    def prune(groups):                               # N6
        kept = []
        for g in groups:
            if g.get("origin") == "index.md" and only_group_items(g):
                continue
            g["children"] = prune(g["children"])
            kept.append(g)
        return kept

    top = prune(top)
    listed = {it["id"] for g in walk(top) for it in g["items"] if it["state"] == "resolved"}
    rest = sorted(pid for pid in c.drawn if pid not in listed)
    if rest:                                         # N7
        by_type = {}
        for pid in rest:
            by_type.setdefault(str(c.page(pid)["meta"].get("type") or ""), []).append(pid)
        top.append({"id": "_rest", "title": "索引にないページ", "summary": "", "items": [], "origin": "",
                    "children": [{"id": f"_rest_{t}", "title": TYPE_LABELS.get(t, t or "種類なし"), "summary": "",
                                  "origin": "", "children": [],
                                  "items": [{"state": "resolved", "id": pid, "label": c.title(pid)} for pid in pids]}
                                 for t, pids in sorted(by_type.items())]})

    def count(g):                                    # N8
        ids = {it["id"] for it in g["items"] if it["state"] == "resolved"}
        for ch in g["children"]:
            ids |= count(ch)
        g["count"] = len(ids)
        return ids

    for g in top:
        count(g)
    shown = {g["id"] for g in walk(top)}            # 2.1 の末尾の性質
    for g in walk(top):
        for it in g["items"]:
            assert it["state"] != "group" or it["group"] in shown, f"木にないグループを指す: {g['title']}"
    return top


def render(top: list, id_to_title: dict) -> list:
    out = []

    def rec(g, depth):
        items = []
        for it in g["items"]:
            if it["state"] == "resolved":
                items.append(it["id"].rsplit("/", 1)[-1] + (f"#{it['anchor']}" if it.get("anchor") else ""))
            elif it["state"] == "group":
                items.append("→" + id_to_title.get(it["group"], "?"))
            else:
                items.append(f"?{it['label']}（{it['state']}）")
        line = "　" * depth + f"{g['title']}（{g['count']}）"
        if g.get("summary"):
            line += f"「{g['summary']}」"
        if items:
            line += ": " + "、".join(items)
        out.append(line)
        for ch in g["children"]:
            rec(ch, depth + 1)

    for g in top:
        rec(g, 0)
    return out


def page(slug: str, type_: str, title: str = "") -> str:
    return f'---\ntype: "{type_}"\ntitle: "{title or slug}"\n---\n\n# {title or slug}\n\n本文。\n'


# 設計書の当てはめの例と、レビューの反例。値が bytes のファイルは、そのまま書く（読めない索引の再現）。
# ページは concepts/ に置き、索引からはスラッグ（ディレクトリなし）で指す。
CASES = [
    ("1 回目のレビューの重大 2", {"index.md": "# 索引\n- [[a]]\n\n## 分類\n- [[b]]\n"}, {"a": "concept", "b": "concept"}),
    ("見出しが 2 つの h1", {"indexes/x.md": "# 表題\n## 旧節\n- [[a]]\n# 別章\n- [[b]]\n"}, {"a": "concept", "b": "concept"}),
    ("frontmatter の title と h1（3 回目のレビューの重大 1）",
     {"indexes/concept.md": "---\ntitle: コンセプトの索引\n---\n# コンセプト\n## 検索\n- [[a]]\n"}, {"a": "concept"}),
    ("index.md が分割した索引への行だけ（3 回目のレビューの重大 1）",
     {"index.md": "# Wiki のインデックス\n## 索引\n- [[indexes/source]]: ソースの一覧\n",
      "indexes/source.md": "# ソース\n- [[s]]\n"}, {"s": "source"}),
    ("index.md が見出しなしで分割した索引への行だけ",
     {"index.md": "- [[indexes/source]]: ソースの一覧\n- [[indexes/concept]]\n",
      "indexes/source.md": "# ソース\n- [[s]]\n", "indexes/concept.md": "# コンセプト\n- [[c]]\n"},
     {"s": "source", "c": "concept"}),
    ("中継の索引（2 回目のレビューの重大 1）",
     {"index.md": "# 入口\n- [[a]]\n- [[indexes/relay]]\n", "indexes/relay.md": "# 中継\n- [[indexes/leaf]]\n",
      "indexes/leaf.md": "# 記事\n- [[b]]\n"}, {"a": "concept", "b": "concept"}),
    ("index.md がない", {"indexes/b.md": "# B\n- [[y]]\n", "indexes/a.md": "# A\n- [[x]]\n"},
     {"x": "concept", "y": "entity", "z": ""}),
    ("読めない索引のファイル", {"index.md": "# 索引\n- [[indexes/broken]]\n- [[a]]\n", "indexes/broken.md": b"\xff\xfe\x00bad"},
     {"a": "concept", "b": "note"}),
    ("同じページが 2 つのグループ", {"index.md": "## 第一\n- [[a]]: 一つ目\n## 第二\n- [[a]]\n- [[b]]\n"},
     {"a": "concept", "b": "concept"}),
    ("索引のファイルどうしが互いを指す",
     {"indexes/p.md": "# P\n- [[indexes/q]]\n- [[a]]\n", "indexes/q.md": "# Q\n- [[indexes/p]]\n- [[indexes/q]]\n"},
     {"a": "concept"}),
    ("コードの中の wikilink と見出し（4 回目のレビューの重大 1）",
     {"index.md": "# Index\n- `[[a]]` [[b]]\n\n```\n# Fake\n- [[a]]\n```\n"}, {"a": "concept", "b": "concept"}),
    ("Setext の見出しと番号つきのリスト",
     {"index.md": "索引の表題\n==========\n\n分類\n----\n\n1. [[a]]\n2. [[b]]\n"}, {"a": "concept", "b": "concept"}),
    ("`.md` つきのリンクと見出しへのリンク（4 回目のレビューの重大 2）",
     {"index.md": "# Index\n- [[a.md]]\n- [[b#b]]\n- [[indexes/x.md]]: 拡張子つき\n", "indexes/x.md": "# X\n- [[c]]\n"},
     {"a": "concept", "b": "concept", "c": "concept"}),
    ("frontmatter の日本語のキー（4 回目のレビュー）",
     {"indexes/x.md": "---\n題名: Custom\n---\n# Heading\n- [[a]]\n"}, {"a": "concept"}),
    ("グループの要約の表示の文字（4 回目のレビューの軽微 1）",
     {"index.md": "- [[indexes/x]]: **bold** [[a|Alias]]\n", "indexes/x.md": "# X\n- [[b]]\n"},
     {"a": "concept", "b": "concept"}),
]


def make_wiki(root: Path, files: dict, pages: dict) -> None:
    (root / "SCHEMA.md").write_bytes("# スキーマ\n".encode("utf-8"))
    for rel, text in files.items():
        path = root / rel
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(text if isinstance(text, bytes) else text.encode("utf-8"))
    for slug, type_ in pages.items():
        path = root / "concepts" / f"{slug}.md"
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(page(slug, type_).encode("utf-8"))


def show_files(files: dict) -> str:
    parts = []
    for rel, text in files.items():
        shown = "（読めない）" if isinstance(text, bytes) else text.replace("\n", "⏎").replace("|", "\\|")
        parts.append(f"`{rel}`: `{shown}`")
    return "<br>".join(parts)


def run_case(files: dict, pages: dict) -> list:
    tmp = Path(tempfile.mkdtemp(prefix="nav_model_"))
    try:
        make_wiki(tmp, files, pages)
        top = build(tmp)
        titles = {g["id"]: g["title"] for g in walk(top)}
        return render(top, titles)
    finally:
        shutil.rmtree(tmp, ignore_errors=True)


def main() -> int:
    md = "--markdown" in sys.argv
    if md:
        print("| 例 | 索引 | 木（件数、「要約」、項目。→ はグループへのリンク、? は状態つきの文字） |")
        print("| --- | --- | --- |")
    for name, files, pages in CASES:
        lines = run_case(files, pages)
        if md:
            print(f"| {name} | {show_files(files)} | " + "<br>".join(lines) + " |")
        else:
            print(f"== {name}")
            print("\n".join(lines))
    return 0


if __name__ == "__main__":
    sys.exit(main())
