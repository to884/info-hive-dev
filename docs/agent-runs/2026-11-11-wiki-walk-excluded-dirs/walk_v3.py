"""走査の計画の 3 版目の試作と探索。root-causes.md の「構造を変える案」の 1〜4 を写す。

- 口は、os.scandir（開く、項目を 1 つ取り出す、閉じる）、項目の is_symlink、is_dir、stat、os.stat だけ。
  os.path.realpath も、パスの文字列の比較も使わない。
- 同じディレクトリかどうかは、os.stat の st_dev と st_ino だけで決める。取れなければ「分からない」。
- 循環は、道筋のディレクトリの識別子と比べて見つける。
- 並びの鍵、ページかどうかの規則、除く名前は、実物の wiki_text、wiki_pages から読み込む（写しを持たない）。
- 今の実装との照合は、実物の wiki_pages.iter_page_files() と wiki_lint.index_files() を呼ぶ。
- 探索の答えは、木の作り（SPEC）から計算し、走査の結果と等しいことを確かめる。

使い方:
    python walk_v3.py check <作業用のディレクトリ>     木ごとに、答えとの一致と、今の実装との照合を見る
    python walk_v3.py explore <作業用のディレクトリ>   口の呼び出しの N 回目に失敗を入れ、答えと等しいかを見る
    python walk_v3.py wikis <wiki>...                  実物の wiki で、今の実装と照合する
"""
import errno
import os
import shutil
import stat
import subprocess
import sys
import unicodedata
from pathlib import Path
from typing import NamedTuple

HERE = Path(__file__).resolve().parent
SCRIPTS = HERE.parents[2] / "info-hive-wiki" / "skills" / "info-hive" / "scripts"
sys.path.insert(0, str(SCRIPTS))
import wiki_lint  # noqa: E402 実物（今の index_files()）
import wiki_pages  # noqa: E402 実物（今の iter_page_files()、is_page_path()、SKIP_TOP_LEVEL_DIRS）
import wiki_text  # noqa: E402 実物（並びの鍵の posix_rel()）

ABSENT = (FileNotFoundError, NotADirectoryError)
NT = os.name == "nt"


class MdFile(NamedTuple):
    rel: str
    size: int
    mtime_ns: int


class Walk(NamedTuple):
    files: list
    unlistable: list
    unknown: list


def sort_key(rel):
    """並びの鍵。今の iter_page_files() の鍵（posix_rel）に、同じ鍵のときの決め方（綴り）を足したもの。"""
    return (wiki_text.posix_rel(rel), rel)


def read_os(call, *args, **kwargs):
    """口の呼び出しの結果を (状態, 値) で返す。失敗の読み替えは、ここだけで行う。"""
    try:
        return "ok", call(*args, **kwargs)
    except ABSENT:
        return "absent", None
    except PermissionError:
        return "denied", None


def list_dir(directory):
    with os.scandir(directory) as it:
        return list(it)


def identity(path):
    """(状態, 識別子)。識別子は (st_dev, st_ino)。st_ino が 0 なら、分からない（"denied" と同じ扱い）。"""
    state, st = read_os(os.stat, path)
    if state != "ok":
        return state, None
    if not st.st_ino:
        return "denied", None
    return "ok", (st.st_dev, st.st_ino)


def is_junction(entry):
    """(状態, ジャンクションか)。Windows のほかでは、呼び出しをせずに偽を返す。"""
    if not NT:
        return "ok", False
    state, st = read_os(entry.stat, follow_symlinks=False)
    if state != "ok":
        return state, False
    return "ok", bool(st.st_file_attributes & stat.FILE_ATTRIBUTE_REPARSE_POINT) \
        and st.st_reparse_tag == stat.IO_REPARSE_TAG_MOUNT_POINT


