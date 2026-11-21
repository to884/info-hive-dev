---
title: "Queue configuration reference"
doc_type: reference
---

# Queue configuration reference

Every configurable field on a queue. This page covers queue configuration only.

Applies to demo 1.2.

## Fields

| Name | Type | Required | Default | Constraints | Description |
|---|---|---|---|---|---|
| `name` | string | Yes | none | 1-64 characters | Queue identifier. |
| `region` | string | No | `us-east-1` | a supported region | Storage region. |
| `retention` | duration | No | `24h` | `1h`-`336h` | How long undelivered messages are kept. |
| `max_size` | integer | No | `262144` | bytes, maximum `1048576` | Maximum message size. |
| `dead_letter` | string | No | `null` | queue name | Destination for exhausted messages. |

## Errors

| Error | Cause | Retryable |
|---|---|---|
| `queue_exists` | A queue with this name exists | No |
| `region_unavailable` | The region is not enabled | No |
| `quota_exceeded` | Queue count limit reached | No |

## Compatibility

| Version | Change |
|---|---|
| 1.2 | `dead_letter` added. |
| 1.1 | `retention` maximum raised. |
