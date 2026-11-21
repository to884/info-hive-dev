# Composite and record documents

Read this when the artifact is a README, landing page, FAQ, troubleshooting hub, changelog, glossary, ADR, runbook, migration index, or generated symbol index.

Diátaxis has four modes. A documentation *set* has more artifact kinds than that. Some artifacts are containers (they route the reader elsewhere) or records (they log what happened). Forcing them into a single mode makes them worse.

## The rule

1. Identify the artifact's container or record function.
2. Apply Diátaxis to its individual sections and linked destinations.
3. Keep the container concise and navigational.
4. Do not split content merely to achieve categorical purity.
5. Split when a secondary user need is substantial, interrupts flow, or deserves an independently findable page.

The test for splitting is not "does this paragraph belong to a different mode?" It is "would a reader arrive looking for this, and be poorly served by finding it here?"

## README

A README is a composite landing artifact with a strict ordering constraint: the reader decides within a screen whether to keep going.

A good structure, in order:

1. What this is, in one or two sentences (explanation, minimal).
2. Who it is for / what problem it solves.
3. Install or run it — the shortest real path (how-to, compressed).
4. A single smallest working example (tutorial-flavoured, but not a lesson).
5. Links out: full documentation, tutorial, how-to index, reference, explanation.
6. Project matter: status, versioning, licence, contributing, security.

Do not turn a README into four files. Do split out anything that grows: a full option table (→ reference), a real getting-started lesson (→ tutorial), an architecture discussion (→ explanation).

For a repository with no docs site, the README is the documentation; apply the mode boundaries to its *sections* and keep the exact facts in one section rather than sprinkled through prose.

## Landing and index pages

Purpose: help the reader choose a destination.

- Group destinations by user need, not by product component, unless the components *are* how users think.
- Every link needs a snippet that helps the reader choose — a title alone is not enough.
- Do not reproduce child-page content; a landing page that answers the question stops the reader from reaching the page that answers it fully.
- Keep lists short enough to scan; group beyond about seven items.
- No orphans: every page reachable, every link resolving.

## FAQ collections

An FAQ is a symptom, and often a useful one: it is a list of questions the documentation did not answer where the reader looked.

- Treat each entry as a routing stub: answer briefly, then link to the page that owns the answer.
- Move any entry that has grown into a procedure to a how-to guide; leave the question as a link.
- Move any entry that is a fact to reference.
- If several entries cluster around one concept, that is a missing explanation page.
- Keep questions in the reader's words, not the product's.

## Troubleshooting hubs

Organize by **symptom**, because that is all the reader has.

- Entry shape: symptom → likely cause → check → fix (or link to the how-to that fixes it).
- Link the error identifier so a pasted error string is findable.
- Keep the diagnosis here and the long procedures in how-to guides.
- A troubleshooting entry that keeps recurring is a product or reference defect; report it rather than documenting around it.

## Changelogs and release notes

These are **records**, not modes. Do not restructure them.

- Changelogs are terse and complete, ordered by version, aimed at readers diffing two versions.
- Release notes are selective and framed around user impact, and may carry explanation and links to migration how-tos.
- Neither is the place for reference facts: link to the reference page that now documents the new behavior.
- A breaking change entry must link to the migration path.

## Glossaries

A glossary is reference for vocabulary.

- One entry per concept, defined neutrally, in the project's own terms.
- Do not explain design rationale in a glossary; link to the explanation page.
- Point synonyms and deprecated terms at the canonical entry rather than defining them twice.

## ADRs and design records

An ADR is a record of a decision at a point in time — it is *not* an explanation page, and must not be edited to stay current.

- Preserve the ADR as written; supersede it with a new ADR instead of rewriting it.
- When the decision is still in force, write an explanation page that carries the current mental model and cites the ADR.
- An ADR is an authoritative source for *why*, and only for the moment it was written.

## Runbooks

A runbook is an operational how-to for a reader who is often under time pressure and may be half-awake.

- Preconditions, blast radius, and rollback at the top, not the bottom.
- Exact commands, no choices, no teaching.
- Verification after every destructive step.
- Escalation path and who to notify.
- Keep the reasoning out; link to the explanation for anyone who reads it later.

## Migration indexes

A container listing per-version migration how-tos. Keep it a table (from → to → guide → breaking changes) and let each guide carry the procedure.

## Generated symbol indexes

API symbol dumps (Javadoc, Sphinx autodoc, TypeDoc) are generated reference with no curation.

- Do not hand-edit them.
- They do not satisfy a reference need on their own: readers still need a curated, task-shaped reference page for the interfaces that matter.
- Improve them at the source — the docstrings — and treat docstring quality as reference quality.
