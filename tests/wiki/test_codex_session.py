"""Codex の履歴を共通の伏せ字・確認・raw 保存へ接続する試験。

履歴はすべて人工的な API 応答である。app-server とモデルは起動せず、
利用者の履歴や認証情報は読まない。Claude の既存 fixture のハッシュも固定して比較する。
"""
from __future__ import annotations

import copy
import hashlib
import io
import json
import os
import queue
import shutil
import stat
import subprocess
import sys
import tempfile
import time
import unittest
from datetime import datetime, timedelta, timezone
from pathlib import Path
from types import SimpleNamespace
from unittest import mock

ROOT = Path(__file__).resolve().parents[2]
SCRIPTS = ROOT / "info-hive-wiki/skills/info-hive/scripts"
sys.path.insert(0, str(SCRIPTS))

import wiki_session as ws  # noqa: E402
import wiki_codex_session as cs  # noqa: E402

SID = "019a7a00-aaaa-4bbb-8ccc-0123456789ab"
TITLE = "履歴の取り込みの試験"
PRIVATE = "顧客A"
EMAIL = "alice@example.test"
KEY = "sk-synthetic0123456789abcdefghijklmnop"
HIDDEN = "NOSHOW_SYNTHETIC_ONLY"


def entry(turn: str, kind: str, ident: str, **values) -> dict:
    return {"turnId": turn, "item": {"type": kind, "id": ident, **values},
            "startedAtMs": 1794618000000, "completedAtMs": 1794618001000}


def snapshot() -> dict:
    """同じアシスタントの作業が複数の項目に分かれた、2 ターンの会話。"""
    return {
        "thread": {
            "id": SID, "cwd": "C:/Users/alice/work/試験", "cliVersion": "0.166.0",
            "historyMode": "paginated", "source": "cli",
            "gitInfo": {"branch": "feature/試験", "originUrl": f"https://{HIDDEN}.invalid/repo"},
            "name": HIDDEN, "preview": HIDDEN,
        },
        "turns": [
            {"id": "turn-one", "status": "completed", "startedAt": 1794618000,
             "completedAt": 1794618010},
            {"id": "turn-two", "status": "completed", "startedAt": 1794618020,
             "completedAt": 1794618030},
        ],
        "items": [
            entry("turn-one", "userMessage", "u1", content=[
                {"type": "text", "text": f"{PRIVATE} の索引を整理して。連絡先は {EMAIL}、鍵は {KEY}。"},
                {"type": "image", "url": HIDDEN},
            ]),
            entry("turn-one", "reasoning", "r1", summary=[HIDDEN], content=[HIDDEN]),
            entry("turn-one", "commandExecution", "tool1", command="python -m unittest",
                  cwd="C:/work", aggregatedOutput=HIDDEN, status="completed"),
            entry("turn-one", "agentMessage", "a1", text="索引を確認します。", phase="commentary"),
            entry("turn-one", "agentMessage", "a2", text="索引を整理しました。", phase="final_answer"),
            entry("turn-one", "agentMessage", "thinking-as-message", text=HIDDEN, phase="analysis"),
            entry("turn-one", "contextCompaction", "compact1", summary=HIDDEN, text=HIDDEN),
            entry("turn-one", "collabAgentToolCall", "peer1", prompt=HIDDEN, result=HIDDEN),
            entry("turn-one", "futureUnknownItem", "unknown1", text=HIDDEN),
            entry("turn-two", "userMessage", "u2", content=[
                {"type": "text", "text": "この発言は後で消してください。"},
            ]),
            entry("turn-two", "agentMessage", "a3", text="作業を終えました。", phase="final_answer"),
        ],
    }


def extracted(data: dict | None = None, **options) -> ws.Extract:
    return cs.extract_snapshot(data if data is not None else snapshot(), ws.Options(**options), ws.DEFAULT_MAX_BYTES)


def remove_tree(path: Path) -> None:
    def onexc(func, name, _exc):
        os.chmod(name, stat.S_IWRITE | stat.S_IREAD)
        func(name)
    shutil.rmtree(path, onexc=onexc)


