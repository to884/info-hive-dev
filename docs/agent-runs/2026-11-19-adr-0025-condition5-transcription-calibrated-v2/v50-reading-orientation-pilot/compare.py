"""同じ16行の保存票と、表示を加えた開発票の違いを集計する。"""

import argparse
from collections import Counter, defaultdict
from difflib import SequenceMatcher
from pathlib import Path
import sys

import prepare

HERE = Path(__file__).resolve().parent
pilot = prepare.pilot
sys.path.insert(0, str(HERE.parent / "v47-reference-audit"))
import official

core = official.core
reference = core.ref


def verdict(record, expected):
    if record["status"] == "unreadable":
        return "unresolved"
    text = reference.NORMALIZE(record["text"])
    if reference.MARK.search(text):
        return "source-pending"
    if text == expected:
        return "same"
    edits = {op for op, *_ in SequenceMatcher(None, expected, text, autojunk=False).get_opcodes()} - {"equal"}
    if edits == {"delete"}:
        return "omitted"
    if edits == {"insert"}:
        return "extra"
    return "different"


def compare(old, new, row, expected, roles):
    outcomes = {}
    for name, votes in (("before", old), ("after", new)):
        values = {role: verdict(votes[role], expected) for role in roles}
        if len(roles) == 2:
            outcome, marks = reference.aligned(*(votes[r] for r in roles), row["box"][2])
            values["pair"] = "source-pending" if marks else verdict(outcome, expected)
        outcomes[name] = values
    return outcomes


def main():
    cli = argparse.ArgumentParser(description=__doc__)
    cli.add_argument("--codex", type=Path, required=True)
    cli.add_argument("--claude", type=Path, required=True)
    cli.add_argument("--role", choices=("gpt", "both"), required=True)
    cli.add_argument("--sha256", required=True)
    args = cli.parse_args()
    roles = ("gpt", "claude") if args.role == "both" else ("gpt",)
    result = HERE / f"comparison-{args.role}.json"
    if result.exists():
        raise FileExistsError("開発の原票の比較は確定済み")
    digest = core.sha(pilot.LOCK)
    plan = core.load(pilot.LOCK)
    if digest != args.sha256 or any(core.sha(Path(name)) != value for name, value in plan["files"].items()):
        raise ValueError("開発用の画像指示が事前固定と異なる")
    core.verify_methods()
    folder = core.OUT / "delivery"
    original = folder / "packages.json"
    prior = core.transport.check(folder, core.sha(original))
    runtimes = pilot.audit.delivery.runtime({"gpt": args.codex, "claude": args.claude})
    rows = core.load(pilot.OUT / "display/selection.json")["selected"]
    by_case, aggregate = {}, defaultdict(lambda: defaultdict(Counter))
    seen = set()
    previous_sessions = set()
    for name, job in plan["jobs"].items():
        label, = job["request"]["ids"]
        link = plan["mapping"][name.split("/")[0]]
        row = rows[link["entry"]]
        raw_before = {role: core.transport.attempts(prior, link["baseline_packet"], role)[-1]["receipt"] for role in roles}
        raw_after = {role: pilot.outcome(digest, name, role, job, runtimes[role])[-1] for role in roles}
        if any(record["availability"] != "received" for record in (*raw_before.values(), *raw_after.values())):
            raise ValueError("確定した画像の原票が不足")
        for before, after in zip(raw_before.values(), raw_after.values(), strict=True):
            if after["session"] in seen:
                raise ValueError("別の開発行で読取セッションを再利用した")
            seen.add(after["session"])
            previous_sessions.add(before["session"])
        votes = [{role: reference.decoded(source[role]["answers"][label], link["partitions"]) for role in roles}
                 for source in (raw_before, raw_after)]
        outcomes = compare(*votes, row, reference.NORMALIZE(row["effective"]), roles)
        for version, cells in outcomes.items():
            for role, value in cells.items():
                aggregate[version][role][value] += 1
        by_case[name] = {"page": row["key"], "line_index": row["line_index"], "category": link["category"],
                         "outcomes": outcomes}
    if seen & previous_sessions or len(by_case) != len(plan["jobs"]):
        raise ValueError("保存済みの独立票と開発用の新規票の来歴が異なる")
    core.save_once(result, core.encoded({"scope": "development-only", "lock_sha256": digest,
                                       "cases": by_case, "counts": aggregate}))
    print({k: {role: dict(v) for role, v in s.items()} for k, s in aggregate.items()}, flush=True)
    for case in by_case.values():
        print(case["page"], case["line_index"], case["category"], case["outcomes"], flush=True)


if __name__ == "__main__":
    main()
