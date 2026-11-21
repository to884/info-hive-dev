"""旧指示の括弧8行をFableで第三読し、保存済みの新指示の票と比べる。"""

import argparse
from collections import Counter
import importlib.util
import json
from pathlib import Path

HERE = Path(__file__).resolve().parent
ANALYZER = HERE.parent / "model-vote-comparison/analyze.py"
FAMILY_RESULT = HERE.parent / "family-vote-comparison/result.json"
FAMILY_SHA = "b9e7c8f6b2cd5a1078a6c207ba1528a09a95091cb406339b6bda17d910a3e273"
spec = importlib.util.spec_from_file_location("saved_votes", ANALYZER)
saved = importlib.util.module_from_spec(spec)
spec.loader.exec_module(saved)
fable = saved.load_runner("saved_fable", "fable-third")
base, trial = fable.base, fable.trial
MODEL = fable.MODEL
OUT = trial.ROOT / "old-bracket-fable-third"
LABELS = ("correct", "wrong", "unresolved")


def original():
    rows, directory, first, requests, _, _, sessions, input_record = fable.original()
    previous = saved.record(fable, saved.BRACKET_SHA, saved.BRACKET_LOCK_SHA, input_record)
    if base.sha(FAMILY_RESULT) != FAMILY_SHA:
        raise ValueError("前回の異系統集計が変化")
    family = base.load(FAMILY_RESULT)
    if family["family"] != {"sol": "GPT", "astra": "GPT", "fable": "Claude", "opus": "Claude"}:
        raise ValueError("系統の割付が異なる")
    thirds = saved.claude_votes(fable.reader, fable.OUT, previous["receipts"],
                                {a: requests[a][3] for a in fable.ARMS})
    past = sessions | {r["session"] for r in previous["receipts"]}
    brackets = [r for r in rows if r["case"] in ("2a", "2b")]
    ids = [r["id"] for r in brackets]
    studies = family["bracket"]
    old, new = (studies[a]["fable"]["rows"] for a in ("old", "new"))
    if len(ids) != 8 or [r["id"] for r in old] != ids or [r["id"] for r in new] != ids:
        raise ValueError("固定の括弧8行を再現できない")
    if set(ids) & set(requests["old"][3]["ids"]) or not set(ids) <= set(requests["new"][3]["ids"]):
        raise ValueError("旧・新の第三読対象が記録と異なる")
    pack = {k: requests["new"][3][k] for k in ("images", "image_sha256")}
    pack.update(ids=ids, prompt=trial.prompt("old", ids))
    fixed = {
        "script_sha256": base.sha(Path(__file__)), "agreement_code_sha256": base.sha(ANALYZER),
        "comparison_lock_sha256": input_record["comparison_lock_sha256"],
        "fable_lock_sha256": saved.BRACKET_LOCK_SHA, "fable_result_sha256": saved.BRACKET_SHA,
        "family_result_sha256": FAMILY_SHA, "model": MODEL, "effort": "medium", "old_pack": pack,
        "new_saved_scope_ids": requests["new"][3]["ids"],
    }
    return brackets, directory, first, thirds["new"], studies, past, fixed


def prepare():
    *_, fixed = original()
    fixed["fixed_at"] = base.utc_now()
    base.write_json(HERE / "lock.json", fixed)
    print("固定", base.sha(HERE / "lock.json"), "旧の括弧8行", flush=True)


def decide(first, third, arm, i, gold):
    sol, astra = first[arm][1][i], first[arm][2][i]
    value, _ = saved.decision([("GPT", sol), ("GPT", astra), ("Claude", third)], True)
    match = [name for name, vote in (("sol", sol), ("astra", astra)) if third is not None and third == vote]
    return {"fable_vote": saved.status(gold, third), "matching_gpt_models": match,
            "distinct_families_required": saved.status(gold, value)}


def run(exe, expected):
    path = HERE / "lock.json"
    if base.sha(path) != expected:
        raise ValueError("指定された固定SHAと異なる")
    rows, directory, first, new_third, prior, past, fixed = original()
    if {k: v for k, v in base.load(path).items() if k != "fixed_at"} != fixed:
        raise ValueError("固定後に入力が変化")
    reader = fable.load_module("old_bracket_reader", fable.sol_run.OPUS_RUN)
    reader.MODEL, reader.OUT = MODEL, OUT
    OUT.mkdir(parents=True)
    old_third, receipt = reader.read_opus(exe, "old", fixed["old_pack"], directory)
    if original()[-1] != fixed or base.sha(path) != expected or receipt["session"] in past:
        raise ValueError("読みの前後で入力が変化したかセッションが重複")
    decisions = []
    prior_new = {r["id"]: r["distinct_families_required"] for r in prior["new"]["fable"]["rows"]}
    old_baseline = {r["id"]: r["distinct_families_required"] for r in prior["old"]["fable"]["rows"]}
    for row in rows:
        i, gold = row["id"], base.normalize(row["gold"])
        old_data = decide(first, old_third[i], "old", i, gold)
        new_data = decide(first, new_third[i], "new", i, gold)
        if new_data["distinct_families_required"] != prior_new[i]:
            raise ValueError("保存済み新指示の集計と違う")
        decisions.append({"id": i, "old_without_third": old_baseline[i], "old": old_data, "new": new_data})
    summary = {}
    for arm in ("old", "new"):
        counts = {}
        for field in ("fable_vote", "distinct_families_required"):
            tally = Counter(r[arm][field] for r in decisions)
            counts[field] = {k: tally[k] for k in LABELS}
        summary[arm] = counts
    result = {"finished": base.utc_now(), "lock_sha256": expected, "receipt": receipt,
              "summary": summary, "row_outcomes": decisions}
    base.write_json(HERE / "result.json", result)
    print(json.dumps(summary, ensure_ascii=False), flush=True)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("action", choices=("prepare", "run"))
    parser.add_argument("--claude", type=Path)
    parser.add_argument("--lock-sha256")
    args = parser.parse_args()
    if args.action == "prepare":
        prepare()
    else:
        run(args.claude.resolve(), args.lock_sha256)
