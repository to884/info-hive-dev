"""Fable・Opusの二票を固定し、未決定の縦列だけにSolの第三票を加える。"""

import argparse
from collections import Counter
from concurrent.futures import ThreadPoolExecutor
import importlib.util
import json
from pathlib import Path
from shutil import copyfile

HERE = Path(__file__).resolve().parent
SOURCE = HERE.parent / "vertical-reread/run.py"
SOURCE_LOCK = "36aceb2df1202e76316e12f176c43d81ed35111a5eab36ebd5c3b820963cc643"
SOURCE_RESULT = "c39c0b1a29f0a6f7ccdc577fd699d30440744812e04efdcdf9b98773ecf1dfff"
spec = importlib.util.spec_from_file_location("vertical", SOURCE)
vertical = importlib.util.module_from_spec(spec)
spec.loader.exec_module(vertical)
base, trial, rep = vertical.base, vertical.trial, vertical.rep
ARMS = vertical.ARMS
MODEL = "gpt-6.2-sol"
OUT = trial.ROOT / "vertical-sol-third"


def original():
    rows, directory, sessions, source = vertical.original()
    lock_file, result_file = SOURCE.parent / "lock.json", SOURCE.parent / "result.json"
    if base.sha(lock_file) != SOURCE_LOCK or base.sha(result_file) != SOURCE_RESULT:
        raise ValueError("縦列二読の固定記録または結果が変化")
    previous = base.load(result_file)
    if previous["lock_sha256"] != SOURCE_LOCK or {
        k: v for k, v in base.load(lock_file).items() if k != "fixed_at"
    } != source:
        raise ValueError("縦列二読の固定元がつながらない")
    votes, raw_hashes = {}, {}
    for receipt in previous["receipts"]:
        arm, model = receipt["arm"], receipt["model"]
        who = next(k for k, m in vertical.MODELS.items() if m == model)
        reader = vertical.prior.load_module(f"recorded_vertical_{who}", vertical.prior.sol_run.OPUS_RUN)
        reader.MODEL = model
        raw = vertical.OUT / who / f"{arm}-response.jsonl"
        request = source["packs"][arm]
        raw_hashes[f"{who}/{raw.name}"] = base.sha(raw)
        if ((arm, who) in votes or raw_hashes[f"{who}/{raw.name}"] != receipt["response_sha256"]
                or request["images"] != receipt["images"] or request["image_sha256"] != receipt["image_sha256"]
                or reader.digest(request["prompt"].encode("utf-8")) != receipt["prompt_sha256"]):
            raise ValueError("縦列二読の原票と依頼が一致しない")
        answers, response = reader.parse(raw.read_text(encoding="utf-8"), request["ids"])
        if response["session_id"] != receipt["session"] or receipt["session"] in sessions:
            raise ValueError("縦列二読のセッションが違う")
        votes[arm, who] = answers
        sessions.add(receipt["session"])
    if set(votes) != {(a, who) for a in ARMS for who in vertical.MODELS}:
        raise ValueError("既存の二票がそろわない")
    packs, before = {}, {}
    for a in ARMS:
        before[a] = {r["id"]: base.consensus([votes[a, who][r["id"]] for who in vertical.MODELS])
                     for r in rows}
        targets = [r["id"] for r in rows if before[a][r["id"]] is None]
        if targets != [r["id"] for r in previous["row_outcomes"] if r[a]["unknown"]]:
            raise ValueError("第三読の対象が元の未決定行と異なる")
        packs[a] = {k: source["packs"][a][k] for k in ("images", "image_sha256")}
        packs[a].update(ids=targets, prompt=trial.prompt(a, targets))
    if len(rows) != 12 or [len(packs[a]["ids"]) for a in ARMS] != [11, 10]:
        raise ValueError("縦列の対象数が異なる")
    fixed = {
        "comparison_lock_sha256": source["comparison_lock_sha256"],
        "vertical_lock_sha256": SOURCE_LOCK, "vertical_result_sha256": SOURCE_RESULT,
        "vertical_script_sha256": source["script_sha256"], "vertical_raw_sha256": raw_hashes,
        "script_sha256": base.sha(Path(__file__)), "model": MODEL, "effort": "medium", "packs": packs,
    }
    return rows, directory, sessions, previous, votes, before, fixed


