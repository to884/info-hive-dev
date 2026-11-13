"""browse の索引の木の規則（設計書 2.1 の N1〜N8）の参照の実装。

設計書の「当てはめの例」の表は、この実装の出力から写す。手で書いた期待は使わない。
実装（wiki_browse_core.py）の試験は、このファイルの CASES を入力にし、同じ木になることを確かめる。

使い方: python -X utf8 nav_model.py            # すべての例の木を出す
        python -X utf8 nav_model.py --markdown # 設計書の表の行を出す
"""
from __future__ import annotations

import re
import sys

WIKILINK = re.compile(r"\[\[([^\]|#]+)(?:#[^\]|]*)?(?:\|([^\]]+))?\]\]")
TYPE_LABELS = {"source": "ソース", "entity": "エンティティ", "concept": "コンセプト", "synthesis": "シンセシス"}


class Group:
    _n = 0

    def __init__(self, title: str, gid: "str | None" = None, origin: str = "", kind: str = "heading"):
        Group._n += 1
        self.id = gid or f"_g{Group._n}"
        self.title = title
        self.origin = origin   # どの索引のファイルから来たか（"index.md" か "indexes/x.md"）
        self.kind = kind       # "file"（索引のファイルのグループ）か "heading"（見出しのグループ）か "unlisted"
        self.items: list = []  # ("page", slug) / ("group", ref, summary) / ("unresolved", text)
        self.children: list = []
        self.summary = ""
        self.count = 0


def split_fm(text: str) -> tuple:
    m = re.match(r"---\n(.*?)\n---\n?", text, flags=re.S)
    if not m:
        return {}, text
    meta = {}
    for line in m.group(1).splitlines():
        k, _, v = line.partition(":")
        if k.strip() and v.strip():
            meta[k.strip()] = v.strip().strip('"')
    return meta, text[m.end():]


def after_link(text: str, end: int) -> str:
    """4.2 の 2 と同じ取り方: wikilink より後ろの文字から、先頭の区切りと空白を除く。"""
    return text[end:].strip().lstrip(":：—–-").strip()


def build_file(rel: str, text: str, pages: set, readable_indexes: set) -> Group:
    """N1、N2: 索引のファイル 1 つの木を、今の Core._nav() と同じに組む。"""
    meta, body = split_fm(text)
    lines = body.splitlines()
    first_heading = next((m.group(2).strip() for ln in lines if (m := re.match(r"(#{1,6})\s+(.*)", ln))), None)
    if rel == "index.md":
        name = "索引"
    else:
        name = meta.get("title") or first_heading or rel.rsplit("/", 1)[-1][:-3]
    top = Group(name, f"_f:{rel}", rel, "file")
    stack = [(0, top)]
    for ln in lines:
        hm = re.match(r"(#{1,6})\s+(.*)", ln)
        if hm:
            level = len(hm.group(1))
            while len(stack) > 1 and stack[-1][0] >= level:
                stack.pop()
            g = Group(hm.group(2).strip(), None, rel, "heading")
            stack[-1][1].children.append(g)
            stack.append((level, g))
            continue
        im = re.match(r"\s*[-*+]\s+(.*)", ln)
        if not im:
            continue
        lm = WIKILINK.search(im.group(1))
        if not lm:
            continue
        target = lm.group(1).strip()
        if target.startswith("indexes/") and target + ".md" in readable_indexes:
            stack[-1][1].items.append(("group", target + ".md", after_link(im.group(1), lm.end())))
        elif target in pages:
            stack[-1][1].items.append(("page", target))
        else:
            stack[-1][1].items.append(("unresolved", lm.group(2) or target))
    return top


def fold_once(g: Group) -> None:
    """N3: ファイルのグループが項目を持たず、子のグループを 1 つだけ持つなら、1 度だけ、その子と 1 つにする。"""
    if not g.items and len(g.children) == 1:
        child = g.children[0]
        g.items, g.children = child.items, child.children


def walk(groups):
    for g in groups:
        yield g
        yield from walk(g.children)


def only_group_items(g: Group) -> bool:
    return all(it[0] == "group" for x in walk([g]) for it in x.items)


