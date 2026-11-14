"""`/wiki:help [command]`（wiki_help.py の --command と commands/help.md）の試験。

設計は docs/plans/wiki-help-command-2026-11-14.md にある。

- コマンド名の正規化と照合、見つからないときの近い名前。
- `docs/commands.md` の節の取り出し（フェンス、閉じの `#`、同じ名前の節）。
- 節の相対リンクの、GitHub の導入した版のタグの文書への書き換え。
- 書き換えの前後を同梱の Markdown のパーサーで照らし合わせ、リンクの宛先のほかが変わる書き方（実装のレビューの
  反例）では書き換えずに節をそのまま出して警告すること。
- 実物の commands/ と docs/commands.md で、すべてのコマンドの詳細が警告なしに出て、出力のリンクがすべて
  GitHub の URL か外部の URL になり、GitHub の URL が実在するファイルを指すこと。
- commands/help.md が、利用者の引数をそのままシェルに渡さない手順を書いていること。

実行（標準ライブラリと、プラグインに同梱の markdown-it-py だけで動く）:
    python -X utf8 -m unittest tests/wiki/test_help_command.py -v
"""
from __future__ import annotations

import contextlib
import io
import json
import os
import re
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path
from urllib.parse import unquote, urlsplit

ROOT = Path(__file__).resolve().parents[2]
PLUGIN = ROOT / "info-hive-wiki"
SCRIPTS = PLUGIN / "skills/info-hive/scripts"
sys.path.insert(0, str(SCRIPTS))

import wiki_help  # noqa: E402
import wiki_pages  # noqa: E402

EXPECTED = ["init", "ingest", "query", "lint", "stats", "graph", "browse", "learn", "evolve", "upgrade", "help"]
# commands/help.md がシェルに渡す名前を確かめる正規表現。help.md の文と同じ文字列であること。
SHELL_SAFE = r"^[A-Za-z0-9][A-Za-z0-9-]*$"
BASE = "https://github.com/owner/repo/blob/v1.2.3"
MANIFEST = '{"name": "wiki", "version": "1.2.3", "repository": "https://github.com/owner/repo"}\n'


def write(root: Path, rel: str, text: str) -> Path:
    path = root / rel
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes(text.encode("utf-8"))
    return path


def run_main(*argv: str) -> tuple[int, str, str]:
    out, err = io.StringIO(), io.StringIO()
    with contextlib.redirect_stdout(out), contextlib.redirect_stderr(err):
        code = wiki_help.main(list(argv))
    return code, out.getvalue(), err.getvalue()


def parsed_destinations(markdown: str) -> list[tuple[str, str]]:
    """同梱のパーサーが読んだリンクと画像の宛先を、(種類, 宛先) で書いた順に返す。"""
    found = []

    def walk(tokens):
        for t in tokens:
            if t.type == "link_open":
                found.append(("link", t.attrs["href"]))
            elif t.type == "image":
                found.append(("image", t.attrs["src"]))
            if t.children:
                walk(t.children)

    walk(wiki_pages.new_parser().parse(markdown, {}))
    return found


