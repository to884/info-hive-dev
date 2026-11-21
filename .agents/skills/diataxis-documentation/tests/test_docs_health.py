"""Tests for the objective document-health checks."""

from __future__ import annotations

import io
import json
import tempfile
import unittest
from contextlib import redirect_stdout
from pathlib import Path

from tests import REPO_ROOT

import docs_health  # noqa: E402


class Tree:
    def __init__(self, files: dict[str, str]):
        self.files = files

    def __enter__(self) -> Path:
        self._dir = tempfile.TemporaryDirectory()
        root = Path(self._dir.name)
        for name, text in self.files.items():
            path = root / name
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_text(text, encoding="utf-8")
        return root

    def __exit__(self, *exc):
        self._dir.cleanup()
        return False


def checks(root: Path) -> dict[str, int]:
    findings, _ = docs_health.run(root)
    counts: dict[str, int] = {}
    for finding in findings:
        counts[finding.check] = counts.get(finding.check, 0) + 1
    return counts


class ChecksTest(unittest.TestCase):
    def test_broken_link_and_anchor(self):
        files = {
            "index.md": "# Index\n\n[Real](other.md) and [Gone](missing.md) and [Anchor](other.md#nope)\n",
            "other.md": "# Other\n\n## Present\n\nText.\n",
        }
        with Tree(files) as root:
            counts = checks(root)
            self.assertEqual(counts.get("broken-link"), 1)
            self.assertEqual(counts.get("broken-anchor"), 1)

    def test_orphan_page(self):
        with Tree({"index.md": "# Index\n\nNo links.\n", "lonely.md": "# Lonely\n\nText.\n"}) as root:
            self.assertEqual(checks(root).get("orphan-page"), 1)

    def test_duplicate_title(self):
        files = {
            "index.md": "# Index\n\n[a](a.md) [b](b.md)\n",
            "a.md": "# Same title\n\nText.\n",
            "b.md": "# Same title\n\nText.\n",
        }
        with Tree(files) as root:
            self.assertEqual(checks(root).get("duplicate-title"), 1)

    def test_missing_h1(self):
        with Tree({"index.md": "Just prose with no heading.\n"}) as root:
            self.assertEqual(checks(root).get("missing-h1"), 1)

    def test_frontmatter_title_satisfies_h1_check(self):
        with Tree({"index.md": '---\ntitle: "A page"\n---\n\nProse.\n'}) as root:
            self.assertIsNone(checks(root).get("missing-h1"))

    def test_unresolved_placeholder(self):
        with Tree({"index.md": "# Page\n\nSet <your-value> here. TODO: finish.\n"}) as root:
            self.assertGreaterEqual(checks(root).get("unresolved-placeholder", 0), 1)

    def test_placeholder_inside_code_block_is_ignored(self):
        with Tree({"index.md": "# Page\n\n```bash\nexport KEY=<your-key>\n```\n"}) as root:
            self.assertIsNone(checks(root).get("unresolved-placeholder"))

    def test_malformed_fence(self):
        with Tree({"index.md": "# Page\n\n```bash\nnever closed\n"}) as root:
            self.assertEqual(checks(root).get("malformed-fence"), 1)

    def test_empty_section(self):
        with Tree({"index.md": "# Page\n\n## Empty\n\n## Full\n\nText.\n"}) as root:
            self.assertEqual(checks(root).get("empty-section"), 1)

    def test_container_heading_is_not_an_empty_section(self):
        with Tree({"index.md": "# Page\n\n## Container\n\n### Child\n\nText.\n"}) as root:
            self.assertIsNone(checks(root).get("empty-section"))

    def test_image_without_alt(self):
        with Tree({"index.md": "# Page\n\n![](diagram.png)\n\n<img src=\"x.png\">\n"}) as root:
            self.assertEqual(checks(root).get("image-without-alt"), 2)

    def test_vague_link_text(self):
        files = {"index.md": "# Page\n\nSee [here](other.md) and [Other page](other.md).\n",
                 "other.md": "# Other page\n\nText.\n"}
        with Tree(files) as root:
            self.assertEqual(checks(root).get("vague-link-text"), 1)

    def test_nav_target_missing(self):
        files = {"mkdocs.yml": "nav:\n  - Home: index.md\n  - Gone: missing.md\n",
                 "index.md": "# Index\n\nText.\n"}
        with Tree(files) as root:
            self.assertEqual(checks(root).get("nav-target-missing"), 1)

    def test_heading_level_jump(self):
        with Tree({"index.md": "# Page\n\n### Too deep\n\nText.\n"}) as root:
            self.assertEqual(checks(root).get("heading-level-jump"), 1)


class CliTest(unittest.TestCase):
    def test_json_shape_and_exit_policy(self):
        with Tree({"index.md": "# Index\n\n[Gone](missing.md)\n"}) as root:
            buffer = io.StringIO()
            with redirect_stdout(buffer):
                code = docs_health.main([str(root), "--format", "json", "--fail-on", "error"])
            payload = json.loads(buffer.getvalue())
            self.assertEqual(code, 1)
            self.assertEqual(payload["schema_version"], docs_health.SCHEMA_VERSION)
            self.assertIn("summary", payload)
            for finding in payload["findings"]:
                self.assertEqual(set(finding), {"path", "line", "check", "message", "severity"})

    def test_clean_tree_exits_zero(self):
        files = {"index.md": "# Index\n\n[Other page](other.md)\n", "other.md": "# Other page\n\nText.\n"}
        with Tree(files) as root:
            buffer = io.StringIO()
            with redirect_stdout(buffer):
                code = docs_health.main([str(root), "--fail-on", "any"])
            self.assertEqual(code, 0, buffer.getvalue())

