"""初回票を固定したままSolの第三読をAstra・Opusと比較する。"""

import argparse
from concurrent.futures import ThreadPoolExecutor
import importlib.util
import json
from pathlib import Path
from shutil import copyfile

HERE = Path(__file__).resolve().parent
OPUS_RUN = HERE.parent / "opus-third/run.py"
OPUS_LOCK_SHA = "4b626097bb54cea9558e6e26f17f0434b6630c3c4a9c52074614b46837ee2e81"
OPUS_RESULT_SHA = "b60d39903ad923bb2e5951661fd71ca6e407b037e66d2286bcd858a8741fc912"
spec = importlib.util.spec_from_file_location("opus_third", OPUS_RUN)
opus_run = importlib.util.module_from_spec(spec)
spec.loader.exec_module(opus_run)
base, trial, rep = opus_run.base, opus_run.trial, opus_run.rep
MODEL = "gpt-6.2-sol"
ARMS = opus_run.ARMS
OUT = trial.ROOT / "sol-third"


def original():
    rows, directory, baseline, votes, requests, previous = opus_run.original()
    opus_lock_file = OPUS_RUN.parent / "lock.json"
    opus_result_file = OPUS_RUN.parent / "result.json"
    if base.sha(opus_lock_file) != OPUS_LOCK_SHA or base.sha(opus_result_file) != OPUS_RESULT_SHA:
        raise ValueError("Opusの固定記録または集計が違う")
    opus_result = base.load(opus_result_file)
    if opus_result["lock_sha256"] != OPUS_LOCK_SHA:
        raise ValueError("Opusの集計と固定記録がつながらない")
    opus_votes, opus_raw_hashes = {}, {}
    for receipt in opus_result["receipts"]:
        arm = receipt["arm"]
        raw = opus_run.OUT / f"{arm}-response.jsonl"
        sha = base.sha(raw)
        req = requests[arm][3]
        if (arm in opus_votes or sha != receipt["response_sha256"]
                or req["images"] != receipt["images"] or req["image_sha256"] != receipt["image_sha256"]
                or opus_run.digest(req["prompt"].encode("utf-8")) != receipt["prompt_sha256"]):
            raise ValueError("Opusの原票と入力の組が違う")
        answers, result = opus_run.parse(raw.read_text(encoding="utf-8"), req["ids"])
        if result["session_id"] != receipt["session"]:
            raise ValueError("Opusの原票とセッションが違う")
        opus_votes[arm] = answers
        opus_raw_hashes[raw.name] = sha
    expected = {(arm, read, model) for arm in ARMS
                for read, model in enumerate(("gpt-6.2-sol", "gpt-6.2-astra", "gpt-6.2-astra"), 1)}
    if len(baseline["receipts"]) != 6 or {
        (r["arm"], r["read"], r["model"]) for r in baseline["receipts"]
    } != expected or set(opus_votes) != set(ARMS):
        raise ValueError("過去の票の数または担当が違う")
    fixed = {
        **previous, "previous_script_sha256": previous["script_sha256"],
        "script_sha256": base.sha(Path(__file__)), "model": MODEL, "effort": "medium",
        "opus_lock_sha256": OPUS_LOCK_SHA, "opus_result_sha256": OPUS_RESULT_SHA,
        "opus_original_sha256": opus_raw_hashes,
    }
    return rows, directory, baseline, opus_result, votes, requests, opus_votes, fixed


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
    rows, directory, baseline, opus_result, votes, requests, opus_votes, fixed = original()
    if {k: v for k, v in base.load(lock_file).items() if k != "fixed_at"} != fixed:
        raise ValueError("固定後に入力が変化")
    study_lock, _, _ = trial.check("comparison", opus_run.SOURCE_LOCK)
    OUT.mkdir(parents=True)
    names = {name for arm in ARMS for name in requests[arm][3]["images"]}
    for name in names:
        copyfile(directory / name, OUT / name)
        if base.sha(OUT / name) != study_lock["image_sha256"][name]:
            raise ValueError("配布用画像が固定画像と異なる")
    base.PRIVATE = OUT
    base.prompt_for = trial.prompt
    with ThreadPoolExecutor(max_workers=2) as pool:
        jobs = {
            a: pool.submit(base.read_images, exe, study_lock,
                           [r for r in rows if r["id"] in requests[a][3]["ids"]], a, 3, MODEL)
            for a in ARMS
        }
        returned = {a: jobs[a].result() for a in ARMS}
    if original()[-1] != fixed or base.sha(lock_file) != expected:
        raise ValueError("読みの前後で入力が変化")
    receipts = [returned[a][1] for a in ARMS]
    sessions = {r["session"] for r in receipts}
    if len(sessions) != 2 or sessions & {r["session"] for r in baseline["receipts"] + opus_result["receipts"]}:
        raise ValueError("過去の読取セッションと重複")
    for a, receipt in zip(ARMS, receipts, strict=True):
        req = requests[a][3]
        actual = base.load(OUT / f"{a}-read3-{MODEL}-request.json")
        if any(actual[k] != req[k] for k in ("ids", "images", "image_sha256", "prompt")):
            raise ValueError("過去の第三読と対象、画像または指示が違う")
        if receipt["prompt_sha256"] != fixed["packs"][a]["prompt_sha256"]:
            raise ValueError("指示の固定SHAが違う")
    base.metrics = rep.metrics
    ids = [r["id"] for r in rows]
    raw = {"astra": {a: votes[a][3] for a in ARMS}, "opus": opus_votes,
           "sol": {a: returned[a][0] for a in ARMS}}
    final = {name: {a: opus_run.fold(ids, votes[a], group[a]) for a in ARMS} for name, group in raw.items()}
    paired = {name: base.paired(rows, group["old"], group["new"]) for name, group in final.items()}
    if (paired["astra"] != opus_result["astra_third_old_vs_new"]
            or paired["opus"] != opus_result["opus_third_old_vs_new"]):
        raise ValueError("前回の第三読の集計を原票から再現できない")
    result = {
        "finished": base.utc_now(), "lock_sha256": expected, "receipts": receipts,
        "old_vs_new": paired,
        "changes_from_prior": {name: {a: base.paired(rows, final[name][a], final["sol"][a]) for a in ARMS}
                               for name in ("astra", "opus")},
        "raw_sol_votes": {
            a: {
                "targets": len(raw["sol"][a]),
                "unreadable": sum(v is None for v in raw["sol"][a].values()),
                "agree_known_initial_sol": sum(v is not None and v == votes[a][1][i]
                                               for i, v in raw["sol"][a].items()),
                "agree_known_initial_astra": sum(v is not None and v == votes[a][2][i]
                                                 for i, v in raw["sol"][a].items()),
            } for a in ARMS
        },
        "row_outcomes": [
            {"id": r["id"], "case": r["case"],
             **{a: {name: rep.metrics([r], group[a]) for name, group in final.items()} for a in ARMS}}
            for r in rows
        ],
    }
    base.write_json(HERE / "result.json", result)
    print(json.dumps({name: pair["all"] for name, pair in paired.items()}, ensure_ascii=False), flush=True)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("action", choices=("prepare", "run"))
    parser.add_argument("--codex", type=Path)
    parser.add_argument("--lock-sha256")
    args = parser.parse_args()
    if args.action == "prepare":
        prepare()
    else:
        run(args.codex.resolve(), args.lock_sha256)
