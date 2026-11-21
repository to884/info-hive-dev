---
title: "Understanding <topic>"
---

<!--
AUTHORING CONTRACT

Delete every section that does not materially serve this document. Most
explanations need three or four of these sections, not all of them.
Do not publish angle-bracket placeholders or these instructions.
Use the repository's existing frontmatter instead of this example when present.
Record evidence and verification in the agent's work summary, not necessarily
in the published page.

Explanation-specific requirements:
- The page answers ONE bounded conceptual question.
- Confirmed rationale (ADR, design doc, maintainer statement) is distinguished
  from inferred rationale. Never present inference as confirmed.
- Say where the mental model stops being accurate.
- Discuss alternatives that were actually considered, and label merely
  conceivable alternatives as such.
- No procedures; link to how-to. No exact fact tables; link to reference.
-->

<!--
PLANNING (delete before publishing)
Reader:
Situation:
Question this page answers:
Assumed competence:
Product/version:
Primary mode: explanation
Authoritative sources (ADRs, design docs, issues):
Confirmed vs inferred rationale:
Non-goals:
-->

# Understanding <topic>

<Open with the core idea, tension, or question this explanation resolves.>

## Why <topic> matters

<Explain the user-facing or system-facing significance.>

## The mental model

<Give the reader a way to think about the topic. Use a diagram or analogy if it helps; provide a text equivalent for any diagram.>

Evidence for this model: <what in the system behaves this way, and where you can observe it>.

### Where this model breaks down

<Name the cases the model does not cover, so the reader knows when to stop trusting it.>

## How it works

<Unfold the mechanism at a conceptual level. Avoid turning this into a procedure.>

## Why it was designed this way

<Confirmed rationale, with its source: "ADR-014 records that...".>

<Inferred rationale, labelled: "The constraint appears to exist because...". Do not present inference as confirmed.>

## Trade-offs and alternatives

<Compare approaches. Distinguish alternatives that were considered and rejected from alternatives that are merely conceivable.>

## Common misconceptions

### <Misconception>

<Clarify.>

## What this means in practice

<Explain how this understanding affects decisions — what to watch, what to expect, what to avoid. Keep task steps out; link to how-to guides.>

## Related documentation

- Try it: <tutorial link>
- Apply it: <how-to link>
- Exact details: <reference link>
