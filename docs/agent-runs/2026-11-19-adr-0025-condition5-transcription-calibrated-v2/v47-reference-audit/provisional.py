"""利用枠の解除待ちに、保全済みの両票から開発用の原因を数える。"""

import argparse
from collections import Counter, defaultdict
from pathlib import Path

import official

audit = official.audit
core, previous = audit.core, audit.previous
HERE = Path(__file__).resolve().parent


def main():
    cli = argparse.ArgumentParser(description=__doc__)
    cli.add_argument("--sha256", required=True)
    args = cli.parse_args()
    output = HERE / "provisional-before-last-vote.json"
    if output.exists() or (HERE / "result.json").exists():
        raise FileExistsError("暫定の集計を確定したか、正式の集計が既にある")
    core.verify_methods()
    audit.verify_delivery(args.sha256)
    binding = core.OUT / "delivery"
    shipment = core.transport.check(binding, args.sha256)
    evidence, votes = core.transport.collect(shipment, core.old_sessions())
    selection = core.OUT / "selection.json"
    rows = core.load(selection)["selected"]
    ref = core.ref
    classify = previous.module("image_discrepancy_causes", HERE.parent / "v10-reference-audit/diagnose.py")
    guard = previous.module("confirmed_round_shapes", HERE.parent / "v23-round-pixel-pilot/run.py")
    issues, tally, pair_tally = [], defaultdict(Counter), Counter()

    for pack, job in shipment.document["packs"].items():
        (ident, binding), = job["mapping"].items()
        val = [role.get(ident) for role in votes[pack].values()]
        row = rows[binding["entry"]]
        if any(v is None for v in val):
            status, reason = "not-paired", "waiting-for-vote"
        else:
            decoded = [ref.decoded(v, binding["partitions"]) for v in val]
            answer, positions = ref.aligned(*decoded, row["box"][2])
            if guard.unverified_round(answer, row, binding["image_reference"]["sha"], positions):
                status, reason = "image-unresolved", "unverified-round"
            elif answer["status"] == "unreadable":
                status, reason = "image-unresolved", classify.summarize_unknown(*decoded)
            elif ref.MARK.search(answer["text"]):
                status, reason = "source-not-attempted", "physical-position-agreed"
            else:
                status, reason = "image-resolved", "direct-image"
        pair_tally[status] += 1
        for group, known in row["targets"].items():
            text = known["text"]
            mode, explanation = status, reason
            scope = group if known["known"] else f"{group}-unknown"
            if status == "image-resolved" and known["known"]:
                expected = ref.NORMALIZE(text)
                if expected == answer["text"]:
                    mode = "image-same"
                else:
                    mode = "image-different"
                    explanation = classify.diagnose_difference(expected, answer["text"])
            tally[scope][mode] += 1
            if known["known"] and mode not in ("image-same", "not-paired"):
                issues.append({"page": row["key"], "line_index": row["line_index"], "axis": row["allocation_axis"],
                               "stratum": scope, "category": mode, "reason": explanation})

    if evidence["counts"]["gpt"] != {"received": 376} or evidence["counts"]["claude"] != {
            "received": 375, "quota-rejection": 1}:
        raise ValueError("確認対象が利用枠で停止した375行と違う")
    core.save_once(output, core.encoded({"scope": "development-only-provisional-image-votes",
                                       "packages_sha256": args.sha256, "selection_sha256": core.sha(selection),
                                       "collection_sha256": previous.readers.sha(core.encoded(evidence)),
                                       "pairs": pair_tally, "by_domain": tally, "causes": issues}))
    print(dict(pair_tally), dict(tally), flush=True)


if __name__ == "__main__":
    main()
