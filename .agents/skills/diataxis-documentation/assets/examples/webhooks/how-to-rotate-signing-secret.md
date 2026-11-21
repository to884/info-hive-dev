---
title: "How to rotate a Beacon signing secret"
doc_type: how-to
---

# How to rotate a Beacon signing secret

This guide shows how to replace the signing secret on a live Beacon endpoint without dropping or failing to verify any event. It assumes you operate the receiving service and can deploy configuration changes to it.

## Use this when / do not use this when

Use this guide when:

- The secret is on a routine rotation schedule.
- You believe the secret may have been exposed.

Do not use this guide when:

- You are changing the endpoint URL. Rotating the secret does not move an endpoint; use the endpoint-move guide instead.
- The endpoint is disabled. Rotation on a disabled endpoint is safe but pointless; re-enable it first.

## Before you begin

You need:

- The endpoint ID (`beacon endpoints list`)
- The `beacon` CLI 3.2 or later, authenticated against the environment you are rotating
- The `webhooks:write` scope on your API key
- The ability to deploy a configuration change to your receiver and roll it back

> **Warning:** Beacon signs each delivery with **one** secret. If you activate a new secret before your receiver accepts it, every delivery fails signature verification and Beacon will retry them for up to 24 hours, after which those events are lost. Follow the overlap order below exactly.

## Add a second secret

Beacon endpoints accept up to two active secrets so that rotation can overlap. Add one:

```bash
beacon endpoints secrets add ep_7f3a
```

Beacon prints the new secret **once**:

```text
Secret added: whsec_NEW...
Active secrets: 2 (whsec_OLD..., whsec_NEW...)
```

Beacon still signs with the old secret at this point. Adding a secret does not change which one signs.

## Accept both secrets in your receiver

Deploy a configuration change so your receiver verifies a request if it matches **either** secret:

```python
def verify(body, header_sig, secrets):
    return any(hmac.compare_digest(sign(body, s), header_sig) for s in secrets)
```

Deploy this before continuing. Confirm it is live:

```bash
beacon events send --endpoint ep_7f3a beacon.ping
beacon events list --endpoint ep_7f3a --limit 1
```

Expected result:

```text
ID              TYPE          STATUS      ATTEMPTS
evt_01J2...     beacon.ping   delivered   1
```

If the status is `failed`, your receiver has not picked up the new configuration. Do not continue — a `failed` ping here means every real event would also fail after the next step.

## Promote the new secret

Tell Beacon to sign with the new secret:

```bash
beacon endpoints secrets promote ep_7f3a --secret whsec_NEW...
```

Both secrets remain active; only the signing secret changes.

## Verify the result

Send a ping and check which secret signed it:

```bash
beacon events send --endpoint ep_7f3a beacon.ping
beacon deliveries describe --endpoint ep_7f3a --limit 1 --format json
```

Expected result:

```json
{ "status": "delivered", "signed_with": "whsec_NEW...", "attempts": 1 }
```

Two things must both be true: `signed_with` names the new secret, and `status` is `delivered`. If `signed_with` still names the old secret, the promote did not apply. If `status` is `failed`, your receiver is not accepting the new secret and you should roll back now.

## Roll back

If deliveries fail after promotion, promote the old secret again:

```bash
beacon endpoints secrets promote ep_7f3a --secret whsec_OLD...
```

Then confirm recovery:

```bash
beacon events send --endpoint ep_7f3a beacon.ping
beacon deliveries describe --endpoint ep_7f3a --limit 1
```

Beacon automatically re-delivers events that failed within the retry window, so events that failed during a short rollback are not lost.

## Remove the old secret

Once you have seen a full retry window (24 hours) with no signature failures, remove the old secret:

```bash
beacon endpoints secrets remove ep_7f3a --secret whsec_OLD...
```

Then remove it from your receiver's configuration and deploy.

## Recover from a partial rotation

If you stopped after adding the second secret, nothing is wrong: two secrets are active and the old one still signs. Either continue from "Promote the new secret", or run `beacon endpoints secrets remove` on the unused new secret.

If you stopped after promoting but before removing, you are in a supported steady state. Finish the removal at your convenience.

## Troubleshooting

### Deliveries fail with `signature_mismatch` immediately after promotion

Your receiver is not accepting the new secret. Roll back, confirm the dual-verification deploy actually shipped, and retry.

### `beacon endpoints secrets add` returns `secret_limit_reached`

The endpoint already has two active secrets, probably from an unfinished rotation. Remove the one that is not signing, then start again.

## Related information

- Every field of the signature header: [Beacon event payload reference](reference-event-payload.md)
- Why retries can deliver an event twice: [Understanding Beacon delivery and retries](explanation-delivery-and-retry-model.md)
