# Diátaxis principles

This reference distills the Diátaxis framework into operational guidance for documentation authors and agents. It is for use while classifying, writing, reviewing, and restructuring technical documentation.

## Diátaxis in one page

Diátaxis starts from a simple premise: documentation should serve the user's needs. In a craft or technical domain, the user alternates between learning, working, checking facts, and reflecting. Those needs produce four documentation modes.

| Mode | Need | Axis | Reader question | Form | Reader stance |
|---|---|---|---|---|---|
| Tutorial | Learning | Action + acquisition | “Can you teach me to do this?” | Lesson | Learner at study |
| How-to guide | Goal | Action + application | “How do I achieve this?” | Directions | Practitioner at work |
| Reference | Information | Cognition + application | “What is true here?” | Description | Practitioner checking facts |
| Explanation | Understanding | Cognition + acquisition | “Why is it like this?” | Discussion | Practitioner reflecting |

The main documentation failures Diátaxis exposes are boundary failures: a lesson tries to solve a work problem; a task guide starts teaching; reference turns discursive; explanation hides critical facts or procedures.

## The compass

When classification is uncertain, use the compass instead of intuition.

First ask whether the content informs **action** or **cognition**:

- Action: steps, operations, tasks, procedures, “do this”.
- Cognition: facts, concepts, definitions, descriptions, “know this”.

Then ask whether it serves **acquisition** or **application**:

- Acquisition: the reader is studying, practicing, forming competence or understanding.
- Application: the reader is working, using competence to solve a problem or check facts.

Result:

- Action + acquisition = tutorial.
- Action + application = how-to guide.
- Cognition + application = reference.
- Cognition + acquisition = explanation.

Use the compass at multiple scales: a whole site, a section, one page, one paragraph, or one sentence.

## Tutorial: learning-oriented lesson

A tutorial is a guided learning experience. The reader is not merely completing a task; the reader is being led through an encounter that builds confidence and basic competence.

### Purpose

A tutorial creates a safe, meaningful, successful, and repeatable experience. It is a lesson in written form.

### Reader

The reader is a learner. They may not yet know the vocabulary, file locations, command habits, failure modes, or judgement calls that experienced users take for granted.

### Content standards

A strong tutorial:

- has a concrete outcome the learner can understand before starting
- uses a controlled environment
- makes the learner do practical things
- produces visible, meaningful results early and often
- shows expected output and tells the learner what to notice
- avoids optional branches and alternative approaches
- keeps explanation minimal and contextual
- avoids exhaustive reference details
- is testable end-to-end
- can be repeated without surprising state or irreversible damage

### Good tutorial patterns

- “In this tutorial, we will build...”
- “First, create...”
- “You should see output similar to...”
- “Notice that...”
- “If you see ..., check that you...”
- “We use this setting here because ..., and the full discussion is in ...”

### Tutorial anti-patterns

- “In this tutorial you will learn...” as the main promise. Prefer describing what the learner will do.
- Long conceptual background before the first action.
- Optional side quests.
- Several alternative tools or approaches.
- Failure-prone setup that is not checked.
- A final result that is too abstract to feel like an achievement.
- A lesson that assumes expert tacit knowledge.

## How-to guide: goal-oriented directions

A how-to guide helps a competent user achieve a specific real-world result. It belongs to the user’s work.

### Purpose

A how-to guide answers a practical question: “How do I accomplish this?” It helps the user navigate the problem field efficiently and safely.

### Reader

The reader is already competent enough to know what they want, interpret instructions, make routine decisions, and recover from ordinary variation.

### Content standards

A strong how-to guide:

- is defined by a user goal, not a product feature
- uses a task-oriented title, usually “How to ...”
- starts and ends at practical, meaningful points
- gives a logical sequence of actions
- includes prerequisites, warnings, and decision points
- accounts for real-world variation with conditional guidance
- omits unnecessary conceptual teaching
- links to reference for full option lists and to explanation for background
- assumes competence without being careless

### Good how-to patterns

- “This guide shows how to...”
- “Before you begin...”
- “To achieve ..., do ...”
- “If ..., then ...”
- “For the full list of options, see ...”
- “Use this approach when...”

### How-to anti-patterns

- Feature tours disguised as tasks.
- Overly broad titles such as “Build a web application”.
- Teaching fundamentals inside the task flow.
- Long explanations of design rationale.
- Exhaustive parameter reference.
- A single happy path where real work requires branches.
- “Getting started” pages that try to be both tutorial and how-to guide.

## Reference: information-oriented description

Reference provides accurate, complete, authoritative information. It is a map of the machinery.

### Purpose

Reference helps a user at work confirm what is true: what commands exist, what parameters mean, what defaults apply, what a function returns, what errors can occur, what limits exist.

### Reader

The reader is working and needs certainty. They may consult reference briefly, repeatedly, and non-linearly.

### Content standards

Strong reference:

- describes and only describes
- mirrors the structure of the thing described
- uses standard patterns consistently
- is neutral, factual, terse, and authoritative
- separates facts from interpretation
- includes warnings where required
- includes examples as compact illustrations, not as lessons
- is maintained against the product source of truth

