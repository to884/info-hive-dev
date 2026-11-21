# The repair

`../mixed-page-before.md` was one "Webhooks" page serving four different readers at once: someone with no receiver yet, someone configuring an endpoint, someone looking up a header, and someone trying to understand duplicates. Each of them had to read past the other three.

## What moved where

| Material in the before-page | Went to | Why |
|---|---|---|
| "Getting started" walkthrough | The existing [tutorial](../tutorial-build-first-receiver.md) | It was an untested sketch of a lesson that already exists properly elsewhere. Merged, not duplicated. |
| Endpoint settings table | `reference-endpoint-settings.md` | Exact facts a reader looks up; the table was also missing types, defaults, and constraints. |
| Signature header format | The existing [payload reference](../reference-event-payload.md) | It belongs with the other headers, not on a second page. |
| Rotation paragraph | The existing [rotation how-to](../how-to-rotate-signing-secret.md) | It was a procedure compressed into one sentence, with the ordering warning buried at the end. |
| "Why we sign instead of mTLS" | `explanation-why-signatures.md` | Design rationale — the one genuinely explanatory passage on the page. |
| Retries and ordering | The existing [delivery model explanation](../explanation-delivery-and-retry-model.md) | Same topic, already covered in depth. |
| Troubleshooting | `how-to-diagnose-failing-deliveries.md` | Symptom-first task material for someone with a live problem. |
| "Polling is still supported…" aside | Deleted from this page | Off-topic here; it belongs on the polling page, which owns that comparison. |

## What the repair did not do

- It did not create four pages to match four modes. The before-page had no real tutorial content worth keeping, so nothing new was written to fill a tutorial slot.
- It did not split every paragraph by mode. The landing page keeps one orienting sentence of explanation because it preserves the reader's flow.
- It did not invent facts to complete the settings table. Types and defaults were read from the endpoint schema; two constraints that could not be verified were left out and reported rather than guessed.

## The result

- [`landing-webhooks.md`](landing-webhooks.md) — a short container that routes each reader to the right page.
- [`reference-endpoint-settings.md`](reference-endpoint-settings.md) — new.
- [`explanation-why-signatures.md`](explanation-why-signatures.md) — new.
- [`how-to-diagnose-failing-deliveries.md`](how-to-diagnose-failing-deliveries.md) — new, organized by the symptom the reader can see.
- Three existing pages absorbed the rest.

The old URL redirects to `landing-webhooks.md`, which is the page that kept the original need: "I am here to find out about webhooks."
