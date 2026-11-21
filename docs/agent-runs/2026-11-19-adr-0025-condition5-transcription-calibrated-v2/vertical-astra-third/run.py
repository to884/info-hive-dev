"""縦列の未決定行をAstraで第三読し、同じ二票を使ったSolと比較する。"""

import argparse
import importlib.util
import json
from pathlib import Path

HERE = Path(__file__).resolve().parent
SOURCE = HERE.parent / "vertical-sol-third/run.py"
SOL_LOCK_SHA = "cf244e0074e2710c9d554c7cfb5f67040aa79ca98d646b0437c476ffa99f7759"
SOL_RESULT_SHA = "a5fae8a5fc76d77c2f66a846f7428fcf372c245e06473faaede70954e28c7e28"
spec = importlib.util.spec_from_file_location("vertical_third", SOURCE)
runner = importlib.util.module_from_spec(spec)
spec.loader.exec_module(runner)
base, trial, rep = runner.base, runner.trial, runner.rep
ARMS, SOL_OUT, SOL_MODEL = runner.ARMS, runner.OUT, runner.MODEL
MODEL = "gpt-6.2-astra"
OUT = trial.ROOT / "vertical-astra-third"
original_vertical_votes = runner.original


def third_votes(folder, model, recorded, fixed):
    by_arm = {}
    for receipt in recorded["receipts"]:
        arm = receipt["arm"]
        prefix = f"{arm}-read3-{model}"
        path = folder / f"{prefix}-{receipt['attempt']}.jsonl"
        request = base.load(folder / f"{prefix}-request.json")
        pack = fixed["packs"][arm]
        if (arm in by_arm or receipt["model"] != model or base.sha(path) != receipt["response_sha256"]
                or any(request[k] != v for k, v in pack.items())
                or receipt["image_sha256"] != pack["image_sha256"]
                or runner.vertical.prior.reader.digest(pack["prompt"].encode("utf-8")) != receipt["prompt_sha256"]):
            raise ValueError("第三読の原票とモデル・固定入力が一致しない")
        session, _, answers = base.parse_response(path.read_text(encoding="utf-8"), pack["ids"])
        if session != receipt["session"]:
            raise ValueError("第三読のセッション記録が異なる")
        by_arm[arm] = answers
    if set(by_arm) != set(ARMS):
        raise ValueError("両群の第三票がそろわない")
    return by_arm


def with_third(rows, votes, third, arm):
    return {r["id"]: base.consensus([votes[arm, who][r["id"]] for who in runner.vertical.MODELS]
                                    + [third[arm].get(r["id"])]) for r in rows}


def original():
    rows, directory, sessions, previous, votes, before, fixed = original_vertical_votes()
    sol_lock, sol_result = SOURCE.parent / "lock.json", SOURCE.parent / "result.json"
    if base.sha(sol_lock) != SOL_LOCK_SHA or base.sha(sol_result) != SOL_RESULT_SHA:
        raise ValueError("Solの固定記録または結果が変化")
    if {k: v for k, v in base.load(sol_lock).items() if k != "fixed_at"} != {**fixed, "model": SOL_MODEL}:
        raise ValueError("SolとAstraの固定元が異なる")
    sol = base.load(sol_result)
    if sol["lock_sha256"] != SOL_LOCK_SHA or sol["two_reads"] != previous["old_vs_new"]:
        raise ValueError("Solの結果が二読とつながらない")
    base.metrics = rep.metrics
    sol_votes = third_votes(SOL_OUT, SOL_MODEL, sol, fixed)
    if base.paired(rows, *(with_third(rows, votes, sol_votes, a) for a in ARMS)) != sol["three_reads"]:
        raise ValueError("Solの集計を原票から再現できない")
    if base.paired(rows, before["old"], before["new"]) != previous["old_vs_new"]:
        raise ValueError("元の二読結果を原票から再現できない")
    study, _, _ = trial.check("comparison", fixed["comparison_lock_sha256"])
    for a in ARMS:
        pack = fixed["packs"][a]
        sheets = dict.fromkeys(str(r["sheet"]) for r in rows if r["id"] in pack["ids"])
        actual = [n for sheet in sheets for n in study["image_order_by_sheet"][sheet]]
        if actual != pack["images"]:
            raise ValueError("派生した画像順が固定パックと異なる")
    prior_sessions = {r["session"] for r in sol["receipts"]}
    if len(prior_sessions) != 2 or prior_sessions & sessions:
        raise ValueError("Solの新規セッションが重複")
    fixed.update(model=MODEL, previous_script_sha256=fixed["script_sha256"],
                 script_sha256=base.sha(Path(__file__)), sol_lock_sha256=SOL_LOCK_SHA,
                 sol_result_sha256=SOL_RESULT_SHA)
    return rows, directory, sessions | prior_sessions, previous, votes, before, fixed


def compare():
    rows, _, _, _, votes, _, fixed = original()
    sol = base.load(SOURCE.parent / "result.json")
    astra = base.load(HERE / "result.json")
    sol_votes = third_votes(SOL_OUT, SOL_MODEL, sol, fixed)
    astra_votes = third_votes(OUT, MODEL, astra, fixed)
    astra_final = {a: with_third(rows, votes, astra_votes, a) for a in ARMS}
    if base.paired(rows, astra_final["old"], astra_final["new"]) != astra["three_reads"]:
        raise ValueError("Astraの集計を原票から再現できない")
    outcome = {
        a: base.paired(rows, with_third(rows, votes, sol_votes, a), astra_final[a]) for a in ARMS
    }
    base.write_json(HERE / "comparison.json", {"sol_to_astra": outcome})
    print(json.dumps({"sol_to_astra": outcome}, ensure_ascii=False), flush=True)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("action", choices=("prepare", "run"))
    parser.add_argument("--codex", type=Path)
    parser.add_argument("--lock-sha256")
    args = parser.parse_args()
    runner.HERE, runner.OUT, runner.MODEL, runner.original = HERE, OUT, MODEL, original
    if args.action == "prepare":
        runner.prepare()
    else:
        runner.run(args.codex.resolve(), args.lock_sha256)
        compare()
