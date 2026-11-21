"""新指示を括弧8行に限定し、同じ範囲の旧指示のFable第三読と比べる。"""

import argparse
from collections import Counter
import importlib.util
import json
from pathlib import Path

HERE = Path(__file__).resolve().parent
SOURCE = HERE.parent / "old-bracket-fable-third/run.py"
OLD_LOCK_SHA = "7efc2db37f7ab3d52bd2c1031c5bbec867807f6ae9cca4c6da0a92b28a1de356"
OLD_RESULT_SHA = "69a5428713ffb008a62b40b90d9d2ec449f09ab91018353105a89123860c1b29"
spec = importlib.util.spec_from_file_location("eight_old", SOURCE)
old = importlib.util.module_from_spec(spec)
spec.loader.exec_module(old)
base, trial, fable, MODEL = old.base, old.trial, old.fable, old.MODEL
OUT = trial.ROOT / "new-bracket-fable-third"


def original():
    rows, directory, first, _, _, past, prior = old.original()
    old_lock, old_result = SOURCE.parent / "lock.json", SOURCE.parent / "result.json"
    if base.sha(old_lock) != OLD_LOCK_SHA or base.sha(old_result) != OLD_RESULT_SHA:
        raise ValueError("旧指示の8行限定の固定または結果が異なる")
    if {k: v for k, v in base.load(old_lock).items() if k != "fixed_at"} != prior:
        raise ValueError("旧指示の8行限定の入力が再現しない")
    record = base.load(old_result)
    pack = prior["old_pack"]
    receipt, raw = record["receipt"], old.OUT / "old-response.jsonl"
    reader = fable.reader
    if (record["lock_sha256"] != OLD_LOCK_SHA or receipt["model"] != MODEL
            or reader.base.sha(raw) != receipt["response_sha256"]
            or any(receipt[k] != pack[k] for k in ("images", "image_sha256"))
            or reader.digest(pack["prompt"].encode("utf-8")) != receipt["prompt_sha256"]):
        raise ValueError("旧指示のFable原票と固定入力が合わない")
    old_votes, response = reader.parse(raw.read_text(encoding="utf-8"), pack["ids"])
    if response["session_id"] != receipt["session"] or response["session_id"] in past:
        raise ValueError("旧指示のFableセッションが異なる")
    if len(rows) != 8 or [r["id"] for r in rows] != pack["ids"]:
        raise ValueError("比較する8行が異なる")
    new_pack = {**pack, "prompt": trial.prompt("new", pack["ids"])}
    if new_pack["prompt"].count(base.EXTRA) != 1 or new_pack["prompt"].replace(base.EXTRA, "", 1) != pack["prompt"]:
        raise ValueError("旧・新の指示が一文差ではない")
    reference = {row["id"]: row["old"] for row in record["row_outcomes"]}
    if any(old.decide(first, old_votes[r["id"]], "old", r["id"], base.normalize(r["gold"]))
           != reference[r["id"]] for r in rows):
        raise ValueError("旧指示の8行限定の結果を原票から再現できない")
    fixed = {
        **prior, "previous_script_sha256": prior["script_sha256"],
        "script_sha256": base.sha(Path(__file__)), "old_lock_sha256": OLD_LOCK_SHA,
        "old_result_sha256": OLD_RESULT_SHA, "old_raw_sha256": base.sha(raw),
        "new_pack": new_pack,
    }
    return rows, directory, first, old_votes, reference, past | {receipt["session"]}, fixed


def prepare():
    *_, fixed = original()
    fixed["fixed_at"] = base.utc_now()
    base.write_json(HERE / "lock.json", fixed)
    print("固定", base.sha(HERE / "lock.json"), "旧・新の括弧各8行、画像16枚", flush=True)


def run(exe, expected):
    path = HERE / "lock.json"
    if base.sha(path) != expected:
        raise ValueError("指定された固定SHAと異なる")
    rows, directory, first, old_votes, reference, past, fixed = original()
    if {k: v for k, v in base.load(path).items() if k != "fixed_at"} != fixed:
        raise ValueError("固定後に入力が変化")
    reader = fable.load_module("new_bracket_reader", fable.sol_run.OPUS_RUN)
    reader.MODEL, reader.OUT = MODEL, OUT
    OUT.mkdir(parents=True)
    new_votes, receipt = reader.read_opus(exe, "new", fixed["new_pack"], directory)
    if original()[-1] != fixed or base.sha(path) != expected or receipt["session"] in past:
        raise ValueError("読みの前後で入力が変化したかセッションが重複")
    decisions = []
    for row in rows:
        i, gold = row["id"], base.normalize(row["gold"])
        decisions.append({"id": i, "old": reference[i], "new": old.decide(first, new_votes[i], "new", i, gold),
                          "fable_text_agrees_between_arms": old_votes[i] is not None and old_votes[i] == new_votes[i]})
    summary = {}
    for arm in ("old", "new"):
        counts = {}
        for field in ("fable_vote", "distinct_families_required"):
            tally = Counter(row[arm][field] for row in decisions)
            counts[field] = {k: tally[k] for k in old.LABELS}
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
