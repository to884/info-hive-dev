"""wiki をたどる経路（wiki_pages.walk_markdown、walk_pages、walk_index_files。wiki 0.10.2）の試験。

設計は `docs/plans/wiki-walk-excluded-dirs-2026-11-11.md`（7 版目、2026年11月12日に承認）にある。試作と実測は
`docs/agent-runs/2026-11-11-wiki-walk-excluded-dirs/` の walk_v7.py と results.md にある。

- 木の表から、失敗のないときの答え（ページと索引のファイル）を、走査のコードを使わずに計算し、等しいことを確かめる。
- 今（0.10.1）の実装と照らす。写しを持たず、info-hive-wiki のコミット BASE_COMMIT の wiki_pages.py と wiki_lint.py を
  git から取り出して読み込む。違ってよいのは、今の関数の並びの鍵で同じになる組の中の順と、設計の 7 の表のものだけ。
- 探索: OS を呼ぶ口のすべてを差し替えて呼び出しを数え、走査が呼ぶはずの呼び出しの集合と役割を木から計算して、
  失敗のない実行で集合が等しいことを確かめる。そのうえで、呼び出しのそれぞれに失敗を 1 つずつ入れ、木と役割から
  計算した答えと等しいことを確かめる。わざと決まりを破った実装（対照）を、探索が見つけることも確かめる。
- 口の一覧: 走査の関数の構文木に、口の一覧にない入出力の呼び出しと、read_os のほかの except OSError がないこと。
- 使う側: stats、MCP の索引の印、list_index、索引の更新の失敗。

リンクを作れない環境では、その木を飛ばす。ジャンクションは Windows だけ、FIFO と名前に \\ を含むファイルは
Linux と macOS だけで作る。大文字と小文字を区別するフォルダーは、Windows で fsutil が使えるときだけ作る。

実行（標準ライブラリだけで動く。MCP の索引の試験は、索引の依存がなければ飛ばす）:
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
CYCLIC = {name for name in TREES if name.startswith("循環")}


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


def model(spec, start, prefix="", skip_top=False):
    """失敗のないときの .md のふつうのファイルの相対パス（並びも）を、木の表から計算する。"""
    kind, real = resolve(spec, start)
    found = []
    if kind != "dir":
        return found

    def descend(real, pre, path):
        for name, value in node_at(spec, real).items():
            rel = pre + name
            if skip_top and pre == prefix and name in wiki_pages.SKIP_TOP_LEVEL_DIRS:
                continue
            if isinstance(value, dict):
                child = real + (name,)
                if child not in path:
                    descend(child, rel + "/", path + (child,))
            elif isinstance(value, str):
                if name.lower().endswith(".md"):
                    found.append(rel)
            elif value[0] == "junction":
                target_kind, child = link_target(spec, value)
                if target_kind == "dir" and child not in path:
                    descend(child, rel + "/", path + (child,))
            elif value[0] == "flink":
                target_kind, _real = link_target(spec, value)
                if target_kind == "file" and name.lower().endswith(".md"):
                    found.append(rel)
            # dlink、broken、rawlink、fifo は、降りず、ふつうのファイルでもない
    descend(real, prefix, (real,))
    return sorted(found, key=sort_key)


def model_pages(spec):
    return [rel for rel in model(spec, ("wiki",), skip_top=True) if wiki_pages.is_page_path(rel)]


def model_index(spec):
    kind, _real = resolve(spec, ("wiki", "index.md"))
    return (["index.md"] if kind == "file" else []) + model(spec, ("wiki", "indexes"), prefix="indexes/")


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

    戻り値は {(名前, wiki からの相対パス): 役割の集合}。役割は ("list", X)、("entry", E)、("file", X)、
    ("self", X)（ディレクトリの識別子）、("chain", J)（ジャンクション J のための道筋の識別子）。
    """
    calls = {}

    def add(op, rel, role):
        calls.setdefault((op, rel), set()).add(role)

    if top_index:
        add("stat", "index.md", ("file", "index.md"))
    start_rel = prefix.rstrip("/") or "."
    kind, real = resolve(spec, start)
    add("scandir", start_rel, ("list", start_rel))
    if kind != "dir":
        return calls

    def chain_rels(pre):
        rels = [start_rel]
        parts = [p for p in pre[len(prefix):].split("/") if p]
        for i in range(1, len(parts) + 1):
            rels.append(prefix + "/".join(parts[:i]))
        return rels

    def descend(real, pre, path, through):
        rel_dir = pre.rstrip("/") or "."
        add("scandir", rel_dir, ("list", rel_dir))
        add("scandir.next", rel_dir, ("list", rel_dir))
        for name, value in node_at(spec, real).items():
            rel = pre + name
            if skip_top and pre == prefix and name in wiki_pages.SKIP_TOP_LEVEL_DIRS:
                continue
            add("is_symlink", rel, ("entry", rel))
            add("is_dir", rel, ("entry", rel))
            junction = isinstance(value, tuple) and value[0] == "junction"
            child = None
            if isinstance(value, dict):
                child = real + (name,)
            elif junction:
                target_kind, target = link_target(spec, value)
                child = target if target_kind == "dir" else None
            if child is not None:
                if NT:
                    add("entry.stat", rel, ("entry", rel))
                if junction or through:
                    add("file_id", rel, ("self", rel))
                    if junction and not through:
                        for c in chain_rels(pre):
                            add("file_id", c, ("chain", rel))
                if child not in path:
                    descend(child, rel + "/", path + (child,), through or junction)
            elif not (isinstance(value, tuple) and value[0] in ("dlink", "rawlink")) and name.lower().endswith(".md"):
                # 解けないリンクは is_dir() が送出し、そこで「ない」になるので、os.stat() を呼ばない
                add("stat", rel, ("file", rel))
    descend(real, prefix, (real,), False)
    return calls


