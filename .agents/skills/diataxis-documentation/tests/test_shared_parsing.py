"""Drift guard for logic duplicated across the two distributed scripts.

`diataxis_audit.py` and `docs_health.py` are distributed as standalone files —
a user can copy either one on its own — so they cannot import a shared module.
The cost of that guarantee is duplicated frontmatter parsing, file discovery,
and code-block detection, and duplication drifts silently. These tests are the
thing that stops it: they pin the copies to identical behaviour on a shared
table of cases, so a change to one that is not made to the other fails here.

`validate_package.py` is repository-only and parses only `SKILL.md`, so it is
held to the weaker contract of agreeing on which keys exist.
"""

from __future__ import annotations

import unittest

from tests import REPO_ROOT

import diataxis_audit as audit  # noqa: E402
import docs_health as health  # noqa: E402
import validate_package as validate  # noqa: E402

# (label, document text). Each case exercises a decision the parsers make.
FRONTMATTER_CASES = [
    ("dash fence", '---\ntitle: "A page"\ndoc_type: reference\n---\n\n# A page\n'),
    ("plus fence", '+++\ntitle = ignored\ntitle: "A page"\n+++\n\n# A page\n'),
    ("no frontmatter", "# A page\n\nretention: 24h is the default.\n"),
    ("leading blank lines", '\n\n---\ntitle: "A page"\n---\n\nBody.\n'),
    ("unterminated fence", '---\ntitle: "A page"\n\n# A page\n'),
    ("quoted values", "---\nname: 'single'\nother: \"double\"\n---\n\nBody.\n"),
    ("dotted key", "---\nsite.title: Value\n---\n\nBody.\n"),
    ("empty document", ""),
    ("fence-only document", "---\n---\n"),
    ("value containing a colon", "---\ntitle: A: B\n---\n\nBody.\n"),
]


class FrontmatterParserAgreementTest(unittest.TestCase):
    def test_distributed_parsers_agree(self):
        for label, text in FRONTMATTER_CASES:
            with self.subTest(case=label):
                audit_fields, audit_body = audit.split_frontmatter(text)
                health_fields, health_body, _offset = health.split_frontmatter(text)
                self.assertEqual(audit_fields, health_fields)
                self.assertEqual(audit_body, health_body)

    def test_body_offset_points_at_the_body(self):
        for label, text in FRONTMATTER_CASES:
            with self.subTest(case=label):
                _fields, body, offset = health.split_frontmatter(text)
                if offset:
                    self.assertEqual(text.splitlines()[offset:], body.splitlines())

    def test_validate_package_agrees_on_keys(self):
        for label, text in FRONTMATTER_CASES:
            if not text.startswith(("---", "\n")):
                continue
            with self.subTest(case=label):
                audit_fields, _ = audit.split_frontmatter(text)
                validate_fields, _ = validate.read_frontmatter(text)
                self.assertEqual(set(validate_fields), set(audit_fields))


class FileDiscoveryAgreementTest(unittest.TestCase):
    def test_ignore_sets_match(self):
        self.assertEqual(audit.IGNORE_DIRS, health.IGNORE_DIRS)

    def test_health_scans_a_documented_subset_of_the_audit_extensions(self):
        # The extension sets differ on purpose: docs_health resolves Markdown
        # links and navigation, so it only handles Markdown. Anything it does
        # scan, the auditor must scan too.
        self.assertTrue(health.DOC_EXTENSIONS < audit.DOC_EXTENSIONS)

    def test_read_text_agrees_on_every_shipped_document(self):
        for path in sorted(REPO_ROOT.glob("references/*.md")):
            with self.subTest(path=path.name):
                self.assertEqual(audit.read_text(path), health.read_text(path))


class CodeBlockAgreementTest(unittest.TestCase):
    """`strip_code` removes fenced lines; `code_line_flags` marks them.

    They are written differently because they answer different questions, but
    they must agree about which fenced lines are code.
    """

    CASES = [
        "# T\n\nProse.\n\n```bash\nsecret-token\n```\n\nAfter.\n",
        "# T\n\nProse.\n\n~~~bash\nsecret-token\n~~~\n\nAfter.\n",
        "# T\n\n````md\n```\nsecret-token\n```\n````\n\nAfter.\n",
        "# T\n\nProse.\n\n```\nsecret-token\n",
    ]

    def test_fenced_content_is_code_to_both(self):
        for text in self.CASES:
            with self.subTest(text=text.splitlines()[2:4]):
                stripped = audit.strip_code(text)
                flags, _unclosed = health.code_line_flags(text.splitlines())
                flagged = {line for line, is_code in zip(text.splitlines(), flags) if is_code}
                self.assertNotIn("secret-token", stripped)
                self.assertIn("secret-token", flagged)
                if "After." in text:
                    self.assertIn("After.", stripped.splitlines())


class FrontmatterAllowListTest(unittest.TestCase):
    """The validator's allow-list must be exactly the documented standard set."""

    def test_allow_list_matches_agents_md(self):
        text = (REPO_ROOT / "AGENTS.md").read_text(encoding="utf-8")
        sentence = text.split("must stick to standard fields (", 1)[1].split(")", 1)[0]
        documented = set(field.strip().strip("`") for field in sentence.split(","))
        self.assertEqual(validate.ALLOWED_FRONTMATTER, documented)

    def test_vendor_specific_keys_are_rejected(self):
        for key in ("allowed-tools", "version", "model"):
            with self.subTest(key=key):
                self.assertNotIn(key, validate.ALLOWED_FRONTMATTER)
