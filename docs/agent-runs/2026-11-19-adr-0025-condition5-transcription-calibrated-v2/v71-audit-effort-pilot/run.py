"""v64の確定画像と同じ指示を、新規セッションでhighにして比較する。"""

import argparse
from collections import Counter, defaultdict
from hashlib import sha256
from pathlib import Path
import sys


HERE = Path(__file__).resolve().parent
STAGES = HERE.parent
AUDIT = STAGES / "v64-reference-audit"
sys.path.insert(0, str(AUDIT))
import launch

core = launch.core
previous = launch.previous
base = STAGES / "v24-physical-transcription-pilot/run.py"
pilot = previous.module("fixed_effort_pilot", base)
judge = previous.module("fixed_effort_grade", STAGES / "v67-neutral-transcription-pilot/grade.py")
pilot.HERE = HERE
pilot.OUT = core.CORPUS / "reference-v71-audit-effort-pilot"
pilot.LOCK, pilot.RESULT = HERE / "lock.json", HERE / "high-pair.json"
delivery = launch.OUT / "delivery"
roles = ("gpt", "claude")
medium = pilot.audit.readers.command


def high(exe, folder, names, model, role, cwd):
    argv = medium(exe, folder, names, model, role, cwd)
    if role == "gpt":
        argv[argv.index('model_reasoning_effort="medium"')] = 'model_reasoning_effort="high"'
    else:
        index = argv.index("--effort") + 1
        if argv[index] != "medium":
            raise ValueError("比較元のOpusの設定が異なる")
        argv[index] = "high"
    return argv


def key(row):
    return row["key"], row["line_index"]


def shape(row):
    if row["allocation_axis"] == "y":
        return "vertical-short" if row["box"][3] <= 120 else "vertical-long"
    return "horizontal-short" if launch.render.short_frame(row) else "horizontal-other"


def snapshot():
    core.verify_methods()
    result = core.load(AUDIT / "result.json")
    diagnosed = core.load(AUDIT / "diagnosis.json")
    receipt = delivery / "received.json"
    evidence = launch.OUT / "reference-evidence.json"
    if (diagnosed["result_sha256"] != core.sha(AUDIT / "result.json")
            or result["receipts_sha256"] != core.sha(receipt)
            or result["reference_sha256"] != core.sha(evidence)):
        raise ValueError("確定した原票と判定が異なる")
    issues = {(r["page"], r["line_index"]): r["reason"] for r in diagnosed["issues"]}
    if len(issues) != 27 or any(r["outcome"] != "insufficient" for r in diagnosed["issues"]):
        raise ValueError("既知の参照不足27行を確認できない")
    original = launch.OUT / "selection.json"
    rows = core.load(original)["selected"]
    manifest = delivery / "packages.json"
    files = core.load(manifest)
    grading = core.load(evidence)
    recorded = {}
    controls = defaultdict(list)
    for pack, batch in files["packs"].items():
        (label, binding), = batch["mapping"].items()
        row = rows[binding["entry"]]
        expected = {core.ref.NORMALIZE(t["text"]) for t in row["targets"].values() if t["known"]}
        if len(expected) != 1:
            continue
        row = {**row, "effective": expected.pop()}
        identity = key(row)
        recorded[identity] = (pack, batch, label, binding, row)
        entry = grading[f"{identity[0]}/{identity[1]}"]
        if identity not in issues and entry["evidence"] == "image-only" and entry["answer"]["text"] == row["effective"]:
            rank = sha256(f"adr0025-v71-control\0{identity[0]}\0{identity[1]}".encode()).hexdigest()
            controls[shape(row)].append((rank, identity))
    if len(controls) != 4 or any(len(v) < 2 for v in controls.values()):
        raise ValueError("形状の各群で一致対照を2行選べない")
    selected = {**issues, **{identity: "control" for group in controls.values()
                             for _, identity in sorted(group)[:2]}}
    checks, jobs, ready = {}, {}, []
    for identity, category in sorted(selected.items()):
        pack, batch, label, binding, row = recorded[identity]
        request = batch["request"]
        cards = delivery / "cards" / pack
        if request["ids"] != [label] or [core.sha(cards / f) for f in request["images"]] != request["image_sha256"]:
            raise ValueError("固定した一行一束の画像が異なる")
        checks[pack] = {**binding, "entry": len(ready), "category": category, "shape": shape(row)}
        jobs[f"{pack}/high"] = {"cards": str(cards), "request": request}
        ready.append(row)
    pilot.SAMPLES = ready
    display = pilot.OUT / "display/selection.json"
    display.parent.mkdir(parents=True)
    core.save_once(display, core.encoded({"selected": ready}))
    sources = (Path(__file__), HERE / "protocol.md", base, Path(judge.__file__), AUDIT / "diagnosis.json",
               AUDIT / "result.json", receipt, evidence, original, manifest, display)
    pins = core.load(core.LOCK)["inputs"] | {str(f): core.sha(f) for f in sources}
    return {"jobs": jobs, "mapping": checks, "files": pins, "efforts": {"saved": "medium", "new": "high"}}


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
            past = core.transport.attempts(old, pack, role)
            if past != receipt["votes"][pack][role] or past[-1]["receipt"]["availability"] != "received":
                raise ValueError("既存監査の確定原票と異なる")
            prior_vote = past[-1]["receipt"]
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
            prior.append(core.ref.decoded(prior_vote["answers"][label], link["partitions"]))
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
    if len(sys.argv) > 1 and sys.argv[1] == "compare":
        compare()
    else:
        pilot.snapshot = snapshot
        pilot.audit.readers.command = high
        pilot.main()
