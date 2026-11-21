"""Regression tests for the Diátaxis evidence collector."""

from __future__ import annotations

import io
import json
import unittest
from contextlib import redirect_stdout
from pathlib import Path

from tests import AUDIT_CORPUS as FIXTURES, REPO_ROOT

import diataxis_audit as audit  # noqa: E402


def run_audit(*argv: str) -> tuple[int, str]:
    buffer = io.StringIO()
    with redirect_stdout(buffer):
        code = audit.main(list(argv))
    return code, buffer.getvalue()


class LabeledCorpusTest(unittest.TestCase):
    """A small labeled corpus: the fixtures must keep classifying as labeled."""

    EXPECTED = {
        "pure-tutorial.md": ("clear", "tutorial"),
        "pure-how-to.md": ("clear", "how-to"),
        "pure-reference.md": ("clear", "reference"),
        "pure-explanation.md": ("clear", "explanation"),
        "intentionally-mixed.md": ("ambiguous", None),
        "unknown-purpose.md": ("insufficient-context", None),
    }

    def test_fixture_corpus(self):
        for name, (status, mode) in self.EXPECTED.items():
            with self.subTest(fixture=name):
                result = audit.audit_file(FIXTURES / name)
                self.assertEqual(result.classification_status, status)
                if mode is not None:
                    self.assertEqual(result.candidate_modes[0], mode)

    def test_mixed_page_names_two_candidates(self):
        result = audit.audit_file(FIXTURES / "intentionally-mixed.md")
        self.assertEqual(len(result.candidate_modes), 2)
        self.assertIn("strong-competing-user-needs", {r["rule"] for r in result.risks})

    def test_unknown_page_reports_missing_context(self):
        result = audit.audit_file(FIXTURES / "unknown-purpose.md")
        self.assertEqual(result.candidate_modes, [])
        self.assertTrue(result.missing_context)


class FrontmatterTest(unittest.TestCase):
    def test_leading_frontmatter_is_parsed(self):
        fm, body = audit.split_frontmatter('---\ntitle: "A page"\ndoc_type: reference\n---\n\n# A page\n')
        self.assertEqual(fm["title"], "A page")
        self.assertEqual(fm["doc_type"], "reference")
        self.assertNotIn("title:", body)

    def test_key_value_line_in_body_is_not_frontmatter(self):
        fm, body = audit.split_frontmatter("# A page\n\nretention: 24h is the default.\n")
        self.assertEqual(fm, {})
        self.assertIn("retention: 24h", body)

    def test_declared_doc_type_is_reported(self, ):
        result = audit.audit_file(FIXTURES / "pure-reference.md")
        self.assertEqual(result.declared_doc_type, "reference")

    def test_declared_type_conflict_is_flagged(self):
        with TempDoc('---\ndoc_type: tutorial\n---\n\n' + (FIXTURES / "pure-reference.md").read_text(encoding="utf-8").split("---", 2)[2]) as path:
            result = audit.audit_file(path)
            self.assertIn("declared-type-conflicts-with-signals", {r["rule"] for r in result.risks})


class TempDoc:
    """Write a temporary Markdown document and yield its path."""

    def __init__(self, text: str, suffix: str = ".md"):
        self.text = text
        self.suffix = suffix

    def __enter__(self) -> Path:
        import tempfile

        self._dir = tempfile.TemporaryDirectory()
        path = Path(self._dir.name) / f"doc{self.suffix}"
        path.write_text(self.text, encoding="utf-8")
        return path

    def __exit__(self, *exc):
        self._dir.cleanup()
        return False


class FenceTest(unittest.TestCase):
    BODY = "# Title\n\nProse before.\n\n{fence}bash\nrationale trade-off because architecture\n{fence}\n\nProse after.\n"

    def test_backtick_fence_content_is_excluded_from_body(self):
        with TempDoc(self.BODY.format(fence="```")) as path:
            body = audit.strip_code(path.read_text(encoding="utf-8"))
            self.assertNotIn("rationale trade-off", body)

    def test_tilde_fence_content_is_excluded_from_body(self):
        with TempDoc(self.BODY.format(fence="~~~")) as path:
            body = audit.strip_code(path.read_text(encoding="utf-8"))
            self.assertNotIn("rationale trade-off", body)

    def test_indented_code_is_excluded_from_body(self):
        body = audit.strip_code("# Title\n\nProse.\n\n    rationale trade-off\n\nMore prose.\n")
        self.assertNotIn("rationale trade-off", body)

    def test_code_blocks_are_counted(self):
        with TempDoc(self.BODY.format(fence="~~~")) as path:
            result = audit.audit_file(path)
            self.assertGreaterEqual(result.structural_signals["fenced_code_blocks"], 1)


