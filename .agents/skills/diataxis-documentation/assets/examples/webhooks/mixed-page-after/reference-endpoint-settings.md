---
title: "Beacon endpoint settings reference"
doc_type: reference
---

# Beacon endpoint settings reference

Every configurable field on a Beacon webhook endpoint. This page covers endpoint configuration only; the delivered payload is documented in the [event payload reference](../reference-event-payload.md).

Applies to Beacon API version 3.4.

## Settings

| Field | Type | Required on create | Mutability | Default | Constraints |
|---|---|---|---|---|---|
| `url` | string | Yes | updatable | none | Absolute `https://` URL. `http://` is accepted in sandbox only. |
| `enabled_events` | array of string | No | updatable | `["*"]` | Event type names, or `*` for all. Maximum 200 entries. |
| `api_version` | string | No | write-once | account default at creation | A supported payload version, for example `3.4`. |
| `status` | string | No | updatable | `enabled` | One of `enabled`, `disabled`. |
| `description` | string | No | updatable | `null` | Maximum 200 characters. |
| `secrets` | array of string | No | see below | one generated secret | Maximum 2 active. Managed through `beacon endpoints secrets`, not by writing this field. |

## Status values

| Value | Meaning |
|---|---|
| `enabled` | Beacon delivers events to this endpoint. |
| `disabled` | Beacon stops delivering and does not queue. Events occurring while disabled are not backfilled on re-enable. |

Beacon sets `status` to `disabled` automatically after an endpoint returns `410 Gone`.

## Compatibility

| Version | Change |
|---|---|
| 3.4 | `description` added. |
| 3.2 | Second active secret allowed, enabling overlapping rotation. |

## See also

- [How to rotate a signing secret](../how-to-rotate-signing-secret.md)
- [Event payload reference](../reference-event-payload.md)