def answers_with_failure(answer, roles, behavior):
    """失敗を入れた呼び出しの役割から、ありうる答え (files, unlistable, unknown) を計算する。"""
    out = []
    for what, place in sorted(roles):
        if what == "list":
            files = [rel for rel in answer if not (place == "." or rel.startswith(place + "/"))]
            notices = ([place], [])
        else:
            files = [rel for rel in answer if not (rel == place or rel.startswith(place + "/"))]
            notices = ([], [place])
        out.append((files, [], []) if behavior == "absent" else (files, notices[0], notices[1]))
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
    FAILURES["noid"] = lambda: wiki_pages.NoFileId(None, "入れた失敗", None, 50)
    FAILURES["blk"] = None  # 例外ではなく、os.stat() が S_IFBLK の成功を返す
ONLY_FOR = {"blk": ("stat",), "noid": ("file_id",)}
EXPECT = {"absent": "absent", "denied": "denied", "eio": "raise", "loop": "absent", "ebadf": "denied",
          "badname": "absent", "notready": "denied", "noid": "denied", "blk": "denied"}
BLOCK_DEVICE = os.stat_result((0x6000, 0, 0, 0, 0, 0, 0, 0, 0, 0))


class Injector:
    """口の呼び出しを数え、N 回目に失敗を入れる。一覧は、開くと取り出すを別々に数える（閉じるときの失敗は CPython が捨てる）。"""

    def __init__(self, root, fail_at=None, kind=None):
        self.root = os.path.abspath(str(root))
        self.fail_at, self.kind = fail_at, kind
        self.count = 0
        self.failed = None
        self.calls = []
        self.real = {"scandir": os.scandir, "stat": os.stat, "file_id": wiki_pages.win_file_id}

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
            def __init__(self, entry):
                self._entry = entry
                self.name, self.path = entry.name, entry.path

            def is_symlink(self):
                injector.hit("is_symlink", self.path)
                return self._entry.is_symlink()

            def is_dir(self, **kwargs):
                injector.hit("is_dir", self.path)
                return self._entry.is_dir(**kwargs)

            def stat(self, **kwargs):
                injector.hit("entry.stat", self.path)
                return self._entry.stat(**kwargs)

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

    def stat(self, path, *args, **kwargs):
        if self.hit("stat", path):
            return BLOCK_DEVICE
        return self.real["stat"](path, *args, **kwargs)

    def file_id(self, path):
        self.hit("file_id", path)
        return self.real["file_id"](path)

    def __enter__(self):
        os.scandir, os.stat = self.scandir, self.stat
        wiki_pages.win_file_id = self.file_id
        return self

    def __exit__(self, *exc):
        os.scandir, os.stat = self.real["scandir"], self.real["stat"]
        wiki_pages.win_file_id = self.real["file_id"]


