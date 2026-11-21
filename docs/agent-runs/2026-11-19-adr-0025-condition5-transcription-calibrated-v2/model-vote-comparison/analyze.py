"""保存済みの三票を、同一モデル可と異なるモデル必須で再集計する。"""

from collections import Counter
import importlib.util
from itertools import combinations
import json
from pathlib import Path

HERE = Path(__file__).resolve().parent
BRACKET_SHA = "e06be89a3384095433b886efc608a4b276f436c025d0613c070b8671d4130f84"
BRACKET_LOCK_SHA = "f994af109ea09c180e8b3025e5331c61bcd1f7c6ae010ebbcb6bec13d6f0dcb2"
VERTICAL_SHA = "19145126b757f71dbc84f0673b827898c05954eef05b28dd3105f153f900b375"
VERTICAL_LOCK_SHA = "4c2e9c1196a4fee7e02ba9fb155b69cf7898106e41397c4912990f758347a1e4"
READERS = ("sol", "astra", "fable", "opus")
ARMS = ("old", "new")


def load_runner(name, branch):
    path = HERE.parent / branch / "run.py"
    spec = importlib.util.spec_from_file_location(name, path)
    runner = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(runner)
    return runner


def record(runner, result_sha, lock_sha, expected):
    result_file, lock_file = runner.HERE / "result.json", runner.HERE / "lock.json"
    if runner.base.sha(result_file) != result_sha or runner.base.sha(lock_file) != lock_sha:
        raise ValueError("保存済みの固定記録または結果が違う")
    result, lock = runner.base.load(result_file), runner.base.load(lock_file)
    if result["lock_sha256"] != lock_sha or {k: v for k, v in lock.items() if k != "fixed_at"} != expected:
        raise ValueError("結果と原票から再現した固定記録がつながらない")
    return result


def claude_votes(reader, folder, receipts, requests):
    answers_by_arm = {}
    for receipt in receipts:
        arm = receipt["arm"]
        pack = requests[arm]
        raw = folder / f"{arm}-response.jsonl"
        if (arm in answers_by_arm or receipt["model"] != reader.MODEL
                or reader.base.sha(raw) != receipt["response_sha256"]
                or any(receipt[k] != pack[k] for k in ("images", "image_sha256"))
                or reader.digest(pack["prompt"].encode("utf-8")) != receipt["prompt_sha256"]):
            raise ValueError("保存済みの第三票と固定入力が一致しない")
        answers, response = reader.parse(raw.read_text(encoding="utf-8"), pack["ids"])
        if response["session_id"] != receipt["session"]:
            raise ValueError("保存済みの第三票のセッションが違う")
        answers_by_arm[arm] = answers
    if set(answers_by_arm) != set(ARMS):
        raise ValueError("旧・新の保存済み第三票がそろわない")
    return answers_by_arm


def recover_brackets():
    runner = load_runner("bracket_fable", "fable-third")
    rows, _, first, requests, thirds, _, _, fixed = runner.original()
    prior = record(runner, BRACKET_SHA, BRACKET_LOCK_SHA, fixed)
    thirds["fable"] = claude_votes(runner.reader, runner.OUT, prior["receipts"],
                                  {a: requests[a][3] for a in ARMS})
    selected = [r for r in rows if r["case"] in ("2a", "2b")]
    initial = {a: {"sol": first[a][1], "astra": first[a][2]} for a in ARMS}
    if len(selected) != 8:
        raise ValueError("括弧8行が再現しない")
    return selected, initial, thirds, prior, runner.base.normalize


def recover_vertical():
    runner = load_runner("vertical_opus", "vertical-opus-third")
    rows, _, _, first, _, _, fixed = runner.original()
    prior = record(runner, VERTICAL_SHA, VERTICAL_LOCK_SHA, fixed)
    fable = runner.fable
    astra = fable.astra
    sol_result = runner.base.load(astra.SOURCE.parent / "result.json")
    astra_result = runner.base.load(fable.SOURCE.parent / "result.json")
    fable_result = runner.base.load(runner.SOURCE.parent / "result.json")
    opus_reader = runner.vertical.prior.load_module("saved_vertical_opus", runner.vertical.prior.sol_run.OPUS_RUN)
    opus_reader.MODEL = runner.MODEL
    thirds = {
        "sol": astra.third_votes(astra.SOL_OUT, astra.SOL_MODEL, sol_result, fixed),
        "astra": astra.third_votes(astra.OUT, astra.MODEL, astra_result, fixed),
        "fable": claude_votes(runner.vertical.prior.reader, fable.OUT, fable_result["receipts"], fixed["packs"]),
        "opus": claude_votes(opus_reader, runner.OUT, prior["receipts"], fixed["packs"]),
    }
    initial = {a: {who: first[a, who] for who in ("fable", "opus")} for a in ARMS}
    if len(rows) != 12:
        raise ValueError("縦列12行が再現しない")
    return rows, initial, thirds, prior, runner.base.normalize


def decision(votes, distinct):
    pairs = [(model_a, model_b, value_a)
             for (model_a, value_a), (model_b, value_b) in combinations(votes, 2)
             if value_a is not None and value_a == value_b and (not distinct or model_a != model_b)]
    if len({text for _, _, text in pairs}) > 1:
        raise ValueError("異なる転記が同時に確定")
    return (pairs[0][2] if pairs else None), [[a, b] for a, b, _ in pairs]


def status(gold, value):
    return "unresolved" if value is None else "correct" if value == gold else "wrong"


def analyze(rows, initial, thirds, prior, normalize):
    recorded = {r["id"]: r for r in prior["row_outcomes"]}
    output = {}
    for a in ARMS:
        output[a] = {}
        for who in READERS:
            decisions = []
            for row in rows:
                i, gold = row["id"], normalize(row["gold"])
                votes = [(model, group[i]) for model, group in initial[a].items()]
                if i in thirds[who][a]:
                    votes.append((who, thirds[who][a][i]))
                allowed, all_pairs = decision(votes, False)
                distinct, distinct_pairs = decision(votes, True)
                counts = recorded[i][a][who]
                if (allowed == gold, allowed is not None and allowed != gold, allowed is None) != (
                    bool(counts["exact"]), bool(counts["wrong"]), bool(counts["unknown"])
                ):
                    raise ValueError(f"元の通常集計が再現しない: {a}/{who}/{i}")
                if distinct is not None and (distinct != allowed or not distinct_pairs):
                    raise ValueError("異モデル必須の結果が従来規則と矛盾")
                decisions.append({"id": i, "same_model_allowed": status(gold, allowed),
                                  "distinct_models_required": status(gold, distinct),
                                  "agreeing_models": all_pairs,
                                  "distinct_agreeing_models": distinct_pairs})
            counts = {}
            for rule in ("same_model_allowed", "distinct_models_required"):
                tally = Counter(row[rule] for row in decisions)
                counts[rule] = {k: tally[k] for k in ("correct", "wrong", "unresolved")}
            output[a][who] = {"counts": counts, "rows": decisions}
    return output


def main():
    result = {
        "source_result_sha256": {"bracket": BRACKET_SHA, "vertical": VERTICAL_SHA},
        "bracket": analyze(*recover_brackets()),
        "vertical": analyze(*recover_vertical()),
    }
    text = json.dumps(result, ensure_ascii=False, indent=2) + "\n"
    (HERE / "result.json").write_text(text, encoding="utf-8", newline="\n")
    for group in ("bracket", "vertical"):
        for arm, strategies in result[group].items():
            for name, comparison in strategies.items():
                print(group, arm, name, comparison["counts"])


if __name__ == "__main__":
    main()
