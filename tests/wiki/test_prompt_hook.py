"""プロンプトのフック（ADR-0032）の試験。wiki_prompt_context.py と wiki_prompt_hook.py、hooks.json、wiki-reader。

実行（標準ライブラリだけで動く）:
    python -X utf8 -m unittest tests/wiki/test_prompt_hook.py -v

実際の wiki での評価（EvaluationGateTests）は、評価のデータに書いたコミットが git の履歴にあるときだけ動く。
CI の浅い取得では飛ばす。
"""
from __future__ import annotations

import ast
import json
import os
import subprocess
import sys
import tempfile
import time
import threading
import unittest
from unittest.mock import patch
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
PLUGIN = ROOT / "info-hive-wiki"
SCRIPTS = PLUGIN / "skills" / "info-hive" / "scripts"
sys.path.insert(0, str(SCRIPTS))

import wiki_initialized  # noqa: E402
import wiki_prompt_context as context  # noqa: E402

HOOK = SCRIPTS / "wiki_prompt_hook.py"


def is_wiki(root) -> bool:
    return wiki_initialized.check(root) is None


def page(title: str, body: str = "", aliases: list[str] | None = None) -> str:
    lines = ["---", 'type: "concept"', f'title: "{title}"']
    if aliases:
        lines.append("aliases: [" + ", ".join(f'"{a}"' for a in aliases) + "]")
    lines += ["---", "", f"# {title}", "", body, ""]
    return "\n".join(lines)