class CodexExtractionTests(unittest.TestCase):
    def test_source_hash_is_independent_of_the_display_timezone(self):
        utc = extracted(utc_offset="+00:00")
        japan = extracted(utc_offset="+09:00")
        self.assertEqual(utc.source_sha256, japan.source_sha256)
        self.assertEqual(utc.source_bytes, japan.source_bytes)
        self.assertNotEqual(utc.base_sha256, japan.base_sha256)
        self.assertNotEqual(utc.turns[0].time, japan.turns[0].time)

    def test_only_public_conversation_and_tool_names_are_retained(self):
        ex = extracted()
        text = ws.render(ex, TITLE, [], []).decode("utf-8")
        self.assertNotIn(HIDDEN, text)
        self.assertNotIn(EMAIL, text)
        self.assertNotIn(KEY, text)
        self.assertIn("索引を整理して", text)
        self.assertIn("索引を確認します", text)
        self.assertIn("索引を整理しました", text)
        self.assertIn("[ツール] commandExecution", text)
        self.assertNotIn("python -m unittest", text)
        self.assertIn("Codex（", text)
        self.assertNotIn("Claude（", text)
        self.assertEqual(ex.source_kind, "codex-session")
        self.assertEqual(ex.source_sha256_of, "codex-thread-range-v1")
        self.assertEqual(ex.extracted_by, "wiki_codex_session.py 0.1")
        self.assertEqual(ex.version_field, "codex_versions")
        self.assertIn('source_kind: "codex-session"', text)
        self.assertIn('codex_versions: "0.166.0"', text)
        self.assertNotIn("claude_code_versions:", text)

    def test_codex_replies_point_to_their_user_turn(self):
        ex = extracted(tools="none")
        user = next(t for t in ex.turns if "索引を整理して" in t.body)
        first_replies = [t for t in ex.turns if t.kind == "codex" and "索引" in t.body]
        self.assertTrue(first_replies)
        self.assertTrue(all(t.reply_to == user.n for t in first_replies))
        second_user = next(t for t in ex.turns if "この発言" in t.body)
        final = next(t for t in ex.turns if "作業を終えました" in t.body)
        self.assertEqual(final.reply_to, second_user.n)
        self.assertTrue(all(t.fenced for t in ex.turns if t.kind == "codex"))

    def test_tool_names_are_optional(self):
        text = ws.render(extracted(tools="none"), TITLE, [], []).decode("utf-8")
        self.assertNotIn("[ツール]", text)
        self.assertIn("索引を整理しました", text)
        self.assertNotIn(HIDDEN, text)

    def test_legacy_api_history_uses_the_same_public_conversation_rules(self):
        data = snapshot()
        data["thread"]["historyMode"] = "legacy"
        text = ws.render(extracted(data), TITLE, [], []).decode("utf-8")
        self.assertIn("索引を整理しました", text)
        self.assertNotIn(HIDDEN, text)

    def test_item_timestamps_use_the_requested_utc_offset(self):
        ex = extracted(utc_offset="+09:00")
        expected = datetime.fromtimestamp(1794618000, timezone.utc).astimezone(timezone(timedelta(hours=9)))
        user = next(t for t in ex.turns if "索引を整理して" in t.body)
        self.assertEqual(user.time, expected.strftime("%Y-%m-%d %H:%M:%S"))

    def test_unknown_model_is_not_replaced_with_current_thread_model(self):
        data = snapshot()
        data["thread"]["model"] = "future-current-model"
        text = ws.render(extracted(data), TITLE, [], []).decode("utf-8")
        self.assertNotIn("future-current-model", text)

    def test_user_authored_instruction_prefixes_remain_source_text(self):
        data = snapshot()
        messages = ["# AGENTS.md instructions の例を調べたい", "<INSTRUCTIONS> は資料中の引用である。",
                    "<environment_context> というタグについて質問した。"]
        data["items"][0]["item"]["content"] = [{"type": "text", "text": text} for text in messages]
        text = ws.render(extracted(data), TITLE, [], []).decode("utf-8")
        for message in messages:
            self.assertIn(message, text)

    def test_metadata_does_not_expose_title_preview_or_remote_url(self):
        ex = extracted()
        self.assertNotIn(HIDDEN, json.dumps(ex.base(), ensure_ascii=False))
        self.assertNotIn("alice", ex.cwd)
        self.assertIn("~", ex.cwd)
        self.assertEqual(ex.session_id, SID)

    def test_cutoff_excludes_the_requested_item_and_later_items(self):
        ex = extracted(before="u2")
        text = ws.render(ex, TITLE, [], []).decode("utf-8")
        self.assertEqual(ex.cut_before, "u2")
        self.assertNotIn("この発言", text)
        self.assertNotIn("作業を終えました", text)
        self.assertEqual(len(ex.humans), 1)

    def test_cutoff_by_turn_and_missing_cutoff(self):
        ex = extracted(before="turn-two")
        self.assertNotIn("この発言", ws.render(ex, TITLE, [], []).decode("utf-8"))
        with self.assertRaises(ws.Fail):
            extracted(before="missing-item")

    def test_appending_after_cutoff_keeps_source_and_base_hashes(self):
        data = snapshot()
        first = extracted(data, before="u2")
        changed = copy.deepcopy(data)
        changed["items"][-1]["item"]["text"] = "cutoff より後の変更"
        changed["items"].append(entry("turn-two", "agentMessage", "a4", text="追記", phase="final_answer"))
        changed["thread"]["updatedAt"] = 1900000000
        changed["thread"]["preview"] = "変わったプレビュー"
        second = extracted(changed, before="u2")
        self.assertEqual(first.source_sha256, second.source_sha256)
        self.assertEqual(first.source_bytes, second.source_bytes)
        self.assertEqual(first.base_sha256, second.base_sha256)

    def test_changing_selected_range_invalidates_decisions(self):
        first = extracted(before="u2")
        decisions = ws.Decisions(None, ws.new_decisions(first))
        changed = snapshot()
        changed["items"][0]["item"]["content"][0]["text"] += " 範囲内の追記"
        second = extracted(changed, before="u2")
        self.assertNotEqual(first.source_sha256, second.source_sha256)
        with self.assertRaises(ws.Fail):
            ws.check_decisions(decisions, second)

    def test_malformed_or_ambiguous_history_is_refused(self):
        duplicate = snapshot()
        duplicate["items"].append(copy.deepcopy(duplicate["items"][0]))
        with self.assertRaises(ws.Fail):
            extracted(duplicate)
        mismatched = snapshot()
        with self.assertRaises(ws.Fail):
            cs.extract_snapshot(mismatched, ws.Options(session_id_arg="019a7a00-bbbb-4bbb-8ccc-0123456789ab"), ws.DEFAULT_MAX_BYTES)
        with self.assertRaises(ws.Fail):
            cs.extract_snapshot(snapshot(), ws.Options(), 20)

    def test_subagent_history_is_not_a_human_session(self):
        data = snapshot()
        data["thread"]["source"] = {"subAgent": {"threadId": SID}}
        with self.assertRaises(ws.Fail):
            extracted(data)