### Good reference patterns

- “`--timeout` sets the maximum wait time in seconds.”
- “Default: `30`.”
- “Returns: ...”
- “Raises: ...”
- “Subcommands: ...”
- “You must not use ... unless ...”

### Reference anti-patterns

- Discursive “why” sections embedded in API pages.
- Step-by-step task flows inside command pages.
- Inconsistent parameter ordering.
- Reference organized by imagined user journeys rather than product structure.
- Auto-generated pages treated as sufficient when they lack context, examples, warnings, or completeness checks.
- Examples that turn into mini-tutorials.

## Explanation: understanding-oriented discussion

Explanation helps readers make sense of a topic. It is where context, background, design rationale, trade-offs, and conceptual models belong.

### Purpose

Explanation illuminates. It connects ideas, shows why things are the way they are, and gives the reader a broader understanding of the craft or product.

### Reader

The reader is not necessarily in the middle of doing a task. They are reflecting, studying, forming mental models, or trying to understand implications.

### Content standards

Strong explanation:

- is topic-oriented and bounded
- answers “why?”, “what does this mean?”, and “how should I think about this?”
- provides background, history, constraints, and design reasons
- compares alternatives and trade-offs
- can include perspective and judgement
- links to how-to guides for procedures
- links to reference for exact facts
- avoids hiding must-know operational details in prose

### Good explanation patterns

- “The reason for this design is...”
- “This trade-off matters when...”
- “Historically...”
- “This is analogous to...”
- “Some teams choose ..., but ...”
- “The model to keep in mind is...”

### Explanation anti-patterns

- A conceptual article that becomes a hidden procedure.
- A background page that becomes the only place a critical default is documented.
- Unbounded essays that attempt to explain everything.
- Reference tables without interpretive context.
- A “concepts” page that is really a product feature list.

## Critical boundaries

### Tutorial vs how-to guide

Both contain actions and steps. The difference is the user’s relationship to the work.

| Question | Tutorial | How-to guide |
|---|---|---|
| User stance | At study | At work |
| Purpose | Build competence and confidence | Achieve a task or solve a problem |
| Responsibility | Teacher/writer owns the learning experience | User owns the real-world situation |
| Setting | Controlled and safe | Real-world and variable |
| Path | One managed path | May branch and adapt |
| Reader knowledge | May be new to basics | Already competent |
| Success | Learner completes a meaningful exercise | User reaches a practical goal |
| Options | Avoided | Included when real cases require them |
| Explanation | Minimal | Only what helps action |

A beginner document is not automatically a tutorial. An advanced document is not automatically a how-to guide. The distinction is study vs work.

### Reference vs explanation

Both contain knowledge rather than action. The difference is whether the reader is applying or acquiring knowledge.

| Question | Reference | Explanation |
|---|---|---|
| User stance | At work | At study/reflection |
| Purpose | Check facts | Understand meaning and context |
| Form | Neutral description | Discursive discussion |
| Structure | Mirrors the machinery | Follows a bounded topic |
| Voice | Austere, objective | Interpretive, connective |
| Examples | Illustrate facts | Develop understanding |
| Risk when mixed | Facts get obscured | Ideas become cramped and brittle |

## Mixed-mode repair patterns

When content contains multiple modes:

1. Identify the primary user need.
2. Highlight passages that serve a different need.
3. Move those passages into the appropriate mode.
4. Replace moved material with a short bridge or link.
5. Rename the page if its title implies the wrong need.
6. Check whether the resulting page now has a coherent flow.

Common repairs:

- Tutorial overloaded with conceptual background -> move background to explanation and link.
- Tutorial containing optional deployment paths -> keep one path in the tutorial; move alternatives to how-to guides.
- How-to with full option tables -> move tables to reference.
- Reference with “why this exists” sections -> move to explanation.
- Explanation with commands to run -> move procedure to how-to guide; link from explanation.

## Functional quality and deep quality

Diátaxis governs deep quality — fit, flow, and the reader's need. It cannot supply functional quality: accuracy, completeness, consistency, and precision need separate technical discipline. That discipline is in `evidence-and-verification.md` and `document-testing.md`, and it takes precedence: a well-shaped page carrying an invented default is worse than a clumsy page with correct facts, because the shape makes it look trustworthy.

Diátaxis is not a substitute for accuracy, completeness, consistency, and technical validation. Those are functional qualities and still require normal documentation craft.

Diátaxis supports deeper quality: fitting user needs, preserving flow, anticipating the reader, and making documentation feel natural to use. It also exposes functional gaps: once material is correctly separated, missing facts, missing task coverage, and weak learning paths become easier to see.

## Practical rule of thumb

For any paragraph, ask: “What is the reader trying to do with this paragraph right now?”

- Learn by doing? Tutorial.
- Complete a task? How-to guide.
- Confirm a fact? Reference.
- Understand a concept? Explanation.

If the answer changes inside a page, you may need a split.
