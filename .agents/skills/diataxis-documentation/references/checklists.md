# Diátaxis checklists and rubrics

Use these checklists for audits, reviews, and self-checks.

These cover mode and structure. They do not replace the per-mode definitions of done and the universal publish gate in `SKILL.md`, which every page must pass regardless of mode.

## Compass checklist

For each page or section, answer:

- What is the user's immediate need?
- Is the user at study or at work?
- Does the page guide action or provide knowledge?
- Which mode is primary?
- Which mode is secondary, if any?
- Does the title signal the primary mode?
- Does the opening paragraph set the correct expectation?
- Does the page contain blocks that belong somewhere else?
- What is the smallest useful change?

## Mode classification signals

| Signal | Tutorial | How-to guide | Reference | Explanation |
|---|---|---|---|---|
| Title | “Tutorial”, “Build your first...” | “How to...”, task verbs | “API”, “CLI”, “Options”, object name | “Concepts”, “Overview”, “Why”, “Architecture” |
| Reader | Learner | Competent practitioner | Practitioner checking facts | Practitioner reflecting |
| Structure | One controlled path | Task sequence with possible branches | Entries, tables, schemas, definitions | Prose, diagrams, comparisons |
| Voice | Guiding, reassuring | Direct, practical | Neutral, terse | Discursive, interpretive |
| Examples | Part of the lesson | Used to complete task | Compact illustrations | Used to explain ideas |
| Should avoid | choices, long explanations | teaching, exhaustive facts | opinions, task flow | procedures, hidden facts |

## Tutorial checklist

A tutorial should:

- [ ] Define a concrete thing the learner will make, do, or experience.
- [ ] State assumptions and setup clearly.
- [ ] Use one reliable path.
- [ ] Avoid optional branches and alternatives.
- [ ] Start action early.
- [ ] Produce visible results early and often.
- [ ] Show expected output or observable effects.
- [ ] Tell the learner what to notice.
- [ ] Use “we” where it reinforces guided learning.
- [ ] Keep concepts short and link to explanation.
- [ ] Keep facts minimal and link to reference.
- [ ] Include recovery hints for likely mistakes.
- [ ] End by naming what the learner accomplished.
- [ ] Be tested from a clean environment.

Red flags:

- [ ] “You will learn...” is the main promise.
- [ ] The first action appears late.
- [ ] It offers multiple tools, platforms, or approaches.
- [ ] It assumes expert setup knowledge.
- [ ] It contains long sections titled “Background”, “Theory”, or “Reference”.
- [ ] It cannot be completed reliably.
- [ ] It causes irreversible side effects without a safe sandbox.

## How-to guide checklist

A how-to guide should:

- [ ] Address a real user goal or problem.
- [ ] Have a task title, preferably “How to ...”.
- [ ] Define scope: when to use it and when not to.
- [ ] State prerequisites and risks.
- [ ] Assume competence without omitting task-critical details.
- [ ] Provide ordered steps that match the user's workflow.
- [ ] Include conditional branches for meaningful real-world variation.
- [ ] Keep explanation short and action-serving.
- [ ] Link to reference for options, parameters, and complete lists.
- [ ] Link to explanation for design rationale or conceptual background.
- [ ] End at a practical completion point.

Red flags:

- [ ] It is organized around a product feature rather than a user goal.
- [ ] It teaches fundamentals before doing the task.
- [ ] It contains a full API/CLI/options reference.
- [ ] It has no branches despite real-world variability.
- [ ] It is a vague “guide” or “overview” with no concrete goal.
- [ ] It starts with “What is...” or “Why...” and stays there.

## Reference checklist

Reference should:

- [ ] Be accurate against the source of truth.
- [ ] Be complete for its declared scope.
- [ ] Mirror the structure of the product, API, CLI, schema, or system.
- [ ] Use repeatable entry patterns.
- [ ] List names, types, defaults, constraints, limits, returns, errors, and version notes where relevant.
- [ ] Keep prose neutral and factual.
- [ ] Include warnings where incorrect use is risky.
- [ ] Include compact examples when they clarify use.
- [ ] Avoid task sequences except short usage forms.
- [ ] Avoid conceptual discussion except minimal clarifying notes.

Red flags:

- [ ] Entries differ in structure for no reason.
- [ ] Important defaults or limits are missing.
- [ ] It tells a story instead of describing.
- [ ] It explains design rationale at length.
- [ ] It contains numbered task steps.
- [ ] Examples become multi-step lessons.
- [ ] It is generated but not checked for usability or completeness.

## Explanation checklist

Explanation should:

- [ ] Be about a bounded topic.
- [ ] Answer “why”, “what this means”, or “how to think about it”.
- [ ] Provide context, background, causes, constraints, and implications.
- [ ] Connect the topic to other relevant ideas.
- [ ] Discuss alternatives and trade-offs.
- [ ] Use examples to illuminate, not to instruct.
- [ ] Admit perspective or judgement when helpful.
- [ ] Link to how-to guides for procedures.
- [ ] Link to reference for exact facts.
- [ ] Stay readable away from the product interface.