class ClaudeCompatibilityTests(unittest.TestCase):
    def test_preexisting_fixture_keeps_base_and_render_hashes(self):
        path = ROOT / "tests/wiki/fixtures/session/basic.jsonl"
        opts = ws.Options(utc_offset="+09:00")
        ex = ws.extract(ws.read_range(path, None, ws.DEFAULT_MAX_BYTES), opts)
        self.assertEqual(ex.base_sha256, "3cbdc27b8abd34d261082ccf307062d47638b4861976f51fffe1d159e7af6a08")
        raw = ws.render(ex, "索引の作り方", [], [])
        self.assertEqual(hashlib.sha256(raw).hexdigest(), "605a6e24410d7accd3d0a76967e91bbc5cc8b905eb436cc71f007bb0f06f6d8a")


class CodexDiscoveryTests(unittest.TestCase):
    def test_current_id_uses_thread_id_before_parent_session_id(self):
        parent = "019a7a00-bbbb-4bbb-8ccc-0123456789ab"
        with mock.patch.dict(os.environ, {"CODEX_THREAD_ID": SID, "CODEX_SESSION_ID": parent}, clear=True):
            self.assertEqual(cs.current_session_id(), SID)
        with mock.patch.dict(os.environ, {"CODEX_SESSION_ID": parent}, clear=True):
            self.assertEqual(cs.current_session_id(), parent)

    def test_absent_current_id_does_not_choose_a_recent_chat(self):
        with mock.patch.dict(os.environ, {}, clear=True), mock.patch.object(cs, "fetch_snapshot") as fetch:
            with self.assertRaises(ws.Fail):
                cs.locate(None, current=True)
            fetch.assert_not_called()

    def test_current_locate_cuts_the_entire_latest_turn_before_steering(self):
        data = snapshot()
        data["items"].append(entry("turn-two", "userMessage", "steering", content=[
            {"type": "text", "text": "この作業を続けて"},
        ]))
        with mock.patch.dict(os.environ, {"CODEX_THREAD_ID": SID}, clear=True), \
                mock.patch.object(cs, "fetch_snapshot", return_value=data):
            result = cs.locate(None, current=True)
        self.assertEqual(result["before"], "turn-two")
        self.assertEqual(result["cutoff_kind"], "turn")
        text = ws.render(extracted(data, before=result["before"]), TITLE, [], []).decode("utf-8")
        self.assertNotIn("この発言", text)
        self.assertNotIn("この作業を続けて", text)

    def test_current_extraction_requires_a_frozen_boundary(self):
        with mock.patch.dict(os.environ, {"CODEX_THREAD_ID": SID}, clear=True), mock.patch.object(cs, "Rpc") as rpc:
            with self.assertRaises(ws.Fail):
                cs.extract_session(SID, ws.Options())
            rpc.assert_not_called()

    def test_list_returns_redacted_metadata_from_active_and_archived_chats(self):
        meta = snapshot()["thread"]
        meta["updatedAt"] = 20
        archived = copy.deepcopy(meta)
        archived["id"] = "019a7a00-bbbb-4bbb-8ccc-0123456789ab"
        archived["updatedAt"] = 30
        with mock.patch.object(cs, "Rpc") as rpc:
            rpc.return_value.__enter__.return_value.request.side_effect = [
                {"data": [meta], "nextCursor": None}, {"data": [archived], "nextCursor": None},
            ]
            result = cs.list_sessions(1)
            calls = rpc.return_value.__enter__.return_value.request.call_args_list
        self.assertEqual(len(result), 1)
        self.assertEqual(result[0]["session_id"], archived["id"])
        self.assertTrue(result[0]["archived"])
        text = json.dumps(result, ensure_ascii=False)
        self.assertNotIn(HIDDEN, text)
        self.assertNotIn("alice", text)
        self.assertTrue(all(call.args[0] == "thread/list" for call in calls))
        self.assertTrue(all(call.args[1]["useStateDbOnly"] for call in calls))


