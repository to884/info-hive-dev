#!/usr/bin/env python3
"""Objective document-health checks for a Markdown documentation tree.

This script deliberately knows nothing about Diátaxis modes. It checks facts
that are true or false regardless of which user need a page serves: broken
internal links, orphaned pages, duplicate titles, missing H1s, unresolved
placeholders, malformed code fences, empty sections, images without alt text,
non-descriptive link text, and navigation entries pointing at missing files.

Mode assessment lives in diataxis_audit.py. Keeping them apart matters: these
findings are defects, those are signals.

Standard library only. No network access.
"""

from __future__ import annotations

import argparse
import json
import os
import re
import sys
from dataclasses import dataclass, asdict
from pathlib import Path
from urllib.parse import unquote, urlparse

SCHEMA_VERSION = "1.0"

DOC_EXTENSIONS = {".md", ".mdx"}
IGNORE_DIRS = {
    ".git", ".hg", ".svn", "node_modules", "vendor", "dist", "build",
    "site", "public", "__pycache__", ".venv", "venv",
}

NAV_FILES = ("mkdocs.yml", "mkdocs.yaml", "SUMMARY.md", "_toc.yml", "sidebars.js", "sidebars.json")

VAGUE_LINK_TEXT = {
    "here", "click here", "this", "this page", "this link", "read more",
    "more", "link", "see here", "learn more", "docs", "documentation",
}

PLACEHOLDER_PATTERNS = (
    (r"<[a-z][a-z0-9 _/-]{2,40}>", "angle-bracket placeholder"),
    (r"\bTODO\b", "TODO"),
    (r"\bTBD\b", "TBD"),
    (r"\bFIXME\b", "FIXME"),
    (r"\bLorem ipsum\b", "lorem ipsum"),
)


@dataclass
class Finding:
    path: str
    line: int
    check: str
    message: str
    severity: str


def iter_docs(root: Path) -> list[Path]:
    files: list[Path] = []
    for child in sorted(root.rglob("*")):
        if child.is_dir():
            continue
        if child.suffix.lower() not in DOC_EXTENSIONS:
            continue
        if any(part in IGNORE_DIRS for part in child.parts):
            continue
        files.append(child)
    return files


def read_text(path: Path) -> str:
    try:
        return path.read_text(encoding="utf-8")
    except (UnicodeDecodeError, OSError):
        return path.read_text(encoding="utf-8", errors="replace")


def split_frontmatter(text: str) -> tuple[dict[str, str], str, int]:
    """Parse a leading frontmatter block only.

    Deliberately kept behaviour-compatible with ``diataxis_audit`` — the two
    scripts are distributed standalone and cannot share a module, so
    ``tests/test_shared_parsing.py`` pins them to the same behaviour. The extra
    third element is this script's own need: the body's line offset, so that
    findings can report line numbers in the original file.
    """
    lines = text.splitlines()
    idx = 0
    while idx < len(lines) and lines[idx].strip() == "":
        idx += 1
    if idx >= len(lines) or lines[idx].strip() not in {"---", "+++"}:
        return {}, text, 0
    fence = lines[idx].strip()
    for end in range(idx + 1, len(lines)):
        if lines[end].strip() == fence:
            data: dict[str, str] = {}
            for line in lines[idx + 1:end]:
                m = re.match(r"^([A-Za-z0-9_.-]+)\s*:\s*(.*)$", line)
                if m:
                    data[m.group(1)] = m.group(2).strip().strip('"').strip("'")
            return data, "\n".join(lines[end + 1:]), end + 1
    return {}, text, 0


def code_line_flags(lines: list[str]) -> tuple[list[bool], int | None]:
    """Mark lines inside fenced code blocks; return the line of an unclosed fence."""
    in_code = [False] * len(lines)
    fence: str | None = None
    fence_line: int | None = None
    for i, line in enumerate(lines):
        m = re.match(r"^\s{0,3}(`{3,}|~{3,})", line)
        if m:
            token = m.group(1)
            if fence is None:
                fence, fence_line = token, i
                in_code[i] = True
                continue
            # CommonMark: the closing fence uses the same character and is at
            # least as long as the opening one. A shorter run inside a block is
            # content, not a close.
            if token[0] == fence[0] and len(token) >= len(fence):
                fence, fence_line = None, None
                in_code[i] = True
                continue
        if fence is not None:
            in_code[i] = True
    return in_code, fence_line


def anchor_slug(heading: str) -> str:
    slug = heading.strip().lower()
    slug = re.sub(r"[`*_~\[\]()]", "", slug)
    slug = re.sub(r"[^a-z0-9À-￿\s-]", "", slug)
    slug = re.sub(r"\s+", "-", slug).strip("-")
    return slug


