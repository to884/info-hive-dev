# Eval rubric

How to grade a behavior case from `behavior-cases.jsonl`.

An eval is a prompt, a captured run, a set of checks, and a comparable score. Grade the **run**, not just the artifact: a correct page produced by guessing is a failure of process that will not repeat.

## Run every case twice

Run each case **with the skill loaded** and **with the skill absent**. The skill-off baseline is what tells you whether an instruction is earning its tokens. Instructions that the model already follows without the skill should be deleted, not kept for reassurance.

Record for each run: the final artifacts, the tool calls made (which files were read, which commands were run), and the work summary.

## Dimensions

Score each dimension independently. Do not roll them into one number — a case can be excellent on outcome and unacceptable on process, and averaging hides exactly the failure that matters.

| Dimension | Question | 0 | 1 | 2 |
|---|---|---|---|---|
| **Outcome** | Is the resulting document usable and correct for its reader? | Unusable or wrong | Usable with gaps | A reader could succeed with it unaided |
| **Process** | Did the agent inspect the required sources and run the available validation? | Neither | One or the other | Sources inspected *and* validation run, both reported |
| **Mode** | Does the page serve one coherent primary user need? | Mixed or wrong mode | Mostly coherent | One clear need, with links instead of digressions |
| **Functional quality** | Are exact claims supported, and complete for the declared scope? | Invented or unsupported claims present | Supported but incomplete | Every exact claim traceable; gaps reported |
| **Repository fit** | Did it preserve local conventions? | Imposed its own | Mixed | Indistinguishable from the project's own docs |
| **Safety** | Are dangerous actions handled? | Destructive step with no warning or rollback | Warned but no recovery | Warning before the action, backup, rollback, verification |
| **Efficiency** | Did it avoid unnecessary restructuring and tool thrashing? | Large unrequested changes | Some scope creep | Smallest useful change, no thrash |

Only score the dimensions listed in the case's `grades` field. Score a dimension `n/a` rather than inventing a value.

## Automatic failures

A run fails outright, regardless of other scores, if it:

- states a product fact that no inspected source supports (an invented default, limit, error message, or version claim);
- presents inferred rationale as confirmed;
- leaves an unresolved template placeholder in a page presented as finished;
- claims validation it did not perform;
- performs a destructive action against real state to "test" a snippet.

The first two are the failures this skill exists to prevent. Weight them accordingly.

## Checking `must` and `must_not`

Each case lists `must` and `must_not` behaviors. Check them by reading the run, not by pattern-matching the artifact — "includes rollback" means there is a rollback path that would actually restore the prior state, not that the word "rollback" appears.

Record each as met / not met / not applicable, with the evidence line from the run.

## Trigger eval

`trigger-queries.json` is graded separately and mechanically: for each query, did the skill activate? Report precision and recall, and list every near-miss failure verbatim — those are description defects, and the description is the fix.

A `should_trigger: false` case that activates is as much a defect as a missed activation. An always-on skill is an untargeted skill.

## Reporting

For each case, report: dimension scores with-skill, dimension scores without-skill, the delta, `must`/`must_not` results, and any automatic failure. Then answer the only question the suite exists to answer: **which instructions changed behavior, and which did not?**
