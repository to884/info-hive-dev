# Diátaxis workflows

Every workflow here runs **inside** the evidence-first authoring workflow in `SKILL.md`: establish the reader contract, discover project conventions, identify the source of truth per claim, draft, validate, and report sources/validation/assumptions/unknowns. Mode selection is a step in that loop, not a substitute for it.

Use these workflows to apply Diátaxis in real documentation work. Prefer small, verifiable improvements over speculative reorganizations.

## Workflow 1: Classify an existing page

1. Read the title, opening paragraph, headings, examples, and call-to-action.
2. Ask the compass questions:
   - Action or cognition?
   - Acquisition or application?
3. Name the primary mode.
4. Record evidence: title signals, sentence patterns, headings, code shape, examples, user assumptions.
5. Find secondary-mode passages that interrupt the primary mode.
6. Decide whether to:
   - keep the page and edit for mode purity
   - split the page into two or more pages
   - rename the page
   - move the page to a different section
   - replace some content with links
7. Recommend one smallest useful next action.

Output pattern:

```markdown
## Classification

- Current page: `docs/example.md`
- Primary mode: How-to guide
- User need: accomplish a specific deployment task
- Evidence: task title, prerequisites, ordered steps, conditional branches
- Mixed-mode risks: long background section before step 1; full CLI options table
- Recommended changes: move background to explanation; move option table to CLI reference; add links
- Smallest useful next action: cut the background section to a two-sentence note and link to a new explanation stub
```

## Workflow 2: Create a new page

1. Write the user's need as a sentence.
   - “The reader needs to learn the basic workflow.”
   - “The reader needs to rotate credentials in production.”
   - “The reader needs exact API parameter information.”
   - “The reader needs to understand why the system uses eventual consistency.”
2. Use the compass to choose a mode.
3. Choose a title that signals the mode.
4. Select the matching template from `assets/templates/`.
5. Fill the template with product facts from reliable sources.
6. Remove sections that are not needed. Templates are starting points, not compliance checklists.
7. Add cross-links to other modes only where they preserve flow.
8. Verify that the page serves one primary need.

## Workflow 3: Rewrite a mixed page

1. Duplicate the page mentally into four bins: tutorial, how-to, reference, explanation.
2. Move each paragraph or block into the bin it serves.
3. Identify the page's most important user need.
4. Keep the primary bin as the page body.
5. Turn the other bins into:
   - links to existing pages
   - new page stubs
   - short notes that do not interrupt flow
6. Rename the page to match the primary mode.
7. Add redirects if the project uses them.
8. Validate internal links and build output.

## Workflow 4: Audit a documentation set

Report functional quality and experience quality separately, using the two-part assessment in `checklists.md`. Do not produce a single aggregate score.

1. Inventory pages and existing sections.
2. Classify pages using the compass.
3. Group by mode and by user/job-to-be-done.
4. Look for missing coverage:
   - No learning path for new users?
   - Many procedures but no reference?
   - Good reference but no task coverage?
   - Concepts scattered through tutorials and reference?
5. Look for overload:
   - Tutorials too long or too brittle?
   - How-to guides with too much background?
   - Reference pages with task flow?
   - Explanation pages with hidden operational requirements?
6. Recommend small, sequenced improvements.
7. Avoid a giant restructure unless the user asks for it.

Optional repository-scale aid:

```bash
python scripts/diataxis_audit.py docs/ --format markdown
```

The script is heuristic. Use it as a triage tool, not as authority.

## Workflow 5: Design documentation architecture

1. Start with user groups and user situations, not the four labels.
2. Decide whether users experience the product as one product or several products.
3. Choose the highest-level split that best matches the reader's mental model.
4. Within each major area, separate modes where doing so helps users.
5. Use landing pages as overviews, not as long undifferentiated lists.
6. Keep lists short or grouped.
7. Link across modes deliberately:
   - tutorial -> explanation for background when the learner is ready
   - how-to -> reference for full option lists
   - reference -> how-to for common tasks
   - explanation -> tutorial/how-to/reference for practical follow-up
8. Let structure emerge from improved pages; do not create empty sections.

## Workflow 6: Review a pull request that changes docs

