"""縦列の未決定行を新規Opusで第三読し、Sol・Astra・Fableと比較する。"""

import argparse
from collections import Counter
from concurrent.futures import ThreadPoolExecutor
import importlib.util
import json
from pathlib import Path

HERE = Path(__file__).resolve().parent
SOURCE = HERE.parent / "vertical-fable-third/run.py"
FABLE_LOCK_SHA = "28fbb26701beed0d13bcb7fdaffa77dfa019bcab682f446b757486001295ed56"
FABLE_RESULT_SHA = "3bf2b2d3edd8575aa5e5290a626c3c35b04183882b41aac62e32313aca8d0293"
spec = importlib.util.spec_from_file_location("previous_fable", SOURCE)
fable = importlib.util.module_from_spec(spec)
spec.loader.exec_module(fable)
base, trial, rep = fable.base, fable.trial, fable.rep
vertical = fable.vertical
ARMS = fable.ARMS
MODEL = vertical.MODELS["opus"]
OUT = trial.ROOT / "vertical-opus-third"


def original():
    rows, directory, sessions, votes, previous, final, fixed = fable.original()
    lock_file, result_file = SOURCE.parent / "lock.json", SOURCE.parent / "result.json"
    if base.sha(lock_file) != FABLE_LOCK_SHA or base.sha(result_file) != FABLE_RESULT_SHA:
        raise ValueError("Fableの固定記録または結果が変化")
    if {k: v for k, v in base.load(lock_file).items() if k != "fixed_at"} != fixed:
        raise ValueError("Fableの固定元が異なる")
    result = base.load(result_file)
    if result["lock_sha256"] != FABLE_LOCK_SHA or result["two_reads"] != previous["old_vs_new"]:
        raise ValueError("Fableの結果と先行二票がつながらない")
    reader = vertical.prior.reader
    fable_third, hashes, recent = {}, {}, set()
    for receipt in result["receipts"]:
        a = receipt["arm"]
        p = fable.OUT / f"{a}-response.jsonl"
        hashes[p.name] = base.sha(p)
        pack = fixed["packs"][a]
        if (a in fable_third or receipt["model"] != fable.MODEL
                or hashes[p.name] != receipt["response_sha256"]
                or any(receipt[k] != pack[k] for k in ("images", "image_sha256"))
                or reader.digest(pack["prompt"].encode("utf-8")) != receipt["prompt_sha256"]):
            raise ValueError("Fableの第三票と固定入力が一致しない")
        answers, response = reader.parse(p.read_text(encoding="utf-8"), pack["ids"])
        session = response["session_id"]
        if session != receipt["session"] or session in sessions | recent:
            raise ValueError("Fableの第三読セッションが違うか重複")
        recent.add(session)
        fable_third[a] = answers
    if set(fable_third) != set(ARMS):
        raise ValueError("Fableの旧・新の第三票がそろわない")
    final["fable"] = {a: fable.astra.with_third(rows, votes, fable_third, a) for a in ARMS}
    for who, panel in final.items():
        if base.paired(rows, panel["old"], panel["new"]) != result["old_vs_new"][who]:
            raise ValueError(f"{who}の確定結果を原票から再現できない")
    errors = [r["id"] for r in rows if rep.metrics([r], final["fable"]["new"])["wrong"]]
    if len(errors) != 4 or any(i not in fixed["packs"]["new"]["ids"] for i in errors):
        raise ValueError("Fableの誤り4行が再現しない")
    fixed.update(model=MODEL, previous_script_sha256=fixed["script_sha256"],
                 script_sha256=base.sha(Path(__file__)), fable_lock_sha256=FABLE_LOCK_SHA,
                 fable_result_sha256=FABLE_RESULT_SHA, fable_raw_sha256=hashes,
                 prior_fable_wrong_ids=errors)
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
    rows, directory, past, votes, previous, final, fixed = original()
    if {k: v for k, v in base.load(lock_file).items() if k != "fixed_at"} != fixed:
        raise ValueError("固定後に入力が変化")
    reader = vertical.prior.load_module("opus_vertical_third", vertical.prior.sol_run.OPUS_RUN)
    reader.MODEL, reader.OUT = MODEL, OUT
    OUT.mkdir(parents=True)
    with ThreadPoolExecutor(max_workers=2) as pool:
        jobs = {a: pool.submit(reader.read_opus, exe, a, fixed["packs"][a], directory) for a in ARMS}
        received = {a: jobs[a].result() for a in ARMS}
    if original()[-1] != fixed or base.sha(lock_file) != expected:
        raise ValueError("読みの前後で入力が変化")
    receipts = [received[a][1] for a in ARMS]
    sessions = {r["session"] for r in receipts}
    if len(sessions) != 2 or sessions & past:
        raise ValueError("読取セッションが重複")
    third = {a: received[a][0] for a in ARMS}
    final["opus"] = {a: fable.astra.with_third(rows, votes, third, a) for a in ARMS}
    paired = {who: base.paired(rows, panel["old"], panel["new"]) for who, panel in final.items()}
    statuses = {
        a: {i: ("unreadable" if v is None
                else "matches_first_fable" if v == votes[a, "fable"][i]
                else "matches_first_opus" if v == votes[a, "opus"][i]
                else "matches_neither") for i, v in third[a].items()} for a in ARMS
    }
    row_outcomes = [
        {"id": r["id"], "case": r["case"],
         **{a: {who: rep.metrics([r], panel[a]) for who, panel in final.items()} for a in ARMS}}
        for r in rows
    ]
    tracked = [{"id": row["id"], "third_vote": statuses["new"][row["id"]], **row["new"]}
               for row in row_outcomes if row["id"] in fixed["prior_fable_wrong_ids"]]
    output = {
        "finished": base.utc_now(), "lock_sha256": expected, "receipts": receipts,
        "two_reads": previous["old_vs_new"], "old_vs_new": paired,
        "changes_from_prior": {
            who: {a: base.paired(rows, final[who][a], final["opus"][a]) for a in ARMS}
            for who in ("sol", "astra", "fable")
        },
        "third_vote": {a: dict(Counter(v.values())) for a, v in statuses.items()},
        "prior_fable_wrong_rows": tracked, "row_outcomes": row_outcomes,
    }
    base.write_json(HERE / "result.json", output)
    print(json.dumps({"summary": {who: p["all"] for who, p in paired.items()},
                      "third_vote": output["third_vote"], "tracked": tracked}, ensure_ascii=False), flush=True)


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
