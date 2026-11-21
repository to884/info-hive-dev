---
title: "Beacon event payload reference"
doc_type: reference
---

# Beacon event payload reference

The JSON body and HTTP headers of every webhook Beacon delivers. This page covers the delivery envelope and the signature headers. It does not cover the per-type contents of `data`, which are documented with each event type.

Applies to Beacon API version 3.4. Payloads are versioned per endpoint; an endpoint pinned to 3.3 receives the 3.3 envelope.

## Request

```http
POST /your-path HTTP/1.1
Content-Type: application/json
Beacon-Signature: t=1714646100,v1=5257a869e7...
Beacon-Event-Id: evt_01HZX8QK3M7VYB2N4C6D8EFGHJ
Beacon-Delivery-Attempt: 1
```

## Headers

| Header | Type | Always present | Description |
|---|---|---|---|
| `Beacon-Signature` | string | Yes | Comma-separated key=value pairs. `t` is the Unix timestamp used in the signed payload; `v1` is the hex HMAC-SHA256 of `"{t}.{raw body}"` using the endpoint's signing secret. |
| `Beacon-Event-Id` | string | Yes | The event's `id`. Identical across retries of the same event. |
| `Beacon-Delivery-Attempt` | integer | Yes | 1 for the first delivery; increments on each retry. |
| `Content-Type` | string | Yes | Always `application/json`. |

## Body

| Field | Type | Nullable | Description |
|---|---|---|---|
| `id` | string | No | Event identifier, prefix `evt_`, 30 characters. Stable across retries. |
| `type` | string | No | Event type, in `resource.action` form. See the event type index. |
| `api_version` | string | No | Payload version this body conforms to, for example `3.4`. |
| `created_at` | string | No | RFC 3339 timestamp, always UTC, when the event occurred — not when it was delivered. |
| `livemode` | boolean | No | `false` for sandbox events, `true` for production events. |
| `data` | object | No | Type-specific contents. Documented per event type. |
| `data.previous` | object | Yes | Present only on `*.updated` events. Contains the prior values of changed fields, and only those fields. |

## Constraints

| Constraint | Value |
|---|---|
| Maximum body size | 256 KiB |
| Signature validity window enforced by Beacon | None — the window is chosen by the receiver |
| Recommended receiver tolerance | 300 seconds |
| Delivery timeout | 10 seconds to first byte of response |

## Response contract

| Receiver response | Beacon behavior |
|---|---|
| `2xx` | Delivery recorded as `delivered`. |
| `410 Gone` | Endpoint disabled immediately; no retries. |
| Any other status | Delivery recorded as `failed`; retried per the retry schedule. |
| No response within 10 seconds | Delivery recorded as `failed`; retried. Beacon does not cancel the request on your side. |

## Errors

Beacon does not return errors to the receiver; failures are recorded on the delivery. Delivery failure reasons:

| Reason | Cause | Retried |
|---|---|---|
| `timeout` | No response within 10 seconds | Yes |
| `connection_error` | TLS or TCP failure | Yes |
| `http_error` | Non-2xx status other than 410 | Yes |
| `endpoint_disabled` | Endpoint disabled before the attempt | No |

## Example

```json
{
  "id": "evt_01HZX8QK3M7VYB2N4C6D8EFGHJ",
  "type": "order.created",
  "api_version": "3.4",
  "created_at": "2024-05-02T10:15:00Z",
  "livemode": true,
  "data": {
    "order": { "id": "ord_9f2", "amount": 1250, "currency": "usd" }
  }
}
```

## Compatibility

| Version | Change |
|---|---|
| 3.4 | `api_version` added to the body. |
| 3.3 | `Beacon-Delivery-Attempt` header added. |
| 3.2 | `v0` signature scheme removed. Endpoints must use `v1`. |

## See also

- Verifying signatures in practice: [How to rotate a Beacon signing secret](how-to-rotate-signing-secret.md)
- Why the same `id` can arrive twice: [Understanding Beacon delivery and retries](explanation-delivery-and-retry-model.md)
