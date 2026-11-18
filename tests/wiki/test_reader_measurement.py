"""読むモデルの測定で、読む失敗や欠測を採用の根拠にしないこと。API は呼ばない。"""
from __future__ import annotations

import contextlib
import io
import json
import subprocess
import sys
import tempfile
import threading
import unittest
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parent))
import measure_reader_models as measurement
import reader_measurement_runtime as runtime


def encode(events):
    return "\n".join(json.dumps(e, ensure_ascii=False) for e in events).encode("utf-8")


class MeasurementTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.out = Path(self.temp.name)
        self.roots = {s: self.out / "snapshot" / s / "wiki" for s in ("project", "user")}
        for root in self.roots.values():
            (root / "concepts").mkdir(parents=True)
            (root / "concepts/a.md").write_text("# A\n\nalpha\n", encoding="utf-8")
            (root / "concepts/b.md").write_text("# B\n\nbeta\n", encoding="utf-8")
        self.question = {"id": "q", "class": "R1", "prompt": "alpha の記録を確認して",
                         "candidates": ["concepts/a.md"], "must_read": ["concepts/a.md"],
                         "facts": ["alpha"], "fact_sources": {"alpha": "concepts/a.md L3: alpha"}}
        self.experiment = {"fingerprint": "fixed", "spec": {"runs": 2}}

    def events(self, model="haiku", *, failed_read=False):
        answer = f"## 答え\nalpha\n## 根拠\n- [[a]]（{self.roots['project'].as_posix()}/concepts/a.md）: alpha"
        return [
            {"type": "system", "subtype": "init", "model": f"claude-{model}-5-5"},
            {"type": "assistant", "message": {"content": [
                {"type": "tool_use", "name": "Read", "id": "read-1", "input": {
                    "file_path": str(self.roots["project"] / "concepts/a.md")}}]}},
            {"type": "user", "message": {"content": [
                {"type": "tool_result", "tool_use_id": "read-1", "is_error": failed_read,
                 "content": "読めなかった" if failed_read else "alpha"}]}},
            {"type": "result", "result": answer, "is_error": False, "total_cost_usd": .01,
             "duration_ms": 1000, "modelUsage": {f"claude-{model}-5-5": {"inputTokens": 10}}},
        ]

    def record(self, model="haiku", effort="low", run=1):
        return {"protocol": measurement.PROTOCOL, "fingerprint": "fixed", "id": "q", "class": "R1",
                "model": model, "effort": effort, "run": run, "exit": 0,
                **measurement.parse_events(encode(self.events(model)), self.roots)}

    def test_only_successful_read_results_count(self):
        events = self.events(failed_read=True)
        self.assertEqual(measurement.parse_events(encode(events), self.roots)["opened"], [])
        events.pop(2)
        self.assertEqual(measurement.parse_events(encode(events), self.roots)["opened"], [])
        self.assertEqual(measurement.parse_events(encode(self.events()), self.roots)["opened"],
                         ["project:concepts/a.md"])

    def test_glob_and_reads_outside_the_wiki_do_not_count(self):
        for name, target in (("Glob", self.roots["project"] / "concepts/a.md"),
                             ("Read", self.out / "outside.md")):
            events = self.events()
            block = events[1]["message"]["content"][0]
            block.update({"name": name, "input": {"file_path": str(target)}})
            self.assertEqual(measurement.parse_events(encode(events), self.roots)["opened"], [])

    def test_matching_basename_in_another_scope_does_not_count(self):
        record = self.record()
        record["opened"] = ["user:concepts/a.md"]
        result = measurement.score(record, self.question, self.roots)
        self.assertFalse(result["read_all_must"])
        self.assertEqual(result["fact_rate"], 0)
        self.assertEqual(result["unopened"], ["project:concepts/a.md"])

    def test_wrong_wikilink_is_distinct_from_unopened_citation(self):
        record = self.record()
        record["result"] = record["result"].replace("[[a]]", "[[A の表示用の題]]")
        result = measurement.score(record, self.question, self.roots)
        self.assertEqual(result["unopened_citations"], 0)
        self.assertEqual(result["invalid_citations"], ["A の表示用の題"])
        self.assertFalse(result["has_citations"])

    def test_ambiguous_scope_requires_the_absolute_path(self):
        record = self.record()
        record["result"] = "## 答え\nalpha\n## 根拠\n- [[a]]（concepts/a.md）: alpha"
        question = {**self.question, "candidates": ["concepts/a.md", "user:concepts/a.md"]}
        result = measurement.score(record, question, self.roots)
        self.assertEqual(result["ambiguous_citations"], ["a"])

    def test_unoffered_scope_does_not_make_a_citation_ambiguous(self):
        record = self.record()
        record["result"] = "## 答え\nalpha\n## 根拠\n- [[a]]（concepts/a.md）: alpha"
        result = measurement.score(record, self.question, self.roots)
        self.assertEqual(result["ambiguous_citations"], [])
        self.assertTrue(result["has_citations"])

    def test_nested_citations_use_parent_paths_without_leaking_to_siblings(self):
        record = self.record()
        record["opened"].append("user:concepts/a.md")
        record["result"] = (f"## 答え\nalpha\n## 根拠\n- project: {self.roots['project'].as_posix()}/concepts/a.md\n"
                            "  - [[a]]: alpha\n"
                            f"- user: {self.roots['user'].as_posix()}/concepts/a.md\n"
                            "  - [[a]]: alpha\n")
        question = {**self.question, "candidates": ["concepts/a.md", "user:concepts/a.md"]}
        self.assertEqual(measurement.score(record, question, self.roots)["ambiguous_citations"], [])
        record["result"] += "- [[a]]: スコープなし\n"
        self.assertEqual(measurement.score(record, question, self.roots)["ambiguous_citations"], ["a"])

    def test_missing_sections_do_not_score_the_echoed_question(self):
        record = self.record()
        record["result"] = "候補: alpha [[a]]"
        result = measurement.score(record, self.question, self.roots)
        self.assertEqual(result["fact_rate"], 0)
        self.assertFalse(result["ok"])
        self.assertTrue(result["observation_ok"])
        self.assertFalse(result["format_ok"])

    def test_format_failure_is_a_quality_observation_and_is_not_retried(self):
        record = self.record()
        record["fingerprint"] = "fixed"
        record["result"] = "形式を守らなかった回答"
        path = self.out / "runs/q__haiku-low__1.json"
        path.parent.mkdir()
        path.write_text(json.dumps(record), encoding="utf-8")
        with patch.object(runtime.subprocess, "run") as run:
            self.assertEqual(measurement.run_once(self.question, "haiku", "low", 1, self.out,
                                                 self.experiment, retry_failed=True), path)
            run.assert_not_called()

    def test_auto_memory_contamination_rejects_protocol_three(self):
        record = self.record()
        record.update(protocol=3, memory_paths={"auto": "shared-memory"})
        self.assertFalse(measurement.valid_observation(record))
        record["memory_paths"] = {}
        self.assertTrue(measurement.valid_observation(record))

    def test_model_mismatch_or_missing_cost_rejects_a_run(self):
        for changed in ({"model_used": "claude-opus-5-5"}, {"model_usage": {}}, {"cost_usd": None},
                        {"cost_usd": float("nan")}, {"duration_ms": None},
                        {"model_usage": {"claude-haiku-5-5": {}, "claude-opus-5-5": {}}}):
            result = measurement.score({**self.record(), **changed}, self.question, self.roots)
            self.assertFalse(result["ok"])

    def test_quota_is_not_a_success_even_with_exit_zero(self):
        record = self.record()
        record.update({"exit": 0, "is_error": True, "api_error_status": 429, "result": "limit"})
        self.assertTrue(measurement.quota_error(record))
        self.assertFalse(measurement.score(record, self.question, self.roots)["ok"])

    def test_retry_preserves_the_failed_attempt_and_raw_events(self):
        failure = [{"type": "result", "is_error": True, "api_error_status": 429,
                    "result": "You've hit your limit", "total_cost_usd": 0}]
        replies = [subprocess.CompletedProcess([], 1, encode(failure), b""),
                   subprocess.CompletedProcess([], 0, encode(self.events()), b"")]
        stop = threading.Event()
        with patch.object(runtime.subprocess, "run", side_effect=replies) as run:
            path = measurement.run_once(self.question, "haiku", "low", 1, self.out, self.experiment, stop=stop)
            self.assertTrue(stop.is_set())
            stop.clear()
            measurement.run_once(self.question, "haiku", "low", 1, self.out, self.experiment, stop=stop)
            self.assertEqual(run.call_count, 1)
            stop.clear()
            measurement.run_once(self.question, "haiku", "low", 1, self.out, self.experiment, True, stop)
            self.assertEqual(run.call_count, 2)
        current = json.loads(path.read_text(encoding="utf-8"))
        self.assertFalse(current["is_error"])
        self.assertEqual(current["opened"], ["project:concepts/a.md"])
        self.assertTrue(current["events"])
        previous = list((self.out / "attempts").glob("*.json"))
        self.assertEqual(len(previous), 1)
        self.assertTrue(json.loads(previous[0].read_text(encoding="utf-8"))["is_error"])

    def test_quota_stops_the_batch_before_scheduling_more_calls(self):
        args = SimpleNamespace(out=self.out, runs=2, workers=4, question=["q"], only=None, retry_failed=False)
        data = self.out / "data.json"
        data.write_text(json.dumps({"questions": [self.question]}), encoding="utf-8")

        def blocked(*args):
            args[-1].set()
            return Path("failed.json")

        with patch.object(measurement, "DATA", data), patch.object(measurement, "prepare", return_value={
                **self.experiment, "spec": {"seed": 32}}), patch.object(measurement, "run_once", blocked), \
                patch.object(measurement.concurrent.futures, "ThreadPoolExecutor") as pool, \
                contextlib.redirect_stdout(io.StringIO()), contextlib.redirect_stderr(io.StringIO()):
            self.assertEqual(measurement.cmd_run(args), 3)
            pool.assert_not_called()

    def test_snapshot_change_is_rejected_on_resume(self):
        import eval_prompt_context

        target = self.out / "experiment"

        def materialize(commit, project):
            (project / "wiki").mkdir(parents=True)
            (project / "wiki/SCHEMA.md").write_text("# SCHEMA\n", encoding="utf-8")

        version = subprocess.CompletedProcess([], 0, "test-cli", "")
        with patch.object(eval_prompt_context, "materialize", materialize), \
                patch.object(runtime.subprocess, "run", return_value=version):
            manifest = measurement.prepare(target, 2)
            self.assertEqual(measurement.prepare(target, 2), manifest)
            with patch.object(measurement, "PLUGIN", Path("missing-current-plugin")):
                archived, _ = measurement.recorded_experiment(target)
                self.assertEqual(archived, manifest)
            (target / "snapshot/project/wiki/SCHEMA.md").write_text("changed", encoding="utf-8")
            with self.assertRaisesRegex(ValueError, "固定した入力"):
                measurement.prepare(target, 2)
            with self.assertRaisesRegex(ValueError, "固定した入力"):
                measurement.recorded_experiment(target)

    def make_summary(self, complete):
        data = self.out / "data.json"
        data.write_text(json.dumps({"questions": [self.question]}), encoding="utf-8")
        (self.out / "experiment.json").write_text(json.dumps(self.experiment), encoding="utf-8")
        (self.out / "runs").mkdir()
        combos = measurement.COMBOS if complete else measurement.COMBOS[:1]
        for model, effort in combos:
            for run in (1, 2):
                record = self.record(model, effort, run)
                (self.out / "runs" / f"q__{model}-{effort}__{run}.json").write_text(json.dumps(record), encoding="utf-8")
        with patch.object(measurement, "DATA", data), \
                patch.object(measurement, "prepare", return_value=self.experiment), \
                contextlib.redirect_stdout(io.StringIO()):
            measurement.cmd_summary(SimpleNamespace(out=self.out))
        return json.loads((self.out / "summary.json").read_text(encoding="utf-8"))

    def test_incomplete_grid_never_recommends_a_model(self):
        report = self.make_summary(False)
        self.assertEqual(report["recommendations"]["R1"]["status"], "incomplete")

    def test_complete_grid_still_requires_semantic_review(self):
        report = self.make_summary(True)
        self.assertEqual(report["recommendations"]["R1"]["status"], "awaiting_semantic_review")
        self.assertTrue(report["recommendations"]["R1"]["eligible_by_cost"])
        self.assertNotIn("selected", report["recommendations"]["R1"])

    def test_duplicate_record_cannot_fill_a_missing_question(self):
        self.make_summary(False)
        original = next((self.out / "runs").glob("*.json"))
        (self.out / "runs/duplicate.json").write_bytes(original.read_bytes())
        with patch.object(measurement, "DATA", self.out / "data.json"), \
                patch.object(measurement, "prepare", return_value=self.experiment):
            with self.assertRaisesRegex(ValueError, "重複"):
                measurement.cmd_summary(SimpleNamespace(out=self.out))