def walk(start, prefix="", skip_top=False):
    """start の下をたどり、Walk を返す。

    起点には、リンクであっても降りる。途中のディレクトリのシンボリックリンクには降りない。ジャンクションには降りる。
    ジャンクションを通った道筋では、入ろうとするディレクトリの識別子が、起点からそこまでのどれかと同じなら降りない。
    """
    files, unlistable, unknown = [], [], []
    # スタックの項目: (ディレクトリのパス, 相対パスの接頭辞, 起点からここまでのパスの並び, 識別子の並びか None)
    start = str(start)
    stack = [(start, prefix, (start,), None)]
    while stack:
        directory, pre, chain, ids = stack.pop()
        state, entries = read_os(list_dir, directory)
        if state == "absent":
            continue
        if state == "denied":
            unlistable.append(pre.rstrip("/") or ".")
            continue
        for entry in entries:
            name = entry.name
            rel = pre + name
            if skip_top and pre == prefix and name in wiki_pages.SKIP_TOP_LEVEL_DIRS:
                continue
            state, is_link = read_os(entry.is_symlink)
            if state == "ok":
                state, is_dir = read_os(entry.is_dir)
            if state == "ok" and is_dir and not is_link:
                state, junction = is_junction(entry)
            if state == "absent":
                continue
            if state == "denied":
                unknown.append(rel)
                continue
            if is_dir:
                if is_link:
                    continue  # ディレクトリのシンボリックリンク。降りず、ファイルでもない
                child_ids = None
                if junction or ids is not None:
                    state, child = identity(entry.path)
                    if state == "ok" and ids is None:
                        # この道筋で初めて識別子が要る。起点からここまでの識別子を取る。
                        found = []
                        for path in chain:
                            state, one = identity(path)
                            if state != "ok":
                                break
                            found.append(one)
                        else:
                            ids = tuple(found)
                    if state == "absent":
                        continue
                    if state == "denied":
                        unknown.append(rel)  # 同じ場所を回っていないかを、調べられなかった
                        continue
                    if child in ids:
                        continue  # 道筋の上のディレクトリに戻る。降りない
                    child_ids = ids + (child,)
                stack.append((entry.path, rel + "/", chain + (entry.path,), child_ids))
                continue
            if name.lower().endswith(".md"):
                state, st = read_os(os.stat, entry.path)
                if state == "absent":
                    continue  # 先のないリンク
                if state == "denied":
                    unknown.append(rel)
                    continue
                if stat.S_ISREG(st.st_mode):
                    files.append(MdFile(rel, st.st_size, st.st_mtime_ns))
    files.sort(key=lambda f: sort_key(f.rel))
    return Walk(files, sorted(unlistable, key=sort_key), sorted(unknown, key=sort_key))


def walk_pages(root):
    found = walk(root, skip_top=True)
    return Walk([f for f in found.files if wiki_pages.is_page_path(f.rel)], found.unlistable, found.unknown)


def walk_index_files(root):
    files, unknown = [], []
    state, st = read_os(os.stat, os.path.join(str(root), "index.md"))
    if state == "denied":
        unknown.append("index.md")
    elif state == "ok" and stat.S_ISREG(st.st_mode):
        files.append(MdFile("index.md", st.st_size, st.st_mtime_ns))
    below = walk(os.path.join(str(root), "indexes"), prefix="indexes/")
    unlistable = ["indexes" if u == "." else u for u in below.unlistable]
    return Walk(files + below.files, unlistable, unknown + below.unknown)


def iter_page_files(root):
    return [f.rel for f in walk_pages(root).files]


def index_files(root):
    """今と同じ並び（index.md、そのあと indexes の下を Path の順）。"""
    found = [f.rel for f in walk_index_files(root).files]
    rest = sorted(Path(root) / rel for rel in found if rel != "index.md")
    return [rel for rel in found if rel == "index.md"] + [p.relative_to(root).as_posix() for p in rest]


# ---------------------------------------------------------------------------
# 木の作り（SPEC）と、そこから計算する答え
# ---------------------------------------------------------------------------
#
# 値が str ならファイル、dict ならディレクトリ、タプルならリンク。リンクの先は、木の根（wiki の親）からの相対パス。
#   ("dlink", 先)     ディレクトリのシンボリックリンク
#   ("flink", 先)     ファイルのシンボリックリンク
#   ("broken",)       先のないシンボリックリンク
#   ("junction", 先)  ジャンクション（Windows だけ）

