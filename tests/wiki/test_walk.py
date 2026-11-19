"""wiki をたどる経路（wiki_pages.walk_markdown、walk_pages、walk_index_files、article_path）の試験。

設計は `docs/plans/wiki-walk-excluded-dirs-2026-11-11.md`（7 版目、2026年11月12日に承認）にある。試作と実測は
`docs/agent-runs/2026-11-11-wiki-walk-excluded-dirs/` の walk_v7.py と results.md にある。ADR-0029（wiki と raw の
記事にリンクを置かない）の実装で、走査はリンクに降りず、リンクの記事を読まず、拒んだものを Walk.links で返す形に
変わった（`docs/plans/wiki-links-2026-11-16.md` の「ページの走査」）。名前が . で始まる項目には、どの深さでも降りない。

- 木の表から、失敗のないときの答え（ページと索引のファイル）を、走査のコードを使わずに計算し、等しいことを確かめる。
- 0.10.1 の実装と照らす。写しを持たず、info-hive-wiki のコミット BASE_COMMIT の wiki_pages.py と wiki_lint.py を
  git から取り出して読み込む。照らすのは、リンクも、名前が . で始まる項目もない木だけである（ADR-0029 で、
  それ以外の木の答えは意図して変わった）。違ってよいのは、並びの鍵で同じになる組の中の順と、設計の 7 の表のものだけ。
- 探索: OS を呼ぶ口のすべてを差し替えて呼び出しを数え、走査が呼ぶはずの呼び出しの集合と役割を木から計算して、
  失敗のない実行で集合が等しいことを確かめる。そのうえで、呼び出しのそれぞれに失敗を 1 つずつ入れ、木と役割から
  計算した答えと等しいことを確かめる。わざと決まりを破った実装（対照）を、探索が見つけることも確かめる。
- 口の一覧: 走査の関数の構文木に、口の一覧にない入出力の呼び出しと、read_os のほかの except OSError がないこと。
- 使う側: stats、MCP の索引の印、list_index、索引の更新の失敗。
- 記事を読む口（article_path）と、link_warnings の形。

リンクを作れない環境では、その木を飛ばす。ジャンクションは Windows だけ、FIFO と名前に \\ を含むファイルは
Linux と macOS だけで作る。大文字と小文字を区別するフォルダーは、Windows で fsutil が使えるときだけ作る。

実行（Python 3.12 以上。標準ライブラリだけで動く。MCP の索引の試験は、索引の依存がなければ飛ばす）:
    python -X utf8 -B -m unittest tests/wiki/test_walk.py -v
"""
from __future__ import annotations

import ast
import contextlib
import errno
import importlib.util
import os
import shutil
import stat
import subprocess
import sys
import tempfile
import unicodedata
import unittest
from pathlib import Path, PurePath
from unittest import mock

ROOT = Path(__file__).resolve().parents[2]
WIKI_REPO = ROOT / "info-hive-wiki"
SCRIPTS = WIKI_REPO / "skills/info-hive/scripts"
sys.path.insert(0, str(SCRIPTS))

import wiki_lint  # noqa: E402
import wiki_pages  # noqa: E402
import wiki_stats  # noqa: E402
import wiki_text  # noqa: E402

NT = os.name == "nt"
# 照らす今の実装。0.10.0 から 0.10.1 までに、走査に関わるファイルは変わっていない。
BASE_COMMIT = "2756a4e"


def sort_key(rel):
    return (wiki_text.posix_rel(rel), rel)


# ---------------------------------------------------------------------------
# 木の表
# ---------------------------------------------------------------------------
#
# 値が str ならファイル、dict ならディレクトリ、タプルならリンクなど。リンクの先は、木の根（wiki の親）からの相対パス。
#   ("dlink", 先)              ディレクトリのシンボリックリンク
#   ("flink", 先)              ファイルのシンボリックリンク
#   ("broken",)                先のないシンボリックリンク
#   ("junction", 先)           ジャンクション（Windows だけ）
#   ("rawlink", 先[, "dir"])   先を、リンクのあるディレクトリからの相対パスのまま書いたリンク（解けないリンク）
#   ("fifo",)                  FIFO（Linux と macOS だけ）
#   ("hlink", 先)              ハードリンク（先と同じ実体の、ふつうのファイル。先もリンクの数が 2 になる）

NFD = unicodedata.normalize("NFD", "ガイド")
E_NFC = unicodedata.lookup("LATIN SMALL LETTER E WITH ACUTE")
E_NFD = unicodedata.normalize("NFD", E_NFC)
BACKSLASH = chr(92)

