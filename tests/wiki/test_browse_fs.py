"""閲覧（browse）のファイルの入出力の層（wiki_browse_fs.py）の試験。

設計は `docs/plans/wiki-browse-structure-2026-11-11.md` の 3（入出力の層）、6（書く側）、7.1（サーバーの記録）、
9（試験）。層の口の決まり、失敗の読み替え、Wiki のルートと重ならないことの確かめ、領分の扱い、門を確かめる。
口の呼び出しの N 回目に手を入れる探索は、browse_sweep.py にある。ここでは、少しの状態と対照だけを流す
（全量は `python -X utf8 tests/wiki/browse_sweep.py` で、数時間かかる）。

ジャンクションの試験は Windows だけ、シンボリックリンクの試験は作れる環境だけで流す。

実行（標準ライブラリだけで動く）:
    python -X utf8 -m unittest tests/wiki/test_browse_fs.py -v
"""
from __future__ import annotations

import ast
import errno
import os
import stat
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
SCRIPTS = ROOT / "info-hive-wiki/skills/info-hive/scripts"
sys.path.insert(0, str(SCRIPTS))
sys.path.insert(0, str(HERE))
sys.dont_write_bytecode = True

import browse_sandbox as bs  # noqa: E402
import browse_sweep as sweep  # noqa: E402
import wiki_browse_fs as fs  # noqa: E402

MODULES = ("wiki_browse.py", "wiki_browse_core.py", "wiki_browse_fs.py")


def can_symlink(base: Path) -> bool:
    try:
        (base / ".probe-target").write_text("x", encoding="utf-8")
        os.symlink(base / ".probe-target", base / ".probe-link")
        os.unlink(base / ".probe-link")
        return True
    except (OSError, NotImplementedError):
        return False
    finally:
        try:
            (base / ".probe-target").unlink()
        except OSError:
            pass


# ---------------------------------------------------------------------------
# 3.4: 口の一覧にない入出力と、一覧にない OSError の受け口がないこと
# ---------------------------------------------------------------------------

# 層の外の 2 つのモジュールが呼んではならない入出力（属性の名前）。os と pathlib の入出力、組み込みの open。
FORBIDDEN_ATTRS = {
    "open", "read_text", "read_bytes", "write_text", "write_bytes", "exists", "is_file", "is_dir", "is_symlink",
    "iterdir", "rglob", "glob", "mkdir", "rmdir", "unlink", "rename", "replace", "stat", "lstat", "chmod",
    "resolve", "scandir", "listdir", "walk", "makedirs", "removedirs", "remove", "realpath", "lexists", "isfile",
    "isdir", "islink", "samefile", "touch", "symlink", "link", "truncate", "rmtree", "copytree", "copy", "copy2",
    "move", "utime", "access", "fdopen", "readlink",
}
# 受け手を問わずに、層の外で呼んではならない入出力のメソッドの名前（pathlib.Path と DirEntry のもの）。変数に入れた
# Path でも見つける（実装の 1 回目のレビューの軽微）。中核のメソッドや str と名前が重なる resolve と stat は、
# 引数のない呼び出しだけを数える。
ANY_RECEIVER = {
    "read_text", "read_bytes", "write_text", "write_bytes", "is_file", "is_dir", "is_symlink", "is_junction",
    "exists", "iterdir", "rglob", "glob", "mkdir", "rmdir", "unlink", "touch", "lstat", "chmod", "samefile",
    "readlink", "symlink_to", "hardlink_to",
}
# 層の外の 2 つのモジュールが呼んでよい os の関数（入出力をしない、純粋なもの）。ここにない os の呼び出しは、
# どれも違反にする（実装の 4 回目のレビューの軽微。禁じる名前を数え上げると、os.read などが漏れる）
PURE_OS_CALLS = {
    "os.fspath", "os.environ.get", "os.path.join", "os.path.dirname", "os.path.basename", "os.path.abspath",
    "os.path.expanduser", "os.path.normcase", "os.path.splitext", "os.path.relpath",
}
# 口（層）の中だけで呼んでよい os の入出力の関数（設計の 3.1 の口の一覧）。
LAYER_OS_CALLS = {
    "lstat", "stat", "scandir", "mkdir", "open", "read", "write", "close", "rename", "replace", "unlink",
    "rmdir", "fstat", "lseek", "chmod", "ftruncate",
}
# OSError を受けてよい箇所（設計の 3.2）: (モジュール, 関数)。層の読み替えの関数と、閉じる・ロックを離す口、
# 通信（サーバーへの問い合わせ、ブラウザとの接続、標準入出力）、要求の境界とコマンドの出口。
OSERROR_ALLOWED = {
    ("wiki_browse_fs.py", "_win_open"), ("wiki_browse_fs.py", "open_lock"), ("wiki_browse_fs.py", "try_lock"),
    ("wiki_browse_fs.py", "x"), ("wiki_browse_fs.py", "_close"), ("wiki_browse_fs.py", "kind"),
    ("wiki_browse_fs.py", "release"), ("wiki_browse_fs.py", "lock_held"), ("wiki_browse_fs.py", "walk_inputs"),
    ("wiki_browse.py", "say"), ("wiki_browse.py", "_route"), ("wiki_browse.py", "send_error"),
    ("wiki_browse.py", "_live_status"), ("wiki_browse.py", "_locate"), ("wiki_browse.py", "_emit"),
    ("wiki_browse.py", "stop"), ("wiki_browse.py", "_print_json"), ("wiki_browse.py", "_exit_for"),
    ("wiki_browse.py", "_final_flush"),
}
OSERROR_NAMES = {"OSError", "IOError", "EnvironmentError", "PermissionError", "FileNotFoundError",
                 "FileExistsError", "NotADirectoryError", "IsADirectoryError", "BlockingIOError",
                 "InterruptedError", "ConnectionError", "BrokenPipeError", "TimeoutError"}