def prepare():
    *_, fixed = original()
    fixed["fixed_at"] = base.utc_now()
    base.write_json(HERE / "lock.json", fixed)
    print("固定", base.sha(HERE / "lock.json"),
          {a: len(p["ids"]) for a, p in fixed["packs"].items()}, flush=True)


def run(exe, expected):
    lock_file = HERE / "lock.json"
    if base.sha(lock_file) != expected:
        raise ValueError("指定された固定SHAと異なる")
    rows, directory, past, previous, votes, before, fixed = original()
    if {k: v for k, v in base.load(lock_file).items() if k != "fixed_at"} != fixed:
        raise ValueError("固定後に入力が変化")
    study_lock, _, _ = trial.check("comparison", fixed["comparison_lock_sha256"])
    OUT.mkdir(parents=True)
    image_sha = {n: h for p in fixed["packs"].values()
                 for n, h in zip(p["images"], p["image_sha256"], strict=True)}
    for name, digest in image_sha.items():
        copyfile(directory / name, OUT / name)
        if base.sha(OUT / name) != digest:
            raise ValueError("配布用画像が固定画像と異なる")
    base.PRIVATE = OUT
    base.prompt_for = trial.prompt
    with ThreadPoolExecutor(max_workers=2) as pool:
        jobs = {a: pool.submit(base.read_images, exe, study_lock,
                               [r for r in rows if r["id"] in fixed["packs"][a]["ids"]], a, 3, MODEL)
                for a in ARMS}
        received = {a: jobs[a].result() for a in ARMS}
    if original()[-1] != fixed or base.sha(lock_file) != expected:
        raise ValueError("読みの前後で入力が変化")
    receipts = [received[a][1] for a in ARMS]
    sessions = {r["session"] for r in receipts}
    if len(sessions) != 2 or sessions & past:
        raise ValueError("読取セッションが重複")
    for a in ARMS:
        actual = base.load(OUT / f"{a}-read3-{MODEL}-request.json")
        if any(actual[k] != v for k, v in fixed["packs"][a].items()):
            raise ValueError("第三読に渡した画像、指示、対象が違う")
    base.metrics = rep.metrics
    if base.paired(rows, before["old"], before["new"]) != previous["old_vs_new"]:
        raise ValueError("縦列二読の結果を再現できない")
    final = {
        a: {i: base.consensus([votes[a, who][i] for who in vertical.MODELS] + [received[a][0].get(i)])
            for i in before[a]} for a in ARMS
    }
    result = {
        "finished": base.utc_now(), "lock_sha256": expected, "receipts": receipts,
        "two_reads": previous["old_vs_new"], "three_reads": base.paired(rows, final["old"], final["new"]),
        "changes_from_two_reads": {a: base.paired(rows, before[a], final[a]) for a in ARMS},
        "third_vote": {
            a: dict(Counter(
                "unreadable" if value is None
                else "matches_fable" if value == votes[a, "fable"][i]
                else "matches_opus" if value == votes[a, "opus"][i]
                else "matches_neither"
                for i, value in received[a][0].items()
            )) for a in ARMS
        },
        "row_outcomes": [
            {"id": r["id"], "case": r["case"],
             **{a: {"two_reads": rep.metrics([r], before[a]), "three_reads": rep.metrics([r], final[a])}
                for a in ARMS}} for r in rows
        ],
    }
    base.write_json(HERE / "result.json", result)
    print(json.dumps({k: result[k] for k in ("three_reads", "third_vote")}, ensure_ascii=False), flush=True)


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
