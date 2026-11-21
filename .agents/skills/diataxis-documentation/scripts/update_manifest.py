#!/usr/bin/env python3
"""Generate or verify manifest.txt, the list of distributable files.

manifest.txt used to be maintained by hand, which meant a forgotten update
shipped an incomplete package. The rules below decide what is distributable;
run with --check in CI to fail when the file drifts.

Standard library only. No network access.
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

# Files shipped as part of the skill package.
INCLUDE_FILES = (
    "SKILL.md",
    "README.md",
    "LICENSE.md",
    "NOTICE.md",
    "SECURITY.md",
    "CHANGELOG.md",
    "manifest.txt",
)

INCLUDE_TREES = (
    "references",
    "assets",
)

# Scripts that are part of the distributed skill, as opposed to repository
# maintenance tooling.
INCLUDE_SCRIPTS = (
    "scripts/diataxis_audit.py",
    "scripts/diataxis_scaffold.py",
    "scripts/docs_health.py",
)

# Never distributed: repository-only material.
EXCLUDE_DIRS = {
    ".git", ".github", ".idea", ".serena", "__pycache__", "tests", "evals",
    "node_modules", ".venv", "venv",
}
EXCLUDE_SUFFIXES = {".pyc", ".pyo"}
EXCLUDE_NAMES = {".DS_Store", ".gitignore", "AGENTS.md", "CLAUDE.md", "skill-feedback.md"}


def repo_root() -> Path:
    return Path(__file__).resolve().parents[1]


def is_excluded(path: Path, root: Path) -> bool:
    rel = path.relative_to(root)
    if any(part in EXCLUDE_DIRS for part in rel.parts):
        return True
    if path.suffix in EXCLUDE_SUFFIXES:
        return True
    return path.name in EXCLUDE_NAMES


def compute_manifest(root: Path | None = None) -> list[str]:
    root = root or repo_root()
    entries: set[str] = set()
    for name in INCLUDE_FILES:
        if (root / name).exists():
            entries.add(name)
    for tree in INCLUDE_TREES:
        base = root / tree
        if not base.exists():
            continue
        for path in base.rglob("*"):
            if path.is_dir() or is_excluded(path, root):
                continue
            entries.add(path.relative_to(root).as_posix())
    for script in INCLUDE_SCRIPTS:
        if (root / script).exists():
            entries.add(script)
    return sorted(entries)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Generate or verify manifest.txt.")
    parser.add_argument("--check", action="store_true", help="Verify without writing; exit 1 on drift")
    args = parser.parse_args(argv)

    root = repo_root()
    expected = compute_manifest(root)
    manifest = root / "manifest.txt"
    current = manifest.read_text(encoding="utf-8").split() if manifest.exists() else []

    if args.check:
        missing = [e for e in expected if e not in current]
        extra = [e for e in current if e not in expected]
        if not missing and not extra:
            print(f"manifest.txt is up to date ({len(expected)} entries).")
            return 0
        for entry in missing:
            print(f"missing from manifest.txt: {entry}", file=sys.stderr)
        for entry in extra:
            print(f"listed but not distributable: {entry}", file=sys.stderr)
        print("Run: python3 scripts/update_manifest.py", file=sys.stderr)
        return 1

    manifest.write_text("\n".join(expected) + "\n", encoding="utf-8")
    print(f"Wrote {manifest} ({len(expected)} entries).")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