Red flags:

- [ ] It contains sequential instructions.
- [ ] It is the only place an operational fact is documented.
- [ ] It becomes an unbounded essay.
- [ ] It is mostly tables, parameters, or definitions.
- [ ] It avoids the real “why” question.
- [ ] It tries to teach by doing; that is tutorial material.

## Landing page checklist

A landing page should:

- [ ] Orient the reader to the material inside.
- [ ] Explain what each group of pages helps the reader do or understand.
- [ ] Use short grouped lists rather than one long list.
- [ ] Keep groups to a comfortable size, often around seven items or fewer.
- [ ] Include snippets that help users choose a page.
- [ ] Reflect user needs, not just filesystem order.
- [ ] Avoid empty sections.
- [ ] Avoid a page that is only a raw table of contents unless a mechanical index is the right tool.

## Mixed-mode checklist

For every page, scan for these mixed-mode patterns:

- [ ] Tutorial contains “advanced options”, “alternatives”, or long conceptual background.
- [ ] How-to guide contains “What is...” sections that do not directly serve the task.
- [ ] How-to guide contains full option, parameter, endpoint, or class tables.
- [ ] Reference contains “Step 1...” or “How to...” content.
- [ ] Reference contains design rationale or historical context.
- [ ] Explanation contains command sequences or procedural steps.
- [ ] Explanation contains tables of exact defaults, limits, or errors that belong in reference.
- [ ] Landing page lists more than a few items without grouping.

For each checked item, decide whether to move, link, shorten, or split.

## Documentation-set assessment

Do not produce a single aggregate score. Mode purity is not correctness, and a number invites a compliance gate the framework cannot support. Assess two things separately, and require evidence for every rating.

### Part 1: functional-quality checks (objective)

These can be checked against the world. Each is pass / fail / not-checked, with the check named.

| Check | What to verify | How |
|---|---|---|
| Accuracy against source | Exact claims match the authoritative source for that claim type | Read schema/parser/tests; see `evidence-and-verification.md` |
| Completeness for declared scope | Every entry in the source appears; every documented entry still exists | Two-way coverage diff |
| Internal consistency | The same fact has the same value everywhere it appears | Grep the value across the tree |
| Version correctness | Pages state the versions they document and describe that version | Compare with release metadata |
| Example validity | Snippets run, or are marked illustrative | Execute where safe; see `document-testing.md` |
| Link validity | Internal links and anchors resolve; no orphan pages | Docs build, link checker, `scripts/docs_health.py` |
| Terminology consistency | One term per concept; glossary respected | Term sweep against the glossary or UI |
| Accessibility | Headings, link text, alt text, table structure | See `accessibility-and-global-readers.md` |
| Freshness and ownership | Pages have an owner and a real last-verified date | See `content-lifecycle.md` |

### Part 2: experience checks (judgement)

These require informed judgement and must not be disguised as measurement. Rate each **strong / adequate / weak / missing / unknown**, and cite the page or passage that justifies the rating.

| Check | Question |
|---|---|
| Fit | Does the page serve the situation its reader is actually in? |
| Flow | Can the reader move through it without stalling or backtracking? |
| Findability | Would a reader with this need arrive here — from navigation, search, or a link? |
| Scannability | Can a reader locate the part they need without reading the whole page? |
| Cognitive load | Is the reader asked to hold more in mind than the task requires? |
| Level of detail | Is detail proportionate to the need, or padded/starved? |
| Confidence and trust | Does the page give the reader reason to believe it? |
| Mode coherence | Does the page serve one primary user need? |

Use `unknown` honestly. "Findability: unknown — no analytics and no navigation entry found" is a finding; a guessed `adequate` is not.

### Reporting

Report the two parts separately, and lead with functional-quality failures: a beautifully shaped page with a wrong default is worse than a clumsy page with correct facts. For each finding, record severity, user impact, evidence, epistemic status, recommended action, effort, dependencies, and acceptance criteria — the fields in `assets/templates/audit-report.md`.

## Smallest useful next actions

When stuck, choose one:

- Rename a page so the title matches its mode.
- Add expected output to a tutorial step.
- Remove one optional branch from a tutorial.
- Move one option table from a how-to guide to reference.
- Add one missing default or error to reference.
- Move one “why” paragraph from reference to explanation.
- Add one conceptual link from tutorial to explanation.
- Split one long landing-page list into groups.
- Add a task-oriented intro to a how-to guide.
- Add “when to use this” to a how-to guide.

## Review comment snippets

Use precise comments:

- “This section interrupts the tutorial’s learning path. Move it to an explanation page and link it after the learner sees the result.”
- “This how-to guide needs a real-world goal in the title. Consider `How to ...`.”
- “This table is reference material. Keep only the options used in this task and link to the full reference.”
- “This API entry is becoming explanatory. Keep the facts here and move the rationale to a concept page.”
- “This explanation contains a procedure. Split it into a how-to guide and link back for background.”
- “This page appears to be both a tutorial and a deployment guide. Choose one primary need or split it.”
