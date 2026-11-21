---
title: "Understanding Beacon delivery and retries"
doc_type: explanation
---

# Understanding Beacon delivery and retries

Every team integrating Beacon eventually asks the same two questions: why did we get that event twice, and why did it arrive out of order? Both follow from one design decision — Beacon delivers **at least once**, not exactly once.

## Why this matters

If you assume exactly-once delivery, your integration will be wrong in production and correct in every test. Duplicates are rare enough to miss in staging and common enough to double-charge a customer once you have real traffic. The cost of assuming wrongly is asymmetric, which is why this page exists at all.

## The mental model

Think of Beacon as a persistent queue per endpoint, not as a caller making a function call.

When something happens in Beacon, an event is written to durable storage first and enqueued for your endpoint second. A delivery worker then takes the event and makes an HTTP request. If it does not see a 2xx response, it puts the event back with a delay. It has no way to know whether your server processed the event and failed to reply, or never processed it at all — those two situations look identical from outside.

Given that ambiguity, there are only two possible policies: retry and risk duplicates, or do not retry and risk loss. Beacon retries.

The consequence is a rule you can design against: **`id` identifies the event; a delivery is just one attempt at it.** The same `id` may arrive many times. Store processed `id`s and ignore repeats, and duplicates stop being a problem you have to think about.

### Where this model breaks down

The queue metaphor is only accurate per endpoint. Two endpoints on the same account are independent queues and can be arbitrarily far apart in time. And the queue is not strictly FIFO under retry: a failed event is re-enqueued behind events that have arrived since. That is the source of most out-of-order surprises.

## Why it was designed this way

Beacon's public design notes record that at-least-once was chosen because the alternative pushes an unsolvable problem onto the sender: exactly-once delivery across a network partition requires the receiver to participate in a distributed transaction, which no webhook receiver does.

The 24-hour retry ceiling appears to be a queue-depth bound rather than a correctness property — nothing in the documented behavior depends on the specific value, and it has changed once before. Treat that as our reading, not as a stated guarantee.

## Ordering

Beacon does not promise ordering, and the retry mechanism makes that visible rather than causing it. An `order.updated` can arrive before the `order.created` it follows if the first attempt at `created` failed.

The usual fix is not to reconstruct order but to stop depending on it: use `created_at` to reject stale state, or re-fetch the current resource from the API when an event arrives and treat the event only as a signal that *something* changed. That second approach costs an extra request and makes ordering irrelevant, which is why it is the common choice at scale.

## Trade-offs

| Approach | Cost | When it fits |
|---|---|---|
| Idempotency key on `id` | One storage lookup per event | Always. This is the baseline. |
| Reject stale events by `created_at` | Requires a per-resource timestamp | State updates where last-write-wins is acceptable |
| Re-fetch on every event | One extra API call per event | Anything where correctness beats latency |
| Reconstruct ordering from a sequence number | Complex, and Beacon exposes no global sequence | Rarely worth it; considered and rejected by most integrations |

## Common misconceptions

### "A 200 means Beacon will never send it again"

It means Beacon recorded this delivery as successful. If your server returned 200 after a network failure lost the response, Beacon retries anyway.

### "Retries mean my endpoint is broken"

A single retry usually means one slow response. Sustained retries mean something is wrong. The distinction is in the pattern, not the presence.

### "Duplicates only happen during incidents"

They also happen when your own response takes just over ten seconds.

## What this means in practice

- Treat `Beacon-Event-Id` as the deduplication key, and store it before doing work.
- Answer fast and do work asynchronously; the ten-second timeout is the main source of avoidable retries.
- Do not build logic that depends on receiving events in order.
- Expect old events during recovery after an outage: a backlog drains in whatever order the queue holds it.

## Related documentation

- The exact headers and fields: [Beacon event payload reference](reference-event-payload.md)
- Handling secrets safely: [How to rotate a Beacon signing secret](how-to-rotate-signing-secret.md)
- Start here if you have not received an event yet: [Tutorial: Receive your first Beacon webhook](tutorial-build-first-receiver.md)
