---
title: "<Object> object"
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

# `<Object>` object

<What this object represents.> It is returned by <endpoints> and accepted by <endpoints>.

Applies to API version <version>.

## Fields

| Field | Type | Nullable | Required on create | Mutability | Default | Constraints | Description |
|---|---|---|---|---|---|---|---|
| `<field>` | `<type>` | Yes/No | Yes/No | read-only / write-once / updatable | `<default>` | <constraint> | <description> |

## Enumerations

### `<field>`

| Value | Meaning |
|---|---|
| `<value>` | <meaning> |

<Every permitted value must be listed.>

## Relationships

| Related object | Expressed as | Notes |
|---|---|---|
| `<Object>` | id / embedded / link | <notes> |

## Lifecycle

<States and permitted transitions. Delete if the object has no lifecycle.>

## Limits

| Constraint | Value |
|---|---|
| <array length, string length, object size> | <value> |

## Example

```json
{
  "example": "compact illustration"
}
```

## Compatibility

| Version | Change |
|---|---|
| <version> | <field added/deprecated/removed> |

## See also

- Endpoints: <reference link>
- Task guide: <how-to link>
