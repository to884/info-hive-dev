# Diátaxis information architecture

Diátaxis often leads to a four-part documentation structure, but the four-part structure is an outcome of good documentation work, not a rule to impose blindly.

## Architecture principle

Organize documentation around user needs. The four modes are powerful because they describe different user needs:

- learning through guided action
- accomplishing goals through practical action
- checking information while working
- understanding through reflection

A site structure should make those needs easy to satisfy.

## Do not create empty boxes

Some artifacts are containers or records rather than mode pages — READMEs, FAQs, troubleshooting hubs, changelogs, glossaries, ADRs, runbooks. Do not force them into one of the four modes at file level; see `composite-documents.md`.

Do not create empty `tutorials/`, `how-to/`, `reference/`, and `explanation/` folders just to match the diagram. Empty sections create a false sense of completeness and make navigation worse.

Instead:

1. Improve existing pages one at a time.
2. Move or split content when it clearly serves a different need.
3. Add landing pages when there is enough content to justify them.
4. Let the structure become visible as the documentation improves.

## Simple structure

For a focused product with one main user group, a simple structure may work well:

```text
Home
Tutorials
  Build your first project
  Add your first integration
How-to guides
  Install the CLI
  Deploy to production
  Troubleshoot failed jobs
Reference
  CLI reference
  API reference
  Configuration reference
Explanation
  Architecture
  Authentication concepts
  Performance model
```

Use this when it matches how users think about the product.

## Landing pages

Landing pages should provide an overview, not just a list.

A good landing page:

- says what need the section serves
- groups pages by user goals or topics
- uses snippets to help users choose
- avoids long ungrouped lists
- links to the most common next pages
- does not include the content that belongs in child pages

### Landing page pattern

```markdown
# How-to guides

Use these guides when you know what you want to accomplish and need practical steps.

## Installation and setup

Prepare the tool for local development or production use.

- [Install the CLI](install-cli.md)
- [Configure credentials](configure-credentials.md)
- [Set up a project](set-up-project.md)

## Operations

Run, monitor, and maintain production systems.

- [Rotate API keys](rotate-api-keys.md)
- [Upgrade a deployment](upgrade-deployment.md)
- [Troubleshoot failed jobs](troubleshoot-failed-jobs.md)
```

## List length

Long lists are hard to scan unless they have a strong mechanical order such as alphabetical or numeric order. When a list grows beyond a few items, group it by meaningful categories.

Practical strategies:

- group by task area
- group by user role
- group by lifecycle stage
- group by product component
- group by frequency or importance
- create a separate index for mechanical lookup

## Cross-mode linking

Cross-links should preserve flow.

### Tutorial links

A tutorial should not stop to explain everything. Link after the learner has had the relevant encounter.

Good:

```markdown
The server responds with a signed token. We will use it in the next step. For the full authentication model, see [How authentication works](../explanation/authentication.md).
```

### How-to links

A how-to guide should not carry full reference data.

Good:

```markdown
This guide uses `--strategy rolling`. For the full list of deployment strategies, see [Deployment CLI reference](../reference/deploy.md).
```

### Reference links

Reference can point to tasks and explanations but should not become either.

Good:

```markdown
See also: [How to deploy with a rolling strategy](../how-to/deploy-rolling.md).
```

### Explanation links

Explanation can link in all directions because it often connects the documentation set.

Good:

```markdown
To apply this model in production, see [How to choose a retention policy](../how-to/choose-retention-policy.md).
```

## Complex hierarchies

Some products have more than one organizing dimension:

- multiple user roles
- multiple deployment targets
- multiple product editions
- separate audiences such as users, developers, operators, contributors
- platform-specific workflows
- large APIs with nested resource groups

In these cases, Diátaxis still applies, but the top-level structure may not be the four modes.

### Choose the top-level split by user perspective

Ask:

- Do users experience these as different products?
- Do user groups share tasks and concepts?
- Will a user in one area need content from another area?
- Which split prevents the most wrong turns?
- Which split best matches search and navigation behavior?

If users experience variants as separate products, split by variant first:

```text
Cloud A
  Tutorials
  How-to guides
  Reference
  Explanation
Cloud B
  Tutorials
  How-to guides
  Reference
  Explanation
```

If users share the product but need different tasks, split by Diátaxis first and group inside:

```text
How-to guides
  For administrators
  For application developers
  For contributors
Reference
  Public API
  Admin API
  Contributor tooling
```

If the same reader moves through roles over time, consider a progressive structure:

```text
Use the product
Extend the product
Contribute to the product
```

Each area can still preserve tutorial/how-to/reference/explanation distinctions.

## Shared content

Shared content is often a sign that exact facts belong in reference or that concepts belong in explanation.

Avoid copying the same explanation or parameter table into many task pages. Instead:

- put exact shared facts in reference
- put shared concepts in explanation
- link from tutorials and how-to guides
- use snippets/includes only when the docs platform can keep them accurate and readable

## Reference architecture

Reference should usually mirror the structure of the thing being described.

Examples:

```text
CLI reference
  command-a
  command-b
  command-c
API reference
  Accounts
  Projects
  Jobs
  Webhooks
Configuration reference
  Authentication
  Storage
  Logging
  Network
```

Avoid organizing reference primarily by user journey. Reference users often arrive by search and need a stable map of the machinery.

## How-to architecture

How-to guides should be organized by goals and problem areas.

Examples:

```text
How-to guides
  Installation
  Deployment
  Operations
  Security
  Troubleshooting
  Migration
```

Within each group, titles should still be concrete tasks.

## Tutorial architecture

Tutorials often form a sequence or a small set of standalone lessons.

Good tutorial sequences:

- establish a controlled environment
- build confidence in small increments
- avoid multiplying paths
- introduce concepts through action
- leave production variation for how-to guides

Do not turn tutorials into a full curriculum unless the product genuinely needs a curriculum.

## Explanation architecture

Explanation is topic-based and can be organized by conceptual area.

Examples:

```text
Explanation
  Architecture
  Security model
  Data consistency
  Performance and scaling
  Design decisions
```

Explanation topics should be bounded. When one topic expands into many, split it into smaller concept pages.

## Migration structure

When migrating an existing site, avoid one large “big bang” move. Use staged structure changes:

1. Label or tag current pages by likely mode.
2. Rename the highest-traffic pages first.
3. Move obvious reference material into reference sections.
4. Split obviously mixed tutorials/how-to guides.
5. Add landing pages only after groups are meaningful.
6. Fix navigation and redirects gradually.
7. Add review rules to prevent regression.

## Navigation smells

These are signs the architecture may not fit user needs:

- Several pages called “Overview”.
- One “Guides” section contains lessons, tasks, concepts, and API facts.
- “Getting started” is the only entry point for both learners and production users.
- Reference pages are hidden inside task flows.
- Concepts are scattered across pages and cannot be linked directly.
- Long ungrouped sidebars.
- Product-feature categories do not match user goals.
- Search results land users in conceptual pages when they need exact facts.

## Architecture output format

When proposing an architecture, include:

```markdown
## Proposed documentation structure

### Rationale

This structure is organized first by user role because administrators and application developers rarely share workflows. Within each role, pages are separated by Diátaxis mode.

### Tree

[tree here]

### Migration notes

- Move `docs/getting-started.md` to `tutorials/build-your-first-project.md` after removing production deployment steps.
- Extract the CLI options table to `reference/cli/deploy.md`.
- Create `explanation/deployment-strategies.md` from the current background section.

### Risks

- Existing external links need redirects.
- Shared configuration facts should not be duplicated.
```