class MdxAndRstTest(unittest.TestCase):
    def test_mdx_components_do_not_become_prose(self):
        text = 'import Foo from "./foo"\n\n# Options\n\n<Callout type="warn">Careful</Callout>\n\nSome text.\n'
        with TempDoc(text, suffix=".mdx") as path:
            result = audit.audit_file(path)
            self.assertEqual(result.title, "Options")

    def test_rst_underlined_heading_becomes_title(self):
        text = "Queue reference\n===============\n\nParameters\n----------\n\nA field with a default.\n"
        with TempDoc(text, suffix=".rst") as path:
            result = audit.audit_file(path)
            self.assertEqual(result.title, "Queue reference")
            self.assertIn("parameters", audit.extract_headings(text, rst=True))

    def test_rst_directive_body_is_excluded(self):
        text = "Title\n=====\n\n.. code-block:: bash\n\n   rationale trade-off\n\nProse.\n"
        body = audit.strip_code(text, rst=True)
        self.assertNotIn("rationale trade-off", body)


class TitleTest(unittest.TestCase):
    def test_unicode_title_survives(self):
        with TempDoc("# ドキュメントの参照\n\nSome content about defaults and parameters.\n") as path:
            result = audit.audit_file(path)
            self.assertEqual(result.title, "ドキュメントの参照")

    def test_frontmatter_title_wins_over_h1(self):
        with TempDoc('---\ntitle: "Declared title"\n---\n\n# Body heading\n\nText.\n') as path:
            self.assertEqual(audit.audit_file(path).title, "Declared title")

    def test_missing_title_falls_back_to_filename(self):
        with TempDoc("Just prose, no heading at all.\n") as path:
            self.assertEqual(audit.audit_file(path).title, "Doc")


class SignalsTest(unittest.TestCase):
    def test_unresolved_placeholders_are_detected(self):
        template = REPO_ROOT / "assets" / "templates" / "how-to-guide.md"
        result = audit.audit_file(template)
        self.assertGreater(result.structural_signals["unresolved_placeholders"], 0)
        self.assertIn("unresolved-placeholders", {r["rule"] for r in result.risks})

    def test_risky_command_without_rollback_is_flagged(self):
        text = "# How to clean up\n\nRun this:\n\n```bash\nrm -rf /var/lib/demo\n```\n\nDone.\n"
        with TempDoc(text) as path:
            result = audit.audit_file(path)
            self.assertIn("risky-commands-without-rollback", {r["rule"] for r in result.risks})

    def test_signal_separation_is_not_called_confidence(self):
        result = audit.audit_file(FIXTURES / "pure-reference.md")
        self.assertFalse(hasattr(result, "confidence"))
        self.assertIsInstance(result.signal_separation, float)

    def test_status_label_describes_the_margin_not_a_confidence(self):
        result = audit.audit_file(FIXTURES / "pure-reference.md")
        label = audit.status_label(result)
        self.assertIn("reference", label)
        self.assertIn("margin", label)
        for word in ("strong", "weak", "confidence", "confident"):
            self.assertNotIn(word, label.lower())

    def test_ambiguity_evidence_matches_the_threshold_constant(self):
        result = audit.audit_file(FIXTURES / "intentionally-mixed.md")
        evidence = next(r["evidence"] for r in result.risks if r["rule"] == "strong-competing-user-needs")
        self.assertIn(f"within {audit.AMBIGUITY_GAP_PERCENT}%", evidence)
        self.assertEqual(audit.AMBIGUITY_GAP_PERCENT, round((1.0 - audit.AMBIGUITY_RATIO) * 100))


