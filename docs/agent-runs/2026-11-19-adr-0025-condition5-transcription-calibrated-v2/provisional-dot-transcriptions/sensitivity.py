"""仮転記をすべて正しいと仮定した場合だけを、固定予測と既存採点器で測る。"""

from collections import Counter, defaultdict
import hashlib
import json
from pathlib import Path
import sys

import numpy as np

HERE = Path(__file__).resolve().parent
BENCH = HERE.parents[2] / "research/adr-0025-condition5-2026-11-16"
CORPUS = BENCH / "corpus"
V9 = CORPUS / "flag-revalidation-v9"
sys.path.insert(0, str(BENCH / "scripts"))
import revalidate_flags_v9 as score


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def load(path):
    return json.loads(path.read_text(encoding="utf-8"))


def identity(row):
    return row["key"], row["line_index"]


def main():
    output = HERE / "sensitivity.json"
    if output.exists():
        raise FileExistsError("採点の診断を上書きしない")
    fixed_path = BENCH / "results/v9-fixed-revalidation.json"
    plan_path = BENCH / "results/v9-revalidation-plan.json"
    fixed, plan = load(fixed_path), load(plan_path)
    scoring_path, predictions_path = V9 / "scoring-data.json", V9 / "predictions.npz"
    identities_path = V9 / "row-identities.json"
    if (sha(plan_path) != fixed["plan_sha256"] or sha(predictions_path) != fixed["prediction_sha256"]
            or sha(scoring_path) != plan["scoring_data_sha256"] or sha(identities_path) != plan["identities_sha256"]
            or plan["threshold"] != score.THRESHOLD):
        raise ValueError("元の固定資料が一致しない")
    full_path = CORPUS / "provisional-dot-transcriptions/full-lines.json"
    provisional_path = HERE / "result.json"
    provisional = load(provisional_path)
    if sha(full_path) != provisional["private_full_lines_sha256"]:
        raise ValueError("仮転記の本文が証跡と異なる")
    fields = ("key", "line_index", "box", "canonical_dot_codepoint", "symbol_count", "provisional", "reasons")
    private = load(full_path)
    valid = {identity(r): r for r in provisional["rows"] if r["provisional"]}
    if {identity(r): {k: r[k] for k in fields} for r in private} != valid or len(private) != len(valid):
        raise ValueError("仮転記一覧と公開する対応記録が異なる")
    by_identity = {identity(r): r for r in private}
    data = score.unpack_scoring(load(scoring_path))
    saved_identities = load(identities_path)
    raw_ocr = {}
    seen = set()
    updates = defaultdict(Counter)
    changed = {}
    with np.load(predictions_path, allow_pickle=False) as arrays:
        probabilities = arrays["probabilities"]
    if probabilities.shape != (15658,) or not np.isfinite(probabilities).all():
        raise ValueError("固定確率の全行が一致しない")
    flags = probabilities >= score.THRESHOLD
    cursor = 0
    for group, sample in data.items():
        for row in sample["lines"]:
            record = saved_identities[cursor]
            row_id = identity(row)
            if row_id != identity(record) or row["unit"] != record["unit"]:
                raise ValueError("採点と固定予測の順が一致しない")
            candidate = by_identity.get(row_id)
            if candidate is not None:
                if not group.endswith("-public") or row["rule"] != "unresolved" or row_id in seen:
                    raise ValueError("仮転記が元の未決定の公開行と対応しない")
                seen.add(row_id)
                key, i = row_id
                if key not in raw_ocr:
                    raw_ocr[key] = load(CORPUS / "ocr3" / (key + ".json"))["lines"]
                primary = raw_ocr[key][i]
                digest = hashlib.sha256(primary["text"].encode()).hexdigest()
                if not (candidate["ocr_text_sha256"] == record["ocr_text_sha256"] == digest
                        and candidate["box"] == record["box"] == primary["box"]):
                    raise ValueError("OCRの本文か枠を固定したものと照合できない")
                error = score.audit.normalize(candidate["text"]) != score.audit.normalize(primary["text"])
                row.update(rule="exact", error=error)
                updates[group]["rows"] += 1
                updates[group]["errors_if_provisional"] += error
                updates[group]["detected_errors_if_provisional"] += error and bool(flags[cursor])
                changed[group] = True
            cursor += 1
    if cursor != len(flags) or seen != by_identity.keys():
        raise ValueError("仮転記と採点行の対応が欠ける")
    points = score.training.evaluate(data, flags, score.SELECTED)
    selected = score.training.predicted_samples(data, flags)
    previous = fixed["refitted_fixed_configuration"]["robust"]
    results = dict(previous)
    for group in sorted(changed):
        print("全配置の診断", group, flush=True)
        results[group] = score.frozen.score_v4.robust_verdict(selected[group], public_margin=True)
    inputs = (Path(__file__), provisional_path, full_path, fixed_path, plan_path, scoring_path,
              predictions_path, identities_path, BENCH / "scripts/score_v4.py")
    with output.open("x", encoding="utf-8") as stream:
        json.dump({"scope": "hypothetical-performance-with-provisional-ground-truth",
                   "inputs": {p.name: sha(p) for p in inputs}, "flag_rule": score.SELECTED,
                   "updates": updates, "points": points, "robust": results}, stream, ensure_ascii=False, indent=2)
    print(json.dumps({g: {"updates": updates[g], "result": results[g]} for g in changed},
                     ensure_ascii=False), flush=True)


if __name__ == "__main__":
    main()