class SemanticSelectionTests(unittest.TestCase):
    def setUp(self):
        import grade_reader_models as semantic
        self.semantic = semantic
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.out = Path(self.temp.name)
        (self.out / "runs").mkdir()
        (self.out / "blind").mkdir()
        self.question = {"id": "q", "class": "R1", "prompt": "alpha", "assertions": [{"claim": "alpha"}], "must_read": []}
        self.experiment = {"fingerprint": "fixed", "spec": {"runs": 1, "data_sha256": "data"}}
        mapping, self.grades = {}, {}
        for i, (model, effort) in enumerate(runtime.COMBOS):
            record = {"id": "q", "class": "R1", "model": model, "effort": effort, "run": 1,
                      "protocol": 3, "exit": 0, "is_error": False, "opened": [], "result": "## 答え\nalpha",
                      "cost_usd": i + 1, "duration_ms": 10, "model_used": f"claude-{model}-5-5",
                      "model_usage": {f"claude-{model}-5-5": {}}, "memory_paths": {}, "cli_version": "test-cli"}
            path = self.out / "runs" / f"{model}-{effort}.json"
            path.write_text(json.dumps(record), encoding="utf-8")
            blind = f"A{i}"
            mapping[blind] = {"file": path.name, "sha256": runtime.digest(path.read_bytes())}
            self.grades[blind] = {"labels": ["supported"], "citation_errors": [], "unsupported_claims": []}
        bundle = {"question": "alpha", "assertions": self.question["assertions"], "pages": {},
                  "answers": [{"id": blind, "answer": "## 答え\nalpha", "opened": []} for blind in mapping]}
        self.semantic.write(self.out / "blind/questions/q.json", bundle)
        self.semantic.write(self.out / "blind/map.json", {"fingerprint": "fixed", "records": mapping,
                            "bundles": {"q.json": runtime.digest((self.out / "blind/questions/q.json").read_bytes())}})

    def finalize(self):
        self.semantic.write(self.out / "semantic-grades.json", self.grades)
        judge_files = {}
        for model in ("judge-one", "judge-two"):
            path = self.out / (model + ".json")
            self.semantic.write(path, {"model": model})
            judge_files[path.name] = runtime.digest(path.read_bytes())
        self.semantic.write(self.out / "semantic-provenance.json", {
            "fingerprint": "fixed", "input_map_sha256": runtime.digest((self.out / "blind/map.json").read_bytes()),
            "final_grades_sha256": runtime.digest((self.out / "semantic-grades.json").read_bytes()),
            "judge_models": ["judge-one", "judge-two"], "files": judge_files})
        with patch.object(runtime, "recorded_experiment", return_value=(self.experiment, {"questions": [self.question]})), \
                contextlib.redirect_stdout(io.StringIO()):
            self.semantic.finalize(self.out)
        return self.semantic.read(self.out / "model-selection.json")

    def test_semantic_omission_cannot_pass_by_word_presence(self):
        self.grades["A0"]["labels"] = ["omitted"]
        result = self.finalize()
        self.assertEqual(result["selection"]["R1"]["selected"], "haiku-medium")

    def test_unread_basis_disqualifies_the_cheapest_model(self):
        self.grades["A0"]["citation_errors"] = ["未読を根拠にしている"]
        result = self.finalize()
        self.assertEqual(result["selection"]["R1"]["selected"], "haiku-medium")

    def test_missing_grade_is_rejected(self):
        del self.grades["A0"]
        with self.assertRaisesRegex(ValueError, "採点が欠け"):
            self.finalize()

    def test_record_change_after_grading_is_rejected(self):
        path = next((self.out / "runs").glob("*.json"))
        path.write_text("{}", encoding="utf-8")
        with self.assertRaisesRegex(ValueError, "回答が変わった"):
            self.finalize()

    def test_missing_input_bundles_are_rejected(self):
        path = self.out / "blind/map.json"
        value = self.semantic.read(path)
        value["bundles"] = {}
        self.semantic.write(path, value)
        with self.assertRaisesRegex(ValueError, "問いの写しが欠け"):
            self.finalize()

    def test_product_table_must_match_the_selection(self):
        decision = {"selection": {cls: {"selected": "impossible-low"} for cls in ("R1", "R2", "R3")}}
        self.semantic.write(self.out / "model-selection.json", decision)
        with self.assertRaisesRegex(ValueError, "製品のモデル表"):
            self.semantic.verify_product(self.out)