TREES = {
    "リンクを置いた木": {
        "wiki": {
            "a.md": "a", "Upper.MD": "u", ".hidden.md": "h", "index.md": "i", "SCHEMA.md": "s", "notes.txt": "n",
            "real": {"b.md": "b", "notes.txt": "n"},
            "concepts": {".NET": {"c.md": "c"}, "raw": {"cr.md": "cr"}},
            ".obsidian": {"o.md": "o"},
            "dir.md": {"in.md": "in"},
            "graph": {"README.md": "g"},
            "assets": {"x": {"as.md": "as"}},
            NFD: {NFD + ".md": "nfd"},
            "が.md": "ga", "か.md": "ka",
            "indexes": {"sources.md": "s", "Upper.MD": "u", "A.md": "a", ".hidden.md": "h", "i.md": "i",
                        "sub": {"deep.md": "d", "dir.md": {"in.md": "in"}}, "raw": {"r.md": "r"}},
            "raw": ("junction", "ext") if NT else ("dlink", "ext"),
            "dlink": ("dlink", "ext"),
            "flink.md": ("flink", "ext/c.md"),
            "broken.md": ("broken",),
            "dirlink.md": ("dlink", "ext"),
            **({"junc": ("junction", "ext")} if NT else {}),
        },
        "ext": {"c.md": "c", "deep": {"d.md": "d"}},
    },
    "indexes がシンボリックリンク": {
        "wiki": {"concepts": {"c.md": "c"}, "indexes": ("dlink", "ext")},
        "ext": {"sources.md": "s"},
    },
    "indexes がページのディレクトリを指す": {
        "wiki": {"index.md": "i", "concepts": {"c.md": "c"},
                 "indexes": ("junction", "wiki/concepts") if NT else ("dlink", "wiki/concepts")},
    },
    "indexes がファイル": {"wiki": {"indexes": "x", "a.md": "a"}},
    "indexes がハードリンクのファイル": {"wiki": {"indexes": ("hlink", "ext/file"), "a.md": "a"},
                                           "ext": {"file": "text"}},
    "空の wiki": {"wiki": {}},
    "NFC と NFD の名前": {"wiki": {E_NFC + ".md": "1", E_NFD + ".md": "2",
                                   "indexes": {E_NFC + ".md": "1", E_NFD + ".md": "2"}}},
    "解けないリンク": {
        "wiki": {"a.md": "a", "loop.md": ("rawlink", "loop.md"), "m1.md": ("rawlink", "m2.md"),
                 "m2.md": ("rawlink", "m1.md"), "sub": {"b.md": "b", "dloop": ("rawlink", "dloop", "dir")},
                 "indexes": {"ok.md": "o", "iloop.md": ("rawlink", "iloop.md")}}},
    "索引の下の、ふつうのファイルでない項目": {
        "wiki": {"index.md": "i", "real": {"r.md": "r"},
                 "indexes": {"ok.md": "o", "broken.md": ("broken",), "dirlink.md": ("dlink", "wiki/real"),
                             "dir.md": {"in.md": "i"}, **({} if NT else {"pipe.md": ("fifo",)})},
                 **({} if NT else {"pipe.md": ("fifo",)})}},
}
TREES.update({
    "ハードリンクの記事": {"wiki": {"a.md": "a", "h.md": ("hlink", "wiki/a.md"), "n.txt": "n", "hn.txt": ("hlink", "wiki/n.txt"),
                                "cache": {"t.md": ("hlink", "ext/p.md")}, "indexes": {"i.md": ("hlink", "ext/q.md")}},
                       "ext": {"p.md": "p", "q.md": "q"}},
    "README.md という名前のディレクトリのリンク": {
        "wiki": {"README.md": ("junction", "ext") if NT else ("dlink", "ext"), "a.md": "a",
                 "sub": {"README.md": ("flink", "ext/x.md")}},
        "ext": {"x.md": "x"}},
    "最上位の README.md がファイルのリンク": {"wiki": {"README.md": ("flink", "ext/x.md"), "a.md": "a"},
                                             "ext": {"x.md": "x"}},
    "最上位の README.md がハードリンク": {"wiki": {"README.md": ("hlink", "ext/x.md"), "a.md": "a"},
                                         "ext": {"x.md": "x"}},
    "名前が . で始まる項目の下": {"wiki": {".git": {"info": {"notes.md": "n"}}, "c": {".d": {"x.md": "x"}, "y.md": "y"},
                                         "indexes": {".private.md": "p", ".h": {"z.md": "z"}, "ok.md": "o"}}},
})
if NT:
    TREES.update({
        "ジャンクションと通常のディレクトリが兄弟": {
            "wiki": {"j": ("junction", "ext"), "plain": {"x.md": "x", "deep": {"y.md": "y"}}, "z.md": "z"},
            "ext": {"c.md": "c"}},
        "輪でないジャンクションの別名": {"wiki": {"a": {"x.md": "x"}, "alias": ("junction", "wiki/a")}},
        "下を指すジャンクション": {"wiki": {"a": {"b": {"c.md": "c"}, "j": ("junction", "wiki/a/b")}}},
        "循環: sub/loop と indexes が wiki を指す": {
            "wiki": {"a.md": "a", "sub": {"b.md": "b", "loop": ("junction", "wiki")}, "indexes": ("junction", "wiki")}},
        "循環: a/b/j が a を、a/me が a を指す": {
            "wiki": {"a": {"top.md": "t", "b": {"c.md": "c", "j": ("junction", "wiki/a")}, "me": ("junction", "wiki/a")}}},
        "循環: 2 つのジャンクション": {
            "wiki": {"x": {"p.md": "p", "j1": ("junction", "ext")}},
            "ext": {"q.md": "q", "j2": ("junction", "wiki/x")}},
        "循環: wiki の親を指す": {"wiki": {"a.md": "a", "up": ("junction", "")}, "side": {"s.md": "s"}},
    })
else:
    TREES["名前に区切りの文字を含む"] = {"wiki": {"a" + BACKSLASH + "b.md": "1", "a0.md": "2", "c": {"d.md": "3"}}}
    TREES["鍵が同じになる名前"] = {"wiki": {"a" + BACKSLASH + "b.md": "1", "a": {"b.md": "2"}, "a0.md": "3"}}



def plain(spec) -> bool:
    """リンクも、名前が . で始まる項目もない木か（0.10.1 の実装と照らせる木）。"""
    def walk(node):
        for name, value in node.items():
            if name.startswith(".") or isinstance(value, tuple):
                return False
            if isinstance(value, dict) and not walk(value):
                return False
        return True
    return walk(spec)


def build(base: Path, spec: dict) -> bool:
    """木をディスクの上に作る。リンクは、ふつうの項目を作り終えてから作る。作れなければ偽を返す。"""
    links = []

    def make(directory, node):
        directory.mkdir(parents=True, exist_ok=True)
        for name, value in node.items():
            path = directory / name
            if isinstance(value, dict):
                make(path, value)
            elif isinstance(value, str):
                path.write_text(value, encoding="utf-8")
            else:
                links.append((path, value))
    make(base, spec)
    for path, value in links:
        kind = value[0]
        try:
            if kind == "fifo":
                os.mkfifo(path)
            elif kind == "rawlink":
                os.symlink(value[1], path, target_is_directory=(len(value) > 2 and value[2] == "dir"))
            elif kind == "hlink":
                os.link(base / value[1], path)
            elif kind == "junction":
                target = base / value[1]
                if subprocess.run(["cmd", "/c", "mklink", "/J", str(path), str(target)],
                                  capture_output=True).returncode != 0:
                    return False
            else:
                target = base / value[1] if len(value) > 1 else base / "no-such-target"
                os.symlink(target, path, target_is_directory=(kind == "dlink"))
        except (OSError, AttributeError, NotImplementedError):
            return False

    # 表と同じ木ができたかを確かめる。ファイルシステムが名前を同じものとみなすと（macOS の APFS は、NFC と NFD だけが
    # 違う名前を、大文字と小文字だけが違う名前を区別しない設定もある）、あとから書いた項目が先の項目を上書きする。
    def same(directory, node):
        try:
            names = os.listdir(directory)
        except OSError:
            return False
        if len(names) != len(node):
            return False
        return all(same(directory / name, value) for name, value in node.items() if isinstance(value, dict))
    return same(base, spec)


def remove_tree(base: Path) -> None:
    """リンクの先を消さずに、木を消す。"""
    if not base.exists():
        return
    for directory, dirs, files in os.walk(base, topdown=True):
        for name in list(dirs) + list(files):
            p = os.path.join(directory, name)
            if os.path.islink(p) or getattr(os.lstat(p), "st_reparse_tag", 0):
                if name in dirs:
                    dirs.remove(name)
                try:
                    os.unlink(p)
                except OSError:
                    os.rmdir(p)
    shutil.rmtree(base)


def resolve(spec, parts):
    """木の根からのパスを、リンクを解いて (種類, 実体のパス) にする。種類は "dir"、"file"、"fifo"、None（ない）。"""
    node, real = spec, ()
    for part in parts:
        if not isinstance(node, dict) or part not in node:
            return None, None
        value = node[part]
        if isinstance(value, tuple):
            if value[0] in ("broken", "rawlink"):
                return None, None
            if value[0] == "hlink":
                return "file", real + (part,)
            if value[0] == "fifo":
                return "fifo", real + (part,)
            kind, real = resolve(spec, tuple(p for p in value[1].split("/") if p))
            if kind is None:
                return None, None
            node = spec
            for p in real:
                node = node[p]
        else:
            node, real = value, real + (part,)
    return ("dir" if isinstance(node, dict) else "file"), real