1. Identify the target mode of each changed page.
2. Check whether the title, intro, headings, examples, and conclusion match that mode.
3. Check technical accuracy against code, CLI output, schemas, tests, or user-provided facts.
4. Flag mode drift:
   - tutorial gains options or theory
   - how-to gains teaching or reference tables
   - reference gains discussion or task flow
   - explanation gains procedures or hidden facts
5. Suggest specific edits, not abstract Diátaxis lectures.
6. Prefer comments like:
   - “Move this paragraph to explanation and link it here.”
   - “Keep one happy path in this tutorial; move the Docker/Kubernetes alternatives to how-to guides.”
   - “This table belongs in reference; the how-to guide only needs the two options used by the task.”
7. If the PR is already useful, do not block on ideal architecture.

## Workflow 7: Convert feature knowledge into docs

Given a feature, produce a small documentation plan:

1. Tutorial: What minimal, controlled exercise lets a learner encounter the feature successfully?
2. How-to guides: What real tasks will users search for?
3. Reference: What exact objects, APIs, configuration, limits, and errors must be described?
4. Explanation: What concepts, design reasons, trade-offs, or mental models must users understand?
5. Prioritize by user pain and release risk.
6. Create only pages that have immediate value.

Example output:

```markdown
## Documentation plan for connection pooling

Immediate:
- Reference: `pool` configuration keys and defaults.
- How-to: Configure pool size for a high-concurrency service.

Next:
- Explanation: How pool size affects latency and database load.
- Tutorial: Build a small app that uses pooled connections.
```

## Workflow 8: Test documentation by mode

For the mechanics — finding the project's docs build, running lint and link checks, executing snippets safely, and cleaning up afterwards — read `document-testing.md`. The per-mode questions below are what to test; that file is how.

### Test a tutorial

- Can a newcomer follow it from a clean environment?
- Does every step produce the promised result?
- Are commands copy/pasteable?
- Are expected outputs shown?
- Are failures anticipated?
- Can the exercise be repeated?
- Is explanation minimal?

### Test a how-to guide

- Does it solve a real task?
- Are prerequisites clear?
- Is the sequence logical?
- Are branches and warnings included where real work requires them?
- Does it omit teaching and full reference detail?
- Can a competent user adapt it to their situation?

### Test reference

- Is it complete for its scope?
- Is it accurate against the source of truth?
- Is it organized like the machinery?
- Are defaults, limits, errors, types, and version differences included?
- Are entries consistent in shape?
- Are examples concise and illustrative?

### Test explanation

- Is the topic bounded?
- Does it answer why and how to think about the topic?
- Does it connect concepts and trade-offs?
- Does it avoid becoming a procedure or reference dump?
- Does it leave the reader with a clearer mental model?

## Workflow 9: Apply the one-step improvement loop

Use this loop when documentation feels overwhelming.

1. Choose one page, paragraph, section, or heading.
2. Ask which user need it serves.
3. Ask how well it serves that need.
4. Choose one small change that improves it.
5. Make the change.
6. Stop and repeat.

Examples of one-step improvements:

- Rename “Authentication” to “How to configure token authentication”.
- Move a three-paragraph conceptual aside out of a tutorial.
- Add expected output after a command.
- Add a missing default value to reference.
- Split a 20-item landing page list into three grouped lists.
- Add a link from a how-to guide to the exact reference entry it uses.

## Workflow 10: Handle ambiguity

When you cannot classify a document, **infer and declare** — do not stop and ask by default:

1. Inspect the evidence: surrounding navigation, neighboring pages, terminology, assumed prerequisites, inbound links, and the page's own history.
2. Infer the most likely user need, and note the competing needs you rejected.
3. State the assumption plainly in the audit or work summary, with the evidence behind it.
4. Proceed on that assumption and deliver the work.
5. Offer a split when both needs are substantial.

Ask the user only when **both** are true: different answers would materially change the deliverable, *and* repository evidence cannot resolve it. When you do ask, ask the specific question ("is this page for operators running this in production, or for new users trying the product?"), not "what mode should this be?".

Do not pretend the category is obvious when it is not. Ambiguity is often a useful signal that the page is trying to do too much.
