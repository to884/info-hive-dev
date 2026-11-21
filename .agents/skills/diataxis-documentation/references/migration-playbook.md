# Diátaxis migration playbook

Use this playbook to migrate an existing documentation set toward Diátaxis without disrupting users or maintainers.

## Migration principles

- Start from user needs, not from the four labels.
- Preserve useful content wherever possible.
- Avoid a big-bang restructure unless the current site is unusable and the user explicitly asks for it.
- Make changes that are independently valuable.
- Keep redirects and search behavior in mind.
- Validate technical accuracy during migration; moving content often exposes stale facts.
- Treat page titles as user-facing promises.

## Phase 1: Inventory

Create a page inventory with:

- path
- title
- current section
- likely Diátaxis mode
- primary user need
- mixed-mode signals
- traffic or importance if known
- source-of-truth dependencies
- proposed action

Example:

```markdown
| Path | Current title | Likely mode | Issue | Proposed action |
|---|---|---|---|---|
| docs/getting-started.md | Getting started | Tutorial + how-to | learning path includes production deployment | split |
| docs/api/users.md | Users API | Reference | missing errors and rate limits | enrich |
| docs/scaling.md | Scaling | Explanation + how-to | concept page contains procedure | split |
```

Optional heuristic inventory:

```bash
python scripts/diataxis_audit.py docs/ --format markdown > diataxis-audit.md
```

Use the script output to focus human review; do not rely on it as final classification.

## Phase 2: Identify high-value fixes

Prioritize pages that are:

- highly visited
- entry points for new users
- support burden sources
- release blockers
- technically risky if misunderstood
- obvious mixed-mode pages
- stale reference sources

Good first fixes:

- split a tutorial/how-to hybrid
- extract a reference table from a task guide
- create a real task title for a vague guide
- add missing expected output to a tutorial
- move conceptual rationale out of reference
- group a long landing-page list

## Phase 3: Define target conventions

Before moving many pages, define conventions.

### Naming conventions

Example:

```text
tutorials/build-your-first-<thing>.md
how-to/<verb>-<object>.md
reference/<object-or-interface>.md
explanation/<topic>.md
```

### Frontmatter conventions

If the docs system supports frontmatter, consider fields such as:

```yaml
title: How to rotate API keys
doc_type: how-to
audience: operators
status: draft
```

Keep frontmatter compatible with the site's generator.

### Review conventions

Add a docs PR checklist:

```markdown
- [ ] The page has one primary user need.
- [ ] The title matches the mode.
- [ ] Tutorial/how-to/reference/explanation boundaries are preserved.
- [ ] Exact facts are verified against source of truth.
- [ ] Cross-links replace mixed-mode digressions.
```

## Phase 4: Split mixed pages

Use the following split patterns.

### Getting started hybrid

Before:

```text
Getting started
- product overview
- install locally
- build first app
- deploy to production
- configuration options
```

After:

```text
Tutorial: Build your first app
How to deploy to production
Configuration reference
Understanding the product architecture
```

### Feature guide hybrid

Before:

```text
Caching
- what caching is
- enable caching
- cache settings table
- trade-offs
```

After:

```text
How to enable caching
Cache configuration reference
Understanding cache freshness
```

### API guide hybrid

Before:

```text
Users API
- authentication concepts
- create a user walkthrough
- endpoint list
- error handling philosophy
```

After:

```text
Users API reference
How to create a user
Understanding API authentication
Understanding error handling
```

## Phase 5: Move exact facts to reference

When content appears in more than one place, decide whether it is a fact. Facts belong in reference.

Move these to reference:

- defaults
- limits
- parameter definitions
- CLI flags
- endpoint schemas
- error codes
- environment variables
- return values
- compatibility matrices
- version notes

Then update task and learning pages to link to the reference.

## Phase 6: Move reasons to explanation

Move these to explanation:

- design rationale
- historical context
- trade-offs
- mental models
- architecture diagrams
- conceptual background
- comparisons with alternatives
- “why this works” material

Then update tutorials and how-to guides to include only the short explanation needed at that point.

## Phase 7: Preserve and improve flow

After moving content, reread each page in its mode.

### Tutorial flow check

- Does action start early?
- Does each step build on the previous one?
- Are results visible?
- Are errors anticipated?
- Are side topics removed?

### How-to flow check

- Does the sequence match real work?
- Are prerequisites before steps?
- Are warnings before risky actions?
- Are branches close to the decisions they affect?
- Is verification included?

### Reference flow check

- Are entries consistent?
- Can users scan quickly?
- Are exact facts easy to find?
- Does the structure match the product?

### Explanation flow check

- Does the topic unfold logically?
- Are concepts connected?
- Are examples illuminating rather than procedural?
- Is the topic bounded?

## Phase 8: Redirects and search

Redirects, canonical pages, deprecation notices, and ownership are covered in depth in `content-lifecycle.md`.

For moved pages:

- add redirects where supported
- keep old slugs as aliases if the platform supports them
- update internal links
- update sidebar/navigation files
- update search metadata if the project uses it
- avoid deleting high-traffic pages without a replacement

If search indexing is important, choose titles that match user queries:

- users search “how to rotate API keys”, not “Credential lifecycle”.
- users search “environment variables”, not “Runtime customization surface”.

## Phase 9: Measure and iterate

After migration, watch:

- support questions
- search queries with no clicks
- pages with high exits
- docs feedback
- broken links
- stale generated reference
- onboarding success
- PR review friction

Use data to choose the next one-step improvement.

## Migration output format

When asked for a migration plan, produce:

```markdown
# Diátaxis migration plan

## Summary

[one paragraph]

## Current issues

- [issue]

## Proposed target structure

[tree]

## Page moves and splits

| Current page | Target | Action | Notes |
|---|---|---|---|

## First three PRs

1. [small PR]
2. [small PR]
3. [small PR]

## Review checklist

[checklist]

## Risks and mitigations

[risks]
```

## Migration anti-patterns

Avoid:

- Creating empty sections.
- Renaming everything before improving anything.
- Moving content without updating links.
- Treating Diátaxis labels as more important than user mental models.
- Splitting pages so aggressively that users must click constantly.
- Duplicating reference facts across tutorials and how-to guides.
- Leaving conceptual material orphaned because it is not urgent.
- Using Diátaxis as a compliance framework rather than a guide to better docs.

## Minimal migration strategy

When time is limited:

1. Keep the existing structure.
2. Add `doc_type` labels or comments internally.
3. Fix the most harmful mixed-mode pages.
4. Rename only pages where title mismatch causes user confusion.
5. Add links to separate modes.
6. Create landing pages later.

This is still a valid Diátaxis application. The goal is better documentation, not diagram compliance.
