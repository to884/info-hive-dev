"""固定画素と二票から確認した官報の二字を別版の正解へ加える。"""

import hashlib
import importlib.util
from pathlib import Path
import sys

import numpy as np

HERE = Path(__file__).resolve().parent
BASE = HERE.parent / "v26-kanpo-name-candidate"
spec = importlib.util.spec_from_file_location("independent_kanpo_candidate", BASE / "score.py")
old = importlib.util.module_from_spec(spec)
sys.path.insert(0, str(BASE))
spec.loader.exec_module(old)
audit, evaluate = old.audit, old.evaluate
SOURCE = HERE.parent / "v36-glyph-detail-pilot"
OUT = old.OUT.with_name(HERE.name)
ACCEPT = {("kanpo1828-p3-p0001", 196), ("kanpo1828-p3-p0001", 206)}


def main():
    if OUT.exists() or (HERE / "result.json").exists():
        raise FileExistsError("この版は採点済み")
    prior = audit.load(BASE / "candidate-score.json")
    if (not prior["evaluation"]["all_pass"] or not prior["evaluation"]["all_gates"]
            or any(audit.sha(old.OUT / p) != h for p, h in prior["artifacts"].items())
            or any(audit.sha(Path(p)) != h for p, h in prior["inputs"].items())):
        raise ValueError("前の開発正解の来歴が異なる")
    manifest = SOURCE / "lock.json"
    plan = audit.load(manifest)
    result = audit.load(SOURCE / "result.json")
    if (result["lock_sha256"] != audit.sha(manifest) or result["scope"] != "development-only"
            or any(audit.sha(Path(p)) != h for p, h in plan["files"].items())
            or any(c["pair_result"] != "same" for c in result["cases"].values() if c["category"] == "control")):
        raise ValueError("画像の二票または対照の来歴が異なる")
    read = {(r["page"], r["line_index"]): r for r in result["cases"].values()}
    rows = audit.load(old.OUT / "public.json")
    scoring = audit.v14.old.score.unpack_scoring(audit.load(old.OUT / "scoring.json"))
    changes = []
    for r in rows:
        ident = r["key"], r["line_index"]
        if ident not in ACCEPT:
            continue
        confirmation = read[ident]
        answer = confirmation["readings"]
        before = r["effective"]
        after = answer["pair"]["text"]
        if (confirmation["pair_result"] != "different" or before != confirmation["expected"]
                or answer["coordinates"] or any(v["text"] != after for k, v in answer.items() if k in ("gpt", "claude"))
                or not r["image_population"] or r["raw_region"] is not None
                or not before.startswith("野崎家別邸迨暇堂")
                or after != "野﨑" + before[2:]):
            raise ValueError("固定画像で確認した異体字の一字以外に違いがある")
        was = r["ocr_error"]
        new = hashlib.sha256(after.encode("utf-8")).hexdigest() != r["ocr_normalized_sha256"]
        item, = (item for item in scoring[r["group"]]["lines"] if (item["key"], item["line_index"]) == ident)
        if item["rule"] != "exact" or item["error"] != was:
            raise ValueError("既定の採点と画像正解の行が異なる")
        item.update(error=new, label_source="image-only-kanpo-glyph-v38")
        r.update(effective=after, source="image-only-kanpo-glyph-v38", ocr_error=new,
                 development_proof={"stage": SOURCE.name, "lock_sha256": audit.sha(manifest),
                                    "readings_sha256": audit.sha(SOURCE / "result.json")})
        changes.append({"page": ident[0], "line_index": ident[1], "before": before, "after": after,
                        "before_error": was, "after_error": new})
    if len(changes) != len(ACCEPT):
        raise ValueError("固定画像を確認した対象が不足")
    with np.load(audit.v14.old.PREDICTIONS, allow_pickle=False) as data:
        outcome = evaluate(scoring, data["probabilities"])
    OUT.mkdir()
    audit.save_once(OUT / "public.json", audit.encoded(rows))
    audit.save_once(OUT / "scoring.json", audit.encoded(audit.v14.old.score.pack_scoring(scoring)))
    materials = (Path(__file__), HERE / "physical-review.md", BASE / "physical-proof.json",
                 BASE / "candidate-score.json", old.OUT / "public.json", old.OUT / "scoring.json",
                 SOURCE / "result.json", manifest, audit.v14.old.PREDICTIONS)
    audit.save_once(HERE / "result.json", audit.encoded({
        "scope": "development-only", "changed": prior["changed"] + changes,
        "evaluation": outcome, "same_predictions_sha256": audit.sha(audit.v14.old.PREDICTIONS),
        "development_control_issues": prior["development_control_issues"],
        "inputs": {str(p): audit.sha(p) for p in materials},
        "artifacts": {p.name: audit.sha(p) for p in OUT.iterdir()},
    }))
    print("累計", len(prior["changed"]) + len(changes), "訂正、開発6組", outcome["all_pass"],
          "公開3組", outcome["all_gates"], flush=True)


if __name__ == "__main__":
    main()
