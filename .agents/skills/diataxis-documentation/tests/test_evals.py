"""Tests that the eval suite itself is well formed."""

from __future__ import annotations

import json
import unittest

from tests import REPO_ROOT

EVALS = REPO_ROOT / "evals"

GRADE_DIMENSIONS = {
    "outcome", "process", "mode", "functional_quality",
    "repository_fit", "safety", "efficiency",
}


class TriggerQueriesTest(unittest.TestCase):
    def setUp(self):
        self.data = json.loads((EVALS / "trigger-queries.json").read_text(encoding="utf-8"))

    def test_shape(self):
        self.assertIn("queries", self.data)
        for entry in self.data["queries"]:
            self.assertEqual(set(entry), {"query", "should_trigger", "why"})
            self.assertIsInstance(entry["should_trigger"], bool)
            self.assertTrue(entry["query"].strip())

    def test_has_both_polarities_and_enough_cases(self):
        positives = [q for q in self.data["queries"] if q["should_trigger"]]
        negatives = [q for q in self.data["queries"] if not q["should_trigger"]]
        self.assertGreaterEqual(len(self.data["queries"]), 20)
        self.assertGreaterEqual(len(positives), 8)
        self.assertGreaterEqual(len(negatives), 5)

    def test_queries_are_unique(self):
        queries = [q["query"] for q in self.data["queries"]]
        self.assertEqual(len(queries), len(set(queries)))


class BehaviorCasesTest(unittest.TestCase):
    def setUp(self):
        lines = (EVALS / "behavior-cases.jsonl").read_text(encoding="utf-8").splitlines()
        self.cases = [json.loads(line) for line in lines if line.strip()]

    def test_shape(self):
        required = {"id", "name", "prompt", "fixtures", "expected_mode", "must", "must_not", "grades"}
        for case in self.cases:
            with self.subTest(case=case.get("id")):
                self.assertTrue(required.issubset(case))
                self.assertTrue(case["must"])
                self.assertTrue(case["grades"])
                self.assertTrue(set(case["grades"]).issubset(GRADE_DIMENSIONS))

    def test_ids_are_unique(self):
        ids = [c["id"] for c in self.cases]
        self.assertEqual(len(ids), len(set(ids)))

    def test_referenced_fixtures_exist(self):
        for case in self.cases:
            for fixture in case["fixtures"]:
                with self.subTest(case=case["id"], fixture=fixture):
                    self.assertTrue((EVALS / "fixtures" / fixture).exists(), fixture)

    def test_covers_the_required_scenarios(self):
        names = {c["name"] for c in self.cases}
        for expected in (
            "first-success-tutorial",
            "production-how-to-from-issue",
            "api-reference-from-schema-and-code",
            "cli-reference-from-parser-and-help",
            "explanation-from-adr",
            "repair-mixed-getting-started",
            "audit-tree-with-coverage-gaps",
            "insufficient-source-material",
            "project-style-conflicts-with-fallback",
            "readme-as-composite",
            "risky-migration-instructions",
            "should-not-trigger-copyediting",
        ):
            self.assertIn(expected, names)

    def test_rubric_documents_every_grade_dimension(self):
        rubric = (EVALS / "rubric.md").read_text(encoding="utf-8").lower()
        for dimension in sorted(GRADE_DIMENSIONS):
            self.assertIn(dimension.replace("_", " "), rubric)

    def test_rubric_requires_a_skill_off_baseline(self):
        rubric = (EVALS / "rubric.md").read_text(encoding="utf-8")
        self.assertIn("skill-off", rubric.lower())

