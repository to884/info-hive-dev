---
title: "Tutorial: Build your first <thing>"
---

<!--
AUTHORING CONTRACT

Delete every section that does not materially serve this document.
Do not publish angle-bracket placeholders or these instructions.
Use the repository's existing frontmatter instead of this example when present.
Record evidence and verification in the agent's work summary, not necessarily
in the published page.

Tutorial-specific requirements:
- The starting state is defined, controlled, and reproducible.
- One path only. No choices, no alternatives, no "you could also".
- Every substantial action has an observable result the learner can check.
- Every "you should see" block is REAL output from an executed run.
- Likely mistakes have recovery text.
- Irreversible actions are avoided, or cleanup is provided.
- This tutorial has been executed end to end from its declared starting state
  before publication. If it has not, it is a draft.
-->

<!--
PLANNING (delete before publishing)
Reader:
Situation:
Desired outcome:
Assumed competence:
Product/version:
Primary mode: tutorial
Authoritative sources:
Validation plan (clean-environment run):
Non-goals:
-->

# Tutorial: Build your first <thing>

In this tutorial, we will <create/build/run> <a concrete outcome>. We will start from <known starting point> and finish with <visible result>.

This tutorial was written and tested against <product> <version> on <platform>.

## Before you start

You need:

- <tool or account>
- <local requirement>
- <sample project or clean environment>

Check that everything is ready:

```bash
<command>
```

You should see output similar to:

```text
<expected output>
```

If you see <common failure>, <recovery>.

## Create the project

First, create <specific object>:

```bash
<command>
```

You should now have:

```text
<file tree or output>
```

Notice that <small concrete observation>.

## Add <first meaningful part>

Open `<file>` and add:

```<language>
<code>
```

Now run:

```bash
<command>
```

You should see:

```text
<expected output>
```

## Make it do something visible

<Continue with small steps. Each step must have an observable result.>

```bash
<command>
```

The output should look like:

```text
<expected output>
```

If you do not see this, check that <likely fix>.

## Check what we built

Run the end-to-end check:

```bash
<command>
```

You should see:

```text
<final visible result>
```

That is the whole thing working. <One sentence naming what the learner just proved.>

## Clean up

<Remove everything the tutorial created, so the learner can run it again from the same starting state.>

```bash
<command>
```

## What happened

We created <short concrete summary>. We used <concept> because <one-sentence explanation>.

For more background, see <link to explanation>.
For exact options, see <link to reference>.

## Next steps

- <How-to guide for a real task>
- <Reference page for exact details>
- <Explanation page for concepts>
