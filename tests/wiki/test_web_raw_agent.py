"""URL の取り込みの raw の段を任せるエージェント（agents/web-raw.md）と、その手順の文書の静的な試験。

設計: docs/plans/wiki-web-raw-agent-2026-11-14.md

エージェントが実際に Sonnet で動き、後段をメインのモデルが行うかは、tests/wiki/check_web_raw_agent.py で
claude -p を動かして確かめる（費用がかかるので、この試験では動かさない）。

実行（標準ライブラリだけで動く）:
    python -X utf8 -m unittest tests/wiki/test_web_raw_agent.py -v
"""
from __future__ import annotations

import json
import os
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


# 報告の question.kind が取りうる値（references/web-raw.md の needs_user の表）
QUESTION_KINDS = {"existing_differs", "already_ingested", "old_work_dir", "needs_browser"}


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
        self.assertIn(asked["question"]["kind"], QUESTION_KINDS)
        self.assertTrue(asked["question"]["message"])
        self.assertIsNone(asked["error"])
        broke = reports["failed"]
        self.assertIn(broke["error"]["kind"], {"fetch_failed", "not_initialized", "no_raw_root", "model_unknown", "other"})
        self.assertIsNone(broke["question"])

    def test_status_and_question_kinds_are_documented(self):
        text = read(REFERENCE)
        for status in ("done", "warnings", "needs_user", "failed"):
            self.assertIn(f"| `{status}` |", text)
        for kind in sorted(QUESTION_KINDS):
            self.assertIn(f"| `{kind}` |", text)
        for kind in ("fetch_failed", "not_initialized", "no_raw_root", "model_unknown"):
            self.assertIn(f"`{kind}`", text)

    def test_needs_browser_can_continue_with_the_short_body(self):
        # 取り直さずに今の本文で続ける答えにも、依頼の変え方（conditions の決まった文）があり、W3 がそれに従う
        text = read(REFERENCE)
        phrase = "「本文が短いまま続ける"
        row = next(line for line in text.splitlines() if line.lstrip().startswith("| `needs_browser` |"))
        self.assertIn(phrase, row)
        # 続ける答えで fetch を残すと、前の呼び出しの --force や --html-file でまた取り直す（レビュー 5 の反例）
        self.assertNotIn("`fetch` は変えずに", row)
        w3 = text[text.index("- **W3.**"):text.index("- **W4.**")]
        self.assertIn("「本文が短いまま続ける", w3)

    def test_short_body_approval_is_bound_to_the_body(self):
        # 承認は本文のハッシュに結ぶ。エージェントが自分で --force で取り直すと、本文が変わっても承認が残るため
        # （レビュー 6 の反例）、最後の wiki_fetch.py の出力の fetched_sha256 と同じときだけ効かせる。
        text = read(REFERENCE)
        row = next(line for line in text.splitlines() if line.lstrip().startswith("| `needs_browser` |"))
        self.assertIn("「本文が短いまま続ける（fetched_sha256: <`question.fetched_sha256` の値>）」", row)
        w3 = text[text.index("- **W3.**"):text.index("- **W4.**")]
        self.assertIn("最後に実行した `wiki_fetch.py` の出力の `fetched_sha256` と同じなら", w3)
        asked = [b for b in json_fences(text) if b.get("web_raw") == 1 and b.get("status") == "needs_user"
                 and b["question"]["kind"] == "needs_browser"]
        self.assertTrue(asked and all(b["question"].get("fetched_sha256") for b in asked))
        status_row = next(line for line in text.splitlines() if line.startswith("| `needs_user` |"))
        self.assertIn("`fetched_sha256`", status_row)

    def test_one_shot_fetch_options_are_reset_on_every_call(self):
        # force、html_file、page_url は 1 回の取得への指示。呼び直すたびに戻さないと、続けるだけの呼び直しでも
        # 取り直して途中の作業を消す。戻せば、wiki_fetch.py は途中の写しから続ける
        # （tests/wiki/test_wiki_web_check.py の test_dom_take_resumes_without_fetch がスクリプトの側を確かめる）。
        text = read(REFERENCE)
        step4 = text[text.index("\n4. "):text.index("\n5. ")]
        self.assertIn("`fetch.force` を `false`、`fetch.html_file` と `fetch.page_url` を `null` に戻して", step4)
        self.assertIn("「本文が短いまま続ける」を消す", step4)

    def test_old_work_dir_does_not_hide_fetch_errors(self):
        # 終了コード 1 と 2 では、取得や --html-file の誤りを先に返す（old_work_dir の問いで隠さない）
        text = read(REFERENCE)
        w2 = text[text.index("- **W2.**"):text.index("- **W3.**")]
        bullet = next(line for line in w2.splitlines() if "`\"old_work_dir\": true`" in line)
        self.assertIn("終了コード 1 と 2 では、まずその誤り", bullet)
        self.assertIn("`failed`", bullet)


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
# wiki_fetch.py --json の出力（の一部）。実行者は、この形の結果を受け取ったかで決める。
FETCH_OUTPUT = json.dumps({"path": "raw/cqrs.md", "url": "https://martinfowler.com/bliki/CQRS.html",
                           "final_url": "https://martinfowler.com/bliki/CQRS.html", "source_sha256": "a" * 64, "source_sha256_of": "html", "unchanged": False,
                           "fetched_sha256": "b" * 64}, indent=2)