def node_at(spec, real):
    node = spec
    for part in real:
        node = node[part]
    return node


def link_target(spec, value):
    return resolve(spec, tuple(p for p in value[1].split("/") if p))


def hard_targets(spec):
    """ハードリンクで、リンクの数が 2 以上になるファイルの、木の根からのパスの集合（リンクの名前と先の両方）。"""
    found = set()

    def walk(node, path):
        for name, value in node.items():
            if isinstance(value, dict):
                walk(value, path + (name,))
            elif isinstance(value, tuple) and value[0] == "hlink":
                found.add(path + (name,))
                found.add(tuple(p for p in value[1].split("/") if p))
    walk(spec, ())
    return found


def link_entry_kind(value, name, top_readme=False):
    """リンクの項目（タプル）を、走査が links に入れるなら (種類,)、入れないなら None で返す（ADR-0029）。

    名前が .md で終わるリンクは、先によらず入れる。そのほかは、ディレクトリへのリンク（ジャンクションと、先が
    ディレクトリのシンボリックリンク）だけを入れる。Windows では、ディレクトリとして作ったシンボリックリンクに
    ディレクトリの属性が付くので、先のない（解けない）ものも入れる。POSIX では is_dir() が先をたどるので、先のないものは
    「ない」になり、入れない。FIFO はリンクでない。
    """
    kind = value[0]
    if kind == "fifo":
        return None
    link = "junction" if kind == "junction" else "symlink"
    if name.lower().endswith(".md") and not top_readme:
        return link
    if kind in ("junction", "dlink"):
        return link
    if kind == "rawlink" and len(value) > 2 and value[2] == "dir":
        return link if NT else None
    return None


def model(spec, start, prefix="", skip_top=False):
    """失敗のないときの (.md のふつうのファイルの相対パス, 拒んだリンクの (相対パス, 種類)) を、木の表から計算する。"""
    kind, real = resolve(spec, start)
    found, links = [], []
    if kind != "dir":
        return found, links
    hard = hard_targets(spec)

    def descend(real, pre):
        for name, value in node_at(spec, real).items():
            rel = pre + name
            if skip_top and pre == prefix and name in wiki_pages.SKIP_TOP_LEVEL_DIRS:
                continue
            if name.startswith("."):
                continue
            path = real + (name,)
            if isinstance(value, dict):
                descend(path, rel + "/")
            elif isinstance(value, str) or value[0] == "hlink":
                if name.lower().endswith(".md"):
                    if path in hard and skip_top and pre == prefix and name == "README.md":
                        continue  # 起点の直下の README.md は記事でない
                    if path in hard:
                        links.append((rel, "hardlink"))
                    else:
                        found.append(rel)
            else:
                link = link_entry_kind(value, name, top_readme=skip_top and pre == prefix and name == "README.md")
                if link is not None:
                    links.append((rel, link))
    descend(real, prefix)
    return sorted(found, key=sort_key), sorted(links, key=lambda item: sort_key(item[0]))


def model_pages(spec):
    found, links = model(spec, ("wiki",), skip_top=True)
    return [rel for rel in found if wiki_pages.is_page_path(rel)], links


def model_index(spec):
    files, links = [], []
    node = spec["wiki"]
    top = node.get("index.md")
    hard = hard_targets(spec)
    if isinstance(top, str):
        if ("wiki", "index.md") in hard:
            links.append(("index.md", "hardlink"))
        else:
            files.append("index.md")
    elif isinstance(top, tuple):
        if top[0] == "hlink":
            links.append(("index.md", "hardlink"))
        elif top[0] != "fifo":
            links.append(("index.md", "junction" if top[0] == "junction" else "symlink"))
    value = node.get("indexes")
    if isinstance(value, tuple):
        if value[0] not in ("fifo", "hlink"):  # ふつうのファイルのハードリンクは、記事でも記事までの道でもない
            return files, links + [("indexes", "junction" if value[0] == "junction" else "symlink")]
        return files, links
    below, below_links = model(spec, ("wiki", "indexes"), prefix="indexes/")
    return files + below, links + below_links


def expected_old_index(spec):
    """今（0.10.1）の index_files() の集合を、今の規則で木から計算する。新しい集合からは作らない。

    今の規則: 最上位の index.md がファイルなら、それ。そのあと、indexes を起点に rglob("*.md") が返す名前のすべて。
    rglob は、名前が合えば種類を確かめない。ふつうのディレクトリとジャンクションには降り、ディレクトリの
    シンボリックリンクには降りない。名前の合わせ方は、Windows では大文字と小文字を区別しない。
    """
    rels = []
    kind, _real = resolve(spec, ("wiki", "index.md"))
    if kind == "file":
        rels.append("index.md")
    kind, real = resolve(spec, ("wiki", "indexes"))
    if kind != "dir":
        return rels
    match = (lambda n: n.lower().endswith(".md")) if NT else (lambda n: n.endswith(".md"))

    def descend(real, pre, path):
        for name, value in node_at(spec, real).items():
            rel = pre + name
            if match(name):
                rels.append(rel)
            child = None
            if isinstance(value, dict):
                child = real + (name,)
            elif isinstance(value, tuple) and value[0] == "junction":
                target_kind, target = link_target(spec, value)
                child = target if target_kind == "dir" else None
            if child is not None and child not in path:
                descend(child, rel + "/", path + (child,))
    descend(real, "indexes/", (real,))
    return rels


def expected_calls(spec, start, prefix="", skip_top=False, top_index=False):
    """走査が呼ぶはずの口の呼び出しと、その役割を、木の表から計算する。

    戻り値は {(名前, wiki からの相対パス): 役割の集合}。役割は ("list", X)、("entry", E)、("file", X)、("top", X)
    （最上位の index.md と indexes の os.lstat()）。口は、scandir、scandir.next、項目の stat(follow_symlinks=False)
    （entry_stat）、POSIX でリンクの項目の is_dir()、os.lstat() である。
    """
    calls = {}

    def add(op, rel, role):
        calls.setdefault((op, rel), set()).add(role)

    if top_index:
        add("lstat", "index.md", ("top", "index.md"))
        add("lstat", "indexes", ("top", "indexes"))
        value = spec["wiki"].get("indexes")
        if isinstance(value, tuple) and value[0] != "hlink":
            return calls  # ディレクトリのリンクなどは、走査の起点にも渡さない
        if value is None:
            return calls
    start_rel = prefix.rstrip("/") or "."
    kind, real = resolve(spec, start)
    add("scandir", start_rel, ("list", start_rel))
    if kind != "dir":
        return calls

    def descend(real, pre):
        rel_dir = pre.rstrip("/") or "."
        add("scandir", rel_dir, ("list", rel_dir))
        add("scandir.next", rel_dir, ("list", rel_dir))
        for name, value in node_at(spec, real).items():
            rel = pre + name
            if skip_top and pre == prefix and name in wiki_pages.SKIP_TOP_LEVEL_DIRS:
                continue
            if name.startswith("."):
                continue
            add("entry_stat", rel, ("entry", rel))
            if isinstance(value, dict):
                add("lstat", rel, ("entry", rel))  # 降りる前に、リンクに替わっていないかを確かめる
                descend(real + (name,), rel + "/")
            elif isinstance(value, str) or value[0] in ("hlink", "fifo"):
                if name.lower().endswith(".md"):
                    add("lstat", rel, ("file", rel))
            elif not NT and (not name.lower().endswith(".md") or (skip_top and pre == prefix and name == "README.md")):
                # POSIX で、名前が .md でないリンク（と起点の直下の README.md のリンク）は、先がディレクトリかを見る
                add("is_dir", rel, ("entry", rel))
    descend(real, prefix)
    return calls


