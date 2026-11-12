"""走査の計画の 2 版目の試作と、OS の呼び出しに失敗を入れる探索。

2 版目の決定を写す。
- OS は、os.scandir（と項目の is_symlink、is_dir、stat）、os.stat、os.path.realpath(strict=True) だけで呼ぶ。
  呼ぶたびに os から引く。pathlib の入出力は使わない。
- 失敗は 1 つの関数で読み替える。ない（FileNotFoundError、NotADirectoryError）、権限がない（PermissionError）、
  そのほか（送出）の 3 つ。
- たどり方は 1 つで、起点を変えて使う。ページは wiki のルート、索引は indexes が起点。
- 結果は、ファイルの一覧と、知らせ（一覧を作れなかったディレクトリ、調べられなかった項目）の組。

使い方:
    python walk_v2.py compare <作業用のディレクトリ>   今の実装（rglob）と、ページと索引の集合を比べる
    python walk_v2.py explore <作業用のディレクトリ>   OS の呼び出しの N 回目に失敗を入れ、決まりが守られるかを見る
    python walk_v2.py wikis <wiki>...                  実物の wiki で比べる
"""
import errno
import os
import shutil
import stat
import sys
import unicodedata
from pathlib import Path
from typing import NamedTuple

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import walk_probe as v1  # noqa: E402 木を作る関数と、今の iter_page_files() の写しを使う
import index_probe  # noqa: E402 今の index_files() の写しを使う

SKIP_TOP_LEVEL_DIRS = v1.SKIP_TOP_LEVEL_DIRS
is_page_path = v1.is_page_path
ABSENT = (FileNotFoundError, NotADirectoryError)


class MdFile(NamedTuple):
    rel: str        # wiki のルートからの相対パス（/ 区切り、ディスク上の綴り）
    size: int
    mtime_ns: int


class Walk(NamedTuple):
    files: list      # 名前が .md で終わる、ふつうのファイル（リンクの先がファイルのものを含む）
    unlistable: list  # 一覧を作れなかったディレクトリ（相対パス。起点そのものは "."）
    unknown: list     # 種類を調べられなかった項目（相対パス）


def read_os(call, *args, **kwargs):
    """OS の呼び出しの結果を (状態, 値) で返す。失敗の読み替えは、ここだけで行う。

    状態は "ok"、"absent"（ない）、"denied"（権限がなくて分からない）。そのほかの OSError は送出する。
    """
    try:
        return "ok", call(*args, **kwargs)
    except ABSENT:
        return "absent", None
    except PermissionError:
        return "denied", None


def list_dir(directory):
    with os.scandir(directory) as it:
        return list(it)


def is_junction(entry):
    """(状態, ジャンクションか)。Windows のほかでは、いつも偽。"""
    if os.name != "nt":
        return "ok", False
    state, st = read_os(entry.stat, follow_symlinks=False)
    if state != "ok":
        return state, False
    return "ok", bool(st.st_file_attributes & stat.FILE_ATTRIBUTE_REPARSE_POINT) \
        and st.st_reparse_tag == stat.IO_REPARSE_TAG_MOUNT_POINT


def same_dir(st_a, a, b):
    """(状態, 同じか)。a と b は解いた絶対パスで、st_a は a の os.stat() の結果。

    識別子（st_dev と st_ino）で比べる。stat は成功したが識別子が 0 のとき（識別子を持たないファイルシステム）
    だけ、文字列で比べる。stat の失敗は、文字列の比較に落とさず、状態で返す。
    """
    state, st_b = read_os(os.stat, b)
    if state != "ok":
        return state, False
    if st_a.st_ino and st_b.st_ino:
        return "ok", (st_a.st_dev, st_a.st_ino) == (st_b.st_dev, st_b.st_ino)
    return "ok", os.path.normcase(a) == os.path.normcase(b)


def cycles(target, directories):
    """(状態, 循環するか)。target が、directories のどれかと同じディレクトリか、その祖先なら、循環する。

    状態が "ok" でなければ、判定できなかった。"absent" は比べる相手がなくなった、"denied" は権限で調べられなかった。
    """
    state, st_target = read_os(os.stat, target)
    if state != "ok":
        return state, False
    for directory in directories:
        here = directory
        while True:
            state, same = same_dir(st_target, target, here)
            if state != "ok":
                return state, False
            if same:
                return "ok", True
            parent = os.path.dirname(here)
            if parent == here:
                break
            here = parent
    return "ok", False


