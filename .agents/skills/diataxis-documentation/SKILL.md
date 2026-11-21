---
name: diataxis-documentation
description: >-
  Use this skill when creating, rewriting, reviewing, auditing, or organizing
  technical documentation. Apply Diátaxis to learning tutorials, task-oriented
  how-to guides, API/CLI/configuration reference, conceptual explanations,
  documentation architecture, and migrations—even when the user does not name
  Diátaxis. Also use it to turn source code, schemas, tests, design records, or
  existing mixed documentation into accurate user-facing docs. Do not use it for
  generic non-technical copyediting.
license: CC-BY-SA-4.0
compatibility: Core skill needs no special environment. Optional helper scripts in scripts/ require Python 3 (standard library only, no network access).
metadata:
  source: https://diataxis.fr/
---

# Diátaxis Documentation

This skill produces documentation that is **grounded in authoritative evidence, aimed at a specific reader need, validated against the real product, and maintainable in the project where it lives**. Diátaxis supplies the shape; the evidence and validation rules below supply the trustworthiness that Diátaxis explicitly does not.

It is suitable for software documentation, API docs, CLI docs, product docs, internal engineering docs, scientific software docs, and any documentation for a craft or tool.

This skill is vendor-neutral: it follows the [Agent Skills standard](https://agentskills.io/specification) and uses only the common package shape (`SKILL.md`, optional `references/`, optional `assets/`, optional `scripts/`) so it can run in Claude Code, Codex, and Pi.

## Instruction precedence

For documentation-specific choices, follow this order:

1. The user's explicit request.
2. Repository instructions and project-specific documentation standards.
3. Authoritative product sources and maintained terminology.
4. Existing local documentation conventions.
5. This skill's templates and fallback style guidance.

Do not introduce `doc_type` frontmatter, four top-level directories, title patterns, admonition syntax, or link conventions that the project does not already use, unless the user asks for an architectural change.

## Evidence-first authoring workflow

This is the controlling workflow. Mode selection happens inside it, not before it.

Before drafting or materially rewriting documentation:

1. **Establish the reader contract:** audience or role, current situation, goal or question, assumed competence, environment and relevant product version, risks and constraints.
2. **Discover project conventions:** repository instructions, documentation style guide, terminology or glossary, existing navigation and file conventions, documentation build/lint/test commands.
3. **Identify the source of truth for each kind of fact:**
   - public API behavior → schema, implementation, tests, or generated API data
   - CLI behavior → installed CLI help, parser definitions, tests
   - configuration → schema, defaults in code, validation logic
   - UI behavior → current product, UI tests, product specifications
   - design rationale → ADRs, design documents, issue or commit history
   - version support → release metadata and maintained compatibility policy
4. **Record unknowns.** Never fill factual gaps with plausible details.
5. **Choose one primary Diátaxis mode** for the reader's immediate need.
6. **Draft the smallest complete document** that satisfies that need.
7. **Validate the document:** run or compile examples where safe, build the documentation, run existing lint and link checks, compare reference coverage with its source, inspect the rendered result when possible.
8. **Revise until the relevant completion checks pass.**
9. **Report in the work summary:** sources inspected, validation performed, assumptions made, and anything that could not be verified.

Source of truth is defined **per kind of claim**. Code is authoritative for runtime behavior; an ADR may be authoritative for design rationale; a policy document may be authoritative for support guarantees.

### Never

- Never invent defaults, limits, error messages, output, version support, security guarantees, or performance characteristics.
- Do not present inferred design rationale as confirmed rationale.
- Do not leave template placeholders in a publishable document.
- When a claim cannot be verified, omit it, mark the document as a draft, or report the gap separately.
- Do not include the internal evidence ledger in the published page unless the project's documentation conventions call for provenance metadata.

## The reader contract

Establish this before selecting a mode. Keep it internal unless the user asks for a plan or an audit.

```yaml
reader:
  audience: application developer
  situation: integrating the API into an existing service
  immediate_goal: retry failed webhook deliveries safely
  assumed_competence: understands HTTP and the product's authentication
  environment: product 3.x, production deployment
  constraints:
    - cannot lose events
    - cannot stop existing delivery
primary_mode: how-to
```

When the intended audience of an existing document is unclear, **infer and declare** rather than stopping to ask:

1. Inspect surrounding navigation, neighboring pages, terminology, and expected prerequisites.
2. Infer the most likely user need.
3. State the assumption in the audit or work summary.
4. Ask only when different answers would materially change the deliverable **and** repository evidence cannot resolve it.

## Core model

Diátaxis organizes documentation by the user's need, not by the author's mental model of the product.

Ask two questions:

1. Does the content inform **action** or **cognition**?
2. Does it serve **acquisition** of skill or **application** of skill?

| User need | Content informs | User is | Documentation type |
|---|---|---|---|
| Learning | Action | Acquiring skill | Tutorial |
| Goal | Action | Applying skill | How-to guide |
| Information | Cognition | Applying skill | Reference |
| Understanding | Cognition | Acquiring skill | Explanation |

- **Tutorials** are lessons. They guide a learner through a safe, successful learning experience. They are practical, concrete, reliable, and deliberately narrow.
- **How-to guides** are directions for already-competent users at work. They help the user accomplish a real-world task or solve a real-world problem.
- **Reference** is authoritative technical description. It is neutral, factual, structured like the thing it describes, and consulted rather than read.
- **Explanation** is reflective discussion. It provides context, reasons, background, design rationale, trade-offs, and conceptual understanding.

If a document mixes modes, do not simply smooth over the mixture. Identify the competing user needs, split or move the material, and add cross-links.

## Short guidance by mode

### Tutorial

- Say what the learner will make, do, or experience.
- Lead with concrete steps and visible results; every substantial action needs an observable result.
- Use a reliable, controlled path with no choices unless unavoidable.
- Give expected outputs and checks so the learner knows they are on track.
- Keep explanation minimal and link to explanation pages instead.
- Prefer "we will build/create/do..." over promises like "you will learn...".

### How-to guide

- Title it as a task, often "How to ...".
- Focus on a real user goal or problem, not a product feature tour.
- Give a logical sequence of actions, including conditional branches where real-world cases vary.
- Omit teaching, background, and exhaustive option lists; link out instead.
- Assume competence, but warn about risks and prerequisites **before** the actions they qualify.

### Reference

- Describe only: commands, APIs, options, parameters, return values, errors, schemas, configuration keys, limits, guarantees, defaults.
- Mirror the structure of the product, API, CLI, protocol, or system.
- Use standard, repeatable patterns; declare the scope of the page.
- Be accurate, complete, neutral, and concise.
- Include examples only as compact illustrations, not as lessons or task walkthroughs.

### Explanation

- Answer "why?", "what does this mean?", "how should I think about this?", "what trade-offs exist?".
- Make connections across concepts, history, design decisions, alternatives, and implications.
- Distinguish confirmed rationale from inferred rationale.
- Keep the topic bounded; move procedures to how-to guides and facts to reference.

## Composite and record documents

Do not force every artifact into one of the four modes at file level.

For landing pages, READMEs, FAQs, troubleshooting hubs, changelogs, release notes, glossaries, ADRs, runbooks, migration indexes, and generated symbol indexes:

1. Identify the artifact's container or record function.
2. Apply Diátaxis to its individual sections and linked destinations.
3. Keep the container concise and navigational.
4. Do not split content merely to achieve categorical purity.
5. Split when a secondary user need is substantial, interrupts flow, or deserves an independently findable page.

## Definition of done by mode

| Mode | Required completion checks |
|---|---|
| **Tutorial** | Starts from a defined, reproducible state; uses one controlled path; produces meaningful observable results; shows expected output; includes recovery for likely mistakes; avoids irreversible actions or supplies cleanup; has been followed end-to-end from a clean environment. |
| **How-to guide** | Solves a real user goal; states preconditions; places warnings before risky actions; handles meaningful branches; includes verification; includes rollback or recovery when failure would matter; does not become a feature tour or option catalog. |
| **Reference** | Declares its scope; is checked against an authoritative source; uses a consistent entry schema; includes applicable types, defaults, constraints, limits, errors, side effects, compatibility, and deprecation information; contains no unsupported facts. |
| **Explanation** | Answers a bounded conceptual question; provides an accurate mental model; distinguishes fact from interpretation; discusses meaningful trade-offs; does not hide required procedures or exact operational facts; links to sources of action and certainty. |
| **Landing/index page** | Helps readers choose a destination; uses meaningful grouping and descriptive link text; has no orphaned or broken destinations; does not reproduce child-page content. |

## Universal publish gate

Every document must also pass:

- [ ] Correct for the documented version
- [ ] Complete for its declared scope
- [ ] Consistent with project terminology and style
- [ ] Appropriate for its stated audience
- [ ] Free of unresolved placeholders and invented details
- [ ] Examples are valid, safe, and clearly identified as exact or illustrative
- [ ] Links and cross-references resolve
- [ ] Warnings appear before the actions they qualify
- [ ] Images and diagrams have equivalent textual information
- [ ] The documentation build and available checks pass

## Work summary requirements

When you finish a documentation change, report:

- **Sources inspected** — files, schemas, CLI output, tests, ADRs.
- **Validation performed** — commands run, builds, link checks, snippets executed.
- **Assumptions made** — including the inferred reader contract.
- **Unverified or missing** — every claim you could not ground, and what would settle it.

For classification or audits, also report: current mode and intended user need, evidence for the classification, boundary problems, recommended target mode, and the smallest useful next change.

## When to read each reference

- `references/principles.md` — full Diátaxis model, boundaries, and anti-patterns. Read for substantial classification or restructuring work.
- `references/workflows.md` — create/review/refactor/audit flows. Read before multi-page work or a docs PR review.
- `references/checklists.md` — audit rubrics and mode-purity checks. Read when auditing or scoring a documentation set.
- `references/style-guide.md` — **fallback** language, titles, examples, and cross-linking patterns. Project style wins; read this only where the project is silent.
- `references/information-architecture.md` — navigation, landing pages, hierarchies. Read when changing structure or navigation.
- `references/migration-playbook.md` — staged migration of an existing docs set.
- `references/evidence-and-verification.md` — read **before** creating reference material or making exact behavioral, compatibility, security, or version claims.
- `references/document-testing.md` — read when the document contains commands, code, configuration, API requests, UI procedures, or generated output.
- `references/content-lifecycle.md` — read for site audits, migrations, deprecations, versioned docs, release documentation, or ownership planning.
- `references/accessibility-and-global-readers.md` — read when using screenshots, diagrams, tables, directional UI language, or terminology intended for a broad audience.
- `references/reference-patterns.md` — read when writing API, CLI, configuration, schema, environment-variable, or error reference.
- `references/composite-documents.md` — read when the artifact is a README, landing page, FAQ, troubleshooting hub, changelog, glossary, ADR, or runbook.

Templates are in `assets/templates/`; each carries an authoring contract telling you to delete sections that do not serve the document. Worked examples of all four modes for one small product are in `assets/examples/webhooks/`.

Scripts in `scripts/` are optional repository-scale helpers. They use the Python standard library only and do not access the network.

## Repository workflow

1. Inspect the docs tree and existing documentation conventions.
2. Run the evidence-first workflow above. Verify every product fact against a source of truth.
3. For triage, optionally run `python3 scripts/diataxis_audit.py <docs-path>` and `python3 scripts/docs_health.py <docs-path>`. The auditor reports **structural signals and risks**, not verdicts — you make the semantic classification.
4. Propose or make small, reviewable changes unless asked for a larger restructuring.
5. Preserve project style, file naming, build tooling, and link conventions.

## Hard rules

- Do not create four empty top-level sections just because Diátaxis has four modes.
- Do not force every page into a rigid global hierarchy if user needs suggest a different structure.
- Do not combine substantial tutorial and how-to journeys on one page. Brief supporting material is acceptable when it directly preserves the primary mode's flow and does not require the reader to change stance. "Basic vs advanced" is not the distinction.
- Do not mix reference and explanation; "theory" can still serve either work or study.
- Do not bury essential reference facts inside explanation or tutorial text.
- Do not overload tutorials with explanation or options.
- Do not turn how-to guides into product-feature tours.
- Do not present a heuristic score as a verdict, a compliance gate, or a measure of correctness.
