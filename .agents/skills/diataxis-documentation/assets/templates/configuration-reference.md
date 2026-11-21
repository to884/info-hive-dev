---
title: "<Component> configuration reference"
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

# <Component> configuration reference

Every setting for <component>. This page covers <scope>. It does not cover <exclusion>.

Applies to <product> <version>.

## Precedence

Settings resolve in this order, first match wins:

1. <command-line flag>
2. <environment variable>
3. <config file>
4. <built-in default>

## Settings

### `<key>`

| | |
|---|---|
| **Type** | `<type>` <unit, if any> |
| **Default** | `<default>` <note any platform- or mode-specific default> |
| **Allowed values** | <values or validation rule> |
| **On invalid value** | <startup failure / ignored / clamped> |
| **Set via** | <flag, env var, file path> |
| **Reload behavior** | <immediate / on reload / restart required> |
| **Security implications** | <secret? widens access? disables a protection? "None" if none> |
| **Introduced in** | <version> |
| **Deprecated in** | <version, and replacement key> |

<One or two neutral sentences on what the setting does.>

### `<next key>`

<Repeat the same table for every setting. The schema must not vary between entries.>

## Example configuration

```yaml
<compact, valid example>
```

## See also

- Task guide: <how-to link>
- Background: <explanation link>