class NormalizeTests(unittest.TestCase):
    def test_forms_of_the_same_name(self):
        for raw in ["query", "/wiki:query", "wiki:query", " Query ", "WIKI:QUERY", "/query",
                    "\N{IDEOGRAPHIC SPACE}query\N{IDEOGRAPHIC SPACE}"]:
            with self.subTest(raw=raw):
                self.assertEqual(wiki_help.normalize_command_name(raw, "wiki"), "query")

    def test_plugin_name_comes_from_argument(self):
        self.assertEqual(wiki_help.normalize_command_name("/other:query", "other"), "query")

    def test_rejected_forms(self):
        cases = {
            "query extra": "1 つだけ",
            "query\textra": "1 つだけ",
            "/wiki:": "コマンド名がない",
            "/": "コマンド名がない",
            "wiki:": "コマンド名がない",
            "/rag:query": "/wiki: のコマンドだけ",
            "wiki:rag:query": "/wiki: のコマンドだけ",
        }
        for raw, message in cases.items():
            with self.subTest(raw=raw):
                with self.assertRaises(wiki_help.HelpError) as ctx:
                    wiki_help.normalize_command_name(raw, "wiki")
                self.assertIn(message, str(ctx.exception))

    def test_lookup_is_only_against_collected_names(self):
        commands = [{"name": "query"}, {"name": "Stats"}]
        self.assertIs(wiki_help.find_command(commands, "query"), commands[0])
        self.assertIs(wiki_help.find_command(commands, "stats"), commands[1])
        for name in ["../commands/query", "query.md", "quer", "commands"]:
            self.assertIsNone(wiki_help.find_command(commands, name))


class FindDocSectionTests(unittest.TestCase):
    DOC = (
        "# コマンド\n\n"
        "## `/wiki:query <question>`\n\n"
        "質問に答える。\n\n"
        "### 補足\n\n"
        "```markdown\n"
        "## これは見出しではない\n"
        "```\n\n"
        "~~~~\n"
        "~~~\n"
        "## これも見出しではない\n"
        "~~~~\n\n"
        "最後の段落。\n\n"
        "## `/wiki:stats` ##\n\n"
        "規模を出す。\n"
        "## 次の節\n"
        "## `/other:lint`\n\n"
        "ほかのプラグイン。\n"
    )

    def test_section_runs_to_next_h2_outside_fences(self):
        section, warnings = wiki_help.find_doc_section(self.DOC, "wiki", "query")
        self.assertEqual(warnings, [])
        body = section.body
        self.assertTrue(body.startswith("質問に答える。"))
        self.assertIn("### 補足", body)
        self.assertIn("## これは見出しではない", body)
        self.assertIn("## これも見出しではない", body)
        self.assertTrue(body.endswith("最後の段落。"))
        # 行の範囲は、本文の最初と最後の行を指す。
        lines = self.DOC.split("\n")
        self.assertEqual(lines[section.start], "質問に答える。")
        self.assertEqual(lines[section.end - 1], "最後の段落。")

    def test_heading_with_closing_hashes_and_unformatted_next_heading(self):
        section, warnings = wiki_help.find_doc_section(self.DOC, "wiki", "stats")
        self.assertEqual((section.body, warnings), ("規模を出す。", []))

    def test_missing_and_other_plugin(self):
        self.assertEqual(wiki_help.find_doc_section(self.DOC, "wiki", "lint"), (None, []))
        self.assertEqual(wiki_help.find_doc_section(self.DOC, "wiki", "que"), (None, []))
        section, _ = wiki_help.find_doc_section(self.DOC, "other", "lint")
        self.assertEqual(section.body, "ほかのプラグイン。")

    def test_duplicate_section_uses_first_and_warns(self):
        doc = "## `/wiki:a`\n\n一つ目。\n\n## `/wiki:a`\n\n二つ目。\n"
        section, warnings = wiki_help.find_doc_section(doc, "wiki", "a")
        self.assertEqual(section.body, "一つ目。")
        self.assertEqual(len(warnings), 1)


class DocsBaseUrlTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.root = Path(self.tmp.name)

    def tearDown(self):
        self.tmp.cleanup()

    def base(self, manifest: dict):
        write(self.root, ".claude-plugin/plugin.json", json.dumps(manifest))
        return wiki_help.docs_base_url(self.root)

    def test_repository_forms(self):
        for repository in ["https://github.com/owner/repo", "https://github.com/owner/repo/",
                           "https://github.com/owner/repo.git"]:
            with self.subTest(repository=repository):
                self.assertEqual(self.base({"repository": repository, "version": "1.2.3"}), (BASE, []))

    def test_unusable_manifest(self):
        for manifest in [{"version": "1.2.3"}, {"repository": "https://gitlab.com/o/r", "version": "1.2.3"},
                         {"repository": {"url": "https://github.com/o/r"}, "version": "1.2.3"},
                         {"repository": "https://github.com/o/r"}, {"repository": "https://github.com/o/r", "version": "main"}]:
            with self.subTest(manifest=manifest):
                base, warnings = self.base(manifest)
                self.assertIsNone(base)
                self.assertEqual(len(warnings), 1)


