<!--
AUTHORING CONTRACT

Delete every section that does not materially serve this report.
Do not publish angle-bracket placeholders or these instructions.

Audit requirements:
- Report functional quality and experience quality SEPARATELY. Do not produce a
  single aggregate score; mode purity is not correctness.
- Every finding needs evidence and an epistemic status (observed / inferred /
  unknown). "Inferred" is allowed; unlabelled inference is not.
- Every finding needs acceptance criteria, or it cannot be turned into work.
- Heuristic script output is a signal to verify, never a verdict.
-->

# Diátaxis audit report

**Scope:** <what was audited, and what was excluded>
**Product/version:** <version the docs were assessed against>
**Sources inspected:** <schemas, code, tests, ADRs, analytics, the docs build>
**Validation performed:** <builds run, link checks, snippets executed, tutorials followed>
**Assumptions:** <inferred reader contracts and anything else assumed>
**Could not verify:** <claims and pages left unchecked, and why>

## Summary

<Short summary of overall documentation health and the most important user-need issues.>

## Findings

| ID | Severity | Area | Finding | User impact | Evidence | Epistemic status | Recommended action | Effort | Dependencies | Acceptance criteria | Owner |
|---|---|---|---|---|---|---|---|---|---|---|---|
| F1 | blocker/high/medium/low | <area> | <what is wrong> | <what goes wrong for the reader> | <exact page, heading, or observed behavior> | observed/inferred/unknown | <concrete fix> | small/medium/large | <required source or related page> | <how to know the fix is complete> | <team> |

## Functional quality (objective)

| Check | Result | Evidence |
|---|---|---|
| Accuracy against source | pass/fail/not checked | <what was compared> |
| Completeness for declared scope | pass/fail/not checked | <coverage diff> |
| Internal consistency | pass/fail/not checked | <where the fact diverges> |
| Version correctness | pass/fail/not checked | <versions stated vs supported> |
| Example validity | pass/fail/not checked | <snippets run> |
| Link validity | pass/fail/not checked | <checker output> |
| Terminology consistency | pass/fail/not checked | <terms sweep> |
| Accessibility | pass/fail/not checked | <headings, alt text, link text> |
| Freshness and ownership | pass/fail/not checked | <owners, last-verified dates> |

## Experience quality (judgement)

Rate strong / adequate / weak / missing / unknown. Every rating needs evidence.

| Check | Rating | Evidence |
|---|---|---|
| Fit to the reader's situation | <rating> | <evidence> |
| Flow | <rating> | <evidence> |
| Findability | <rating> | <evidence> |
| Scannability | <rating> | <evidence> |
| Cognitive load | <rating> | <evidence> |
| Level of detail | <rating> | <evidence> |
| Confidence and trust | <rating> | <evidence> |
| Mode coherence | <rating> | <evidence> |

## Page classification

| Page | Inferred reader need | Current mode | Target mode | Evidence | Action |
|---|---|---|---|---|---|
| `<path>` | <need> | <mode> | <mode> | <evidence> | keep/edit/split/move |

## Boundary issues

### Tutorial/how-to conflation

<Examples and recommended fixes.>

### Reference/explanation conflation

<Examples and recommended fixes.>

## Coverage gaps

- Tutorials: <gap>
- How-to guides: <gap>
- Reference: <gap>
- Explanation: <gap>

## Composite artifacts

<READMEs, FAQs, changelogs, glossaries, runbooks: how they are serving readers. Do not force these into a single mode.>

## First three improvements

1. <Small, independently useful improvement, with its finding ID>
2. <Small improvement>
3. <Small improvement>

## Proposed longer-term structure

```text
<tree>
```

## Review checklist

- [ ] Pages have one primary user need.
- [ ] Titles match modes.
- [ ] Cross-links replace mixed-mode digressions.
- [ ] Reference facts are verified against their source of truth.
- [ ] Navigation reflects user needs.
- [ ] Findings carry evidence, epistemic status, and acceptance criteria.
