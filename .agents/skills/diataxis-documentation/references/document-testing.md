# Document testing

Read this when the document contains commands, code, configuration, API requests, UI procedures, or generated output.

A documentation change is not done when it reads well. It is done when it has been exercised.

## 1. Find the project's own checks

Look before inventing anything:

- A docs build: `mkdocs.yml`, `docusaurus.config.js`, `conf.py` (Sphinx), `book.toml`, `.readthedocs.yaml`, an Astro/Starlight or Next.js docs app.
- Task runners: `Makefile`, `justfile`, `package.json` scripts, `tox.ini`, `noxfile.py`.
- Linters: `vale.ini`/`.vale.ini`, `markdownlint`, `remark`, `textlint`, `cspell`, `lychee`/`linkchecker`, `mdbook test`.
- CI workflow files, which usually name the canonical commands.

Run what exists. Do not add a new tool to a project as part of a documentation change unless asked.

## 2. Build the docs

Run the project's build and read the warnings, not just the exit code. Broken cross-references, unknown directives, and missing images usually surface as warnings that a green build hides.

If there is no build, at minimum render the changed Markdown mentally against the project's flavor: tables, admonitions, and code fences differ between MkDocs, Sphinx-MyST, Docusaurus, and GitHub.

## 3. Run lint and link checks

- Style/prose lint with the project's config, never with your own preferences.
- Link check internal links at minimum. Verify anchors, not just files: a link to `page.md#old-heading` breaks silently when a heading is renamed.
- External links: check that they resolve, but do not treat a transient failure as a docs defect.

## 4. Execute the code

For each snippet, decide: is it safe to run here?

| Snippet | Action |
|---|---|
| Pure computation, read-only commands, `--help`, `--dry-run` | Run it. Paste real output. |
| Local build/test commands | Run it in a scratch directory. |
| Creates local state | Run it, then clean up (see below). |
| Mutates shared or remote state, costs money, deletes data | Do **not** run it. Verify the syntax against the parser/schema and mark output as illustrative. |
| Requires credentials you do not have | Do not fabricate a run. Say so in the work summary. |

Prefer the project's existing snippet-testing mechanism when one exists (`pytest --doctest-glob`, `mdbook test`, `cargo test --doc`, tested example files included by transclusion).

## 5. Tutorial test: clean environment, top to bottom

A tutorial that has not been executed end-to-end from its declared starting state is not finished.

1. Start from the state the tutorial declares — fresh directory, fresh container, fresh project.
2. Follow only what is written. Do not use knowledge the page does not give the reader.
3. Record where you had to guess, where output differed, and where a step failed.
4. Every place you needed something the page did not say becomes an edit.
5. Confirm that each "you should see" block matches the real output character for character.
6. Confirm the cleanup section actually returns the environment to its starting state.

## 6. How-to verification, safely

- Verify preconditions are sufficient by attempting the task with only those preconditions met.
- Exercise each branch you document, or mark unexercised branches in the work summary.
- Test the *verification step* — it must fail when the task has not been done. A verification that passes on an untouched system is worse than none.
- Test the rollback path for anything destructive. Rollback is the step readers reach while already in trouble.

## 7. Reference completeness comparison

Mechanically diff the page against its source:

- Extract the names from the source (schema properties, parser flags, config keys, error constants).
- Extract the names documented on the page.
- Report both differences: undocumented entries, and documented entries that no longer exist.
- Spot-check types, defaults, and required/optional against the source rather than against the previous docs.

`scripts/docs_health.py` finds structural defects (broken links, placeholders, missing headings); it does not know your product. Coverage comparison is manual or project-specific.

## 8. Inspect the rendered result

Where a preview is available, look at the page:

- Do tables overflow?
- Are admonitions rendered, or emitted as literal text?
- Do code blocks have the right language and no accidental prompt characters that break copy-paste?
- Are images present, sized sanely, and captioned?

## 9. Clean up

- Remove scratch directories, containers, test resources, and temporary credentials you created.
- Revert configuration you changed on the machine.
- Never leave a half-created remote resource behind; say so immediately if you cannot remove one.

## Report

In the work summary, state exactly which of these ran, which passed, and which you skipped and why. "Docs build passes" and "I did not run the deploy command against production" are both useful; silence is not.
