---
title: "How to <achieve a specific goal>"
---

<!--
AUTHORING CONTRACT

Delete every section that does not materially serve this document.
Do not publish angle-bracket placeholders or these instructions.
Use the repository's existing frontmatter instead of this example when present.
Record evidence and verification in the agent's work summary, not necessarily
in the published page.

How-to-specific requirements:
- The title names a real user goal, not a product feature.
- Preconditions are stated before the first action.
- Warnings appear BEFORE the action they qualify.
- "Backup or rollback" is MANDATORY when the task can lose data, cause an
  outage, or is otherwise hard to reverse. Delete it only for safe tasks.
- The verification step must fail on a system where the task was not done.
- Do not list every option; link to reference.
-->

<!--
PLANNING (delete before publishing)
Reader:
Situation:
Desired outcome:
Assumed competence:
Product/version:
Primary mode: how-to
Authoritative sources:
Validation plan (which branches exercised, how rollback was tested):
Non-goals:
-->

# How to <achieve a specific goal>

This guide shows how to <achieve result>. It assumes you already know <domain/tool basics>.

## Use this when / do not use this when

Use this guide when:

- <situation>

Do not use this guide when:

- <situation> — see <link to the guide that fits>.

## Before you begin

You need:

- <prerequisite>
- <permission or role>
- <existing resource>

> **Warning:** <data-loss, outage, security, or cost risk, stated before any action>.

## Back up first

<Required when the task is materially risky. Delete this section only for safe tasks.>

```bash
<backup command>
```

Confirm the backup exists before continuing:

```bash
<verification command>
```

## <First action-oriented heading>

<Give the first action.>

```bash
<command>
```

## Choose an approach

<Delete if there is only one path.>

| If | Do this |
|---|---|
| <condition> | <approach, with link if it is a separate guide> |
| <other condition> | <other approach> |

## <Second action-oriented heading>

<Continue the task flow.>

```bash
<command>
```

## Verify the result

Check that <result>:

```bash
<command>
```

Expected result:

```text
<expected output or state>
```

<State how this check fails if the task did not work.>

## Roll back

<Required when the task is materially risky.>

If <failure condition>, restore the previous state:

```bash
<rollback command>
```

Then verify:

```bash
<command>
```

## Recover from a partial change

If the task stopped after <step>, <what state the system is in and how to reach a consistent state>.

## Troubleshooting

### <Symptom>

If <symptom>, check <cause> and do <fix>.

## Related information

- Full option list: <reference link>
- Background and trade-offs: <explanation link>
- Related task: <how-to link>
