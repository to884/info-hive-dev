"""確定した独立監査の相違と参照不足を行別に調べる。"""

from collections import Counter

import run

v10 = run.module("v10_diagnosis", run.HERE.parent / "v10-reference-audit/diagnose.py")
load, sha, encoded, save_once = run.load, run.sha, run.encoded, run.save_once


def receipt_texts(delivery, manifest):
    start = load(delivery / "delivery-started.json")
    result = {}
    for pack, job in manifest["packs"].items():
        replies = []
        for role, model in manifest["models"].items():
            r = run.receive(delivery / "reads" / pack / role, role, model, job["request"],
                            delivery / "cards" / pack, start["runtime"][role])
            replies.append(r.get("answers", {}))
        for ident, info in job["mapping"].items():
            opinions = [r.get(ident) for r in replies]
            result[info["entry"]] = [run.reference.decoded(a, info["partitions"]) if a else None for a in opinions]
    return result


def main():
    final = run.HERE / "result.json"
    detailed = run.OUT / "reference-evidence.json"
    delivery = run.OUT / "delivery"
    result = load(final)
    if (result["reference_sha256"] != sha(detailed) or result["receipts_sha256"] != sha(delivery / "received.json")
            or result["source_sha256"] != sha(run.OUT / "source-commands.json")):
        raise ValueError("確定した監査の証跡と異なる")
    manifest = load(delivery / "packages.json")
    selected = load(run.OUT / "selection.json")
    evidence, opinions = load(detailed), receipt_texts(delivery, manifest)
    counts, issues = {}, []
    for i, row in enumerate(selected["selected"]):
        address = f"{row['key']}/{row['line_index']}"
        act = evidence[address]
        result_value = act["answer"]["text"]
        for area, label in row["targets"].items():
            if not label["known"]:
                continue
            if act["answer"]["status"] != "unreadable":
                target = run.reference.NORMALIZE(label["text"])
                if target == result_value:
                    continue
                outcome, reason = "mismatch", v10.diagnose_difference(target, result_value)
            else:
                outcome = "insufficient"
                reason = act["evidence"]
                if reason == "plain-unresolved":
                    reason = v10.summarize_unknown(*opinions[i])
            scope = f"{area}/{row['side']}"
            counts.setdefault(scope, Counter())[f"{outcome}:{reason}"] += 1
            x, y, w, h = row["box"]
            issues.append({"domain": area, "side": row["side"], "key": row["key"], "line_index": row["line_index"],
                           "axis": row["allocation_axis"], "width": w, "height": h, "outcome": outcome, "reason": reason})
    save_once(run.HERE / "diagnosis.json", encoded({"scope": "after-final-diagnosis", "audit_sha256": sha(final),
              "counts": counts, "cases": issues}))
    print(counts, flush=True)


if __name__ == "__main__":
    main()