class ReconciliationTests(unittest.TestCase):
    def setUp(self):
        import reconcile_reader_grades as reconcile
        self.reconcile = reconcile
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.out = Path(self.temp.name)
        self.reconcile.semantic.write(self.out / "runs/q.json", {"id": "q"})
        identity = {"file": "q.json", "sha256": runtime.digest((self.out / "runs/q.json").read_bytes())}
        self.reconcile.semantic.write(self.out / "blind/map.json", {"records": {"A": identity}})
        self.reconcile.semantic.write(self.out / "second-judge-map.json", {"records": {"S": identity}})
        self.grade = {"labels": ["supported"], "citation_errors": [], "unsupported_claims": [], "notes": ""}
        self.reconcile.semantic.write(self.out / "semantic-grades-opus.json", {"A": self.grade})
        self.reconcile.semantic.write(self.out / "semantic-grades-sol.json", {"S": self.grade})

    def test_clean_agreement_needs_no_adjudication(self):
        result = self.reconcile.compare(self.out)
        self.assertEqual(result["requires_adjudication"], [])
        self.assertEqual(result["agreed_labels"], 1)

    def test_disagreement_and_any_claimed_error_require_adjudication(self):
        for changed in ({"labels": ["omitted"]}, {"unsupported_claims": ["断定が本文にない"]}):
            self.reconcile.semantic.write(self.out / "semantic-grades-sol.json", {"S": {**self.grade, **changed}})
            self.assertEqual(self.reconcile.compare(self.out)["requires_adjudication"], ["A"])

    def test_missing_second_judge_grade_is_rejected(self):
        self.reconcile.semantic.write(self.out / "semantic-grades-sol.json", {})
        with self.assertRaisesRegex(ValueError, "採点者の回答が欠け"):
            self.reconcile.compare(self.out)