def io_violations(source: str, module: str) -> list:
    """モジュールの構文木をたどり、口の一覧にない入出力の呼び出しと、一覧にない OSError の受け口を返す。"""
    tree = ast.parse(source)
    found = []
    stack = []

    class V(ast.NodeVisitor):
        def visit_FunctionDef(self, node):
            stack.append(node.name)
            self.generic_visit(node)
            stack.pop()

        visit_AsyncFunctionDef = visit_FunctionDef

        def visit_Call(self, node):
            f = node.func
            where = f"{module}:{node.lineno}"
            if isinstance(f, ast.Name) and f.id == "open":
                found.append(f"{where} 組み込みの open")
            if isinstance(f, ast.Attribute):
                base = ast.unparse(f.value)
                full = ast.unparse(f)
                if module != "wiki_browse_fs.py" and "(" not in full \
                        and (full.startswith("os.") or full.startswith("shutil.")) \
                        and full not in PURE_OS_CALLS:
                    found.append(f"{where} {full}")
                if module != "wiki_browse_fs.py" and base not in ("fs", "wiki_browse_fs"):
                    if f.attr in ANY_RECEIVER or (f.attr in ("resolve", "stat") and not node.args
                                                  and not node.keywords):
                        found.append(f"{where} {base}.{f.attr}")
                    elif f.attr in FORBIDDEN_ATTRS and base in ("os", "os.path", "shutil", "Path", "pathlib.Path") \
                            or (f.attr in FORBIDDEN_ATTRS and isinstance(f.value, ast.Call)
                                and ast.unparse(f.value.func) in ("Path", "pathlib.Path")):
                        found.append(f"{where} {base}.{f.attr}")
                else:
                    in_os = stack and stack[0] in ("Os",) or (len(stack) > 1 and stack[0] == "Os")
                    if base == "os" and f.attr in LAYER_OS_CALLS and not in_os and stack[-1:] != ["_win_open"]:
                        found.append(f"{where} 口の外の os.{f.attr}")
                    if base in ("shutil", "Path", "pathlib.Path") or f.attr in ("rmtree", "read_text", "write_text"):
                        found.append(f"{where} {base}.{f.attr}")
            self.generic_visit(node)

        def visit_Name(self, node):
            # 層の外の 2 つのモジュールは、Path を持たない（PurePath と PurePosixPath だけを使う）。メソッドの名前で
            # 入出力を数え上げると、Path の入出力のすべてを見つけられない（実装の 2 回目のレビューの軽微）。持たな
            # ければ、Path のどの入出力も呼べない
            if module != "wiki_browse_fs.py" and node.id in ("Path", "WindowsPath", "PosixPath"):
                found.append(f"{module}:{node.lineno} Path を持つ")
            self.generic_visit(node)

        def visit_Import(self, node):
            # pathlib を丸ごと取り込むと、別名でも Path に届く。層の外では取り込まない
            if module != "wiki_browse_fs.py" and any(a.name == "pathlib" for a in node.names):
                found.append(f"{module}:{node.lineno} pathlib を取り込む")
            self.generic_visit(node)

        def visit_ImportFrom(self, node):
            # pathlib から取り込んでよいのは、入出力を持たない純粋なパスだけである。別名でも見つける
            # （実装の 3 回目のレビューの軽微）
            if module != "wiki_browse_fs.py" and node.module == "pathlib":
                for a in node.names:
                    if a.name not in ("PurePath", "PurePosixPath", "PureWindowsPath"):
                        found.append(f"{module}:{node.lineno} pathlib から {a.name} を取り込む")
            self.generic_visit(node)

        def visit_Attribute(self, node):
            if module != "wiki_browse_fs.py" and node.attr in ("Path", "WindowsPath", "PosixPath") \
                    and ast.unparse(node.value) == "pathlib":
                found.append(f"{module}:{node.lineno} pathlib.Path を持つ")
            self.generic_visit(node)

        def visit_ClassDef(self, node):
            stack.append(node.name)
            self.generic_visit(node)
            stack.pop()

        def visit_ExceptHandler(self, node):
            names = set()
            if node.type is not None:
                for n in ast.walk(node.type):
                    if isinstance(n, ast.Name):
                        names.add(n.id)
                    elif isinstance(n, ast.Attribute):
                        names.add(n.attr)
            if names & OSERROR_NAMES:
                func = next((s for s in reversed(stack) if s[:1].islower() or s.startswith("_")), "<module>")
                if (module, func) not in OSERROR_ALLOWED:
                    found.append(f"{module}:{node.lineno} 一覧にない OSError の受け口（{func}）")
            self.generic_visit(node)

    V().visit(tree)
    return found


