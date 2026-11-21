# Accessibility and global readers

Read this when using screenshots, diagrams, tables, directional UI language, or terminology intended for a broad audience.

Accessibility is functional quality, not polish. A page that a screen-reader user or a non-native reader cannot follow has failed for that reader regardless of its Diátaxis mode.

## Heading hierarchy

- One `H1` per page, and it is the page title.
- Do not skip levels; `H2` follows `H1`.
- Headings describe content, not sequence — "Rotate the signing secret", not "Step 3".
- Do not use bold text as a fake heading. Screen readers do not announce it as structure.
- Keep headings unique on a page so anchor links and outlines stay unambiguous.

## Descriptive link text

- The link text must make sense read on its own, out of context: screen-reader users navigate by a list of links.
- Never link "here", "this page", "click here", "read more", or a bare URL in prose.
- Prefer the destination's title: "see [Webhook event payload reference]".
- Two links on a page with the same text must go to the same place.

## Positional and sensory language

- Do not rely on position: "the button on the left", "the box below". Layout changes with viewport and does not exist in a screen reader.
- Name the control instead: "select **Rotate secret**".
- Do not rely on colour or shape alone: "the red badge" fails for colour-blind readers. Say what it means: "the **Failed** badge".
- Do not rely on size or motion ("the spinning icon") as the only identifier.

## Keyboard and screen-reader compatible instructions

- Give the control's accessible name (its visible label), not its icon appearance.
- Where a keyboard route exists, document it alongside the pointer route.
- Do not require the reader to hover to reveal a control without saying that a keyboard-focus route exists.
- Describe outcomes ("a confirmation dialog opens"), which is what a screen-reader user hears, rather than visual motion.

## Tables

- Use tables for tabular data, never for layout.
- Give every column a header; give row headers where rows are entities.
- Avoid merged cells and nested tables — they linearize into nonsense.
- Keep tables narrow enough to read on a phone; move long prose out of cells into the body.
- A table with one column is a list. A table with two rows is usually a sentence.

## Diagrams and complex images

Every diagram needs **two** things:

1. A **short identification** in `alt` text — what the image is ("Sequence diagram of webhook delivery and retry").
2. A **long textual equivalent** carrying the essential information — an adjacent paragraph, list, or table that a reader who cannot see the diagram can follow instead. Do not stuff this into `alt`.

Additional rules:

- Do not encode meaning in colour alone; use labels, patterns, or shapes as well.
- Ensure the diagram is legible in both light and dark rendering if the site supports both.
- Prefer diagram-as-code (Mermaid, D2, Graphviz) so the source is diffable and the labels are real text.
- A decorative image gets empty `alt=""`, never a filename.

## Screenshots

- Add text equivalents for every value the reader needs; a screenshot is a supplement, never the only source of a fact.
- Do not screenshot text that could be text.
- Redact real identifiers, tokens, and personal data.
- Note the product version and platform.

## Terminology consistency

- One term per concept, everywhere. Synonym variety is a virtue in prose and a defect in documentation.
- Use the project glossary; if there is none and the product is inconsistent, pick the term the UI uses and say so.
- Expand an acronym on first use per page — readers arrive mid-site from search, not from page one.
- Do not rename the product's own concepts to fit Diátaxis vocabulary.

## Clear language for translation and non-native readers

- Short sentences, one idea each; active voice; explicit subjects.
- Prefer the simple verb: "use", not "utilize"; "start", not "spin up".
- Avoid idioms, metaphor, humour, and cultural references — they translate badly and date fast.
- Avoid negative questions and double negatives.
- Do not use "simply", "just", "easy", "obvious": if the reader struggles, the word tells them the fault is theirs.
- Keep noun stacks short ("the delivery retry policy", not "the webhook delivery retry policy configuration override value").
- Repeat the noun rather than leaning on "it" or "this" across sentences.

## Inclusive examples

- Use neutral, non-gendered example personas; use they/them when a pronoun is unavoidable.
- Use reserved example domains and identifiers (`example.com`, RFC 5737 addresses), never real ones.
- Vary names across cultures; avoid names that encode a stereotype about the role.
- Avoid violent or exclusionary metaphors in examples ("kill", "hang", "master/slave") where the product does not force the term; where the product's API uses such a term, document the term and do not editorialize in reference.

## Formatting for scanning

- Front-load the point of each paragraph.
- Keep paragraphs short in tutorial, how-to, and reference; explanation may run longer.
- Make code blocks copy-pasteable: no leading `$` prompt when the output is not shown separately, no line numbers.
- Put warnings before the action, never after it.
