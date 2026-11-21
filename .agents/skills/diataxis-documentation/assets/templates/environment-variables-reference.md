---
title: "<Component> environment variables"
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

# <Component> environment variables

Every environment variable read by <component>. This page covers <scope>.

Applies to <product> <version>.

## Variables

### `<VAR_NAME>`

| | |
|---|---|
| **Type** | `<type>` <unit, if any> |
| **Default when unset** | `<default>` |
| **Empty string** | <distinct from unset? what it means> |
| **Allowed values** | <values or validation rule> |
| **Read** | <once at startup / per operation> |
| **Secret** | Yes/No — <if yes: must not be logged or committed> |
| **Corresponding config key** | `<key>` — <which wins> |
| **Introduced in** | <version> |
| **Deprecated in** | <version, and replacement> |

<One or two neutral sentences on what the variable does.>

### `<NEXT_VAR>`

<Repeat the same table for every variable.>

## Example

```bash
export <VAR_NAME>=<value>
```

## See also

- Configuration reference: <reference link>
- Task guide: <how-to link>
