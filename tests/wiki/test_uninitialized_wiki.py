"""初期化していないディレクトリを wiki として扱わないこと（ADR-0019、wiki 0.13.0）の試験。

設計は docs/plans/wiki-uninitialized-root-2026-11-13.md にある。

- 判定（wiki_initialized.problem()）の表の各行。
- wiki のパスを受け取る CLI の入口が、SCHEMA.md のないディレクトリを断り、理由と /wiki:init を標準エラーに書いて
  終了コード 1 で止まること。止まる前後で、基準のディレクトリ（wiki、raw、データの場所を含む）の木が変わらないこと。
  同じディレクトリに SCHEMA.md を置くと断らないこと（試験が空振りしていないことの確かめ）。
- Web ページの取得、経験の記録、アップグレードの書く側の入口。
- コマンドの文章とスキルの指示が、同じ扱いを書いていること。

MCP のツールの試験は tests/wiki/test_mcp_server.py の UninitializedWikiTests にある。

PyYAML が要る（グラフ、閲覧、セットアップの入口がサーバーの外で読み込む）。

    uv run --python 3.12 --with pyyaml==6.0.3 python -X utf8 -B -m unittest tests/wiki/test_uninitialized_wiki.py -v
"""
from __future__ import annotations

import json
import os
import shutil
import subprocess
import sys
import tempfile
import re
import unittest
from pathlib import Path
from unittest import mock

ROOT = Path(__file__).resolve().parents[2]
PLUGIN = ROOT / "info-hive-wiki"
SCRIPTS = PLUGIN / "skills" / "info-hive" / "scripts"
TEMPLATE = PLUGIN / "skills" / "info-hive" / "assets" / "ontology.yaml.template"
sys.path.insert(0, str(SCRIPTS))

try:
    import wiki_initialized
except ImportError:  # 実装の前は、判定の試験だけが落ちる
    wiki_initialized = None

REFUSED = "初期化された wiki ではない"
INIT = "/wiki:init"
ENV = {**os.environ, "PYTHONUTF8": "1", "PYTHONDONTWRITEBYTECODE": "1"}


def snapshot(base: Path) -> dict:
    """base の下のすべてのパスの種類、大きさ、更新時刻。"""
    found = {}
    for directory, dirs, files in os.walk(base):
        for name in dirs + files:
            path = Path(directory) / name
            st = path.lstat()
            found[path.relative_to(base).as_posix()] = (st.st_mode, st.st_size, st.st_mtime_ns)
    return found


