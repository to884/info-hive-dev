"""Dreaming の提案を原本と照合する。Claude は起動しない。"""

from argparse import Namespace
from contextlib import closing
import hashlib
import importlib.util
import json
from pathlib import Path
import sqlite3
import sys
import tempfile
import unittest
from unittest.mock import patch


ROOT = Path(__file__).resolve().parents[2]
spec = importlib.util.spec_from_file_location("wiki_dream_run", ROOT / "poc/wiki-dream/run.py")
dream = importlib.util.module_from_spec(spec)
sys.modules[spec.name] = dream
spec.loader.exec_module(dream)


class WikiDreamTests(unittest.TestCase):
    def setUp(self):
        wiki = ROOT / "wiki"
        self.article = dream.Snapshot(
            wiki / "concepts/例.md", wiki,
            '---\ntype: "concept"\n---\n\n# 例\n\nv1 で保存を検証した。\n'.encode(),
        )
        source = dream.Snapshot(wiki / "sources/試行.md", wiki, b"")
        raw_root = ROOT / "raw"
        self.raw = dream.Snapshot(raw_root / "試行.md", raw_root,
                                  "実行後に保存された件数は4件だった。\n再実行で上書きされないことも確認した。\n".encode())
        self.sessions = {"s1": (source, self.raw)}
        self.pages = {"p1": self.article}
        self.index = dream.build_page_index(
            [{"slug": path.path.stem, "rel_path": path.relative} for path in (self.article, source)],
            value=lambda page: page["rel_path"],
        )
        self.finding = {"line": 1, "quote": "保存された件数は4件だった", "claim": "4件を保存した"}
        self.edit = {
            "page": "p1", "line": 7, "text": "v1 で保存を検証し、4件を保存した。",
            "reason": "検証件数を確認した",
            "evidence": [{
                "source": "s1", "line": 1, "checked_line": 2, "checked_quote": "再実行で上書きされない",
            }],
        }

    def compose(self):
        output = {
            "findings": [{"source": "s1", "findings": [self.finding]}],
            "conclusion": {"edits": [self.edit], "notes": ""},
        }
        return dream.compose(output, self.sessions, self.pages, self.index)

    def test_diff_adds_verified_source_without_writing_article(self):
        diff, report, skipped = self.compose()
        self.assertIn("+v1 で保存を検証し、4件を保存した。 [[sources/試行]]", diff)
        self.assertIn(f"{self.raw.path}:1", report[0])
        self.assertEqual(skipped, [])
        self.assertIn("v1 で保存を検証した。", self.article.text)

    def test_unverified_quote_cannot_enter_diff(self):
        self.finding["quote"] = "保存された件数は5件だった"
        diff, report, skipped = self.compose()
        self.assertEqual((diff, report), ("", []))
        self.assertEqual(len(skipped), 1)

    def test_integration_must_have_independent_evidence(self):
        self.edit["evidence"][0].update(checked_line=1, checked_quote=self.finding["quote"])
        self.finding["claim"] = "報告の原文は「保存された件数は4件だった」。"
        diff, report, skipped = self.compose()
        self.assertEqual((diff, report), ("", []))
        self.assertEqual(len(skipped), 1)

    def test_diff_uses_lf_line_numbers_and_preserves_crlf(self):
        article = self.article
        self.pages["p1"] = dream.Snapshot(
            article.path, article.root,
            article.text.replace("検証した。", "検証した。\u2028付記").replace("\n", "\r\n").encode(),
        )
        diff, report, skipped = self.compose()
        self.assertIn("-v1 で保存を検証した。\u2028付記\r\n", diff)
        self.assertIn("+v1 で保存を検証し、4件を保存した。 [[sources/試行]]\r\n", diff)
        self.assertEqual((len(report), skipped), (1, []))

    def test_source_without_recorded_digest_is_not_selected(self):
        with tempfile.TemporaryDirectory() as name:
            wiki = Path(name) / "wiki"
            path = wiki / "sources" / "古い会話.md"
            path.parent.mkdir(parents=True)
            path.write_text('---\ntype: "source"\nsession_id: "sample"\n---\n\n# 古い会話\n', encoding="utf-8")
            self.assertEqual(dream.select_sources([path], wiki, [], 2), [])
            with self.assertRaisesRegex(ValueError, "SHA-256 が記録されていません"):
                dream.select_sources([path], wiki, ["古い会話"], 2)

    def test_heading_and_new_link_are_not_editable(self):
        for number, text in [(5, "# 別の見出し"), (7, "記録 [[実在しないページ]]")]:
            with self.subTest(number=number):
                self.edit.update(line=number, text=text)
                diff, report, skipped = self.compose()
                self.assertEqual((diff, report), ("", []))
                self.assertEqual(len(skipped), 1)

    def test_duplicate_edits_do_not_prevent_proposals_for_other_lines(self):
        article = self.article
        self.pages["p1"] = dream.Snapshot(
            article.path, article.root, article.data + "再実行を検証した。\n".encode("utf-8"),
        )
        result = {
            "findings": [{"source": "s1", "findings": [self.finding]}],
            "conclusion": {"edits": [{**self.edit, "line": 8}, self.edit, self.edit], "notes": ""},
        }
        diff, report, skipped = dream.compose(result, self.sessions, self.pages, self.index)
        self.assertIn("-再実行を検証した。", diff)
        self.assertEqual((len(report), len(skipped)), (1, 2))

    def test_concurrent_change_is_detected(self):
        with tempfile.TemporaryDirectory() as name:
            root = Path(name)
            path = root / "記事.md"
            path.write_bytes(b"old")
            snapshot = dream.read_snapshot(path, root)
            path.write_bytes(b"new")
            with self.assertRaisesRegex(ValueError, "版が変わりました"):
                snapshot.verify()


