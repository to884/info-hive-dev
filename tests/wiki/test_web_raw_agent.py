"""URL の取り込みの raw の段を任せるエージェント（agents/web-raw.md）と、その手順の文書の静的な試験。

設計: docs/plans/wiki-web-raw-agent-2026-11-14.md

エージェントが実際に Sonnet で動き、後段をメインのモデルが行うかは、tests/wiki/check_web_raw_agent.py で
claude -p を動かして確かめる（費用がかかるので、この試験では動かさない）。

実行（標準ライブラリだけで動く）:
    python -X utf8 -m unittest tests/wiki/test_web_raw_agent.py -v
"""
from __future__ import annotations

import json
import re
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
PLUGIN = ROOT / "info-hive-wiki"
SKILL = PLUGIN / "skills/info-hive"
AGENT = PLUGIN / "agents/web-raw.md"
REFERENCE = SKILL / "references/web-raw.md"
COMMAND = PLUGIN / "commands/ingest.md"
sys.path.insert(0, str(Path(__file__).resolve().parent))

import check_web_raw_agent  # noqa: E402


def read(path: Path) -> str:
    return path.read_bytes().decode("utf-8")


def frontmatter(text: str) -> dict[str, str]:
    """エージェントの frontmatter（1 行の `キー: 値` だけ）。"""
    m = re.match(r"---\n(.*?)\n---\n", text, re.S)
    assert m, "frontmatter がない"
    out = {}
    for line in m.group(1).split("\n"):
        key, _, value = line.partition(":")
        out[key.strip()] = value.strip()
    return out


def json_fences(text: str) -> list[dict]:
    """```json のフェンスの中身（リストの中で字下げしたフェンスも読む）。"""
    out = []
    for indent, block in re.findall(r"^( *)```json\n(.*?)\n\1```", text, re.M | re.S):
        lines = [line[len(indent):] if line.startswith(indent) else line for line in block.split("\n")]
        out.append(json.loads("\n".join(lines)))
    return out


class AgentDefinitionTest(unittest.TestCase):
    def test_frontmatter(self):
        fm = frontmatter(read(AGENT))
        self.assertEqual(fm["name"], "web-raw")
        self.assertEqual(fm["model"], "sonnet")
        self.assertEqual(fm["omitClaudeMd"], "true")
        tools = {t.strip() for t in fm["tools"].split(",")}
        self.assertTrue({"Bash", "Read", "Edit", "Write"} <= tools, tools)
        self.assertFalse(tools & {"Agent", "Task", "WebFetch", "AskUserQuestion"}, tools)
        self.assertTrue(fm["description"])

    def test_plugin_root_paths_exist(self):
        paths = re.findall(r"\$\{CLAUDE_PLUGIN_ROOT\}/([\w./-]+)", read(AGENT))
        self.assertTrue(paths)
        for rel in paths:
            with self.subTest(rel=rel):
                self.assertTrue((PLUGIN / rel).exists(), rel)
        self.assertIn("${CLAUDE_PLUGIN_ROOT}/skills/info-hive/references/web-raw.md", read(AGENT))

    def test_agent_keeps_its_limits(self):
        body = read(AGENT)
        for phrase in ("--accept-warnings", "index.md", "log.md", "question", "model_unknown", "SCHEMA.md"):
            with self.subTest(phrase=phrase):
                self.assertIn(phrase, body)


