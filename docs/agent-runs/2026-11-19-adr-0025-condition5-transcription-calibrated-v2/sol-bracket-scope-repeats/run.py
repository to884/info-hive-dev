"""Solで依頼範囲8行・32行と旧・新指示の4条件を各3回測る。"""

import argparse
from collections import Counter
from concurrent.futures import ThreadPoolExecutor
import importlib.util
import json
from pathlib import Path
from shutil import copyfile

HERE = Path(__file__).resolve().parent
SOURCE = HERE.parent / "eight-bracket-sol-reread/run.py"
SOURCE_LOCK_SHA = "ab5736458b69eb585edb498298486c38ac2c963aa0b1303f78c5fe9c6722f90d"
SOURCE_RESULT_SHA = "4712d12ddf757d645b4713ddfd689ba09823ae39b51ede812d824fcd7129e027"
spec = importlib.util.spec_from_file_location("saved_eight_sol", SOURCE)
prior = importlib.util.module_from_spec(spec)
spec.loader.exec_module(prior)
base, trial, MODEL = prior.base, prior.trial, prior.MODEL
OUT = trial.ROOT / "sol-bracket-scope-repeats"
ARMS = ("old", "new")
LABELS = ("correct", "wrong", "unresolved")
SCHEDULE = [
    ["8-old", "32-new", "32-old", "8-new"],
    ["32-old", "8-new", "8-old", "32-new"],
    ["8-new", "32-old", "32-new", "8-old"],
]


def original():
    brackets, directory, first, _, past, source = prior.original()
    lock_file, result_file = SOURCE.parent / "lock.json", SOURCE.parent / "result.json"
    if base.sha(lock_file) != SOURCE_LOCK_SHA or base.sha(result_file) != SOURCE_RESULT_SHA:
        raise ValueError("前回のSol再読の固定または結果が変化")
    if {k: v for k, v in base.load(lock_file).items() if k != "fixed_at"} != source:
        raise ValueError("前回のSol再読の入力が再現しない")
    previous = base.load(result_file)
    if previous["lock_sha256"] != SOURCE_LOCK_SHA:
        raise ValueError("前回のSol再読と固定SHAがつながらない")
    other = prior.prior.fable.sol_run.opus_run
    rows, full_dir, baseline, full_votes, full_requests, _ = other.original()
    if len(rows) != 32 or len(brackets) != 8 or full_dir != directory or any(
        first[a][1] != full_votes[a][1] for a in ARMS
    ):
        raise ValueError("初回の32行または評価対象の括弧8行が異なる")
    if {a: sorted((r["read"], r["model"]) for r in baseline["receipts"] if r["arm"] == a)
            for a in ARMS} != {a: [(1, MODEL), (2, "gpt-6.2-astra"), (3, "gpt-6.2-astra")] for a in ARMS}:
        raise ValueError("初回Solの受領が見つからない")
    packs = {
        f"{size}-{a}": {k: request[k] for k in ("ids", "images", "image_sha256", "prompt")}
        for a in ARMS for size, request in ((8, source["packs"][a]), (32, full_requests[a][1]))
    }
    ids = {"8": [r["id"] for r in brackets], "32": [r["id"] for r in rows]}
    reference = packs["8-old"]
    for label, pack in packs.items():
        size, arm = label.split("-")
        if (pack["ids"] != ids[size] or pack["prompt"] != trial.prompt(arm, pack["ids"])
                or pack["images"] != reference["images"] or pack["image_sha256"] != reference["image_sha256"]):
            raise ValueError("対象・指示・画像・順序の固定が異なる")
    for size in (8, 32):
        new_prompt = packs[f"{size}-new"]["prompt"]
        if new_prompt.count(base.EXTRA) != 1 or new_prompt.replace(base.EXTRA, "", 1) != packs[f"{size}-old"]["prompt"]:
            raise ValueError("旧・新の指示が一文差ではない")
    prior_counts = {
        a: sum(first[a][1][r["id"]] == base.normalize(r["gold"]) for r in brackets) for a in ARMS
    }
    if any(prior_counts[a] != previous["summary"][a]["initial_sol"]["correct"] for a in ARMS):
        raise ValueError("初回Solの正解数が原票から再現しない")
    fixed = {
        "script_sha256": base.sha(Path(__file__)), "source_script_sha256": source["script_sha256"],
        "source_lock_sha256": SOURCE_LOCK_SHA, "source_result_sha256": SOURCE_RESULT_SHA,
        "comparison_lock_sha256": source["comparison_lock_sha256"],
        "model": MODEL, "effort": "medium", "packs": packs, "schedule": SCHEDULE,
        "scored_ids": ids["8"], "initial_sol_correct": prior_counts,
    }
    return rows, brackets, directory, past | {r["session"] for r in previous["receipts"]}, fixed