NFD = unicodedata.normalize("NFD", "ガイド")

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
}
if NT:
    TREES.update({
        "輪でないジャンクションの別名": {"wiki": {"a": {"x.md": "x"}, "alias": ("junction", "wiki/a")}},
        "下を指すジャンクション": {"wiki": {"a": {"b": {"c.md": "c"}, "j": ("junction", "wiki/a/b")}}},
        "循環: sub/loop と indexes が wiki を指す": {
            "wiki": {"a.md": "a", "sub": {"b.md": "b", "loop": ("junction", "wiki")}, "indexes": ("junction", "wiki")}},
        "循環: a/b/j が a を、a/me が a を指す": {
            "wiki": {"a": {"top.md": "t", "b": {"c.md": "c", "j": ("junction", "wiki/a")}, "me": ("junction", "wiki/a")}}},
        "循環: 2 つのジャンクション": {
            "wiki": {"x": {"p.md": "p", "j1": ("junction", "ext")}},
            "ext": {"q.md": "q", "j2": ("junction", "wiki/x")}},
        "循環: wiki の親を指す": {
            "wiki": {"a.md": "a", "up": ("junction", "")},
            "side": {"s.md": "s"}},
    })
else:
    TREES["名前に \\ を含む"] = {"wiki": {"a\\b.md": "1", "a0.md": "2", "c": {"d.md": "3"}}}
    TREES["鍵が同じになる名前"] = {"wiki": {"a\\b.md": "1", "a": {"b.md": "2"}, "a0.md": "3"}}

# 今の実装と、失敗のないときの結果が違ってよい木（設計が挙げた違い）。
CYCLIC = {name for name in TREES if name.startswith("循環")}
SAME_KEY = {"鍵が同じになる名前"}


def build(base, spec):
    """SPEC を、ディスクの上に作る。リンクは、ふつうの項目を作り終えてから作る。"""
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
        target = base / value[1] if len(value) > 1 else base / "no-such-target"
        if kind == "junction":
            done = subprocess.run(["cmd", "/c", "mklink", "/J", str(path), str(target)], capture_output=True).returncode == 0
        else:
            try:
                os.symlink(target, path, target_is_directory=(kind == "dlink"))
                done = True
            except OSError:
                done = False
        if not done:
            return False
    return True


def remove_tree(base):
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
    """木の根からのパスを、リンクを解いて、(種類, 実体のパス) にする。種類は "dir"、"file"、None（ない）。"""
    node, real = spec, ()
    for part in parts:
        if not isinstance(node, dict) or part not in node:
            return None, None
        value = node[part]
        if isinstance(value, tuple):
            if value[0] == "broken":
                return None, None
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


def model(spec, start, prefix="", skip_top=False):
    """SPEC から、失敗のないときの .md のファイルの相対パス（並びも）を計算する。走査のコードを使わない。"""
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
                kind, child = resolve(spec, tuple(p for p in value[1].split("/") if p))
                if kind == "dir" and child not in path:
                    descend(child, rel + "/", path + (child,))
            elif value[0] == "flink":
                kind, _real = resolve(spec, tuple(p for p in value[1].split("/") if p))
                if kind == "file" and name.lower().endswith(".md"):
                    found.append(rel)
            # dlink と broken は、降りず、ファイルでもない
    descend(real, prefix, (real,))
    return sorted(found, key=sort_key)


def model_pages(spec):
    return [rel for rel in model(spec, ("wiki",), skip_top=True) if wiki_pages.is_page_path(rel)]


def model_index(spec):
    kind, _real = resolve(spec, ("wiki", "index.md"))
    top = ["index.md"] if kind == "file" else []
    return top + model(spec, ("wiki", "indexes"), prefix="indexes/")


# ---------------------------------------------------------------------------
# 木ごとの確かめ
# ---------------------------------------------------------------------------


def old_pages(wiki):
    return [p.relative_to(wiki).as_posix() for p in wiki_pages.iter_page_files(Path(wiki))]


def old_index(wiki):
    return [p.relative_to(wiki).as_posix() for p in wiki_lint.index_files(Path(wiki))]