class LinkTests(unittest.TestCase):
    """節の相対リンクの書き換えと、書き換えの照らし合わせ。"""

    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.root = (Path(self.tmp.name) / "プラグイン 1").resolve()
        write(self.root, ".claude-plugin/plugin.json", MANIFEST)
        write(self.root, "commands/query.md", "---\ndescription: 答える。\n---\n")
        write(self.root, "docs/workflows.md", "x\n")
        write(self.root, "docs/search.md", "x\n")
        write(self.root, "docs/ワーク フロー.md", "x\n")
        write(self.root, "docs/p.png", "x\n")
        write(self.root, "skills/info-hive/references/mcp-server.md", "x\n")
        self.root = self.root.resolve()
        self.docs = (self.root / "docs").resolve()

    def tearDown(self):
        self.tmp.cleanup()

    def details(self, body: str, before: str = "") -> tuple[str | None, list[str]]:
        """docs/commands.md に query の節を書き、command_details() の結果を返す。"""
        write(self.root, "docs/commands.md", f"# コマンド\n\n{before}## `/wiki:query <question>`\n\n{body}\n\n## `/wiki:x`\n")
        return wiki_help.command_details(self.root, "wiki", "query")

    def test_relative_parent_fragment_and_fragment_only(self):
        body = ("詳しくは[取り込み](./workflows.md#ソースを取り込む)と"
                "[MCP](../skills/info-hive/references/mcp-server.md)と[表](#wikiinit)を参照。")
        out, warnings = self.details(body)
        self.assertEqual(warnings, [])
        self.assertEqual(
            out,
            f"詳しくは[取り込み]({BASE}/docs/workflows.md#%E3%82%BD%E3%83%BC%E3%82%B9%E3%82%92%E5%8F%96%E3%82%8A%E8%BE%BC%E3%82%80)と"
            f"[MCP]({BASE}/skills/info-hive/references/mcp-server.md)と"
            f"[表]({BASE}/docs/commands.md#wikiinit)を参照。",
        )

    def test_space_japanese_and_image(self):
        out, warnings = self.details("[x](./ワーク%20フロー.md) と ![図](./p.png)")
        self.assertEqual(warnings, [])
        self.assertEqual(parsed_destinations(out), [
            ("link", f"{BASE}/docs/%E3%83%AF%E3%83%BC%E3%82%AF%20%E3%83%95%E3%83%AD%E3%83%BC.md"),
            ("image", f"{BASE}/docs/p.png?raw=true"),
        ])

    def test_untouched(self):
        body = "\n".join([
            "[外](https://example.com/a.md) と [メール](mailto:a@example.com) と [根](/abs.md)",
            "`[コード](./workflows.md)` と ``[二重](./workflows.md) ` `` はコード",
            "```markdown",
            "[フェンス](./workflows.md)",
            "```",
        ])
        self.assertEqual(self.details(body), (body, []))

    def test_forms_the_rewriter_reads(self):
        # 実装の 1 回目のレビューの軽微な指摘のうち、書き換えで正しく読めるようにしたもの。
        cases = {
            "リンクの文字のインラインコード": "[`/wiki:init`](./workflows.md)",
            "リンクの文字の入れ子の []": "[search [note] text](./search.md)",
            "エスケープしたバッククォート": "\\`prefix [search](./search.md) suffix\\`",
            "文字参照の #": "[x](./search.md&#35;intro)",
            "閉じないバッククォートが次の行のリンクを隠さない": "`one\n### 見出し\n[検索](./search.md)\n`",
        }
        for label, body in cases.items():
            with self.subTest(label=label):
                out, warnings = self.details(body)
                self.assertEqual(warnings, [])
                self.assertNotEqual(out, body)
                for _, dest in parsed_destinations(out):
                    self.assertTrue(dest.startswith(BASE), dest)

    def test_unreadable_forms_fall_back_to_the_section_as_is(self):
        # 書き換えが読めない書き方。照らし合わせで見つけ、書き換えずに節をそのまま出す。
        cases = {
            "引用の中の字下げしたフェンス（実装のレビューの反例 A）": ("> text\n>   ~~~md\n>   [search](./search.md)\n>   ~~~", ""),
            "リストの中のフェンス": ("- ```md\n  [search](./search.md)\n  ```", ""),
            "節の外の参照リンクの定義（実装のレビューの反例 B）": ("[search][s]", "[s]: ./search.md\n\n"),
            "節の中の参照リンクの定義": ("[search][s]\n\n[s]: ./search.md", ""),
            "山かっこの宛先": ("[検索](<./search.md>)", ""),
            "題名つきの宛先": ('[検索](./search.md "検索")', ""),
            "丸かっこを含む宛先": ("[検索](./a\\(b\\).md)", ""),
        }
        for label, (body, before) in cases.items():
            with self.subTest(label=label):
                out, warnings = self.details(body, before)
                self.assertEqual(out, body)
                self.assertTrue(any("節をそのまま出す" in w for w in warnings), warnings)

    def test_missing_target_warns(self):
        out, warnings = self.details("[x](./nowhere.md)")
        self.assertEqual(out, f"[x]({BASE}/docs/nowhere.md)")
        self.assertEqual(len(warnings), 1)
        self.assertIn("./nowhere.md", warnings[0])

    def test_outside_plugin_root_is_kept(self):
        out, warnings = self.details("[x](../../outside.md)")
        self.assertEqual(out, "[x](../../outside.md)")
        self.assertTrue(any("プラグインの外" in w for w in warnings), warnings)

    def test_no_repository_keeps_links(self):
        write(self.root, ".claude-plugin/plugin.json", '{"name": "wiki", "version": "1.2.3"}\n')
        out, warnings = self.details("[x](./search.md)")
        self.assertEqual(out, "[x](./search.md)")
        self.assertTrue(any("repository" in w for w in warnings), warnings)


