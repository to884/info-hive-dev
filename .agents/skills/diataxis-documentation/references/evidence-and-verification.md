# Evidence and verification

Diátaxis governs *fit* — whether a page serves the right user need. It does not supply *functional quality*: accuracy, completeness, consistency, precision. This file covers the part Diátaxis leaves to technical discipline.

Read this before creating reference material or making exact behavioral, compatibility, security, or version claims.

## Source hierarchy by claim type

There is no single "source of truth" for a page. There is one per kind of claim.

| Claim | Authoritative source | Weaker corroboration |
|---|---|---|
| Runtime behavior of an API | Implementation, plus tests that assert the behavior | Generated OpenAPI, existing docs |
| Request/response shape | Schema (OpenAPI/JSON Schema/protobuf) checked against serializer code | Example payloads in docs |
| CLI flags, defaults, exit codes | Argument-parser definition; `--help` from the installed version | Shell history, blog posts |
| Configuration keys and defaults | Config schema, default constants, validation code | Sample config files |
| Limits and quotas | Enforcement code, or a published limits policy | Support answers, changelogs |
| Error messages and codes | The string/constant in source, or an error registry | Screenshots, transcripts |
| UI flow and labels | The running product at a stated version; UI tests | Old screenshots |
| Design rationale | ADRs, design docs, linked issue/PR discussion | Commit messages alone |
| Version support and deprecation | Release metadata and the maintained support policy | README badges |
| Security guarantees | Threat model, security policy, code enforcing the control | Marketing copy |

## Handling source conflicts

1. Prefer the source that *executes*: code and tests beat generated artifacts, which beat prose.
2. Prefer the source the project treats as normative (a schema the server validates against, not a hand-kept copy).
3. When two authoritative-looking sources disagree, do not silently choose. Document the conflict, pick the one you can demonstrate, and report the discrepancy in the work summary — a docs conflict is often a product bug.
4. Never resolve a conflict by averaging or hedging ("usually around 30 seconds").

## Observed versus inferred

Mark every statement to yourself as one of:

- **Observed** — you ran it, read the constant, or executed the test.
- **Derived** — it follows from an observed fact by a stated rule (for example, a default read from the schema).
- **Inferred** — plausible from context but unverified.
- **Unknown** — no source available.

Only observed and derived facts belong in reference. Inferred material may appear in explanation **only** when labelled as interpretation ("the retry ceiling appears to exist to bound queue depth"). Unknowns are reported, not written.

Do not publish the ledger itself unless the project uses provenance metadata.

## Version-specific claims

- State the version the page documents, using the project's own versioning vocabulary.
- Do not describe behavior for versions you have not inspected.
- When behavior changed, say when it changed and what it was, or link the release note — do not silently document only the newest behavior on a page serving older users.
- "Latest" is not a version. Resolve it.

## Illustrative versus observed output

Every code block is one of two things, and the reader must be able to tell:

- **Observed output** — copied from a real run. Do not edit it except to redact secrets and to elide with a marked `...`.
- **Illustrative output** — hand-written to show shape. Say so ("output resembles"), and keep it obviously schematic.

Never paste hand-written output under a heading like "Expected output" in a tutorial. That is the one place a reader will diff character by character.

## Generated reference

Prefer generation when the source supports it (OpenAPI, docstrings, `--help`, JSON Schema).

- Generated pages must say they are generated and name the generator.
- Do not hand-edit generated output; fix the source.
- Hand-written reference next to generated reference must declare which entries it covers, or it will silently rot.
- Compare coverage both ways: entries in the source missing from docs, and entries in docs missing from the source (those are usually removed features).

## Citations and source links

Inside a repository, link the reader to *user-facing* sources (release notes, policy pages), and record internal sources (file paths, test names, ADR ids) in the work summary instead. Deep links into source files age badly in published docs; they are excellent in a PR description.

## Unknowns and incomplete evidence

When you cannot verify a claim, choose one, in this order:

1. **Omit it.** A shorter accurate page beats a complete plausible one.
2. **Scope it down** to what you did verify ("on Linux, with the bundled runtime").
3. **Mark the document a draft** using the project's own status convention.
4. **Report the gap** in the work summary with the exact question and the source that would answer it.

Never close the gap with a plausible sentence. That is the single most damaging failure mode in agent-written documentation, because it is indistinguishable from verified content once published.