def answers_with_failure(answer, links, roles, behavior):
    """失敗を入れた呼び出しの役割から、ありうる答え (files, unlistable, unknown, links) を計算する。"""
    out = []
    for what, place in sorted(roles):
        def keep(rel):
            if what == "list":
                return not (place == "." or rel.startswith(place + "/"))
            return not (rel == place or rel.startswith(place + "/"))
        files = [rel for rel in answer if keep(rel)]
        kept = [item for item in links if keep(item[0])]
        if what == "list":
            notices = ([place], [])
        else:
            notices = ([], [place])
        out.append((files, [], [], kept) if behavior == "absent" else (files, notices[0], notices[1], kept))
    return out


# ---------------------------------------------------------------------------
# 探索
# ---------------------------------------------------------------------------

FAILURES = {
    "absent": lambda: FileNotFoundError(errno.ENOENT, "入れた失敗"),
    "denied": lambda: PermissionError(errno.EACCES, "入れた失敗"),
    "eio": lambda: OSError(errno.EIO, "入れた失敗"),
    "loop": (lambda: OSError(None, "入れた失敗", None, 1921)) if NT else (lambda: OSError(errno.ELOOP, "入れた失敗")),
    "ebadf": lambda: OSError(errno.EBADF, "入れた失敗"),
}
if NT:
    FAILURES["badname"] = lambda: OSError(None, "入れた失敗", None, 123)
    FAILURES["notready"] = lambda: OSError(None, "入れた失敗", None, 21)
    FAILURES["blk"] = None  # 例外ではなく、os.lstat() が S_IFBLK の成功を返す
ONLY_FOR = {"blk": ("lstat",)}
EXPECT = {"absent": "absent", "denied": "denied", "eio": "raise", "loop": "absent", "ebadf": "denied",
          "badname": "absent", "notready": "denied", "blk": "denied"}
BLOCK_DEVICE = os.stat_result((0x6000, 0, 0, 0, 0, 0, 0, 0, 0, 0))


class Injector:
    """口の呼び出しを数え、N 回目に失敗を入れる。一覧は、開くと取り出すを別々に数える（閉じるときの失敗は CPython が捨てる）。"""

    def __init__(self, root, fail_at=None, kind=None):
        self.root = os.path.abspath(str(root))
        self.fail_at, self.kind = fail_at, kind
        self.count = 0
        self.failed = None
        self.calls = []
        self.real = {"scandir": os.scandir, "lstat": os.lstat}

    def rel(self, path):
        text = os.fspath(path)
        if text == self.root:
            return "."
        if text.startswith(self.root + os.sep):
            rest = text[len(self.root) + 1:]
            return rest.replace(os.sep, "/") if NT else rest
        raise AssertionError(f"走査が、wiki の外のパスを口に渡した: {text}")

    def hit(self, name, path):
        index = self.count
        self.count += 1
        rel = self.rel(path)
        self.calls.append((name, rel))
        if index == self.fail_at:
            self.failed = (name, rel)
            if FAILURES[self.kind] is None:
                return True
            raise FAILURES[self.kind]()
        return False

    def scandir(self, path):
        self.hit("scandir", path)
        injector = self

        class Entry:
            # 走査が呼んでよい項目の口は stat(follow_symlinks=False) と is_dir() だけである。is_symlink() や
            # is_junction() を持たせないので、走査がそれらを呼ぶと AttributeError で落ちる。
            def __init__(self, entry):
                self._entry = entry
                self.name, self.path = entry.name, entry.path

            def stat(self, *, follow_symlinks=True):
                if follow_symlinks:
                    raise AssertionError("走査が、リンクをたどる DirEntry.stat() を呼んだ")
                injector.hit("entry_stat", self.path)
                return self._entry.stat(follow_symlinks=False)

            def is_dir(self, **kwargs):
                injector.hit("is_dir", self.path)
                return self._entry.is_dir(**kwargs)

        class Listing:
            def __enter__(self):
                self.it = injector.real["scandir"](path)
                self.it.__enter__()
                return self

            def __iter__(self):
                return self

            def __next__(self):
                injector.hit("scandir.next", path)
                return Entry(next(self.it))

            def __exit__(self, *exc):
                self.it.__exit__(*exc)
                return False

        return Listing()

    def lstat(self, path, *args, **kwargs):
        if self.hit("lstat", path):
            return BLOCK_DEVICE
        return self.real["lstat"](path, *args, **kwargs)

    def __enter__(self):
        os.scandir, os.lstat = self.scandir, self.lstat
        return self

    def __exit__(self, *exc):
        os.scandir, os.lstat = self.real["scandir"], self.real["lstat"]


def explore(wiki, function, answer, expected, first_only=False, links=()):
    """function(wiki) -> Walk に失敗を 1 つずつ入れ、木から計算した答えと比べる。破られた決まりの並びと、実行の数を返す。

    first_only が真なら、最初の破れで止める（対照が見つかることを確かめるときに使う）。
    """
    violations = []
    with Injector(wiki) as base_run:
        try:
            baseline = function(wiki)
        except OSError as exc:
            return [f"失敗なし: 送出した（{type(exc).__name__}）"], 0
    links = list(links)
    if [f.rel for f in baseline.files] != answer or baseline.unlistable or baseline.unknown:
        violations.append(f"失敗なし: 答えと違う {[f.rel for f in baseline.files]}")
    if list(baseline.links) != links:
        violations.append(f"失敗なし: 拒んだリンクが違う {list(baseline.links)}")
    made = set(base_run.calls)
    extra, missing = sorted(made - set(expected)), sorted(set(expected) - made)
    if extra:
        violations.append(f"失敗なし: 木から決まらない呼び出しをした {extra[:4]}")
    if missing:
        violations.append(f"失敗なし: 木から決まる呼び出しをしなかった {missing[:4]}")
    runs = 0
    for index in range(base_run.count):
        for kind in FAILURES:
            if first_only and violations:
                return violations, runs
            if kind in ONLY_FOR and base_run.calls[index][0] not in ONLY_FOR[kind]:
                continue
            runs += 1
            with Injector(wiki, index, kind) as run:
                try:
                    result, raised = function(wiki), None
                except OSError as exc:
                    result, raised = None, exc
            if run.failed is None:
                violations.append(f"{index} 回目の呼び出しに届かなかった（{kind}）")
                continue
            where = f"{run.failed[0]}({run.failed[1]}) に {kind}"
            behavior = EXPECT[kind]
            if behavior == "raise":
                if raised is None or raised.errno != errno.EIO:
                    violations.append(f"{where}: 送出しなかった")
                continue
            if raised is not None:
                violations.append(f"{where}: 送出した（{type(raised).__name__}）")
                continue
            roles = expected.get(run.failed)
            if not roles:
                violations.append(f"{where}: 木から決まらない呼び出し")
                continue
            wants = answers_with_failure(answer, links, roles, behavior)
            got = ([f.rel for f in result.files], result.unlistable, result.unknown, list(result.links))
            if got not in wants:
                violations.append(f"{where}: 答えと違う。答え {wants[0]}、走査 {got}")
    return violations, runs