class RenderDetailTests(unittest.TestCase):
    BASE = {"name": "query", "command": "/wiki:query", "description": "答える。"}

    def test_with_argument_and_details(self):
        c = {**self.BASE, "argument_hint": "<質問>", "argument_description": "質問。"}
        self.assertEqual(
            wiki_help.render_detail(c, "本文。\n\n```bash\n/wiki:query x\n```"),
            "### `/wiki:query` `<質問>`\n\n答える。\n\n**引数**: 質問。\n\n**詳細**\n\n本文。\n\n```bash\n/wiki:query x\n```\n",
        )

    def test_without_argument(self):
        c = {**self.BASE, "argument_hint": None, "argument_description": None}
        self.assertEqual(wiki_help.render_detail(c, "本文。"),
                         "### `/wiki:query`\n\n答える。\n\n**引数**: 引数はない。\n\n**詳細**\n\n本文。\n")

    def test_hint_without_description_and_no_details(self):
        c = {**self.BASE, "argument_hint": "<x>", "argument_description": None}
        self.assertEqual(wiki_help.render_detail(c, None),
                         "### `/wiki:query` `<x>`\n\n答える。\n\n**引数**: （引数の説明は未記入）\n")


class MainWithFakePluginTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.root = Path(self.tmp.name)
        write(self.root, ".claude-plugin/plugin.json", MANIFEST)
        write(self.root, "commands/query.md",
              '---\ndescription: 答える。\nargument-hint: "<質問>"\nargument-description: "質問。"\n---\n\n本文。\n')
        write(self.root, "commands/stats.md", "---\ndescription: 規模を出す。\n---\n\n本文。\n")
        write(self.root, "docs/search.md", "x\n")
        write(self.root, "docs/commands.md",
              "## `/wiki:query <question>`\n\n答える。[検索](./search.md#a)を参照。\n")

    def tearDown(self):
        self.tmp.cleanup()

    def test_detail(self):
        code, out, err = run_main(str(self.root), "--command", "/wiki:query")
        self.assertEqual((code, err), (0, ""))
        self.assertEqual(out, "### `/wiki:query` `<質問>`\n\n答える。\n\n**引数**: 質問。\n\n**詳細**\n\n"
                              f"答える。[検索]({BASE}/docs/search.md#a)を参照。\n")

    def test_missing_section_warns_and_omits_details(self):
        code, out, err = run_main(str(self.root), "--command=stats")
        self.assertEqual(code, 0)
        self.assertNotIn("**詳細**", out)
        self.assertIn("/wiki:stats の節がない", err)

    def test_missing_doc_warns(self):
        (self.root / "docs/commands.md").unlink()
        code, out, err = run_main(str(self.root), "--command=query")
        self.assertEqual(code, 0)
        self.assertNotIn("**詳細**", out)
        self.assertIn("コマンドの文書がない", err)

    def test_json(self):
        code, out, _ = run_main(str(self.root), "--json", "--command=query")
        self.assertEqual(code, 0)
        data = json.loads(out)
        self.assertEqual(set(data), {"name", "command", "description", "argument_hint", "argument_description", "details"})
        self.assertIn(f"[検索]({BASE}/docs/search.md#a)", data["details"])
        code, out, _ = run_main(str(self.root), "--json", "--command=stats")
        self.assertIsNone(json.loads(out)["details"])

    def test_not_found(self):
        code, out, err = run_main(str(self.root), "--command=qury")
        self.assertEqual((code, out), (1, ""))
        self.assertIn("コマンドが見つからない: qury", err)
        self.assertIn("近い名前: query", err)
        self.assertIn("使えるコマンド: query, stats", err)
        code, _, err = run_main(str(self.root), "--command=zzzzzz")
        self.assertEqual(code, 1)
        self.assertNotIn("近い名前", err)

    def test_bad_name(self):
        code, out, err = run_main(str(self.root), "--command=query extra")
        self.assertEqual((code, out), (1, ""))
        self.assertIn("1 つだけ", err)
        self.assertIn("使えるコマンド", err)

    def test_empty_is_list(self):
        for value in ["", "  "]:
            with self.subTest(value=value):
                code, out, _ = run_main(str(self.root), f"--command={value}")
                self.assertEqual(code, 0)
                self.assertTrue(out.startswith("- **`/wiki:query`**"))