def explore(wiki, function, answer, expected, first_only=False):
    """function(wiki) -> Walk に失敗を 1 つずつ入れ、木から計算した答えと比べる。破られた決まりの並びと、実行の数を返す。

    first_only が真なら、最初の破れで止める（対照が見つかることを確かめるときに使う）。
    """
    violations = []
    with Injector(wiki) as base_run:
        try:
            baseline = function(wiki)
        except OSError as exc:
            return [f"失敗なし: 送出した（{type(exc).__name__}）"], 0
    if [f.rel for f in baseline.files] != answer or baseline.unlistable or baseline.unknown:
        violations.append(f"失敗なし: 答えと違う {[f.rel for f in baseline.files]}")
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
            wants = answers_with_failure(answer, roles, behavior)
            got = ([f.rel for f in result.files], result.unlistable, result.unknown)
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
    return wiki_pages.Walk(found.files, [], [])


def control_discard_all(root):
    found = wiki_pages.walk_pages(root)
    if found.unlistable or found.unknown:
        return wiki_pages.Walk([], ["."], [])
    return found


def control_path_string_identity(root):
    """識別子の代わりに、パスの文字列を使う（文字列の比較への逃げ道）。"""
    with swapped(wiki_pages, "_identity", lambda path: ("ok", ("path", os.path.normcase(path)))):
        return wiki_pages.walk_pages(root)


def control_ignore_block_device(root):
    """os.stat() が返した S_IFBLK の成功を、そのまま受け取る（ページを知らせなしに落とす）。"""
    with swapped(wiki_pages, "_stat_entry", lambda path: wiki_pages.read_os(os.stat, path)):
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


def control_identity_everywhere(root):
    """ジャンクションでないディレクトリにも、識別子を取る呼び出しをする（道筋の識別子が兄弟に漏れるのと同じ形）。"""
    with swapped(wiki_pages, "_is_junction", lambda entry: ("ok", True)):
        return wiki_pages.walk_pages(root)


def control_os_stat_identity(root):
    """識別子を os.stat() から取る（3.12 以降、識別子の取得の失敗で形が変わる）。"""
    def identity(path):
        st = os.stat(path)
        return "ok", (st.st_dev, st.st_ino)
    with swapped(wiki_pages, "_identity", identity):
        return wiki_pages.walk_pages(root)


def control_nfc_key(root):
    found = wiki_pages.walk_pages(root)
    files = sorted(found.files, key=lambda f: (unicodedata.normalize("NFC", f.rel), f.rel))
    return wiki_pages.Walk(files, found.unlistable, found.unknown)


CONTROLS = [("どの失敗も「ない」にする", control_swallow_all), ("権限を知らせずに飛ばす", control_silent),
            ("知らせがあったら全ページを捨てる", control_discard_all),
            ("解けないリンクで送出する", control_raise_on_unresolvable)]