def walk(start, prefix="", skip_top=False):
    """start の下をたどり、Walk を返す。prefix は、返す相対パスの先頭に付ける（"" か "indexes/"）。

    起点には、リンクであっても降りる。途中のディレクトリのシンボリックリンクには降りず、ジャンクションには降りる。
    循環するジャンクションには降りない。skip_top が真なら、起点の直下の除く名前の項目に、どの呼び出しもしない。
    """
    files, unlistable, unknown = [], [], []
    stack = [(str(start), prefix, ())]
    while stack:
        directory, pre, hops = stack.pop()
        state, entries = read_os(list_dir, directory)
        if state == "absent":
            continue
        if state == "denied":
            unlistable.append(pre.rstrip("/") or ".")
            continue
        for entry in entries:
            name = entry.name
            rel = pre + name
            if skip_top and pre == prefix and name in SKIP_TOP_LEVEL_DIRS:
                continue
            state, is_link = read_os(entry.is_symlink)
            if state == "ok":
                state, is_dir = read_os(entry.is_dir)
            if state == "absent":
                continue
            if state == "denied":
                unknown.append(rel)
                continue
            if is_dir:
                if is_link:
                    continue  # ディレクトリのシンボリックリンク。降りず、ファイルでもない
                state, junction = is_junction(entry)
                if state == "absent":
                    continue
                if state == "denied":
                    unknown.append(rel)
                    continue
                child_hops = hops
                if junction:
                    state, target = read_os(os.path.realpath, entry.path, strict=True)
                    if state == "ok":
                        state, here = read_os(os.path.realpath, directory, strict=True)
                    if state == "ok":
                        state, cyclic = cycles(target, (here, *hops))
                    if state == "absent":
                        continue  # 先か、比べる相手がなくなった。降りない
                    if state == "denied":
                        unknown.append(rel)  # 循環かどうかを調べられなかった。降りない
                        continue
                    if cyclic:
                        continue  # 循環するジャンクション
                    child_hops = hops + (here,)
                stack.append((entry.path, rel + "/", child_hops))
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
    key = lambda rel: (unicodedata.normalize("NFC", rel), rel)  # noqa: E731
    files.sort(key=lambda f: key(f.rel))
    return Walk(files, sorted(unlistable, key=key), sorted(unknown, key=key))


def walk_pages(root):
    """ページのファイルと知らせ。"""
    found = walk(root, skip_top=True)
    return Walk([f for f in found.files if is_page_path(f.rel)], found.unlistable, found.unknown)


def walk_index_files(root):
    """索引のファイル（最上位の index.md と、indexes を起点にした .md）と知らせ。"""
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
    """今までどおりの戻り値（知らせを見ない呼び出し元のため）。"""
    return [f.rel for f in walk_pages(root).files]


def index_files(root):
    """今までどおりの並び（index.md、そのあと indexes の下を Path の順）。"""
    found = [f.rel for f in walk_index_files(root).files]
    top = [rel for rel in found if rel == "index.md"]
    rest = sorted((Path(root) / rel for rel in found if rel != "index.md"))
    return top + [p.relative_to(root).as_posix() for p in rest]


# ---------------------------------------------------------------------------
# 今の実装との比較
# ---------------------------------------------------------------------------


def old_index_files(root):
    return [p.relative_to(root).as_posix() for p in index_probe.index_files(Path(root))]


def compare(root, label=None):
    root = Path(root)
    old_pages, new_pages = v1.old_iter_page_files(root), iter_page_files(root)
    old_index, new_index = old_index_files(root), index_files(root)
    # 決めた違い: 索引の側で、.md で終わる名前のディレクトリを返さない。拡張子の大文字と小文字を問わない。
    expected_index = [rel for rel in old_index if (root / rel).is_file()]
    upper = [rel for rel in new_index if not rel.endswith(".md")]
    same_index = [rel for rel in new_index if rel.endswith(".md") or os.name == "nt"] == expected_index
    print(f"  {label or root.name}: ページ {len(new_pages)} 個、並びも一致: {old_pages == new_pages}。"
          f"索引 {len(new_index)} 個、決めた違いを除いて一致: {same_index}"
          + (f"（Linux で足される大文字の拡張子: {upper}）" if upper and os.name != "nt" else ""))
    if old_pages != new_pages:
        print("    今だけ:", sorted(set(old_pages) - set(new_pages)), "案だけ:", sorted(set(new_pages) - set(old_pages)))
    if not same_index:
        print("    今の索引:", old_index, "案の索引:", new_index)
    return old_pages == new_pages and same_index


