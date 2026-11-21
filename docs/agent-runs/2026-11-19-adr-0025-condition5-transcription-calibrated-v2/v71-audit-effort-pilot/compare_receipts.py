"""回答を載せない監査の受領台帳は元の照合関数で検証し、別に検証済みの回答を使う。"""

from collections import Counter, defaultdict

import argparse
from importlib.util import module_from_spec, spec_from_file_location
from pathlib import Path

HERE = Path(__file__).resolve().parent
STAGES = HERE.parent
spec = spec_from_file_location("fixed_effort_run", HERE / "run.py")
fixed = module_from_spec(spec)
spec.loader.exec_module(fixed)
core, delivery, high, judge = fixed.core, fixed.delivery, fixed.high, fixed.judge
launch, medium, pilot, previous, roles = fixed.launch, fixed.medium, fixed.pilot, fixed.previous, fixed.roles


def compare():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("action", choices=("compare",))
    parser.add_argument("--sha256", required=True)
    parser.add_argument("--codex", required=True, type=Path)
    parser.add_argument("--claude", required=True, type=Path)
    args = parser.parse_args()
    plan, digest = core.load(pilot.LOCK), core.sha(pilot.LOCK)
    if digest != args.sha256 or any(core.sha(Path(p)) != h for p, h in plan["files"].items()):
        raise ValueError("事前固定した開発試験の入力が異なる")
    core.verify_methods()
    old = core.transport.check(delivery, core.sha(delivery / "packages.json"))
    receipt = core.load(delivery / "received.json")
    verified, saved_answers = core.transport.collect(old, core.old_sessions())
    if verified != receipt:
        raise ValueError("既存監査の確定原票と異なる")
    rows = core.load(pilot.OUT / "display/selection.json")["selected"]
    runtime = pilot.audit.delivery.runtime({"gpt": args.codex, "claude": args.claude})
    painted = previous.module("effort_point_shape_guard", STAGES / "v23-round-pixel-pilot/run.py")
    older, fresh, cases = set(), set(), {}
    counts = defaultdict(lambda: defaultdict(Counter))
    for name, job in plan["jobs"].items():
        pack = name.split("/")[0]
        link = plan["mapping"][pack]
        row = rows[link["entry"]]
        label, = job["request"]["ids"]
        prior, higher = [], []
        for role in roles:
            prior_vote = receipt["votes"][pack][role][-1]["receipt"]
            if prior_vote["availability"] != "received":
                raise ValueError("既存監査の確定原票と異なる")
            older.add(prior_vote["session"])
            pilot.audit.readers.command = high
            try:
                attempts = pilot.outcome(digest, name, role, job, runtime[role])
            finally:
                pilot.audit.readers.command = medium
            if not attempts or attempts[-1]["availability"] != "received":
                raise ValueError(f"開発票がそろっていない {name} {role}")
            vote = attempts[-1]
            if vote["session"] in fresh:
                raise ValueError("開発用の新規セッションが重複した")
            fresh.add(vote["session"])
            prior.append(core.ref.decoded(saved_answers[pack][role][label], link["partitions"]))
            higher.append(core.ref.decoded(vote["answers"][label], link["partitions"]))
        readings, scores = {}, {}
        alternatives = {"medium": prior, "high": higher, "opus-high": [prior[0], higher[1]],
                        "sol-high": [higher[0], prior[1]]}
        for arm, votes in alternatives.items():
            pair, points = core.ref.aligned(*votes, row["box"][2])
            if painted.unverified_round(pair, row, link["image_reference"]["sha"], points):
                pair, points = core.ref.UNKNOWN, []
            readings[arm] = {"gpt": votes[0], "claude": votes[1], "pair": pair, "coordinates": points}
            scores[arm] = {r: judge.verdict(core.ref, readings[arm][r], row["effective"])
                           for r in ("gpt", "claude", "pair")}
            for group in (link["category"], "all"):
                counts[group][arm][scores[arm]["pair"]] += 1
        cases[pack] = {"page": row["key"], "line_index": row["line_index"], "category": link["category"],
                       "shape": link["shape"], "reference": row["effective"], "readings": readings,
                       "outcomes": scores}
    if fresh & older:
        raise ValueError("保存済みの監査セッションを開発で再利用した")
    core.save_once(HERE / "comparison.json", core.encoded({"scope": "development-only",
                   "lock_sha256": digest, "counts": counts, "cases": cases}))
    print({k: dict(v) for k, v in counts["all"].items()}, flush=True)


if __name__ == "__main__":
    launch.configure()
    compare()
