"""閲覧（browse）の書き込みの守り（wiki_browse_fs.py）の試験。

設計は `docs/plans/wiki-browse-stage1-2026-11-09.md` の 6（守ること 1）。守る場所の中への書き込みを、
パスの文字ではなく実体で見つけて止めること、ファイルをその場で書き換えないこと、リンクをたどって消さないこと、
browse のディレクトリの目印の規則を確かめる。ジャンクションの試験は Windows だけ、シンボリックリンクの試験は
作れる環境だけで流す。

実行（標準ライブラリだけで動く）:
    python -X utf8 -m unittest tests/wiki/test_browse_fs.py -v
"""
from __future__ import annotations

import os
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
SCRIPTS = ROOT / "info-hive-wiki/skills/info-hive/scripts"
sys.path.insert(0, str(SCRIPTS))
sys.dont_write_bytecode = True

import wiki_browse_fs as fs  # noqa: E402


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


def make_junction(link: Path, target: Path) -> bool:
    if os.name != "nt":
        return False
    import _winapi
    _winapi.CreateJunction(str(target), str(link))
    return True


def tree_state(root: Path) -> dict:
    """ディレクトリの中のファイルとディレクトリの一覧と、ファイルの中身。"""
    state = {}
    for p in sorted(root.rglob("*")):
        rel = p.relative_to(root).as_posix()
        state[rel] = p.read_bytes() if p.is_file() else None
    return state


