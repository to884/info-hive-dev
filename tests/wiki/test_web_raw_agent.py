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
        self.assertTrue(done["check"]["completed"])
        self.assertEqual(done["check"]["translation"]["state"], "checked")
        for key in ("slug", "raw", "url", "wiki_root", "raw_root", "model", "translated_by", "caption_names",
                    "language_override", "warnings", "question", "error", "notes"):
            self.assertIn(key, done)
        self.assertEqual((done["warnings"], done["question"], done["error"]), ([], None, None))
        warned = reports["warnings"]
        self.assertFalse(warned["check"]["completed"])
        self.assertTrue(warned["warnings"])
        for item in warned["warnings"]:
            self.assertEqual(set(item), {"kind", "line", "message", "proposed_reason"})
        self.assertEqual((warned["question"], warned["error"]), (None, None))
        asked = reports["needs_user"]
        self.assertIn(asked["question"]["kind"], QUESTION_KINDS)
        self.assertTrue(asked["question"]["message"])
        self.assertIsNone(asked["error"])
        broke = reports["failed"]
        self.assertIn(broke["error"]["kind"], {"fetch_failed", "youtube", "not_initialized", "no_raw_root", "model_unknown", "other"})
        self.assertIsNone(broke["question"])

    def test_status_and_question_kinds_are_documented(self):
        text = read(REFERENCE)
        for status in ("done", "warnings", "needs_user", "failed"):
            self.assertIn(f"| `{status}` |", text)
        for kind in sorted(QUESTION_KINDS):
            self.assertIn(f"| `{kind}` |", text)
        for kind in ("fetch_failed", "youtube", "not_initialized", "no_raw_root", "model_unknown"):
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

    def test_every_retake_goes_back_to_w3(self):
        # 取り直したら、どの段からでも W2 の出力の扱いと W3 に戻る（レビュー 7 の重大 1。W5 の取り直しが
        # 「W4 からやり直す」で W3 を飛ばし、承認を照らし合わせずに新しい本文で進めた）。
        text = read(REFERENCE)
        steps = text[text.index("## W1〜W8"):]
        steps = steps[:steps.index("\n## ", 5)] if "\n## " in steps[5:] else steps
        self.assertIn("**取り直したら、W2 の出力の扱いと W3 に戻る。**", steps)
        # 途中の写しから続けるときは取り直しではないので、段ごとの続け方に従う（レビュー 8 の軽微。frozen の写しに
        # W3 から戻ると、訳したあとの raw に freeze をかけ直してしまう）
        rule = steps[steps.index("**取り直したら"):]
        rule = rule[:rule.index("\n")]
        self.assertIn('`"unchanged": false`', rule)
        self.assertIn('`"work_dir": true`', rule)
        retakes = [s for s in re.split(r"(?<=。)", steps) if re.search(r"取り直|--force", s)]
        self.assertTrue(retakes)
        for sentence in retakes:
            with self.subTest(sentence=sentence[:80]):
                # 取り直しの文で、W3 より後の段から続けると書かない
                self.assertNotRegex(sentence, r"W[4-8][^。]*?から(?:やり直|続け|進)")

    def test_old_work_dir_does_not_hide_fetch_errors(self):
        # 終了コード 1 と 2 では、取得や --html-file の誤りを先に返す（old_work_dir の問いで隠さない）
        text = read(REFERENCE)
        w2 = text[text.index("- **W2.**"):text.index("- **W3.**")]
        bullet = next(line for line in w2.splitlines() if "`\"old_work_dir\": true`" in line)
        self.assertIn("終了コード 1 と 2 では、まずその誤り", bullet)
        self.assertIn("`failed`", bullet)

    def test_w8_runs_check_with_json(self):
        # W8 は check --finish --json で動かす。表示名と、写しを消したかが、機械で読める形で記録に残る（13 回目）
        text = read(REFERENCE)
        w8 = next(line for line in text.splitlines() if line.startswith("- **W8.**"))
        self.assertIn('--slug "<スラッグ>" --finish --json`', w8)
        self.assertIn("`--json` は外さない", w8)


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
CHECK_OUTPUT = json.dumps({"stage": "check", "ok": True, "completed": True, "needs_translation": True,
                           "translation": {"state": "checked", "checked_blocks": 1}, "language_override": None,
                           "translated_by": "Claude Sonnet 5.5",
                           "caption_names": ["Claude Sonnet 5.5"], "errors": [], "warnings": [], "work_dir_removed": True},
                          indent=2)
# check --finish --accept-warnings で、警告が残ったまま写しを消したときの出力（の一部）
ACCEPTED_OUTPUT = json.dumps({"stage": "check", "ok": True, "completed": True, "needs_translation": True,
                              "translation": {"state": "checked", "checked_blocks": 1}, "language_override": None,
                              "translated_by": "Claude Sonnet 5.5",
                              "caption_names": ["Claude Sonnet 5.5"], "errors": [],
                              "warnings": [{"kind": "style", "line": None, "message": "文体が混ざっている"}],
                              "work_dir_removed": True}, indent=2)
W8 = ("W8 の check --finish --json を wiki:web-raw が自分で動かして通った（警告を受け入れる流れでは、メインが警告の"
      "残ったまま終える）")
SHAPES = "raw に、確かめが読むスクリプトの出力の形の文字列がない（あれば、記録の中で本物の出力と見分けられず、判定できない）"
UNREADABLE = "セッションの記録のすべての行と、エージェントのメタデータを読めた（読めないものの証拠は判定できない）"
GAPS = "check --finish の呼び出しの結果と、check の JSON をすべて読めた（読めない回があれば、違反がないとは言えない）"