class ReferenceTest(unittest.TestCase):
    def test_skill_root_paths_exist_and_no_plugin_root(self):
        text = read(REFERENCE)
        self.assertNotIn("${CLAUDE_PLUGIN_ROOT}", text)
        scripts = set(re.findall(r"<skill-root>/scripts/([\w.]+)", text))
        self.assertEqual(scripts, {"wiki_fetch.py", "wiki_rawcheck.py"})
        for name in scripts:
            self.assertTrue((SKILL / "scripts" / name).is_file(), name)

    def test_steps_w1_to_w8_live_here_only(self):
        ref, cmd = read(REFERENCE), read(COMMAND)
        for n in range(1, 9):
            with self.subTest(step=n):
                self.assertIn(f"- **W{n}.**", ref)
                self.assertNotIn(f"- **W{n}.**", cmd)
        self.assertIn("- **W9.**", cmd)
        self.assertNotIn("- **W9.**", ref)

    def test_json_examples_follow_the_rules(self):
        blocks = json_fences(read(REFERENCE))
        requests = [b for b in blocks if b.get("web_raw_request") == 1]
        reports = [b for b in blocks if b.get("web_raw") == 1]
        self.assertEqual(len(requests), 1)
        self.assertEqual(len(reports), 1)
        request = requests[0]
        self.assertEqual(set(request), {"web_raw_request", "url", "wiki_root", "raw_root", "slug", "fetch",
                                        "language", "language_reason", "conditions"})
        self.assertEqual(set(request["fetch"]), {"force", "keep_noise", "html_file", "page_url"})
        report = reports[0]
        self.assertEqual(report["status"], "done")
        self.assertEqual(report["warnings"], [])
        self.assertIsNone(report["question"])
        self.assertIsNone(report["error"])
        for key in ("slug", "raw", "url", "wiki_root", "raw_root", "model", "translated_by", "caption_names",
                    "language_override", "notes"):
            self.assertIn(key, report)

    def test_status_and_question_kinds_are_documented(self):
        text = read(REFERENCE)
        for status in ("done", "warnings", "needs_user", "failed"):
            self.assertIn(f"| `{status}` |", text)
        for kind in ("existing_differs", "already_ingested", "needs_browser"):
            self.assertIn(f"| `{kind}` |", text)
        for kind in ("fetch_failed", "not_initialized", "no_raw_root", "model_unknown"):
            self.assertIn(f"`{kind}`", text)


class EntryPointsTest(unittest.TestCase):
    def test_command_and_skill_point_to_the_reference(self):
        cmd = read(COMMAND)
        self.assertIn("references/web-raw.md", cmd)
        self.assertIn("wiki:web-raw", cmd)
        self.assertIn("`model` の引数は渡さない", cmd)
        self.assertIn("references/web-raw.md", read(SKILL / "SKILL.md"))
        self.assertIn("references/web-raw.md", read(SKILL / "references/ingest-workflow.md"))

    def test_version_and_changelog(self):
        version = json.loads(read(PLUGIN / ".claude-plugin/plugin.json"))["version"]
        self.assertIn(f"## [{version}]", read(PLUGIN / "CHANGELOG.md"))


class TranscriptCheckTest(unittest.TestCase):
    """実地の確かめのスクリプトの判定（記録を読まない部分）。"""

    def test_raw_write_detection(self):
        hits = ["echo x > raw/cqrs.md", "sed -i 's/a/b/' raw/cqrs.md", "cp a.png raw/assets/cqrs/a.png",
                'python x.py >> "raw/cqrs.md"', "Set-Content raw\\cqrs.md x"]
        misses = ["ls raw 2>&1; cat raw/cqrs.md", "wc -c raw/cqrs.md", "grep -n x raw/cqrs.md 2>/dev/null",
                  "python wiki_rawcheck.py check --raw-root raw --slug cqrs"]
        for c in hits:
            with self.subTest(hit=c):
                self.assertTrue(check_web_raw_agent.RAW_WRITE_RE.search(c))
        for c in misses:
            with self.subTest(miss=c):
                self.assertFalse(check_web_raw_agent.RAW_WRITE_RE.search(c))

    def test_shared_text_ignores_source_phrases(self):
        summary = "CQRS は Command Query Responsibility Segregation の略で、読み書きのモデルを分ける考え方である。" * 2
        raw = "Command Query Responsibility Segregation の略である。"
        self.assertEqual(check_web_raw_agent.shares_text(summary, [raw], raw), [])
        self.assertTrue(check_web_raw_agent.shares_text(summary, [summary]))


if __name__ == "__main__":
    unittest.main()