class LayerContractTest(unittest.TestCase):
    """設計の 3.4。違反を 1 つ埋めた写しで、この試験が失敗することも確かめる（対照）。"""

    def test_no_io_outside_the_layer(self):
        found = []
        for name in MODULES:
            found += io_violations((SCRIPTS / name).read_text(encoding="utf-8"), name)
        self.assertEqual(found, [])

    def test_control_copies_fail(self):
        core = (SCRIPTS / "wiki_browse_core.py").read_text(encoding="utf-8")
        browse = (SCRIPTS / "wiki_browse.py").read_text(encoding="utf-8")
        layer = (SCRIPTS / "wiki_browse_fs.py").read_text(encoding="utf-8")
        controls = (
            (core + "\n\ndef leak(p):\n    return Path(p).read_text()\n", "wiki_browse_core.py"),
            (core + "\n\ndef leak(p):\n    return open(p).read()\n", "wiki_browse_core.py"),
            (core + "\n\ndef leak():\n    p = Path('x')\n    return p.read_text(encoding='utf-8')\n",
             "wiki_browse_core.py"),
            (browse + "\n\ndef leak(root):\n    return root.resolve()\n", "wiki_browse.py"),
            (browse + "\n\nfrom pathlib import Path\n\ndef leak(p):\n    return Path(p).open()\n", "wiki_browse.py"),
            (browse + "\n\nfrom pathlib import Path as P\n\ndef leak(p):\n    return P(p).open()\n", "wiki_browse.py"),
            (core + "\n\ndef leak(fd):\n    return os.read(fd, 1024)\n", "wiki_browse_core.py"),
            (browse + "\n\ndef leak(fd, data):\n    return os.write(fd, data)\n", "wiki_browse.py"),
            (core + "\n\nimport pathlib as pl\n\ndef leak(p):\n    return pl.Path(p).open()\n", "wiki_browse_core.py"),
            (core + "\n\nimport pathlib\n\ndef leak(p):\n    q = pathlib.Path(p)\n    return q.stat(follow_symlinks=False)\n",
             "wiki_browse_core.py"),
            (browse + "\n\ndef leak(p):\n    return os.path.isfile(p)\n", "wiki_browse.py"),
            (browse + "\n\ndef leak():\n    try:\n        pass\n    except OSError:\n        pass\n", "wiki_browse.py"),
            (layer + "\n\ndef leak(p):\n    return os.lstat(p)\n", "wiki_browse_fs.py"),
            (layer + "\n\ndef leak():\n    try:\n        pass\n    except PermissionError:\n        return None\n",
             "wiki_browse_fs.py"),
        )
        for source, name in controls:
            self.assertTrue(io_violations(source, name), name)