def expected_old_index(spec):
    """今の index_files() が返すはずのもの。答えから、設計が挙げた 2 つの違いを戻して作る。"""
    rels = model_index(spec)
    if not NT:
        rels = [rel for rel in rels if rel == "index.md" or rel.endswith(".md")]  # 今は、大文字の拡張子を返さない
    kind, _real = resolve(spec, ("wiki", "indexes"))
    if kind == "dir":
        # 今は、.md で終わる名前のディレクトリも返す
        def dirs(real, pre, path):
            for name, value in node_at(spec, real).items():
                if isinstance(value, dict):
                    child = real + (name,)
                    if name.endswith(".md") or (NT and name.lower().endswith(".md")):
                        rels.append(pre + name)
                    if child not in path:
                        dirs(child, pre + name + "/", path + (child,))
        _kind, real = resolve(spec, ("wiki", "indexes"))
        dirs(real, "indexes/", (real,))
    top = [rel for rel in rels if rel == "index.md"]
    rest = sorted(Path("w") / rel for rel in rels if rel != "index.md")
    return top + [p.relative_to("w").as_posix() for p in rest]


def cmd_check(work):
    base_dir = Path(work) / "v3"
    ok = True
    for number, (label, spec) in enumerate(TREES.items()):
        base = base_dir / f"t{number}"
        remove_tree(base)
        if not build(base, spec):
            print(f"  {label}: リンクを作れなかったので飛ばした")
            continue
        wiki = base / "wiki"
        pages, index = walk_pages(wiki), walk_index_files(wiki)
        answer_pages, answer_index = model_pages(spec), model_index(spec)
        same_answer = [f.rel for f in pages.files] == answer_pages and [f.rel for f in index.files] == answer_index \
            and not (pages.unlistable or pages.unknown or index.unlistable or index.unknown)
        line = f"  {label}: ページ {len(answer_pages)} 個、索引 {len(answer_index)} 個、答えと一致: {same_answer}"
        if label in CYCLIC:
            line += "。今の実装との照合はしない（循環）"
            same_old = True
        else:
            got_old = old_pages(wiki)
            if label in SAME_KEY:
                same_old = sorted(got_old) == sorted(iter_page_files(wiki))
                line += f"。今の実装とページの集合が一致: {same_old}（並びは、鍵が同じ名前の順だけ違ってよい。今 {got_old}、案 {iter_page_files(wiki)}）"
            else:
                same_old = got_old == iter_page_files(wiki)
                line += f"。今の実装とページの並びまで一致: {same_old}"
            old_idx = old_index(wiki)
            same_index = old_idx == expected_old_index(spec) and \
                [rel for rel in index_files(wiki) if rel in old_idx] == [rel for rel in old_idx if rel in index_files(wiki)]
            line += f"、索引は挙げた違いを除いて一致: {same_index}"
            same_old = same_old and same_index
        print(line)
        if not same_answer:
            print("    答え:", answer_pages, answer_index)
            print("    走査:", [f.rel for f in pages.files], [f.rel for f in index.files], pages.unlistable, pages.unknown)
        if label in CYCLIC or "別名" in label or "指す" in label:
            print("    ページ:", answer_pages, "索引:", answer_index)
        ok = ok and same_answer and same_old
        remove_tree(base)
    return ok


# ---------------------------------------------------------------------------
# 探索: 口の呼び出しの N 回目に失敗を入れ、木から計算した答えと比べる
# ---------------------------------------------------------------------------

FAILURES = {
    "absent": lambda: FileNotFoundError(errno.ENOENT, "入れた失敗"),
    "denied": lambda: PermissionError(errno.EACCES, "入れた失敗"),
    "eio": lambda: OSError(errno.EIO, "入れた失敗"),
}
ENTRY_OPS = ("is_symlink", "is_dir", "entry.stat")
LIST_OPS = ("scandir", "scandir.next", "scandir.close")


class Injector:
    """口の呼び出しを数え、N 回目に失敗を入れる。一覧は、開く、取り出す、閉じるを別々に数える。"""

    def __init__(self, root, fail_at=None, kind=None):
        self.root = os.path.abspath(str(root))
        self.fail_at, self.kind = fail_at, kind
        self.count = 0
        self.failed = None     # 失敗を入れた呼び出しの (名前, wiki からの相対パス, 直前に調べていた項目)
        self.last_entry = None
        self.real = {"scandir": os.scandir, "stat": os.stat}

    def rel(self, path):
        text = os.fspath(path)
        if text == self.root:
            return "."
        if text.startswith(self.root + os.sep):
            return text[len(self.root) + 1:].replace(os.sep, "/") if NT else text[len(self.root) + 1:]
        raise AssertionError(f"走査が、wiki の外のパスを口に渡した: {text}")

    def hit(self, name, path):
        index = self.count
        self.count += 1
        if name in ENTRY_OPS:
            self.last_entry = self.rel(path)
        if index == self.fail_at:
            self.failed = (name, self.rel(path), self.last_entry)
            raise FAILURES[self.kind]()

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
                if exc[0] is None:
                    injector.hit("scandir.close", path)
                return False

        return Listing()

    def stat(self, path, *args, **kwargs):
        self.hit("stat", path)
        return self.real["stat"](path, *args, **kwargs)

    def __enter__(self):
        os.scandir, os.stat = self.scandir, self.stat
        return self

    def __exit__(self, *exc):
        os.scandir, os.stat = self.real["scandir"], self.real["stat"]


