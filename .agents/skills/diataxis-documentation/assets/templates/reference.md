---
title: "<Object or interface> reference"
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

# <Object or interface> reference

<One-sentence factual description.> This page covers <scope>. It does not cover <exclusion>.

Applies to <product> <version>.

## Synopsis

```text
<syntax or shape>
```

## Fields

| Name | Type | Required | Default | Constraints | Description |
|---|---|---|---|---|---|
| `<name>` | `<type>` | Yes/No | `<default>` | <constraint> | <neutral factual description> |

## Values

| Value | Meaning |
|---|---|
| `<value>` | <description> |

## Behavior

<Neutral description. Include guarantees, limits, side effects, and ordering.>

## Errors

| Error | Cause | Retryable |
|---|---|---|
| `<error>` | <cause> | Yes/No |

## Example

```bash
<compact example>
```

## Compatibility

| Version | Change |
|---|---|
| <version> | <added/changed/deprecated> |

## See also

- Task guide: <how-to link>
- Conceptual background: <explanation link>
