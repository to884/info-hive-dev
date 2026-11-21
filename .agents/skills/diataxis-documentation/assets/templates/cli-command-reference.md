---
title: "<command> <subcommand>"
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

# `<command> <subcommand>`

<One factual sentence describing what the command does.>

Applies to <command> version <version>. The synopsis and flags below must match `<command> <subcommand> --help` for that version.

## Synopsis

```text
<command> <subcommand> [OPTIONS] <ARG>...
```

## Arguments

| Argument | Required | Variadic | Description |
|---|---|---|---|
| `<ARG>` | Yes/No | Yes/No | <description> |

## Flags

| Flag | Short | Value | Default | Repeatable | Description |
|---|---|---|---|---|---|
| `--<flag>` | `-<f>` | `<type>` | `<default>` | Yes/No | <description> |

## Environment variables

| Variable | Effect | Precedence |
|---|---|---|
| `<VAR>` | <effect> | <where it sits in the order below> |

## Precedence

Settings resolve in this order, first match wins:

1. <command-line flag>
2. <environment variable>
3. <config file>
4. <built-in default>

## Output

**stdout:** <what is written, and its format; state whether the format is stable enough to parse.>

**stderr:** <what is written, including progress and log output.>

## Exit codes

| Code | Meaning |
|---|---|
| `0` | <meaning> |
| `<n>` | <meaning> |

## Side effects

<Files written, state changed, network calls made. Write "None" if there are none.>

## Examples

```bash
<compact example, one per distinct usage shape>
```

## Compatibility

| Version | Change |
|---|---|
| <version> | <flag added/renamed/deprecated> |

## See also

- Task guide: <how-to link>
- Related command: <reference link>