if NT:
    CONTROLS += [("識別子の代わりにパスの文字列を使う", control_path_string_identity),
                 ("os.stat() の S_IFBLK の成功を、そのまま受け取る", control_ignore_block_device),
                 ("ジャンクションでないディレクトリにも識別子を取る", control_identity_everywhere),
                 ("識別子を os.stat() から取る", control_os_stat_identity)]
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
                self.assertEqual([f.rel for f in pages.files], model_pages(spec))
                self.assertEqual([f.rel for f in index.files], model_index(spec))
                self.assertEqual((pages.unlistable, pages.unknown, index.unlistable, index.unknown), ([], [], [], []))
                if label in CYCLIC:
                    continue  # 今の実装は、循環するジャンクションで壊れる（3.10 は送出、3.14 は同じページを何度も返す）
                self.assertTrue(same_up_to_ties(old_pages(wiki), new_pages(wiki), wiki_text.posix_rel),
                                (old_pages(wiki), new_pages(wiki)))
                old_idx, new_idx = old_index(wiki), new_index(wiki)
                self.assertEqual(sorted(old_idx), sorted(expected_old_index(spec)))
                self.assertTrue(same_up_to_ties([r for r in old_idx if r in new_idx], [r for r in new_idx if r in old_idx],
                                                PurePath), (old_idx, new_idx))

    def test_case_sensitive_folder(self):
        """Windows で、大文字と小文字を区別するフォルダーの a.md と A.md。今の 3.10 は片方を落とす（設計の 7 の表）。"""
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
        old_p, old_i = old_pages(wiki), old_index(wiki)
        if sys.version_info >= (3, 12):
            self.assertEqual(old_p, new_pages(wiki))
            self.assertTrue(same_up_to_ties(old_i, new_index(wiki), PurePath))
        else:
            # 3.10 の rglob は、返したパスを Path の比較で重複除去する
            self.assertEqual(len(old_p), 1)
            self.assertEqual(len(old_i), 1)

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
            for name, function, answer, expected in targets:
                with self.subTest(tree=label, target=name):
                    found, runs = explore(wiki, function, answer, expected)
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
                    found, _runs = explore(wiki, function, model_pages(spec), expected_calls(spec, ("wiki",), "", True),
                                           first_only=True)
                    if found:
                        caught = True
                        break
                self.assertTrue(caught, f"対照「{name}」を、探索が見つけなかった")