LOOP = "循環するジャンクション（sub/loop と indexes が wiki を指す）"


def make_trees(work):
    """比べる木を作り、(ラベル, wiki) の並びを返す。"""
    base = Path(work) / "v2"
    v1.remove_tree(base)
    trees = []
    wiki, _made = v1.make_tree(base / "links")
    for d in ("indexes/sub/dir.md",):
        (wiki / d).mkdir(parents=True)
    for f in ("indexes/sources.md", "indexes/Upper.MD", "indexes/A.md", "indexes/.hidden.md", "indexes/sub/deep.md",
              "indexes/sub/dir.md/in.md"):
        (wiki / f).write_text("x", encoding="utf-8")
    trees.append(("リンクを置いた木", wiki))

    wiki, ext = base / "symlink" / "wiki", base / "symlink" / "ext"
    (wiki / "concepts").mkdir(parents=True)
    ext.mkdir(parents=True)
    (wiki / "concepts" / "c.md").write_text("x", encoding="utf-8")
    (ext / "sources.md").write_text("x", encoding="utf-8")
    if v1.link("dir", wiki / "indexes", ext):
        trees.append(("indexes がシンボリックリンク", wiki))

    wiki = base / "alias" / "wiki"
    (wiki / "concepts").mkdir(parents=True)
    (wiki / "concepts" / "c.md").write_text("x", encoding="utf-8")
    (wiki / "index.md").write_text("x", encoding="utf-8")
    if v1.link("junction" if os.name == "nt" else "dir", wiki / "indexes", wiki / "concepts"):
        trees.append(("indexes がページのディレクトリを指す", wiki))
    if os.name == "nt":
        wiki = base / "twin" / "wiki"
        (wiki / "a").mkdir(parents=True)
        (wiki / "a" / "x.md").write_text("x", encoding="utf-8")
        if v1.link("junction", wiki / "alias", wiki / "a"):
            trees.append(("輪でないジャンクションの別名（a と alias）", wiki))
        wiki = base / "loop" / "wiki"
        (wiki / "sub").mkdir(parents=True)
        (wiki / "a.md").write_text("x", encoding="utf-8")
        (wiki / "sub" / "b.md").write_text("x", encoding="utf-8")
        if v1.link("junction", wiki / "sub" / "loop", wiki) and v1.link("junction", wiki / "indexes", wiki):
            trees.append((LOOP, wiki))

    wiki = base / "file" / "wiki"
    wiki.mkdir(parents=True)
    (wiki / "indexes").write_text("x", encoding="utf-8")
    (wiki / "a.md").write_text("x", encoding="utf-8")
    trees.append(("indexes がファイル", wiki))

    wiki = base / "empty" / "wiki"
    wiki.mkdir(parents=True)
    trees.append(("空の wiki", wiki))
    return base, trees


def cmd_compare(work):
    base, trees = make_trees(work)
    ok = all([compare(wiki, label) for label, wiki in trees if label != LOOP])
    label, wiki = trees[0]
    found = walk_pages(wiki)
    print("  リンクを置いた木のページ:", [f.rel for f in found.files])
    print("  リンクを置いた木の索引:", index_files(wiki))
    for label, wiki in trees:
        if "別名" in label or "ページのディレクトリを指す" in label or label == LOOP:
            print(f"  {label}: ページ {iter_page_files(wiki)}、索引 {index_files(wiki)}")
    v1.remove_tree(base)
    return ok


# ---------------------------------------------------------------------------
# 探索: OS の呼び出しの N 回目に失敗を入れる
# ---------------------------------------------------------------------------

FAILURES = {
    "absent": lambda: FileNotFoundError(errno.ENOENT, "入れた失敗"),
    "denied": lambda: PermissionError(errno.EACCES, "入れた失敗"),
    "eio": lambda: OSError(errno.EIO, "入れた失敗"),
}


