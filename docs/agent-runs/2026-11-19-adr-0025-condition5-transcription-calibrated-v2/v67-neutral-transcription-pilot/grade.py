"""二票が実際に読んだ依頼と原票を固定し、同じ参照で各版を採点する。"""

import argparse
from collections import Counter, defaultdict
from difflib import SequenceMatcher
from pathlib import Path


def verdict(ref, answer, expected):
    if answer["status"] == "unreadable":
        return "unresolved"
    if ref.MARK.search(answer["text"]):
        return "source-pending"
    read = ref.NORMALIZE(answer["text"])
    if read == expected:
        return "same"
    steps = {k for k, *_ in SequenceMatcher(None, expected, read, autojunk=False).get_opcodes()} - {"equal"}
    if steps == {"delete"}:
        return "omitted"
    if steps == {"insert"}:
        return "extra"
    return "different"


def collect(core, pilot, plan, digest, runtime, output):
    ref = core.ref
    rows = core.load(pilot.OUT / "display/selection.json")["selected"]
    roles = ("gpt", "claude")
    seen, cases = set(), {}
    result = defaultdict(lambda: defaultdict(Counter))
    painted = core.previous.module("conventional_point_shape_guard",
                                  pilot.HERE.parent / "v23-round-pixel-pilot/run.py")
    for name, job in plan["jobs"].items():
        tag, arm = name.split("/")
        item = plan["mapping"][tag]["arms"][arm]
        row = rows[item["entry"]]
        label, = job["request"]["ids"]
        expected = ref.NORMALIZE(row["effective"])
        answers, provenance = {}, {}
        for role in roles:
            history = pilot.outcome(digest, name, role, job, runtime[role])
            folder = pilot.OUT / "reads" / name / role
            if not history or history[-1]["availability"] in ("quota-rejection", "unstarted"):
                raise ValueError(f"保留中のため比較しない {name} {role}")
            records = {}
            for path in sorted(folder.glob("attempt-*")):
                stage = path / "raw"
                for file in (path / "claim.json", stage / "start.json", stage / "process.json",
                             stage / "response.jsonl", stage / "schema.json"):
                    if not file.exists():
                        raise ValueError(f"監査票の来歴が不足 {file}")
                    records[str(file.relative_to(folder))] = core.sha(file)
            latest = history[-1]
            if latest["availability"] == "received":
                session = latest["session"]
                if session in seen:
                    raise ValueError("新規画像票に同じセッションがある")
                seen.add(session)
                answers[role] = ref.decoded(latest["answers"][label], item["partitions"])
            else:
                answers[role] = ref.UNKNOWN
            provenance[role] = {"attempt_sha256": records, "availability": latest["availability"],
                                "session": latest.get("session")}
        paired, coordinates = ref.aligned(*(answers[role] for role in roles), row["box"][2])
        if painted.unverified_round(paired, row, item["image_reference"]["sha"], coordinates):
            paired = ref.UNKNOWN
        labels = {role: verdict(ref, answers[role], expected) for role in roles}
        labels["pair"] = verdict(ref, paired, expected)
        for role, value in labels.items():
            result[arm][role][value] += 1
        cases[name] = {"page": row["key"], "line_index": row["line_index"], "expected": expected,
                       "group": plan["mapping"][tag]["group"], "outcomes": labels, "answers": {**answers, "pair": paired},
                       "provenance": provenance, "coordinates": coordinates}
    artifacts = {str(p): core.sha(p) for p in (pilot.LOCK, pilot.OUT / "display/selection.json")}
    core.save_once(output, core.encoded({"scope": "development-only", "lock_sha256": digest, "cases": cases,
                                         "counts": result, "artifacts": artifacts}))
    print({arm: {r: dict(v) for r, v in s.items()} for arm, s in result.items()}, flush=True)


def main(core, pilot):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("action", choices=("compare",))
    parser.add_argument("--sha256", required=True)
    parser.add_argument("--codex", required=True, type=Path)
    parser.add_argument("--claude", required=True, type=Path)
    args = parser.parse_args()
    output = pilot.HERE / "comparison.json"
    if output.exists():
        raise FileExistsError("採点は確定済み")
    digest, plan = core.sha(pilot.LOCK), core.load(pilot.LOCK)
    if digest != args.sha256 or any(core.sha(Path(f)) != h for f, h in plan["files"].items()):
        raise ValueError("事前固定した方法または画像が異なる")
    runtime = pilot.audit.delivery.runtime({"gpt": args.codex, "claude": args.claude})
    collect(core, pilot, plan, digest, runtime, output)