def check_file(path: Path, root: Path, all_headings: dict[Path, set[str]]) -> tuple[list[Finding], set[Path], str | None]:
    findings: list[Finding] = []
    rel = path.relative_to(root).as_posix()
    raw = read_text(path)
    frontmatter, body, offset = split_frontmatter(raw)
    lines = body.splitlines()
    in_code, unclosed = code_line_flags(lines)

    def add(line: int, check: str, message: str, severity: str = "error") -> None:
        findings.append(Finding(rel, line + offset + 1, check, message, severity))

    if unclosed is not None:
        add(unclosed, "malformed-fence", "Code fence opened here is never closed.")

    # Headings and H1.
    headings: list[tuple[int, int, str]] = []
    for i, line in enumerate(lines):
        if in_code[i]:
            continue
        m = re.match(r"^\s{0,3}(#{1,6})\s+(.*?)\s*#*\s*$", line)
        if m:
            headings.append((i, len(m.group(1)), m.group(2).strip()))

    h1s = [h for h in headings if h[1] == 1]
    title_fm = frontmatter.get("title")
    if not h1s and not title_fm:
        add(0, "missing-h1", "No H1 heading and no frontmatter title.")
    elif len(h1s) > 1:
        add(h1s[1][0], "multiple-h1", f"{len(h1s)} H1 headings; a page should have one.", "warning")

    # Heading level jumps.
    prev = None
    for i, level, text in headings:
        if prev is not None and level > prev + 1:
            add(i, "heading-level-jump", f"Heading jumps from H{prev} to H{level}.", "warning")
        prev = level

    # Empty sections. A heading followed immediately by a deeper heading is a
    # container, not an empty section.
    for idx, (i, level, text) in enumerate(headings):
        if idx + 1 < len(headings):
            next_i, next_level, _ = headings[idx + 1]
            if next_level > level:
                continue
            end = next_i
        else:
            end = len(lines)
        content = "\n".join(lines[i + 1:end]).strip()
        if not content:
            add(i, "empty-section", f"Section '{text}' has no content.", "warning")

    # Duplicate headings within the page (anchor collisions).
    seen: dict[str, int] = {}
    for i, level, text in headings:
        slug = anchor_slug(text)
        if slug and slug in seen:
            add(i, "duplicate-heading", f"Heading '{text}' repeats; anchors will collide.", "warning")
        seen.setdefault(slug, i)

    # Placeholders.
    for i, line in enumerate(lines):
        if in_code[i]:
            continue
        for pattern, label in PLACEHOLDER_PATTERNS:
            if re.search(pattern, line, flags=re.IGNORECASE if label != "TODO" else 0):
                add(i, "unresolved-placeholder", f"Unresolved {label} on this line.")
                break

    # Images without alt text.
    for i, line in enumerate(lines):
        if in_code[i]:
            continue
        for m in re.finditer(r"!\[(.*?)\]\(([^)]*)\)", line):
            if not m.group(1).strip():
                add(i, "image-without-alt", f"Image {m.group(2)} has empty alt text.")
        for m in re.finditer(r"<img\b[^>]*>", line):
            if "alt=" not in m.group(0):
                add(i, "image-without-alt", "HTML <img> without an alt attribute.")

    # Links.
    links: set[Path] = set()
    for i, line in enumerate(lines):
        if in_code[i]:
            continue
        for m in re.finditer(r"(?<!\!)\[([^\]]+)\]\(([^)\s]+)(?:\s+\"[^\"]*\")?\)", line):
            text, target = m.group(1).strip(), m.group(2).strip()
            if text.lower().strip(".:!") in VAGUE_LINK_TEXT:
                add(i, "vague-link-text", f"Link text '{text}' does not describe its destination.", "warning")
            if re.match(r"^https?://", target):
                if text == target:
                    add(i, "vague-link-text", "Bare URL used as link text.", "warning")
                continue
            parsed = urlparse(target)
            if parsed.scheme or target.startswith("#"):
                if target.startswith("#"):
                    slug = unquote(target[1:]).lower()
                    if slug and slug not in {anchor_slug(h[2]) for h in headings}:
                        add(i, "broken-anchor", f"Anchor '{target}' does not match a heading on this page.")
                continue
            file_part = unquote(parsed.path)
            if not file_part:
                continue
            resolved = (path.parent / file_part).resolve()
            if resolved.is_dir():
                index = next((resolved / name for name in ("index.md", "README.md") if (resolved / name).exists()), None)
                resolved = index or resolved
            if not resolved.exists():
                add(i, "broken-link", f"Link target '{target}' does not exist.")
                continue
            if resolved.suffix.lower() in DOC_EXTENSIONS:
                links.add(resolved)
                if parsed.fragment:
                    targets = all_headings.get(resolved)
                    if targets is not None and unquote(parsed.fragment).lower() not in targets:
                        add(i, "broken-anchor", f"Anchor '#{parsed.fragment}' not found in {file_part}.")

    title = title_fm or (h1s[0][2] if h1s else None)
    return findings, links, title


