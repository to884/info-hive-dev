"""確定済みの監査の不一致と参照不足を調べ、本文を含まない分類を残す。"""

from collections import Counter, defaultdict
import unicodedata

from cards import HERE, OUT, load, score, sha
from resolve import MARK, RECEIVED, image_agreement
from readers import encoded, receive, save_once
from runner import START


def diagnose_difference(expected, observed):
    difference = Counter(expected) - Counter(observed)
    addition = Counter(observed) - Counter(expected)
    if not difference and not addition:
        return "reading-order"
    if not difference or not addition:
        inspected = difference if difference else addition
        punctuation = all(unicodedata.category(c)[0] in "PS" for c in inspected)
        return ("omitted" if difference else "added") + ("-punctuation" if punctuation else "-text")
    return "different-characters"


def summarize_unknown(a, b):
    if a is None or b is None:
        return "technical-incomplete"
    if a["status"] == "unreadable" or b["status"] == "unreadable":
        return "both-unreadable" if a["status"] == b["status"] else "one-unreadable"
    normalized = [score.audit.normalize(r["text"]) for r in (a, b)]
    if normalized[0] == normalized[1]:
        return "equal-but-insufficient"
    left, right = normalized
    if MARK.sub(lambda m: m.group(1), left) == MARK.sub(lambda m: m.group(1), right):
        return "point-coordinates"
    if MARK.search(left) or MARK.search(right):
        return "point-or-body-disagreement"
    return diagnose_difference(left, right)


def main():
    result_path = HERE / "result.json"
    destination = HERE / "diagnosis.json"
    result = load(result_path)
    if result["all_quality_checks_pass"]:
        print("二つの監査は通過済み", flush=True)
        return
    original = OUT / "reference-evidence.json"
    if result["detailed_reference_sha256"] != sha(original) or result["receipts_sha256"] != sha(RECEIVED):
        raise ValueError("確定済みの監査と証跡が違う")
    evidence = load(original)
    cases, unused_summary = image_agreement()
    packs = load(OUT / "packages.json")
    runtime = load(START)["runtime"]
    raw, classified = {}, defaultdict(Counter)
    for pack, job in packs["packs"].items():
        all_votes = []
        for family, model in packs["models"].items():
            verdict = receive(OUT / "reads" / pack / family, family, model, job["request"],
                              OUT / "cards" / pack, runtime[family])
            all_votes.append(verdict.get("answers", {}))
        for i, v in job["mapping"].items():
            raw[v["entry"]] = tuple(w.get(i) for w in all_votes)
    details = []
    for index, case in cases.items():
        row = case["row"]
        address = row["key"] + "/" + str(row["line_index"])
        item = evidence[address]
        final = item["answer"]
        for domain, expected in row["targets"].items():
            if not expected["known"]:
                continue
            scope = domain + "/" + row["side"]
            if final["status"] == "unreadable":
                outcome = "insufficient"
                method = item["evidence"]
                change = summarize_unknown(*raw[index]) if method == "plain-unresolved" else method
            else:
                actual, target = (score.audit.normalize(x["text"]) for x in (final, expected))
                if actual == target:
                    continue
                outcome, change = "mismatch", diagnose_difference(target, actual)
            classified[scope][outcome + ":" + change] += 1
            details.append({"domain": domain, "side": row["side"], "key": row["key"], "line_index": row["line_index"],
                            "axis": row["allocation_axis"], "width": row["box"][2], "height": row["box"][3],
                            "outcome": outcome, "diagnosis": change, "earlier_audit": row["previously_audited"]})
    save_once(destination, encoded({"scope": "post-result-diagnosis-no-label-or-ballot-change",
                                    "audit_sha256": sha(result_path), "cases": details, "counts": classified}))
    print(dict(classified), flush=True)


if __name__ == "__main__":
    main()
