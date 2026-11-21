---
title: "Webhooks"
doc_type: landing-page
---

# Webhooks

Beacon notifies your application by POSTing an event to a URL you own, instead of you polling the API.

## Get started

- [Receive your first webhook](../tutorial-build-first-receiver.md) - a 10-minute lesson that ends with a real event printed in your terminal.

## Set up and operate an endpoint

- [Rotate a signing secret](../how-to-rotate-signing-secret.md) - replace a secret with no dropped events.
- [Diagnose failing deliveries](how-to-diagnose-failing-deliveries.md) - work back from timeouts, signature mismatches, and 404s.

## Look up exact details

- [Event payload reference](../reference-event-payload.md) - the body, the headers, size limits, and the response contract.
- [Endpoint settings reference](reference-endpoint-settings.md) - every configurable field, its type, and its default.

## Understand the behavior

- [Delivery and retries](../explanation-delivery-and-retry-model.md) - why an event can arrive twice or out of order.
- [Why Beacon signs requests](explanation-why-signatures.md) - the reasoning behind signatures rather than mTLS or IP allowlists.