# wiki_rawcheck.py check --finish --json が通ったときの出力（の一部）
CHECK_OUTPUT = json.dumps({"stage": "check", "ok": True, "errors": [], "warnings": [], "work_dir_removed": True},
                          indent=2)


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
    def got(text, is_error=False):
        """直前の呼び出しの結果（write で、直前の tool_use の id に結ぶ）。"""
        part = {"type": "tool_result", "tool_use_id": "x", "content": text}
        if is_error:
            part["is_error"] = True
        return {"message": {"role": "user", "content": [part]}}

    @staticmethod
    def paired(records):
        """got の結果を直前の呼び出しの id に結び、結果のない呼び出しには成功の結果を足す（実際の記録の形）。"""
        out, last, answered = [], None, set()
        for rec in records:
            parts = rec["message"]["content"] if isinstance(rec["message"].get("content"), list) else []
            for part in parts:
                if part.get("type") == "tool_use":
                    if last is not None and last not in answered:
                        out.append({"message": {"role": "user", "content": [
                            {"type": "tool_result", "tool_use_id": last, "content": "ok"}]}})
                        answered.add(last)
                    last = part["id"]
                elif part.get("type") == "tool_result" and part.get("tool_use_id") == "x" and last is not None:
                    rec = json.loads(json.dumps(rec))
                    rec["message"]["content"][0]["tool_use_id"] = last
                    answered.add(last)
            out.append(rec)
        if last is not None and last not in answered:
            out.append({"message": {"role": "user", "content": [
                {"type": "tool_result", "tool_use_id": last, "content": "ok"}]}})
        return out

    def write(self, main_records, agents, project=None):
        main_records = self.paired(main_records)
        self.main_path.write_bytes("\n".join(json.dumps(r, ensure_ascii=False) for r in main_records).encode("utf-8"))
        paths = []
        for i, (meta, records) in enumerate(agents):
            records = self.paired(records)
            path = self.session / "subagents" / f"agent-{i}.jsonl"
            path.write_bytes("\n".join(json.dumps(r, ensure_ascii=False) for r in records).encode("utf-8"))
            path.with_suffix(".meta.json").write_bytes(json.dumps(meta).encode("utf-8"))
            path.with_suffix(".prefix.json").write_bytes(
                json.dumps({"state": {"model": meta.get("_model", "claude-sonnet-5-5")}}).encode("utf-8"))
            paths.append(path)
        return check_web_raw_agent.analyze_paths(self.main_path, paths, project or self.project, "opus")

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
        agent = [self.use("Bash", {"command": "python wiki_fetch.py URL --slug cqrs --json"}, sonnet),
                 self.got(FETCH_OUTPUT),
                 self.use("Bash", {"command": "python wiki_rawcheck.py freeze --slug cqrs"}, sonnet),
                 self.got("freeze: 通った"),
                 self.use("Bash", {"command": "python - <<'EOF'\nfrom pathlib import Path\n"
                                              "Path('raw/cqrs.md').write_text('訳', encoding='utf-8')\nEOF"}, sonnet),
                 self.use("Bash", {"command": "python wiki_rawcheck.py check --slug cqrs --finish"}, sonnet),
                 self.got(CHECK_OUTPUT),
                 *agent_extra]
        return main, [({"agentType": "wiki:web-raw", "launchedWithDefaults": True}, agent)]

    def failed(self, report):
        return sorted(c["check"] for c in report["checks"] if not c["ok"])

    def test_division_of_labor_passes(self):
        report = self.write(*self.good())
        self.assertTrue(report["ok"], self.failed(report))

    def test_relative_project_path_passes(self):
        """プロジェクトを相対パスで渡しても、記録の絶対パスと同じファイルとして比べる（PR #103 の指摘）。"""
        cwd = os.getcwd()
        os.chdir(self.project.parent)
        self.addCleanup(os.chdir, cwd)
        main, agents = self.good()
        report = self.write(main, agents, project=Path("proj"))
        self.assertTrue(report["ok"], self.failed(report))
        # 相対パスでも、ほかのサブエージェントの raw への書き込みは見つける
        agents.append(({"agentType": "general-purpose", "launchedWithDefaults": True, "_model": "claude-opus-5-5"},
                       [self.use("Write", {"file_path": str(self.project / "raw/cqrs.md"), "content": "x"})]))
        report = self.write(main, agents, project=Path("proj"))
        self.assertIn("raw に書いた（Edit、Write）のは wiki:web-raw だけ", self.failed(report))

    def test_script_runs_are_judged_by_their_results(self):
        """実行者は、コマンドの文字列ではなく受け取った結果の形で決める（PR #103 とレビュー 6 の指摘）。

        パスの引用符、サブコマンドの引用符、変数に入れたパスのどれでも、メインが freeze の出力を受け取れば不合格に
        する。表示だけの echo は実行に数えず、スクリプトの名前を含むコマンドは見直す一覧に出す。
        """
        name = "wiki_fetch.py と freeze を実行したのは wiki:web-raw だけ（道具の結果の形）"
        main, agents = self.good()
        quoted = []
        for rec in agents[0][1]:
            text = json.dumps(rec, ensure_ascii=False)
            for script in ("wiki_fetch.py", "wiki_rawcheck.py"):
                text = text.replace(f"python {script}", f"python '/plugin/scripts/{script}'")
            quoted.append(json.loads(text))
        agents = [(agents[0][0], quoted)]
        report = self.write(main, agents)
        self.assertTrue(report["ok"], self.failed(report))
        for command in ("python '/plugin/scripts/wiki_rawcheck.py' freeze --slug cqrs",
                        "& python 'C:/plugin/scripts/wiki_rawcheck.py' 'freeze' --wiki $w --raw-root $r --slug cqrs",
                        "& python $s freeze --wiki $w --raw-root $r --slug cqrs"):
            with self.subTest(command=command):
                report = self.write(main + [self.use("Bash", {"command": command}), self.got("freeze: 通った")], agents)
                self.assertIn(name, self.failed(report))
        echo = "echo 'wiki_rawcheck.py freeze を実行するのはエージェント'"
        report = self.write(main + [self.use("Bash", {"command": echo}), self.got(echo[6:-1])], agents)
        self.assertTrue(report["ok"], self.failed(report))
        self.assertIn(echo, report["bash_to_review"]["main"])

    def test_failed_write_over_an_old_summary_fails(self):
        """前の取り込みの要約ページが残っていても、今回の Write が失敗していれば、書いたと数えない（レビュー 6）。"""
        main, agents = self.good()
        at = next(i for i, r in enumerate(main)
                  if isinstance(r["message"]["content"], list) and r["message"]["content"][0].get("name") == "Write")
        main = main[:at + 1] + [self.got("Permission denied", is_error=True)] + main[at + 1:]
        report = self.write(main, agents)
        self.assertIn("メインが要約ページ、index.md、log.md を書いた（要約ページはファイルがある）", self.failed(report))

    def test_dotdot_write_into_raw_is_found(self):
        """`wiki/../raw/` のような書き込み先も、raw への書き込みとして見つける（レビュー 6）。"""
        main, agents = self.good(main_extra=[self.use("Write", {
            "file_path": str(self.project / "wiki" / ".." / "raw" / "cqrs.md"), "content": "x"})])
        report = self.write(main, agents)
        self.assertIn("raw に書いた（Edit、Write）のは wiki:web-raw だけ", self.failed(report))

    def test_missing_summary_file_fails(self):
        """要約ページの Write が失敗してファイルがなければ、不合格にする（PR #103 の指摘）。"""
        (self.project / "wiki/sources/cqrs.md").unlink()
        report = self.write(*self.good())
        failed = self.failed(report)
        self.assertIn("要約ページがある", failed)
        self.assertIn("メインが要約ページ、index.md、log.md を書いた（要約ページはファイルがある）", failed)

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
