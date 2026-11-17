"""Codex の配布契約と、共通の操作手順を表示する入口の試験。"""
from __future__ import annotations

import contextlib
import io
import json
import os
import shutil
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path
from unittest import mock

ROOT = Path(__file__).resolve().parents[2]
PLUGIN = ROOT / "info-hive-wiki"
SCRIPTS = PLUGIN / "skills/info-hive/scripts"
sys.path.insert(0, str(SCRIPTS))
import wiki_codex  # noqa: E402
import wiki_help  # noqa: E402


def read_json(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def run_main(*args: str) -> tuple[int, str, str]:
    out, err = io.StringIO(), io.StringIO()
    with contextlib.redirect_stdout(out), contextlib.redirect_stderr(err):
        code = wiki_codex.main(list(args))
    return code, out.getvalue(), err.getvalue()


class CodexPackageTests(unittest.TestCase):
    def test_identity_and_version_match_claude(self):
        claude = read_json(PLUGIN / ".claude-plugin/plugin.json")
        codex = read_json(PLUGIN / ".codex-plugin/plugin.json")
        for key in ("name", "version", "repository", "license"):
            self.assertEqual(codex[key], claude[key], key)
        self.assertTrue((PLUGIN / codex["skills"] / "info-hive/SKILL.md").is_file())

    def test_mcp_launches_same_script_without_claude_variable(self):
        claude = read_json(PLUGIN / ".mcp.json")["mcpServers"]["wiki"]
        codex = read_json(PLUGIN / ".codex-plugin/plugin.json")["mcpServers"]["wiki"]
        self.assertEqual(codex["command"], claude["command"])
        self.assertEqual(codex["args"][:-1], claude["args"][:-1])
        self.assertEqual(codex["cwd"], ".")
        self.assertNotIn("${", " ".join(codex["args"]))
        self.assertEqual(codex["args"][-1], claude["args"][-1].removeprefix("${CLAUDE_PLUGIN_ROOT}/"))
        self.assertTrue((PLUGIN / codex["cwd"] / codex["args"][-1]).is_file())
        self.assertGreaterEqual(codex["startup_timeout_sec"], 120)
        self.assertEqual(codex["env"]["PYTHONUTF8"], "1")
        self.assertIn("UV_SYSTEM_CERTS", codex["env_vars"])
        self.assertIn("INFO_HIVE_DATA_DIR", codex["env_vars"])

    @unittest.skipUnless((ROOT / "info-hive-marketplace/.agents/plugins/marketplace.json").is_file(),
                         "配布カタログの試験は marketplace のチェックアウトがある場合だけ行う")
    def test_remote_marketplace_exposes_only_supported_plugin(self):
        catalog = read_json(ROOT / "info-hive-marketplace/.agents/plugins/marketplace.json")
        self.assertEqual(catalog["name"], "info-hive")
        self.assertEqual([p["name"] for p in catalog["plugins"]], ["wiki"])
        entry = catalog["plugins"][0]
        self.assertEqual(entry["source"], {"source": "url", "url": "https://github.com/to884/info-hive-wiki.git"})
        self.assertNotIn("version", entry)

    def test_dev_marketplace_points_to_this_checkout(self):
        catalog = read_json(ROOT / ".agents/plugins/marketplace.json")
        self.assertEqual(catalog["name"], "info-hive-dev")
        entry = catalog["plugins"][0]
        self.assertEqual(entry["source"]["source"], "local")
        self.assertEqual((ROOT / entry["source"]["path"]).resolve(), PLUGIN.resolve())
        self.assertNotIn("version", entry)


class CodexWorkflowTests(unittest.TestCase):
    def test_every_command_has_a_workflow_and_help(self):
        commands, warnings = wiki_help.collect_commands(PLUGIN, "wiki")
        self.assertFalse(warnings)
        self.assertEqual({c["name"] for c in commands}, set(wiki_help.PREFERRED_ORDER))
        for command in commands:
            operation = command["name"]
            with self.subTest(operation=operation):
                code, out, err = run_main("help", operation)
                self.assertEqual((code, err), (0, ""))
                self.assertIn(f"$wiki:info-hive {operation}", out)
                self.assertNotIn("/wiki:", out)
                if operation == "help":
                    continue
                text = wiki_codex.workflow(PLUGIN, operation)
                self.assertIn("# Codex での操作", text)
                self.assertNotIn("${CLAUDE_PLUGIN_ROOT}", text)
                self.assertNotIn("$ARGUMENTS", text)
                self.assertIn("利用者の引数", text)

    def test_workflow_uses_canonical_body(self):
        text = (PLUGIN / "commands/query.md").read_text(encoding="utf-8")
        body = text[wiki_help.FRONTMATTER_RE.match(text).end():].lstrip()
        self.assertEqual(wiki_codex.workflow(PLUGIN, "query"), wiki_codex.HEADER + wiki_codex.adapt(body))
        self.assertIn("query-confidence.md", wiki_codex.workflow(PLUGIN, "query"))

    def test_absolute_script_paths_are_skill_relative_placeholders(self):
        text = wiki_codex.workflow(PLUGIN, "query")
        self.assertIn('"<skill-root>/scripts/wiki_search.py"', text)
        self.assertNotIn("skills/info-hive/references/", text)

    def test_help_is_for_codex_and_does_not_run_a_workflow(self):
        code, out, err = run_main("help")
        self.assertEqual((code, err), (0, ""))
        for operation in wiki_help.PREFERRED_ORDER:
            self.assertIn(f"$wiki:info-hive {operation}", out)
        self.assertNotIn("/wiki:", out)
        self.assertNotIn("# Codex での操作", out)

    def test_invalid_help_name_is_not_executed(self):
        code, out, err = run_main("help", "query; Write-Output BAD")
        self.assertEqual(code, 1)
        self.assertEqual(out, "")
        self.assertIn("使えるコマンド", err)

    def test_path_traversal_is_rejected(self):
        for operation in ("../init", "../../AGENTS", "query.md", "", "help"):
            with self.subTest(operation=operation), self.assertRaises(ValueError):
                wiki_codex.workflow(PLUGIN, operation)

    def test_workflow_arguments_are_not_accepted(self):
        with contextlib.redirect_stderr(io.StringIO()), self.assertRaises(SystemExit) as result:
            wiki_codex.main(["query", "a; echo BAD"])
        self.assertEqual(result.exception.code, 2)

    def test_missing_plugin_is_a_failure(self):
        with tempfile.TemporaryDirectory() as folder, mock.patch.object(wiki_codex, "PLUGIN_ROOT", Path(folder)):
            code, out, err = run_main("query")
        self.assertEqual((code, out), (1, ""))
        self.assertIn("操作手順を読めない", err)

    def test_codex_constraints_precede_claude_instructions(self):
        text = wiki_codex.workflow(PLUGIN, "ingest")
        self.assertLess(text.index("Claude CLI、Agent ツール、Sonnet の起動は行わない"), text.index("## Web ページの取り込み"))
        self.assertIn("locate --host codex --current", text)
        self.assertIn("依頼を含むターン全体より前の範囲に固定する", text)
        self.assertIn("AGENTS.md", text)

    def test_copied_plugin_works_from_an_unrelated_project_without_writes(self):
        with tempfile.TemporaryDirectory(prefix="wiki-codex-") as folder:
            base = Path(folder)
            plugin = base / "日本語 プラグイン"
            scripts = plugin / "skills/info-hive/scripts"
            shutil.copytree(SCRIPTS, scripts, ignore=shutil.ignore_patterns("__pycache__", "browse_assets"))
            shutil.copytree(PLUGIN / "commands", plugin / "commands")
            shutil.copytree(PLUGIN / ".claude-plugin", plugin / ".claude-plugin")
            shutil.copytree(PLUGIN / "docs", plugin / "docs")
            project = base / "利用者の プロジェクト"
            project.mkdir()
            before = {p.relative_to(base): p.read_bytes() for p in base.rglob("*") if p.is_file()}
            result = subprocess.run(
                [sys.executable, str(scripts / "wiki_codex.py"), "query"],
                cwd=project, env={**os.environ, "PYTHONUTF8": "0", "PYTHONIOENCODING": "cp932"}, capture_output=True,
                encoding="utf-8", timeout=20,
            )
            self.assertEqual(result.returncode, 0, result.stderr)
            self.assertIn("query-confidence.md", result.stdout)
            after = {p.relative_to(base): p.read_bytes() for p in base.rglob("*") if p.is_file()}
            self.assertEqual(before, after)


if __name__ == "__main__":
    unittest.main()