def under(rel, place):
    return place == "." or rel == place or rel.startswith(place + "/")


def answer_with_failure(answer, wiki, failed, kind, start_rel):
    """失敗を入れたときの答え (files, unlistable, unknown) を、失敗のないときの答えと、失敗の場所から計算する。"""
    name, place, last_entry = failed
    if name in LIST_OPS:
        # そのディレクトリの中身が、すべて分からなくなる（なくなる）
        lost = lambda rel: place == "." or rel.startswith(place + "/")  # noqa: E731
        notice = ("unlistable", place)
    elif name in ENTRY_OPS:
        lost = lambda rel: under(rel, place)  # noqa: E731
        notice = ("unknown", place)
    else:  # os.stat
        target = os.path.join(str(wiki), place) if place != "." else str(wiki)
        try:
            is_dir = stat.S_ISDIR(os.stat(target).st_mode)
        except OSError:
            is_dir = False
        # ディレクトリへの os.stat は、識別子を取る呼び出しである。調べていた項目（ジャンクションか、その下のディレクトリ）が分からなくなる。
        judged = last_entry if is_dir else place
        lost = lambda rel: under(rel, judged)  # noqa: E731
        notice = ("unknown", judged)
    files = [rel for rel in answer if not lost(rel)]
    if kind == "absent":
        return files, [], []
    return files, ([notice[1]] if notice[0] == "unlistable" else []), ([notice[1]] if notice[0] == "unknown" else [])


def explore(wiki, function, answer, start_rel, label, quiet=False):
    """function(wiki) -> Walk に、口の呼び出しのそれぞれで 3 つの失敗を入れ、答えと等しいかを見る。"""
    violations = []
    with Injector(wiki) as base_run:
        baseline = function(wiki)
    if [f.rel for f in baseline.files] != answer or baseline.unlistable or baseline.unknown:
        violations.append(f"失敗なし: 答えと違う {[f.rel for f in baseline.files]}")
    runs = 0
    for index in range(base_run.count):
        for kind in FAILURES:
            runs += 1
            with Injector(wiki, index, kind) as run:
                try:
                    result, raised = function(wiki), None
                except OSError as exc:
                    result, raised = None, exc
            where = f"{run.failed[0]}({run.failed[1]}) に {kind}"
            if kind == "eio":
                if raised is None or raised.errno != errno.EIO:
                    violations.append(f"{where}: 送出しなかった")
                continue
            if raised is not None:
                violations.append(f"{where}: 送出した（{type(raised).__name__}）")
                continue
            want = answer_with_failure(answer, wiki, run.failed, kind, start_rel)
            got = ([f.rel for f in result.files], result.unlistable, result.unknown)
            if got != want:
                violations.append(f"{where}: 答えと違う。答え {want}、走査 {got}")
    if not quiet:
        print(f"  {label}: 口の呼び出し {base_run.count} 回、失敗を入れた実行 {runs} 回、答えと違った実行 {len(violations)} 件")
    return violations, runs


# 対照: わざと決まりを破った実装。探索が、どれも見つけることを確かめる。


def swapped(name, replacement, function):
    def run(root):
        original = globals()[name]
        globals()[name] = replacement
        try:
            return function(root)
        finally:
            globals()[name] = original
    return run


def read_os_swallow(call, *args, **kwargs):
    try:
        return "ok", call(*args, **kwargs)
    except OSError:
        return "absent", None


def identity_ignores_zero(path):
    """識別子を取れなかったとき、パスの文字列を識別子の代わりにする（文字列の比較への逃げ道）。"""
    try:
        st = os.stat(path)
    except OSError:
        return "ok", ("path", os.path.normcase(path))
    return "ok", (st.st_dev, st.st_ino)