def write(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes(text.encode("utf-8"))


def foreign_wiki(base: Path) -> Path:
    """GitHub の wiki の写しのような、Markdown のページだけがあり SCHEMA.md のないディレクトリ。"""
    wiki = base / "wiki"
    write(wiki / "Home.md", "# Home\n\n[[目印のページ]] へのリンク。\n")
    write(wiki / "目印のページ.md", "---\ntitle: \"目印のページ\"\n---\n\n# 目印\n\n目印の本文。\n")
    write(wiki / "concepts" / "概念.md", "# 概念\n\n目印について。\n")
    return wiki


def run(args, cwd: Path, env: dict | None = None, stdin: str | None = None, timeout: int = 300):
    done = subprocess.run([sys.executable, "-X", "utf8", "-B", *map(str, args)], cwd=cwd, input=stdin,
                          capture_output=True, encoding="utf-8", errors="replace", timeout=timeout,
                          env=env or ENV)
    return done


class ProblemTests(unittest.TestCase):
    """判定の表（設計の「決めること」の 1）。"""

    def setUp(self):
        self.assertIsNotNone(wiki_initialized, "wiki_initialized.py がない")
        self.temp = tempfile.TemporaryDirectory()
        self.base = Path(self.temp.name)
        self.addCleanup(self.temp.cleanup)

    def test_missing(self):
        message = wiki_initialized.problem(self.base / "ない")
        self.assertIn("wiki のディレクトリが見つからない", message)

    def test_parent_is_a_file(self):
        write(self.base / "file", "x")
        self.assertIn("wiki のディレクトリが見つからない", wiki_initialized.problem(self.base / "file" / "wiki"))

    def test_root_is_a_file(self):
        write(self.base / "wiki", "x")
        self.assertIn("ディレクトリではない", wiki_initialized.problem(self.base / "wiki"))

    def test_empty_directory(self):
        (self.base / "wiki").mkdir()
        message = wiki_initialized.problem(self.base / "wiki")
        self.assertIn(REFUSED, message)
        self.assertIn("SCHEMA.md がない", message)

    def test_pages_without_schema(self):
        self.assertIn(REFUSED, wiki_initialized.problem(foreign_wiki(self.base)))

    def test_schema_is_a_directory(self):
        wiki = foreign_wiki(self.base)
        (wiki / "SCHEMA.md").mkdir()
        self.assertIn("通常のファイルではない", wiki_initialized.problem(wiki))

    def test_dangling_link(self):
        wiki = foreign_wiki(self.base)
        try:
            os.symlink(self.base / "ない.md", wiki / "SCHEMA.md")
        except (OSError, NotImplementedError):
            self.skipTest("シンボリックリンクを作れない")
        self.assertIn("SCHEMA.md がない", wiki_initialized.problem(wiki))

    def test_link_to_file(self):
        wiki = foreign_wiki(self.base)
        write(self.base / "schema-real.md", "# スキーマ\n")
        try:
            os.symlink(self.base / "schema-real.md", wiki / "SCHEMA.md")
        except (OSError, NotImplementedError):
            self.skipTest("シンボリックリンクを作れない")
        self.assertIsNone(wiki_initialized.problem(wiki))

    def test_initialized(self):
        wiki = foreign_wiki(self.base)
        write(wiki / "SCHEMA.md", "# スキーマ\n")
        self.assertIsNone(wiki_initialized.problem(wiki))
        self.assertEqual(wiki_initialized.require(wiki), wiki)

    def test_require_raises_value_error_with_hint(self):
        with self.assertRaises(ValueError) as caught:
            wiki_initialized.require(foreign_wiki(self.base))
        self.assertIsInstance(caught.exception, wiki_initialized.NotInitialized)
        self.assertIn(REFUSED, str(caught.exception))
        self.assertIn(INIT, str(caught.exception))

    def test_schema_is_not_read(self):
        """中身は判定に使わない。読めない中身（UTF-8 でないバイト列）でも初期化済みとみなす。"""
        wiki = foreign_wiki(self.base)
        (wiki / "SCHEMA.md").write_bytes(b"\xff\xfe\x00")
        self.assertIsNone(wiki_initialized.problem(wiki))

    def stat_failing_for(self, target: Path):
        real = os.stat

        def fake(path, *args, **kwargs):
            if Path(path) == target:
                raise PermissionError(13, "アクセスが拒否された")
            return real(path, *args, **kwargs)
        return mock.patch.object(wiki_initialized.os, "stat", side_effect=fake)

    def test_root_cannot_be_examined(self):
        wiki = foreign_wiki(self.base)
        write(wiki / "SCHEMA.md", "# スキーマ\n")
        with self.stat_failing_for(wiki):
            message = wiki_initialized.problem(wiki)
        self.assertIn("wiki のディレクトリを確かめられない", message)
        self.assertIn("アクセスが拒否された", message)

    def test_schema_cannot_be_examined(self):
        wiki = foreign_wiki(self.base)
        write(wiki / "SCHEMA.md", "# スキーマ\n")
        with self.stat_failing_for(wiki / "SCHEMA.md"):
            message = wiki_initialized.problem(wiki)
        self.assertIn("初期化された wiki か確かめられない", message)

    def test_letter_case_follows_the_file_system(self):
        """大文字と小文字はファイルシステムに任せる。schema.md で SCHEMA.md が見つかる環境では初期化済み。"""
        wiki = foreign_wiki(self.base)
        write(wiki / "schema.md", "# スキーマ\n")
        insensitive = os.path.exists(wiki / "SCHEMA.md")
        self.assertEqual(wiki_initialized.problem(wiki) is None, insensitive)


class EntryCase(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory(ignore_cleanup_errors=True)
        self.base = Path(self.temp.name)
        self.addCleanup(self.temp.cleanup)
        self.wiki = foreign_wiki(self.base)
        self.raw = self.base / "raw"
        self.raw.mkdir()
        write(self.raw / "記事.md", "# 記事\n\n目印。\n")
        self.data = self.base / "data"
        self.data.mkdir()
        self.env = {**ENV, "INFO_HIVE_DATA_DIR": str(self.data)}
        # 外に置いたオントロジー。wiki の中にはない。
        self.outside = Path(tempfile.mkdtemp())
        self.addCleanup(shutil.rmtree, self.outside, True)
        shutil.copyfile(TEMPLATE, self.outside / "ontology.yaml")
        write(self.outside / "source.md", "# ソース\n\n目印。\n")
        write(self.outside / "record.json", json.dumps({
            "id": "uninit-check", "task": "確かめ", "verification": "試験", "model": "m", "tools": "t",
            "scope": "試験", "outcome": "success", "actions": ["動かした"]}, ensure_ascii=False))

    def assert_refused(self, args, stdin=None, cwd=None, hint=INIT):
        before = snapshot(self.base)
        done = run(args, cwd or self.base, self.env, stdin)
        after = snapshot(self.base)
        self.assertEqual(done.returncode, 1, f"{args}\n{done.stdout[-2000:]}\n{done.stderr[-2000:]}")
        self.assertIn(hint, done.stderr, done.stderr)
        self.assertNotIn("Traceback", done.stderr)
        self.assertEqual(after, before, f"{args} が書いた: {sorted(set(after) ^ set(before))}")
        return done

    def accepted(self, args, stdin=None):
        """SCHEMA.md を置いて同じ呼び出しをする。断らないことだけを確かめる（成功するかは入口による）。"""
        write(self.wiki / "SCHEMA.md", "# スキーマ\n")
        done = run(args, self.base, self.env, stdin)
        self.assertNotIn(REFUSED, done.stderr, f"{args}\n{done.stderr[-2000:]}")
        return done


class ReaderEntryTests(EntryCase):
    """wiki を読む CLI の入口。"""

    def cases(self):
        w = self.wiki
        return {
            "lint": [SCRIPTS / "wiki_lint.py", w, "--json"],
            "stats": [SCRIPTS / "wiki_stats.py", w, "--json"],
            "search": [SCRIPTS / "wiki_search.py", "目印", "--wiki", w, "--json", "--no-embed"],
            "search-cache": [SCRIPTS / "wiki_search.py", "目印", "--wiki", w, "--cache", "--json", "--no-embed"],
            "backlinks": [SCRIPTS / "wiki_search.py", "", "--wiki", w, "--backlinks", "目印のページ"],
            "graph-lint": [SCRIPTS / "wiki_graph_lint.py", w, "--ontology", self.outside / "ontology.yaml"],
            "graph-extract": [SCRIPTS / "wiki_graph_extract.py", w, "--ontology", self.outside / "ontology.yaml"],
            "graph-query": [SCRIPTS / "wiki_graph_query.py", w, "neighbors", "--node", "concept:概念"],
            "decide-shortlist": [SCRIPTS / "wiki_decide.py", "shortlist", self.outside / "source.md", "--wiki", w,
                                 "--no-embed"],
            "decide-contradictions": [SCRIPTS / "wiki_decide.py", "contradictions", "--wiki", w],
            "evolve-history": [SCRIPTS / "wiki_evolve.py", "--wiki", w, "history"],
            "evolve-loop": [SCRIPTS / "wiki_evolve_loop.py", "--wiki", w, "--skill", self.outside, "--suite",
                            self.outside / "suite.json", "--config", self.outside / "config.json", "--id", "x"],
            "setup": [SCRIPTS / "setup_wiki.py", "--wiki", w],
            "browse-build": [SCRIPTS / "wiki_browse.py", "build", w, "--out", self.base / "site"],
            "browse-stop": [SCRIPTS / "wiki_browse.py", "stop", w],
        }

    def test_entries_refuse_and_write_nothing(self):
        for name, args in self.cases().items():
            with self.subTest(entry=name):
                done = self.assert_refused(args)
                self.assertIn(REFUSED, done.stderr)

    def test_default_wiki_is_checked(self):
        """wiki を省くと ./wiki を使う。その ./wiki も確かめる。"""
        for script in ("wiki_lint.py", "wiki_stats.py"):
            with self.subTest(script=script):
                self.assertIn(REFUSED, self.assert_refused([SCRIPTS / script, "--json"]).stderr)

    def test_missing_directory_shows_hint(self):
        shutil.rmtree(self.wiki)
        for name, args in self.cases().items():
            with self.subTest(entry=name):
                done = self.assert_refused(args)
                self.assertIn("wiki のディレクトリが見つからない", done.stderr)

    def test_file_as_wiki_shows_hint(self):
        """ディレクトリでないものを渡しても、同じ判定の文と案内で止まる。"""
        shutil.rmtree(self.wiki)
        write(self.wiki, "ファイル\n")
        for name, args in self.cases().items():
            with self.subTest(entry=name):
                self.assertIn("ディレクトリではない", self.assert_refused(args).stderr)

    def test_browse_core_answers_no_wiki(self):
        request = json.dumps({"op": "manifest", "wiki": str(self.wiki)}, ensure_ascii=False) + "\n"
        before = snapshot(self.base)
        done = run([SCRIPTS / "wiki_browse.py", "core"], self.base, self.env, request)
        self.assertEqual(snapshot(self.base), before)
        self.assertEqual(json.loads(done.stdout.splitlines()[0]), {"ok": False, "error": "no_wiki"})

    def test_initialized_wiki_is_accepted(self):
        """同じ呼び出しが、SCHEMA.md を置くと断られない（lint、stats、search は成功する）。"""
        cases = self.cases()
        for name in ("lint", "stats", "search", "search-cache"):
            with self.subTest(entry=name):
                done = self.accepted(cases[name])
                self.assertEqual(done.returncode, 0, done.stderr[-2000:])
        for name in ("graph-lint", "graph-query", "decide-contradictions", "evolve-history", "browse-build"):
            with self.subTest(entry=name):
                self.accepted(cases[name])


class WriterEntryTests(EntryCase):
    """wiki のために書く入口: Web ページの取得、経験の記録、アップグレード。"""

    def test_fetch_checks_wiki_before_network(self):
        # 届かない URL。確かめがネットより先なら終了コード 1、取得の失敗なら 2 になる。
        args = [SCRIPTS / "wiki_fetch.py", "http://127.0.0.1:9/", "--wiki", self.wiki, "--raw-root",
                self.base / "raw-new", "--slug", "記事", "--json"]
        done = self.assert_refused(args)
        self.assertIn(REFUSED, done.stderr)

    def test_fetch_does_not_create_raw_root(self):
        write(self.wiki / "SCHEMA.md", "# スキーマ\n")
        args = [SCRIPTS / "wiki_fetch.py", "http://127.0.0.1:9/", "--wiki", self.wiki, "--raw-root",
                self.base / "raw-new", "--slug", "記事", "--json"]
        done = self.assert_refused(args, hint="/wiki:upgrade")
        self.assertIn("raw のルートがない", done.stderr)

    def test_fetch_requires_wiki(self):
        done = run([SCRIPTS / "wiki_fetch.py", "http://127.0.0.1:9/", "--raw-root", self.raw, "--slug", "記事"],
                   self.base, self.env)
        self.assertEqual(done.returncode, 2, done.stderr)
        self.assertIn("--wiki", done.stderr)

    def test_capture_checks_wiki(self):
        args = [SCRIPTS / "wiki_evolve.py", "--wiki", self.wiki, "capture", "--raw", self.raw, "--record",
                self.outside / "record.json"]
        self.assertIn(REFUSED, self.assert_refused(args).stderr)
        self.assertFalse((self.raw / "experiences").exists())

    def test_capture_default_wiki_is_checked(self):
        args = [SCRIPTS / "wiki_evolve.py", "capture", "--raw", self.raw, "--record", self.outside / "record.json"]
        self.assertIn(REFUSED, self.assert_refused(args).stderr)

    def test_capture_missing_raw_does_not_ask_to_create_it(self):
        write(self.wiki / "SCHEMA.md", "# スキーマ\n")
        args = [SCRIPTS / "wiki_evolve.py", "--wiki", self.wiki, "capture", "--raw", self.base / "raw-new",
                "--record", self.outside / "record.json"]
        before = snapshot(self.base)
        done = run(args, self.base, self.env)
        self.assertEqual(done.returncode, 1, done.stderr)
        self.assertEqual(snapshot(self.base), before)
        self.assertNotIn("先に作っておく", done.stderr)
        self.assertIn("/wiki:upgrade", done.stderr)

    def test_capture_into_initialized_wiki(self):
        write(self.wiki / "SCHEMA.md", "# スキーマ\n")
        done = run([SCRIPTS / "wiki_evolve.py", "--wiki", self.wiki, "capture", "--raw", self.raw, "--record",
                    self.outside / "record.json"], self.base, self.env)
        self.assertEqual(done.returncode, 0, done.stderr)
        self.assertTrue((self.raw / "experiences" / "uninit-check.json").is_file())

    def test_upgrade_refuses_uninitialized_wiki(self):
        # uv を見つけられないようにする。確かめが効かなければ、ファイルを作ってから uv がないと止まる。
        empty = Path(tempfile.mkdtemp())
        self.addCleanup(shutil.rmtree, empty, True)
        env = {**self.env, "PATH": str(empty)}
        before = snapshot(self.base)
        done = run([SCRIPTS / "init_wiki.py", self.base, "--upgrade"], self.base, env)
        self.assertEqual(snapshot(self.base), before, sorted(set(snapshot(self.base)) ^ set(before)))
        self.assertEqual(done.returncode, 1, done.stdout + done.stderr)
        self.assertIn("アップグレードする wiki がない", done.stderr)
        self.assertIn(INIT, done.stderr)
        self.assertNotIn("uv が必要", done.stderr)

    def test_upgrade_refuses_missing_wiki_dir(self):
        shutil.rmtree(self.wiki)
        empty = Path(tempfile.mkdtemp())
        self.addCleanup(shutil.rmtree, empty, True)
        before = snapshot(self.base)
        done = run([SCRIPTS / "init_wiki.py", self.base, "--upgrade"], self.base, {**self.env, "PATH": str(empty)})
        self.assertEqual(snapshot(self.base), before)
        self.assertEqual(done.returncode, 1)
        self.assertIn("アップグレードする wiki がない", done.stderr)


class EntranceInventoryTests(unittest.TestCase):
    """wiki のパスを受け取る入口を、ファイルから機械的に数える（設計の「決めること」の 3）。

    入口は、最上位に `__main__` の分岐を持つスクリプトのうち、wiki のパスを引数（`args.wiki`、`args.wiki_dir`）か
    標準入力の JSON（`wiki`、`wiki_root`）から受け取るもの。どの入口も wiki_initialized を使い、この試験か
    ほかの試験で振る舞いを確かめていなければならない。判定しない入口は、理由とともに EXEMPT に書く。
    """

    TAKES_WIKI = re.compile(r"args\.wiki(_dir)?\b|\[['\"]wiki_root['\"]\]|\.get\(\s*['\"]wiki(_root)?['\"]")
    EXEMPT = {
        # 評価ループ（wiki_evolve_loop.py、wiki_evolve.py evaluate）が、suite.json の事実情報のコーパスを
        # 一時ディレクトリに写して渡す。利用者の wiki ではない。学習用の wiki はループの側で確かめる。
        "wiki_evolve_agent.py": "評価のランナー",
        "wiki_evolve_claude.py": "評価のランナー",
        "wiki_evolve_api.py": "評価のランナー",
        "wiki_evolve_stream.py": "評価のランナー",
    }
    # 入口ごとの振る舞いの試験。ReaderEntryTests.cases() の入口に加えて、ほかで確かめるもの。
    TESTED_ELSEWHERE = {
        "wiki_fetch.py": "WriterEntryTests",
        "init_wiki.py": "WriterEntryTests（--upgrade）",
        "wiki_mcp_server.py": "tests/wiki/test_mcp_server.py の UninitializedWikiTests",
    }

    @staticmethod
    def is_entry(source: str) -> bool:
        return re.search(r"^if __name__ == ['\"]__main__['\"]:", source, re.MULTILINE) is not None

    def entrances(self) -> set[str]:
        found = set()
        for path in sorted(SCRIPTS.glob("*.py")):
            if path.name.startswith("test_"):
                continue
            source = path.read_text(encoding="utf-8")
            if self.is_entry(source) and self.TAKES_WIKI.search(source):
                found.add(path.name)
        # MCP のツールは関数の引数で wiki を受け取る。サーバーの入口は wiki_root() である。
        found.add("wiki_mcp_server.py")
        return found

    def test_inventory_is_not_empty(self):
        # 数え方が壊れて、何も確かめなくなるのを防ぐ。
        self.assertTrue({"wiki_lint.py", "wiki_search.py", "wiki_browse.py", "wiki_fetch.py", "init_wiki.py",
                         "wiki_evolve.py", "wiki_evolve_loop.py"} <= self.entrances(), sorted(self.entrances()))

    def test_every_entrance_uses_the_shared_check(self):
        for name in sorted(self.entrances() - set(self.EXEMPT)):
            with self.subTest(script=name):
                source = (SCRIPTS / name).read_text(encoding="utf-8")
                # wiki_evolve_loop.py は wiki_evolve.locked() を通る。
                self.assertTrue("wiki_initialized" in source or (name == "wiki_evolve_loop.py" and "locked(" in source))

    def test_every_entrance_is_tested(self):
        cases = ReaderEntryTests.cases(EntryCaseStub())
        tested = {Path(str(args[0])).name for args in cases.values()} | set(self.TESTED_ELSEWHERE)
        self.assertEqual(sorted(self.entrances() - set(self.EXEMPT) - tested), [])

    def test_exempt_scripts_still_exist(self):
        self.assertEqual(sorted(name for name in self.EXEMPT if not (SCRIPTS / name).is_file()), [])


class EntryCaseStub:
    """ReaderEntryTests.cases() の引数の組み立てだけを使う。パスは実在しなくてよい。"""
    wiki = Path("wiki")
    outside = Path("outside")
    base = Path("base")


class DocumentTests(unittest.TestCase):
    """コマンドの文章とスキルの指示（設計の「決めること」の 7）。"""

    GATE = "`<WIKI_ROOT>/SCHEMA.md` がなければ、初期化された wiki ではない"
    COMMANDS = ("query", "lint", "stats", "graph", "browse", "ingest", "learn", "evolve", "upgrade")

    def test_commands_share_the_gate(self):
        for name in self.COMMANDS:
            with self.subTest(command=name):
                text = (PLUGIN / "commands" / f"{name}.md").read_text(encoding="utf-8")
                self.assertIn(self.GATE, text)
                self.assertIn("/wiki:init --user", text)

    def test_skill_proposes_init(self):
        text = (PLUGIN / "skills" / "info-hive" / "SKILL.md").read_text(encoding="utf-8")
        self.assertNotIn("wiki がない場合は、下の初期化の手順を実行する", text)
        self.assertIn("SCHEMA.md", text)

    def test_fetch_examples_pass_wiki(self):
        for path in (PLUGIN / "commands" / "ingest.md", PLUGIN / "skills" / "info-hive" / "references" / "ingest-workflow.md"):
            with self.subTest(path=path.name):
                for line in path.read_text(encoding="utf-8").splitlines():
                    if "wiki_fetch.py\" \"" in line or "wiki_fetch.py\" \"<URL>\"" in line:
                        self.assertIn("--wiki", line)


if __name__ == "__main__":
    unittest.main()
