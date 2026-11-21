---
title: "<Component> error reference"
---

<!--
AUTHORING CONTRACT

Delete every field and section that does not apply — but write "None" rather
than dropping a field the reader will look for.
Do not publish angle-bracket placeholders or these instructions.
Use the repository's existing frontmatter instead of this example when present.
Every fact here must come from the authoritative source for that claim type
(see references/evidence-and-verification.md). No inferred values, no invented
defaults, limits, or error messages.
Record evidence and verification in the agent's work summary.
-->

<!--
PLANNING (delete before publishing)
Reader:
Scope of this page (and what it excludes):
Product/version:
Primary mode: reference
Authoritative source (file, schema, parser, registry):
Generated or hand-written:
Coverage check (source entries vs documented entries):
-->

# <Component> error reference

Every error <component> emits, with its stable identifier and meaning. This page covers <scope>.

Applies to <product> <version>.

## Index

| Code | Message | Retryable |
|---|---|---|
| `<CODE>` | <literal message text> | Yes/No |

<Make both the code and the literal message searchable: readers arrive with one or the other pasted from a terminal.>

## Errors

### `<CODE>`

| | |
|---|---|
| **Message** | `<exact literal text, if stable>` |
| **Raised when** | <the condition, from source — not a guess> |
| **Retryable** | Yes/No — <backoff, if yes> |
| **HTTP status / exit code** | `<value>` |
| **What to do** | <one line; link the full procedure> |
| **Introduced in** | <version> |
| **Changed in** | <version, and what changed> |

### `<NEXT_CODE>`

<Repeat the same table for every error.>

## See also

- Troubleshooting: <how-to link>
- Background: <explanation link>