# ---------------------------------------------------------------------------
# 3.2: 失敗の読み替え
# ---------------------------------------------------------------------------

class ClassifyTest(unittest.TestCase):
    def test_absent_and_unknown(self):
        self.assertIs(fs.classify(FileNotFoundError(errno.ENOENT, "x")), fs.Absent)
        self.assertIs(fs.classify(NotADirectoryError(errno.ENOTDIR, "x")), fs.Absent)
        self.assertIs(fs.classify(OSError(errno.ELOOP, "loop")), fs.Absent)
        self.assertIs(fs.classify(PermissionError(errno.EACCES, "x")), fs.Unknown)
        self.assertIs(fs.classify(OSError(errno.EBADF, "x")), fs.Unknown)
        self.assertIs(fs.classify(OSError(errno.EIO, "x")), fs.Unknown)
        if os.name == "nt":
            self.assertIs(fs.classify(OSError(None, "x", "p", 1921)), fs.Absent)    # 解けないリンク
            self.assertIs(fs.classify(OSError(None, "x", "p", 123)), fs.Absent)     # 正しくない名前
            self.assertIs(fs.classify(OSError(None, "x", "p", 21)), fs.Unknown)     # 準備のできていないドライブ

    def test_failure_keeps_the_call_and_path(self):
        with tempfile.TemporaryDirectory() as d:
            with self.assertRaises(fs.Absent) as cm:
                fs.x("lstat", os.path.join(d, "missing"))
        self.assertIn("lstat", str(cm.exception))
        self.assertTrue(cm.exception.path.endswith("missing"))
        self.assertIs(cm.exception.os_error, FileNotFoundError)

    def test_zero_identifier_is_unknown(self):
        class Zero(fs.Os):
            def file_id(self, path):
                real = fs.Os.file_id(self, path)
                return (real[0], bytes(16)) if fs.NT else (real[0], 0)
        saved = fs.X
        fs.X = Zero()
        try:
            with tempfile.TemporaryDirectory() as d:
                with self.assertRaises(fs.Unknown):
                    fs.ident(d)
        finally:
            fs.X = saved


# ---------------------------------------------------------------------------
# 6.1、6.2: 書き込みの口と領分
# ---------------------------------------------------------------------------

