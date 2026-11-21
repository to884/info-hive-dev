"""モデルの出典とセッションを確認し、集合で数えた判定を再集計と照合する。"""

from collections import Counter, defaultdict
from itertools import product
import json

import analyze


def verify_receipts():
    sol, astra = "gpt-6.2-sol", "gpt-6.2-astra"
    fable, opus = "claude-fable-5-2", "claude-opus-5-5"
    expected = {
        "comparison-result.json": Counter({(1, sol): 1, (2, astra): 1, (3, astra): 1}),
        "sol-third/result.json": Counter({(3, sol): 1}),
        "opus-third/result.json": Counter({(None, opus): 1}),
        "fable-third/result.json": Counter({(None, fable): 1}),
        "vertical-reread/result.json": Counter({(None, fable): 1, (None, opus): 1}),
        "vertical-sol-third/result.json": Counter({(3, sol): 1}),
        "vertical-astra-third/result.json": Counter({(3, astra): 1}),
        "vertical-fable-third/result.json": Counter({(None, fable): 1}),
        "vertical-opus-third/result.json": Counter({(None, opus): 1}),
    }
    sessions = set()
    for file, expected_per_arm in expected.items():
        result = json.loads((analyze.HERE.parent / file).read_text(encoding="utf-8"))
        by_arm = {a: Counter() for a in analyze.ARMS}
        for r in result["receipts"]:
            assert r["session"] not in sessions, file
            sessions.add(r["session"])
            by_arm[r["arm"]][r.get("read"), r["model"]] += 1
        assert all(counts == expected_per_arm for counts in by_arm.values()), file
    assert len(sessions) == 24


def grouped_decision(ballots):
    counts = Counter()
    models = defaultdict(set)
    for who, text in ballots:
        if text is not None:
            counts[text] += 1
            models[text].add(who)
    return (next((v for v, n in counts.items() if n >= 2), None),
            next((v for v, names in models.items() if len(names) >= 2), None))


def label(value, truth):
    if value is None:
        return "unresolved"
    return "correct" if value == truth else "wrong"


def verify_decisions():
    reported = json.loads((analyze.HERE / "result.json").read_text(encoding="utf-8"))
    for ballots in product(product(("a", "b", "c"), (None, "", "甲", "乙")), repeat=3):
        assert grouped_decision(ballots) == tuple(analyze.decision(ballots, r)[0] for r in (False, True))
    rules = ("same_model_allowed", "distinct_models_required")
    for group, read in (("bracket", analyze.recover_brackets), ("vertical", analyze.recover_vertical)):
        rows, initial, thirds, _, normalize = read()
        for arm in analyze.ARMS:
            for who in analyze.READERS:
                result = reported[group][arm][who]
                tallies = {rule: Counter() for rule in rules}
                for row, recorded in zip(rows, result["rows"], strict=True):
                    i = row["id"]
                    assert i == recorded["id"]
                    ballots = [(model, vote[i]) for model, vote in initial[arm].items()]
                    if i in thirds[who][arm]:
                        ballots.append((who, thirds[who][arm][i]))
                    for rule, value in zip(rules, grouped_decision(ballots), strict=True):
                        outcome = label(value, normalize(row["gold"]))
                        assert outcome == recorded[rule]
                        tallies[rule][outcome] += 1
                assert result["counts"] == {
                    rule: {key: counts[key] for key in ("correct", "wrong", "unresolved")}
                    for rule, counts in tallies.items()
                }


if __name__ == "__main__":
    verify_receipts()
    verify_decisions()
    print("24セッション・160行の指定条件・1,728通りの三票を照合")
