# Worked example: Beacon webhooks

One small fictional product — **Beacon**, a service that delivers webhooks — documented in all four Diátaxis modes, plus a mixed page and its repair.

These are filled-in examples, not templates. Read them to see the judgement calls: what each mode includes, what it refuses to include, and where it links instead.

| File | Mode | The reader need it serves |
|---|---|---|
| [`tutorial-build-first-receiver.md`](tutorial-build-first-receiver.md) | Tutorial | "I have never used this. Give me one safe success." |
| [`how-to-rotate-signing-secret.md`](how-to-rotate-signing-secret.md) | How-to | "I run this in production and I need to rotate the secret without dropping events." |
| [`reference-event-payload.md`](reference-event-payload.md) | Reference | "What exactly is in the payload, and what does this header mean?" |
| [`explanation-delivery-and-retry-model.md`](explanation-delivery-and-retry-model.md) | Explanation | "Why do I sometimes get the same event twice, and how should I think about ordering?" |
| [`mixed-page-before.md`](mixed-page-before.md) | Mixed (the problem) | A real "Webhooks" page trying to serve all four needs at once. |
| [`mixed-page-after/`](mixed-page-after/README.md) | The repair | The same content split into three pages that each serve one need, cross-linked. |

Note what the split does **not** do: it does not create four pages because Diátaxis has four modes. The before-page had no tutorial in it, so the after-set has no tutorial. Content is moved, not manufactured.

Beacon is fictional. Every value in these examples is illustrative. In real work, each of those values would come from the source of truth for its claim type — see `references/evidence-and-verification.md`.