class WriteGuardTest(unittest.TestCase):
    def setUp(self):
        self._tmp = tempfile.TemporaryDirectory()
        self.base = Path(os.path.realpath(self._tmp.name))
        self.wiki = self.base / "wiki"
        (self.wiki / "concepts").mkdir(parents=True)
        (self.wiki / "concepts" / "a.md").write_text("# a\n", encoding="utf-8")
        fs.G = fs.Guard(self.wiki)
        fs.WARNINGS.clear()

    def tearDown(self):
        fs.G = fs.Guard(None)
        self._tmp.cleanup()

    def test_no_write_under_the_wiki_root(self):
        before = bs.tree(str(self.wiki))
        for call in (lambda: fs.w("mkdir", str(self.wiki / "x")),
                     lambda: fs.create_file(str(self.wiki / "concepts" / "b.md"), b"x"),
                     lambda: fs.w("unlink", str(self.wiki / "concepts" / "a.md")),
                     lambda: fs.w("rmdir", str(self.wiki))):
            with self.assertRaises(fs.Stop):
                call()
        self.assertEqual(bs.tree(str(self.wiki)), before)

    def test_root_and_its_ancestors_are_not_moved(self):
        with self.assertRaises(fs.Stop):
            fs.w("rename", str(self.base), str(self.base) + "-moved")

    def test_absent_parent_is_not_a_safe_answer(self):
        # 「ない」の答えから、あとの書き込みが安全だと決めない。親がなければ失敗する（設計の 6.1）
        with self.assertRaises(fs.Absent):
            fs.w("mkdir", str(self.base / "no" / "x"))

    def test_lock_name_link_is_removed_not_followed(self):
        if not can_symlink(self.base):
            self.skipTest("シンボリックリンクを作れない")
        work = self.base / "site.browse-work"
        work.mkdir()
        (work / fs.WORK_MARKER).write_text("", encoding="utf-8")
        os.symlink(self.wiki / "created.md", work / "build.lock")      # 先のないリンク
        lock = fs.Lock(str(work / "build.lock"))
        self.assertTrue(lock.try_acquire())
        lock.release()
        self.assertFalse((self.wiki / "created.md").exists())
        self.assertFalse(os.path.islink(work / "build.lock"))
        self.assertTrue((work / "build.lock").is_file())

    def test_open_lock_does_not_follow_the_last_name(self):
        # 種類の答えが誤っていても、ロックの口はリンクを開かずに失敗し、先を作らない（設計の 3.1、6.2）
        if not can_symlink(self.base):
            self.skipTest("シンボリックリンクを作れない")
        link = self.base / "x.lock"
        os.symlink(self.wiki / "created.md", link)
        with self.assertRaises((fs.Unknown, fs.Absent)):
            fs.x("open_lock", str(link))
        with self.assertRaises((fs.Unknown, fs.Absent)):
            fs.x("open_excl", str(link))
        self.assertFalse((self.wiki / "created.md").exists())

    def test_remove_tree_unlinks_links_and_keeps_targets(self):
        work = self.base / "w"
        (work / "d").mkdir(parents=True)
        (work / "d" / "f.txt").write_text("x", encoding="utf-8")
        made = False
        if os.name == "nt":
            bs.junction(str(work / "d" / "j"), str(self.wiki))
            made = True
        elif can_symlink(self.base):
            os.symlink(self.wiki, work / "d" / "j", target_is_directory=True)
            made = True
        before = bs.tree(str(self.wiki))
        fs.remove_tree(str(work))
        self.assertFalse(work.exists())
        self.assertEqual(bs.tree(str(self.wiki)), before)
        self.assertTrue(made or True)

    def test_read_only_file_is_not_chmodded(self):
        work = self.base / "w"
        work.mkdir()
        f = work / "ro.txt"
        f.write_text("x", encoding="utf-8")
        os.chmod(f, stat.S_IREAD)
        try:
            if os.name == "nt":
                with self.assertRaises(fs.Unknown):
                    fs.remove_tree(str(work))
                self.assertFalse(os.stat(f).st_mode & stat.S_IWRITE)
        finally:
            os.chmod(f, stat.S_IWRITE | stat.S_IREAD)

    def test_unmarked_nonempty_territory_is_not_used(self):
        d = self.base / "x.browse-work"
        d.mkdir()
        (d / "mine.txt").write_text("x", encoding="utf-8")
        with self.assertRaises(fs.Stop):
            fs.use_territory(str(d), fs.WORK_MARKER, lock_name="build.lock")
        self.assertEqual(sorted(p.name for p in d.iterdir()), ["mine.txt"])

    def test_root_name_link_is_not_entered(self):
        if os.name != "nt" and not can_symlink(self.base):
            self.skipTest("リンクを作れない")
        data = self.base / "data"
        data.mkdir()
        elsewhere = self.base / "elsewhere"
        elsewhere.mkdir()
        bs.junction(str(data / "browse"), str(elsewhere))
        with self.assertRaises(fs.Stop):
            fs.enter_root(str(data / "browse"), create=True)
        with self.assertRaises(fs.Stop):
            fs.enter_root(str(data / "browse"), create=False)
        self.assertEqual(list(elsewhere.iterdir()), [])