class SyntheticTranscriptTest(unittest.TestCase):
    """作り物の記録で、実地の確かめの判定が、分担どおりの記録を通し、レビューの反例を止めることを確かめる。"""

    def setUp(self):
        import tempfile
        tmp = tempfile.TemporaryDirectory()
        self.addCleanup(tmp.cleanup)
        base = Path(tmp.name)
        self.project = base / "proj"
        for rel, text in (("wiki/sources/cqrs.md", "---\ntitle: \"CQRS\"\n---\n" + SUMMARY_BODY + "\n"),
                          ("wiki/index.md", "# 索引\n\n- [[cqrs]]: CQRS の要約\n"), ("wiki/log.md", "## [2026-11-14] ingest | CQRS\n   raw: `wiki:web-raw` に任せた\n"),
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
    def got(text, is_error=False, used=None):
        """直前の呼び出しの結果（write で、直前の tool_use の id に結ぶ）。

        used は、記録の toolUseResult（Claude Code が書く。Agent なら、起動したサブエージェントの agentId）。
        """
        part = {"type": "tool_result", "tool_use_id": "x", "content": text}
        if is_error:
            part["is_error"] = True
        record = {"message": {"role": "user", "content": [part]}}
        if used is not None:
            record["toolUseResult"] = used
        return record

    @staticmethod
    def launched(agent_id="0"):
        """Agent の起動の結果。記録のファイル agent-<agent_id>.jsonl と結ぶ（write は agent-<番号>.jsonl に書く）。"""
        return SyntheticTranscriptTest.got("Async agent launched",
                                           used={"agentId": agent_id, "status": "async_launched"})

    @staticmethod
    def paired(records, unanswered=()):
        """got の結果を直前の呼び出しの id に結び、結果のない呼び出しには成功の結果を足す（実際の記録の形）。

        unanswered の id の呼び出しには足さない（結果の欠けた記録を試すため。足すと、欠けたことが消える）。
        """
        out, last, answered = [], None, set(unanswered)
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

    def write(self, main_records, agents, project=None, unanswered=()):
        main_records = self.paired(main_records, unanswered)
        self.main_path.write_bytes("\n".join(json.dumps(r, ensure_ascii=False) for r in main_records).encode("utf-8"))
        paths = []
        for i, (meta, records) in enumerate(agents):
            records = self.paired(records, unanswered)
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
        main = [self.use("Agent", call), self.launched(),
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
                 self.use("Bash", {"command": "python wiki_rawcheck.py check --wiki wiki --raw-root raw --slug cqrs "
                                              "--finish --json"}, sonnet),
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

    def test_script_runs_by_others_are_listed_not_judged(self):
        """ほかの担当がスクリプトを動かさなかったことは、記録からは示せないので、合否を決めずに一覧に出す（レビュー 7）。

        wiki:web-raw が出力を受け取ったこと（あったことの証拠）は、パスの引用符を変えても読む。メインが freeze を
        動かしたときは、結果の形が見えれば other_script_runs に、出力を捨てた形でも、コマンドは bash_to_review に出る。
        """
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
        self.assertEqual(report["other_script_runs"], {})
        for command, output in (("& python $s freeze --wiki $w --raw-root $r --slug cqrs", "freeze: 通った"),
                                ("& python $s freeze --wiki (Join-Path $PWD wiki) --slug cqrs > $null", "")):
            with self.subTest(command=command):
                report = self.write(main + [self.use("PowerShell", {"command": command}), self.got(output)], agents)
                self.assertTrue(report["ok"], self.failed(report))
                self.assertIn(command, report["bash_to_review"]["main"])
                self.assertEqual(bool(report["other_script_runs"]), bool(output))

    def test_agent_must_receive_fetch_and_freeze_output(self):
        """wiki:web-raw が取得か freeze の出力を受け取っていなければ不合格にする。"""
        name = "wiki:web-raw が wiki_fetch.py と freeze の出力を受け取った（道具の結果の形）"
        main, agents = self.good()
        records = [r for r in agents[0][1] if "freeze: 通った" not in json.dumps(r, ensure_ascii=False)]
        report = self.write(main, [(agents[0][0], records)])
        self.assertIn(name, self.failed(report))

    def test_w8_needs_the_agents_own_finish(self):
        """W8 は、wiki:web-raw が自分で check --finish を動かして通ったことで決める（レビュー 7）。

        前の出力を cat で表示しただけ、メインが警告のない check で代わりに終えた、は通さない。
        警告を受け入れる流れで、メインが警告の残ったまま終えたとき（--accept-warnings）は通し、終えた担当を書く。
        """
        name = W8
        finish = "python wiki_rawcheck.py check --slug cqrs --finish"
        main, agents = self.good()
        sonnet = "claude-sonnet-5-5"
        without = [r for r in agents[0][1] if "--finish" not in json.dumps(r, ensure_ascii=False)
                   and "work_dir_removed" not in json.dumps(r, ensure_ascii=False)]
        cases = {
            "cat_of_old_output": (main, [(agents[0][0], without + [
                self.use("Bash", {"command": "cat previous-check-output.json"}, sonnet), self.got(CHECK_OUTPUT)])]),
            "main_finished_without_accept": (main + [self.use("Bash", {"command": finish}), self.got(CHECK_OUTPUT)],
                                             [(agents[0][0], without)]),
        }
        for case, (m, a) in cases.items():
            with self.subTest(case=case):
                self.assertIn(name, self.failed(self.write(m, a)))
        accepted = main + [self.use("Bash", {"command": finish + " --accept-warnings"}), self.got(ACCEPTED_OUTPUT)]
        report = self.write(accepted, [(agents[0][0], without)])
        self.assertTrue(report["ok"], self.failed(report))
        self.assertEqual(report["w8_finished_by"], ["main"])

    def test_w8_requires_completion_and_translation_evidence(self):
        main, agents = self.good()
        cases = {
            "not_completed": {"completed": False},
            "missing_completed": {"completed": None},
            "missing_translation": {"translation": None},
            "untranslated": {"translation": {"state": "incomplete", "checked_blocks": 1}},
            "non_boolean_requirement": {"needs_translation": "false"},
            "inconsistent_requirement": {"needs_translation": False},
            "keep": {"language_override": {"value": "keep", "reason": "原文の再現性"}},
            "no_translator": {"translated_by": ""},
            "non_string_translator": {"translated_by": ["Model"]},
            "non_integer_block_count": {"translation": {"state": "checked", "checked_blocks": True}},
        }
        for name, changes in cases.items():
            with self.subTest(name=name):
                result = json.loads(CHECK_OUTPUT)
                result.update(changes)
                if name == "missing_completed":
                    result.pop("completed")
                records = [self.got(json.dumps(result)) if self._is_check(record) else record
                           for record in agents[0][1]]
                failures = self.failed(self.write(main, [(agents[0][0], records)]))
                self.assertIn(W8, failures)
                self.assertIn("写しを消したすべての JSON に、完了と翻訳の検査結果がある", failures)

    def test_later_success_does_not_hide_an_unverified_completion(self):
        main, agents = self.good()
        result = json.loads(CHECK_OUTPUT)
        result.pop("completed")
        records = [self.got(json.dumps(result)) if self._is_check(record) else record
                   for record in agents[0][1]]
        records += [self.use("Bash", {"command": "python wiki_rawcheck.py check --slug cqrs --finish --json"},
                             "claude-sonnet-5-5"), self.got(CHECK_OUTPUT)]
        report = self.write(main, [(agents[0][0], records)])
        self.assertIn("写しを消したすべての JSON に、完了と翻訳の検査結果がある", self.failed(report))

    def test_failed_write_over_an_old_summary_fails(self):
        """前の取り込みの要約ページが残っていても、今回の Write が失敗していれば、書いたと数えない（レビュー 6）。"""
        main, agents = self.good()
        at = next(i for i, r in enumerate(main)
                  if isinstance(r["message"]["content"], list) and r["message"]["content"][0].get("name") == "Write")
        main = main[:at + 1] + [self.got("Permission denied", is_error=True)] + main[at + 1:]
        report = self.write(main, agents)
        self.assertIn("メインが要約ページを Edit か Write で書いた（成功した呼び出しで、ファイルがある）", self.failed(report))

    def test_extended_prefix_write_into_raw_is_found(self):
        """Windows の拡張パスの接頭辞が付いた書き込み先も、raw への書き込みとして見つける（レビュー 7）。"""
        target = "\\\\?\\" + str(self.project / "raw" / "cqrs.md")
        self.assertEqual(check_web_raw_agent.norm(target, self.project),
                         check_web_raw_agent.norm(self.project / "raw" / "cqrs.md", self.project))
        main, agents = self.good(main_extra=[self.use("Write", {"file_path": target, "content": "x"})])
        self.assertIn("raw に書いた（Edit、Write）のは wiki:web-raw だけ", self.failed(self.write(main, agents)))

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
        self.assertIn("メインが要約ページを Edit か Write で書いた（成功した呼び出しで、ファイルがある）", failed)

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
            self.assertIn(c, listed["main"])
        for c in agent_cmds:
            self.assertIn(c, listed["wiki:web-raw"])


    def test_review8_counterexamples(self):
        """8 回目のレビューの反例。範囲の中の違反を通さず、手順に従った取り込みを落とさない。"""
        sonnet = "claude-sonnet-5-5"

        def said_as(text, model, mid):
            return {"message": {"role": "assistant", "model": model, "id": mid, "content": [{"type": "text", "text": text}]}}

        main, agents = self.good()
        # 1. 別の応答が同じ文を返しても、モデルの違いを落とさない
        same = (main, [(agents[0][0], agents[0][1] + [said_as("確かめた。", sonnet, "m1"),
                                                      said_as("確かめた。", "claude-opus-5-5", "m2")])])
        self.assertIn("wiki:web-raw のすべての応答のモデルと、prefix.json のモデルが Sonnet", self.failed(self.write(*same)))
        # 要求の写し（api-request-blob。モデルを持たない）は、応答に数えない
        blob = {"type": "api-request-blob", "message": {"role": "assistant", "content": [
            {"type": "text", "text": "前の応答の写し"}]}}
        report = self.write(main, [(agents[0][0], agents[0][1] + [blob])])
        self.assertTrue(report["ok"], self.failed(report))
        # 3. 索引の更新は、ファイルの中身で決める（9 回目: 別のフォルダーの index.md に書いても、索引にリンクがなければ通さない）
        index = self.project / "wiki/index.md"
        original_index = index.read_bytes()
        index.write_bytes("# 索引\n".encode("utf-8"))
        self.addCleanup(index.write_bytes, original_index)
        moved = main + [self.use("Bash", {"command": "mkdir -p notes && printf 'topic' >> notes/index.md"})]
        self.assertIn("index.md に、メインが書いた要約ページのすべてへのリンクがある（ファイルの中身）",
                      self.failed(self.write(moved, agents)))
        index.write_bytes(original_index)
        # 5. 表示名は W8 の check --json の結果から取り、Sonnet でなければ不合格（9 回目: リストの中の補足も、
        #    プラグインが見分けた名前なら落とさない）
        opus = CHECK_OUTPUT.replace('"caption_names": [\n    "Claude Sonnet 5.5"\n  ]',
                                    '"caption_names": [\n    "Claude Opus 5.5"\n  ]')
        self.assertNotEqual(opus, CHECK_OUTPUT)
        swapped = [self.got(opus) if CHECK_OUTPUT in json.dumps(r, ensure_ascii=False) or self._is_check(r) else r
                   for r in agents[0][1]]
        self.assertIn("W8 の check の結果の、訳と補足の表示名が Sonnet（空はよい）",
                      self.failed(self.write(main, [(agents[0][0], swapped)])))
        # 6. エージェントが警告の残ったまま写しを消したら（--accept-warnings を付けたときだけ起きる）不合格。
        #    W8 の証拠にもしない
        accepted = [self.got(ACCEPTED_OUTPUT) if self._is_check(r) else r for r in agents[0][1]]
        failed = self.failed(self.write(main, [(agents[0][0], accepted)]))
        self.assertIn("wiki:web-raw は警告を受け入れて終えていない（check --finish の出力。どの回も）", failed)

    def test_review10_counterexamples(self):
        """10 回目のレビューの反例（1、2、3、5）。"""
        main, agents = self.good()
        index = self.project / "wiki/index.md"
        log = self.project / "wiki/log.md"
        original_index, original_log = index.read_bytes(), log.read_bytes()
        self.addCleanup(index.write_bytes, original_index)
        self.addCleanup(log.write_bytes, original_log)
        template = PLUGIN / "skills" / "info-hive" / "assets"
        # 1. 初期の index.md と log.md の説明文の記入例（インラインのコード）だけでは通さない
        index.write_bytes((template / "index.md.template").read_bytes().replace("[[消費税]]".encode("utf-8"), b"[[cqrs]]"))
        log.write_bytes((template / "log.md.template").read_bytes() + "   raw: `wiki:web-raw` に任せた\n".encode("utf-8"))
        failed = self.failed(self.write(main, agents))
        self.assertIn("index.md に、メインが書いた要約ページのすべてへのリンクがある（ファイルの中身）", failed)
        self.assertIn("log の取り込みの項目に、raw の段の分担のサブ行がある（ファイルの中身）", failed)
        log.write_bytes(original_log)
        # 2. パス付きのリンクと、別名やアンカーの付いたリンクは通す
        for link in ("[[sources/cqrs]]", "[[sources/cqrs|別名]]", "[[cqrs|別名]]", "[[cqrs#要点]]"):
            with self.subTest(link=link):
                index.write_bytes(f"# 索引\n\n- {link}: CQRS の要約\n".encode("utf-8"))
                report = self.write(main, agents)
                self.assertTrue(report["ok"], self.failed(report))
        index.write_bytes(original_index)
        # 3. 1 つの呼び出しで check を 2 度動かしたときは、写しを消した最後の出力の表示名を使う
        before = CHECK_OUTPUT.replace('"Claude Sonnet 5.5"', '"Claude Opus 5.5"').replace(
            '"work_dir_removed": true', '"work_dir_kept": "errors"')
        self.assertNotIn("work_dir_removed", before)
        twice = [self.got(before + "\n" + CHECK_OUTPUT) if self._is_check(r) else r for r in agents[0][1]]
        report = self.write(main, [(agents[0][0], twice)])
        self.assertTrue(report["ok"], self.failed(report))
        self.assertEqual(report["translated_by"], "Claude Sonnet 5.5")
        # 5. 検索と check を 1 つの呼び出しにまとめても、警告がなく写しを消したなら違反にしない
        combined = [json.loads(json.dumps(r, ensure_ascii=False).replace(
            "python wiki_rawcheck.py check --wiki wiki",
            "rg -n -- '--accept-warnings' web-raw.md; python wiki_rawcheck.py check --wiki wiki"))
            for r in agents[0][1]]
        self.assertTrue(any("rg -n" in json.dumps(r, ensure_ascii=False) for r in combined))
        report = self.write(main, [(agents[0][0], combined)])
        self.assertTrue(report["ok"], self.failed(report))

    def test_review11_counterexamples(self):
        """11 回目のレビューの反例。1 つの呼び出しで check --finish を何度か動かしたとき。"""
        main, agents = self.good()
        kept = "check: 通った\n警告: 文体が混ざっている\n警告があるので、作業用の写しを残した。直したら --finish を付けて再検査する。"
        removed = "check: 通った\n作業用の写しを消した"
        accepted_text = "check: 通った\n警告: 文体が混ざっている\n作業用の写しを消した"
        opus = CHECK_OUTPUT.replace('"Claude Sonnet 5.5"', '"Claude Opus 5.5"')

        def agent_with(output):
            return [(agents[0][0], [self.got(output) if self._is_check(r) else r for r in agents[0][1]])]

        w8 = W8
        accept = "wiki:web-raw は警告を受け入れて終えていない（check --finish の出力。どの回も）"
        # 1. 文字の出力で警告で写しを残し、直して警告なしで消したなら、別の回に分ける（最後の回を JSON にすれば通る）
        report = self.write(main, agent_with(kept + "\n" + CHECK_OUTPUT))
        self.assertTrue(report["ok"], self.failed(report))
        self.assertTrue(report["display_names_verified"])
        # 1. 最後の回が文字の出力なら、W8 は通らない（W8 は --json で動かす。0.18.1 の手順）
        report = self.write(main, agent_with(kept + "\n" + removed))
        self.assertEqual(self.failed(report), [w8])
        self.assertFalse(report["display_names_verified"])
        # 1. メインが同じ形で、警告なしで代わりに終えたら通さない（警告の受け入れの流れではない）
        without = [r for r in agents[0][1] if not self._is_check(r)
                   and "--finish" not in json.dumps(r, ensure_ascii=False)]
        finish = "python wiki_rawcheck.py check --slug cqrs --finish"
        report = self.write(main + [self.use("Bash", {"command": finish}), self.got(kept + "\n" + removed)],
                            [(agents[0][0], without)])
        self.assertIn(w8, self.failed(report))
        # 2. 前の回で警告を受け入れて消し、取り直して正しく終えても、前の回の違反は消えない
        report = self.write(main, agent_with(ACCEPTED_OUTPUT + "\n" + CHECK_OUTPUT))
        self.assertIn(accept, self.failed(report))
        # 3. 前の回が JSON で、最後の回が文字の出力なら、最後の回で決める（警告を受け入れていれば違反。前の回の
        #    JSON の表示名は使わず、W8 も通さない）
        report = self.write(main, agent_with(CHECK_OUTPUT + "\n" + accepted_text))
        self.assertIn(accept, self.failed(report))
        report = self.write(main, agent_with(opus + "\n" + removed))
        self.assertEqual(self.failed(report), [w8])
        self.assertFalse(report["display_names_verified"])
        # 1 つの結果の中の 2 回の W8 は、結果の中で後に出た回を最後とする
        report = self.write(main, agent_with(opus + "\n" + CHECK_OUTPUT))
        self.assertTrue(report["ok"], self.failed(report))
        self.assertEqual(report["translated_by"], "Claude Sonnet 5.5")
        # 時刻の同じ（ここでは時刻のない）別の呼び出しの 2 回の W8 は、担当の中の呼び出しの順で後の回を最後とする
        again = self.use("Bash", {"command": "python wiki_rawcheck.py check --slug cqrs --finish --json"},
                         "claude-sonnet-5-5")
        records = [self.got(opus) if self._is_check(r) else r for r in agents[0][1]] + [again, self.got(CHECK_OUTPUT)]
        report = self.write(main, [(agents[0][0], records)])
        self.assertTrue(report["ok"], self.failed(report))
        self.assertEqual(report["translated_by"], "Claude Sonnet 5.5")

    def test_review12_counterexamples(self):
        """12 回目のレビューの反例。check のあとの freeze の警告と、呼び出し全体が誤りになった結果。"""
        main, agents = self.good()
        render = check_web_raw_agent.wiki_rawcheck.render
        finished = render({"stage": "check", "ok": True, "errors": [], "warnings": [], "work_dir_removed": True})
        freeze = render({"stage": "freeze", "ok": True, "errors": [], "removed_lines": ["Subscribe"],
                         "warnings": [{"kind": "removed_much",
                                       "message": "消した文字が本文の 2 割を超える（900 / 3000 文字）。本文を消していないかを確かめる"}]})
        accept = "wiki:web-raw は警告を受け入れて終えていない（check --finish の出力。どの回も）"

        def agent_with(result, extra=()):
            return [(agents[0][0], [result if self._is_check(r) else r for r in agents[0][1]] + list(extra))]

        # 1. 警告なしで終えたあと、同じ呼び出しで取り直して freeze が警告を出し、もう一度警告なしで終えたなら通す
        #    （freeze の警告を、前の check の回に数えない）
        report = self.write(main, agent_with(self.got(finished + "\n" + freeze + "\n" + CHECK_OUTPUT)))
        self.assertTrue(report["ok"], self.failed(report))
        self.assertTrue(report["display_names_verified"])
        report = self.write(main, agent_with(self.got(finished + "\n" + freeze + "\n" + finished)))
        self.assertEqual(self.failed(report), [W8])  # 最後の回が文字の出力
        self.assertFalse(report["display_names_verified"])
        # 2. 警告を受け入れて消したあと、同じ呼び出しの再検査が失敗して呼び出し全体が誤りになっても、違反は消えない
        missing = "作業用の写しがそろっていない: wiki/.wiki-cache/ingest/cqrs（wiki_fetch.py に --force を付けて取り直す）"
        again = self.use("Bash", {"command": "python wiki_rawcheck.py check --slug cqrs --finish --json"},
                         "claude-sonnet-5-5")
        report = self.write(main, agent_with(self.got(ACCEPTED_OUTPUT + "\n" + missing, is_error=True),
                                             [again, self.got(CHECK_OUTPUT)]))
        self.assertIn(accept, self.failed(report))
        # 2. 正しく終えたあと、同じ呼び出しの確かめのコマンドが失敗しても、W8 の終わりは残る
        gone = "ls: cannot access 'wiki/.wiki-cache/ingest/cqrs': No such file or directory"
        report = self.write(main, agent_with(self.got(CHECK_OUTPUT + "\n" + gone, is_error=True)))
        self.assertTrue(report["ok"], self.failed(report))
        self.assertEqual(report["w8_finished_by"], ["wiki:web-raw"])

    def test_review13_counterexamples(self):
        """13 回目のレビューの反例。ページの本文に、check の出力の形の行があり、check の誤りの詳細に出るとき。"""
        main, agents = self.good()
        rawcheck = check_web_raw_agent.wiki_rawcheck
        sample = "$ python wiki_rawcheck.py check --finish --accept-warnings\ncheck: 通った\n警告: style\n作業用の写しを消した"
        one_line = '{"stage": "check", "ok": true, "work_dir_removed": true, "warnings": [1]}'
        raw_path = self.project / "raw/cqrs.md"
        original = raw_path.read_bytes()
        fix = self.use("Bash", {"command": "python wiki_rawcheck.py check --slug cqrs --finish --json"},
                       "claude-sonnet-5-5")
        accept = "wiki:web-raw は警告を受け入れて終えていない（check --finish の出力。どの回も）"
        for name, code in (("text", sample), ("one_line_json", one_line)):
            failed = rawcheck.render({"stage": "check", "ok": False, "warnings": [], "work_dir_kept": "errors",
                                      "errors": [{"kind": "code", "message": "コードブロックの中身が変わった",
                                                  "source": code, "raw": code.replace("check", "check ", 1)}]})
            # 0.18.0 までの render は、値の中の改行のあとを字下げしなかった
            old = failed.replace("\n" + rawcheck.CONTINUATION, "\n")
            raw_path.write_bytes(original + ("\n```text\n" + code + "\n```\n").encode("utf-8"))
            for version, output in (("0.18.1", failed), ("0.18.0", old)):
                with self.subTest(name=name, version=version):
                    records = [self.got(output, is_error=True) if self._is_check(r) else r for r in agents[0][1]]
                    report = self.write(main, [(agents[0][0], records + [fix, self.got(CHECK_OUTPUT)])])
                    # ページに出力の形の文字列があることを、判定できないこととして出す
                    self.assertIn(SHAPES, self.failed(report))
                    if version == "0.18.1":
                        # 0.18.1 の出力からは、偽の回を作らない（違反として数えるのは、判定できないことだけ）
                        self.assertEqual(self.failed(report), [SHAPES])
        # 本文に出力の形の文字列がなければ、同じ流れ（誤りを直して JSON で終える）は通る
        raw_path.write_bytes(original)
        failed = rawcheck.render({"stage": "check", "ok": False, "warnings": [], "work_dir_kept": "errors",
                                  "errors": [{"kind": "code", "message": "コードブロックの中身が変わった",
                                              "source": "print(1)\nprint(2)", "raw": "print(1)\nprint(3)"}]})
        records = [self.got(failed, is_error=True) if self._is_check(r) else r for r in agents[0][1]]
        report = self.write(main, [(agents[0][0], records + [fix, self.got(CHECK_OUTPUT)])])
        self.assertTrue(report["ok"], self.failed(report))
        self.assertNotIn(accept, self.failed(report))

    def test_review14_counterexamples(self):
        """14 回目のレビューの反例。JSONL の JSON の文字列の中の、エスケープしていない行の区切りの文字。

        Claude Code の記録を書く JSON.stringify は、U+2028、U+2029、U+0085 をエスケープしない。記録を
        str.splitlines で分けると、その記録が切れて読めなくなり、証拠が消える。
        """
        main, agents = self.good()
        sonnet = "claude-sonnet-5-5"
        accept = "wiki:web-raw は警告を受け入れて終えていない（check --finish の出力。どの回も）"
        fix = self.use("Bash", {"command": "python wiki_rawcheck.py check --slug cqrs --finish --json"}, sonnet)
        without = [r for r in agents[0][1] if not self._is_check(r)
                   and "--finish" not in json.dumps(r, ensure_ascii=False)]
        for sep in (chr(0x2028), chr(0x2029), chr(0x85)):
            with self.subTest(sep=hex(ord(sep))):
                # 1. 警告の詳細に原文の行の区切りの文字が入った回の、警告の受け入れの違反を見逃さない
                accepted = json.dumps({"stage": "check", "ok": True, "completed": True, "needs_translation": True,
                                       "translation": {"state": "checked", "checked_blocks": 1}, "language_override": None,
                                       "translated_by": "Claude Sonnet 5.5",
                                       "caption_names": ["Claude Sonnet 5.5"], "errors": [],
                                       "warnings": [{"kind": "missing_names", "line": 3,
                                                     "message": "訳文にない名前: ['Greenwich']",
                                                     "source": "The town of Greenwich" + sep + "is old."}],
                                       "work_dir_removed": True}, ensure_ascii=False, indent=2)
                self.assertIn(sep, accepted)
                records = [self.got(accepted) if self._is_check(r) else r for r in agents[0][1]]
                report = self.write(main, [(agents[0][0], records + [fix, self.got(CHECK_OUTPUT)])])
                self.assertIn(accept, self.failed(report))
                self.assertNotIn(UNREADABLE, self.failed(report))
                # 2. W8 のコマンドの --reason に行の区切りの文字があっても、W8 の終わりを読む
                reason = self.use("Bash", {"command": "python wiki_rawcheck.py check --slug cqrs --language-override "
                                                      f'translate --reason "lang=en{sep}本文は英語" --finish --json'}, sonnet)
                report = self.write(main, [(agents[0][0], without + [reason, self.got(CHECK_OUTPUT)])])
                self.assertTrue(report["ok"], self.failed(report))
        # 3. 読めない行があれば、そこにある証拠を判定できないので不合格にする
        report = self.write(main, agents)
        self.assertTrue(report["ok"], self.failed(report))
        path = self.session / "subagents" / "agent-0.jsonl"
        path.write_bytes(path.read_bytes() + b'\n{"message": {"role": "user", "content": [')
        report = check_web_raw_agent.analyze_paths(self.main_path, [path], self.project, "opus")
        self.assertEqual(self.failed(report), [UNREADABLE])

    def test_unreadable_evidence_is_not_a_pass(self):
        """読めた回に違反がないことと、要る回をすべて読めたことを分ける（14 回目の総括。Sol の修正案）。

        読めないものは、違反があったとは決めず、違反がないとは言えないとして不合格にする。
        """
        main, agents = self.good()
        sonnet = "claude-sonnet-5-5"
        fix = self.use("Bash", {"command": "python wiki_rawcheck.py check --slug cqrs --finish --json"}, sonnet)
        without = [r for r in agents[0][1] if not self._is_check(r)
                   and "--finish" not in json.dumps(r, ensure_ascii=False)]
        # 1. 結果のない check --finish の呼び出し（途中で止めたセッションなど）は、あとの回が正しく終えても通さない
        lost = self.use("Bash", {"command": "python wiki_rawcheck.py check --slug cqrs --finish --accept-warnings --json"},
                        sonnet, uid="u-lost")
        report = self.write(main, [(agents[0][0], without + [lost, fix, self.got(CHECK_OUTPUT)])], unanswered={"u-lost"})
        self.assertEqual(self.failed(report), [GAPS])
        # 2. 途中で切れた check の JSON（警告の受け入れの回かもしれない）は、あとの回が正しく終えても通さない
        cut = ACCEPTED_OUTPUT[: len(ACCEPTED_OUTPUT) // 2] + "\n…（出力を切り詰めた）"
        records = [self.got(cut) if self._is_check(r) else r for r in agents[0][1]]
        report = self.write(main, [(agents[0][0], records + [fix, self.got(CHECK_OUTPUT)])])
        self.assertEqual(self.failed(report), [GAPS])
        # 3. エージェントのメタデータがないか読めないときは、担当をほかのサブエージェントと取り違えたまま決めない
        agent_path = self.session / "subagents" / "agent-0.jsonl"
        for name, content in (("meta", None), ("meta", b"{broken"), ("prefix", b"[1]")):
            with self.subTest(file=name, content=content):
                self.write(main, agents)
                path = self.session / "subagents" / f"agent-0.{name}.json"
                if content is None:
                    path.unlink()
                else:
                    path.write_bytes(content)
                report = check_web_raw_agent.analyze_paths(self.main_path, [agent_path], self.project, "opus")
                self.assertIn(UNREADABLE, self.failed(report))
        # 4. 記録の中の、UTF-8 として読めない行と、オブジェクトでない行は、落ちずに判定できないとする
        for bad in (b"\xff\xfe{}", b"[1, 2]", b'"text"'):
            with self.subTest(line=bad):
                self.write(main, agents)
                agent_path.write_bytes(agent_path.read_bytes() + b"\n" + bad)
                report = check_web_raw_agent.analyze_paths(self.main_path, [agent_path], self.project, "opus")
                self.assertEqual(self.failed(report), [UNREADABLE])

    def test_real_rawcheck_output_through_jsonl(self):
        """実際の wiki_rawcheck.main() の freeze と check --finish --json の出力を、記録の JSONL に通して読む。

        14 回目の総括（Sol の修正案）: 試験の結果を、手で作った文字列でなく、出す側から作る。コマンドと出力は
        同じ引数から作り、--reason に行の区切りの文字（U+2028）を入れる。
        """
        import contextlib
        import io
        import shlex
        rawcheck = check_web_raw_agent.wiki_rawcheck
        base = self.project.parent / "real"
        wiki, raw = base / "wiki", base / "raw"
        work = rawcheck.work_dir(wiki, "cqrs")
        work.mkdir(parents=True)
        raw.mkdir()
        (wiki / "SCHEMA.md").write_bytes(b"# s\n")
        text = ('---\nurl: "https://martinfowler.com/bliki/CQRS.html"\ntitle: "CQRS"\nsource_sha256: "x"\n'
                'translated_by: ""\n---\n\n# CQRS\n\n' + RAW_BODY + "\n")
        (work / "fetched.md").write_bytes(text.encode("utf-8"))
        (raw / "cqrs.md").write_bytes(text.encode("utf-8"))
        (work / "fetch.json").write_bytes(
            json.dumps({"needs_translation": False, "images": [], "removed_by_rule": []}).encode("utf-8"))

        def run(argv):
            out = io.StringIO()
            with contextlib.redirect_stdout(out):
                code = rawcheck.main(argv)
            self.assertEqual(code, 0, out.getvalue())
            return "python wiki_rawcheck.py " + shlex.join(argv), out.getvalue()

        common = ["--wiki", str(wiki), "--raw-root", str(raw), "--slug", "cqrs"]
        freeze = run(["freeze", *common])
        finish = run(["check", *common, "--language-override", "keep",
                      "--reason", "英語のページ" + chr(0x2028) + "訳さない", "--finish", "--json"])
        self.assertIn(chr(0x2028), finish[1])  # JSON の中に、エスケープされずに出る
        self.assertFalse(work.exists())  # --finish が写しを消した
        main, agents = self.good()
        sonnet = "claude-sonnet-5-5"
        records = [r for r in agents[0][1] if not self._is_check(r)
                   and "--finish" not in json.dumps(r, ensure_ascii=False)
                   and "freeze" not in json.dumps(r, ensure_ascii=False)]
        records += [self.use("Bash", {"command": freeze[0]}, sonnet), self.got(freeze[1]),
                    self.use("Bash", {"command": finish[0]}, sonnet), self.got(finish[1])]
        report = self.write(main, [(agents[0][0], records)])
        self.assertTrue(report["ok"], self.failed(report))
        self.assertTrue(report["display_names_verified"])
        self.assertEqual(report["w8_finished_by"], ["wiki:web-raw"])

    def test_review15_counterexamples(self):
        """15 回目のレビューの反例。行の途中から始まる check の JSON と、起動したエージェントの記録の欠け。"""
        main, agents = self.good()
        sonnet = "claude-sonnet-5-5"
        accept = "wiki:web-raw は警告を受け入れて終えていない（check --finish の出力。どの回も）"
        fix = self.use("Bash", {"command": "python wiki_rawcheck.py check --slug cqrs --finish --json"}, sonnet)

        def agent_with(result, extra=()):
            return [(agents[0][0], [result if self._is_check(r) else r for r in agents[0][1]] + list(extra))]

        # 1. 前のコマンドの改行のない出力（printf）のあとの JSON も読む。警告の受け入れの違反を見逃さない
        report = self.write(main, agent_with(self.got("check result: " + ACCEPTED_OUTPUT), [fix, self.got(CHECK_OUTPUT)]))
        self.assertIn(accept, self.failed(report))
        # 1. 正しく終えた最後の W8 に、改行のない前置きがあっても、W8 の終わりを読む
        report = self.write(main, agent_with(self.got("check result: " + CHECK_OUTPUT)))
        self.assertTrue(report["ok"], self.failed(report))
        self.assertTrue(report["display_names_verified"])
        # 1. 同じ呼び出しの freeze の「消した行」の値（雑音として消した、ページの 1 行の JSON）は、回に数えない
        render = check_web_raw_agent.wiki_rawcheck.render
        one_line = '{"stage": "check", "ok": true, "work_dir_removed": true, "warnings": [1]}'
        freeze = render({"stage": "freeze", "ok": True, "errors": [], "warnings": [], "removed_lines": [one_line]})
        report = self.write(main, agent_with(self.got(freeze + "\n" + CHECK_OUTPUT)))
        self.assertTrue(report["ok"], self.failed(report))
        # 1. 出力でも値でもない印（ソースを検索した結果など）は説明できないので、判定できないとする
        grep = 'wiki_rawcheck.py:1048:    result = {"stage": "check", "ok": not errors, "needs_translation": translate,'
        report = self.write(main, agent_with(self.got(grep + "\n" + CHECK_OUTPUT)))
        self.assertEqual(self.failed(report), [GAPS])
        # 2. 起動したエージェントの記録のファイルがない。正しい記録がほかにあっても通さない
        links = "wiki:web-raw のすべての呼び出しに、応答のある記録がある（Agent の結果の agentId で、記録のファイルと結ぶ）"
        again = self.use("Agent", {"subagent_type": "wiki:web-raw", "prompt": "この依頼の raw を作る（取り直す）"})
        report = self.write(main + [again, self.launched("1")], agents)
        self.assertEqual(self.failed(report), [links])
        # 2. 記録のファイルはあるが、応答がない（空の記録）。ほかのエージェントの応答で補わない
        empty = ({"agentType": "wiki:web-raw", "launchedWithDefaults": True}, [])
        report = self.write(main + [again, self.launched("1")], agents + [empty])
        self.assertEqual(self.failed(report), [links])
        # 2. 起動に失敗した呼び出し（結果が誤り）には、記録がないのが正しい
        report = self.write(main + [again, self.got("起動できなかった", is_error=True)], agents)
        self.assertTrue(report["ok"], self.failed(report))
        # 2. 結果に agentId がない呼び出しは、記録と結べないので通さない
        report = self.write(main + [again, self.got("Async agent launched")], agents)
        self.assertEqual(self.failed(report), [links])

    @staticmethod
    def _is_check(record) -> bool:
        """CHECK_OUTPUT を返した結果の記録か。"""
        content = record["message"].get("content")
        return isinstance(content, list) and content[0].get("type") == "tool_result" \
            and content[0].get("content") == CHECK_OUTPUT

    def test_review9_correct_runs_pass(self):
        """9 回目のレビューの反例のうち、手順に従った取り込みを落とさないもの。"""
        main, agents = self.good()

        def with_finish(command):
            records = json.loads(json.dumps(agents[0][1], ensure_ascii=False))
            for rec in records:
                for part in rec["message"]["content"] if isinstance(rec["message"]["content"], list) else []:
                    if part.get("type") == "tool_use" and "--finish" in str(part["input"].get("command", "")):
                        part["input"]["command"] = command
            return records

        for command in ('python wiki_rawcheck.py check --slug cqrs --language-override translate '
                        '--reason "lang=en; 本文は英語" --finish',
                        'python wiki_rawcheck.py check --wiki "C:/Research & Development/wiki" --slug cqrs --finish',
                        "python wiki_rawcheck.py \\\n  check --slug cqrs --finish"):
            with self.subTest(command=command):
                report = self.write(main, [(agents[0][0], with_finish(command))])
                self.assertTrue(report["ok"], self.failed(report))
                self.assertEqual(report["w8_finished_by"], ["wiki:web-raw"])
        # オプションの名前を検索しただけでは、--accept-warnings の違反にしない
        search = "rg -n -- '--accept-warnings' info-hive-wiki/skills/info-hive/references/web-raw.md"
        report = self.write(main, [(agents[0][0], agents[0][1] + [
            self.use("Bash", {"command": search}, "claude-sonnet-5-5"), self.got("28:- `--accept-warnings` を付けない。")])])
        self.assertTrue(report["ok"], self.failed(report))
        # W8 を文字の出力で動かしたときは、W8 を通さず、表示名を判定しない（W8 は --json で動かす。0.18.1 の手順）
        text_output = "check: 通った\n作業用の写しを消した"
        records = [self.got(text_output) if self._is_check(r) else r for r in agents[0][1]]
        report = self.write(main, [(agents[0][0], records)])
        self.assertEqual(self.failed(report), [W8])
        self.assertFalse(report["display_names_verified"])

    def test_review8_correct_runs_pass_and_long_commands_are_kept(self):
        """行の継続で分けた W8 は通し（4）、長いコマンドは切り詰めずに見直しの一覧に出す（2）。"""
        main, agents = self.good()
        wrapped = json.loads(json.dumps(agents[0][1], ensure_ascii=False))
        continued = "python wiki_rawcheck.py check \\\n  --slug cqrs --finish"
        for rec in wrapped:
            for part in rec["message"]["content"] if isinstance(rec["message"]["content"], list) else []:
                if part.get("type") == "tool_use" and "--finish" in str(part["input"].get("command", "")):
                    part["input"]["command"] = continued
        self.assertTrue(any(continued in json.dumps(r, ensure_ascii=False) or
                            continued == r["message"]["content"][0].get("input", {}).get("command")
                            for r in wrapped if isinstance(r["message"]["content"], list)))
        long_cmd = ("python - <<'EOF'\n# " + "x" * 600 +
                    "\nopen('wiki/log.md', 'a', encoding='utf-8').write('raw')\nEOF")
        report = self.write(main + [self.use("Bash", {"command": long_cmd})], [(agents[0][0], wrapped)])
        self.assertTrue(report["ok"], self.failed(report))
        self.assertEqual(report["w8_finished_by"], ["wiki:web-raw"])
        self.assertIn(long_cmd, report["bash_to_review"]["main"])

class TranscriptCheckTest(unittest.TestCase):
    """実地の確かめのスクリプトの判定（記録を読まない部分）。"""

    def test_names_finish_and_check_json(self):
        names = check_web_raw_agent.names_finish
        self.assertTrue(names('python "C:/p/wiki_rawcheck.py" check --slug a --finish --json'))
        self.assertFalse(names("cat previous-check-output.json"))
        self.assertFalse(names("python wiki_rawcheck.py freeze --slug a"))
        self.assertFalse(names("python wiki_rawcheck.py check --slug a"))
        jsons = check_web_raw_agent.check_jsons
        found = jsons('ls\r\n{\r\n  "stage": "check",\r\n  "ok": true\r\n}\r\nafter')
        self.assertEqual(found, [{"stage": "check", "ok": True}])
        self.assertEqual(jsons("check: 通った"), [])
        two = '{"stage": "check", "ok": false}\n{"stage": "check", "ok": true, "work_dir_removed": true, "warnings": []}'
        self.assertEqual(len(jsons(two)), 2)
        runs = check_web_raw_agent.check_runs
        self.assertEqual([(r["removed"], r["accepted"]) for r in runs(two)], [(False, False), (True, False)])
        self.assertFalse(runs('{"stage": "check", "ok": true, "work_dir_kept": "warnings"}')[0]["removed"])
        self.assertTrue(runs("check: 通った\n警告: 文体\n作業用の写しを消した")[0]["accepted"])
        # 文字の出力で、警告で写しを残した回と、直して警告なしで消した回を、別の回に分ける（11 回目の 1）
        text = ("check: 通った\n警告: 文体が混ざっている\n警告があるので、作業用の写しを残した。\n"
                "check: 通った\n作業用の写しを消した")
        self.assertEqual([(r["removed"], r["warnings"]) for r in runs(text)], [(False, True), (True, False)])
        # JSON の回と文字の出力の回を、出た順に並べる（11 回目の 3）
        mixed = '{"stage": "check", "ok": true, "work_dir_removed": true, "warnings": []}\ncheck: 通った\n作業用の写しを消した'
        self.assertEqual([r["json"] is not None for r in runs(mixed)], [True, False])
        # 文字の出力の回は、render の形の行だけを読む。freeze の行が来たら終わる（12 回目の 1）
        after = "check: 通った\n作業用の写しを消した\nfreeze: 通った\n警告: 消した文字が本文の 2 割を超える"
        self.assertEqual([(r["removed"], r["warnings"]) for r in runs(after)], [(True, False)])
        before = "check: 通った\nfreeze: 通った\n警告: 消した文字が本文の 2 割を超える\n作業用の写しを消した"
        self.assertEqual([(r["removed"], r["warnings"]) for r in runs(before)], [(False, False)])
        # Windows の print の CRLF でも読む
        self.assertTrue(runs("check: 通った\r\n警告: 文体\r\n作業用の写しを消した\r\n")[0]["accepted"])
        # 誤りの回の、取得と raw の行も回の中に読む
        failed = "check: 規則に反している\n誤り: 本文が変わった\n    取得: a\n    raw : b\n警告: 文体\n作業用の写しを消した"
        self.assertEqual([(r["removed"], r["warnings"]) for r in runs(failed)], [(False, True)])
        # 0.18.1 の render は、値の中の改行のあとを字下げするので、本文の中の見出しや最後の行の形を回にしない
        # （13 回目）。字下げした行は、回の中の行として読む
        render = check_web_raw_agent.wiki_rawcheck.render
        sample = "check: 通った\n警告: style\n作業用の写しを消した"
        error = {"stage": "check", "ok": False, "warnings": [], "work_dir_kept": "errors",
                 "errors": [{"message": "コードが変わった", "source": sample, "raw": sample}]}
        self.assertEqual([(r["removed"], r["warnings"]) for r in runs(render(error))], [(False, False)])
        passed = {"stage": "check", "ok": True, "errors": [], "work_dir_removed": True,
                  "warnings": [{"message": "2 行の\n警告"}]}
        self.assertEqual([(r["removed"], r["accepted"]) for r in runs(render(passed))], [(True, True)])
        # 行の途中から始まる JSON（誤りの詳細の中の、ページの 1 行の JSON）は、回にしない
        line_json = '{"stage": "check", "ok": true, "work_dir_removed": true, "warnings": [1]}'
        error["errors"][0].update(source=line_json, raw=line_json + " ")
        self.assertEqual([r["json"] for r in runs(render(error))], [None])
        self.assertEqual(len(jsons(line_json)), 1)  # 行の頭からなら読む
        # ページの本文の中の、スクリプトの出力の形の文字列を見つける（字下げや引用の記号があっても）
        shapes = check_web_raw_agent.output_shapes
        self.assertEqual(shapes("# CQRS\n\nCQRS は考え方である。保存したファイルを読む。\n"), [])
        self.assertEqual(shapes("> check: 通った"), ["check: 通った"])
        self.assertEqual(shapes('    {"stage": "check"}'), ['"stage": "check"'])
        self.assertEqual(shapes("    freeze: 通った"), ["freeze: 通った"])
        # 探す形は、結果を読む形と同じにする（ふつうの JSON の final_url は数えない。14 回目の軽微）
        self.assertEqual(shapes('```json\n{"final_url": "https://example.com/", "status": 200}\n```'), [])
        self.assertTrue(shapes(FETCH_OUTPUT))
        self.assertTrue(shapes("ログ: 保存した: raw/a.md"))

    def test_shared_text_ignores_source_phrases(self):
        summary = "CQRS は Command Query Responsibility Segregation の略で、読み書きのモデルを分ける考え方である。" * 2
        raw = "Command Query Responsibility Segregation の略である。"
        self.assertEqual(check_web_raw_agent.shares_text(summary, [raw], raw), [])
        self.assertTrue(check_web_raw_agent.shares_text(summary, [summary]))


if __name__ == "__main__":
    unittest.main()