class BrowseFsTest(unittest.TestCase):
    def setUp(self):
        self._tmp = tempfile.TemporaryDirectory()
        self.base = Path(self._tmp.name).resolve()
        self.wiki = self.base / "work" / "Wiki"
        (self.wiki / "concepts").mkdir(parents=True)
        (self.wiki / "concepts" / "a.md").write_bytes(b"# a\n")
        self.guard = fs.Guard([self.wiki])

    def tearDown(self):
        self._tmp.cleanup()

    # --- 重なりの判定 ---

    def test_inside_and_containing_are_refused(self):
        with self.assertRaises(fs.Refused):
            self.guard.mkdir(self.wiki / "preview")
        with self.assertRaises(fs.Refused):
            self.guard.write_text(self.wiki / "x.html", "x")
        with self.assertRaises(fs.Refused):
            self.guard.rmtree(self.base / "work")       # Wiki を含む
        with self.assertRaises(fs.Refused):
            self.guard.rename(self.base / "work", self.base / "moved")
        with self.assertRaises(fs.Refused):
            self.guard.check(self.wiki)                  # 同じ場所
        self.assertTrue(self.guard.overlapping(self.base / "work"))
        self.assertEqual(tree_state(self.wiki), {"concepts": None, "concepts/a.md": b"# a\n"})

    def test_unverifiable_protected_place_is_refused(self):
        # 守る場所の属性を読めないときは、守りを外さずに止まる（ないものとして扱わない）。
        from unittest import mock
        real = os.stat

        def denied(path, *a, **k):
            if Path(path) == self.wiki:
                raise PermissionError("denied")
            return real(path, *a, **k)
        with mock.patch.object(os, "stat", denied):
            with self.assertRaises(fs.Refused):
                fs.Guard([self.wiki])
            with self.assertRaises(fs.Refused):
                self.guard.mkdir(self.wiki / "preview")
        with self.assertRaises(fs.Refused):
            fs.Guard([self.base / "no-such-wiki"])
        self.assertEqual(sorted(p.name for p in self.wiki.iterdir()), ["concepts"])

    def test_sibling_under_same_parent_is_allowed(self):
        view = self.guard.mkdir(self.base / "work" / "view")
        self.guard.write_text(view / "index.html", "ok")
        self.assertEqual((view / "index.html").read_text(encoding="utf-8"), "ok")
        self.guard.rmtree(view)
        self.assertFalse(view.exists())
        self.assertFalse(self.guard.overlapping(self.base / "work" / "view"))

    @unittest.skipUnless(os.path.normcase("A") == "a" or sys.platform == "darwin",
                         "大文字と小文字を区別しないファイルシステムの試験")
    def test_case_differs_but_same_entity(self):
        other = Path(str(self.wiki).replace("Wiki", "wiki"))
        self.assertNotEqual(str(other), str(self.wiki))
        with self.assertRaises(fs.Refused):
            self.guard.mkdir(other / "preview")
        self.assertTrue(fs.is_within(other / "preview", self.wiki))

    @unittest.skipUnless(os.name == "nt", "ジャンクションは Windows だけ")
    def test_junction_into_wiki_is_refused(self):
        data = self.base / "data"
        data.mkdir()
        make_junction(data / "state", self.wiki)
        with self.assertRaises(fs.Refused):
            self.guard.write_text(data / "state" / "server.json", "{}")
        with self.assertRaises(fs.Refused):
            self.guard.open_lock(data / "state" / "server.lock")
        self.assertEqual(sorted(p.name for p in self.wiki.iterdir()), ["concepts"])

    @unittest.skipUnless(os.name == "nt", "ジャンクションは Windows だけ")
    def test_rmtree_does_not_follow_junction(self):
        out = self.base / "out"
        out.mkdir()
        outside = self.base / "outside"
        outside.mkdir()
        (outside / "keep.txt").write_text("keep", encoding="utf-8")
        make_junction(out / "link", outside)
        # 守る場所でない外のディレクトリへのジャンクション。消してもその先は残る。
        guard = fs.Guard([self.wiki])
        guard.rmtree(out)
        self.assertFalse(out.exists())
        self.assertEqual((outside / "keep.txt").read_text(encoding="utf-8"), "keep")

    def test_symlink_into_wiki_is_refused(self):
        if not can_symlink(self.base):
            self.skipTest("シンボリックリンクを作れない")
        os.symlink(self.wiki, self.base / "link", target_is_directory=True)
        with self.assertRaises(fs.Refused):
            self.guard.mkdir(self.base / "link" / "preview")
        # リンクそのものは消せるが、先（Wiki）は消えない。
        self.guard.rmtree(self.base / "link")
        self.assertTrue((self.wiki / "concepts" / "a.md").exists())

    def test_external_input_is_protected(self):
        # Wiki の外にある入力の実体（ページのシンボリックリンクの先など）も守る。
        site = self.base / "site"
        site.mkdir()
        (site / "original.md").write_text("# o\n", encoding="utf-8")
        guard = fs.Guard([self.wiki, site / "original.md"])
        with self.assertRaises(fs.Refused):
            guard.rmtree(site)
        with self.assertRaises(fs.Refused):
            guard.write_text(site / "original.md", "x")
        self.assertEqual((site / "original.md").read_text(encoding="utf-8"), "# o\n")

    # --- 書き方 ---

    def test_write_does_not_modify_hardlinked_page(self):
        out = self.base / "out"
        out.mkdir()
        try:
            os.link(self.wiki / "concepts" / "a.md", out / "report.json")
        except OSError:
            self.skipTest("ハードリンクを作れない")
        self.guard.write_text(out / "report.json", "{}")
        self.assertEqual((self.wiki / "concepts" / "a.md").read_bytes(), b"# a\n")
        self.assertEqual((out / "report.json").read_text(encoding="utf-8"), "{}")
        self.assertEqual([p.name for p in out.iterdir()], ["report.json"])  # 一時のファイルが残らない

    def test_rmtree_does_not_change_attributes_of_hardlinked_page(self):
        import stat as st
        page = self.wiki / "concepts" / "a.md"
        old = self.base / "old-1"
        old.mkdir()
        try:
            os.link(page, old / "a.html")
        except OSError:
            self.skipTest("ハードリンクを作れない")
        os.chmod(page, st.S_IREAD)
        mode = os.stat(page).st_mode
        try:
            try:
                self.guard.rmtree(old)
            except OSError:
                pass   # Windows では読み取り専用のファイルを消せずに失敗する。それでよい
            self.assertEqual(os.stat(page).st_mode, mode)
        finally:
            os.chmod(page, st.S_IREAD | st.S_IWRITE)

    def test_rename_does_not_replace(self):
        a = self.guard.mkdir(self.base / "a")
        b = self.guard.mkdir(self.base / "b")
        with self.assertRaises(FileExistsError):
            self.guard.rename(a, b)

    def test_make_marked_dir(self):
        target = self.base / "state"
        self.assertTrue(self.guard.make_marked_dir(target, fs.SERVER_MARKER))
        self.assertTrue(fs.has_marker(target, fs.SERVER_MARKER))
        self.assertFalse(self.guard.make_marked_dir(target, fs.SERVER_MARKER))
        self.assertEqual(sorted(p.name for p in self.base.iterdir()), ["state", "work"])  # 一時のものが残らない

    def test_lock_is_exclusive(self):
        path = self.base / "build.lock"
        first = fs.Lock(self.guard, path)
        second = fs.Lock(self.guard, path)
        self.assertTrue(first.try_acquire())
        self.assertFalse(second.try_acquire())
        first.release()
        self.assertTrue(second.try_acquire())
        second.release()
        self.assertTrue(path.exists())                   # ロックのファイルは消さない
        self.assertEqual(path.read_bytes(), b"")         # 中身を書かない

    # --- 目印 ---

    def test_output_dir_rules(self):
        out = self.base / "out"
        fs.check_output_dir(out)                         # まだない
        out.mkdir()
        fs.check_output_dir(out)                         # 空
        (out / "stray.txt").write_text("x", encoding="utf-8")
        with self.assertRaises(fs.Refused):
            fs.check_output_dir(out)                     # 目印のない空でないディレクトリ
        (out / fs.GENERATION_MARKER).write_text("{}", encoding="utf-8")
        fs.check_output_dir(out)
        (out / "nested").mkdir()
        (out / "nested" / fs.GENERATION_MARKER).write_text("{}", encoding="utf-8")
        with self.assertRaises(fs.Refused):
            fs.check_output_dir(out)                     # 中にほかの書き出し
        with self.assertRaises(fs.Refused):
            fs.check_output_dir(out / "nested" / "deeper")   # ほかの書き出しの中

    def test_work_dir_allows_own_generations(self):
        work = self.base / "out.browse-work"
        fs.check_work_dir(work)
        work.mkdir()
        with self.assertRaises(fs.Refused):
            fs.check_work_dir(work)                      # 目印がない
        (work / fs.WORK_MARKER).write_text("", encoding="utf-8")
        for name in ("tmp-2", "old-2", "old-1"):
            (work / name).mkdir()
            (work / name / fs.GENERATION_MARKER).write_text("{}", encoding="utf-8")
        fs.check_work_dir(work)                          # 作りかけと退避の世代は入れ子に数えない
        (work / "tmp-2" / "deep").mkdir()
        (work / "tmp-2" / "deep" / fs.GENERATION_MARKER).write_text("{}", encoding="utf-8")
        with self.assertRaises(fs.Refused):
            fs.check_work_dir(work)

    def test_server_dir_rules(self):
        state = self.base / "k.server"
        fs.check_server_dir(state)
        state.mkdir()
        with self.assertRaises(fs.Refused):
            fs.check_server_dir(state)
        (state / fs.SERVER_MARKER).write_text("", encoding="utf-8")
        fs.check_server_dir(state)
        (state / fs.GENERATION_MARKER).write_text("", encoding="utf-8")
        with self.assertRaises(fs.Refused):
            fs.check_server_dir(state)


if __name__ == "__main__":
    unittest.main()
