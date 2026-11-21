"""官報の画像二票が示した字形の訂正を候補に反映して固定予測で採点する。"""

import hashlib
from pathlib import Path

import numpy as np

import prepare

pilot = prepare.pilot
audit = pilot.audit
HERE = Path(__file__).resolve().parent
OUT = audit.LABELS.with_name(HERE.name)
CONFIRMATION = HERE.parent / "v31-kanpo-glyph-pilot"
LOCK = CONFIRMATION / "lock.json"
READ = CONFIRMATION / "result.json"
from verify_candidate_prediction import evaluate


def corrections(plan, read, public):
    expected = {identity for identity, k in pilot.SAMPLES.items() if k == "name"}
    addresses = {(r["page"], r["line_index"]): r for r in read["cases"].values()}
    if (set(addresses) != set(pilot.SAMPLES) or len(addresses) != len(read["cases"]) or not expected
            or read["scope"] != "development-only" or read["lock_sha256"] != audit.sha(LOCK)):
        raise ValueError("事前に固定した対象の画像二読を確認できない")
    by_id = {(r["key"], r["line_index"]): r for r in public}
    changes, control_issues = {}, {}
    for ident, row in addresses.items():
        old = by_id[ident]
        body = row["readings"]["pair"]
        before = audit.ref.NORMALIZE(old["effective"])
        if row["expected"] != before or row["arm"] != "new":
            raise ValueError("画像二読で使った枠か比較元の版が異なる")
        if ident not in expected:
            if row["pair_result"] != "same":
                control_issues[ident] = row["pair_result"]
            continue
        if body["status"] != "readable" or row["readings"]["coordinates"]:
            continue
        updated = body["text"]
        if updated == before:
            continue
        suffix_confirmed = (before[8:] == updated[8:]
                            or (ident == ("kanpo1828-p3-p0001", 208) and before[8:] == "有與亭" and updated[8:] == "有藇"))
        if (not old["image_population"] or old["raw_region"] is not None
                or not before.startswith(("野崎家別邸治暇堂", "野崎家別邸迨暇堂"))
                or not updated.startswith("野﨑家別邸迨暇堂") or not suffix_confirmed):
            raise ValueError("固定画素で確認した箇所以外に差がある")
        changes[ident] = before, updated
    first = {"scope": "development-only", "lock_sha256": audit.sha(LOCK),
             "rows": [{"page": key, "line_index": i, "before": b, "after": a}
                      for (key, i), (b, a) in sorted(changes.items())]}
    verified_path = HERE / "physical-proof.json"
    verified = audit.load(verified_path)
    if (verified.get("corrections") != first or not changes
            or any(audit.sha(Path(p)) != value for p, value in verified["fixed_pixel_artifacts"].items())):
        raise ValueError("二票一致に加えて固定画素で確認した訂正を結び付けられない")
    for name, job in plan["jobs"].items():
        if len(job["request"]["ids"]) != 1:
            raise ValueError("同じ枠の画像二読の結果でない")
    return changes, control_issues


def main():
    if OUT.exists() or (HERE / "candidate-score.json").exists():
        raise FileExistsError("固定した訂正候補は採点済み")
    previous_labels = audit.LABELS / "public.json"
    previous_scoring = audit.LABELS / "scoring.json"
    original = audit.load(audit.REPORT)
    if any(audit.sha(audit.LABELS / p) != h for p, h in original["artifacts"].items()):
        raise ValueError("既存の固定正解が変化した")
    plan, reads = audit.load(LOCK), audit.load(READ)
    if any(audit.sha(Path(p)) != h for p, h in plan["files"].items()):
        raise ValueError("画像二読で固定した条件が変化した")
    rows = audit.load(previous_labels)
    changed, controls = corrections(plan, reads, rows)
    scoring = audit.v14.old.score.unpack_scoring(audit.load(previous_scoring))
    report = []
    for r in rows:
        ident = r["key"], r["line_index"]
        if ident not in changed:
            continue
        before, text = changed[ident]
        error = hashlib.sha256(text.encode("utf-8")).hexdigest() != r["ocr_normalized_sha256"]
        old_error = r["ocr_error"]
        row, = (row for row in scoring[r["group"]]["lines"] if (row["key"], row["line_index"]) == ident)
        if row["rule"] != "exact" or old_error != row["error"]:
            raise ValueError("置き換える行の採点規則やラベルの来歴が異なる")
        row.update(error=error, label_source="image-only-kanpo-glyph-v26")
        r.update(effective=text, source="image-only-kanpo-glyph-v26", ocr_error=error,
                 development_proof={"stage": CONFIRMATION.name, "lock_sha256": audit.sha(LOCK),
                                    "readings_sha256": audit.sha(READ)})
        report.append({"page": ident[0], "line_index": ident[1], "before": before, "after": text,
                       "before_error": old_error, "after_error": error})
    with np.load(audit.v14.old.PREDICTIONS, allow_pickle=False) as data:
        res = evaluate(scoring, data["probabilities"])
    OUT.mkdir()
    audit.save_once(OUT / "public.json", audit.encoded(rows))
    audit.save_once(OUT / "scoring.json", audit.encoded(audit.v14.old.score.pack_scoring(scoring)))
    materials = (Path(__file__), audit.REPORT, previous_labels, previous_scoring, LOCK, READ, pilot.LOCK, pilot.RESULT,
                 HERE / "physical-proof.json", audit.v14.old.PREDICTIONS,
                 *(Path(p) for p in audit.load(HERE / "physical-proof.json")["fixed_pixel_artifacts"]))
    audit.save_once(HERE / "candidate-score.json", audit.encoded({
        "scope": "development-only", "changed": report, "evaluation": res,
        "development_control_issues": [{"page": p, "line_index": i, "status": status}
                                       for (p, i), status in sorted(controls.items())],
        "same_predictions_sha256": audit.sha(audit.v14.old.PREDICTIONS),
        "inputs": {str(p): audit.sha(p) for p in materials},
        "artifacts": {p.name: audit.sha(p) for p in OUT.iterdir()},
    }))
    print(len(report), "訂正、開発6組", res["all_pass"], "公開3組", res["all_gates"], flush=True)


if __name__ == "__main__":
    main()
