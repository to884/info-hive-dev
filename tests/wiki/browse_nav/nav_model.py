"""browse の索引の木の規則（設計書 2.1）の参照の実装。

1 つ目の段（N1。索引の解析、項目の決め方、リンクの解決、グループの ID）は、今の中核の
`Core._nav()` をそのまま使う。設計は 1 つ目の段を変えないので、別に書き直すと、コードの中の
`[[…]]`、Setext の見出し、`[[a.md]]` のようなリンクで、今の実装と食い違う（4 回目のレビュー）。
この参照の実装が持つのは、新しく足す 2 つ目の段（N2 の `index.md` の名前、N3〜N8）と、グループの
要約（N5。4.2 の 2 と同じ取り方）だけである。

設計書の「当てはめの例」の表は、この実装の出力から写す。手で書いた期待は使わない。
実装（wiki_browse_core.py）の試験は、このファイルの CASES を入力にし、同じ木になることを確かめる。

使い方（info-hive-dev のルートで）:
  uv run --with pyyaml==6.0.3 python -X utf8 -B tests/wiki/browse_nav/nav_model.py [--markdown]
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
sys.path.insert(0, str(HERE))

import core_before as core  # noqa: E402  書き換える前の中核（9 節）
import wiki_pages  # noqa: E402

TYPE_LABELS = {"source": "ソース", "entity": "エンティティ", "concept": "コンセプト", "synthesis": "シンセシス"}
SEPARATORS = ":：—–-"


class StageOneCore(core.Core):
    """今の Core に、2 つの違いだけを持たせたもの。

    - 索引のファイルのグループの ID を、`_gf` と索引のファイルの並びの番号にする（設計 2.2）。今の ID は
      ディスク上の綴りの SHA-256 の先頭 10 桁で、重なりうる（6 回目のレビューの A）。
    - 項目に、4.2 の 2 の取り方で、最初の wikilink より後ろの表示の文字を足す。
    """

    def _nav(self):
        # 今の _nav() は、索引のファイルのグループの ID を "_g" + short_hash(disk_rel, 10) で作る。
        # その 2 か所だけを、並びの番号に差し替えて呼ぶ。ほかの short_hash の呼び出し（出力の名前）は桁が違う。
        # 番号は、グループを作る（読めて解釈できた）索引のファイルの並びで振る（設計の 2.2。実装の段で直した）。
        # 書き換える前の中核は、解釈できたファイルだけについて、索引のファイルの並びの順に ID を求めるので、
        # 初めて求められた順に番号を振れば、その並びの番号になる。
        index_disks = {f.disk_rel for f in self.snapshot.by_kind("index")}
        assigned = {}
        original = core.short_hash

        def file_id(text, digits=8):
            if digits == 10 and text in index_disks:
                if text not in assigned:
                    assigned[text] = f"f{len(assigned)}"
                return assigned[text]
            return original(text, digits)

        core.short_hash = file_id
        try:
            super()._nav()
        finally:
            core.short_hash = original

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
            # 表示の文字は NFC で書く（設計の 5.1）。実装と同じにそろえる
            return unicodedata.normalize("NFC", text.strip().lstrip(SEPARATORS).strip())
    return ""


def stage_one(root: Path) -> tuple:
    """今の Core で 1 つ目の段を作る。

    返すのは、(索引のファイル, そのグループ) の並び（今の Core の並び）、索引にないページのグループ（0 か 1 個）、Core。
    グループは ID だけで見分ける。索引のファイルの NFC の名前では見分けない。NFC で同じになる 2 つの名前の
    索引のファイルを、今の Core は別のグループ（ディスク上の綴りのハッシュの ID）にするからである。
    """
    c = StageOneCore(core.take_snapshot(root))
    # 読めない索引と、解釈できない索引（構造の直しのあと）はグループを作らず、番号も数えない
    failed = {rel for kind, rel in c.parse_failures if kind == "index"}
    readable = [f for f in c.snapshot.by_kind("index") if f.text is not None and f.rel not in failed]
    order = {f.disk_rel: k for k, f in enumerate(readable)}
    file_groups = list(zip(readable, c.nav_groups[:len(readable)]))
    for f, g in file_groups:
        assert g["id"] == f"_gf{order[f.disk_rel]}", "ファイルのグループの並びが想定と違う"
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
            g["title"] = "Index"                      # N2
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
            top.append({**index_g, "title": "Index", "children": []})
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
        g["title"] = "Index にないページ"             # 画面の名前（左のペインの木の設計の 8 節）
        g["origin"], g["summary"] = "", ""
        for sub in g["children"]:
            t = str(c.page(sub["items"][0]["id"])["meta"].get("type") or "")
            sub["title"] = TYPE_LABELS.get(t, t or "種類なし")
            sub["origin"], sub["summary"] = "", ""
        top.append(g)
    tag_stage(top, c)                                  # N9: 件数（N8）より前に当てる

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


NO_TAG = "タグなし"


def first_tag(c, pid: str) -> "str | None":
    """ページの最初のタグ（タグでまとめる設計の N9-2）。frontmatter の読み方（ref_values と NFC）だけを共有する。"""
    tags = [unicodedata.normalize("NFC", t) for t in wiki_pages.ref_values(c.page(pid)["meta"].get("tags"))]
    return tags[0] if tags else None


def tag_stage(top: list, c) -> None:
    """3 つ目の段 N9。ページの項目を持つグループごとに、ページの項目を最初のタグのグループに移す。

    ID は `_gt` と、木を深さ優先でたどって（親、子の順）タグのグループを作った順の番号。
    """
    before = {g["id"]: [it["id"] for it in g["items"] if it["state"] == "resolved"] for g in walk(top)}
    listed = page_ids(top)
    counter = [0]

    def apply(g):
        original_children = g["children"]
        pages = [it for it in g["items"] if it["state"] == "resolved"]
        if pages:
            buckets, order = {}, []
            for it in pages:
                key = first_tag(c, it["id"])
                if key not in buckets:
                    buckets[key] = []
                    order.append(key)
                buckets[key].append(it)
            keys = [k for k in order if k is not None] + ([None] if None in buckets else [])
            made = []
            for k in keys:
                counter[0] += 1
                made.append({"id": f"_gt{counter[0]}", "title": NO_TAG if k is None else k, "summary": "",
                             "origin": "tag", "items": buckets[k], "children": []})
            g["items"] = [it for it in g["items"] if it["state"] != "resolved"]
            g["children"] = made + original_children
        for ch in original_children:
            apply(ch)

    for g in top:
        apply(g)
    # 2.4 の 3 つの性質
    assert page_ids(top) == listed, "N9 で、木に載ったページが変わった"
    by_id = {g["id"]: g for g in walk(top)}
    for gid, pids in before.items():
        g = by_id[gid]
        assert not any(it["state"] == "resolved" for it in g["items"]), f"N9 のあとも、ページの項目が残る: {gid}"
        holders = {}
        for ch in g["children"]:
            if ch.get("origin") == "tag":
                for pid in {it["id"] for it in ch["items"]}:
                    holders.setdefault(pid, []).append(ch["title"])
        for pid in set(pids):
            assert len(holders.get(pid, [])) == 1, f"ページがちょうど 1 つのタグのグループにない: {pid}"
            assert holders[pid][0] == (first_tag(c, pid) or NO_TAG), f"タグのグループの名前が違う: {pid}"
    for g in walk(top):
        if g.get("origin") == "tag":
            assert not g["children"] and all(it["state"] == "resolved" for it in g["items"]), "タグのグループの形が違う"


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
    titles = {g["id"]: g["title"] for g in walk(top)}
    for g in walk(top):
        for it in g["items"]:
            assert it["state"] != "group" or it["label"] == titles[it["group"]], f"label が行き先の名前と違う: {it}"


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


def page(slug: str, spec, title: str = "") -> str:
    """ページの本文。spec は種類の文字か、(種類, frontmatter の tags の行) の組。tags の行は書いたまま入れる。"""
    type_, tags_line = (spec, None) if isinstance(spec, str) else spec
    extra = f"{tags_line}\n" if tags_line is not None else ""
    return f'---\ntype: "{type_}"\ntitle: "{title or slug}"\n{extra}---\n\n# {title or slug}\n\n本文。\n'


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
    ("SHA-256 の先頭 10 桁が同じ 2 つの索引のファイル（6 回目のレビューの A）",
     {"indexes/probe-910039.md": "# A\n- [[a]]\n", "indexes/probe-1542287.md": "# B\n- [[b]]\n"},
     {"a": "concept", "b": "concept"}),
    ("グループへの行の別名（5 回目のレビューの軽微）",
     {"index.md": "- [[a]]\n- [[indexes/x|User alias]]\n", "indexes/x.md": "---\ntitle: Custom\n---\n- [[b]]\n"},
     {"a": "concept", "b": "concept"}),
    # タグでまとめる設計（2026年11月16日）の 2.5 の例。`# Wiki` の h1 は N3 で畳まれ、`##` の見出しが最上位に並ぶ
    ("タグ: 基本",
     {"index.md": "# Wiki\n## コンセプト\n- [[a]]\n- [[b]]\n- [[c]]\n- [[d]]\n## ソース\n- [[s]]\n"},
     {"a": ("concept", "tags: [検索, bm25]"), "b": ("concept", "tags: [取り込み]"), "c": "concept",
      "d": ("concept", "tags: 検索"), "s": "source"}),
    ("タグ: 項目と見出しの子",
     {"index.md": "# Wiki\n## 章\n- [[a]]\n- [[nope]]\n### 節\n- [[b]]\n## 付録\n- [[c]]\n"},
     {"a": ("concept", "tags: [x]"), "b": ("concept", "tags: [y]"), "c": "concept"}),
    ("タグ: グループへの項目", {"index.md": "- [[a]]\n- [[indexes/x]]\n", "indexes/x.md": "# X\n- [[b]]\n"},
     {"a": "concept", "b": ("concept", "tags: [t]")}),
    ("タグ: 同じページが 2 つのグループ",
     {"index.md": "# Wiki\n## 第一\n- [[a]]\n## 第二\n- [[a]]\n- [[b]]\n"},
     {"a": ("concept", "tags: [t]"), "b": "concept"}),
    ("タグ: 同じグループに同じページが 2 回",
     {"index.md": "# Wiki\n## G\n- [[a]]\n- [[a#a]]\n## H\n- [[b]]\n"},
     {"a": ("concept", "tags: [t]"), "b": "concept"}),
    ("タグ: 索引にないページ", {}, {"a": ("concept", "tags: [t]"), "b": "concept", "c": ("source", "tags: [t]")}),
    ("タグ: NFC で同じになるタグ", {"index.md": "# Wiki\n## G\n- [[a]]\n- [[b]]\n## H\n- [[c]]\n"},
     {"a": ("concept", "tags: [cafe\u0301]"), "b": ("concept", "tags: [caf\u00e9]"), "c": "concept"}),
    ("タグ: 大文字と小文字", {"index.md": "# Wiki\n## G\n- [[a]]\n- [[b]]\n## H\n- [[c]]\n"},
     {"a": ("concept", "tags: [Windows]"), "b": ("concept", "tags: [windows]"), "c": "concept"}),
    ("タグ: 「タグなし」という値のタグ", {"index.md": "# Wiki\n## G\n- [[a]]\n- [[b]]\n## H\n- [[c]]\n"},
     {"a": ("concept", "tags: [タグなし]"), "b": "concept", "c": "concept"}),
    ("タグ: 値のない tags と空の要素", {"index.md": "# Wiki\n## G\n- [[a]]\n- [[b]]\n- [[c]]\n## H\n- [[d]]\n"},
     {"a": ("concept", "tags:"), "b": ("concept", 'tags: ["", "  ", t]'), "c": ("concept", "tags: []"),
      "d": "concept"}),
    ("タグ: 空白と記号を含むタグ", {"index.md": "# Wiki\n## G\n- [[a]]\n## H\n- [[b]]\n"},
     {"a": ("concept", 'tags: ["research note <b>\\"x\\""]'), "b": "concept"}),
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