class ScheduledWikiDreamTests(unittest.TestCase):
    def setUp(self):
        directory = tempfile.TemporaryDirectory()
        self.addCleanup(directory.cleanup)
        root = Path(directory.name).resolve()
        self.wiki = root / "wiki"
        self.raw = root / "raw"
        self.out = root / "out"
        for path in (self.wiki / "concepts", self.wiki / "sources", self.raw):
            path.mkdir(parents=True)
        (self.wiki / "SCHEMA.md").write_text("# Schema\n", encoding="utf-8")
        (self.wiki / "concepts" / "例.md").write_text(
            '---\ntype: "concept"\n---\n\n# 例\n\nv1 で保存を検証した。\n', encoding="utf-8",
        )
        self.add_source("a")
        self.add_source("b")
        self.args = Namespace(source=[], limit=2, timeout=10, out=self.out, scheduled=True)

    def add_source(self, name, suffix=""):
        data = f'---\nsession_id: "{name}"\n---\n\n検証結果を記録した。{suffix}\n'.encode("utf-8")
        (self.raw / f"{name}.md").write_bytes(data)
        (self.wiki / "sources" / f"{name}.md").write_text(
            f'---\ntype: "source"\nsession_id: "{name}"\n'
            f'raw: "raw/{name}.md"\nraw_sha256: "{hashlib.sha256(data).hexdigest()}"\n'
            '---\n\n[[例]]\n', encoding="utf-8",
        )

    def run_job(self):
        with patch("builtins.print"):
            return dream.propose(self.wiki, self.raw, self.args)

    def states(self):
        with closing(sqlite3.connect(self.out / "ledger.sqlite")) as db:
            return db.execute("SELECT session_id, state FROM sessions ORDER BY session_id, attempt").fetchall()

    def fake_result(self, staging, manifest, timeout, incomplete=()):
        readings = [
            {"source": source["id"], "findings": [], "checks": [
                (staging / file).read_text(encoding="utf-8").splitlines()[-1].split()[-1]
                for file in source["chunks"]
            ]}
            for source in manifest["sources"] if source["id"] not in incomplete
        ]
        return {
            "run": manifest["run"], "incomplete": list(incomplete),
            "findings": readings,
            "conclusion": {"edits": [], "notes": ""},
        }, {}

    def test_partial_failure_retries_only_failed_source_and_new_version(self):
        with patch.object(dream, "claude_workflow", side_effect=lambda *a: self.fake_result(*a, incomplete=["s2"])):
            self.assertEqual(self.run_job(), 1)
        self.assertEqual(self.states(), [("a", "done"), ("b", "retry")])
        with patch.object(dream, "claude_workflow", side_effect=self.fake_result) as workflow:
            self.assertEqual(self.run_job(), 0)
            self.assertEqual(workflow.call_args.args[1]["sources"], [{"id": "s1", "chunks": ["s1-part1.txt"]}])
            self.assertEqual(self.run_job(), 0)
            self.assertEqual(workflow.call_count, 1)
            self.add_source("a", "内容を更新した。")
            self.assertEqual(self.run_job(), 0)
            self.assertEqual(workflow.call_count, 2)
        self.assertEqual(self.states(), [("a", "done"), ("a", "done"), ("b", "done")])
        receipts = [json.loads(file.read_text(encoding="utf-8")) for file in self.out.glob("*/run.json")]
        self.assertEqual(len(receipts), 3)
        self.assertIn(["sources/b.md"], [[item["source"] for item in run["inputs"]] for run in receipts])

    def test_changed_raw_does_not_stop_other_source(self):
        (self.raw / "b.md").write_text("原本が変更された。", encoding="utf-8")
        with patch.object(dream, "claude_workflow", side_effect=self.fake_result) as workflow:
            self.assertEqual(self.run_job(), 1)
            self.assertEqual(workflow.call_args.args[1]["sources"], [{"id": "s1", "chunks": ["s1-part1.txt"]}])
        self.assertEqual(self.states(), [("a", "done"), ("b", "retry")])

    def test_retry_keeps_a_slot_when_new_sources_arrive(self):
        with patch.object(dream, "claude_workflow", side_effect=lambda *a: self.fake_result(*a, incomplete=["s2"])):
            self.assertEqual(self.run_job(), 1)
        self.add_source("c")
        self.add_source("d")
        with patch.object(dream, "claude_workflow", side_effect=self.fake_result):
            self.assertEqual(self.run_job(), 0)
        self.assertEqual(self.states(), [("a", "done"), ("b", "done"), ("c", "done")])

    def test_limit_one_keeps_a_slot_for_new_sources_despite_multiple_failures(self):
        self.args.limit = 1
        for name in ("a", "b"):
            (self.raw / f"{name}.md").write_text("台帳と一致しない内容", encoding="utf-8")
            self.args.source = [name]
            self.assertEqual(self.run_job(), 1)
        self.args.source = []
        self.add_source("c")
        with patch.object(dream, "claude_workflow", side_effect=self.fake_result):
            self.assertIn(0, [self.run_job(), self.run_job()])
        self.assertIn(("c", "done"), self.states())

    def test_shared_workflow_failure_is_retried_in_independent_workflows(self):
        with patch.object(dream, "claude_workflow", side_effect=ValueError("統合処理が中断")):
            self.assertEqual(self.run_job(), 1)

        def retry(staging, manifest, timeout):
            self.assertEqual(len(manifest["sources"]), 1)
            data = (staging / "s1.txt").read_text(encoding="utf-8")
            if 'session_id: "a"' in data:
                raise ValueError("会話 a は引き続き失敗")
            return self.fake_result(staging, manifest, timeout)

        with patch.object(dream, "claude_workflow", side_effect=retry):
            self.assertEqual(self.run_job(), 1)
        self.assertEqual(self.states(), [("a", "retry"), ("b", "done")])

    def test_missing_last_chunk_does_not_mark_source_done(self):
        self.add_source("a", "\n" + "確認した記録です。\n" * 900)
        self.args.source = ["a"]

        def incomplete_read(*args):
            result, models = self.fake_result(*args)
            checks = result["findings"][0]["checks"]
            self.assertGreater(len(checks), 1)
            checks.pop()
            return result, models

        with patch.object(dream, "claude_workflow", side_effect=incomplete_read):
            self.assertEqual(self.run_job(), 1)
        self.assertEqual(self.states(), [("a", "retry")])
        with patch.object(dream, "claude_workflow", side_effect=self.fake_result):
            self.assertEqual(self.run_job(), 0)
        self.assertEqual(self.states(), [("a", "done")])

    def test_competing_run_skips_workflow(self):
        self.out.mkdir()
        db = sqlite3.connect(self.out / "ledger.sqlite")
        self.addCleanup(db.close)
        db.execute("BEGIN IMMEDIATE")
        with patch.object(dream, "claude_workflow") as workflow:
            self.assertEqual(self.run_job(), 0)
            workflow.assert_not_called()

    def test_unsaved_proposal_leaves_all_sources_eligible(self):
        with patch.object(dream, "claude_workflow", side_effect=self.fake_result):
            with patch.object(dream, "save_proposal", side_effect=OSError("保存先に書き込めない")):
                self.assertEqual(self.run_job(), 1)
            self.assertEqual(self.states(), [("a", "retry"), ("b", "retry")])
            self.assertEqual(self.run_job(), 0)
        self.assertEqual(self.states(), [("a", "done"), ("b", "done")])