class CliTest(unittest.TestCase):
    def test_json_output_shape_is_stable(self):
        code, out = run_audit(str(FIXTURES), "--format", "json")
        self.assertEqual(code, 0)
        payload = json.loads(out)
        self.assertEqual(payload["schema_version"], audit.SCHEMA_VERSION)
        first = payload["results"][0]
        for key in (
            "schema_version", "path", "title", "declared_doc_type", "classification_status",
            "candidate_modes", "mode_hypotheses", "signal_separation", "scores",
            "structural_signals", "risks", "missing_context", "suggestions",
        ):
            self.assertIn(key, first)
        for risk in first["risks"]:
            self.assertEqual(set(risk), {"rule", "category", "evidence"})
            self.assertIn(risk["category"], {audit.DEFECT, audit.PURITY})

    def test_max_files_is_deterministic(self):
        _, first = run_audit(str(FIXTURES), "--format", "json", "--max-files", "3")
        _, second = run_audit(str(FIXTURES), "--format", "json", "--max-files", "3")
        self.assertEqual(first, second)
        paths = [r["path"] for r in json.loads(first)["results"]]
        self.assertEqual(paths, sorted(paths))
        self.assertEqual(len(paths), 3)

    def test_include_and_exclude_filters(self):
        _, out = run_audit(str(FIXTURES), "--format", "json", "--include", "pure-*.md")
        paths = [r["path"] for r in json.loads(out)["results"]]
        self.assertTrue(all(p.startswith("pure-") for p in paths))
        _, out = run_audit(str(FIXTURES), "--format", "json", "--exclude", "pure-*.md")
        paths = [r["path"] for r in json.loads(out)["results"]]
        self.assertFalse(any(p.startswith("pure-") for p in paths))

    def test_ignore_generated(self):
        import tempfile

        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            (root / "generated.md").write_text("<!-- Automatically generated. Do not edit. -->\n\n# Gen\n\nText.\n", encoding="utf-8")
            (root / "handwritten.md").write_text("# Hand\n\nText.\n", encoding="utf-8")
            _, out = run_audit(str(root), "--format", "json", "--ignore-generated")
            paths = [r["path"] for r in json.loads(out)["results"]]
            self.assertEqual(paths, ["handwritten.md"])

    def test_fail_on_placeholders(self):
        code, _ = run_audit(str(REPO_ROOT / "assets" / "templates"), "--format", "json", "--fail-on", "placeholders")
        self.assertEqual(code, 1)
        code, _ = run_audit(str(FIXTURES / "pure-reference.md"), "--format", "json", "--fail-on", "placeholders")
        self.assertEqual(code, 0)

    def test_fail_on_risks_ignores_mode_purity_risks(self):
        """`--fail-on risks` must not become a mode-purity compliance gate."""
        # A reference page carrying a procedure is a purity risk and nothing else.
        text = (
            '---\ntitle: "Queue settings"\n---\n\n# Queue settings\n\n'
            "| Field | Type | Default |\n|---|---|---|\n| retention | duration | 24h |\n\n"
            "To change it:\n\n1. Open settings.\n2. Edit the field.\n"
            "3. Confirm the change.\n4. Reload the service.\n"
        )
        with TempDoc(text) as path:
            result = audit.audit_file(path)
            categories = {r["category"] for r in result.risks}
            self.assertEqual(categories, {audit.PURITY}, result.risks)
            code, _ = run_audit(str(path), "--format", "json", "--fail-on", "risks")
            self.assertEqual(code, 0)

    def test_fail_on_risks_still_catches_defects(self):
        text = "# How to clean up\n\nRun this:\n\n```bash\nrm -rf /var/lib/demo\n```\n\nDone.\n"
        with TempDoc(text) as path:
            code, _ = run_audit(str(path), "--format", "json", "--fail-on", "risks")
            self.assertEqual(code, 1)

    def test_missing_path_returns_two(self):
        buffer = io.StringIO()
        with redirect_stdout(buffer):
            code = audit.main([str(REPO_ROOT / "does-not-exist")])
        self.assertEqual(code, 2)

    def test_custom_pattern_set(self):
        import tempfile

        patterns = {"title": {"tutorial": [["\\btutoriel\\b", 9]], "how-to": [], "reference": [], "explanation": []}}
        with tempfile.TemporaryDirectory() as tmp:
            pattern_file = Path(tmp) / "patterns.json"
            pattern_file.write_text(json.dumps(patterns), encoding="utf-8")
            loaded = audit.PatternSet.load(pattern_file)
            self.assertEqual(loaded.title["tutorial"], [("\\btutoriel\\b", 9)])
            self.assertEqual(loaded.body, audit.DEFAULT_BODY_PATTERNS)

