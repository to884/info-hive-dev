"""Fableの第三票を、同じ初回票を使ったAstra・Opus・Solの結果と比較する。"""

import argparse
from concurrent.futures import ThreadPoolExecutor
import importlib.util
import json
from pathlib import Path

HERE = Path(__file__).resolve().parent
SOL_RUN = HERE.parent / "sol-third/run.py"
SOL_LOCK_SHA = "db9bdc7dda0dde3ce68ab4578f64a7ed63dc0f4affbc09f28062206306592675"
SOL_RESULT_SHA = "0203722b4c0c70fcbb2717213bfba816ecc637f668df84f72fd9708b41e126e5"
MODEL = "claude-fable-5-2"


def load_module(name, path):
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


sol_run = load_module("sol_third", SOL_RUN)
base, trial, rep = sol_run.base, sol_run.trial, sol_run.rep
ARMS = sol_run.ARMS
OUT = trial.ROOT / "fable-third"
# 前回のClaude画像添付と応答検証を、別のモジュール状態でFableに適用する。
reader = load_module("fable_image_reader", sol_run.OPUS_RUN)
reader.MODEL = MODEL
reader.OUT = OUT


def original():
    rows, directory, baseline, opus, first, requests, opus_votes, prior = sol_run.original()
    lock_file, result_file = SOL_RUN.parent / "lock.json", SOL_RUN.parent / "result.json"
    if base.sha(lock_file) != SOL_LOCK_SHA or base.sha(result_file) != SOL_RESULT_SHA:
        raise ValueError("Solの固定記録または結果が違う")
    sol = base.load(result_file)
    if sol["lock_sha256"] != SOL_LOCK_SHA or {
        k: v for k, v in base.load(lock_file).items() if k != "fixed_at"
    } != prior:
        raise ValueError("Solの比較と固定元がつながらない")
    sol_votes, hashes = {}, {}
    for receipt in sol["receipts"]:
        arm = receipt["arm"]
        prefix = f"{arm}-read3-{sol_run.MODEL}"
        raw = sol_run.OUT / f"{prefix}-{receipt['attempt']}.jsonl"
        req_file = sol_run.OUT / f"{prefix}-request.json"
        req = base.load(req_file)
        hashes[raw.name], hashes[req_file.name] = base.sha(raw), base.sha(req_file)
        if (arm in sol_votes or receipt["model"] != sol_run.MODEL
                or hashes[raw.name] != receipt["response_sha256"]
                or any(req[k] != requests[arm][3][k] for k in ("ids", "images", "image_sha256", "prompt"))
                or sol_run.opus_run.digest(req["prompt"].encode("utf-8")) != receipt["prompt_sha256"]):
            raise ValueError("Solの原票と入力の組が違う")
        session, _, answers = base.parse_response(raw.read_text(encoding="utf-8"), req["ids"])
        if session != receipt["session"]:
            raise ValueError("Solの原票とセッションが違う")
        sol_votes[arm] = answers
    if set(sol_votes) != set(ARMS):
        raise ValueError("Solの第三票が両群にない")
    fixed = {**prior, "previous_script_sha256": prior["script_sha256"],
             "script_sha256": base.sha(Path(__file__)), "model": MODEL, "effort": "medium",
             "sol_lock_sha256": SOL_LOCK_SHA, "sol_result_sha256": SOL_RESULT_SHA,
             "sol_original_sha256": hashes}
    now = {"astra": {a: first[a][3] for a in ARMS}, "opus": opus_votes, "sol": sol_votes}
    past_sessions = {r["session"] for record in (baseline, opus, sol) for r in record["receipts"]}
    return rows, directory, first, requests, now, sol, past_sessions, fixed


def prepare():
    *_, fixed = original()
    fixed["fixed_at"] = base.utc_now()
    base.write_json(HERE / "lock.json", fixed)
    print("固定", base.sha(HERE / "lock.json"),
          {a: len(p["ids"]) for a, p in fixed["packs"].items()}, flush=True)


def run(exe, expected):
    path = HERE / "lock.json"
    if base.sha(path) != expected:
        raise ValueError("指定された固定SHAと異なる")
    rows, directory, first, requests, raw, sol, past_sessions, fixed = original()
    if {k: v for k, v in base.load(path).items() if k != "fixed_at"} != fixed:
        raise ValueError("固定後に入力が変化")
    OUT.mkdir(parents=True)
    with ThreadPoolExecutor(max_workers=2) as pool:
        jobs = {a: pool.submit(reader.read_opus, exe, a, requests[a][3], directory) for a in ARMS}
        received = {a: jobs[a].result() for a in ARMS}
    if original()[-1] != fixed or base.sha(path) != expected:
        raise ValueError("読みの前後で入力が変化")
    receipts = [received[a][1] for a in ARMS]
    sessions = {r["session"] for r in receipts}
    if len(sessions) != 2 or sessions & past_sessions:
        raise ValueError("読取セッションが重複")
    raw["fable"] = {a: received[a][0] for a in ARMS}
    base.metrics = rep.metrics
    ids = [r["id"] for r in rows]
    final = {name: {a: sol_run.opus_run.fold(ids, first[a], group[a]) for a in ARMS}
             for name, group in raw.items()}
    paired = {name: base.paired(rows, group["old"], group["new"]) for name, group in final.items()}
    if any(paired[name] != previous for name, previous in sol["old_vs_new"].items()):
        raise ValueError("過去3方式の結果を原票から再現できない")
    double = [r for r in rows if r["case"] in ("2a", "2b")]
    result = {
        "finished": base.utc_now(), "lock_sha256": expected, "receipts": receipts,
        "old_vs_new": paired,
        "changes_from_prior": {
            name: {a: base.paired(rows, final[name][a], final["fable"][a]) for a in ARMS}
            for name in ("astra", "opus", "sol")
        },
        "double_bracket": {name: base.paired(double, group["old"], group["new"])
                           for name, group in final.items()},
        "fable_double_votes": [
            {"id": r["id"], "third_status": "unreadable" if raw["fable"]["new"][r["id"]] is None else "known",
             "matches_first_sol": raw["fable"]["new"][r["id"]] == first["new"][1][r["id"]],
             "matches_first_astra": raw["fable"]["new"][r["id"]] == first["new"][2][r["id"]],
             "final": rep.metrics([r], final["fable"]["new"])}
            for r in double
        ],
        "row_outcomes": [
            {"id": r["id"], "case": r["case"],
             **{a: {name: rep.metrics([r], group[a]) for name, group in final.items()} for a in ARMS}}
            for r in rows
        ],
    }
    base.write_json(HERE / "result.json", result)
    print(json.dumps({k: result[k] for k in ("old_vs_new", "fable_double_votes")}, ensure_ascii=False), flush=True)


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
