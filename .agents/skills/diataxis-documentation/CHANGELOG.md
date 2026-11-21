# Changelog

All notable changes to this skill package. This project uses date-based releases.

## [Unreleased]

### Code review follow-up

- `diataxis_audit.py` risks now carry a **`category`**: `defect` (computed without reference to the inferred mode) or `purity` (depends on it). `--fail-on risks` counts only `defect` risks, so the flag can no longer act as the mode-purity CI gate the script's own epilog forbids. JSON `schema_version` is now `2.1`.
- The Markdown report says **"wide margin" / "narrow margin"** instead of "strong" / "weak", so the label describes the gap between the top two scores rather than reintroducing the confidence reading `signal_separation` disclaims.
- `validate_package.ALLOWED_FRONTMATTER` is now exactly the documented standard set; the vendor-specific `allowed-tools` and the undocumented `version` no longer pass. A test pins the constant to the sentence in `AGENTS.md`.
- The labeled audit corpus moved from `tests/fixtures/audit/` to **`assets/examples/audit-corpus/`** and is distributed. The README tutorial's checkpoint is now reachable for anyone who installed from `manifest.txt`, and a test fails if the README runs a script against a path the manifest does not ship.
- Templates no longer hard-code `doc_type:` frontmatter, and `diataxis_scaffold.py` emits it only with the new **`--with-doc-type`** flag. The default output no longer imposes a convention the skill tells agents not to introduce.
- Fenced code blocks now follow the CommonMark length rule in both distributed scripts, fixing a page documenting Markdown leaking its code into the prose signals (`diataxis_audit.py`) or out of the code flags (`docs_health.py`).
- New `tests/test_shared_parsing.py` pins the logic that the two standalone scripts must duplicate — frontmatter parsing, ignore sets, fence handling — to identical behaviour, so the copies cannot drift silently.
- CI runs the Agent Skills reference validator (`skills-ref validate`) alongside the repository's own checks, as the specification recommends.
- Internal: per-mode risk rules and suggestions come from one `MODE_RULES` table rather than two parallel `if` cascades; the ambiguity threshold and its evidence string derive from one constant; `ParsedDoc` replaces the four-value clump passed between passes; dead parameters removed; each script exposes `build_parser()` so the tests can read its flags directly instead of monkeypatching `argparse`; the test bootstrap lives once in `tests/__init__.py`.

Evidence-first overhaul, in response to an external review. The operating promise changes from "the agent will organize documentation according to Diátaxis" to "the agent will create or improve documentation that is grounded in authoritative evidence, appropriate to a specific reader need, validated against the real product, and maintainable in the project where it lives."

### Added

- **Evidence-first authoring workflow** in `SKILL.md`, as the controlling loop that mode selection happens inside.
- **Reader contract** established before mode selection, with infer-and-declare handling of ambiguity instead of stopping to ask.
- **Per-mode definitions of done** and a **universal publish gate**.
- **Instruction precedence** order — the user's request, then repository standards, then authoritative sources, then local conventions, then this skill's fallbacks.
- **Composite and record documents** handling for READMEs, landing pages, FAQs, troubleshooting hubs, changelogs, glossaries, ADRs, and runbooks.
- **Work summary requirements**: sources inspected, validation performed, assumptions made, and what could not be verified.
- New references: `evidence-and-verification.md`, `document-testing.md`, `content-lifecycle.md`, `accessibility-and-global-readers.md`, `reference-patterns.md`, `composite-documents.md`. Each has an explicit loading condition in `SKILL.md`.
- Specialized reference templates: API endpoint, API object, CLI command, configuration, environment variables, schema, and error.
- **Authoring contracts** and removable planning blocks in every template.
- `assets/examples/webhooks/` — one fictional product documented in all four modes, plus a mixed page and its repair.
- `scripts/docs_health.py` — objective document-health checks (broken links and anchors, orphans, duplicate titles, missing H1, unresolved placeholders, malformed fences, empty sections, missing alt text, vague link text, missing navigation targets).
- `scripts/validate_package.py` and `scripts/update_manifest.py` — package validation and a generated `manifest.txt`.
- `tests/` — standard-library `unittest` suite with a labeled audit fixture corpus.
- `evals/` — trigger queries, twelve behavior cases, a grading rubric, and fixtures.
- CI workflow running the tests, package validation, and manifest drift check.

### Changed

- **Description** rewritten to imperative "Use this skill when..." phrasing, covering requests that do not name Diátaxis and stating what the skill is not for.
- `diataxis_audit.py` is now an **evidence collector**: it reports structural signals, named risks with evidence, ranked mode hypotheses, and a `classification_status` of `clear` / `ambiguous` / `insufficient-context`. Added leading-frontmatter parsing, tilde and indented fences, MDX handling, basic reStructuredText structure, deterministic `--max-files`, `--include` / `--exclude` / `--ignore-generated`, configurable pattern sets, declared-`doc_type` comparison, a versioned JSON schema, and a `--fail-on` exit policy.
- The documentation-set rubric no longer produces an aggregate 0–24 score. Functional-quality checks (objective) and experience checks (judgement, rated strong/adequate/weak/missing/unknown with evidence) are reported separately.
- The hard rule against mixing tutorial and how-to now forbids combining substantial *journeys*, allowing brief supporting material that preserves the primary mode's flow.
- `style-guide.md` is explicitly a fallback; project-specific style wins.
- `audit-report.md` findings carry severity, user impact, evidence, epistemic status, recommended action, effort, dependencies, acceptance criteria, and owner.
- `doc-index.md` expanded to a real portfolio table with audience, source of truth, versions, last-verified date, and risk.
- README rewritten: the tutorial now uses labeled fixtures with distinguishable results, and installation covers per-runtime activation and troubleshooting.
- `AGENTS.md` is canonical and `CLAUDE.md` points at it, ending the drift that produced "Codex, Codex, and Pi".

### Fixed

- `diataxis_audit.py` treated any `key: value` line as frontmatter.
- `diataxis_audit.py` applied `--max-files` before sorting, so capped results were non-deterministic.
- `diataxis_scaffold.py` raised `IndexError` on an empty how-to title.
- `diataxis_scaffold.py` inserted titles into double-quoted YAML without escaping quotes or backslashes.
- `slugify()` discarded all non-ASCII characters, silently producing `untitled.md` for non-Latin titles; it now preserves Unicode letters and asks for `--filename` when no usable slug remains.
