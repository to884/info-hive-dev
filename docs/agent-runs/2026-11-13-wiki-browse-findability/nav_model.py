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

import re
import shutil
import sys
import tempfile
import unicodedata
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
    """今の Core で 1 つ目の段を作る。

    返すのは、(索引のファイル, そのグループ) の並び（今の Core の並び）、索引にないページのグループ（0 か 1 個）、Core。
    グループは ID だけで見分ける。索引のファイルの NFC の名前では見分けない。NFC で同じになる 2 つの名前の
    索引のファイルを、今の Core は別のグループ（ディスク上の綴りのハッシュの ID）にするからである。
    """
    c = StageOneCore(core.take_snapshot(root), record=False)
    readable = [f for f in c.snapshot.by_kind("index") if f.text is not None]
    file_groups = list(zip(readable, c.nav_groups[:len(readable)]))
    for f, g in file_groups:
        assert g["id"] == "_g" + core.short_hash(f.disk_rel, 10), "ファイルのグループの並びが想定と違う"
    rest = c.nav_groups[len(readable):]
    assert len(rest) <= 1 and all(g["title"] == "索引にないページ" for g in rest)
    return file_groups, rest, c


def walk(groups):
    for g in groups:
        yield g
        yield from walk(g["children"])


def page_ids(groups) -> set:
    return {it["id"] for g in walk(groups) for it in g["items"] if it["state"] == "resolved"}


ID_RE = re.compile(r"_g[0-9a-z]+\Z")


def build(root: Path) -> list:
    file_groups, rest, c = stage_one(root)
    listed_before = page_ids([g for _f, g in file_groups])
    by_id = {g["id"]: g for _f, g in file_groups}
    index_g = next((g for f, g in file_groups if f.rel == "index.md"), None)
    for _f, g in file_groups:
        origin = "index" if g is index_g else "indexes"
        for x in walk([g]):
            x["origin"] = origin
            x.setdefault("summary", "")
        if g is index_g:
            g["title"] = "索引"                      # N2
        if not g["items"] and len(g["children"]) == 1:   # N3: 1 度だけ畳む
            child = g["children"][0]
            g["items"], g["children"] = child["items"], child["children"]
    for _f, g in file_groups:                         # N6: グループへの項目の名前は、行き先のグループの名前
        for x in walk([g]):
            for it in x["items"]:
                if it["state"] == "group":
                    it["label"] = by_id[it["group"]]["title"]
    top = []
    if index_g is not None:                           # N4
        if index_g["items"]:
            top.append({**index_g, "title": "索引", "children": []})
        top.extend(index_g["children"])
    order, summaries = [], {}                         # N5: 順と要約は、グループの ID で決める
    if index_g is not None:
        for x in walk([index_g]):
            for it in x["items"]:
                if it["state"] == "group" and it["group"] not in summaries:
                    order.append(it["group"])
                    summaries[it["group"]] = it.get("after", "")
    for _f, g in file_groups:
        if g is not index_g and g["id"] not in summaries:
            order.append(g["id"])
    for gid in order:
        by_id[gid]["summary"] = summaries.get(gid, "")
        top.append(by_id[gid])

    def only_group_items(g):
        return all(it["state"] == "group" for x in walk([g]) for it in x["items"])

    def prune(groups):                                 # N6: index.md から来たグループだけを外せる
        kept = []
        for g in groups:
            if g.get("origin") == "index" and only_group_items(g):
                continue
            g["children"] = prune(g["children"])
            kept.append(g)
        return kept

    top = prune(top)
    assert page_ids(top) == listed_before, "2 つ目の段で、索引に載ったページが変わった"
    for g in rest:                                     # N7: 今のグループと ID を使い、名前だけを変える
        g["origin"], g["summary"] = "", ""
        for sub in g["children"]:
            t = str(c.page(sub["items"][0]["id"])["meta"].get("type") or "")
            sub["title"] = TYPE_LABELS.get(t, t or "種類なし")
            sub["origin"], sub["summary"] = "", ""
        top.append(g)

    def count(g):                                      # N8
        ids = {it["id"] for it in g["items"] if it["state"] == "resolved"}
        for ch in g["children"]:
            ids |= count(ch)
        g["count"] = len(ids)
        return ids

    for g in top:
        count(g)
    check(top)
    return top


def data_groups(top: list) -> dict:
    """4.1 の data-groups。ページごとに、そのページを項目に持つグループと祖先のグループの ID。"""
    out = {}

    def rec(g, trail):
        trail = trail + [g["id"]]
        for it in g["items"]:
            if it["state"] == "resolved":
                out.setdefault(it["id"], set()).update(trail)
        for ch in g["children"]:
            rec(ch, trail)

    for g in top:
        rec(g, [])
    return out


def check(top: list) -> None:
    """2.1 の末尾の性質を確かめる。"""
    ids = [g["id"] for g in walk(top)]
    assert len(ids) == len(set(ids)), "グループの ID が重なる"
    assert all(ID_RE.match(i) for i in ids), f"ID の形が違う: {ids}"
    shown = set(ids)
    for g in walk(top):
        for it in g["items"]:
            assert it["state"] != "group" or it["group"] in shown, f"木にないグループを指す: {g['title']}"
    for pid, gids in data_groups(top).items():
        attr = " ".join(sorted(gids))
        assert set(attr.split(" ")) == gids and gids <= shown, f"data-groups を読み戻せない: {pid}"


def render(top: list) -> list:
    """木のデータ（nav.js に書くもの）を、そのまま 1 行ずつ描く。名前は項目の label を使い、引き直さない。"""
    out = []

    def rec(g, depth):
        items = []
        for it in g["items"]:
            if it["state"] == "resolved":
                items.append(it["id"].rsplit("/", 1)[-1] + (f"#{it['anchor']}" if it.get("anchor") else ""))
            elif it["state"] == "group":
                items.append("→" + it["label"])
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
    ("NFC で同じになる 2 つの索引のファイル（5 回目のレビューの重大 1）",
     {"index.md": "- [[indexes/caf\u00e9]]\n", "indexes/cafe\u0301.md": "# First\n- [[a]]\n",
      "indexes/caf\u00e9.md": "# Second\n- [[b]]\n"}, {"a": "concept", "b": "concept"}),
    ("空白を含む種類（5 回目のレビューの重大 2）", {}, {"a": "research note", "b": "concept"}),
    ("グループへの行の別名（5 回目のレビューの軽微）",
     {"index.md": "- [[a]]\n- [[indexes/x|User alias]]\n", "indexes/x.md": "---\ntitle: Custom\n---\n- [[b]]\n"},
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
        # NFC でない名前は、結合文字が見えるように、符号位置で書く
        name = rel if unicodedata.is_normalized("NFC", rel) else rel.encode("ascii", "backslashreplace").decode("ascii")
        parts.append(f"`{name}`: `{shown}`")
    return "<br>".join(parts)


def run_case(files: dict, pages: dict) -> list:
    tmp = Path(tempfile.mkdtemp(prefix="nav_model_"))
    try:
        make_wiki(tmp, files, pages)
        return render(build(tmp))
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