def control_silent(root):
    found = walk_pages(root)
    return Walk(found.files, [], [])


def control_discard_all(root):
    """知らせがあったら、知らせを 1 つにして全ページを捨てる（2 回目のレビューの軽微 1 の対照）。"""
    found = walk_pages(root)
    if found.unlistable or found.unknown:
        return Walk([], ["."], [])
    return found


def control_nfc_key(root):
    """並びの鍵を、NFC だけにする（2 版目と同じ誤り）。"""
    found = walk_pages(root)
    files = sorted(found.files, key=lambda f: (unicodedata.normalize("NFC", f.rel), f.rel))
    return Walk(files, found.unlistable, found.unknown)


CONTROLS = [
    ("どの失敗も「ない」にする", swapped("read_os", read_os_swallow, walk_pages)),
    ("権限を知らせずに飛ばす", control_silent),
    ("知らせがあったら全ページを捨てる", control_discard_all),
]
if NT:
    # 識別子を使うのは、ジャンクションのある道筋だけである。ジャンクションのない OS では、違いが出ない。
    CONTROLS.append(("識別子を取れないとき、パスの文字列で比べる", swapped("identity", identity_ignores_zero, walk_pages)))
if not NT:
    # Windows では、名前に \ を置けないので、今の鍵と NFC だけの鍵が同じになる。違いが出る Linux と macOS でだけ確かめる。
    CONTROLS.append(("並びの鍵を NFC だけにする", control_nfc_key))


def cmd_explore(work):
    base_dir = Path(work) / "v3"
    ok = True
    total = 0
    built = {}
    for number, (label, spec) in enumerate(TREES.items()):
        base = base_dir / f"t{number}"
        remove_tree(base)
        if not build(base, spec):
            print(f"  {label}: リンクを作れなかったので飛ばした")
            continue
        built[label] = (base / "wiki", spec)
        wiki = base / "wiki"
        for name, function, answer, start_rel in (("ページ", walk_pages, model_pages(spec), "."),
                                                  ("索引", walk_index_files, model_index(spec), "indexes")):
            found, runs = explore(wiki, function, answer, start_rel, f"{label}、{name}")
            total += runs
            ok = ok and not found
            for line in found[:4]:
                print("    ", line)
    print(f"  失敗を入れた実行の合計: {total} 回")
    print("  対照（どの木かで、答えと違った実行が 1 件以上あれば、探索が働いている）:")
    for name, function in CONTROLS:
        caught, where = 0, None
        for label, (wiki, spec) in built.items():
            found, _runs = explore(wiki, function, model_pages(spec), ".", label, quiet=True)
            if found and where is None:
                where = (label, found[0])
            caught += len(found)
        print(f"  対照「{name}」: 答えと違った実行 {caught} 件" + (f"（例: {where[0]}、{where[1][:110]}）" if where else ""))
        ok = ok and caught > 0
    for label, (wiki, _spec) in built.items():
        remove_tree(wiki.parent)
    return ok


def cmd_wikis(paths):
    ok = True
    for path in paths:
        wiki = Path(path)
        same_pages = old_pages(wiki) == iter_page_files(wiki)
        old_idx = [rel for rel in old_index(wiki) if (wiki / rel).is_file()]
        new_idx = [rel for rel in index_files(wiki) if NT or rel == "index.md" or rel.endswith(".md")]
        print(f"  {wiki.name}: ページ {len(iter_page_files(wiki))} 個、並びまで一致: {same_pages}。"
              f"索引 {len(new_idx)} 個、挙げた違いを除いて一致: {old_idx == new_idx}")
        ok = ok and same_pages and old_idx == new_idx
    return ok


if __name__ == "__main__":
    for stream in (sys.stdout, sys.stderr):
        stream.reconfigure(encoding="utf-8")
    print(f"python {sys.version.split()[0]} {sys.platform}  {sys.argv[1]}")
    if sys.argv[1] == "wikis":
        done = cmd_wikis(sys.argv[2:])
    else:
        done = {"check": cmd_check, "explore": cmd_explore}[sys.argv[1]](sys.argv[2])
    print("  終了:", "よい" if done else "だめ")
    sys.exit(0 if done else 1)
