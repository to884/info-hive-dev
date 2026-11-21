---
title: "<METHOD> <path>"
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

# <METHOD> `<path>`

<One factual sentence describing what this endpoint does.>

Applies to API version <version>. This page covers <scope>.

## Request

```http
<METHOD> <path> HTTP/1.1
Host: <host>
Authorization: <scheme> <credential>
Content-Type: application/json
```

## Authentication

Requires <scheme>. Required scopes or permissions: `<scope>`.

## Path parameters

| Name | Type | Constraints | Description |
|---|---|---|---|
| `<name>` | `<type>` | <constraint> | <description> |

## Query parameters

| Name | Type | Required | Default | Constraints | Description |
|---|---|---|---|---|---|
| `<name>` | `<type>` | Yes/No | `<default>` | <constraint> | <description> |

## Request body

Media type: `application/json`. Schema: <link or name>.

| Field | Type | Required | Default | Constraints |
|---|---|---|---|---|
| `<field>` | `<type>` | Yes/No | `<default>` | <constraint> |

## Responses

| Status | Media type | Body |
|---|---|---|
| `200` | `application/json` | <link to object reference> |

### Errors

| Status | Error code | Meaning | Retryable |
|---|---|---|---|
| `<status>` | `<code>` | <meaning> | Yes/No |

## Idempotency

<Whether repeating the call is safe, and the mechanism (idempotency key, natural idempotency, or none).>

## Rate limits

<Limits that apply to this endpoint, and the response when exceeded.>

## Pagination

<Model, parameters, and how to detect the last page. Delete if not a collection.>

## Side effects

<Resources created, events emitted, webhooks fired, background work queued. Write "None" if there are none.>

## Compatibility

| Version | Change |
|---|---|
| <version> | <added/changed/deprecated> |

## See also

- Task guide: <how-to link>
- Object reference: <reference link>
