# Labeled audit corpus

Six small pages with known answers, used by the README tutorial (*Read your first audit*) and by the repository's own tests. They ship with the skill so the tutorial works from any install, not only from a Git clone.

Each page is labeled by its filename, so you can compare what `diataxis_audit.py` reports against what the page is:

| File | What it is | What the auditor should report |
|---|---|---|
| [`pure-tutorial.md`](pure-tutorial.md) | A lesson with observable checkpoints | `tutorial`, wide margin |
| [`pure-how-to.md`](pure-how-to.md) | A real-world task with verification | `how-to`, wide margin |
| [`pure-reference.md`](pure-reference.md) | A settings table | `reference`, wide margin |
| [`pure-explanation.md`](pure-explanation.md) | A bounded conceptual question | `explanation`, wide margin |
| [`intentionally-mixed.md`](intentionally-mixed.md) | One page serving two needs | `ambiguous`, naming both |
| [`unknown-purpose.md`](unknown-purpose.md) | Too little content to have a mode | `insufficient-context` |

The last two are the point of the corpus. They are not defects in the pages or failures of the script: they are the two outcomes where the script correctly declines to decide, and the reader has to supply the context it lacks.

Run it yourself:

```bash
python3 scripts/diataxis_audit.py assets/examples/audit-corpus --format markdown
```