def collect_headings(files: list[Path]) -> dict[Path, set[str]]:
    table: dict[Path, set[str]] = {}
    for path in files:
        _, body, _ = split_frontmatter(read_text(path))
        lines = body.splitlines()
        in_code, _ = code_line_flags(lines)
        slugs = set()
        for i, line in enumerate(lines):
            if in_code[i]:
                continue
            m = re.match(r"^\s{0,3}#{1,6}\s+(.*?)\s*#*\s*$", line)
            if m:
                slugs.add(anchor_slug(m.group(1)))
        table[path.resolve()] = slugs
    return table


def nav_targets(root: Path) -> list[tuple[str, str]]:
    """Extract .md paths mentioned in common navigation files."""
    entries: list[tuple[str, str]] = []
    for name in NAV_FILES:
        nav = root / name
        if not nav.exists():
            nav = next((p for p in root.rglob(name) if not any(part in IGNORE_DIRS for part in p.parts)), None)
        if not nav or not nav.exists():
            continue
        for target in re.findall(r"[\w./-]+\.mdx?", read_text(nav)):
            entries.append((nav.relative_to(root).as_posix(), target))
    return entries


def run(root: Path) -> tuple[list[Finding], dict[str, object]]:
    files = iter_docs(root)
    headings = collect_headings(files)
    findings: list[Finding] = []
    linked: set[Path] = set()
    titles: dict[str, list[str]] = {}

    for path in files:
        file_findings, links, title = check_file(path, root, headings)
        findings.extend(file_findings)
        linked |= links
        if title:
            titles.setdefault(title.strip().lower(), []).append(path.relative_to(root).as_posix())

    for title, paths in sorted(titles.items()):
        if len(paths) > 1:
            for p in paths[1:]:
                findings.append(Finding(p, 1, "duplicate-title",
                                        f"Title duplicates {paths[0]}; readers and search cannot tell them apart.",
                                        "warning"))

    entry_names = {"index.md", "readme.md", "index.mdx"}
    nav = nav_targets(root)
    nav_resolved: set[Path] = set()
    for nav_file, target in nav:
        candidates = [
            (root / target).resolve(),
            (root / "docs" / target).resolve(),
            ((root / nav_file).parent / target).resolve(),
        ]
        found = next((c for c in candidates if c.exists()), None)
        if found is None:
            findings.append(Finding(nav_file, 1, "nav-target-missing",
                                    f"Navigation entry '{target}' points at a file that does not exist.",
                                    "error"))
        else:
            nav_resolved.add(found)

    for path in files:
        resolved = path.resolve()
        if resolved in linked or resolved in nav_resolved:
            continue
        if path.name.lower() in entry_names:
            continue
        findings.append(Finding(path.relative_to(root).as_posix(), 1, "orphan-page",
                                "No other page links to this file and no navigation entry references it.",
                                "warning"))

    summary = {
        "files_scanned": len(files),
        "findings": len(findings),
        "errors": sum(1 for f in findings if f.severity == "error"),
        "warnings": sum(1 for f in findings if f.severity == "warning"),
        "by_check": {},
    }
    for finding in findings:
        by_check = summary["by_check"]
        by_check[finding.check] = by_check.get(finding.check, 0) + 1
    return findings, summary


def markdown_report(findings: list[Finding], summary: dict[str, object]) -> str:
    lines = ["# Documentation health", "",
             f"Scanned {summary['files_scanned']} files. "
             f"{summary['errors']} error(s), {summary['warnings']} warning(s).", ""]
    if not findings:
        lines.append("No findings.")
        return "\n".join(lines)
    lines.append("| File | Line | Severity | Check | Finding |")
    lines.append("|---|---:|---|---|---|")
    for f in sorted(findings, key=lambda f: (f.severity != "error", f.path, f.line)):
        lines.append(f"| `{f.path}` | {f.line} | {f.severity} | `{f.check}` | {f.message.replace('|', chr(92) + '|')} |")
    lines.append("")
    lines.append("## Counts by check")
    lines.append("")
    for check, count in sorted(summary["by_check"].items(), key=lambda kv: (-kv[1], kv[0])):
        lines.append(f"- `{check}`: {count}")
    return "\n".join(lines)


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Check a documentation tree for objective structural defects.")
    parser.add_argument("path", help="Documentation root directory")
    parser.add_argument("--format", choices=("markdown", "json"), default="markdown")
    parser.add_argument("--fail-on", choices=("never", "error", "any"), default="never",
                        help="Exit non-zero when findings of this severity exist (default: never)")
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)

    root = Path(args.path).resolve()
    if not root.exists():
        print(f"Missing path: {root}", file=sys.stderr)
        return 2
    if not root.is_dir():
        print(f"Not a directory: {root}", file=sys.stderr)
        return 2

    findings, summary = run(root)
    if args.format == "json":
        print(json.dumps({"schema_version": SCHEMA_VERSION, "summary": summary,
                          "findings": [asdict(f) for f in findings]}, indent=2, ensure_ascii=False))
    else:
        print(markdown_report(findings, summary))

    if args.fail_on == "error" and summary["errors"]:
        return 1
    if args.fail_on == "any" and findings:
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