class Injector:
    """os.scandir、項目の is_symlink、is_dir、stat、os.stat、os.path.realpath を数え、N 回目に失敗を入れる。"""

    def __init__(self, root, fail_at=None, kind=None):
        self.root = os.path.normcase(os.path.abspath(str(root)))
        self.fail_at, self.kind = fail_at, kind
        self.count = 0
        self.failed = None  # 失敗を入れた呼び出しの (名前, wiki からの相対パス)
        self.calls = []
        self.real = {"scandir": os.scandir, "stat": os.stat, "realpath": os.path.realpath}

    def rel(self, path):
        text = os.path.normcase(os.path.abspath(os.fspath(path)))
        if text == self.root:
            return "."
        if text.startswith(self.root + os.sep):
            return os.fspath(path)[len(self.root) + 1:].replace("\\", "/")
        return None  # wiki の外（循環の検出が親をさかのぼるとき）

    def hit(self, name, path):
        index = self.count
        self.count += 1
        self.calls.append((name, self.rel(path)))
        if index == self.fail_at:
            self.failed = (name, self.rel(path))
            raise FAILURES[self.kind]()

    def scandir(self, path):
        self.hit("scandir", path)
        injector = self

        class Wrapped:
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

        class Context:
            def __enter__(self_inner):
                self_inner.it = injector.real["scandir"](path)
                return (Wrapped(e) for e in self_inner.it.__enter__())

            def __exit__(self_inner, *exc):
                return self_inner.it.__exit__(*exc)

        return Context()

    def stat(self, path, *args, **kwargs):
        self.hit("stat", path)
        return self.real["stat"](path, *args, **kwargs)

    def realpath(self, path, **kwargs):
        self.hit("realpath", path)
        return self.real["realpath"](path, **kwargs)

    def __enter__(self):
        os.scandir, os.stat, os.path.realpath = self.scandir, self.stat, self.realpath
        return self

    def __exit__(self, *exc):
        os.scandir, os.stat, os.path.realpath = self.real["scandir"], self.real["stat"], self.real["realpath"]


def junction_rels(root):
    """木の中のジャンクションの相対パス（試験の側が、OS を直接見て調べる。循環には降りない）。"""
    found = []
    if os.name != "nt":
        return found
    stack = [(str(root), "")]
    while stack:
        directory, prefix = stack.pop()
        with os.scandir(directory) as it:
            for entry in it:
                st = entry.stat(follow_symlinks=False)
                if st.st_file_attributes & stat.FILE_ATTRIBUTE_REPARSE_POINT:
                    if st.st_reparse_tag == stat.IO_REPARSE_TAG_MOUNT_POINT:
                        found.append(prefix + entry.name)
                elif entry.is_dir(follow_symlinks=False):
                    stack.append((entry.path, prefix + entry.name + "/"))
    return found


def covered(rel, places):
    return any(place == "." or rel == place or rel.startswith(place + "/") for place in places)


def explore(root, function, label):
    """function(root) -> Walk を、失敗を入れずに 1 回、入れて (呼び出しの数 × 3) 回流し、破られた決まりを返す。"""
    junctions = junction_rels(root)
    with Injector(root) as base_run:
        baseline = function(root)
    names = {f.rel for f in baseline.files}
    violations = []
    runs = 0
    for index in range(base_run.count):
        for kind in FAILURES:
            runs += 1
            with Injector(root, index, kind) as run:
                try:
                    result, raised = function(root), None
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
            got = {f.rel for f in result.files}
            if not got <= names:
                violations.append(f"{where}: 失敗を入れない実行にないファイルを返した {sorted(got - names)}")
            missing = names - got
            place = run.failed[1]
            if kind == "denied":
                notices = result.unlistable + result.unknown
                if not notices:
                    violations.append(f"{where}: 知らせを出さなかった")
                uncovered = [rel for rel in missing if not covered(rel, notices)]
                if uncovered:
                    violations.append(f"{where}: 知らせのないまま減った {sorted(uncovered)}")
            else:  # absent
                # なくなった場所の下か、その場所を先や比べる相手にしていたジャンクションの下だけが減ってよい。
                allowed = ([place] if place is not None else []) + junctions
                uncovered = [rel for rel in missing if not covered(rel, allowed)]
                if uncovered:
                    violations.append(f"{where}: なくなった場所の外のファイルが減った {sorted(uncovered)}")
                if result.unlistable or result.unknown:
                    violations.append(f"{where}: ないだけなのに、知らせを出した")
    print(f"  {label}: OS の呼び出し {base_run.count} 回、失敗を入れた実行 {runs} 回、破られた決まり {len(violations)} 件")
    return violations