class RealPluginTests(unittest.TestCase):
    """実物の commands/ と docs/commands.md に対して、スクリプトとして実行する。"""

    def run_script(self, *extra, utf8_mode: bool = True):
        env = dict(os.environ)
        env["PYTHONUTF8"] = "1" if utf8_mode else "0"
        env.pop("PYTHONIOENCODING", None)
        return subprocess.run(
            [sys.executable, str(SCRIPTS / "wiki_help.py"), str(PLUGIN), *extra],
            capture_output=True, encoding="utf-8", check=False, env=env,
        )

    def test_every_command_has_details_without_warnings(self):
        base, warnings = wiki_help.docs_base_url(PLUGIN)
        self.assertEqual(warnings, [])
        for name in EXPECTED:
            with self.subTest(name=name):
                result = self.run_script(f"--command={name}")
                self.assertEqual(result.returncode, 0, result.stderr)
                self.assertEqual(result.stderr, "")
                self.assertTrue(result.stdout.startswith(f"### `/wiki:{name}`"))
                self.assertIn("\n**詳細**\n", result.stdout)
                # パーサーが読んだリンクは、外部の URL か、導入した版のタグの GitHub の URL で、実在するファイルを指す。
                for _, dest in parsed_destinations(result.stdout):
                    self.assertRegex(dest, r"^https?://")
                    if dest.startswith(base + "/"):
                        rel = unquote(urlsplit(dest).path[len(urlsplit(base).path) + 1:])
                        self.assertTrue((PLUGIN / rel).is_file(), dest)

    def test_json_details(self):
        result = self.run_script("--json", "--command=query")
        self.assertEqual(result.returncode, 0, result.stderr)
        data = json.loads(result.stdout)
        self.assertEqual(data["name"], "query")
        self.assertTrue(data["details"])

    def test_not_found_and_dash_value(self):
        result = self.run_script("--command=qury")
        self.assertEqual(result.returncode, 1)
        self.assertIn("近い名前: query", result.stderr)
        result = self.run_script("--command=nosuch")
        self.assertEqual(result.returncode, 1)
        self.assertIn("使えるコマンド: " + ", ".join(EXPECTED), result.stderr)
        # `=` でつなげば、- で始まる値も argparse の誤り（終了コード 2）にならない。
        result = self.run_script("--command=-x")
        self.assertEqual(result.returncode, 1, result.stderr)
        self.assertIn("コマンドが見つからない: -x", result.stderr)

    def test_list_is_unchanged_and_help_has_hint(self):
        result = self.run_script()
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual(result.stderr, "")
        lines = result.stdout.splitlines()
        self.assertEqual(len(lines), 3 * len(EXPECTED))
        self.assertIn("- **`/wiki:help`** `[command]`", lines)

    def test_without_utf8_mode(self):
        result = self.run_script("--command=query", utf8_mode=False)
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertIn("LLM Wiki に問い合わせ", result.stdout)
        self.assertEqual(result.stderr, "")


