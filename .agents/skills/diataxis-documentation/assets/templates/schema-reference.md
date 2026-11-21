---
title: "<Schema name> schema reference"
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

# <Schema name> schema reference

<One factual sentence describing what the schema defines.>

| | |
|---|---|
| **Schema language** | <JSON Schema draft / OpenAPI version / protobuf syntax / Avro> |
| **Canonical location** | `<path or URL>` |
| **Generated** | Yes/No — <generator, if generated> |
| **Applies to** | <product> <version> |

## Properties

| Property | Type | Required | Default | Format | Constraints | Description |
|---|---|---|---|---|---|---|
| `<property>` | `<type>` | Yes/No | `<default>` | `<format>` | <constraint> | <description> |

## Composition

<`oneOf`, `anyOf`, `allOf`, discriminators in use, and what each means for a producer of this data. Write "None" if the schema is flat.>

## Unknown properties

<Rejected / ignored / preserved. State the runtime behavior, not the schema keyword alone.>

## Evolution policy

<What counts as a breaking change to this schema, and how consumers are notified.>

## Example document

```json
{
  "example": "valid instance"
}
```

## Compatibility

| Version | Change |
|---|---|
| <version> | <property added/removed/constrained> |

## See also

- Object reference: <reference link>
- Validation guide: <how-to link>
