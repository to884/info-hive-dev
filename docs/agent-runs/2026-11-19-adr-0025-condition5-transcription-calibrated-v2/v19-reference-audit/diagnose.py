"""確定したv19監査を、領域と画像補充に分けて診断する。"""

import json

import run


def main():
    run.reference = run.as_reference()
    recorded = run.load(run.ENDED)
    old = run.module("saved_diagnosis", run.HERE.parent / "v15-reference-audit/diagnose.py")
    old.run = run
    old.main()
    capture, packets = run.load(run.reference.READ), run.load(run.reference.PACKS)
    accepted = {"gpt": set(), "claude": set()}
    for name, status in capture["votes"].items():
        for family, verdict in status.items():
            if verdict["availability"] == "received":
                accepted[family].add(name)

    def rows(names):
        return sum(len(packets["packs"][name]["request"]["ids"]) for name in names)

    print(json.dumps({"sol": rows(accepted["gpt"]), "opus": rows(accepted["claude"]),
                      "paired": rows(accepted["gpt"] & accepted["claude"])}, ensure_ascii=False), flush=True)
    for name, result in recorded["summary"].items():
        totals = {"match": 0, "mismatch": 0, "insufficient": 0, "unknown_known": 0, "unknown_unresolved": 0}
        for scope in result["sides"].values():
            for tag, count in scope["groups"].items():
                if tag == "unknown":
                    totals["unknown_known"] += count.get("reference_known", 0)
                    totals["unknown_unresolved"] += count.get("reference_unknown", 0)
                else:
                    totals["match"] += count.get("same", 0)
                    totals["mismatch"] += count.get("different", 0)
                    totals["insufficient"] += count.get("unresolved_reference", 0)
        print(name, result["status"], totals, flush=True)


if __name__ == "__main__":
    main()