class SecondReviewTest(unittest.TestCase):
    """実装の 2 回目のレビューの指摘（docs/agent-runs/2026-11-14-wiki-browse-structure-impl/impl-review-2.md）。"""

    def setUp(self):
        self._tmp = tempfile.TemporaryDirectory()
        self.base = Path(os.path.realpath(self._tmp.name))
        self.wiki = self.base / "wiki"
        self.wiki.mkdir()
        (self.wiki / "SCHEMA.md").write_text("# s\n", encoding="utf-8")
        self.owner = fs.owner_of(self.wiki)
        fs.WARNINGS.clear()

    def tearDown(self):
        fs.WARNINGS.clear()
        self._tmp.cleanup()

    def build(self, out, browse_root, files=None):
        return fs.build(str(self.wiki), str(out), files or {"index.html": b"x"}, False, self.owner,
                        str(browse_root))

    def test_out_that_is_the_planned_data_dir_is_refused_before_creating(self):
        before = bs.tree(str(self.base))
        for out, root in ((self.base / "newdata", self.base / "newdata" / "browse"),
                          (self.base / "newdata2" / "browse", self.base / "newdata2" / "browse")):
            with self.subTest(out=out.name):
                with self.assertRaises((fs.Stop, fs.Absent)):   # 親がなければ「ない」で止まる（0.10.0 と同じ）
                    self.build(out, root)
                self.assertEqual(bs.tree(str(self.base)), before)
        # 親はあり、--out が、まだない <data_dir> の下の browse そのもの
        (self.base / "newdata3").mkdir()
        before = bs.tree(str(self.base))
        with self.assertRaises(fs.Stop):
            self.build(self.base / "newdata3" / "browse", self.base / "newdata3" / "browse")
        self.assertEqual(bs.tree(str(self.base)), before)

    def test_failure_after_commit_is_a_warning(self):
        # 片付けが、Wiki のルートの祖先を動かそうとして止まる（書き込みの守りの Stop）。新しい世代は書き出してあるので、
        # 0 で終わり、警告を出す
        out = self.base / "site"
        work = self.base / "site.browse-work"
        (work / "old-5" / "wiki").mkdir(parents=True)
        (work / fs.WORK_MARKER).write_text("", encoding="utf-8")
        inner_wiki = work / "old-5" / "wiki"
        (inner_wiki / "SCHEMA.md").write_text("# s\n", encoding="utf-8")
        rc = fs.build(str(inner_wiki), str(out), {"index.html": b"x"}, False, fs.owner_of(inner_wiki),
                      str(self.base / "data" / "browse"))
        self.assertEqual(rc, 0)
        self.assertTrue((out / "index.html").is_file())
        self.assertTrue(inner_wiki.is_dir())
        self.assertTrue(fs.WARNINGS, fs.WARNINGS)

    def test_closed_stdout_after_commit_is_a_warning(self):
        class Closed(fs.Os):
            def stdout_write(self, text):
                raise ValueError("I/O operation on closed file.")
        saved, fs.X = fs.X, Closed()
        try:
            rc = fs.build(str(self.wiki), str(self.base / "site"), {"index.html": b"x"}, False, self.owner,
                          str(self.base / "data" / "browse"), report_text="{}\n")
        finally:
            fs.X = saved
        self.assertEqual(rc, 0)
        self.assertTrue(any("知らせを出せなかった" in w for w in fs.WARNINGS), fs.WARNINGS)

    def test_finish_rechecks_the_state_dir(self):
        # サーバーが動いているあいだに、状態のディレクトリの名前が利用者のディレクトリへのリンクに置き換わっても、
        # 終了は、その先の利用者のファイルを消さない（設計の 7.1）
        root = self.base / "data" / "browse"
        state = root / "KEY.server"
        outcome, server = fs.serve_start(str(self.wiki), str(root), str(state), self.owner,
                                         lambda: {"instance": "x"})
        self.assertEqual(outcome, "started")
        user = self.base / "user"
        user.mkdir()
        (user / "server.json").write_text("mine", encoding="utf-8")
        server.lock.release()
        os.rename(state, self.base / "moved")
        try:
            bs.link_dir("junction" if os.name == "nt" else "symlink", str(state), str(user))
        except OSError:
            self.skipTest("リンクを作れない")
        server.lock.fd = None
        fs.serve_finish(server)
        self.assertEqual((user / "server.json").read_text(encoding="utf-8"), "mine")
        self.assertTrue(any("記録を消せなかった" in w for w in fs.WARNINGS), fs.WARNINGS)

    def test_unnumbered_names_in_work_are_kept(self):
        out = self.base / "site"
        work = self.base / "site.browse-work"
        work.mkdir()
        (work / fs.WORK_MARKER).write_text("", encoding="utf-8")
        for name in ("tmp-not-a-number", "old-x", "del-"):
            (work / name).mkdir()
        self.assertEqual(self.build(out, self.base / "data" / "browse"), 0)
        self.assertEqual(sorted(p.name for p in work.iterdir()),
                         sorted([fs.WORK_MARKER, "build.lock", "tmp-not-a-number", "old-x", "del-"]))


