#!/usr/bin/env python3
"""Create a single Diátaxis documentation page from bundled templates.

This script creates one page at a time. It intentionally does not create four
empty Diátaxis sections by default.

Standard library only. No network access.
"""

from __future__ import annotations

import argparse
import re
import sys
import unicodedata
from pathlib import Path

TEMPLATE_FILES = {
    "tutorial": "tutorial.md",
    "how-to": "how-to-guide.md",
    "reference": "reference.md",
    "explanation": "explanation.md",
    "api-endpoint-reference": "api-endpoint-reference.md",
    "api-object-reference": "api-object-reference.md",
    "cli-command-reference": "cli-command-reference.md",
    "configuration-reference": "configuration-reference.md",
    "environment-variables-reference": "environment-variables-reference.md",
    "schema-reference": "schema-reference.md",
    "error-reference": "error-reference.md",
    "landing-page": "landing-page.md",
    "audit-report": "audit-report.md",
    "doc-index": "doc-index.md",
}

# The Diátaxis mode each template represents. Used only by --with-doc-type:
# the templates themselves carry no `doc_type:` field, because the skill does
# not ask a project to adopt that convention.
DOC_TYPE_VALUES = {
    "tutorial": "tutorial",
    "how-to": "how-to",
    "reference": "reference",
    "explanation": "explanation",
    "api-endpoint-reference": "reference",
    "api-object-reference": "reference",
    "cli-command-reference": "reference",
    "configuration-reference": "reference",
    "environment-variables-reference": "reference",
    "schema-reference": "reference",
    "error-reference": "reference",
    "landing-page": "landing-page",
}

# Characters that are safe in a filename across the platforms this may run on.
_SLUG_STRIP = re.compile(r"[`'\"\u2019]")
_SLUG_SEP = re.compile(r"[^\w]+", re.UNICODE)


def slugify(title: str) -> str:
    """Slugify a title, preserving non-ASCII letters rather than discarding them.

    Returns an empty string when nothing usable survives, so the caller can ask
    for an explicit filename instead of silently writing to `untitled.md`.
    """
    slug = unicodedata.normalize("NFKC", title).strip().lower()
    slug = _SLUG_STRIP.sub("", slug)
    slug = _SLUG_SEP.sub("-", slug)
    slug = slug.strip("-_")
    return slug


def yaml_double_quote(value: str) -> str:
    """Quote a string for a YAML double-quoted scalar."""
    escaped = value.replace("\\", "\\\\").replace('"', '\\"')
    escaped = escaped.replace("\n", "\\n").replace("\r", "\\r").replace("\t", "\\t")
    return f'"{escaped}"'


def skill_root() -> Path:
    return Path(__file__).resolve().parents[1]


def template_path(doc_type: str) -> Path:
    return skill_root() / "assets" / "templates" / TEMPLATE_FILES[doc_type]


def heading_for(doc_type: str, title: str) -> str:
    if doc_type == "tutorial":
        if title.lower().startswith("tutorial"):
            return f"# {title}"
        return f"# Tutorial: {title}"
    if doc_type == "how-to":
        if title.lower().startswith("how to"):
            return f"# {title}"
        return f"# How to {title[0].lower()}{title[1:]}"
    return f"# {title}"


def add_doc_type(text: str, value: str) -> str:
    """Insert a `doc_type:` field after the frontmatter title line.

    Only called when the caller explicitly asks for it. Returns the text
    unchanged when the template has no frontmatter to put the field in.
    """
    def insert(match: re.Match[str]) -> str:
        return f"{match.group(0)}\ndoc_type: {value}"

    return re.sub(r"^title:.*$", insert, text, count=1, flags=re.MULTILINE)


def render_template(text: str, title: str, doc_type: str, with_doc_type: bool = False) -> str:
    """Replace the frontmatter title and the first H1; leave other placeholders."""
    text = re.sub(r'^(\s*title:\s*)"[^"]*"\s*$',
                  lambda m: m.group(1) + yaml_double_quote(title),
                  text, count=1, flags=re.MULTILINE)
    text = re.sub(r"^# .+$", lambda _m: heading_for(doc_type, title), text, count=1, flags=re.MULTILINE)
    if with_doc_type and doc_type in DOC_TYPE_VALUES:
        text = add_doc_type(text, DOC_TYPE_VALUES[doc_type])
    return text


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Create a Diátaxis documentation page from a bundled template.")
    parser.add_argument("doc_type", choices=sorted(TEMPLATE_FILES), help="Template type to create")
    parser.add_argument("title", help="Page title")
    parser.add_argument("--out-dir", default=".", help="Output directory")
    parser.add_argument("--filename", help="Output filename. Defaults to a slugified title with .md")
    parser.add_argument("--force", action="store_true", help="Overwrite an existing file")
    parser.add_argument("--with-doc-type", action="store_true",
                        help="Also emit a `doc_type:` frontmatter field. Off by default: most "
                             "projects do not use this convention and the skill does not impose it.")
    return parser


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)

    title = args.title.strip()
    if not title:
        parser.error("title must not be empty")

    source = template_path(args.doc_type)
    if not source.exists():
        print(f"Template not found: {source}", file=sys.stderr)
        return 2

    if args.filename:
        filename = args.filename
    else:
        slug = slugify(title)
        if not slug:
            print(
                f"Cannot derive a filename from the title {title!r}. Pass --filename explicitly.",
                file=sys.stderr,
            )
            return 2
        filename = f"{slug}.md"

    out_dir = Path(args.out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)
    target = out_dir / filename

    if target.exists() and not args.force:
        print(f"Refusing to overwrite existing file: {target}. Use --force to overwrite.", file=sys.stderr)
        return 1

    rendered = render_template(source.read_text(encoding="utf-8"), title, args.doc_type,
                               with_doc_type=args.with_doc_type)
    target.write_text(rendered, encoding="utf-8")
    print(target)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