def write(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes(text.encode("utf-8"))


class WikiFixture:
    """小さな合成の wiki を持つプロジェクト。"""

    PAGES = {
        "concepts/リリースの確かめ方.md": (page("プラグインのリリースの確かめ方", "## 完了の条件\n\nタグとリリース。"),
                                       "リリースの完了の条件、タグとリリースの形、マーケットプレイスからの導入の確かめ方"),
        "concepts/pythonの書き戻しの改行.md": (page("Windows の Python で書き戻すと CRLF に変わる", "## 避け方\n\nwrite_bytes を使う。"),
                                        "Windows の Python の write_text が LF を CRLF に変えることと避け方"),
        "concepts/powershellのパイプの打ち切り.md": (page("PowerShell のパイプの打ち切り", "Select-Object -First が上流を止める。"),
                                             "Select-Object -First が上流のスクリプトを止める"),
        "sources/古いuvのUV_SYSTEM_CERTSの直し-wiki-0.19.4.md": (page("古い uv の UV_SYSTEM_CERTS の直しと wiki 0.19.4", "## 直し方\n\n判定を 3 つにした。"),
                                                          "古い uv が読まない UV_SYSTEM_CERTS の不具合と直し"),
        "sources/Pythonの上限の直し-wiki-0.19.5.md": (page("Python の上限の直しと wiki 0.19.5", "UV_SYSTEM_CERTS にも触れる。"),
                                                 "Python のない PC で MCP サーバーが起動しなかった不具合"),
        "concepts/セッションの記録の構造.md": (page("セッションの記録（JSONL）の構造", "JSONL の各行。"),
                                       "Claude Code のセッションの記録から会話を抜き出すときの性質"),
        "concepts/エッジの識別子.md": (page("グラフのエッジの識別子", "## 入れる値\n\nエッジの ID。", aliases=["edge-id"]),
                                  "グラフのエッジの ID に入れる値と入れない値と、その理由"),
        "concepts/取り込みの段.md": (page("取り込みの段の分け方", "raw の段を任せる。"),
                                 "取り込みの raw の段を任せるエージェント"),
        "concepts/取り込みのモデル.md": (page("取り込みに使うモデル", "Sonnet にした。"),
                                   "取り込みの raw の段の費用と時間と品質をモデルで比べた結果"),
    }

    def __init__(self, base: Path, name: str = "project", schema: bool = True):
        self.project = base / name
        self.wiki = self.project / "wiki"
        if schema:
            write(self.wiki / "SCHEMA.md", "# SCHEMA\n")
        index = ["# Wiki のインデックス", "", "## ページ", ""]
        for rel, (text, summary) in self.PAGES.items():
            write(self.wiki / rel, text)
            index.append(f"- [[{Path(rel).stem}]]: {summary}")
        write(self.wiki / "index.md", "\n".join(index) + "\n")


def hook_input(project: Path, prompt: str, **extra) -> dict:
    return {"prompt": prompt, "cwd": str(project), "hook_event_name": "UserPromptSubmit", **extra}


class QueryTextTests(unittest.TestCase):
    def test_skips_commands_and_system_turns(self):
        for prompt in ("/wiki:query uv", "  /model", "!ls", "<agent-message from=\"a\">報告</agent-message>",
                       "<task-notification>x</task-notification>", "<command-name>/model</command-name>",
                       "This session is being continued from a previous conversation that ran out", "", "   ",
                       "はい", None, 42):
            with self.subTest(prompt=prompt):
                self.assertIsNone(context.query_text(prompt))

    def test_strips_pasted_content_and_code(self):
        prompt = ("これを見て <pasted_content id=\"x\">Python が CRLF に変える長いログ</pasted_content> 原因は？\n"
                  "```\nprint('UV_SYSTEM_CERTS')\n```\n")
        text = context.query_text(prompt)
        self.assertNotIn("CRLF", text)
        self.assertNotIn("UV_SYSTEM_CERTS", text)
        self.assertIn("原因", text)

    def test_pasted_content_alone_is_user_input(self):
        self.assertIsNotNone(context.query_text("<pasted_content id=\"a\">x</pasted_content> この手順の確かめ方は？"))

    def test_truncates_long_prompts(self):
        self.assertEqual(len(context.query_text("あ" * 5000)), context.MAX_QUERY_CHARS)

    def test_unclosed_pastes_and_fences_are_discarded(self):
        for suffix in ("<pasted_content>[[secret]]", "\n```x\n[[secret]]", "\n~~~x\n[[secret]]"):
            with self.subTest(suffix=suffix):
                self.assertEqual(context.query_text("このログを整形して" + suffix), "このログを整形して")

    def test_nested_pasted_content_is_discarded(self):
        text = context.query_text("これを整形して <pasted_content>A<pasted_content>B</pasted_content>C</pasted_content> 完了")
        self.assertEqual(text, "これを整形して 完了")

    def test_fence_closer_can_be_longer_than_opener(self):
        self.assertEqual(context.query_text("確認して\n```x\n[[secret]]\n````\n続行して"), "確認して 続行して")


class SettingTests(unittest.TestCase):
    def test_defaults(self):
        self.assertTrue(context.setting({}, "enabled"))
        self.assertFalse(context.setting({}, "user_wiki"))
        self.assertTrue(context.setting({}, "delegate"))

    def test_environment_wins_over_plugin_option(self):
        env = {"INFO_HIVE_PROMPT_CONTEXT": "off", "CLAUDE_PLUGIN_OPTION_PROMPT_CONTEXT": "true"}
        self.assertFalse(context.setting(env, "enabled"))
        env = {"CLAUDE_PLUGIN_OPTION_PROMPT_CONTEXT_USER_WIKI": "TRUE"}
        self.assertTrue(context.setting(env, "user_wiki"))

    def test_unreadable_values_fall_through(self):
        env = {"INFO_HIVE_PROMPT_CONTEXT": "maybe", "CLAUDE_PLUGIN_OPTION_PROMPT_CONTEXT": "0"}
        self.assertFalse(context.setting(env, "enabled"))
        self.assertTrue(context.setting({"INFO_HIVE_PROMPT_CONTEXT": "?"}, "enabled"))


class UnitsTests(unittest.TestCase):
    def test_units_drop_hiragana_and_short_words(self):
        self.assertEqual(context.units("続けてください"), [])
        self.assertEqual(context.units("コミットして"), ["コミット"])
        self.assertEqual(context.units("uv の UV_SYSTEM_CERTS と 0.19.4"), ["system", "certs"])
        self.assertEqual(context.units("設計を設計し直す"), ["設計", "直"][:1])

    def test_unit_in_uses_bigrams(self):
        tokens = set(context.tokenize("敵対的なレビュー"))
        self.assertTrue(context.unit_in("敵対的", tokens))
        self.assertTrue(context.unit_in("レビュー", tokens))
        self.assertFalse(context.unit_in("設計", tokens))

    def test_tokenize_is_shared_with_search(self):
        import wiki_search
        import wiki_tokens
        self.assertIs(wiki_search.tokenize, wiki_tokens.tokenize)
        self.assertIs(context.tokenize, wiki_tokens.tokenize)


class GateTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.fixture = WikiFixture(Path(self.tmp.name))

    def tearDown(self):
        self.tmp.cleanup()

    def pick(self, prompt: str, env: dict | None = None):
        picked = context.select(hook_input(self.fixture.project, prompt), env=env or {}, is_wiki=is_wiki)
        return picked

    def kinds(self, prompt: str) -> list[tuple[str, str]]:
        picked = self.pick(prompt)
        return [(c.page.slug, c.kind) for c in (picked.chosen if picked else [])]

    def test_direct_reference(self):
        self.assertEqual(self.kinds("[[リリースの確かめ方]] の手順で進めて"), [("リリースの確かめ方", "S1")])
        self.assertEqual(self.kinds("[[edge-id]] を見て"), [("エッジの識別子", "S1")])

    def test_discarded_references_do_not_reenter_the_gate(self):
        refs = ("[[リリースの確かめ方]]", "concepts/リリースの確かめ方.md", "リリースの確かめ方")
        for ref in refs:
            for prompt in (f"このログを整形して <pasted_content>{ref}</pasted_content>",
                           f"このログを整形して\n```\n{ref}\n```\n",
                           "あ" * context.MAX_QUERY_CHARS + ref):
                with self.subTest(prompt=prompt[-100:]):
                    self.assertEqual(self.kinds(prompt), [])

    def test_expired_scan_or_scoring_never_returns_candidates(self):
        import wiki_pages
        for target in ("walk_pages", "walk_index_files"):
            original = getattr(wiki_pages, target)

            def slow(*args, **kwargs):
                time.sleep(0.03)
                return original(*args, **kwargs)

            with self.subTest(target=target), patch.object(wiki_pages, target, slow):
                result = context.build_context(hook_input(self.fixture.project, "[[リリースの確かめ方]]"),
                                               env={}, is_wiki=is_wiki, deadline=time.monotonic() + 0.01)
                self.assertIsNone(result)
        original = context.candidates

        def slow_candidates(*args, **kwargs):
            result = original(*args, **kwargs)
            time.sleep(0.03)
            return result

        with patch.object(context, "candidates", slow_candidates):
            self.assertIsNone(context.build_context(hook_input(self.fixture.project, "[[リリースの確かめ方]]"),
                                                   env={}, is_wiki=is_wiki, deadline=time.monotonic() + 0.02))

    def test_large_pages_are_skipped(self):
        write(self.fixture.wiki / "concepts/huge.md", page("huge") + "x" * context.MAX_PAGE_BYTES)
        self.assertNotIn(("huge", "S1"), self.kinds("[[huge]] を見て"))

    def test_actual_long_paths_can_be_opened_from_output(self):
        project = Path(self.tmp.name) / ("a" * 70) / ("b" * 70)
        wiki = project / "wiki"
        slug = "page-" + "c" * 90
        rel = "concepts/" + "d" * 70 + "/" + slug + ".md"
        write(wiki / "SCHEMA.md", "# SCHEMA\n")
        write(wiki / rel, page(slug, "実在するページ。"))
        text = context.build_context(hook_input(project, f"[[{slug}]] を開いて"), env={}, is_wiki=is_wiki)
        header = next(line for line in text.splitlines() if line.startswith("プロジェクトの wiki"))
        root = Path(json.loads(header.split("root: ", 1)[1][:-1]))
        row = json.loads(next(line for line in text.splitlines() if line.startswith("1. "))[3:])
        self.assertEqual(row, {"slug": slug, "path": rel})
        self.assertEqual((root / row["path"]).read_text(encoding="utf-8"), page(slug, "実在するページ。"))

    def test_name_match_needs_two_units(self):
        self.assertEqual(self.kinds("Windows の Python で CRLF になる"),
                         [("pythonの書き戻しの改行", "S2")])

    def test_single_rare_unit_needs_backing(self):
        # 「エッジ」は 1 つの題にしかない。要約か見出しにほかの語（理由）があれば採る。
        self.assertEqual(self.kinds("エッジに入れる値の理由は？"), [("エッジの識別子", "S2")])
        # 裏付けがなければ採らない。
        self.assertEqual(self.kinds("エッジの丸みを CSS で付けたい"), [])

    def test_identifier_in_name_beats_body(self):
        self.assertEqual(self.kinds("UV_SYSTEM_CERTS の件はどう直した？"),
                         [("古いuvのUV_SYSTEM_CERTSの直し-wiki-0.19.4", "S3")])

    def test_identifier_matches_whole_words(self):
        # JSON は JSONL に当たらない。大文字だけの略語は識別子ではない。
        self.assertEqual(self.kinds("JSON の書き方を教えて"), [])
        self.assertEqual(self.kinds("HTTP クライアントを書く"), [])

    def test_versions_only_in_names(self):
        self.assertEqual(self.kinds("0.19.5 の直しを確かめる"), [("Pythonの上限の直し-wiki-0.19.5", "S3")])
        self.assertEqual(self.kinds("0.4.0 のリリースの続き"), [])

    def test_index_summary_needs_three_units(self):
        found = self.kinds("費用と時間と品質を比べた結果を見たい")
        self.assertIn(("取り込みのモデル", "S4"), found)
        self.assertTrue(all(kind == "S4" for _slug, kind in found))
        # 2 つの単位だけでは採らない。
        self.assertEqual(self.kinds("費用と品質を見たい"), [])

    def test_short_and_unrelated_prompts(self):
        for prompt in ("続けて", "コミットして", "OK", "React のフォームを書いて", "fix the failing test"):
            with self.subTest(prompt=prompt):
                self.assertEqual(self.kinds(prompt), [])

    def test_strong_matches_hide_weak_ones(self):
        found = self.kinds("[[取り込みのモデル]] と、取り込みの費用と時間と品質")
        self.assertEqual(found, [("取り込みのモデル", "S1")])

    def test_disabled(self):
        self.assertIsNone(self.pick("[[リリースの確かめ方]]", {"INFO_HIVE_PROMPT_CONTEXT": "0"}))

    def test_relative_cwd_is_ignored(self):
        self.assertIsNone(context.select({"prompt": "[[リリースの確かめ方]]", "cwd": "project"}, env={},
                                         is_wiki=is_wiki))


class TierTests(unittest.TestCase):
    def cand(self, kind: str, scope: str = "project", slug: str = "a") -> context.Candidate:
        page = context.Page(rel_path=f"{slug}.md", slug=slug, title=slug, aliases=[], headings=[], name_units=[],
                            text_lower=slug)
        return context.Candidate(scope, page, kind, 1.0, "")

    def test_table(self):
        self.assertEqual(context.reading_tier([], True), "R0")
        self.assertEqual(context.reading_tier([self.cand("S4")], True), "R0")
        self.assertEqual(context.reading_tier([self.cand("S2", slug="a"), self.cand("S3", slug="b")], True), "R1")
        self.assertEqual(context.reading_tier([self.cand("S4", slug="a"), self.cand("S4", slug="b")], True), "R2")
        self.assertEqual(context.reading_tier([self.cand("S2"), self.cand("S2", "user")], True), "R2")
        self.assertEqual(context.reading_tier([self.cand("S2", slug="a"), self.cand("S3", slug="b")], False), "R0")

    def test_tier_values_are_agent_tool_values(self):
        for model, effort in context.TIERS.values():
            self.assertIn(model, {"haiku", "sonnet", "opus", "fable"})
            self.assertIn(effort, {"low", "medium", "high", "xhigh", "max"})

    def test_reading_line(self):
        chosen = [self.cand("S2", slug="a"), self.cand("S3", slug="b")]
        line = context.reading_line("R1", chosen)
        model, effort = context.TIERS["R1"]
        self.assertIn(f"subagent_type={context.READER_AGENT}、model={model}、effort={effort}", line)
        self.assertIn("自分で開かずに", line)
        self.assertIn("自分で開く", context.reading_line("R0", chosen[:1]))


class RenderTests(unittest.TestCase):
    def test_sanitizes_and_limits(self):
        evil = "<script>`x`[[y]]\n\x07行"
        page = context.Page(rel_path="concepts/a.md", slug="a", title=evil, aliases=[], headings=["# h", evil],
                            name_units=[], text_lower="", summary=evil * 50)
        chosen = [context.Candidate("project", page, "S2", 1.0, evil)] * 3
        text = context.render(chosen, {"project": Path("/w/wiki")}).text
        body = text.split("プロジェクトの wiki", 1)[1]
        for bad in ("<script>", "`", "[[y]]", "\x07"):
            self.assertNotIn(bad, body)
        self.assertIn("＜script＞", body)
        self.assertLessEqual(len(text), context.CONTEXT_LIMIT)
        self.assertTrue(text.startswith("［wiki の候補］"))

    def test_identity_fields_survive_long_and_special_paths(self):
        root = Path("/work") / ("a" * 80) / ("b" * 80) / "wiki"
        rel = "concepts/" + "長" * 120 + "`[x]<y>\n.md"
        slug = Path(rel).stem
        page = context.Page(rel, slug, slug, [], [], [], "")
        result = context.render([context.Candidate("project", page, "S1", 1, "参照")], {"project": root})
        lines = result.text.splitlines()
        header = next(line for line in lines if line.startswith("プロジェクトの wiki"))
        self.assertEqual(json.loads(header.split("root: ", 1)[1][:-1]), root.as_posix())
        row = json.loads(next(line for line in lines if line.startswith("1. "))[3:])
        self.assertEqual(row, {"slug": slug, "path": rel})

    def test_omitted_candidates_do_not_affect_the_reading_tier(self):
        page = context.Page("same.md", "same", "題" * 60, [], ["見出し" * 20] * 3, [], "", "要約" * 80)
        chosen = [context.Candidate(scope, page, "S1", 1, "参照") for scope in ("project", "user")]
        root = Path("/work/wiki")
        single_size = len(context.render(chosen[:1], {"project": root}).text)
        with patch.object(context, "CONTEXT_LIMIT", single_size):
            result = context.render(chosen, {"project": root, "user": root / "other"})
        self.assertEqual([(c.scope, c.page.rel_path) for c in result.shown], [("project", "same.md")])
        self.assertEqual(result.tier, "R0")
        self.assertIn("候補 1 件、wiki 1 つ", result.text)
        self.assertNotIn("ユーザースコープの wiki", result.text)

    def test_candidate_too_long_to_fit_is_omitted_instead_of_truncated(self):
        page = context.Page("a" * 2000 + ".md", "a" * 2000, "a", [], [], [], "")
        cand = context.Candidate("project", page, "S1", 1, "")
        self.assertIsNone(context.render([cand], {"project": Path("/wiki")}))

    def test_hook_output_is_ascii_json(self):
        out = context.hook_output("［wiki の候補］日本語")
        out.encode("ascii")
        self.assertEqual(json.loads(out)["hookSpecificOutput"]["additionalContext"], "［wiki の候補］日本語")


class StateTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        base = Path(self.tmp.name)
        self.fixture = WikiFixture(base)
        self.data = base / "plugin-data"
        self.env = {"CLAUDE_PLUGIN_DATA": str(self.data)}

    def tearDown(self):
        self.tmp.cleanup()

    def build(self, prompt: str, session: str = "s-1"):
        return context.build_context(hook_input(self.fixture.project, prompt, session_id=session), env=self.env,
                                     is_wiki=is_wiki, emit=lambda text: None)

    def test_same_page_is_not_repeated(self):
        self.assertIsNotNone(self.build("[[リリースの確かめ方]] を読んで"))
        self.assertIsNone(self.build("[[リリースの確かめ方]] をもう一度"))
        self.assertIsNotNone(self.build("[[リリースの確かめ方]] を別のセッションで", session="s-2"))
        state = (self.data / "prompt-context" / "sessions" / "s-1.json").read_bytes()
        state.decode("ascii")

    def test_repeats_after_the_window(self):
        self.assertIsNotNone(self.build("[[リリースの確かめ方]]"))
        path = self.data / "prompt-context" / "sessions" / "s-1.json"
        state = json.loads(path.read_bytes())
        state["turns"] += context.REPEAT_TURNS
        path.write_bytes(json.dumps(state).encode("ascii"))
        self.assertIsNotNone(self.build("[[リリースの確かめ方]]"))

    def test_short_user_turns_and_commands_advance_the_window(self):
        self.assertIsNotNone(self.build("[[リリースの確かめ方]]"))
        for _ in range(context.REPEAT_TURNS // 2):
            self.assertIsNone(self.build("はい"))
            self.assertIsNone(self.build("/model"))
        self.assertIsNotNone(self.build("[[リリースの確かめ方]]"))

    def test_system_reports_do_not_advance_the_window(self):
        self.assertIsNotNone(self.build("[[リリースの確かめ方]]"))
        for _ in range(context.REPEAT_TURNS):
            self.assertIsNone(self.build("<agent-message>報告</agent-message>"))
        self.assertIsNone(self.build("[[リリースの確かめ方]]"))

    def test_only_rendered_scope_is_marked_as_shown(self):
        home = WikiFixture(Path(self.tmp.name), name="home")
        self.env.update({"INFO_HIVE_PROMPT_CONTEXT_USER_WIKI": "1", "INFO_HIVE_HOME": str(home.project)})
        prompt = "[[リリースの確かめ方]]"
        candidate = context.select(hook_input(self.fixture.project, prompt), env=self.env, is_wiki=is_wiki)
        limit = len(context.render(candidate.chosen[:1], candidate.roots).text)
        with patch.object(context, "CONTEXT_LIMIT", limit):
            text = self.build(prompt)
        state = json.loads((self.data / "prompt-context/sessions/s-1.json").read_bytes())
        self.assertEqual([json.loads(key)[0] + ":" + json.loads(key)[2] for key in state["shown"]],
                         ["project:concepts/リリースの確かめ方.md"])
        self.assertNotIn("ユーザースコープの wiki", text)
        self.assertIn("ユーザースコープの wiki", self.build(prompt))

    def test_concurrent_selection_rechecks_state_under_the_lock(self):
        barrier = threading.Barrier(2)
        original = context.select

        def simultaneous(*args, **kwargs):
            selected = original(*args, **kwargs)
            barrier.wait(timeout=5)
            return selected

        results = []
        with patch.object(context, "select", simultaneous):
            threads = [threading.Thread(target=lambda: results.append(self.build("[[リリースの確かめ方]]")))
                       for _ in range(2)]
            for thread in threads:
                thread.start()
            for thread in threads:
                thread.join(timeout=5)
        self.assertEqual(sum(result is not None for result in results), 1)
        self.assertEqual(len(results), 2)

    def test_lock_contention_preserves_the_existing_state(self):
        self.build("[[リリースの確かめ方]]")
        path = self.data / "prompt-context/sessions/s-1.json"
        before = path.read_bytes()
        with context.state_lock(path) as acquired:
            self.assertTrue(acquired)
            self.assertIsNone(self.build("[[エッジの識別子]]"))
        self.assertEqual(path.read_bytes(), before)

    def test_bad_session_id_and_broken_state(self):
        self.assertIsNotNone(self.build("[[リリースの確かめ方]]", session="../x"))
        self.assertFalse((self.data / "prompt-context").exists())
        path = self.data / "prompt-context" / "sessions" / "s-3.json"
        write(path, "{broken")
        self.assertIsNotNone(self.build("[[リリースの確かめ方]]", session="s-3"))
        self.assertEqual(json.loads(path.read_bytes())["version"], 2)

    def test_other_project_with_same_relative_path_is_not_suppressed(self):
        other = WikiFixture(Path(self.tmp.name), name="other")
        self.assertTrue(self.build("[[リリースの確かめ方]]"))
        self.assertTrue(context.build_context(hook_input(other.project, "[[リリースの確かめ方]]", session_id="s-1"),
                                             env=self.env, is_wiki=is_wiki, emit=lambda text: None))

    def test_delivery_failure_never_marks_the_candidate_as_shown(self):
        def fail(text):
            raise BrokenPipeError("受け取れなかった")

        with self.assertRaises(BrokenPipeError):
            context.build_context(hook_input(self.fixture.project, "[[リリースの確かめ方]]", session_id="s-1"),
                                  env=self.env, is_wiki=is_wiki, emit=fail)
        self.assertTrue(self.build("[[リリースの確かめ方]]"))

    def test_output_precedes_state_save_even_if_saving_takes_too_long(self):
        emitted = []
        save = context.save_state
        clock = [0.0]

        def delayed(path, state, now):
            self.assertEqual(len(emitted), 1)
            clock[0] = 1.0
            save(path, state, now)

        with patch.object(context, "save_state", delayed), patch.object(context.time, "monotonic", side_effect=lambda: clock[0]):
            text = context.build_context(hook_input(self.fixture.project, "[[リリースの確かめ方]]", session_id="s-1"),
                                         env=self.env, is_wiki=is_wiki, emit=emitted.append,
                                         deadline=.02)
        self.assertEqual(emitted, [text])


class WikiRootTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.base = Path(self.tmp.name)

    def tearDown(self):
        self.tmp.cleanup()

    def test_uninitialized_wiki_is_silent_and_untouched(self):
        fixture = WikiFixture(self.base, schema=False)
        before = sorted(p.relative_to(self.base).as_posix() for p in self.base.rglob("*"))
        env = {"CLAUDE_PLUGIN_DATA": str(self.base / "data")}
        self.assertIsNone(context.build_context(hook_input(fixture.project, "[[リリースの確かめ方]]", session_id="a"),
                                                env=env, is_wiki=is_wiki))
        self.assertEqual(sorted(p.relative_to(self.base).as_posix() for p in self.base.rglob("*")), before)

    def test_workspace_config_and_user_wiki(self):
        project = self.base / "proj"
        write(project / ".info-hive" / "workspace.json",
              json.dumps({"version": 1, "kind": "project", "id": "proj", "dirs": {"wiki": "notes/wiki"}}))
        fixture = WikiFixture(self.base / "proj" / "notes", name=".")
        home = WikiFixture(self.base / "home", name="info-hive")
        roots = context.wiki_roots(project, {"INFO_HIVE_HOME": str(home.project)}, True, is_wiki)
        self.assertEqual(roots["project"].resolve(), fixture.wiki.resolve())
        self.assertEqual(roots["user"].resolve(), home.wiki.resolve())
        self.assertNotIn("user", context.wiki_roots(project, {"INFO_HIVE_HOME": str(home.project)}, False, is_wiki))

    def test_same_wiki_is_listed_once(self):
        fixture = WikiFixture(self.base, name="info-hive")
        roots = context.wiki_roots(fixture.project, {"INFO_HIVE_HOME": str(fixture.project)}, True, is_wiki)
        self.assertEqual(list(roots), ["project"])

    def test_user_workspace_is_never_classified_as_project(self):
        home = WikiFixture(self.base, name="home")
        write(home.project / ".info-hive/workspace.json",
              json.dumps({"version": 1, "kind": "user", "dirs": {"wiki": "wiki"}}))
        child = home.project / "projects" / "child"
        child.mkdir(parents=True)
        env = {"INFO_HIVE_HOME": str(home.project)}
        for cwd in (home.project, child):
            with self.subTest(cwd=cwd):
                self.assertEqual(context.wiki_roots(cwd, env, False, is_wiki), {})
                self.assertEqual(context.wiki_roots(cwd, env, True, is_wiki), {"user": home.wiki})


class EntryTests(unittest.TestCase):
    """入口は、どんな入力でも終了コード 0 で終わり、何も出さないか、ASCII だけの正しい JSON を出す。"""

    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.fixture = WikiFixture(Path(self.tmp.name))
        self.env = {k: v for k, v in os.environ.items() if not k.startswith(("INFO_HIVE_", "CLAUDE_PLUGIN"))}
        self.env.update({"PYTHONUTF8": "0", "PYTHONIOENCODING": "", "CLAUDE_PLUGIN_DATA": str(Path(self.tmp.name) / "d")})

    def tearDown(self):
        self.tmp.cleanup()

    def run_hook(self, payload: bytes, *, contract_budget=False) -> subprocess.CompletedProcess:
        # JSON と状態の契約は起動時間から分ける。実際の 2.5 秒の打ち切りは別のテストで確かめる。
        command = [sys.executable, str(HOOK)]
        if contract_budget:
            code = f"import sys, os; sys.path.insert(0, {str(SCRIPTS)!r}); import wiki_prompt_hook as h; h.DEADLINE_SECONDS=15; h.main(); os._exit(0)"
            command = [sys.executable, "-c", code]
        return subprocess.run(command, input=payload, capture_output=True, env=self.env,
                              timeout=60)

    def test_bad_inputs_exit_zero_silently(self):
        too_big = b"{" + b" " * (context.MAX_STDIN_BYTES + 10) + b"}"
        for payload in (b"", b"not json", b"\xff\xfe\x00", b"[]", b"null", too_big,
                        json.dumps({"prompt": 1, "cwd": 2}).encode()):
            with self.subTest(payload=payload[:20]):
                proc = self.run_hook(payload)
                self.assertEqual(proc.returncode, 0)
                self.assertEqual(proc.stdout, b"")

    def test_valid_input_gives_ascii_json(self):
        payload = json.dumps(hook_input(self.fixture.project, "[[リリースの確かめ方]] の手順", session_id="e-1"),
                             ensure_ascii=False).encode("utf-8")
        proc = self.run_hook(payload, contract_budget=True)
        self.assertEqual(proc.returncode, 0)
        proc.stdout.decode("ascii")
        ctx = json.loads(proc.stdout)["hookSpecificOutput"]
        self.assertEqual(ctx["hookEventName"], "UserPromptSubmit")
        self.assertIn("リリースの確かめ方", ctx["additionalContext"])

    def test_long_prompt(self):
        payload = json.dumps(hook_input(self.fixture.project, "設計 " * 200000)).encode("utf-8")
        proc = self.run_hook(payload)
        self.assertEqual(proc.returncode, 0)

    def test_skipped_user_turn_advances_existing_state_in_the_entry(self):
        def send(prompt):
            payload = json.dumps(hook_input(self.fixture.project, prompt, session_id="fast-path")).encode("utf-8")
            proc = self.run_hook(payload, contract_budget=True)
            self.assertEqual(proc.returncode, 0)
            self.assertEqual(proc.stderr, b"")
            return proc.stdout

        self.assertTrue(send("[[リリースの確かめ方]]"))
        path = Path(self.env["CLAUDE_PLUGIN_DATA"]) / "prompt-context/sessions/fast-path.json"
        first = json.loads(path.read_bytes())
        self.assertEqual(send("はい"), b"")
        second = json.loads(path.read_bytes())
        self.assertEqual(second["turns"], first["turns"] + 1)
        self.assertEqual(second["shown"], first["shown"])
        self.assertEqual(send("<agent-message>報告</agent-message>"), b"")
        self.assertEqual(json.loads(path.read_bytes()), second)

    def test_many_unclosed_fences_finish_before_hook_timeout(self):
        prompt = "format this log\n" + "```x\n" * 20000
        payload = json.dumps(hook_input(self.fixture.project, prompt)).encode("utf-8")
        started = time.monotonic()
        proc = self.run_hook(payload)
        self.assertEqual(proc.returncode, 0)
        self.assertEqual(proc.stdout, b"")
        self.assertEqual(proc.stderr, b"")
        self.assertLess(time.monotonic() - started, 4.5)

    def test_supervisor_ends_a_worker_stuck_in_parsing(self):
        # 入口のコピーで子だけを停止させ、実際の親の起動、打ち切り、出力を確かめる。
        slow_hook = Path(self.tmp.name) / "slow_hook.py"
        source = HOOK.read_text(encoding="utf-8")
        call = "        worker(float(sys.argv[2]))\n"
        self.assertEqual(source.count(call), 1)
        source = source.replace("        import wiki_prompt_context as context",
                                f"        sys.path.insert(0, {str(SCRIPTS)!r})\n        import wiki_prompt_context as context")
        write(slow_hook, source.replace(call, "        time.sleep(10)\n"))
        payload = json.dumps(hook_input(self.fixture.project, "[[リリースの確かめ方]]")).encode("utf-8")
        started = time.monotonic()
        proc = subprocess.run([sys.executable, str(slow_hook)], input=payload, capture_output=True,
                              env=self.env, timeout=6)
        self.assertEqual(proc.returncode, 0)
        self.assertEqual(proc.stdout, b"")
        self.assertEqual(proc.stderr, b"")
        self.assertLess(time.monotonic() - started, 4.5)
        self.assertGreater(time.monotonic() - started, 1.5)


class StructureTests(unittest.TestCase):
    FORBIDDEN = {"subprocess", "wiki_index", "wiki_mcp_relay", "wiki_decide", "fastembed", "wiki_search",
                 "urllib", "http", "socket"}

    def imports(self, path: Path) -> set[str]:
        names = set()
        for node in ast.walk(ast.parse(path.read_bytes().decode("utf-8"))):
            if isinstance(node, ast.Import):
                names |= {a.name.split(".")[0] for a in node.names}
            elif isinstance(node, ast.ImportFrom) and node.module:
                names.add(node.module.split(".")[0])
        return names

    def test_no_heavy_or_network_imports(self):
        for name in ("wiki_prompt_context.py", "wiki_prompt_hook.py", "wiki_tokens.py"):
            with self.subTest(script=name):
                # 入口だけは、同じ Python の解析の子を締め切りで止めるため subprocess を使う。
                forbidden = self.FORBIDDEN - {"subprocess"} if name == "wiki_prompt_hook.py" else self.FORBIDDEN
                self.assertEqual(self.imports(SCRIPTS / name) & forbidden, set())

    def test_hooks_json(self):
        data = json.loads((PLUGIN / "hooks" / "hooks.json").read_bytes().decode("utf-8"))
        handlers = data["hooks"]["UserPromptSubmit"][0]["hooks"]
        self.assertEqual(len(handlers), 1)
        hook = handlers[0]
        self.assertEqual(hook["type"], "command")
        self.assertNotIn("args", hook)  # exec 形式だと、uv の段の終了コード 2 が利用者の指示を止める
        self.assertTrue(hook["command"].rstrip().endswith("; exit 0"))
        self.assertNotIn("--script", hook["command"])
        for flag in ("--quiet", "--offline", "--no-python-downloads", "--no-project", "--no-config", "-I", "-S"):
            self.assertIn(flag, hook["command"])
        self.assertIn("${CLAUDE_PLUGIN_ROOT}/skills/info-hive/scripts/wiki_prompt_hook.py", hook["command"])
        self.assertLessEqual(hook["timeout"], 10)

    def test_user_config(self):
        config = json.loads((PLUGIN / ".claude-plugin" / "plugin.json").read_bytes().decode("utf-8"))["userConfig"]
        for name, (_env, option, default) in context.SETTINGS.items():
            key = option.removeprefix("CLAUDE_PLUGIN_OPTION_").lower()
            with self.subTest(setting=name):
                self.assertEqual(config[key]["type"], "boolean")
                self.assertEqual(config[key]["default"], default)

    def test_reader_agent(self):
        text = (PLUGIN / "agents" / "wiki-reader.md").read_bytes().decode("utf-8")
        front = text.split("---", 2)[1]
        fields = dict(line.split(":", 1) for line in front.strip().splitlines())
        self.assertEqual(fields["name"].strip(), context.READER_AGENT.split(":", 1)[1])
        tools = {t.strip() for t in fields["tools"].split(",")}
        self.assertEqual(tools & {"Write", "Edit", "Bash", "PowerShell", "NotebookEdit"}, set())
        self.assertIn(fields["model"].strip(), {"haiku", "sonnet", "opus", "fable"})
        self.assertIn(fields["effort"].strip(), {"low", "medium", "high", "xhigh", "max"})

    def test_pep723_range(self):
        head = HOOK.read_bytes().decode("utf-8").split("# ///", 2)[1]
        self.assertIn('requires-python = ">=3.12,<3.15"', head)
        self.assertIn("dependencies = []", head)
        command = json.loads((PLUGIN / "hooks/hooks.json").read_text(encoding="utf-8"))["hooks"]["UserPromptSubmit"][0]["hooks"][0]["command"]
        declared = next(line.split("=", 1)[1].strip() for line in head.splitlines()
                        if line.startswith("# requires-python")).strip('"')
        self.assertIn('--python "' + declared + '"', command)


class EvaluationGateTests(unittest.TestCase):
    """実際の wiki（評価のデータに書いたコミット）で、合否の基準に届くこと。git の履歴がなければ飛ばす。"""

    def test_gate(self):
        data = json.loads((Path(__file__).resolve().parent / "fixtures" / "prompt_context" / "prompts.json")
                          .read_bytes().decode("utf-8"))
        probe = subprocess.run(["git", "-C", str(ROOT), "cat-file", "-e", data["wiki_commit"] + "^{commit}"],
                               capture_output=True)
        if probe.returncode:
            self.skipTest("評価のデータのコミットが git の履歴にない")
        sys.path.insert(0, str(Path(__file__).resolve().parent))
        import eval_prompt_context as evaluation

        class Args:
            split = "all"
            set = None

        report = evaluation.run(Args())
        self.assertTrue(report["passed"], report["metrics"])


if __name__ == "__main__":
    unittest.main()
