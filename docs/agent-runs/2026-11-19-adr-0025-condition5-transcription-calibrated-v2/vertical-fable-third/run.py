"""縦列の未決定行を新規Fableで第三読し、Sol・Astraと比較する。"""

import argparse
from collections import Counter
from concurrent.futures import ThreadPoolExecutor
import importlib.util
import json
from pathlib import Path

HERE = Path(__file__).resolve().parent
SOURCE = HERE.parent / "vertical-astra-third/run.py"
ASTRA_LOCK_SHA = "629d8e9448d6478916857444332d3c3fb03c4fda37858f5e4ecdfea00ac2dc07"
ASTRA_RESULT_SHA = "a228e6e7502bb3d9af3d81b65caa934697b55ddd28513a406a1960566f793646"
spec = importlib.util.spec_from_file_location("previous_astra", SOURCE)
astra = importlib.util.module_from_spec(spec)
spec.loader.exec_module(astra)
base, trial, rep = astra.base, astra.trial, astra.rep
vertical = astra.runner.vertical
ARMS = astra.ARMS
MODEL = vertical.MODELS["fable"]
OUT = trial.ROOT / "vertical-fable-third"


def original():
    rows, directory, sessions, previous, votes, _, fixed = astra.original()
    lock_file, result_file = SOURCE.parent / "lock.json", SOURCE.parent / "result.json"
    if base.sha(lock_file) != ASTRA_LOCK_SHA or base.sha(result_file) != ASTRA_RESULT_SHA:
        raise ValueError("Astraの固定記録または集計が変化")
    if {k: v for k, v in base.load(lock_file).items() if k != "fixed_at"} != fixed:
        raise ValueError("Astraの固定元が異なる")
    astra_result = base.load(result_file)
    sol_result = base.load(astra.SOURCE.parent / "result.json")
    if astra_result["lock_sha256"] != ASTRA_LOCK_SHA:
        raise ValueError("Astraの固定記録と集計がつながらない")
    thirds = {
        "sol": astra.third_votes(astra.SOL_OUT, astra.SOL_MODEL, sol_result, fixed),
        "astra": astra.third_votes(astra.OUT, astra.MODEL, astra_result, fixed),
    }
    final = {who: {a: astra.with_third(rows, votes, group, a) for a in ARMS}
             for who, group in thirds.items()}
    for who, result in (("sol", sol_result), ("astra", astra_result)):
        if result["two_reads"] != previous["old_vs_new"] or base.paired(
            rows, final[who]["old"], final[who]["new"]
        ) != result["three_reads"]:
            raise ValueError(f"{who}の原票から過去の比較を再現できない")
    recent = {r["session"] for r in astra_result["receipts"]}
    if len(recent) != 2 or recent & sessions:
        raise ValueError("Astraの第三読セッションが重複")
    fixed.update(model=MODEL, previous_script_sha256=fixed["script_sha256"],
                 script_sha256=base.sha(Path(__file__)), astra_lock_sha256=ASTRA_LOCK_SHA,
                 astra_result_sha256=ASTRA_RESULT_SHA)
    return rows, directory, sessions | recent, votes, previous, final, fixed


def prepare():
    *_, fixed = original()
    fixed["fixed_at"] = base.utc_now()
    base.write_json(HERE / "lock.json", fixed)
    print("固定", base.sha(HERE / "lock.json"),
          {a: len(p["ids"]) for a, p in fixed["packs"].items()}, flush=True)


def run(exe, expected):
    lock_file = HERE / "lock.json"
    if base.sha(lock_file) != expected:
        raise ValueError("指定の固定SHAと異なる")
    rows, directory, past, votes, before, final, fixed = original()
    if {k: v for k, v in base.load(lock_file).items() if k != "fixed_at"} != fixed:
        raise ValueError("固定後に入力が変化")
    reader = vertical.prior.load_module("fable_vertical_third", vertical.prior.sol_run.OPUS_RUN)
    reader.MODEL, reader.OUT = MODEL, OUT
    OUT.mkdir(parents=True)
    with ThreadPoolExecutor(max_workers=2) as pool:
        jobs = {a: pool.submit(reader.read_opus, exe, a, fixed["packs"][a], directory) for a in ARMS}
        returned = {a: jobs[a].result() for a in ARMS}
    if original()[-1] != fixed or base.sha(lock_file) != expected:
        raise ValueError("読みの前後で入力が変化")
    receipts = [returned[a][1] for a in ARMS]
    sessions = {r["session"] for r in receipts}
    if len(sessions) != 2 or sessions & past:
        raise ValueError("読取セッションが重複")
    third = {a: returned[a][0] for a in ARMS}
    final["fable"] = {a: astra.with_third(rows, votes, third, a) for a in ARMS}
    paired = {who: base.paired(rows, panel["old"], panel["new"]) for who, panel in final.items()}
    output = {
        "finished": base.utc_now(), "lock_sha256": expected, "receipts": receipts,
        "two_reads": before["old_vs_new"], "old_vs_new": paired,
        "changes_from_prior": {
            who: {a: base.paired(rows, final[who][a], final["fable"][a]) for a in ARMS}
            for who in ("sol", "astra")
        },
        "third_vote": {
            a: dict(Counter("unreadable" if v is None
                            else "matches_first_fable" if v == votes[a, "fable"][i]
                            else "matches_first_opus" if v == votes[a, "opus"][i]
                            else "matches_neither" for i, v in third[a].items()))
            for a in ARMS
        },
        "row_outcomes": [
            {"id": r["id"], "case": r["case"],
             **{a: {who: rep.metrics([r], panel[a]) for who, panel in final.items()} for a in ARMS}}
            for r in rows
        ],
    }
    base.write_json(HERE / "result.json", output)
    print(json.dumps({"summary": {who: pair["all"] for who, pair in paired.items()},
                      "third_vote": output["third_vote"]}, ensure_ascii=False), flush=True)


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
