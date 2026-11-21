---
title: "How to diagnose failing Beacon deliveries"
doc_type: how-to
---

# How to diagnose failing Beacon deliveries

This guide shows how to find out why Beacon deliveries to your endpoint are failing, starting from the symptom you can see. It assumes you operate the receiving service.

## Before you begin

You need:

- The endpoint ID (`beacon endpoints list`)
- The `deliveries:read` scope on your API key
- Access to your receiver's logs

## Find the failure reason

```bash
beacon deliveries list --endpoint ep_7f3a --status failed --limit 20
```

Expected result:

```text
EVENT           ATTEMPT  REASON              STATUS
evt_01J2...     3        timeout             failed
```

The `REASON` column decides which section below applies. Every reason is listed in the [event payload reference](../reference-event-payload.md#errors).

## If the reason is `timeout`

Beacon waits 10 seconds for the first byte of your response.

1. Check your receiver's request duration for that path.
2. Move any work that is not needed to answer — database writes, downstream calls, sending mail — into a background job.
3. Return 2xx as soon as the event is durably recorded.

Verify by sending a ping and confirming a single attempt:

```bash
beacon events send --endpoint ep_7f3a beacon.ping
beacon deliveries list --endpoint ep_7f3a --limit 1
```

`ATTEMPT` must be `1` and `STATUS` must be `delivered`.

## If the reason is `http_error`

Read the status your endpoint returned:

```bash
beacon deliveries describe <delivery_id> --format json
```

| Status returned | Usual cause |
|---|---|
| `404` | The endpoint URL points at a path your router does not serve. |
| `401` or `403` | Your own middleware is rejecting Beacon; webhook paths usually need to bypass session auth. |
| `500` | Your handler raised. Check your logs for the event ID in `Beacon-Event-Id`. |

## If signature verification fails

Signature mismatches surface as `401`/`403` in `http_error`, or in your own logs.

1. Confirm you are verifying the **raw** request body, not a re-serialized parse. This is the most common cause.
2. Confirm you are using the endpoint's current signing secret. If a rotation is in progress, verify against both — see [How to rotate a signing secret](../how-to-rotate-signing-secret.md).
3. Confirm your framework is not stripping or lower-casing the `Beacon-Signature` header.

## If the endpoint was disabled

```bash
beacon endpoints describe ep_7f3a
```

If `status` is `disabled`, your endpoint returned `410 Gone` at some point. Fix the receiver, then re-enable:

```bash
beacon endpoints update ep_7f3a --status enabled
```

> **Warning:** Events that occurred while the endpoint was disabled are not backfilled. Replay them explicitly if you need them.

## Verify the result

```bash
beacon deliveries list --endpoint ep_7f3a --status failed --since 1h
```

Expected result: no rows.

## Related information

- Response contract and failure reasons: [event payload reference](../reference-event-payload.md)
- Why retries happen at all: [delivery and retries](../explanation-delivery-and-retry-model.md)