def build(index_files: dict, pages: dict) -> list:
    """index_files は {相対パス: 文字 | None（読めない）}、pages は {スラッグ: type}。木のいちばん上のグループの並びを返す。"""
    Group._n = 0
    readable = {rel for rel, t in index_files.items() if t is not None and rel.startswith("indexes/")}
    files = {}
    for rel in sorted(index_files, key=lambda r: (r != "index.md", r)):
        if index_files[rel] is None:
            continue   # 読めない索引のファイルは、グループを作らない（診断に挙げる）
        g = build_file(rel, index_files[rel], set(pages), readable)
        fold_once(g)
        files[rel] = g
    top = []
    index_top = files.get("index.md")
    if index_top is not None:
        # N4: index.md のグループはいちばん上に置かない。自身の項目は「索引」のグループにまとめて先に置く
        if index_top.items:
            own = Group("索引", index_top.id, "index.md", "index-own")
            own.items = index_top.items
            top.append(own)
        top.extend(index_top.children)
    # N5: indexes/ のファイルのグループの順と要約
    order, summaries = [], {}
    if index_top is not None:
        for g in walk([index_top]):
            for it in g.items:
                if it[0] == "group" and it[1] not in summaries:
                    order.append(it[1])
                    summaries[it[1]] = it[2]
    for rel in sorted(files):
        if rel != "index.md" and rel not in order:
            order.append(rel)
    for rel in order:
        files[rel].summary = summaries.get(rel, "")
        top.append(files[rel])
    # N6: index.md から来たグループ（どこからも指せない）のうち、グループへの項目しか持たないものは出さない
    def prune(groups):
        kept = []
        for g in groups:
            if g.origin == "index.md" and only_group_items(g):
                continue
            g.children = prune(g.children)
            kept.append(g)
        return kept
    top = prune(top)
    # N7: 索引にないページ
    listed = {it[1] for g in walk(top) for it in g.items if it[0] == "page"}
    rest = sorted(s for s in pages if s not in listed)
    if rest:
        u = Group("索引にないページ", None, "", "unlisted")
        by_type = {}
        for s in rest:
            by_type.setdefault(pages[s] or "", []).append(s)
        for t in sorted(by_type):
            sub = Group(TYPE_LABELS.get(t, t or "種類なし"), None, "", "unlisted")
            sub.items = [("page", s) for s in by_type[t]]
            u.children.append(sub)
        top.append(u)
    # N8: 件数
    def count(g):
        ids = {it[1] for it in g.items if it[0] == "page"}
        for c in g.children:
            ids |= count(c)
        g.count = len(ids)
        return ids
    for g in top:
        count(g)
    check(top, files)
    return top


def check(top: list, files: dict) -> None:
    """組み終えた木の性質（設計書 2.1 の末尾）。グループへの項目は、どれも木にあるグループを指す。"""
    ids = {g.id for g in walk(top)}
    for g in walk(top):
        for it in g.items:
            if it[0] == "group":
                assert files[it[1]].id in ids, f"木にないグループを指す: {g.title} → {it[1]}"


def render(top: list) -> list:
    out = []

    def rec(g, depth):
        items = []
        for it in g.items:
            if it[0] == "page":
                items.append(it[1])
            elif it[0] == "group":
                items.append("→" + it[1][len("indexes/"):-3])
            else:
                items.append("?" + it[1])
        line = "  " * depth + f"{g.title}（{g.count}）"
        if g.summary:
            line += f"「{g.summary}」"
        if items:
            line += ": " + "、".join(items)
        out.append(line)
        for c in g.children:
            rec(c, depth + 1)

    for g in top:
        rec(g, 0)
    return out


# 設計書の当てはめの例と、レビューの反例。pages の値は type。
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
    ("読めない索引のファイル", {"index.md": "# 索引\n- [[indexes/broken]]\n- [[a]]\n", "indexes/broken.md": None},
     {"a": "concept", "b": "note"}),
    ("同じページが 2 つのグループ", {"index.md": "## 第一\n- [[a]]: 一つ目\n## 第二\n- [[a]]\n- [[b]]\n"},
     {"a": "concept", "b": "concept"}),
    ("索引のファイルどうしが互いを指す",
     {"indexes/p.md": "# P\n- [[indexes/q]]\n- [[a]]\n", "indexes/q.md": "# Q\n- [[indexes/p]]\n- [[indexes/q]]\n"},
     {"a": "concept"}),
]


def index_md(files: dict) -> str:
    parts = []
    for rel, text in files.items():
        shown = "（読めない）" if text is None else text.replace("\n", "⏎")
        parts.append(f"`{rel}`: `{shown}`")
    return "<br>".join(parts)


def main() -> int:
    md = "--markdown" in sys.argv
    if md:
        print("| 例 | 索引 | 木（件数、「要約」、項目。→ はグループへのリンク、? は状態つきの文字） |")
        print("| --- | --- | --- |")
    for name, files, pages in CASES:
        lines = render(build(files, pages))
        if md:
            print(f"| {name} | {index_md(files)} | " + "<br>".join(l.replace("  ", "　") for l in lines) + " |")
        else:
            print(f"== {name}")
            print("\n".join(lines))
    return 0


if __name__ == "__main__":
    sys.exit(main())