class CodexApiBoundaryTests(unittest.TestCase):
    def test_invalid_size_is_rejected_before_starting_the_reader(self):
        for value in (0, -1, True):
            with self.subTest(value=value), mock.patch.object(cs, "Rpc") as reader:
                with self.assertRaises(ws.Fail):
                    cs.extract_session(SID, ws.Options(), value)
                reader.assert_not_called()

    def test_snapshot_collects_all_pages_in_ascending_order(self):
        data = snapshot()
        client = mock.Mock()

        def request(method, params):
            if method == "thread/read":
                return {"thread": data["thread"]}
            self.assertEqual(params["sortDirection"], "asc")
            if method == "thread/turns/list":
                return {"data": data["turns"][:1], "nextCursor": "turn-next"} if "cursor" not in params else {
                    "data": data["turns"][1:], "nextCursor": None,
                }
            self.assertEqual(method, "thread/items/list")
            return {"data": data["items"][:4], "nextCursor": "item-next"} if "cursor" not in params else {
                "data": data["items"][4:], "nextCursor": None,
            }

        client.request.side_effect = request
        result = cs._snapshot(client, SID)
        self.assertEqual(result["turns"], data["turns"])
        self.assertEqual(result["items"], data["items"])
        page_calls = [call for call in client.request.call_args_list if call.args[0] != "thread/read"]
        self.assertEqual(len(page_calls), 4)
        self.assertEqual(page_calls[1].args[1]["cursor"], "turn-next")
        self.assertEqual(page_calls[3].args[1]["cursor"], "item-next")

    def test_legacy_history_reads_full_turn_items_without_items_api_or_migration(self):
        data = snapshot()
        data["thread"]["historyMode"] = "legacy"
        full_turns = []
        for turn in data["turns"]:
            full_turns.append({**turn, "itemsView": "full",
                               "items": [row["item"] for row in data["items"] if row["turnId"] == turn["id"]]})
        client = mock.Mock()

        def request(method, params):
            if method == "thread/read":
                return {"thread": data["thread"]}
            self.assertEqual(method, "thread/turns/list", "legacy 履歴で items API や移行を呼んではならない")
            self.assertEqual(params["itemsView"], "full")
            self.assertEqual(params["sortDirection"], "asc")
            return {"data": full_turns[:1], "nextCursor": "next-turn"} if "cursor" not in params else {
                "data": full_turns[1:], "nextCursor": None,
            }

        client.request.side_effect = request
        result = cs._snapshot(client, SID)
        self.assertEqual([(row["turnId"], row["item"]) for row in result["items"]],
                         [(row["turnId"], row["item"]) for row in data["items"]])
        methods = {call.args[0] for call in client.request.call_args_list}
        self.assertEqual(methods, {"thread/read", "thread/turns/list"})
        text = ws.render(extracted(result), TITLE, [], []).decode("utf-8")
        self.assertIn("索引を整理しました", text)
        self.assertNotIn(HIDDEN, text)

    def test_legacy_summary_response_is_not_treated_as_complete_history(self):
        data = snapshot()
        data["thread"]["historyMode"] = "legacy"
        client = mock.Mock()

        def request(method, params):
            if method == "thread/read":
                return {"thread": data["thread"]}
            self.assertEqual(method, "thread/turns/list")
            return {"data": [{**data["turns"][0], "itemsView": "summary", "items": []}], "nextCursor": None}

        client.request.side_effect = request
        with self.assertRaises(ws.Fail):
            cs._snapshot(client, SID)

    def test_repeated_cursor_is_refused_instead_of_looping(self):
        client = mock.Mock()
        client.request.side_effect = [{"data": [], "nextCursor": "same"}, {"data": [], "nextCursor": "same"}]
        with self.assertRaises(ws.Fail):
            list(cs._pages(client, "thread/items/list", {"sortDirection": "asc"}))
        self.assertEqual(client.request.call_count, 2)

    def test_malformed_page_data_is_refused_without_exposing_it(self):
        for value in (None, HIDDEN, {"private": HIDDEN}):
            client = mock.Mock()
            client.request.return_value = {"data": value, "nextCursor": None}
            with self.subTest(value=type(value).__name__), self.assertRaises(ws.Fail) as failure:
                list(cs._pages(client, "thread/items/list", {}))
            self.assertNotIn(HIDDEN, str(failure.exception))

    def test_double_read_refuses_changes_inside_the_selected_range(self):
        first = snapshot()
        second = copy.deepcopy(first)
        second["items"][0]["item"]["content"][0]["text"] += " 読み取りの間の改変"
        with mock.patch.dict(os.environ, {"CODEX_THREAD_ID": SID}, clear=True), \
                mock.patch.object(cs, "Rpc"), mock.patch.object(cs, "_snapshot", side_effect=[first, second]) as read:
            with self.assertRaises(ws.Fail):
                cs.extract_session(SID, ws.Options(before="turn-two"))
            self.assertEqual(read.call_count, 2)

    def test_double_read_accepts_appends_after_the_frozen_cutoff(self):
        first = snapshot()
        second = copy.deepcopy(first)
        second["items"].append(entry("turn-two", "agentMessage", "append-after-cutoff",
                                     text="取得のあいだに増えた応答", phase="final_answer"))
        with mock.patch.dict(os.environ, {"CODEX_THREAD_ID": SID}, clear=True), \
                mock.patch.object(cs, "Rpc"), mock.patch.object(cs, "_snapshot", side_effect=[first, second]) as read:
            result = cs.extract_session(SID, ws.Options(before="turn-two"))
        self.assertEqual(read.call_count, 2)
        self.assertEqual(result.source_sha256, extracted(first, before="turn-two").source_sha256)
        self.assertNotIn("取得のあいだに増えた応答", ws.render(result, TITLE, [], []).decode("utf-8"))

    def test_rpc_error_and_malformed_stdio_do_not_disclose_payloads(self):
        error = {"jsonrpc": "2.0", "id": 1, "error": {"code": -32000, "message": HIDDEN}}
        for raw in ((json.dumps(error) + "\n").encode("utf-8"), (HIDDEN + " not json\n").encode("utf-8")):
            rpc = object.__new__(cs.Rpc)
            rpc.deadline = time.monotonic() + 5
            rpc.limit = 4096
            rpc.next_id = 0
            rpc.messages = queue.Queue()
            rpc.process = SimpleNamespace(stdin=io.BytesIO(), stdout=io.BytesIO(raw))
            rpc._read()
            with self.subTest(kind=raw[:1]), self.assertRaises(ws.Fail) as failure:
                rpc.request("thread/read", {"threadId": SID})
            self.assertNotIn(HIDDEN, str(failure.exception))