class WorkflowResultTests(unittest.TestCase):
    def test_requires_expected_models_and_checks_partial_completion(self):
        with tempfile.TemporaryDirectory() as directory:
            output = Path(directory) / "claude" / "sample" / "tasks" / "task.output"
            output.parent.mkdir(parents=True)
            manifest = {"run": "run", "sources": [{"id": "s1"}, {"id": "s2"}], "pages": []}
            call = {"id": "call", "type": "tool_use", "name": "Workflow", "input": {
                "name": "wiki-dream", "args": manifest,
            }}
            events = [
                {"type": "assistant", "message": {"content": [call]}},
                {"subtype": "task_started", "workflow_name": "wiki-dream", "tool_use_id": "call",
                 "task_id": "task", "run_id": "run", "prompt": dream.WORKFLOW.read_text(encoding="utf-8")},
                {"subtype": "task_notification", "task_id": "task", "run_id": "run",
                 "status": "completed", "output_file": str(output)},
            ]
            models = [
                {"type": "workflow_agent", "label": "s1", "model": "claude-haiku-5-5", "state": "done"},
                {"type": "workflow_agent", "label": "s2", "model": "claude-haiku-5-5", "state": "failed"},
                {"type": "workflow_agent", "label": "integration", "model": "claude-sonnet-5-5", "state": "done"},
            ]
            result = {
                "run": "run", "incomplete": ["s2"], "findings": [{"source": "s1", "findings": []}],
                "conclusion": {"edits": [], "notes": ""},
            }
            with patch.object(dream.tempfile, "gettempdir", return_value=directory):
                output.write_text(json.dumps({"result": result, "workflowProgress": models}), encoding="utf-8")
                actual, used = dream.workflow_result(events, manifest, 0)
                self.assertEqual(actual["incomplete"], ["s2"])
                self.assertEqual(set(used), {"s1", "integration"})
                with self.assertRaisesRegex(ValueError, "一度だけ起動"):
                    dream.workflow_result(events + [events[0]], manifest, 0)
                models[0]["model"] = "claude-sonnet-5-5"
                output.write_text(json.dumps({"result": result, "workflowProgress": models}), encoding="utf-8")
                with self.assertRaisesRegex(ValueError, "指定したモデル"):
                    dream.workflow_result(events, manifest, 0)
                output.write_text('{"result": []}', encoding="utf-8")
                with self.assertRaisesRegex(ValueError, "所定の形式ではありません"):
                    dream.workflow_result(events, manifest, 0)