# 対照: わざと決まりを破った実装。探索が、破れを見つけることを確かめる。


def control_swallow_all(root):
    """どの OSError も、ないことにする（計画の 1 版目の試作と同じ誤り）。"""
    original = globals()["read_os"]

    def swallow(call, *args, **kwargs):
        try:
            return "ok", call(*args, **kwargs)
        except OSError:
            return "absent", None
    globals()["read_os"] = swallow
    try:
        return walk_pages(root)
    finally:
        globals()["read_os"] = original


def control_string_fallback(root):
    """循環の検出で、比べるための stat の失敗を、文字列の比較に落とす（2 版目の最初の試作と同じ誤り）。"""
    original = globals()["cycles"]

    def fallback(target, directories):
        for directory in directories:
            here = directory
            while True:
                try:
                    a, b = os.stat(target), os.stat(here)
                    same = (a.st_dev, a.st_ino) == (b.st_dev, b.st_ino) if a.st_ino and b.st_ino else None
                except (FileNotFoundError, NotADirectoryError, PermissionError):
                    same = None
                if same is None:
                    same = os.path.normcase(target) == os.path.normcase(here)
                if same:
                    return "ok", True
                parent = os.path.dirname(here)
                if parent == here:
                    break
                here = parent
        return "ok", False
    globals()["cycles"] = fallback
    try:
        return walk_pages(root)
    finally:
        globals()["cycles"] = original


def control_silent_denied(root):
    """権限のない場所を、知らせずに飛ばす。"""
    found = walk_pages(root)
    return Walk(found.files, [], [])


def control_pathlib(root):
    """今の実装と同じく、rglob と Path.is_file() で集める（OS の呼び出しに手が届かない）。"""
    files = []
    for rel in v1.old_iter_page_files(Path(root)):
        st = (Path(root) / rel).stat()
        files.append(MdFile(rel, st.st_size, st.st_mtime_ns))
    return Walk(files, [], [])


def cmd_explore(work):
    base, trees = make_trees(work)
    ok = True
    for label, wiki in trees:
        if label in ("indexes がファイル", "空の wiki"):
            continue
        for name, function in (("ページ", walk_pages), ("索引", walk_index_files)):
            found = explore(wiki, function, f"{label}、{name}")
            ok = ok and not found
            for line in found[:5]:
                print("    ", line)
    label, wiki = trees[0]
    print("  対照（破られた決まりが 1 件以上あれば、探索が働いている）:")
    controls = [("どの失敗もないことにする", control_swallow_all), ("権限を知らせずに飛ばす", control_silent_denied)]
    if os.name == "nt":
        controls.append(("比べるための stat の失敗を、文字列の比較に落とす", control_string_fallback))
    for name, function in controls:
        found = explore(wiki, function, f"対照「{name}」")
        ok = ok and bool(found)
        for line in found[:2]:
            print("    ", line)
    # 参考: 今の実装（rglob と Path.is_file()）に同じ探索をかける。pathlib は版によって os.scandir と os.stat を
    # 通らないので、手が届かないことがある。結果は合否に入れない。
    print("  参考（今の実装に同じ探索をかける。合否に入れない）:")
    try:
        found = explore(wiki, control_pathlib, "今の実装（rglob と Path.is_file()）")
        for line in found[:3]:
            print("    ", line)
    except Exception as exc:  # noqa: BLE001 今の実装がどう壊れるかを見る
        print(f"  今の実装（rglob と Path.is_file()）: 探索の途中で {type(exc).__name__}（差し替えた項目を pathlib が扱えない）")
    v1.remove_tree(base)
    return ok


if __name__ == "__main__":
    for stream in (sys.stdout, sys.stderr):
        stream.reconfigure(encoding="utf-8")
    print(f"python {sys.version.split()[0]} {sys.platform}  {sys.argv[1]}")
    if sys.argv[1] == "wikis":
        done = all([compare(p) for p in sys.argv[2:]])
    else:
        done = {"compare": cmd_compare, "explore": cmd_explore}[sys.argv[1]](sys.argv[2])
    print("  終了:", "よい" if done else "だめ")
    sys.exit(0 if done else 1)