@contextlib.contextmanager
def swapped(module, name, value):
    original = getattr(module, name)
    setattr(module, name, value)
    try:
        yield
    finally:
        setattr(module, name, original)


def control_swallow_all(root):
    def swallow(call, *args, **kwargs):
        try:
            return "ok", call(*args, **kwargs)
        except OSError:
            return "absent", None
    with swapped(wiki_pages, "read_os", swallow):
        return wiki_pages.walk_pages(root)


def control_silent(root):
    found = wiki_pages.walk_pages(root)
    return wiki_pages.Walk(found.files, [], [], found.links)


def control_discard_all(root):
    found = wiki_pages.walk_pages(root)
    if found.unlistable or found.unknown:
        return wiki_pages.Walk([], ["."], [], [])
    return found


def control_ignore_block_device(root):
    """os.lstat() が返した S_IFBLK の成功を、そのまま受け取る（ページを知らせなしに落とす）。"""
    with swapped(wiki_pages, "_stat_entry", lambda path: wiki_pages.read_os(os.lstat, path)):
        return wiki_pages.walk_pages(root)


def control_raise_on_unresolvable(root):
    """解けないリンクの失敗を、障害として送出する（自分を指すリンクが 1 つあるだけで止まる）。"""
    def strict(call, *args, **kwargs):
        try:
            return "ok", call(*args, **kwargs)
        except (FileNotFoundError, NotADirectoryError):
            return "absent", None
        except (PermissionError, wiki_pages.NoFileId):
            return "denied", None
    with swapped(wiki_pages, "read_os", strict):
        return wiki_pages.walk_pages(root)


def control_follow_links(root):
    """リンクを見ず、0.25 までのように、リンクの先をたどって、ジャンクションに降り、ファイルのシンボリックリンクを読む
    （ADR-0029 の前の形）。項目の属性を、リンクをたどる os.stat() で取る（POSIX でも S_IFLNK のまま残らない）。"""
    with swapped(wiki_pages, "link_kind", lambda st, nlink_known=True: None), \
            swapped(wiki_pages, "_entry_lstat", lambda entry: wiki_pages.read_os(os.stat, entry.path)), \
            swapped(wiki_pages, "_stat_entry", lambda path: wiki_pages.read_os(os.stat, path)):
        return wiki_pages.walk_pages(root)


def control_ignore_hardlinks(root):
    """ハードリンクを見ない（Windows の DirEntry.stat() の st_nlink はいつも 0 なので、一覧の情報だけで決めるのと同じ形）。"""
    real = wiki_pages.link_kind
    with swapped(wiki_pages, "link_kind", lambda st, nlink_known=True: real(st, nlink_known=False)):
        return wiki_pages.walk_pages(root)


def control_hide_links(root):
    """リンクを拒むが、知らせない（拒んだことを「ない」に変える。ADR-0029 の I4）。"""
    found = wiki_pages.walk_pages(root)
    return wiki_pages.Walk(found.files, found.unlistable, found.unknown, [])


def control_nfc_key(root):
    found = wiki_pages.walk_pages(root)
    files = sorted(found.files, key=lambda f: (unicodedata.normalize("NFC", f.rel), f.rel))
    return wiki_pages.Walk(files, found.unlistable, found.unknown, found.links)


CONTROLS = [("どの失敗も「ない」にする", control_swallow_all), ("権限を知らせずに飛ばす", control_silent),
            ("知らせがあったら全ページを捨てる", control_discard_all),
            ("解けないリンクで送出する", control_raise_on_unresolvable),
            ("リンクに降り、リンクの先を読む", control_follow_links),
            ("ハードリンクを見ない", control_ignore_hardlinks),
            ("拒んだリンクを知らせない", control_hide_links)]
if NT:
    CONTROLS += [("os.lstat() の S_IFBLK の成功を、そのまま受け取る", control_ignore_block_device)]
else:
    CONTROLS.append(("並びの鍵を NFC だけにする", control_nfc_key))


# ---------------------------------------------------------------------------
# 今（0.10.1）の実装
# ---------------------------------------------------------------------------

_OLD = {}


