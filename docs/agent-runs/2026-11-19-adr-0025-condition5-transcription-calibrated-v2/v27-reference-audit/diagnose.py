"""確定済みの三値を原票から照合し、未決定の理由を行ごとに記録する。"""

from collections import Counter, defaultdict
from pathlib import Path
import sys

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parent / "v19-reference-audit"))
import run as previous

audit = previous.module("current_independent_audit", HERE / "run.py")
v10 = previous.module("prior_diagnosis", HERE.parent / "v10-reference-audit/diagnose.py")


def main():
    audit.verify_methods()
    final = HERE / "result.json"
    saved = audit.load(final)
    archive = audit.OUT / "reference-evidence.json"
    delivery = audit.OUT / "delivery"
    if (audit.sha(archive) != saved["reference_sha256"]
            or audit.sha(delivery / "received.json") != saved["receipts_sha256"]
            or audit.sha(audit.OUT / "source-commands.json") != saved["source_sha256"]):
        raise ValueError("確定した監査の出典・原票と異なる")
    ship = audit.transport.check(delivery, audit.sha(delivery / "packages.json"))
    receipt, answers = audit.transport.collect(ship, audit.old_sessions())
    if receipt != audit.load(delivery / "received.json"):
        raise ValueError("正式に受領した原票を再現できない")
    rows = audit.load(audit.OUT / "selection.json")["selected"]
    reference = audit.load(archive)
    issues, totals, bundles = [], defaultdict(Counter), defaultdict(Counter)
    for packet, item in ship.document["packs"].items():
        for role, chain in receipt["votes"][packet].items():
            bundles[role][chain[-1]["receipt"]["availability"] if chain else "unstarted"] += 1
        for ident, binding in item["mapping"].items():
            row = rows[binding["entry"]]
            key = row["key"], row["line_index"]
            verdict = reference[f"{key[0]}/{key[1]}"]
            text = verdict["answer"]["text"]
            readable = verdict["answer"]["status"] != "unreadable"
            actual = [audit.ref.decoded(v.get(ident, audit.ref.UNKNOWN), binding["partitions"])
                      for v in answers[packet].values()]
            for domain, label in row["targets"].items():
                if not label["known"]:
                    totals[domain]["unknown-reference" if readable else "unknown-insufficient"] += 1
                    continue
                expected = audit.ref.NORMALIZE(label["text"])
                if readable and text == expected:
                    totals[domain]["same"] += 1
                    continue
                if readable:
                    outcome, reason = "different", v10.diagnose_difference(expected, text)
                else:
                    outcome, reason = "insufficient", verdict["evidence"]
                    if reason == "plain-unresolved":
                        reason = v10.summarize_unknown(*actual)
                totals[domain][outcome] += 1
                issues.append({"page": key[0], "line_index": key[1], "domain": domain, "side": row["side"],
                               "axis": row["allocation_axis"], "outcome": outcome, "reason": reason})
    audit.save_once(HERE / "diagnosis.json", audit.encoded({
        "scope": "after-final-diagnosis", "result_sha256": audit.sha(final), "totals": totals,
        "receipts": bundles, "issues": issues,
    }))
    print(dict(totals), dict(bundles), flush=True)


if __name__ == "__main__":
    main()