def prepare():
    *_, fixed = original()
    fixed["fixed_at"] = base.utc_now()
    base.write_json(HERE / "lock.json", fixed)
    print("固定", base.sha(HERE / "lock.json"), "4条件×3回、判定対象8行", flush=True)


def read_one(exe, study, rows, directory, condition, repeat, pack):
    size, arm = condition.split("-")
    subset = [r for r in rows if r["id"] in pack["ids"]]
    if [r["id"] for r in subset] != pack["ids"] or len(subset) != int(size):
        raise ValueError("実行する対象が固定と異なる")
    sheets = dict.fromkeys(str(r["sheet"]) for r in subset)
    if [n for s in sheets for n in study["image_order_by_sheet"][s]] != pack["images"]:
        raise ValueError("対象から展開した画像の順序が固定と異なる")
    runner_spec = importlib.util.spec_from_file_location(f"vision_{condition}_{repeat}", base.__file__)
    reader = importlib.util.module_from_spec(runner_spec)
    runner_spec.loader.exec_module(reader)
    dst = OUT / f"round-{repeat:02d}" / condition
    dst.mkdir(parents=True)
    for name, digest in zip(pack["images"], pack["image_sha256"], strict=True):
        copyfile(directory / name, dst / name)
        if base.sha(dst / name) != digest:
            raise ValueError("配布用画像のSHAが違う")
    reader.PRIVATE, reader.prompt_for = dst, trial.prompt
    answers, receipt = reader.read_images(exe, study, subset, arm, 1, MODEL)
    request = base.load(dst / f"{arm}-read1-{MODEL}-request.json")
    if request["model"] != MODEL or any(request[k] != v for k, v in pack.items()):
        raise ValueError("送信した画像・指示・対象が固定と異なる")
    receipt.update(condition=condition, repeat=repeat)
    return answers, receipt


def run(exe, expected):
    lock_file = HERE / "lock.json"
    if base.sha(lock_file) != expected:
        raise ValueError("指定の固定SHAと異なる")
    rows, brackets, directory, past, fixed = original()
    if {k: v for k, v in base.load(lock_file).items() if k != "fixed_at"} != fixed:
        raise ValueError("固定後に入力が変化")
    study, _, _ = trial.check("comparison", fixed["comparison_lock_sha256"])
    OUT.mkdir(parents=True)
    records, receipts = [], []
    with ThreadPoolExecutor(max_workers=4) as pool:
        for n, order in enumerate(fixed["schedule"], 1):
            jobs = {c: pool.submit(read_one, exe, study, rows, directory, c, n, fixed["packs"][c])
                    for c in order}
            for condition, future in jobs.items():
                answers, receipt = future.result()
                receipts.append(receipt)
                decisions = {}
                for r in brackets:
                    i, gold = r["id"], base.normalize(r["gold"])
                    decisions[i] = prior.prior.old.saved.status(gold, answers[i])
                tally = Counter(decisions.values())
                records.append({"repeat": n, "condition": condition, "rows": decisions,
                                "counts": {k: tally[k] for k in LABELS}})
    if original()[-1] != fixed or base.sha(lock_file) != expected:
        raise ValueError("読みの前後で入力が変化")
    sessions = {r["session"] for r in receipts}
    if len(sessions) != 12 or sessions & past:
        raise ValueError("12件の新規セッションがそろわないか過去と重複")
    scores = {c: [r["counts"]["correct"] for r in records if r["condition"] == c]
              for c in fixed["packs"]}
    comparison = {}
    for size in ("8", "32"):
        pairs = list(zip(scores[f"{size}-old"], scores[f"{size}-new"], strict=True))
        comparison[size] = {
            "old_new_by_round": pairs,
            "initial_pattern_matches": sum(pair == (0, 8) for pair in pairs),
            "new_higher": sum(new > old for old, new in pairs),
        }
    result = {"finished": base.utc_now(), "lock_sha256": expected, "receipts": receipts,
              "scores": scores, "comparison": comparison, "runs": records}
    base.write_json(HERE / "result.json", result)
    print(json.dumps({"scores": scores, "comparison": comparison}, ensure_ascii=False), flush=True)


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