class ThirdReviewTest(unittest.TestCase):
    """実装の 3 回目のレビューの指摘（docs/agent-runs/2026-11-14-wiki-browse-structure-impl/impl-review-3.md）。"""

    def setUp(self):
        self._tmp = tempfile.TemporaryDirectory()
        self.base = Path(os.path.realpath(self._tmp.name))
        self.wiki = self.base / "wiki"
        self.wiki.mkdir()
        (self.wiki / "SCHEMA.md").write_text("# s\n", encoding="utf-8")
        self.owner = fs.owner_of(self.wiki)
        fs.WARNINGS.clear()

    def tearDown(self):
        fs.WARNINGS.clear()
        self._tmp.cleanup()

    def test_data_dir_inside_a_generation_is_refused(self):
        site = self.base / "site"
        files = {"index.html": b"x"}
        self.assertEqual(fs.build(str(self.wiki), str(site), files, False, self.owner,
                                  str(self.base / "base-data" / "browse")), 0)
        before = bs.tree(str(self.base))
        inner_root = site / "data" / "browse"
        with self.assertRaises(fs.Stop):         # 既定の書き出し（データの場所が、ほかの世代の中）
            fs.build(str(self.wiki), str(inner_root / "KEY"), files, True, self.owner, str(inner_root))
        with self.assertRaises(fs.Stop):         # 起動も同じ
            fs.serve_start(str(self.wiki), str(inner_root), str(inner_root / "KEY.server"), self.owner,
                           lambda: {"instance": "x"})
        self.assertEqual(bs.tree(str(self.base)), before)
        # 前の世代は、次の書き出しでも門を通る
        self.assertEqual(fs.build(str(self.wiki), str(site), files, False, self.owner,
                                  str(self.base / "base-data" / "browse")), 0)

    def test_failed_final_flush_keeps_exit_zero(self):
        # 標準出力の読み手が閉じていても、公開したあとなら終了コードは 0（Python の終わるときのフラッシュで 120 に
        # ならない。設計の 7）
        out = self.base / "site"
        code = (
            "import os, sys\n"
            f"sys.path.insert(0, {str(SCRIPTS)!r})\n"
            "r, w = os.pipe()\n"
            "os.close(r)\n"
            "sys.stdout = open(w, 'w', encoding='utf-8', buffering=1 << 16)\n"
            "import wiki_browse\n"
            f"sys.exit(wiki_browse.main(['build', {str(self.wiki)!r}, '--out', {str(out)!r}]))\n"
        )
        env = dict(os.environ, INFO_HIVE_DATA_DIR=str(self.base / "data"), PYTHONUTF8="1")
        p = subprocess.run([sys.executable, "-X", "utf8", "-B", "-c", code], capture_output=True, text=True,
                           encoding="utf-8", errors="replace", env=env, timeout=120)
        self.assertEqual(p.returncode, 0, p.stderr)
        self.assertTrue((out / "index.html").is_file())


