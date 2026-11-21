"""Tests for package invariants: manifest, pointers, docs, and agent instructions."""

from __future__ import annotations

import io
import re
import unittest
from contextlib import redirect_stderr, redirect_stdout
from pathlib import Path

from tests import REPO_ROOT

import diataxis_audit  # noqa: E402
import diataxis_scaffold  # noqa: E402
import update_manifest  # noqa: E402
import validate_package  # noqa: E402


class ValidationTest(unittest.TestCase):
    def test_package_validates(self):
        problems = validate_package.check(REPO_ROOT)
        self.assertEqual(problems, [], "\n".join(problems))

    def test_manifest_is_current(self):
        listed = (REPO_ROOT / "manifest.txt").read_text(encoding="utf-8").split()
        self.assertEqual(listed, update_manifest.compute_manifest(REPO_ROOT))

    def test_manifest_excludes_repository_only_files(self):
        listed = set((REPO_ROOT / "manifest.txt").read_text(encoding="utf-8").split())
        for entry in ("AGENTS.md", "CLAUDE.md", "scripts/validate_package.py", "scripts/update_manifest.py"):
            self.assertNotIn(entry, listed)
        self.assertFalse(any(e.startswith(("tests/", "evals/", ".github/")) for e in listed))

    def test_manifest_includes_every_reference_and_template(self):
        listed = set((REPO_ROOT / "manifest.txt").read_text(encoding="utf-8").split())
        for path in sorted((REPO_ROOT / "references").glob("*.md")):
            self.assertIn(f"references/{path.name}", listed)
        for path in sorted((REPO_ROOT / "assets" / "templates").glob("*.md")):
            self.assertIn(f"assets/templates/{path.name}", listed)


class SkillDocumentTest(unittest.TestCase):
    def setUp(self):
        self.text = (REPO_ROOT / "SKILL.md").read_text(encoding="utf-8")

    def test_every_referenced_path_exists(self):
        targets = set(re.findall(r"`((?:references|assets|scripts)/[A-Za-z0-9_./-]+)`", self.text))
        self.assertTrue(targets)
        for target in sorted(targets):
            with self.subTest(target=target):
                self.assertTrue((REPO_ROOT / target).exists(), target)

    def test_every_reference_file_has_a_loading_condition(self):
        for path in sorted((REPO_ROOT / "references").glob("*.md")):
            with self.subTest(reference=path.name):
                self.assertIn(f"`references/{path.name}`", self.text)

    def test_description_states_when_to_use(self):
        description = re.search(r"description:\s*>-\n((?:\s{2,}.*\n)+)", self.text).group(1)
        self.assertIn("Use this skill when", description)
        self.assertIn("Do not use it", description)

    def test_frontmatter_within_size_limit(self):
        block = self.text.split("---", 2)[1]
        self.assertLessEqual(len(block), 1024)


class ReadmeTest(unittest.TestCase):
    def setUp(self):
        self.text = (REPO_ROOT / "README.md").read_text(encoding="utf-8")

    def _flags_for(self, module) -> set[str]:
        """Every option string the module's own parser defines.

        Each script exposes `build_parser()` precisely so this can ask directly
        instead of intercepting argparse.
        """
        parser = module.build_parser()
        flags: set[str] = set()
        for action in parser._actions:
            flags.update(action.option_strings)
        return flags

    def test_documented_audit_flags_exist(self):
        flags = self._flags_for(diataxis_audit)
        for flag in re.findall(r"`(--[a-z-]+)`", self.text.split("### `diataxis_audit.py`")[1].split("###")[0]):
            with self.subTest(flag=flag):
                self.assertIn(flag, flags)

    def test_documented_scaffold_flags_exist(self):
        flags = self._flags_for(diataxis_scaffold)
        section = self.text.split("### `diataxis_scaffold.py`")[1].split("## ")[0]
        for flag in re.findall(r"`(--[a-z-]+)`", section):
            with self.subTest(flag=flag):
                self.assertIn(flag, flags)

    def test_documented_scaffold_types_match_the_script(self):
        section = self.text.split("### `diataxis_scaffold.py`")[1].split("## ")[0]
        documented = set(re.findall(r"`([a-z][a-z-]+)`", section))
        for doc_type in diataxis_scaffold.TEMPLATE_FILES:
            with self.subTest(doc_type=doc_type):
                self.assertIn(doc_type, documented)


class DistributedPathsTest(unittest.TestCase):
    """Every repository path the README tells a reader to run must be shipped.

    The README is read by people who installed the package from `manifest.txt`,
    not only by people who cloned the repository, so a command pointing at
    `tests/` would leave them at a missing path.
    """

    def setUp(self):
        self.text = (REPO_ROOT / "README.md").read_text(encoding="utf-8")
        self.manifest = (REPO_ROOT / "manifest.txt").read_text(encoding="utf-8").split()

    def _is_distributed(self, target: str) -> bool:
        return any(entry == target or entry.startswith(target.rstrip("/") + "/") for entry in self.manifest)

    def test_readme_script_invocations_use_distributed_paths(self):
        pattern = re.compile(r"python3 (scripts/\w+\.py)\s+([\w./-]+)")
        targets = set(pattern.findall(self.text))
        self.assertTrue(targets, "no script invocations found in the README")
        checked = 0
        for script, target in sorted(targets):
            # `docs/` and friends stand for the reader's own tree. Only a path
            # that actually exists here is a claim about this package.
            if not (REPO_ROOT / target).exists():
                continue
            checked += 1
            with self.subTest(command=f"{script} {target}"):
                self.assertTrue(self._is_distributed(target),
                                f"README runs against {target}, which manifest.txt does not distribute")
        self.assertTrue(checked, "the README no longer runs any script against a path in this package")

    def test_labeled_corpus_ships(self):
        for name in ("pure-tutorial", "pure-how-to", "pure-reference", "pure-explanation",
                     "intentionally-mixed", "unknown-purpose"):
            with self.subTest(page=name):
                self.assertIn(f"assets/examples/audit-corpus/{name}.md", self.manifest)


class AgentInstructionsTest(unittest.TestCase):
    """AGENTS.md is canonical; CLAUDE.md must point at it rather than drift."""

    def test_claude_md_defers_to_agents_md(self):
        text = (REPO_ROOT / "CLAUDE.md").read_text(encoding="utf-8")
        self.assertIn("AGENTS.md", text)
        self.assertLess(len(text.split()), 200, "CLAUDE.md should stay a pointer, not a second copy")

    def test_agents_md_names_all_three_runtimes(self):
        text = (REPO_ROOT / "AGENTS.md").read_text(encoding="utf-8")
        for runtime in ("Claude Code", "Codex", "Pi"):
            self.assertIn(runtime, text)

