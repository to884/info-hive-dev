"""Tests for the single-page scaffolder."""

from __future__ import annotations

import io
import tempfile
import unittest
from contextlib import redirect_stderr, redirect_stdout
from pathlib import Path

from tests import REPO_ROOT

import diataxis_scaffold as scaffold  # noqa: E402


def run(*argv: str) -> tuple[int, str, str]:
    out, err = io.StringIO(), io.StringIO()
    with redirect_stdout(out), redirect_stderr(err):
        try:
            code = scaffold.main(list(argv))
        except SystemExit as exc:  # argparse errors
            code = int(exc.code or 0)
    return code, out.getvalue(), err.getvalue()


class SlugifyTest(unittest.TestCase):
    def test_ascii_title(self):
        self.assertEqual(scaffold.slugify("How to Rotate API Keys"), "how-to-rotate-api-keys")

    def test_unicode_letters_are_preserved(self):
        self.assertEqual(scaffold.slugify("ドキュメント 参照"), "ドキュメント-参照")
        self.assertEqual(scaffold.slugify("Añadir configuración"), "añadir-configuración")

    def test_unusable_title_returns_empty_not_untitled(self):
        self.assertEqual(scaffold.slugify("!!! ???"), "")
        self.assertEqual(scaffold.slugify("   "), "")


class YamlQuotingTest(unittest.TestCase):
    def test_quotes_and_backslashes_are_escaped(self):
        self.assertEqual(scaffold.yaml_double_quote('a "b" c'), '"a \\"b\\" c"')
        self.assertEqual(scaffold.yaml_double_quote("a\\b"), '"a\\\\b"')

    def test_rendered_frontmatter_is_parseable(self):
        template = (REPO_ROOT / "assets" / "templates" / "how-to-guide.md").read_text(encoding="utf-8")
        rendered = scaffold.render_template(template, 'Rotate the "primary" key', "how-to")
        line = next(l for l in rendered.splitlines() if l.startswith("title:"))
        value = line.split(":", 1)[1].strip()
        self.assertTrue(value.startswith('"') and value.endswith('"'))
        # A naive YAML double-quoted scalar unescape must round-trip.
        self.assertEqual(value[1:-1].replace('\\"', '"').replace("\\\\", "\\"), 'Rotate the "primary" key')


class CliTest(unittest.TestCase):
    def test_empty_title_is_rejected(self):
        with tempfile.TemporaryDirectory() as tmp:
            code, _, err = run("how-to", "", "--out-dir", tmp)
            self.assertNotEqual(code, 0)
            self.assertIn("title must not be empty", err)

    def test_whitespace_title_is_rejected(self):
        with tempfile.TemporaryDirectory() as tmp:
            code, _, _ = run("how-to", "   ", "--out-dir", tmp)
            self.assertNotEqual(code, 0)

    def test_unusable_title_asks_for_filename(self):
        with tempfile.TemporaryDirectory() as tmp:
            code, _, err = run("how-to", "!!!", "--out-dir", tmp)
            self.assertEqual(code, 2)
            self.assertIn("--filename", err)

    def test_how_to_heading_is_built_safely(self):
        with tempfile.TemporaryDirectory() as tmp:
            code, out, _ = run("how-to", "Rotate a signing secret", "--out-dir", tmp)
            self.assertEqual(code, 0)
            text = Path(out.strip()).read_text(encoding="utf-8")
            self.assertIn("# How to rotate a signing secret", text)

    def test_existing_how_to_title_is_not_doubled(self):
        with tempfile.TemporaryDirectory() as tmp:
            _, out, _ = run("how-to", "How to rotate a secret", "--out-dir", tmp)
            text = Path(out.strip()).read_text(encoding="utf-8")
            self.assertIn("# How to rotate a secret", text)
            self.assertNotIn("How to how to", text)

    def test_refuses_to_overwrite_without_force(self):
        with tempfile.TemporaryDirectory() as tmp:
            run("reference", "Queue reference", "--out-dir", tmp)
            code, _, err = run("reference", "Queue reference", "--out-dir", tmp)
            self.assertEqual(code, 1)
            self.assertIn("Refusing to overwrite", err)
            code, _, _ = run("reference", "Queue reference", "--out-dir", tmp, "--force")
            self.assertEqual(code, 0)

    def test_every_type_scaffolds(self):
        with tempfile.TemporaryDirectory() as tmp:
            for doc_type in sorted(scaffold.TEMPLATE_FILES):
                with self.subTest(doc_type=doc_type):
                    code, out, err = run(doc_type, f"Example {doc_type}", "--out-dir", tmp)
                    self.assertEqual(code, 0, err)
                    self.assertTrue(Path(out.strip()).exists())

    def test_doc_type_is_not_emitted_by_default(self):
        """The skill must not push a `doc_type:` convention onto a project."""
        with tempfile.TemporaryDirectory() as tmp:
            for doc_type in sorted(scaffold.TEMPLATE_FILES):
                with self.subTest(doc_type=doc_type):
                    _, out, err = run(doc_type, f"Example {doc_type}", "--out-dir", tmp)
                    self.assertNotIn("doc_type:", Path(out.strip()).read_text(encoding="utf-8"), err)

    def test_doc_type_is_emitted_on_request(self):
        with tempfile.TemporaryDirectory() as tmp:
            _, out, _ = run("how-to", "Rotate a secret", "--out-dir", tmp, "--with-doc-type")
            text = Path(out.strip()).read_text(encoding="utf-8")
            self.assertIn("doc_type: how-to", text)
            self.assertLess(text.index("doc_type:"), text.index("# How to"))

    def test_templates_declare_no_doc_type(self):
        for filename in sorted(set(scaffold.TEMPLATE_FILES.values())):
            with self.subTest(template=filename):
                text = (REPO_ROOT / "assets" / "templates" / filename).read_text(encoding="utf-8")
                self.assertNotIn("\ndoc_type:", text)

    def test_every_scaffold_type_with_frontmatter_has_a_doc_type_value(self):
        for doc_type, filename in sorted(scaffold.TEMPLATE_FILES.items()):
            template = (REPO_ROOT / "assets" / "templates" / filename).read_text(encoding="utf-8")
            has_frontmatter = template.startswith("---")
            with self.subTest(doc_type=doc_type):
                self.assertEqual(has_frontmatter, doc_type in scaffold.DOC_TYPE_VALUES)

    def test_templates_carry_an_authoring_contract(self):
        for filename in sorted(set(scaffold.TEMPLATE_FILES.values())):
            with self.subTest(template=filename):
                text = (REPO_ROOT / "assets" / "templates" / filename).read_text(encoding="utf-8")
                self.assertIn("AUTHORING CONTRACT", text)

