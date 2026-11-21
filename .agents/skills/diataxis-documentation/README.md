# Diátaxis Documentation Skill

A cross-compatible [Agent Skill](https://agentskills.io/specification) for technical documentation. [Diátaxis](https://diataxis.fr/) — tutorial, how-to, reference, explanation — supplies the shape. The skill adds the part Diátaxis explicitly leaves to technical discipline: evidence, validation, lifecycle, and accessibility.

Its promise is not "the agent will organize documentation according to Diátaxis." It is:

> The agent will create or improve documentation that is grounded in authoritative evidence, appropriate to a specific reader need, validated against the real product, and maintainable in the project where it lives.

This README is itself arranged with Diátaxis. Jump to the part that matches what you need right now:

| If you want to… | Go to | Diátaxis mode |
|---|---|---|
| understand what the skill is and why it works this way | [Understand the skill](#understand-the-skill) | Explanation |
| follow a guided first success | [Tutorial: read your first audit](#tutorial-read-your-first-audit) | Tutorial |
| install it or carry out a specific task | [How-to guides](#how-to-guides) | How-to |
| look up files, paths, or script options | [Reference](#reference) | Reference |

## Understand the skill

### What it is

This repository is not an application. It is a packaged Agent Skill: instructional Markdown, templates, worked examples, and three optional Python helper scripts. When loaded, it gives an agent a working command of Diátaxis — and, more importantly, a controlling workflow that makes it establish who the reader is, find the source of truth for each claim, validate what it wrote, and report what it could not verify.

### What it helps you do

- write a new page in the right mode for a real reader
- turn source code, schemas, `--help` output, tests, or design records into accurate user-facing docs
- rewrite a mixed-mode page and split out the parts that belong elsewhere
- audit a docs tree, separating objective defects from judgement calls
- design user-first documentation architecture
- migrate an existing documentation set in small, reviewable steps
- review a documentation pull request with specific edits rather than a lecture

### Why evidence comes before mode

Diátaxis is a theory of *fit*: it tells you whether a page serves the right need. It says plainly that it cannot supply accuracy, completeness, consistency, or precision — those need separate technical discipline.

A well-shaped page with an invented default is worse than a clumsy page with correct facts, because the shape makes it look trustworthy. So the skill puts the evidence-first workflow above mode selection, prohibits filling factual gaps with plausible detail, and requires the agent to report its sources, its validation, its assumptions, and its unknowns.

### Why it is vendor-neutral

The package uses only the common Agent Skills shape — `SKILL.md` plus optional `references/`, `assets/`, and `scripts/` — and only standard frontmatter fields, under the 1024-character limit. The skill name is lowercase kebab-case and avoids vendor-reserved words. It loads in Claude Code, Codex, and Pi; each runtime discovers it the same way and ignores frontmatter it does not recognize.

### How it is organized

The skill follows *progressive disclosure* — and `SKILL.md` states **when** to read each deeper file, not merely what each one contains:

- `SKILL.md` carries the core instructions and is always loaded.
- `references/` holds depth-on-demand, each with an explicit loading condition.
- `assets/templates/` provides starter pages, each opening with an authoring contract.
- `assets/examples/webhooks/` shows one small product documented in all four modes, plus a mixed page and its repair. Templates show shape; examples show judgement.
- `scripts/` adds optional, repository-scale helpers.

## Tutorial: read your first audit

This short lesson gives you one guaranteed success with the auditor, and teaches you the thing that actually matters about it: how to tell a clear signal from an ambiguous one. All you need beforehand is Python 3 and Git.

We will use the Claude Code location; the other runtimes work the same way.

1. Clone the skill into your skills directory:

   ```bash
   git clone https://github.com/jrajasekera/diataxis-documentation.git \
     ~/.claude/skills/diataxis-documentation
   ```

2. Move into the freshly cloned skill:

   ```bash
   cd ~/.claude/skills/diataxis-documentation
   ```

3. Run the auditor against the labeled corpus that ships with the skill. `assets/examples/audit-corpus/` holds six small pages with known answers; its own `README.md` describes each one, so exclude it from the scan:

   ```bash
   python3 scripts/diataxis_audit.py assets/examples/audit-corpus \
     --exclude README.md --format markdown
   ```

4. Read the table. You should see exactly this:

   ```text
   | File | Title | Declared | Signals suggest | Separation | Risks |
   |---|---|---|---|---:|---:|
   | `intentionally-mixed.md` | Queues |  | ambiguous: how-to + explanation | 0.23 | 2 |
   | `pure-explanation.md` | Understanding queue durability | explanation | explanation (wide margin) | 1.00 | 0 |
   | `pure-how-to.md` | How to migrate a queue to a new region | how-to | how-to (wide margin) | 0.90 | 0 |
   | `pure-reference.md` | Queue configuration reference | reference | reference (wide margin) | 0.95 | 0 |
   | `pure-tutorial.md` | Tutorial: Send your first message | tutorial | tutorial (wide margin) | 0.86 | 0 |
   | `unknown-purpose.md` | Notes |  | insufficient-context | 0.00 | 1 |
   ```

**Checkpoint.** Six rows, and three distinguishable outcomes: four pages whose top mode matches their filename and wins by a wide margin, one `ambiguous` result naming both competing needs, and one `insufficient-context` result where the page does not say enough to have a mode. If you see that, the skill is installed and its scripts run.

Notice what the last two rows are telling you. `intentionally-mixed.md` is not a failure of the script — it is a page genuinely serving two needs, and the script's job is to say so rather than to pick. `unknown-purpose.md` has no mode to find. That is why the output is called *signals*, and why the numeric column is `Separation` rather than "Confidence": it measures the gap between the top two scores, not the probability of being right. The same care applies to the parenthetical — "wide margin" says the runner-up was far behind, not that the answer is right.

Now run the other script on the same tree:

```bash
python3 scripts/docs_health.py assets/examples/audit-corpus
```

You should see a health report with no errors. That is the second half of the picture: `docs_health.py` reports defects that are true or false, while `diataxis_audit.py` reports signals you have to judge.

Where to go next:

- To audit your own documentation, see [Audit a documentation tree](#audit-a-documentation-tree).
- To ask the agent to act on what an audit finds, see [Invoke the skill in a session](#invoke-the-skill-in-a-session).

## How-to guides

### Install the skill

Clone the repository into your agent's skills directory. For Claude Code:

```bash
git clone https://github.com/jrajasekera/diataxis-documentation.git \
  ~/.claude/skills/diataxis-documentation
```

For Codex or Pi, change only the target directory — see [Installation and activation by runtime](#installation-and-activation-by-runtime). If you would rather not use Git, download the files and copy the `diataxis-documentation/` folder into the same directory.

To register the skill with Pi *without* copying it, point Pi at an existing skills directory in `~/.pi/settings.json` (or a project `.pi/settings.json`):

```json
{
  "skills": ["~/.claude/skills"]
}
```

### Fix a skill that does not appear

Do not reach for "restart the agent" first; current runtimes detect skill changes without it.

1. Confirm the location. The skill directory must contain `SKILL.md` at its top level, and its name must match the skill name (`diataxis-documentation`).
2. Validate the package:

   ```bash
   python3 scripts/validate_package.py
   ```

   This checks the frontmatter fields, the frontmatter size limit, the kebab-case name, and that every path `SKILL.md` points at exists. A malformed frontmatter block is the most common reason a runtime silently skips a skill.
3. Ask for it explicitly, using your runtime's syntax from the table below. If explicit invocation works but automatic activation does not, the problem is the `description` field, not the installation.
4. For a project-level install, confirm the project is trusted by the runtime — untrusted projects do not load project skills.
5. Only if all of that checks out, start a fresh session.

### Update an installed skill

```bash
cd ~/.claude/skills/diataxis-documentation
git pull
```

### Invoke the skill in a session

Ask for the skill by name and state the documentation task, or trigger it explicitly with your runtime's syntax.

```text
Use the diataxis-documentation skill to audit docs/ and recommend the first five improvements.
```

```text
Use diataxis-documentation to rewrite this page as a how-to guide and move the explanation and reference material into separate stubs.
```

```text
Document this CLI subcommand from the parser and the tests. Tell me what you could not verify.
```

### Audit a documentation tree

```bash
python3 scripts/diataxis_audit.py docs/ --format markdown
```

Useful filters:

```bash
python3 scripts/diataxis_audit.py docs/ --include '*.md' --exclude 'api/generated/*' --ignore-generated
```

Use `--format json` for machine-readable output. Every risk carries a `category`: a `defect` risk is computed without reference to the inferred mode, and a `purity` risk depends on it. `--fail-on risks` counts only `defect` risks, so it cannot become a mode-purity gate — gating on a purity risk would turn a heuristic into a rule, and the script refuses to offer it. `--fail-on placeholders` is likewise safe, because an unresolved placeholder is a defect rather than a judgement.

### Check documentation health

```bash
python3 scripts/docs_health.py docs/ --fail-on error
```

This is the one that belongs in CI. It reports broken links and anchors, orphan pages, duplicate titles, missing H1s, unresolved placeholders, malformed fences, empty sections, images without alt text, vague link text, and navigation entries pointing at missing files — all of which are true or false regardless of Diátaxis.

### Adapt the auditor to your terminology

The built-in patterns are English and product-neutral. To audit a translated docs set, or one with its own vocabulary, supply your own:

```json
{
  "title": { "tutorial": [["\\btutoriel\\b", 6]], "how-to": [["^\\s*comment\\b", 7]], "reference": [], "explanation": [] }
}
```

```bash
python3 scripts/diataxis_audit.py docs/ --patterns my-terms.json
```

Any of `title`, `body`, and `heading` may be supplied; the rest fall back to the built-ins.

### Scaffold a new page from a template

```bash
python3 scripts/diataxis_scaffold.py how-to "How to rotate API keys" --out-dir docs/how-to
python3 scripts/diataxis_scaffold.py cli-command-reference "demo queue create" --out-dir docs/reference
```

The script deliberately refuses to create four empty mode sections. Every template opens with an authoring contract instructing you to delete the sections that do not serve the document — a template is a starting point, not a checklist to fill in.

### Run the repository's own checks

```bash
python3 -m unittest discover -s tests -v
python3 scripts/validate_package.py
python3 scripts/update_manifest.py --check
```

After adding or removing a distributed file, regenerate the manifest:

```bash
python3 scripts/update_manifest.py
```

## Reference

### Package layout

```text
diataxis-documentation/
  SKILL.md              core instructions, always loaded
  references/           depth-on-demand, each with a loading condition in SKILL.md
  assets/templates/     starter pages with authoring contracts
  assets/examples/      one product documented in all four modes, plus a repair
  scripts/              optional Python helpers
  tests/                unittest suite and labeled fixtures (not distributed)
  evals/                agent-behavior eval suite (not distributed)
  manifest.txt          generated list of distributable files
```

### SKILL.md frontmatter fields

| Field | Value or purpose |
|---|---|
| `name` | Skill identifier; lowercase kebab-case (`diataxis-documentation`). |
| `description` | Activation signal. Imperative "Use this skill when…" phrasing, covering requests that do not name Diátaxis, and stating what the skill is not for. |
| `license` | `CC-BY-SA-4.0`. |
| `compatibility` | Core skill needs no special environment; scripts require Python 3, standard library only. |
| `metadata` | Holds `source: https://diataxis.fr/`. |

No vendor-specific keys are used, and the block stays under the 1024-character limit.

### Installation and activation by runtime

| Runtime | Explicit activation | Personal skills directory | Project skills directory |
|---|---|---|---|
| Claude Code | `/diataxis-documentation` | `~/.claude/skills/` | `.claude/skills/` |
| Codex | `$diataxis-documentation`, or the skills selector | `~/.agents/skills/` | `.agents/skills/` |
| Pi | `/skill:diataxis-documentation` | `~/.pi/agent/skills/`, `~/.agents/skills/` | `.pi/skills/`, `.agents/skills/` (after the project is trusted) |

Pi and Codex both read `~/.agents/skills/`, so one install there covers both. Runtime details change; check your runtime's current documentation if a path does not work.

### Reference files and when they load

| File | Read it when |
|---|---|
| `references/principles.md` | Doing substantial classification or restructuring work. |
| `references/workflows.md` | Doing multi-page work or reviewing a docs PR. |
| `references/checklists.md` | Auditing or assessing a documentation set. |
| `references/style-guide.md` | The project has no style guidance of its own. It is a fallback. |
| `references/information-architecture.md` | Changing structure or navigation. |
| `references/migration-playbook.md` | Migrating an existing documentation set. |
| `references/evidence-and-verification.md` | Before writing reference, or any exact behavioral, compatibility, security, or version claim. |
| `references/document-testing.md` | The document contains commands, code, configuration, API requests, UI procedures, or generated output. |
| `references/content-lifecycle.md` | Site audits, migrations, deprecations, versioned docs, release docs, ownership. |
| `references/accessibility-and-global-readers.md` | Screenshots, diagrams, tables, directional UI language, or a broad or translated audience. |
| `references/reference-patterns.md` | Writing API, CLI, configuration, schema, environment-variable, or error reference. |
| `references/composite-documents.md` | The artifact is a README, landing page, FAQ, troubleshooting hub, changelog, glossary, ADR, or runbook. |

### Templates

| Template | Scaffold type |
|---|---|
| `tutorial.md` | `tutorial` |
| `how-to-guide.md` | `how-to` |
| `explanation.md` | `explanation` |
| `reference.md` | `reference` |
| `api-endpoint-reference.md` | `api-endpoint-reference` |
| `api-object-reference.md` | `api-object-reference` |
| `cli-command-reference.md` | `cli-command-reference` |
| `configuration-reference.md` | `configuration-reference` |
| `environment-variables-reference.md` | `environment-variables-reference` |
| `schema-reference.md` | `schema-reference` |
| `error-reference.md` | `error-reference` |
| `landing-page.md` | `landing-page` |
| `audit-report.md` | `audit-report` |
| `doc-index.md` | `doc-index` |

### `diataxis_audit.py`

Collect Diátaxis structural signals, named risks, and ranked mode hypotheses. Output is evidence, not a verdict.

```text
python3 scripts/diataxis_audit.py PATHS [PATHS ...]
    [--format {markdown,json}] [--max-files N]
    [--include GLOB] [--exclude GLOB] [--ignore-generated]
    [--patterns FILE] [--fail-on {never,risks,placeholders}]
```

| Argument | Description |
|---|---|
| `PATHS` | One or more files or directories to audit. |
| `--format {markdown,json}` | Output format. Defaults to `markdown`. |
| `--max-files N` | Maximum files to scan, applied after sorting so results are deterministic. Defaults to 500. |
| `--include GLOB` | Only audit files matching this glob. Repeatable. |
| `--exclude GLOB` | Skip files matching this glob. Repeatable. |
| `--ignore-generated` | Skip files whose first 20 lines mark them as generated. |
| `--patterns FILE` | JSON file overriding the built-in `title` / `body` / `heading` pattern sets. |
| `--fail-on {never,risks,placeholders}` | Exit non-zero on the named condition. Defaults to `never`. `risks` counts only `defect`-category risks; mode-purity risks never affect the exit code. |

JSON output carries `schema_version` (currently `2.1`) and one object per file with `path`, `title`, `declared_doc_type`, `classification_status`, `candidate_modes`, `mode_hypotheses`, `signal_separation`, `scores`, `structural_signals`, `risks`, `missing_context`, and `suggestions`.

`classification_status` is one of `clear`, `ambiguous`, or `insufficient-context`. `signal_separation` is the normalized gap between the top two hand-weighted scores — **not** a probability that the classification is correct. The Markdown report says "wide margin" or "narrow margin" for the same reason: it describes how far ahead the top mode was, not how likely it is to be right.

Each entry in `risks` is `{"rule", "category", "evidence"}`, where `category` is `defect` (mode-independent) or `purity` (depends on the inferred mode).

File-format support: Markdown and MDX are parsed structurally; reStructuredText gets basic structural support (over/underline headings, directives, literal blocks, enumerated lists); `.txt` is scanned as text only.

### `docs_health.py`

Objective document-health checks. Knows nothing about Diátaxis modes.

```text
python3 scripts/docs_health.py PATH [--format {markdown,json}] [--fail-on {never,error,any}]
```

| Check | Severity |
|---|---|
| `broken-link`, `broken-anchor` | error |
| `missing-h1` | error |
| `unresolved-placeholder` | error |
| `malformed-fence` | error |
| `image-without-alt` | error |
| `nav-target-missing` | error |
| `multiple-h1`, `heading-level-jump` | warning |
| `duplicate-heading`, `duplicate-title` | warning |
| `empty-section` | warning |
| `vague-link-text` | warning |
| `orphan-page` | warning |

### `diataxis_scaffold.py`

Create one Diátaxis page from a bundled template.

```text
python3 scripts/diataxis_scaffold.py TYPE "Title" [--out-dir DIR] [--filename NAME] [--force]
                                     [--with-doc-type]
```

| Argument | Description |
|---|---|
| `TYPE` | One of `tutorial`, `how-to`, `reference`, `explanation`, `api-endpoint-reference`, `api-object-reference`, `cli-command-reference`, `configuration-reference`, `environment-variables-reference`, `schema-reference`, `error-reference`, `landing-page`, `audit-report`, `doc-index`. |
| `Title` | Page title. Must not be empty. Non-Latin titles are preserved in the generated filename; if no usable slug remains, the script asks for `--filename` rather than writing `untitled.md`. |
| `--out-dir DIR` | Output directory. |
| `--filename NAME` | Output filename. Defaults to a slugified title with `.md`. |
| `--force` | Overwrite an existing file. |
| `--with-doc-type` | Also emit a `doc_type:` frontmatter field. Off by default — the skill does not ask a project to adopt that convention. |

### Repository-only scripts

Not distributed with the skill.

| Script | Purpose |
|---|---|
| `scripts/validate_package.py` | Frontmatter fields and size, kebab-case name, every path `SKILL.md` points at, template mapping, manifest correctness. |
| `scripts/update_manifest.py` | Regenerate `manifest.txt`; `--check` fails on drift. |

### Guarantees

All three distributed scripts use the Python standard library only and make no network calls.

## License and attribution

This skill is an original operationalization and paraphrased summary of Diátaxis, based on the framework by Daniele Procida (published at <https://diataxis.fr/>). It is licensed under [CC-BY-SA-4.0](LICENSE.md); attribution details are in [`NOTICE.md`](NOTICE.md).

This package is not affiliated with or endorsed by Daniele Procida.
