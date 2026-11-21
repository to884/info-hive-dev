# Docs style guide (project-local)

This project's conventions. They override any general style advice.

- **No frontmatter.** Pages start with the H1. Do not add `title:` or `doc_type:`.
- **Filenames** are `snake_case.md`. Not kebab-case.
- **Headings** are sentence case, and reference pages use the exact identifier as the heading: `## queue.retention`, not `## Retention`.
- **Admonitions** use the blockquote form `> **Note:**`. Do not use `:::note` or `!!! note`.
- **Links** are relative and always end in `.md`.
- **We say "queue", never "topic" or "channel".** The API once used "topic"; the docs do not.
- **Code blocks** never include a `$` prompt.
- Every reference page ends with a `## See also` list.