class FourthReviewTest(unittest.TestCase):
    """実装の 4 回目のレビューの指摘（docs/agent-runs/2026-11-14-wiki-browse-structure-impl/impl-review-4.md）。"""

    def setUp(self):
        self._tmp = tempfile.TemporaryDirectory()
        self.base = Path(os.path.realpath(self._tmp.name))
        self.wiki = self.base / "wiki"
        self.wiki.mkdir()
        (self.wiki / "SCHEMA.md").write_text("# s\n", encoding="utf-8")
        self.owner = fs.owner_of(self.wiki)
        fs.WARNINGS.clear()

    def tearDown(self):
        fs.WARNINGS.clear()
        self._tmp.cleanup()

    def test_data_root_that_is_a_generation_is_refused(self):
        gen = self.base / "browse"
        files = {"index.html": b"x"}
        self.assertEqual(fs.build(str(self.wiki), str(gen), files, False, self.owner,
                                  str(self.base / "base-data" / "browse")), 0)
        before = bs.tree(str(self.base))
        with self.assertRaises(fs.Stop):         # 起動（データの場所の根そのものが、ほかの世代）
            fs.serve_start(str(self.wiki), str(gen), str(gen / "KEY.server"), self.owner, lambda: {"instance": "x"})
        with self.assertRaises(fs.Stop):         # 既定の書き出し
            fs.build(str(self.wiki), str(gen / "KEY"), files, True, self.owner, str(gen))
        self.assertEqual(bs.tree(str(self.base)), before)
        # 状態のディレクトリそのものが、ほかの browse のディレクトリ（世代）
        root = self.base / "data" / "browse"
        self.assertEqual(fs.build(str(self.wiki), str(root / "KEY"), files, True, self.owner, str(root)), 0)
        with self.assertRaises(fs.Stop):
            fs.serve_start(str(self.wiki), str(root), str(root / "KEY"), self.owner, lambda: {"instance": "x"})

    def test_closed_stderr_keeps_exit_zero(self):
        out = self.base / "site"
        (self.wiki / "concepts").mkdir()
        # ページの本文に絶対パスがあるので、公開のあとに警告を出す
        (self.wiki / "concepts" / "a.md").write_text(f"# a\n\n`{self.base}`\n", encoding="utf-8")
        code = (
            "import os, sys\n"
            f"sys.path.insert(0, {str(SCRIPTS)!r})\n"
            "r, w = os.pipe()\n"
            "os.close(r)\n"
            "sys.stderr = open(w, 'w', encoding='utf-8', buffering=1 << 16)\n"
            "import wiki_browse\n"
            f"sys.exit(wiki_browse.main(['build', {str(self.wiki)!r}, '--out', {str(out)!r}]))\n"
        )
        env = dict(os.environ, INFO_HIVE_DATA_DIR=str(self.base / "data"), PYTHONUTF8="1")
        p = subprocess.run([sys.executable, "-X", "utf8", "-B", "-c", code], capture_output=True, text=True,
                           encoding="utf-8", errors="replace", env=env, timeout=120)
        self.assertEqual(p.returncode, 0, p.stdout)
        self.assertTrue((out / "index.html").is_file())

    def test_remove_record_failure_is_a_warning(self):
        def failing(*a, **k):
            raise fs.failure(fs.Unknown, "scandir_open: PermissionError", "x")
        saved = fs._enter_state
        fs._enter_state = failing
        try:
            fs.remove_record(str(self.wiki), str(self.base / "data" / "browse"), str(self.base / "s"), self.owner,
                             "i")
        finally:
            fs._enter_state = saved
        self.assertTrue(any("記録を消せなかった" in w for w in fs.WARNINGS), fs.WARNINGS)


# ---------------------------------------------------------------------------
# 9.3、9.5: 手早い探索と対照（全量は browse_sweep.py）
# ---------------------------------------------------------------------------

QUICK_CASES = (("absent", "asis", False), ("gen", "leftovers", True), ("browse-junction", "asis", False))
QUICK_MODES = ("denied", "crash")
# 失敗のない実行か、1 種の失敗で見つかる対照だけ（ほかの対照は browse_sweep.py の全量で確かめる）
QUICK_CONTROLS = {"skip_gate": (), "no_root_guard": (), "enter_root_unchecked": (), "recover_unchecked": (),
                  "swallow_close": ("denied",), "follow_on_open": ("absent",)}


class QuickSweepTest(unittest.TestCase):
    def test_quick_states_hold(self):
        for case in QUICK_CASES:
            with self.subTest(case=case):
                _total, runs, problems = sweep.sweep_build(*case, QUICK_MODES)
                self.assertEqual(problems[:3], [])
                if not sweep.SKIPPED:
                    self.assertGreater(runs, 0)

    def test_read_side_holds(self):
        # 走査、入力の読み取り、解釈の入口にも手を入れる（実装の 1 回目のレビューの重大 4）
        try:
            import browse_read_sweep as rs
        except ImportError as e:      # 中核は同梱の markdown-it を読み込む。PyYAML は要らない
            self.skipTest(f"読む側の探索を読み込めない: {e}")
        runs, problems = rs.sweep_read("absent", ("denied", "raise"), only_roles=("walk", "read:", "assets", "parse"))
        self.assertGreater(runs, 0)
        self.assertEqual(problems[:3], [])

    def test_server_states_hold(self):
        runs, problems = sweep.sweep_server_root(("denied",))
        self.assertEqual(problems[:3], [])

    def test_controls_are_found(self):
        for mutant in QUICK_CONTROLS:
            with self.subTest(mutant=mutant):
                cases = sweep.CONTROLS[mutant][:1]
                fs.MUTANTS.add(mutant)
                try:
                    found = []
                    for case in cases:
                        found += sweep.sweep_build(*case, QUICK_CONTROLS[mutant])[2]
                finally:
                    fs.MUTANTS.discard(mutant)
                if any(case[1] in bs.LINK_STATES + bs.ENTRY_LINK or case[0] in bs.ROOT_LINK for case in cases) \
                        and sweep.SKIPPED:
                    continue
                self.assertTrue(found, mutant)


if __name__ == "__main__":
    unittest.main()
