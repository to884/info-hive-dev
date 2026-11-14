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
        reports = {b["status"]: b for b in blocks if b.get("web_raw") == 1}
        self.assertEqual(len(requests), 1)
        self.assertEqual(set(reports), {"done", "warnings", "needs_user", "failed"})
        request = requests[0]
        self.assertEqual(set(request), {"web_raw_request", "url", "wiki_root", "raw_root", "slug", "fetch",
                                        "language", "language_reason", "conditions"})
        self.assertEqual(set(request["fetch"]), {"force", "keep_noise", "html_file", "page_url"})
        done = reports["done"]
        for key in ("slug", "raw", "url", "wiki_root", "raw_root", "model", "translated_by", "caption_names",
                    "language_override", "warnings", "question", "error", "notes"):
            self.assertIn(key, done)
        self.assertEqual((done["warnings"], done["question"], done["error"]), ([], None, None))
        warned = reports["warnings"]
        self.assertTrue(warned["warnings"])
        for item in warned["warnings"]:
            self.assertEqual(set(item), {"kind", "line", "message", "proposed_reason"})
        self.assertEqual((warned["question"], warned["error"]), (None, None))
        asked = reports["needs_user"]
        self.assertIn(asked["question"]["kind"], {"existing_differs", "already_ingested", "needs_browser"})
        self.assertTrue(asked["question"]["message"])
        self.assertIsNone(asked["error"])
        broke = reports["failed"]
        self.assertIn(broke["error"]["kind"], {"fetch_failed", "not_initialized", "no_raw_root", "model_unknown", "other"})
        self.assertIsNone(broke["question"])

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


RAW_BODY = ("CQRS は、情報を更新するモデルと、情報を読むモデルを分けるという考え方である。"
            "多くのシステムでは一つのモデルで足りるが、複雑な領域では二つに分けると見通しがよくなることがある。"
            "ただし、分けることで複雑さが増すので、使う場面はよく選ぶべきだと著者は述べている。")
SUMMARY_BODY = ("この記事は、更新と参照のモデルを分ける設計の利点と危険をまとめたものである。"
                "要約の筆者は、適用する範囲を境界づけられた文脈の中に限るべきだという点を重く見た。")


