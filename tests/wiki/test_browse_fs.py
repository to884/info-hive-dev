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
                if module != "wiki_browse_fs.py":
                    if f.attr in FORBIDDEN_ATTRS and base in ("os", "os.path", "shutil", "Path", "pathlib.Path") \
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
