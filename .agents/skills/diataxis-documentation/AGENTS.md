# AGENTS.md

Guidance for coding agents working in this repository. This file is canonical; `CLAUDE.md` points here so the two cannot drift.

## What this repository is

This is **not an application** — it is a packaged **Agent Skill** that teaches an agent to produce documentation that is grounded in authoritative evidence, aimed at a specific reader need, validated against the real product, and maintainable where it lives. [Diátaxis](https://diataxis.fr/) (tutorial / how-to / reference / explanation) supplies the shape; the evidence and validation rules supply the trustworthiness Diátaxis explicitly does not.

The deliverable is the skill package: instructional Markdown, templates, worked examples, and Python helper scripts.

The package targets the cross-vendor [Agent Skills standard](https://agentskills.io/specification) and must load cleanly in **Claude Code, Codex, and Pi**. That cross-compatibility goal drives most of the constraints below.

## Architecture

Built around **progressive disclosure** — the agent loads the smallest thing first and reads deeper files only when a task needs them:

- `SKILL.md` — the entry point. Frontmatter + core instructions, always loaded. It carries the instruction-precedence order, the evidence-first authoring workflow, the reader contract, per-mode definitions of done, the universal publish gate, composite-document handling, and **an explicit loading condition for every reference file**. Keep it as short as those obligations allow; push detail into `references/`.
- `references/*.md` — depth-on-demand. `principles.md`, `workflows.md`, `checklists.md`, `style-guide.md` (a **fallback**; project style wins), `information-architecture.md`, `migration-playbook.md`, `evidence-and-verification.md`, `document-testing.md`, `content-lifecycle.md`, `accessibility-and-global-readers.md`, `reference-patterns.md`, `composite-documents.md`. Every one of these must be named with a loading condition in `SKILL.md` — `tests/test_package.py` enforces it.
- `assets/templates/*.md` — starter pages. Each begins with an **authoring contract** (delete what does not serve the document; publish no placeholders) and a removable planning block. Consumed by name in `scripts/diataxis_scaffold.py` (`TEMPLATE_FILES`); every template must be reachable from it.
- `assets/examples/webhooks/` — one small fictional product documented in all four modes, plus a mixed page and its repair. Templates show shape; these show judgement.
- `assets/examples/audit-corpus/` — six labeled pages with known audit outcomes (four pure modes, one deliberately mixed, one with insufficient context). Distributed, not repository-only, because the README tutorial runs against it and must work for someone who installed from `manifest.txt`. `tests/test_audit.py` uses the same pages, so the tutorial's expected output and the tests move together.
- `scripts/` — helpers (see below).
- `tests/`, `evals/`, `.github/` — repository-only; never distributed.
- `manifest.txt` — **generated**. Run `python3 scripts/update_manifest.py` after adding or removing a shipped file; CI runs `--check`.

## Scripts

All scripts are **Python 3 standard library only** with **no network access** — a stated compatibility guarantee. Do not add third-party imports or network calls.

Distributed with the skill:

```bash
# Evidence collector: structural signals, named risks, ranked mode hypotheses.
python3 scripts/diataxis_audit.py <docs-path> --format markdown|json
python3 scripts/diataxis_audit.py <docs-path> --include '*.md' --exclude 'api/*' --ignore-generated
python3 scripts/diataxis_audit.py <docs-path> --patterns my-terms.json --fail-on placeholders

# Objective document health: links, orphans, placeholders, alt text, fences, nav.
python3 scripts/docs_health.py <docs-path> --format markdown|json --fail-on error

# Scaffold one page from a bundled template.
python3 scripts/diataxis_scaffold.py <type> "<title>" --out-dir <dir>
```

Repository maintenance only (excluded from `manifest.txt`):

```bash
python3 scripts/validate_package.py        # frontmatter, manifest, pointers, template mapping
python3 scripts/update_manifest.py         # regenerate manifest.txt
python3 scripts/update_manifest.py --check # CI drift check
```

CI also runs the Agent Skills reference validator (`skills-ref validate .`) in its own job, as the specification recommends. That is a third-party check of the same frontmatter rules `validate_package.py` enforces; when the two disagree, the reference implementation is right about the standard and `validate_package.py` should be corrected.

`diataxis_audit.py` is an **evidence collector, not a classifier of record**. It reports `structural_signals`, `risks` with evidence, `mode_hypotheses`, and a `classification_status` of `clear` / `ambiguous` / `insufficient-context`. The numeric field is `signal_separation` — the normalized gap between the top two hand-weighted scores. It is deliberately **not** called `confidence`: it is not a probability that a classification is correct. Never make it a CI compliance gate for mode purity.

Every risk carries a `category`. A `defect` risk is computed without reference to the inferred mode; a `purity` risk depends on it. `--fail-on risks` counts only `defect` risks, so the flag cannot be used as the mode-purity gate the paragraph above forbids. Adding a rule means choosing its category deliberately.

The two scripts are kept apart on purpose: `docs_health.py` reports defects, `diataxis_audit.py` reports signals.

Both are distributed as standalone files, so they cannot import a shared module and duplicate their frontmatter parsing, file discovery, and fence handling. `tests/test_shared_parsing.py` is what keeps the copies honest: change one and the other must change with it. `docs_health.DOC_EXTENSIONS` is deliberately a subset — it resolves Markdown links, so it only handles Markdown.

`diataxis_scaffold.py` emits no `doc_type:` frontmatter unless asked with `--with-doc-type`, and the bundled templates carry none. The skill must not push that convention onto a project that does not already use it.

## Tests

```bash
python3 -m unittest discover -s tests -v
python3 scripts/validate_package.py
python3 scripts/update_manifest.py --check
```

Standard-library `unittest` only, to preserve the no-dependency guarantee. Run them with `unittest discover`, not by executing a module directly: `tests/__init__.py` holds the shared bootstrap (`REPO_ROOT`, the `scripts/` path entry, `AUDIT_CORPUS`) that every module imports. The labeled corpus lives in `assets/examples/audit-corpus/` and is shared with the README tutorial, so its expected output must stay in step with the tests.

## Evals

`evals/` holds the agent-behavior suite: `trigger-queries.json` (activation, both polarities), `behavior-cases.jsonl` (twelve scenarios), `rubric.md`, and `fixtures/`. Run every behavior case **with and without the skill** — the skill-off baseline is what shows whether an instruction earns its tokens. `tests/test_evals.py` checks the suite is well formed; it does not run the agent.

## Conventions and hard constraints

- **Standard frontmatter only.** `SKILL.md` frontmatter must stick to standard fields (`name`, `description`, `license`, `compatibility`, `metadata`), under 1024 characters. No vendor-specific keys — unknown fields can break or get ignored across the three target agents. `validate_package.ALLOWED_FRONTMATTER` is that exact set and `tests/test_shared_parsing.py` pins it to this sentence; widening one without the other is a test failure, on purpose.
- **Skill name is lowercase kebab-case** (`diataxis-documentation`) and avoids vendor-reserved words.
- **The description is the activation signal.** It uses imperative "Use this skill when..." phrasing, covers cases where the user does not name Diátaxis, and states what it is *not* for. Change it only alongside `evals/trigger-queries.json`.
- **License is CC-BY-SA-4.0** (share-alike). This is a derivative/operationalization of Diátaxis by Daniele Procida; preserve attribution in `NOTICE.md` and `README.md`. Do not bundle the upstream source PDF.
- **The content embodies its own rules.** Follow the Diátaxis discipline the skill prescribes, and its evidence rules: do not add a product claim to an example that the example does not support.
- **Do not add more Diátaxis theory.** The model is covered. Additions should improve evidence, validation, lifecycle, or accessibility instead.

## When editing this skill

Changes usually touch several layers together: a behavior change in `SKILL.md` needs a matching update in the relevant `references/` file, possibly a template or example, a test, and a regenerated `manifest.txt`. Prefer the smallest coherent change and keep core → references → templates → examples consistent. Run the tests and `validate_package.py` before committing.