class CodexSharedWorkflowTests(unittest.TestCase):
    def setUp(self):
        self.base = Path(tempfile.mkdtemp(prefix="wiki-codex-session-"))
        self.addCleanup(remove_tree, self.base)
        self.wiki = self.base / "wiki"
        (self.wiki / "sources").mkdir(parents=True)
        (self.wiki / "SCHEMA.md").write_bytes("# 試験のスキーマ\n".encode("utf-8"))
        self.raw = self.base / "raw"
        self.raw.mkdir()

    def run_cli(self, args: list, code: int = 0, stdin: bytes | None = None, data: dict | None = None,
                adapter_patch: str = ""):
        source = repr(data if data is not None else snapshot())
        driver = (
            f"import sys; sys.path.insert(0, {str(SCRIPTS)!r})\n"
            "import wiki_session as ws\nimport wiki_codex_session as cs\n"
            f"fixture = {source}\n"
            "def fake_extract(sid, opts, max_bytes):\n"
            f"    assert sid == {SID!r}\n"
            "    return cs.extract_snapshot(fixture, opts, max_bytes)\n"
            "cs.extract_session = fake_extract\n"
            f"{adapter_patch}\n"
            "sys.exit(ws.main(sys.argv[1:]))\n"
        )
        result = subprocess.run(
            [sys.executable, "-X", "utf8", "-B", "-c", driver, *map(str, args)],
            cwd=self.base, env={**os.environ, "PYTHONUTF8": "1"}, input=stdin,
            capture_output=True, timeout=30,
        )
        self.assertEqual(result.returncode, code, result.stderr.decode("utf-8", "replace"))
        return result

    @staticmethod
    def common() -> list:
        return ["--transcript", f"codex:{SID}", "--utc-offset", "+09:00"]

    def init(self) -> Path:
        result = self.run_cli(["decide", "init", *self.common(), "--wiki", self.wiki, "--slug", "会話", "--json"])
        return Path(json.loads(result.stdout)["decisions"])

    def test_direct_script_catches_adapter_errors_without_a_traceback(self):
        # import して main を呼ぶ driver では、__main__ と wiki_session の二重読み込みを検出できない。
        # PATH を空にし、誤って Codex CLI を起動する余地もなくして入口そのものを試す。
        result = subprocess.run(
            [sys.executable, "-X", "utf8", "-B", str(SCRIPTS / "wiki_session.py"),
             "inspect", "--transcript", "codex:invalid", "--json"],
            cwd=self.base, env={**os.environ, "PYTHONUTF8": "1", "PATH": ""},
            capture_output=True, timeout=15,
        )
        self.assertEqual(result.returncode, 1)
        self.assertEqual(result.stdout, b"")
        error = result.stderr.decode("utf-8")
        self.assertIn("チャット ID は UUID", error)
        self.assertNotIn("Traceback", error)

    def test_locate_current_dispatches_to_codex_without_reading_claude(self):
        patch = (
            "def fake_locate(sid, current):\n"
            "    assert sid is None and current is True\n"
            f"    return {{'session_id': {SID!r}, 'transcript': 'codex:{SID}', 'before': 'turn-two', 'cutoff_kind': 'turn'}}\n"
            "cs.locate = fake_locate\n"
        )
        result = json.loads(self.run_cli(["locate", "--host", "codex", "--current", "--json"],
                                         adapter_patch=patch).stdout)
        self.assertEqual(result["transcript"], f"codex:{SID}")
        self.assertEqual(result["before"], "turn-two")
        self.assertEqual(result["cutoff_kind"], "turn")

    def test_list_dispatches_limit_and_returns_metadata(self):
        patch = (
            "def fake_list(limit):\n"
            "    assert limit == 1\n"
            f"    return [{{'session_id': {SID!r}, 'cwd': '~/work', 'transcript': 'codex:{SID}'}}]\n"
            "cs.list_sessions = fake_list\n"
        )
        result = json.loads(self.run_cli(["list", "--host", "codex", "--limit", "1", "--json"],
                                         adapter_patch=patch).stdout)
        self.assertEqual(len(result), 1)
        self.assertEqual(result[0]["session_id"], SID)

    def test_inspect_and_show_do_not_export_a_copy(self):
        result = self.run_cli(["inspect", *self.common(), "--json"])
        inspected = json.loads(result.stdout)
        self.assertEqual(inspected["verdict"], "session")
        self.assertEqual(inspected["session_id"], SID)
        self.assertNotIn(HIDDEN.encode(), result.stdout)
        decisions = self.init()
        self.run_cli(["show", *self.common(), "--title", TITLE, "--decisions", decisions])
        for path in self.base.rglob("*"):
            if path.is_file():
                data = path.read_bytes()
                self.assertNotIn(PRIVATE.encode(), data)
                self.assertNotIn(EMAIL.encode(), data)
                self.assertNotIn(KEY.encode(), data)
                self.assertNotIn("索引を確認します".encode(), data)

    def test_mark_drop_write_scan_and_verify_share_the_same_contract(self):
        decisions = self.init()
        self.run_cli(["decide", "mark", *self.common(), "--decisions", decisions,
                      "--text", PRIVATE, "--all-turns", "--json"])
        drop = next(t.n for t in extracted().turns if "この発言" in t.body)
        self.run_cli(["decide", "drop", *self.common(), "--decisions", decisions, "--turn", f"T{drop}", "--json"])
        result = self.run_cli(["show", *self.common(), "--title", TITLE, "--decisions", decisions])
        self.assertNotIn(PRIVATE.encode(), result.stdout)
        self.assertNotIn("この発言".encode(), result.stdout)
        self.assertIn(ws.MARK_DROPPED.encode(), result.stdout)
        meta = json.loads(self.run_cli(["show", *self.common(), "--title", TITLE, "--decisions", decisions,
                                       "--slug", "会話", "--meta", "--json"]).stdout)
        self.assertGreater(meta["manual_redactions"], 0)
        self.assertEqual(meta["dropped_turns"], 1)
        findings = self.run_cli(["scan", *self.common(), "--decisions", decisions, "--json"], code=1,
                                stdin=f"記事へ {PRIVATE} を書き戻した。".encode("utf-8"))
        self.assertTrue(json.loads(findings.stdout)["findings"])
        self.assertNotIn(PRIVATE.encode(), findings.stdout)
        self.run_cli(["scan", *self.common(), "--decisions", decisions, "--json"], stdin="索引を整理した。".encode())
        write_args = ["write", *self.common(), "--title", TITLE, "--decisions", decisions,
                      "--wiki", self.wiki, "--raw-root", self.raw, "--slug", "会話",
                      "--expect-sha256", meta["render_sha256"], "--json"]
        written = json.loads(self.run_cli(write_args).stdout)
        self.assertEqual(written["raw_state"], "created")
        raw = Path(written["raw_path"])
        self.assertEqual(hashlib.sha256(raw.read_bytes()).hexdigest(), meta["render_sha256"])
        self.assertTrue(ws.is_read_only(raw))
        self.assertNotIn(PRIVATE.encode(), raw.read_bytes())
        verified = json.loads(self.run_cli(["verify", "--raw-root", self.raw, "--slug", "会話",
                                           "--expect-sha256", meta["render_sha256"], "--json"]).stdout)
        self.assertTrue(verified["sha256_matches"])
        self.assertTrue(verified["read_only"])
        self.assertEqual(json.loads(self.run_cli(write_args).stdout)["raw_state"], "identical")

    def test_write_refuses_a_changed_source_without_creating_raw(self):
        decisions = self.init()
        meta = json.loads(self.run_cli(["show", *self.common(), "--title", TITLE, "--decisions", decisions,
                                       "--meta", "--json"]).stdout)
        changed = snapshot()
        changed["items"][0]["item"]["content"][0]["text"] += " 改変"
        self.run_cli(["write", *self.common(), "--title", TITLE, "--decisions", decisions,
                      "--wiki", self.wiki, "--raw-root", self.raw, "--slug", "会話",
                      "--expect-sha256", meta["render_sha256"], "--json"], code=1, data=changed)
        self.assertEqual(list(self.raw.iterdir()), [])


if __name__ == "__main__":
    unittest.main()
