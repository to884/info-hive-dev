"""保存票で異モデル必須から異系統必須への判定差を調べる。"""

from collections import Counter
import hashlib
import importlib.util
import json
from pathlib import Path

HERE = Path(__file__).resolve().parent
PREVIOUS = HERE.parent / "model-vote-comparison"
PREVIOUS_CODE_SHA = "4382bba5d175b34e47c3db4d5e783d322716682f58bf9e236129e4a703f1d0dc"
PREVIOUS_RESULT_SHA = "5c3eda9d291d0018a603210e88a3659945a2eab85fbad9a32056f0ddf24ac4e3"
FAMILY = {"sol": "GPT", "astra": "GPT", "fable": "Claude", "opus": "Claude"}
OUTCOMES = ("correct", "wrong", "unresolved")
RULES = ("distinct_models_required", "distinct_families_required")


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def analyze_group(prior, previous, rows, initial, thirds, normalize):
    groups = {}
    for arm in prior.ARMS:
        groups[arm] = {}
        for reader in prior.READERS:
            reference = previous[arm][reader]
            decisions = []
            for row, saved in zip(rows, reference["rows"], strict=True):
                i, gold = row["id"], normalize(row["gold"])
                if i != saved["id"]:
                    raise ValueError("前回の行IDと一致しない")
                votes = [(model, values[i]) for model, values in initial[arm].items()]
                if i in thirds[reader][arm]:
                    votes.append((reader, thirds[reader][arm][i]))
                model_vote, model_pairs = prior.decision(votes, True)
                family_vote, family_pairs = prior.decision([(FAMILY[m], v) for m, v in votes], True)
                crossing = [[a, b] for a, b in model_pairs if FAMILY[a] != FAMILY[b]]
                expected_pairs = [[FAMILY[a], FAMILY[b]] for a, b in crossing]
                model_status = prior.status(gold, model_vote)
                if model_status != saved[RULES[0]] or model_pairs != saved["distinct_agreeing_models"]:
                    raise ValueError("前回の異モデル判定を原票から再現できない")
                if expected_pairs != family_pairs or family_vote != (model_vote if crossing else None):
                    raise ValueError("原票の再集計と前回の一致ペアから求めた結果が違う")
                decisions.append({"id": i, RULES[0]: model_status, RULES[1]: prior.status(gold, family_vote),
                                  "model_pairs": model_pairs, "cross_family_model_pairs": crossing})
            counts = {}
            for rule in RULES:
                tally = Counter(row[rule] for row in decisions)
                counts[rule] = {k: tally[k] for k in OUTCOMES}
            if counts[RULES[0]] != reference["counts"][RULES[0]]:
                raise ValueError("前回の全行集計と一致しない")
            groups[arm][reader] = {"counts": counts, "rows": decisions}
    return groups


def main():
    code, previous_file = PREVIOUS / "analyze.py", PREVIOUS / "result.json"
    if sha(code) != PREVIOUS_CODE_SHA or sha(previous_file) != PREVIOUS_RESULT_SHA:
        raise ValueError("前回の集計資料が変化")
    spec = importlib.util.spec_from_file_location("model_agreement", code)
    prior = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(prior)
    previous = json.loads(previous_file.read_text(encoding="utf-8"))
    result = {"family": FAMILY, "previous_result_sha256": PREVIOUS_RESULT_SHA}
    for group, recovery in (("bracket", prior.recover_brackets), ("vertical", prior.recover_vertical)):
        rows, initial, thirds, _, normalize = recovery()
        result[group] = analyze_group(prior, previous[group], rows, initial, thirds, normalize)
        for arm, trials in result[group].items():
            for reader, record in trials.items():
                print(group, arm, reader, record["counts"])
    (HERE / "result.json").write_text(json.dumps(result, ensure_ascii=False, indent=2) + "\n",
                                     encoding="utf-8", newline="\n")


if __name__ == "__main__":
    main()
