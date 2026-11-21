"""初回二票が判読不能だった縦列12行を、Fable・Opusで二読する。"""

import argparse
from collections import Counter
from concurrent.futures import ThreadPoolExecutor
import importlib.util
import json
from pathlib import Path

HERE = Path(__file__).resolve().parent
FABLE_RUN = HERE.parent / "fable-third/run.py"
SOURCE_LOCK = "f994af109ea09c180e8b3025e5331c61bcd1f7c6ae010ebbcb6bec13d6f0dcb2"
SOURCE_RESULT = "e06be89a3384095433b886efc608a4b276f436c025d0613c070b8671d4130f84"
spec = importlib.util.spec_from_file_location("fable_third", FABLE_RUN)
prior = importlib.util.module_from_spec(spec)
spec.loader.exec_module(prior)
base, trial, rep = prior.base, prior.trial, prior.rep
ARMS = prior.ARMS
MODELS = {"fable": prior.MODEL, "opus": prior.sol_run.opus_run.MODEL}
OUT = trial.ROOT / "vertical-reread"


def original():
    rows, directory, first, requests, _, _, sessions, before = prior.original()
    lock_file, result_file = FABLE_RUN.parent / "lock.json", FABLE_RUN.parent / "result.json"
    if base.sha(lock_file) != SOURCE_LOCK or base.sha(result_file) != SOURCE_RESULT:
        raise ValueError("Fable比較の固定記録または集計が異なる")
    if {k: v for k, v in base.load(lock_file).items() if k != "fixed_at"} != before:
        raise ValueError("Fable比較の固定元が合わない")
    source = base.load(result_file)
    if source["lock_sha256"] != SOURCE_LOCK:
        raise ValueError("Fable比較と固定記録がつながらない")
    fable_hashes = {}
    for receipt in source["receipts"]:
        arm = receipt["arm"]
        path = prior.OUT / f"{arm}-response.jsonl"
        fable_hashes[path.name] = base.sha(path)
        _, result = prior.reader.parse(path.read_text(encoding="utf-8"), requests[arm][3]["ids"])
        if fable_hashes[path.name] != receipt["response_sha256"] or result["session_id"] != receipt["session"]:
            raise ValueError("Fable比較の原票が確認できない")
    sessions |= {r["session"] for r in source["receipts"]}
    targets_by_arm = {a: [r for r in rows if all(first[a][n][r["id"]] is None for n in (1, 2))]
                      for a in ARMS}
    targets = targets_by_arm["old"]
    ids = [r["id"] for r in targets]
    if (len(rows) != 32 or len(targets) != 12 or targets != targets_by_arm["new"]
            or any(not r["case"].startswith("v") for r in targets)
            or ids != requests["old"][3]["ids"]):
        raise ValueError("旧・新で共通する縦列12行が再現しない")
    for row in source["row_outcomes"]:
        if row["id"] in ids and any(stats["unknown"] != 1 for a in ARMS for stats in row[a].values()):
            raise ValueError("元の比較で縦列が未決定ではない")
    packs = {}
    for a in ARMS:
        packs[a] = {k: requests[a][3][k] for k in ("images", "image_sha256")}
        packs[a].update(ids=ids, prompt=trial.prompt(a, ids))
    if (packs["old"]["images"] != packs["new"]["images"]
            or packs["old"]["image_sha256"] != packs["new"]["image_sha256"]
            or packs["old"]["prompt"] != packs["new"]["prompt"].replace(base.EXTRA, "", 1)):
        raise ValueError("画像または転記指示の差分が異なる")
    fixed = {
        **before, "previous_script_sha256": before["script_sha256"],
        "script_sha256": base.sha(Path(__file__)), "fable_lock_sha256": SOURCE_LOCK,
        "fable_result_sha256": SOURCE_RESULT, "fable_original_sha256": fable_hashes,
        "old_third_packs": before["packs"], "packs": packs,
        "models": MODELS, "effort": "medium",
    }
    return targets, directory, sessions, fixed


def prepare():
    *_, fixed = original()
    fixed["fixed_at"] = base.utc_now()
    base.write_json(HERE / "lock.json", fixed)
    print("固定", base.sha(HERE / "lock.json"), "旧・新共通12行、各16画像", flush=True)


def pair_status(fable, opus):
    if fable is None and opus is None:
        return "both_unreadable"
    if fable is None or opus is None:
        return "one_unreadable"
    return "agree" if fable == opus else "different"


def run(exe, expected):
    lock_file = HERE / "lock.json"
    if base.sha(lock_file) != expected:
        raise ValueError("指定された固定SHAと異なる")
    rows, directory, past, fixed = original()
    if {k: v for k, v in base.load(lock_file).items() if k != "fixed_at"} != fixed:
        raise ValueError("固定後に入力が変化")
    OUT.mkdir(parents=True)
    readers = {}
    for who, model in MODELS.items():
        reader = prior.load_module(f"vertical_{who}", prior.sol_run.OPUS_RUN)
        reader.MODEL, reader.OUT = model, OUT / who
        reader.OUT.mkdir()
        readers[who] = reader
    with ThreadPoolExecutor(max_workers=4) as pool:
        jobs = {(a, who): pool.submit(reader.read_opus, exe, a, fixed["packs"][a], directory)
                for a in ARMS for who, reader in readers.items()}
        acquired = {k: job.result() for k, job in jobs.items()}
    if original()[-1] != fixed or base.sha(lock_file) != expected:
        raise ValueError("読みの前後で入力が変化")
    receipts = [rec for _, rec in acquired.values()]
    sessions = {r["session"] for r in receipts}
    if len(sessions) != 4 or sessions & past:
        raise ValueError("読取セッションが重複")
    base.metrics = rep.metrics
    all_ids = [r["id"] for r in rows]
    baseline = dict.fromkeys(all_ids)
    final, agreement = {}, {}
    for a in ARMS:
        fable, opus = (acquired[a, who][0] for who in MODELS)
        final[a] = {i: base.consensus([fable[i], opus[i]]) for i in all_ids}
        agreement[a] = {i: pair_status(fable[i], opus[i]) for i in all_ids}
    result = {
        "finished": base.utc_now(), "lock_sha256": expected, "receipts": receipts,
        "previous_all_unresolved": rep.metrics(rows, baseline),
        "old_vs_new": base.paired(rows, final["old"], final["new"]),
        "changes_from_previous": {a: base.paired(rows, baseline, final[a]) for a in ARMS},
        "agreement": {a: dict(Counter(agreement[a].values())) for a in ARMS},
        "row_outcomes": [
            {"id": r["id"], "case": r["case"],
             **{a: {"agreement": agreement[a][r["id"]], **rep.metrics([r], final[a])}
                for a in ARMS}} for r in rows
        ],
    }
    base.write_json(HERE / "result.json", result)
    print(json.dumps({k: result[k] for k in ("old_vs_new", "agreement")}, ensure_ascii=False), flush=True)


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
