"""受領済みの画像票を戻し、既存正解がない対照も区別して記録する。"""

import argparse
from collections import Counter
from pathlib import Path

import prepare

pilot = prepare.pilot
audit = pilot.audit


def main():
    cli = argparse.ArgumentParser(description=__doc__)
    cli.add_argument("--codex", required=True, type=Path)
    cli.add_argument("--claude", required=True, type=Path)
    args = cli.parse_args()
    plan = audit.load(pilot.LOCK)
    sha = audit.sha(pilot.LOCK)
    if any(audit.sha(Path(f)) != h for f, h in plan["files"].items()):
        raise ValueError("固定した画像・依頼と異なる")
    runtime = audit.delivery.runtime({"gpt": args.codex, "claude": args.claude})
    rows = audit.load(pilot.OUT / "display/selection.json")["selected"]
    comparisons, counts, active = {}, Counter(), set()
    for name, task in plan["jobs"].items():
        case = name.split("/")[0]
        index = plan["mapping"][case]
        row = rows[index["entry"]]
        wanted, = task["request"]["ids"]
        found, stamps = {}, {}
        for role in pilot.trial.MODELS:
            records = pilot.outcome(sha, name, role, task, runtime[role])
            if not records or records[-1]["availability"] != "received":
                raise ValueError("当時保存した有効票がそろわない")
            item = records[-1]
            if item["session"] in active:
                raise ValueError("別々の新規セッションが使われていない")
            active.add(item["session"])
            stamps[role] = item["response_sha256"]
            found[role] = pilot.reference.decoded(item["answers"][wanted], index["partitions"])
        merged, coord = pilot.reference.aligned(*found.values(), row["box"][2])
        expected = pilot.reference.NORMALIZE(row["effective"]) if row["effective"] is not None else None
        if merged["status"] == "unreadable":
            verdict = "unresolved"
        elif coord:
            verdict = "both-location-needs-source"
        elif expected is None:
            verdict = "no-existing-reference"
        elif merged["text"] == expected:
            verdict = "same"
        elif merged["text"] and merged["text"] in expected:
            verdict = "omitted"
        elif expected in merged["text"]:
            verdict = "extra"
        else:
            verdict = "different"
        comparisons[name] = {"page": row["key"], "line_index": row["line_index"], "category": index["category"],
                             "result": verdict, "expected": expected, "readings": found,
                             "pair": merged, "coordinates": coord, "receipts": stamps}
        counts[verdict] += 1
    audit.save_once(pilot.HERE / "result-with-unknown-control.json", audit.encoded({
        "scope": "development-only", "lock_sha256": sha, "cases": comparisons, "counts": counts,
    }))
    print(dict(counts), flush=True)


if __name__ == "__main__":
    main()
