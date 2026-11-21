# Reference patterns

Read this when writing API, CLI, configuration, schema, environment-variable, or error reference.

"Fields / parameters / options" is not a shared schema for every kind of reference. Each reference family has a different set of facts a reader consults it for. Pick the family, then use its required fields. Verify each fact against the source of truth named in `references/evidence-and-verification.md`.

## Rules common to all reference families

- **Declare the scope** in the first sentence: what this page covers, and what it does not.
- **Declare the version** the page documents.
- **One entry schema per page.** Every entry has the same fields in the same order, even when a field is "none".
- **Order predictably** — alphabetical for lookup, or source order when the source has a meaningful order (CLI subcommands, config sections). Say which.
- **Neutral voice.** No encouragement, no "simply", no rationale. Rationale goes to explanation, procedures to how-to.
- **Say "none" explicitly** rather than omitting a field; a missing field reads as an oversight.
- **Mark required/optional and defaults** unambiguously; "default: none" and "no default" are different claims.

## API endpoint reference

Required per endpoint:

- Method and path, with path parameters marked.
- One-sentence factual description of what the endpoint does.
- Authentication and required scopes/permissions.
- Path parameters: name, type, constraints.
- Query parameters: name, type, required, default, constraints.
- Request body: media type, schema, required fields, constraints.
- Success responses: status code, media type, schema.
- Error responses: status code, error code, meaning, whether retryable.
- Idempotency: whether repeating the call is safe, and the mechanism if any.
- Rate limits and quotas that apply to this endpoint.
- Pagination model, if the response is a collection.
- Side effects (events emitted, resources created, webhooks fired).
- Version notes and deprecation status.

## API object / resource reference

Required per object:

- What the object represents and where it appears (which endpoints return or accept it).
- Per field: name, type, nullability, required-on-create, mutability (read-only, write-once, updatable), default, constraints, example value.
- Enumerations: every permitted value with its meaning. An enum documented as "one of several statuses" is not reference.
- Relationships to other objects, and how they are expressed (embedded, id, link).
- Lifecycle states and permitted transitions, if the object has them.
- Size limits (array lengths, string lengths).
- Compatibility notes: fields added, deprecated, or removed by version.

## CLI command reference

Required per command:

- **Synopsis** — the exact usage line, matching `--help`.
- **Description** — one factual sentence.
- **Arguments** — name, whether variadic, required, meaning.
- **Flags** — long and short form, value type, default, repeatable or not.
- **Precedence** — how flags, environment variables, config files, and defaults resolve against each other, in order.
- **Environment variables** the command reads.
- **stdout** — what is written, and its format (and whether it is stable enough to parse).
- **stderr** — what is written there, including whether progress/logging goes to stderr.
- **Exit codes** — every code and its meaning, including 0.
- **Side effects** — files written, state changed, network calls made.
- **Examples** — compact, one per distinct usage shape, not a walkthrough.
- **Version notes** — when flags were added, renamed, or deprecated.

Generate from the parser definition or `--help` where possible; hand-written CLI reference drifts within one release.

## Configuration reference

Required per setting:

- Key, in the exact form the project uses (dotted path, YAML nesting, or env name).
- **Type** and, where it is a scalar with units, the unit.
- **Default**, and whether the default differs by platform or deployment mode.
- **Allowed values** or the validation rule that constrains it.
- **Validation behavior** — what happens on an invalid value: startup failure, ignored, clamped.
- **Precedence** — where this key can be set and which source wins.
- **Reload behavior** — does a change take effect immediately, on reload, or only on restart?
- **Security implications** — whether the value is a secret, whether it widens access, whether it disables a protection.
- **Compatibility and deprecation** — introduced in, deprecated in, replacement key.

## Environment-variable reference

Same fields as configuration, plus:

- Exact variable name and its casing.
- Whether it is read once at startup or per operation.
- Whether an empty string is distinct from unset.
- Whether it is a secret (and therefore must not be logged or committed).
- The configuration key it corresponds to, if any, and which wins.

## Schema reference

Required:

- Schema language and version (JSON Schema draft, OpenAPI version, protobuf syntax, Avro).
- Canonical location of the schema file, and whether it is generated.
- Per property: type, required, default, constraints, format, description.
- Composition rules in use (`oneOf`, `allOf`, discriminators) and what they mean for a producer.
- Additional-properties behavior: are unknown fields rejected, ignored, or preserved?
- Evolution policy: what counts as a breaking change to this schema.

## Error reference

Required per error:

- Stable identifier (code, constant, or exact message string) exactly as emitted.
- The literal message text, if the message is stable and user-visible.
- When it is raised — the condition, not a guess.
- Whether it is retryable, and with what backoff.
- What the caller should do about it (one line; the full procedure belongs in a how-to).
- HTTP status or exit code mapping, where applicable.
- Version notes: introduced, changed wording, deprecated.

Group errors by the identifier readers actually have — they arrive with a code or a message string pasted from a terminal, so make both searchable on the page.

## Choosing a template

`assets/templates/` contains: `api-endpoint-reference.md`, `api-object-reference.md`, `cli-command-reference.md`, `configuration-reference.md`, `environment-variables-reference.md`, `schema-reference.md`, `error-reference.md`, and the generic `reference.md` for interfaces that fit none of these. Delete every field the entry genuinely does not have — but state "none" rather than dropping a field the reader will look for.