class SyntheticTranscriptTest(unittest.TestCase):
    """作り物の記録で、実地の確かめの判定が、分担どおりの記録を通し、レビューの反例を止めることを確かめる。"""

    def setUp(self):
        import tempfile
        tmp = tempfile.TemporaryDirectory()
        self.addCleanup(tmp.cleanup)
        base = Path(tmp.name)
        self.project = base / "proj"
        for rel, text in (("wiki/sources/cqrs.md", "---\ntitle: \"CQRS\"\n---\n" + SUMMARY_BODY + "\n"),
                          ("wiki/index.md", "# 索引\n"), ("wiki/log.md", "## [2026-11-14] ingest | CQRS\n   raw: `wiki:web-raw` に任せた\n"),
                          ("raw/cqrs.md", "---\ntranslated_by: \"Claude Sonnet 5.5\"\n---\n" + RAW_BODY + "\n")):
            path = self.project / rel
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_bytes(text.encode("utf-8"))
        self.session = base / "sessions" / "s1"
        (self.session / "subagents").mkdir(parents=True)
        self.main_path = base / "sessions" / "s1.jsonl"

    @staticmethod
    def use(name, inp, model="claude-opus-5-5", uid=None):
        return {"message": {"role": "assistant", "model": model,
                            "content": [{"type": "tool_use", "id": uid or f"u-{name}-{abs(hash(json.dumps(inp)))}",
                                         "name": name, "input": inp}]}}

    @staticmethod
    def said(text, model="claude-opus-5-5"):
        return {"message": {"role": "assistant", "model": model, "content": [{"type": "text", "text": text}]}}

    @staticmethod
    def got(text):
        return {"message": {"role": "user", "content": [{"type": "tool_result", "tool_use_id": "x", "content": text}]}}

    def write(self, main_records, agents):
        self.main_path.write_bytes("\n".join(json.dumps(r, ensure_ascii=False) for r in main_records).encode("utf-8"))
        paths = []
        for i, (meta, records) in enumerate(agents):
            path = self.session / "subagents" / f"agent-{i}.jsonl"
            path.write_bytes("\n".join(json.dumps(r, ensure_ascii=False) for r in records).encode("utf-8"))
            path.with_suffix(".meta.json").write_bytes(json.dumps(meta).encode("utf-8"))
            path.with_suffix(".prefix.json").write_bytes(
                json.dumps({"state": {"model": meta.get("_model", "claude-sonnet-5-5")}}).encode("utf-8"))
            paths.append(path)
        return check_web_raw_agent.analyze_paths(self.main_path, paths, self.project, "opus")

    def good(self, main_extra=(), agent_extra=(), call_input=None):
        call = {"subagent_type": "wiki:web-raw", "prompt": "この依頼の raw を作る。\n```json\n{\"web_raw_request\": 1}\n```"}
        call.update(call_input or {})
        main = [self.use("Agent", call), self.got("Async agent launched"),
                {"message": {"role": "user", "content": "<task-notification>done</task-notification>"}},
                self.use("Read", {"file_path": str(self.project / "raw/cqrs.md")}), self.got(RAW_BODY),
                self.use("Write", {"file_path": str(self.project / "wiki/sources/cqrs.md"), "content": SUMMARY_BODY}),
                self.use("Edit", {"file_path": str(self.project / "wiki/index.md")}),
                self.use("Bash", {"command": "cd wiki && cat >> log.md <<'EOF'\nraw\nEOF"}), *main_extra]
        sonnet = "claude-sonnet-5-5"
        agent = [self.use("Bash", {"command": "python wiki_fetch.py URL --slug cqrs"}, sonnet),
                 self.use("Bash", {"command": "python wiki_rawcheck.py freeze --slug cqrs"}, sonnet),
                 self.use("Bash", {"command": "python - <<'EOF'\nfrom pathlib import Path\n"
                                              "Path('raw/cqrs.md').write_text('訳', encoding='utf-8')\nEOF"}, sonnet),
                 self.use("Bash", {"command": "python wiki_rawcheck.py check --slug cqrs --finish"}, sonnet),
                 self.got('{"ok": true, "work_dir_removed": true}'),
                 *agent_extra]
        return main, [({"agentType": "wiki:web-raw", "launchedWithDefaults": True}, agent)]

    def failed(self, report):
        return sorted(c["check"] for c in report["checks"] if not c["ok"])

    def test_division_of_labor_passes(self):
        report = self.write(*self.good())
        self.assertTrue(report["ok"], self.failed(report))

    def test_unrelated_subagent_is_listed_not_judged(self):
        main, agents = self.good()
        agents.append(({"agentType": "general-purpose", "launchedWithDefaults": True, "_model": "claude-opus-5-5"},
                       [self.said("調べた", "claude-opus-5-5")]))
        report = self.write(main, agents)
        self.assertTrue(report["ok"], self.failed(report))
        self.assertEqual([o["type"] for o in report["other_subagents"]], ["general-purpose"])

    def test_structured_counterexamples_fail(self):
        """確かに読み取れる違反（構造のある道具、メタデータ、応答のモデル、W8、文の受け渡し）は不合格にする。"""
        main, agents = self.good()
        other_writes_raw = (main + [self.use("Agent", {"subagent_type": "general-purpose", "prompt": "直す"}, uid="u-gp")],
                            agents + [({"agentType": "general-purpose", "launchedWithDefaults": True,
                                        "_model": "claude-opus-5-5"},
                                       [self.use("Write", {"file_path": str(self.project / "raw/cqrs.md"), "content": "x"})])])
        no_model = self.good()
        no_model[1][0] = (no_model[1][0][0], [{"message": {**r["message"], "model": ""}} for r in no_model[1][0][1]])
        no_defaults = self.good()
        no_defaults[1][0] = ({"agentType": "wiki:web-raw"}, no_defaults[1][0][1])
        no_finish = self.good()
        no_finish[1][0] = (no_finish[1][0][0], [r for r in no_finish[1][0][1]
                                               if "--finish" not in json.dumps(r, ensure_ascii=False)
                                               and "work_dir_removed" not in json.dumps(r, ensure_ascii=False)])
        before_main, before_agents = self.good()
        cases = {
            "other_subagent_writes_raw": other_writes_raw,
            "response_model_missing": no_model,
            "launched_with_defaults_missing": no_defaults,
            "check_finish_missing": no_finish,
            "main_text_before_agent": ([self.said("訳はこうする: " + RAW_BODY)] + before_main, before_agents),
            "second_prompt_has_raw": self.good(main_extra=[self.use("Agent", {
                "subagent_type": "wiki:web-raw", "prompt": "この訳を書き込む: " + RAW_BODY}, uid="u-second")]),
            "model_passed": self.good(call_input={"model": "opus"}),
            "agent_edits_index": self.good(agent_extra=[self.use(
                "Edit", {"file_path": str(self.project / "wiki/index.md")}, "claude-sonnet-5-5")]),
        }
        for name, (main, agents) in cases.items():
            with self.subTest(case=name):
                report = self.write(main, agents)
                self.assertFalse(report["ok"], name)

    def test_bash_writes_are_listed_for_review(self):
        """Bash のコマンドの中の書き込みは合否を決めず、担当ごとに一覧に出す（レビューの反例を含む）。"""
        sonnet = "claude-sonnet-5-5"
        main_cmds = ["python -c \"from pathlib import Path; Path('raw/x.md').write_text('changed', encoding='utf-8')\"",
                     "mv raw/assets/cqrs/cqrs-01.png /tmp/stolen.png", "cd raw && echo changed > cqrs.md"]
        agent_cmds = ["python -c \"from pathlib import Path; Path('wiki/index.md').write_text('changed')\"",
                      "mv wiki/index.md /tmp/stolen-index.md"]
        report = self.write(*self.good(main_extra=[self.use("Bash", {"command": c}) for c in main_cmds],
                                       agent_extra=[self.use("Bash", {"command": c}, sonnet) for c in agent_cmds]))
        self.assertTrue(report["ok"], self.failed(report))
        listed = report["bash_to_review"]
        for c in main_cmds:
            self.assertIn(c[:300], listed["main"])
        for c in agent_cmds:
            self.assertIn(c[:300], listed["wiki:web-raw"])


class TranscriptCheckTest(unittest.TestCase):
    """実地の確かめのスクリプトの判定（記録を読まない部分）。"""

    def test_bash_write_targets(self):
        targets = check_web_raw_agent.bash_write_targets(
            ["cd wiki && cat >> log.md <<'EOF'\nx\nEOF", "ls raw 2>&1; echo a > 'index.md'", "cmd 2>/dev/null",
             "python x.py &> out.txt"])
        self.assertEqual(targets, ["log.md", "index.md"])
        self.assertTrue(check_web_raw_agent.WIKI_PAGE_RE.search("wiki/sources/ブルームフィルタ.md"))
        self.assertFalse(check_web_raw_agent.WIKI_PAGE_RE.search("wiki/.wiki-cache/ingest/a/fetched.md"))

    def test_shared_text_ignores_source_phrases(self):
        summary = "CQRS は Command Query Responsibility Segregation の略で、読み書きのモデルを分ける考え方である。" * 2
        raw = "Command Query Responsibility Segregation の略である。"
        self.assertEqual(check_web_raw_agent.shares_text(summary, [raw], raw), [])
        self.assertTrue(check_web_raw_agent.shares_text(summary, [summary]))


if __name__ == "__main__":
    unittest.main()