def old_module(name):
    """info-hive-wiki の BASE_COMMIT の scripts/<name>.py を、git から取り出して読み込む（写しを持たない）。"""
    if name in _OLD:
        return _OLD[name]
    try:
        source = subprocess.run(["git", "-C", str(WIKI_REPO), "show", f"{BASE_COMMIT}:skills/info-hive/scripts/{name}.py"],
                                capture_output=True, check=True).stdout
    except (OSError, subprocess.CalledProcessError) as exc:
        raise unittest.SkipTest(f"今の実装（{BASE_COMMIT}）を git から取り出せない: {exc}")
    text = source.decode("utf-8")
    if name == "wiki_pages":
        # 同梱した解析器（_vendor/）の置き場所だけを、本物に向ける。一時フォルダーには _vendor/ がなく、読み込みの
        # 確かめ（同梱したものが読み込まれたか）で止まるからである。走査の規則には関わらない 1 行である。
        line = 'VENDOR_DIR = Path(__file__).resolve().parent / "_vendor"'
        if text.count(line) != 1:
            raise AssertionError("今の実装の wiki_pages.py に、同梱の解析器の置き場所の行がない")
        text = text.replace(line, f"VENDOR_DIR = Path({str(SCRIPTS / '_vendor')!r})")
    folder = Path(tempfile.mkdtemp(prefix="old-wiki-"))
    path = folder / f"old_{name}.py"
    path.write_text(text, encoding="utf-8")
    spec = importlib.util.spec_from_file_location(f"old_{name}", path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    _OLD[name] = module
    return module


def old_pages(wiki):
    return [p.relative_to(wiki).as_posix() for p in old_module("wiki_pages").iter_page_files(Path(wiki))]


def old_index(wiki):
    return [p.relative_to(wiki).as_posix() for p in old_module("wiki_lint").index_files(Path(wiki))]


def new_pages(wiki):
    return [p.relative_to(wiki).as_posix() for p in wiki_pages.iter_page_files(Path(wiki))]


def new_index(wiki):
    return [p.relative_to(wiki).as_posix() for p in wiki_lint.index_files(Path(wiki))]


def same_up_to_ties(old, new, key):
    """old と new が、key で同じになる組の中の順だけ違うか（集合が同じで、各位置の鍵が同じ）。"""
    return sorted(old) == sorted(new) and len(old) == len(new) and all(key(a) == key(b) for a, b in zip(old, new))


# ---------------------------------------------------------------------------
# 試験
# ---------------------------------------------------------------------------

class TreeCase(unittest.TestCase):
    """木を作って消す土台。"""

    def setUp(self):
        self.tmp = Path(tempfile.mkdtemp(prefix="walk-"))

    def tearDown(self):
        remove_tree(self.tmp)

    def make(self, label, spec):
        base = self.tmp / f"t{abs(hash(label)) % 100000}"
        if not build(base, spec):
            return None
        return base / "wiki"


class AnswerTests(TreeCase):
    """失敗のないとき、走査の結果が木から計算した答えと等しく、今の実装と挙げた違いだけが違う。"""

    def test_trees(self):
        for label, spec in TREES.items():
            with self.subTest(tree=label):
                wiki = self.make(label, spec)
                if wiki is None:
                    self.skipTest(f"{label}: 表と同じ木を作れない（リンクを作れないか、名前を区別しないファイルシステム）")
                pages, index = wiki_pages.walk_pages(wiki), wiki_pages.walk_index_files(wiki)
                self.assertEqual(([f.rel for f in pages.files], list(pages.links)), model_pages(spec))
                self.assertEqual(([f.rel for f in index.files], list(index.links)), model_index(spec))
                self.assertEqual((pages.unlistable, pages.unknown, index.unlistable, index.unknown), ([], [], [], []))
                if not plain(spec):
                    continue  # リンクか、名前が . で始まる項目がある木の答えは、ADR-0029 で意図して変わった
                self.assertTrue(same_up_to_ties(old_pages(wiki), new_pages(wiki), wiki_text.posix_rel),
                                (old_pages(wiki), new_pages(wiki)))
                old_idx, new_idx = old_index(wiki), new_index(wiki)
                self.assertEqual(sorted(old_idx), sorted(expected_old_index(spec)))
                self.assertTrue(same_up_to_ties([r for r in old_idx if r in new_idx], [r for r in new_idx if r in old_idx],
                                                PurePath), (old_idx, new_idx))

    def test_case_sensitive_folder(self):
        """Windows で、大文字と小文字を区別するフォルダーの a.md と A.md。今の実装と同じく、両方を返す。"""
        if not NT:
            self.skipTest("Windows だけ")
        wiki = self.tmp / "cs" / "wiki"
        for folder in (wiki / "indexes", wiki / "p"):
            folder.mkdir(parents=True)
            if subprocess.run(["fsutil", "file", "setCaseSensitiveInfo", str(folder), "enable"],
                              capture_output=True).returncode != 0:
                self.skipTest("大文字と小文字を区別するフォルダーを作れない")
            (folder / "a.md").write_text("1", encoding="utf-8")
            (folder / "A.md").write_text("2", encoding="utf-8")
        self.assertEqual(sorted(new_pages(wiki)), ["p/A.md", "p/a.md"])
        self.assertEqual(sorted(new_index(wiki)), ["indexes/A.md", "indexes/a.md"])
        self.assertEqual(old_pages(wiki), new_pages(wiki))
        self.assertTrue(same_up_to_ties(old_index(wiki), new_index(wiki), PurePath))

    def test_eval_wikis(self):
        """今ある試験用の wiki で、今の実装と並びまで一致する。"""
        for wiki in sorted((WIKI_REPO / "eval").glob("**/wiki")):
            if not wiki.is_dir():
                continue
            with self.subTest(wiki=str(wiki.relative_to(WIKI_REPO))):
                self.assertEqual(new_pages(wiki), old_pages(wiki))
                self.assertEqual(new_index(wiki), [r for r in old_index(wiki) if (wiki / r).is_file()])


class ExploreTests(TreeCase):
    """失敗を入れる探索と、対照。"""

    def test_explore(self):
        total = 0
        for label, spec in TREES.items():
            wiki = self.make(label, spec)
            if wiki is None:
                with self.subTest(tree=label):
                    self.skipTest(f"{label}: 表と同じ木を作れない（リンクを作れないか、名前を区別しないファイルシステム）")
                continue
            targets = (("ページ", wiki_pages.walk_pages, model_pages(spec), expected_calls(spec, ("wiki",), "", True)),
                       ("索引", wiki_pages.walk_index_files, model_index(spec),
                        expected_calls(spec, ("wiki", "indexes"), "indexes/", False, True)))
            for name, function, (answer, links), expected in targets:
                with self.subTest(tree=label, target=name):
                    found, runs = explore(wiki, function, answer, expected, links=links)
                    total += runs
                    self.assertEqual(found, [], "\n".join(found[:5]))
        self.assertGreater(total, 500)

    def test_controls(self):
        """わざと決まりを破った実装を、探索がどれも見つける。"""
        built = {}
        for label, spec in TREES.items():
            wiki = self.make(label, spec)
            if wiki is not None:
                built[label] = (wiki, spec)
        for name, function in CONTROLS:
            with self.subTest(control=name):
                caught = False
                for wiki, spec in built.values():
                    answer, links = model_pages(spec)
                    found, _runs = explore(wiki, function, answer, expected_calls(spec, ("wiki",), "", True),
                                           first_only=True, links=links)
                    if found:
                        caught = True
                        break
                self.assertTrue(caught, f"対照「{name}」を、探索が見つけなかった")


class LinkTests(TreeCase):
    """リンクを拒むこと（ADR-0029）、記事を読む口、Windows の os.lstat() の読み替え。"""

    def test_os_lstat_rewrites(self):
        wiki = self.make("t3", {"wiki": {"a.md": "a", "locked.md": "l"}})
        real_lstat = os.lstat
        locked = str(wiki / "locked.md")

        def block(path, *args, **kwargs):
            return BLOCK_DEVICE if os.fspath(path) == locked else real_lstat(path, *args, **kwargs)
        if NT:
            with swapped(os, "lstat", block):  # 属性の取得の失敗: S_IFBLK の成功。分からない
                found = wiki_pages.walk_pages(wiki)
            self.assertEqual(([f.rel for f in found.files], found.unknown), (["a.md"], ["locked.md"]))

    def test_root_link_is_allowed(self):
        """wiki の根そのもののリンク（と祖先のリンク）は許し、降りる。"""
        spec = {"store": {"a.md": "a"}, "wiki": ("junction", "store") if NT else ("dlink", "store")}
        base = self.tmp / "rootlink"
        if not build(base, spec):
            self.skipTest("リンクを作れない")
        found = wiki_pages.walk_pages(base / "wiki")
        self.assertEqual(([f.rel for f in found.files], list(found.links)), (["a.md"], []))
        self.assertEqual(wiki_pages.article_path(base / "wiki", "a.md").state, "ok")

    def test_article_path(self):
        spec = {"wiki": {"a.md": "a", "SCHEMA.md": "s", "log.md": "l", "index.md": ("hlink", "ext/i.md"),
                         "indexes": {"x.md": "x"}, "c": {"d.md": "d"}, "f.md": ("flink", "ext/p.md"),
                         "j": ("junction", "ext") if NT else ("dlink", "ext"), ".git": {"n.md": "n"}},
                "ext": {"i.md": "i", "p.md": "p", "q.md": "q"}}
        wiki = self.make("ap", spec)
        if wiki is None:
            self.skipTest("リンクを作れない")
        ap = wiki_pages.article_path
        self.assertEqual(ap(wiki, "a.md").state, "ok")
        self.assertEqual(ap(wiki, "a.md").path, wiki / "a.md")
        self.assertEqual(ap(wiki, "SCHEMA.md").state, "ok")
        self.assertEqual(ap(wiki, "indexes/x.md").state, "ok")
        self.assertEqual(ap(wiki, "c\\d.md").state, "ok")
        self.assertEqual(ap(wiki, "index.md"), wiki_pages.ArticlePath("link", None, ("index.md", "hardlink")))
        self.assertEqual(ap(wiki, "f.md"), wiki_pages.ArticlePath("link", None, ("f.md", "symlink")))
        self.assertEqual(ap(wiki, "j/q.md").state, "link")
        self.assertEqual(ap(wiki, "j/q.md").link[0], "j")
        self.assertEqual(ap(wiki, "none.md").state, "absent")
        self.assertEqual(ap(wiki, "c").state, "not_article")
        self.assertEqual(ap(wiki, ".git/n.md").state, "not_article")
        self.assertEqual(ap(wiki, "raw/r.md").state, "not_article")
        self.assertEqual(ap(wiki, "README.md").state, "not_article")

    def test_link_warnings(self):
        spec = {"wiki": {"a.md": "a", "h.md": ("hlink", "wiki/a.md"), "index.md": "i",
                         "indexes": ("junction", "ext") if NT else ("dlink", "ext")}, "ext": {"s.md": "s"}}
        wiki = self.make("lw", spec)
        if wiki is None:
            self.skipTest("リンクを作れない")
        pages, index = wiki_pages.walk_pages(wiki), wiki_pages.walk_index_files(wiki)
        warnings = wiki_pages.link_warnings(pages, index, pages)
        self.assertEqual(warnings, [{"path": "a.md", "kind": "hardlink"}, {"path": "h.md", "kind": "hardlink"},
                                    {"path": "indexes", "kind": "junction" if NT else "symlink"}])

    @unittest.skipUnless(NT, "Windows だけ")
    def test_win_file_id(self):
        wiki = self.make("t4", {"wiki": {"sub": {"loop": ("junction", "wiki")}}})
        if wiki is None:
            self.skipTest("ジャンクションを作れない")
        self.assertEqual(wiki_pages.win_file_id(wiki), wiki_pages.win_file_id(wiki / "sub" / "loop"))
        self.assertNotEqual(wiki_pages.win_file_id(wiki), wiki_pages.win_file_id(wiki / "sub"))
        with self.assertRaises(FileNotFoundError):
            wiki_pages.win_file_id(wiki / "none")


class PortTests(unittest.TestCase):
    """走査の関数の構文木に、口の一覧にない入出力の呼び出しと、read_os のほかの except OSError がない。"""

    FUNCTIONS = ("read_os", "_stat_entry", "_list_dir", "_entry_lstat", "_link_is_dir",
                 "walk_markdown", "walk_pages", "walk_index_files", "article_path")
    # 走査の関数が参照してよい os の名前（口と、OS を呼ばない文字列の操作）
    ALLOWED_OS = {"os.scandir", "os.lstat", "os.fspath", "os.path.join"}
    FORBIDDEN_NAMES = {"open", "walk", "isfile", "isdir", "exists", "realpath", "samefile", "rglob", "glob",
                       "iterdir", "resolve", "is_file", "read_text", "read_bytes", "is_symlink", "is_junction"}

    def violations(self, source):
        tree = ast.parse(source)
        found = []
        functions = {node.name: node for node in tree.body if isinstance(node, ast.FunctionDef)}
        # 走査の関数から、名前で呼ぶか参照するモジュールの関数も、たどって確かめる（補助の関数の中の入出力を見逃さない）
        names, queue = [], list(self.FUNCTIONS)
        while queue:
            name = queue.pop(0)
            if name in names:
                continue
            self.assertIn(name, functions)
            names.append(name)
            for node in ast.walk(functions[name]):
                if isinstance(node, ast.Name) and node.id in functions and node.id not in names:
                    queue.append(node.id)
        for name in names:
            for node in ast.walk(functions[name]):
                if isinstance(node, ast.Attribute) and ast.unparse(node.value) in ("os", "os.path"):
                    ref = ast.unparse(node)
                    if ref != "os.path" and ref not in self.ALLOWED_OS:
                        found.append(f"{name}: {ref}")
                if isinstance(node, ast.Call):
                    callee = node.func
                    called = callee.attr if isinstance(callee, ast.Attribute) else getattr(callee, "id", None)
                    if called in self.FORBIDDEN_NAMES:
                        found.append(f"{name}: {called}()")
                if isinstance(node, ast.ExceptHandler) and name != "read_os":
                    caught = ast.unparse(node.type) if node.type is not None else "（すべて）"
                    found.append(f"{name}: except {caught}")
        return found

    def test_ports(self):
        source = (SCRIPTS / "wiki_pages.py").read_text(encoding="utf-8")
        self.assertEqual(self.violations(source), [])

    def test_check_finds_a_planted_violation(self):
        source = (SCRIPTS / "wiki_pages.py").read_text(encoding="utf-8")
        planted = source.replace("    files, unlistable, unknown, links = [], [], [], []\n",
                                 "    files, unlistable, unknown, links = [], [], [], []\n    os.path.isfile(start)\n", 1)
        self.assertNotEqual(planted, source)
        self.assertIn("walk_markdown: isfile()", self.violations(planted))
        planted = source.replace("    files, unlistable, unknown, links = [], [], [], []\n",
                                 "    files, unlistable, unknown, links = [], [], [], []\n    os.listdir(start)\n", 1)
        self.assertIn("walk_markdown: os.listdir", self.violations(planted))
        planted = source.replace("    files, unlistable, unknown, links = [], [], [], []\n",
                                 "    files, unlistable, unknown, links = [], [], [], []\n    _extra_listing(start)\n", 1)
        planted += "\n\ndef _extra_listing(start):\n    return os.listdir(start)\n"
        self.assertIn("_extra_listing: os.listdir", self.violations(planted))
        planted = source.replace("        state, entries = read_os(_list_dir, directory)\n",
                                 "        try:\n            entries = _list_dir(directory)\n        except OSError:\n"
                                 "            continue\n        state = \"ok\"\n", 1)
        self.assertNotEqual(planted, source)
        self.assertIn("walk_markdown: except OSError", self.violations(planted))


class UseTests(TreeCase):
    """使う側（stats、MCP の索引の印、list_index、索引の更新の失敗）。"""

    def wiki_with_raw(self):
        spec = {"wiki": {"index.md": "# 索引\n\n- [[a]]\n", "a.md": "---\ntype: concept\n---\n# a\n[[b]]\n",
                         "b.md": "---\ntype: concept\n---\n# b\n[[a]]\n",
                         "raw": {"r.md": "raw"}, "assets": {"x.md": "x"}, "indexes": {"concepts.md": "# c\n",
                                                                                     "sub": {"dir.md": {}}}}}
        wiki = self.make("use", spec)
        (wiki / "indexes" / "sub" / "dir.md").mkdir(parents=True, exist_ok=True)
        return wiki

    def test_stats_does_not_touch_excluded(self):
        wiki = self.wiki_with_raw()
        # 本文を解析する統計では同梱パーサーを使う。wikiのI/Oだけを監視する前に初期化を済ませる。
        # 走査だけで初期化しないことはVendoredParserTestsのfreshプロセスの試験で確認する。
        wiki_pages.new_parser()
        with Injector(wiki) as run:
            result = wiki_stats.compute_stats(wiki)
        # 除く名前の下には、口のどれも呼ばない。indexes は、名前の項目への os.lstat() だけ。
        touched = [(op, rel) for op, rel in run.calls if rel.split("/")[0] in wiki_pages.SKIP_TOP_LEVEL_DIRS]
        touched = [(op, rel) for op, rel in touched if (op, rel) != ("lstat", "indexes")]
        self.assertEqual(touched, [])
        self.assertEqual(result["pages"], 2)
        self.assertEqual(result["index_lines"], 4)
        self.assertEqual([a["code"] for a in result["advice"]], ["flat"])

    def test_stats_ties_do_not_depend_on_listing_order(self):
        spec = {"wiki": {f"p{i}.md": f"---\ntype: t{i % 2}\n---\n[[h{i}]]\n" for i in range(12)}}
        wiki = self.make("ties", spec)
        first = wiki_stats.compute_stats(wiki)
        real = os.scandir

        def reversed_scandir(path):
            class Listing:
                def __enter__(self):
                    self.it = real(path)
                    return iter(sorted(self.it.__enter__(), key=lambda e: e.name, reverse=True))

                def __exit__(self, *exc):
                    return self.it.__exit__(*exc)
            return Listing()
        with swapped(os, "scandir", reversed_scandir):
            second = wiki_stats.compute_stats(wiki)
        for key in ("most_linked", "pages_by_type", "pages_by_dir"):
            self.assertEqual(first[key], second[key])
        self.assertEqual([h["slug"] for h in first["most_linked"]], [f"h{i}" for i in sorted(range(12), key=str)][:10])

    def test_signature_and_list_index(self):
        try:
            import wiki_index
        except (ImportError, SystemExit) as exc:
            self.skipTest(f"索引の依存がない: {exc}")
        wiki = self.wiki_with_raw()
        before = wiki_index.stat_signature(wiki)
        (wiki / "raw" / "r.md").write_text("changed", encoding="utf-8")
        self.assertEqual(wiki_index.stat_signature(wiki), before)
        (wiki / "a.md").write_text("---\ntype: concept\n---\n# a changed\n", encoding="utf-8")
        self.assertNotEqual(wiki_index.stat_signature(wiki), before)
        listed = wiki_index.list_index(wiki)
        self.assertEqual([f["name"] for f in listed["indexes"]], ["concepts.md"])

    def test_refresh_keeps_rows_on_eio(self):
        """索引を作ったあとで、たどる途中に EIO が起きると、refresh() は失敗し、索引の行は 1 つも消えない。"""
        try:
            import numpy  # noqa: F401
            import tantivy  # noqa: F401
            import usearch  # noqa: F401
            import wiki_index
        except (ImportError, SystemExit) as exc:
            self.skipTest(f"索引の依存がない: {exc}")
        wiki = self.wiki_with_raw()
        with mock.patch.dict(os.environ, {"INFO_HIVE_DATA_DIR": str(self.tmp / "data")}):
            index = wiki_index.WikiIndex(wiki)
            try:
                index.refresh()
                before = dict(index.collection.hashes())
                self.assertTrue(before)
                (wiki / "a.md").write_text("---\ntype: concept\n---\n# a changed\n", encoding="utf-8")

                scandir = os.scandir

                def broken(path):
                    if path in (wiki, os.fspath(wiki)):
                        raise OSError(errno.EIO, "入れた失敗")
                    return scandir(path)

                with swapped(os, "scandir", broken):
                    with self.assertRaisesRegex(OSError, "入れた失敗"):
                        index.refresh()
                self.assertEqual(dict(index.collection.hashes()), before)
                index.refresh()  # 障害がなくなると、今までどおり動く
                self.assertNotEqual(dict(index.collection.hashes()), before)
            finally:
                index.close()

    def test_list_index_upper_extension(self):
        """一覧に出す Upper.MD を、名前で渡すと、そのファイルを返す（.md に置き換えない）。"""
        try:
            import wiki_index
        except (ImportError, SystemExit) as exc:
            self.skipTest(f"索引の依存がない: {exc}")
        wiki = self.make("upper", {"wiki": {"indexes": {"Upper.MD": "UPPER", "Upper.md": "lower"}}})
        if wiki is None:
            self.skipTest("大文字と小文字を区別しないファイルシステム")
        self.assertEqual([f["name"] for f in wiki_index.list_index(wiki)["indexes"]], ["Upper.MD", "Upper.md"])
        self.assertEqual(wiki_index.list_index(wiki, "Upper.MD")["content"], "UPPER")
        self.assertEqual(wiki_index.list_index(wiki, "Upper.md")["content"], "lower")
        self.assertEqual(wiki_index.list_index(wiki, "Upper")["content"], "lower")

    def test_signature_raises_on_eio(self):
        try:
            import wiki_index
        except (ImportError, SystemExit) as exc:
            self.skipTest(f"索引の依存がない: {exc}")
        wiki = self.wiki_with_raw()
        real = os.scandir

        def broken(path):
            raise OSError(errno.EIO, "入れた失敗")
        with swapped(os, "scandir", broken):
            with self.assertRaises(OSError):
                wiki_index.stat_signature(wiki)
        self.assertIs(os.scandir, real)


if __name__ == "__main__":
    unittest.main()