class ProductDecisionTests(unittest.TestCase):
    def test_product_defaults_match_the_recorded_model_decision(self):
        import ast
        fixture = json.loads((measurement.DATA.parent / "reader_model_selection.json").read_text(encoding="utf-8"))
        decision_path = measurement.ROOT / fixture["decision_path"]
        self.assertEqual(runtime.digest(decision_path.read_bytes()), fixture["decision_sha256"])
        decision = json.loads(decision_path.read_text(encoding="utf-8"))
        self.assertEqual(decision["fingerprint"], fixture["fingerprint"])
        self.assertEqual(fixture["table"], {cls: decision["selection"][cls]["selected"].rsplit("-", 1)
                                         for cls in ("R1", "R2", "R3")})
        path = measurement.PLUGIN / "skills/info-hive/scripts/wiki_prompt_context.py"
        tree = ast.parse(path.read_text(encoding="utf-8"))
        actual = next(ast.literal_eval(node.value) for node in tree.body if isinstance(node, ast.Assign)
                      and any(isinstance(t, ast.Name) and t.id == "TIERS" for t in node.targets))
        self.assertEqual(actual, {cls: tuple(value) for cls, value in fixture["table"].items()})
        agent = (measurement.PLUGIN / "agents/wiki-reader.md").read_text(encoding="utf-8")
        normalized_agent = __import__("re").sub(r"^(model|effort):[^\n]*\n", "", agent, flags=__import__("re").M)
        # リリース統合で重複したADR番号だけを振り直した。説明のその参照だけを測定時に戻して照合する。
        adr = fixture["reader_description_adr"]
        description = next(line for line in normalized_agent.splitlines() if line.startswith("description: "))
        self.assertEqual(description.count(adr["current"]), 1)
        normalized_agent = normalized_agent.replace(description, description.replace(adr["current"], adr["measured"], 1), 1)
        self.assertEqual(runtime.digest(normalized_agent.encode("utf-8")), fixture["reader_sha256_without_defaults"])
        model, effort = fixture["table"]["R1"]
        self.assertIn(f"\nmodel: {model}\n", agent)
        self.assertIn(f"\neffort: {effort}\n", agent)
        reference = (measurement.PLUGIN / "skills/info-hive/references/prompt-context.md").read_text(encoding="utf-8")
        for cls, (model, effort) in fixture["table"].items():
            row = next(line for line in reference.splitlines() if line.startswith(f"| {cls} |"))
            self.assertIn(f"model={model}", row)
            self.assertIn(f"effort={effort}", row)


if __name__ == "__main__":
    unittest.main()
