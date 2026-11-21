"""Solに括弧8行だけを再読させ、保存済みの同範囲のFable票と比べる。"""

import argparse
from collections import Counter
from concurrent.futures import ThreadPoolExecutor
import importlib.util
import json
from pathlib import Path
from shutil import copyfile

HERE = Path(__file__).resolve().parent
SOURCE = HERE.parent / "new-bracket-fable-third/run.py"
SOURCE_LOCK_SHA = "a1ef401af929dd14bd2fac814d5bf005ccdd560353b3c429fe9773b7500ee24c"
SOURCE_RESULT_SHA = "532a3d3b92d84dfdcdcd41eeadaa8cfb967763b2cae54d4187379f304c2ad8b5"
spec = importlib.util.spec_from_file_location("saved_fable_eight", SOURCE)
prior = importlib.util.module_from_spec(spec)
spec.loader.exec_module(prior)
base, trial = prior.base, prior.trial
OUT = trial.ROOT / "eight-bracket-sol-reread"
MODEL = "gpt-6.2-sol"
ARMS = ("old", "new")
LABELS = ("correct", "wrong", "unresolved")


def original():
    rows, directory, first, old, reference, past, fixed = prior.original()
    src_lock, src_result = SOURCE.parent / "lock.json", SOURCE.parent / "result.json"
    if base.sha(src_lock) != SOURCE_LOCK_SHA or base.sha(src_result) != SOURCE_RESULT_SHA:
        raise ValueError("Fableの8行限定の固定または結果が変化")
    if {k: v for k, v in base.load(src_lock).items() if k != "fixed_at"} != fixed:
        raise ValueError("Fableの8行限定の入力を再現できない")
    result = base.load(src_result)
    reader = prior.fable.reader
    receipt, path = result["receipt"], prior.OUT / "new-response.jsonl"
    packs = {a: fixed[f"{a}_pack"] for a in ARMS}
    if (result["lock_sha256"] != SOURCE_LOCK_SHA or receipt["model"] != prior.MODEL
            or base.sha(path) != receipt["response_sha256"]
            or any(receipt[k] != packs["new"][k] for k in ("images", "image_sha256"))
            or reader.digest(packs["new"]["prompt"].encode("utf-8")) != receipt["prompt_sha256"]):
        raise ValueError("新指示のFable原票が固定入力と一致しない")
    new, response = reader.parse(path.read_text(encoding="utf-8"), packs["new"]["ids"])
    session = response["session_id"]
    if session != receipt["session"] or session in past:
        raise ValueError("Fableのセッションが違う")
    saved = {r["id"]: r for r in result["row_outcomes"]}
    for r in rows:
        i, gold = r["id"], base.normalize(r["gold"])
        if (reference[i] != saved[i]["old"]
                or prior.old.decide(first, new[i], "new", i, gold) != saved[i]["new"]):
            raise ValueError("先行するFableの結果が原票から再現しない")
    lock = {
        "script_sha256": base.sha(Path(__file__)), "source_script_sha256": fixed["script_sha256"],
        "source_lock_sha256": SOURCE_LOCK_SHA, "source_result_sha256": SOURCE_RESULT_SHA,
        "comparison_lock_sha256": fixed["comparison_lock_sha256"],
        "fable_raw_sha256": {"old": fixed["old_raw_sha256"], "new": base.sha(path)},
        "model": MODEL, "effort": "medium", "packs": packs,
    }
    return rows, directory, first, {"old": old, "new": new}, past | {session}, lock


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
    rows, directory, first, fable, past, fixed = original()
    if {k: v for k, v in base.load(lock_file).items() if k != "fixed_at"} != fixed:
        raise ValueError("固定後に入力が変化")
    study_lock, _, _ = trial.check("comparison", fixed["comparison_lock_sha256"])
    images = fixed["packs"]["old"]["images"]
    sheets = dict.fromkeys(str(r["sheet"]) for r in rows)
    if images != [n for sheet in sheets for n in study_lock["image_order_by_sheet"][sheet]]:
        raise ValueError("8行から展開した配布画像の順序が違う")
    OUT.mkdir(parents=True)
    for name in images:
        copyfile(directory / name, OUT / name)
        if base.sha(OUT / name) != study_lock["image_sha256"][name]:
            raise ValueError("配布用画像が固定画像と異なる")
    base.PRIVATE, base.prompt_for = OUT, trial.prompt
    with ThreadPoolExecutor(max_workers=2) as pool:
        jobs = {a: pool.submit(base.read_images, exe, study_lock, rows, a, 3, MODEL) for a in ARMS}
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
            raise ValueError("Solに渡した画像、指示、対象が違う")
    outcomes = []
    for r in rows:
        i, gold = r["id"], base.normalize(r["gold"])
        entry = {"id": i}
        for a in ARMS:
            initial, sol, claude = first[a][1][i], received[a][0][i], fable[a][i]
            entry[a] = {
                "initial_sol": prior.old.saved.status(gold, initial),
                "fresh_sol": prior.old.saved.status(gold, sol),
                "saved_fable": prior.old.saved.status(gold, claude),
                "initial_sol_fable": prior.old.saved.status(gold, base.consensus([initial, claude])),
                "fresh_sol_fable": prior.old.saved.status(gold, base.consensus([sol, claude])),
            }
        outcomes.append(entry)
    summary = {}
    for a in ARMS:
        summary[a] = {}
        for field in outcomes[0][a]:
            tally = Counter(row[a][field] for row in outcomes)
            summary[a][field] = {k: tally[k] for k in LABELS}
    result = {"finished": base.utc_now(), "lock_sha256": expected, "receipts": receipts,
              "summary": summary, "row_outcomes": outcomes}
    base.write_json(HERE / "result.json", result)
    print(json.dumps(summary, ensure_ascii=False), flush=True)


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
