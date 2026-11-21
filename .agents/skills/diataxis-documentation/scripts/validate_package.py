#!/usr/bin/env python3
"""Validate the skill package: frontmatter, manifest, and internal pointers.

Checks the invariants that would otherwise be maintained by hand and silently
broken: standard-only frontmatter, a manifest that matches what is actually
distributable, every path SKILL.md points at existing, and every scaffold
template being present.

Standard library only. No network access.
"""

from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

from diataxis_scaffold import TEMPLATE_FILES  # noqa: E402
from update_manifest import compute_manifest  # noqa: E402

# The documented standard set (AGENTS.md, "Conventions and hard constraints").
# Vendor-specific keys such as `allowed-tools` are deliberately NOT allowed: an
# unknown field can break or be silently dropped in one of the three target
# runtimes. Widen this only by widening AGENTS.md first.
ALLOWED_FRONTMATTER = {"name", "description", "license", "compatibility", "metadata"}
REQUIRED_FRONTMATTER = {"name", "description"}
MAX_FRONTMATTER_CHARS = 1024
NAME_PATTERN = re.compile(r"^[a-z0-9]+(?:-[a-z0-9]+)*$")


def repo_root() -> Path:
    return Path(__file__).resolve().parents[1]


def read_frontmatter(text: str) -> tuple[dict[str, str], str]:
    """Parse SKILL.md frontmatter, returning (fields, raw block).

    Detects the same keys as the two distributed parsers — see
    ``tests/test_shared_parsing.py`` — but also returns the raw block, which
    this script needs for the 1024-character limit and they do not.
    """
    lines = text.splitlines()
    idx = 0
    while idx < len(lines) and lines[idx].strip() == "":
        idx += 1
    if idx >= len(lines) or lines[idx].strip() not in {"---", "+++"}:
        return {}, ""
    fence = lines[idx].strip()
    for end in range(idx + 1, len(lines)):
        if lines[end].strip() == fence:
            block = "\n".join(lines[idx + 1:end])
            data: dict[str, str] = {}
            for line in lines[idx + 1:end]:
                m = re.match(r"^([A-Za-z0-9_.-]+)\s*:\s*(.*)$", line)
                if m:
                    data[m.group(1)] = m.group(2).strip()
            return data, block
    return {}, ""


def check(root: Path) -> list[str]:
    problems: list[str] = []

    skill = root / "SKILL.md"
    if not skill.exists():
        return ["SKILL.md is missing"]
    text = skill.read_text(encoding="utf-8")
    fields, block = read_frontmatter(text)

    if not fields:
        problems.append("SKILL.md has no parseable YAML frontmatter")
    for required in sorted(REQUIRED_FRONTMATTER):
        if required not in fields:
            problems.append(f"SKILL.md frontmatter is missing required field: {required}")
    for key in sorted(fields):
        if key not in ALLOWED_FRONTMATTER:
            problems.append(f"SKILL.md frontmatter has non-standard field: {key}")
    if len(block) > MAX_FRONTMATTER_CHARS:
        problems.append(f"SKILL.md frontmatter is {len(block)} chars; the limit is {MAX_FRONTMATTER_CHARS}")
    name = fields.get("name", "")
    if name and not NAME_PATTERN.match(name):
        problems.append(f"SKILL.md name '{name}' is not lowercase kebab-case")

    # Every path SKILL.md points at must exist.
    for match in re.finditer(r"`((?:references|assets|scripts)/[A-Za-z0-9_./-]+)`", text):
        target = match.group(1)
        if target.endswith("/"):
            if not (root / target).is_dir():
                problems.append(f"SKILL.md references a missing directory: {target}")
        elif not (root / target).exists():
            problems.append(f"SKILL.md references a missing path: {target}")

    # Every scaffold template must exist, and every template must be reachable.
    templates_dir = root / "assets" / "templates"
    for doc_type, filename in sorted(TEMPLATE_FILES.items()):
        if not (templates_dir / filename).exists():
            problems.append(f"scaffold type '{doc_type}' points at a missing template: {filename}")
    mapped = set(TEMPLATE_FILES.values())
    for path in sorted(templates_dir.glob("*.md")):
        if path.name not in mapped:
            problems.append(f"template {path.name} is not reachable from diataxis_scaffold.py")

    # Manifest must match what is distributable, and every entry must exist.
    manifest = root / "manifest.txt"
    if not manifest.exists():
        problems.append("manifest.txt is missing")
    else:
        listed = manifest.read_text(encoding="utf-8").split()
        expected = compute_manifest(root)
        for entry in listed:
            if not (root / entry).exists():
                problems.append(f"manifest.txt lists a missing file: {entry}")
        for entry in expected:
            if entry not in listed:
                problems.append(f"manifest.txt is missing a distributable file: {entry}")
        for entry in listed:
            if entry not in expected:
                problems.append(f"manifest.txt lists a non-distributable file: {entry}")

    return problems


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Validate the skill package.")
    parser.add_argument("--root", type=Path, default=None, help="Package root (defaults to the repository root)")
    args = parser.parse_args(argv)

    root = (args.root or repo_root()).resolve()
    problems = check(root)
    if problems:
        for problem in problems:
            print(f"error: {problem}", file=sys.stderr)
        print(f"{len(problems)} problem(s) found.", file=sys.stderr)
        return 1
    print("Package is valid.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
