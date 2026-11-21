# Diátaxis style guide

Use this guide for wording, titles, examples, links, and editing choices in Diátaxis-based documentation.

**This guide is a fallback.** Project-specific terminology, style guides, and house conventions win over everything here. Read this only where the project is silent, and never rewrite a project's established phrasing to match it. Precedence is set in `SKILL.md` under "Instruction precedence".

## General style rules

- Write for the reader's current need.
- Make the page's purpose obvious in the title and first paragraph.
- Prefer one page, one primary mode.
- Use cross-links instead of mixing modes.
- Do not duplicate the same fact in many places; put exact facts in reference and link to them.
- Do not use “guide”, “overview”, or “getting started” as a substitute for deciding the mode.
- Keep examples realistic, but not so complex that they obscure the mode.
- Preserve the project's established Markdown, MDX, Sphinx, Docusaurus, MkDocs, or docs-as-code conventions.

## Titles by mode

### Tutorial titles

Good patterns:

- “Tutorial: Build your first ...”
- “Create a ... with ...”
- “Build a small ...”
- “Your first ...”

Avoid:

- “How to ...” when the page is a lesson.
- “Introduction to ...” when the page contains steps.
- “Learn ...” if the outcome is vague.

### How-to titles

Good patterns:

- “How to configure ...”
- “How to troubleshoot ...”
- “How to migrate from ... to ...”
- “Rotate ... credentials”
- “Deploy ... to ...”

Avoid:

- One-word feature names.
- “Overview of ...” for task pages.
- “Tutorial” for work procedures.

### Reference titles

Good patterns:

- “CLI reference”
- “Configuration reference”
- “`WidgetClient` API reference”
- “Environment variables”
- “Error codes”
- “Webhook payload schema”

Avoid:

- “How to use the API” for reference entries.
- Task titles for object descriptions.

### Explanation titles

Good patterns:

- “About ...”
- “Understanding ...”
- “Why ...”
- “Architecture of ...”
- “Concepts: ...”
- “Design trade-offs in ...”

Avoid:

- “Reference” for conceptual topics.
- “How to ...” unless it is actually a procedure.

## Opening paragraphs

### Tutorial opening

Do:

```markdown
In this tutorial, we will build a small service that accepts events and writes them to a local queue. Along the way, we will run the service, send a test event, and inspect the stored message.
```

Avoid:

```markdown
In this tutorial, you will learn queues, event ingestion, service configuration, retries, and observability.
```

Why: describe the concrete experience rather than promising learning outcomes.

### How-to opening

Do:

```markdown
This guide shows how to rotate a production API key without interrupting existing clients. Use it when the old key is still valid and you can deploy configuration changes.
```

Avoid:

```markdown
API keys are an important part of authentication. This guide explains what API keys are and why rotation matters.
```

Why: how-to guides should orient the user to the task, then get them moving.

### Reference opening

Do:

```markdown
The `cache.ttl` setting controls how long cached responses remain valid. Values are durations in seconds.
```

Avoid:

```markdown
Caching is a useful technique that helps applications respond more quickly.
```

Why: reference starts with facts.

### Explanation opening

Do:

```markdown
The cache uses time-based invalidation because the service cannot reliably detect every upstream change. This design favors predictable latency over perfect freshness.
```

Avoid:

```markdown
To set the cache TTL, open `config.yaml` and add the following key.
```

Why: explanation starts with a concept, reason, or mental model.

## Language patterns by mode

| Mode | Prefer | Avoid |
|---|---|---|
| Tutorial | “we will”, “now”, “you should see”, “notice” | “choose one of”, long “why”, exhaustive lists |
| How-to | “to”, “if”, “when”, “before you begin”, “verify” | “you will learn”, broad background, complete reference |
| Reference | “is”, “sets”, “returns”, “default”, “required” | opinion, narrative, “first do...” |
| Explanation | “because”, “this means”, “trade-off”, “historically”, “an analogy” | numbered procedures, exhaustive facts |

## Code examples

### Tutorials

Use code as part of a controlled learning path.

- Provide complete files or precise patches.
- Show where to put each file.
- Keep examples small.
- Show expected output.
- Avoid unexplained substitutions unless the learner must practice them.

### How-to guides

Use code to accomplish the task.

- Use placeholders where the user's real values differ.
- Explain what must change and what should remain.
- Include verification commands.
- Include rollback or cleanup when the task is risky.

### Reference

Use code to illustrate syntax or behavior.

- Keep examples compact.
- Do not build a narrative around them.
- Show edge cases only when they define behavior.
- Keep examples close to the item they illustrate.

### Explanation

Use code to illuminate concepts.

