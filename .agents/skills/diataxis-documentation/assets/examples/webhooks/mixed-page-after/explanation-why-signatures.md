---
title: "Why Beacon signs webhook requests"
doc_type: explanation
---

# Why Beacon signs webhook requests

A webhook receiver has a problem an API client does not: anyone who learns your URL can POST to it. Beacon's answer is to sign every request, rather than to authenticate the connection. That choice is worth understanding, because it determines what your receiver has to do and what it can safely skip.

## The problem being solved

Your endpoint is a public HTTP URL. Obscurity is not a control — URLs leak through logs, proxies, browser history, and screenshots. So the receiver needs some way to establish that a request really came from Beacon and was not altered on the way.

## Why not the obvious alternatives

**IP allowlists** require the sender to have stable addresses. Beacon's delivery workers scale up and down and move between regions, so a published address range would either be enormous or would break during scaling events. It also fails the moment either side sits behind a proxy or a load balancer that rewrites the source.

**Mutual TLS** authenticates the connection rather than the message, and it makes the receiver responsible for certificate distribution, expiry, and rotation. For a receiver that is a single small HTTP handler, that is a large operational burden for a property that a shared secret already provides. Beacon's design notes record mTLS as considered and rejected on that basis; it remains available on enterprise plans where the operational machinery already exists.

**Bearer tokens in a header** would work, but they are only as safe as the transport and are trivially replayed if a request is ever captured. A signature over the body plus a timestamp gives you replay protection and integrity in the same primitive.

## What signing gives you

The signature covers the timestamp and the exact bytes of the body. That means it survives proxies, it detects tampering, and — because the timestamp is inside the signed material — it lets you reject requests that are too old to be plausible.

It also means your receiver must verify against the **raw** body. This is the single most common integration bug: a framework parses JSON, the code re-serializes it, key order or whitespace changes, and the signature no longer matches. Nothing is wrong with the signature; the bytes are simply not the bytes that were signed.

## What signing does not give you

- It does not tell you the request is *new*. That is your timestamp tolerance, and choosing it is your decision, not Beacon's.
- It does not tell you the event has not been delivered before. That is [delivery and retries](../explanation-delivery-and-retry-model.md).
- It does not protect a secret you have leaked. That is [rotation](../how-to-rotate-signing-secret.md).

## Related documentation

- Exact header format and fields: [event payload reference](../reference-event-payload.md)
- Rotating the secret safely: [how to rotate a signing secret](../how-to-rotate-signing-secret.md)
