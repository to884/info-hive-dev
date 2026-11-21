# Content lifecycle

Read this for site audits, migrations, deprecations, versioned docs, release documentation, or ownership planning.

Documentation decays because facts move and nobody notices. Lifecycle metadata exists to make decay visible.

## Per-page lifecycle fields

Adopt only what the project already uses, or propose the smallest useful subset. Do not impose frontmatter on a project that has none.

| Field | Purpose | Typical values |
|---|---|---|
| `owner` | Who answers questions and reviews changes | team or role, not a person who may leave |
| `status` | Whether the page can be trusted | draft, published, deprecated, archived |
| `applies_to` | Product versions the page documents | `>=3.2`, `2.x`, `cloud only` |
| `last_verified` | When someone last checked the facts, not last touched the prose | ISO date |
| `source_of_truth` | What must be re-checked when it changes | schema path, ADR id, policy page |
| `review_cadence` | How often the page must be re-verified | per release, quarterly, on schema change |

`last_verified` is the highest-value field and the one most often faked. It means "someone re-checked the claims", not "someone fixed a typo".

## Status transitions

- **draft → published** when the mode's definition of done and the universal publish gate both pass.
- **published → deprecated** when the feature is deprecated. Keep the page, add the deprecation notice at the top, name the replacement, and say when removal happens.
- **deprecated → archived** after removal. Archived pages stay reachable (URLs are cited elsewhere) but are excluded from search and navigation where the platform allows.
- **Delete** only when the page never had readers and nothing links to it.

## Deprecation notices

Put the notice first, before any procedure. A reader who follows three steps and *then* learns the feature is going away has been failed by the page. State: what is deprecated, from which version, when it is removed, what replaces it, and a link to the migration path.

## Redirects and canonical pages

Moving a page is a breaking change to URLs.

- Add a redirect for every moved or renamed page, using the platform's own mechanism.
- Redirect to the closest equivalent, never to the docs home page.
- When splitting a page, redirect the old URL to the piece that kept the original user need, and cross-link the rest from it.
- When two pages cover the same ground, pick one canonical page, reduce the other to a pointer, and redirect if the platform supports it.
- Preserve heading anchors where you can; external sites and issue threads deep-link to them.

## Duplicated facts

A fact repeated in three pages will be wrong in two of them within a year.

- Keep exact facts (defaults, limits, error codes) in **one** reference page and link to it.
- Where a value must appear inline for flow, prefer transclusion/includes if the platform supports it.
- If duplication is unavoidable, record the duplicate locations in the reference page's source-of-truth note so a change updates all copies.

## Stale screenshots and recordings

- Screenshots age faster than prose and cannot be diffed. Use them only where the visual layout is the point.
- Record the product version in the caption or alt text.
- Prefer text for values that change (numbers, ids, names) so they can be updated without re-shooting.
- Where a screenshot carries required information, that information must also exist as text.

## Release gates

Tie documentation to the release, not to good intentions:

- A user-visible change is not shippable without its reference update.
- A new feature needs at least reference plus one how-to answering the goal it exists for; a tutorial only if the feature is an entry point for new users.
- A breaking change needs a migration how-to and a release-note entry.
- Removal of a feature triggers the deprecated → archived transition and redirect work.

## Review cadence

- Re-verify reference on every release that touches its source of truth.
- Re-run tutorials on a fixed cadence and after any change to the starting environment (installer, template repo, default project layout).
- Re-check explanation when the design changes, not when the code changes.
- Audit navigation and landing pages when pages are added or removed, so orphans do not accumulate.

## Ownership

Every page needs a team that would notice if it were wrong. Pages nobody owns should be archived rather than left as an unmaintained trap. Record ownership where the project already tracks it — `CODEOWNERS`, a docs index, or frontmatter — and not in a new parallel system.