- Prefer small conceptual examples.
- Compare alternatives.
- Do not require the reader to run the example unless the page is actually a tutorial or how-to guide.

## Cross-linking patterns

Use links to preserve mode purity.

### From tutorials

- Link to explanation after the learner has encountered the concept.
- Link to reference only when the learner may later need exact details.
- Do not interrupt early steps with long link lists.

Pattern:

```markdown
We use the default retry policy here so the example stays small. For why retry policies matter, see [Retry behavior explained](../explanation/retry-behavior.md).
```

### From how-to guides

- Link to reference for exhaustive options.
- Link to explanation for rationale that would interrupt the task.
- Link to related how-to guides for adjacent tasks.

Pattern:

```markdown
This guide uses the `safe` migration mode. For all migration modes and defaults, see [Migration options](../reference/migrations.md).
```

### From reference

- Link to common how-to guides from reference entries when useful.
- Link to explanation for design context.
- Do not embed full task flow or rationale.

Pattern:

```markdown
For a production rotation procedure, see [How to rotate API keys](../how-to/rotate-api-keys.md).
```

### From explanation

- Link to tutorials for first experience.
- Link to how-to guides for tasks.
- Link to reference for exact facts.

Pattern:

```markdown
For exact timeout defaults, see [Timeout configuration reference](../reference/timeouts.md).
```

## Editing patterns

### Shrink and link

When a paragraph belongs to another mode, shrink it to one sentence and link to the proper page.

Before:

```markdown
The retry system uses exponential backoff because distributed systems can fail in correlated bursts. Historically, fixed retry intervals caused synchronized request storms...
```

After in a how-to guide:

```markdown
This procedure uses the default exponential backoff policy. For the rationale and trade-offs, see [Retry behavior explained](../explanation/retry-behavior.md).
```

### Split and name

When a page serves two strong needs, split it.

Before:

```text
Getting started with webhooks
- What webhooks are
- Build your first receiver
- Configure retries in production
- Webhook payload schema
```

After:

```text
Tutorial: Build your first webhook receiver
How to configure webhook retries
Webhook payload reference
Understanding webhook delivery
```

### Move facts to reference

Before in a how-to guide:

```markdown
The `mode` field accepts `safe`, `fast`, `force`, `dry-run`, and `legacy`. `safe` is the default. `force` disables validation...
```

After:

```markdown
Set `mode` to `safe` for this procedure. For all values and defaults, see [Migration mode reference](../reference/migration-mode.md).
```

### Move rationale to explanation

Before in reference:

```markdown
The service stores events for 72 hours. This limit exists because storage is optimized for fast replay, not archival retention...
```

After in reference:

```markdown
Retention: 72 hours.
```

Then link to an explanation page if needed.

## Tone by mode

Tutorials can be reassuring and companionable. How-to guides should be direct and practical. Reference should be restrained and exact. Explanation can be thoughtful and expansive, but bounded.

Do not make every mode use the same voice. Consistency matters, but mode-appropriate language matters more.

## Naming the four sections

The sections do not need to be named exactly “Tutorials”, “How-to guides”, “Reference”, and “Explanation”. Acceptable alternatives include:

- Tutorials: “Get started”, “Learning path”, “Lessons”.
- How-to guides: “Guides”, “Tasks”, “Recipes”, “Operations”.
- Reference: “API”, “CLI”, “Configuration”, “Schema”, “Resources”.
- Explanation: “Concepts”, “Background”, “Discussion”, “Architecture”, “Topics”.

Choose labels that users understand, but keep the underlying mode boundaries.

## Accessibility and usability

Diátaxis does not replace normal usability work. For anything involving screenshots, diagrams, tables, directional UI language, or a broad or translated audience, read `accessibility-and-global-readers.md`. The minimum for every page:

- One `H1`, no skipped heading levels, headings that describe content.
- Descriptive link text that makes sense out of context — never “here”.
- Alt text for every image, plus a text equivalent for anything a diagram is the only source of.
- No purely positional or colour-based instructions (“the button on the left”, “the red badge”).
- Consistent terms, expanded acronyms on first use per page.
- Short paragraphs in task and reference pages; copy-pasteable code blocks.
- Warnings before the actions they qualify, never after.

## Final self-check before publishing

- Does the page have one primary mode?
- Does the title match the mode?
- Does the intro set the right reader expectation?
- Are other modes moved or linked?
- Is the page technically accurate, and was each exact fact checked against its source?
- Were the examples run, or marked illustrative?
- Are there any unresolved placeholders left?
- Does the page pass the universal publish gate in `SKILL.md`?
- Does the page feel good to use for its intended need?
