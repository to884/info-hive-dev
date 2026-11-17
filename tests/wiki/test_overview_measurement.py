"""Sonnet の測定で、呼び出しだけを手順の成功と数えないことを確かめる。LLM は起動しない。"""
from __future__ import annotations

import importlib.util
import json
import unittest
from pathlib import Path

SPEC = importlib.util.spec_from_file_location("measure_overview_command", Path(__file__).with_name("measure_overview_command.py"))
measurement = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(measurement)

GUIDE = "SVG と Mermaid\n## 下書きの形\n## 図を書くときの目安"
COPY = "資料を整理する流れ\n原本は資料を確かめ直す\nメモの内容が変わったら"


class MeasurementTraceTests(unittest.TestCase):
    def trace(self):
        rows = []
        def call(identifier, tool, value, result):
            key = "command" if tool == "Bash" else "file_path"
            rows.append({"type": "assistant", "message": {"model": "claude-sonnet-5-5", "content": [
                {"type": "tool_use", "id": identifier, "name": tool, "input": {key: value}}]}})
            rows.append({"type": "user", "message": {"content": [
                {"type": "tool_result", "tool_use_id": identifier, "content": result}]}})
        call("begin", "Bash", 'python "wiki_overview.py" begin wiki', '{"status":"ready","request_path":"x"}')
        call("request", "Write", "wiki/.wiki-cache/overview/request.json", "created")
        call("guide", "Read", "plugin/references/overview-workflow.md", GUIDE)
        call("page", "Read", "wiki/.wiki-cache/overview/work/abc/page.md", COPY)
        call("check", "Bash", 'python "wiki_overview.py" check wiki --work=abc', '{"status":"ok"}')
        call("write", "Bash", 'python "wiki_overview.py" write wiki --work=abc', '{"status":"written"}')
        rows.append({"type": "result", "subtype": "success", "is_error": False})
        return rows

    def analyze(self, rows):
        return measurement.analyze_trace("\n".join(json.dumps(row) for row in rows))

    def result(self, rows, identifier):
        return next(row["message"]["content"][0] for row in rows
                    if row["type"] == "user" and row["message"]["content"][0]["tool_use_id"] == identifier)

    def test_successful_calls_and_results(self):
        report = self.analyze(self.trace())
        self.assertTrue(all(report["checks"].values()), report)
        self.assertEqual(report["operations"], ["begin", "check", "write"])

    def test_failed_reads_and_rejected_check_do_not_pass(self):
        rows = self.trace()
        for identifier in ("guide", "page"):
            self.result(rows, identifier).update(is_error=True, content="File not found")
        self.result(rows, "check")["content"] = '{"status":"rejected","problems":["assembly"]}'
        checks = self.analyze(rows)["checks"]
        for name in ("guide_read", "page_copy_read", "check_then_write"):
            self.assertFalse(checks[name], name)

    def test_missing_failed_or_mismatched_tool_results(self):
        for identifier, name in (("begin", "begin_before_request_write"), ("request", "begin_before_request_write"),
                                 ("guide", "guide_read"), ("page", "page_copy_read"),
                                 ("check", "check_then_write"), ("write", "check_then_write")):
            for change in ("missing", "failed", "other_id"):
                with self.subTest(identifier=identifier, change=change):
                    rows = self.trace()
                    result = self.result(rows, identifier)
                    if change == "missing":
                        rows = [row for row in rows if row.get("message", {}).get("content", [None])[0] is not result]
                    elif change == "failed":
                        result["is_error"] = True
                    else:
                        result["tool_use_id"] = "unknown"
                    self.assertFalse(self.analyze(rows)["checks"][name])

    def test_partial_reads_do_not_prove_the_instructions_arrived(self):
        rows = self.trace()
        self.result(rows, "guide")["content"] = "SVG と Mermaid"
        self.result(rows, "page")["content"] = "資料を整理する流れ"
        checks = self.analyze(rows)["checks"]
        self.assertFalse(checks["guide_read"])
        self.assertFalse(checks["page_copy_read"])

    def test_later_retry_cannot_hide_request_write_before_begin(self):
        rows = self.trace()
        rows[:0] = [
            {"type": "assistant", "message": {"model": "claude-sonnet-5-5", "content": [
                {"type": "tool_use", "id": "early", "name": "Write", "input": {"file_path": "wiki/.wiki-cache/overview/request.json"}}]}},
            {"type": "user", "message": {"content": [{"type": "tool_result", "tool_use_id": "early", "content": "created"}]}}]
        self.assertFalse(self.analyze(rows)["checks"]["begin_before_request_write"])

    def test_begin_and_check_results_must_arrive_before_dependent_calls(self):
        for identifier, name in (("begin", "begin_before_request_write"), ("check", "check_then_write")):
            with self.subTest(identifier=identifier):
                rows = self.trace()
                result = self.result(rows, identifier)
                row = next(row for row in rows if row.get("message", {}).get("content", [None])[0] is result)
                rows.remove(row)
                rows.insert(-1, row)
                self.assertFalse(self.analyze(rows)["checks"][name])

    def test_text_block_results_are_accepted(self):
        rows = self.trace()
        for row in rows:
            if row["type"] == "user":
                result = row["message"]["content"][0]
                result["content"] = [{"type": "text", "text": result["content"]}]
        self.assertTrue(all(self.analyze(rows)["checks"].values()))

    def test_batched_shell_operations_keep_their_order_and_results(self):
        for operations, values, expected in (
                (("check", "write"), ("ok", "written"), True),
                (("write", "check"), ("written", "ok"), False),
                (("check", "write"), ("rejected", "written"), False)):
            with self.subTest(operations=operations, values=values):
                rows = self.trace()
                rows = [row for row in rows if row.get("message", {}).get("content", [{}])[0].get("id") != "write"
                        and row.get("message", {}).get("content", [{}])[0].get("tool_use_id") != "write"]
                check = next(row["message"]["content"][0] for row in rows
                             if row.get("message", {}).get("content", [{}])[0].get("id") == "check")
                check["input"]["command"] = " && ".join(f'python "wiki_overview.py" {op} wiki --work=abc' for op in operations)
                self.result(rows, "check")["content"] = json.dumps({"stdout": "\n".join(json.dumps({"status": value}) for value in values)})
                self.assertEqual(self.analyze(rows)["checks"]["check_then_write"], expected)

    def test_missing_final_error_and_wrong_model_do_not_pass(self):
        for change in ("missing", "error", "other_model"):
            rows = self.trace()
            if change == "missing":
                rows.pop()
            elif change == "error":
                rows[-1].update(is_error=True, subtype="error_during_execution")
            else:
                for row in rows:
                    if row["type"] == "assistant":
                        row["message"]["model"] = "claude-opus-5-5"
            checks = self.analyze(rows)["checks"]
            self.assertFalse(checks["sonnet_5_5" if change == "other_model" else "final_success"])

    def test_attempts_to_use_the_page_in_shell_or_write_final_sidecar_fail(self):
        rows = self.trace()
        for row in rows:
            block = row.get("message", {}).get("content", [{}])[0]
            if block.get("id") == "begin":
                block["input"]["command"] += " " + measurement.PAGE
            elif block.get("id") == "request":
                block["input"]["file_path"] = "wiki/assets/overview/direct.overview.md"
        checks = self.analyze(rows)["checks"]
        self.assertFalse(checks["page_not_in_shell"])
        self.assertFalse(checks["no_direct_sidecar_write"])


if __name__ == "__main__":
    unittest.main()