class HelpCommandTextTests(unittest.TestCase):
    """commands/help.md が、利用者の引数をそのままシェルに渡さない手順を書いていること。"""

    TEXT = (PLUGIN / "commands/help.md").read_text(encoding="utf-8")

    def test_frontmatter(self):
        meta = wiki_help.parse_command_frontmatter(self.TEXT)
        self.assertEqual(meta["argument-hint"], "[command]")
        self.assertIn("/wiki:` を付けずに", meta["argument-description"])

    def test_steps(self):
        self.assertIn("$ARGUMENTS", self.TEXT)
        self.assertIn(f"`{SHELL_SAFE}`", self.TEXT)
        self.assertIn("先頭の `/` を 1 つ除き、続けて先頭の `wiki:` を除く", self.TEXT)
        self.assertIn("引用符なしで `--command=`", self.TEXT)
        self.assertIn("スクリプトに引数を渡さない", self.TEXT)
        self.assertIn("そのままシェルのコマンド行に入れてはならない", self.TEXT)
        # 2 つの実行の形の、どちらも引数の文字列をそのまま埋め込まない。
        self.assertNotIn("$ARGUMENTS\"", self.TEXT)
        self.assertNotIn("'$ARGUMENTS'", self.TEXT)

    def test_shell_safe_pattern(self):
        pattern = re.compile(SHELL_SAFE)
        for name in EXPECTED + ["Query", "a-b", "x1"]:
            self.assertRegex(name, pattern)
        for value in ["query'", "query\"", "q`x`", "$HOME", "a;b", "a&b", "a|b", "a b", "/query",
                      "wiki:query", "-x", "a\nb", "a(b)", "a>b", "a<b", "a*b", "a?b", "a%b", "a^b", "a!b",
                      "クエリ", "a\\b"]:
            with self.subTest(value=value):
                self.assertIsNone(pattern.match(value))


if __name__ == "__main__":
    unittest.main()