@unittest.skipUnless(NT, "Windows だけ")
class IdentityTests(TreeCase):
    """識別子を取れない場合と、Windows の os.stat() の読み替え。"""

    def walk(self, wiki, **patch):
        stack = contextlib.ExitStack()
        with stack:
            for name, value in patch.items():
                if name == "stat":
                    stack.enter_context(swapped(os, "stat", value))
                else:
                    stack.enter_context(swapped(wiki_pages, name, value))
            return wiki_pages.walk_pages(wiki)

    def test_identity(self):
        real = wiki_pages.win_file_id
        wiki = self.make("t1", {"wiki": {"a.md": "a", "junc": ("junction", "ext")}, "ext": {"c.md": "c"}})
        if wiki is None:
            self.skipTest("ジャンクションを作れない")
        junc = str(wiki / "junc")

        def zero(path):
            value = real(path)
            return (value[0], bytes(16)) if os.fspath(path) == junc else value

        def noid(path):
            if os.fspath(path) == junc:
                raise wiki_pages.NoFileId(None, "入れた失敗", path, 50)
            return real(path)

        def zero_start(path):
            value = real(path)
            return (value[0], bytes(16)) if os.fspath(path) == str(wiki) else value

        found = self.walk(wiki)
        self.assertEqual(([f.rel for f in found.files], found.unknown), (["a.md", "junc/c.md"], []))
        for label, fake in (("FileId が 0", zero), ("識別子を持たない", noid), ("起点の FileId が 0", zero_start)):
            with self.subTest(case=label):
                found = self.walk(wiki, win_file_id=fake)
                self.assertEqual(([f.rel for f in found.files], found.unknown), (["a.md"], ["junc"]))

    def test_sibling_has_no_identity_call(self):
        real = wiki_pages.win_file_id
        wiki = self.make("t2", {"wiki": {"j": ("junction", "ext"), "plain": {"x.md": "x"}}, "ext": {"c.md": "c"}})
        if wiki is None:
            self.skipTest("ジャンクションを作れない")
        calls = []

        def recording(path):
            calls.append(os.fspath(path))
            return real(path)
        found = self.walk(wiki, win_file_id=recording)
        self.assertEqual([f.rel for f in found.files], ["j/c.md", "plain/x.md"])
        self.assertNotIn(str(wiki / "plain"), calls)

    def test_os_stat_rewrites(self):
        wiki = self.make("t3", {"wiki": {"a.md": "a", "locked.md": "l"}})
        real_stat = os.stat
        locked = str(wiki / "locked.md")

        def zero(path, *args, **kwargs):
            st = real_stat(path, *args, **kwargs)
            if os.fspath(path) == locked:
                return os.stat_result((st.st_mode, 0, 0, st.st_nlink, st.st_uid, st.st_gid, st.st_size,
                                       st.st_atime, st.st_mtime, st.st_ctime))
            return st

        def block(path, *args, **kwargs):
            return BLOCK_DEVICE if os.fspath(path) == locked else real_stat(path, *args, **kwargs)
        found = self.walk(wiki, stat=zero)  # 開けないファイル: 一覧の情報で成功する。ファイルとして返す
        self.assertEqual(([f.rel for f in found.files], found.unknown), (["a.md", "locked.md"], []))
        found = self.walk(wiki, stat=block)  # 属性の取得の失敗: S_IFBLK の成功。分からない
        self.assertEqual(([f.rel for f in found.files], found.unknown), (["a.md"], ["locked.md"]))

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

    FUNCTIONS = ("read_os", "win_file_id", "_stat_entry", "_list_dir", "_identity", "_chain_identities", "_is_junction",
                 "walk_markdown", "walk_pages", "walk_index_files")
    # 走査の関数が参照してよい os の名前（口と、OS を呼ばない文字列の操作）
    ALLOWED_OS = {"os.scandir", "os.stat", "os.fspath", "os.path.join"}
    FORBIDDEN_NAMES = {"open", "walk", "isfile", "isdir", "exists", "realpath", "samefile", "lstat", "rglob", "glob",
                       "iterdir", "resolve", "is_file", "read_text", "read_bytes"}

    def violations(self, source):
        tree = ast.parse(source)
        found = []
        functions = {node.name: node for node in tree.body if isinstance(node, ast.FunctionDef)}
        for name in self.FUNCTIONS:
            self.assertIn(name, functions)
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
        planted = source.replace("    files, unlistable, unknown = [], [], []\n",
                                 "    files, unlistable, unknown = [], [], []\n    os.path.isfile(start)\n", 1)
        self.assertNotEqual(planted, source)
        self.assertIn("walk_markdown: isfile()", self.violations(planted))
        planted = source.replace("    files, unlistable, unknown = [], [], []\n",
                                 "    files, unlistable, unknown = [], [], []\n    os.listdir(start)\n", 1)
        self.assertIn("walk_markdown: os.listdir", self.violations(planted))
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
        with Injector(wiki) as run:
            result = wiki_stats.compute_stats(wiki)
        # 除く名前の下には、口のどれも呼ばない。indexes は、名前の項目への os.lstat() だけ（口の外）。
        touched = [rel for _op, rel in run.calls if rel.split("/")[0] in wiki_pages.SKIP_TOP_LEVEL_DIRS]
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

                def broken(path):
                    raise OSError(errno.EIO, "入れた失敗")
                with swapped(os, "scandir", broken):
                    with self.assertRaises(OSError):
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
