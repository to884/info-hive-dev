"""生の領域と画像正解を別の母集団として抽出・集計する。"""

from collections import Counter
import math
import hashlib
import random

import numpy as np

import region_audit_v6 as audit
import region_truth_v9 as truth
import region_visual_v9 as visual
import revalidate_flags_v9 as fixed

COHORTS = ("TP", "FN", "FP", "TN")
SEEDS = {"region": 20261118, "image": 2026111801}


def identity(row):
    return row["key"], row["line_index"]


def cohort(error, flagged):
    return ("TP" if flagged else "FN") if error else ("FP" if flagged else "TN")


def populations():
    fixed.checked()
    integrity = audit.load(audit.RESULTS / "v9-fixed-prediction-integrity.json")
    result = audit.load(audit.RESULTS / "v9-fixed-revalidation.json")
    if integrity["result_sha256"] != audit.sha(audit.RESULTS / "v9-fixed-revalidation.json") or not integrity["both_results_reproduced"] or integrity["plan_sha256"] != audit.sha(fixed.PLAN) or result["prediction_sha256"] != audit.sha(fixed.OUT / "predictions.npz"):
        raise ValueError("固定設定の新しいLOPOの予測の検証がない")
    with np.load(fixed.OUT / "predictions.npz", allow_pickle=False) as raw:
        probabilities = raw["probabilities"]
    identities = audit.load(fixed.OUT / "row-identities.json")
    if probabilities.shape != (15658,) or len(identities) != 15658 or not np.isfinite(probabilities).all() or ((probabilities < 0) | (probabilities > 1)).any():
        raise ValueError("新しい全行の確率ではない")
    rows = {identity(row): {**row, "flagged": bool(probabilities[i] >= fixed.THRESHOLD)} for i, row in enumerate(identities) if row["stratum"] == "public"}
    if len(rows) != 8822:
        raise ValueError("全公開の行の対応が違う")
    fresh = {identity(row): row for row in audit.load(visual.OUT / "final.json")["rows"]}
    if len(fresh) != 2865:
        raise ValueError("全画像の正解の母集団と違う")
    primary, region_pool, image_pool = {}, [], []
    for path in sorted(truth.DATA.glob("*.json")):
        page = audit.load(path)
        key = page["key"]
        primary[key] = audit.load(audit.BENCH / "corpus/ocr3" / path.name)["lines"]
        for region in page["lines"]:
            ident = key, region["line_index"]
            row = rows[ident]
            line = primary[key][region["line_index"]]
            base = {"side": row["group"].rsplit("-", 1)[0], "key": key, "line_index": region["line_index"],
                    "box": row["box"], "ocr_text_sha256": row["ocr_text_sha256"], "allocation_axis": "y" if line.get("vertical") else "x",
                    "normalized_ocr_sha256": hashlib.sha256(audit.normalize(line["text"]).encode("utf-8")).hexdigest()}
            if "undecided" not in region:
                error = audit.normalize(region["text"]) != audit.normalize(line["text"])
                region_pool.append({**base, "cohort": cohort(error, row["flagged"]), "text": region["text"], "known": True, "error": error})
            if ident in fresh:
                value = fresh[ident]
                known = value["status"] != "unreadable"
                error = audit.normalize(value["text"]) != audit.normalize(line["text"]) if known else None
                image_pool.append({**base, "cohort": cohort(error, row["flagged"]) if known else "unknown", "text": value["text"], "known": known, "error": error})
    if len(region_pool) != 5988 or len(image_pool) != 2865:
        raise ValueError("二つの監査の母集団の全数が違う")
    return {"region": region_pool, "image": image_pool}


def draw(rows, seed, cohorts):
    if len({identity(r) for r in rows}) != len(rows) or any(r["side"] not in audit.SIDES or r["cohort"] not in cohorts for r in rows):
        raise ValueError("母集団の重複か対象外の層がある")
    rng, selected, summary = random.Random(seed), [], {}
    for side in audit.SIDES:
        summary[side] = {}
        for category in cohorts:
            values = sorted((r for r in rows if r["side"] == side and r["cohort"] == category), key=identity)
            chosen = rng.sample(values, min(15, len(values)))
            summary[side][category] = {"population": len(values), "sample": len(chosen)}
            selected.extend(chosen)
    return selected, summary


def select(pools):
    chosen, summary = {}, {}
    for domain in ("region", "image"):
        selected, summary[domain] = draw(pools[domain], SEEDS[domain], COHORTS + (("unknown",) if domain == "image" else ()))
        for row in selected:
            ident = identity(row)
            if ident not in chosen:
                chosen[ident] = {k: row[k] for k in ("side", "key", "line_index", "box", "ocr_text_sha256", "allocation_axis", "normalized_ocr_sha256")} | {"targets": {}}
            elif any(chosen[ident][k] != row[k] for k in ("side", "box", "ocr_text_sha256", "allocation_axis", "normalized_ocr_sha256")):
                raise ValueError("二つの監査の同じ行の箱か対応が違う")
            chosen[ident]["targets"][domain] = {k: row[k] for k in ("cohort", "known", "text", "error")}
    return [chosen[k] for k in sorted(chosen)], summary


def reference(codex, opus):
    if not strict_answer(codex) or not strict_answer(opus):
        raise ValueError("参照回答の形式が違う")
    if codex["status"] != "unreadable" and opus["status"] != "unreadable" and audit.normalize(codex["text"]) == audit.normalize(opus["text"]):
        return codex
    return {"status": "unreadable", "text": "?"}


def strict_answer(value):
    return isinstance(value, dict) and set(value) == {"status", "text"} and audit.valid_answer(value)


def summarize(entries, summary, references):
    if set(references) != {identity(r) for r in entries} or not all(strict_answer(r) for r in references.values()):
        raise ValueError("監査の参照に過不足か形式の違いがある")
    result = {}
    for domain in ("region", "image"):
        sides = {}
        for side in audit.SIDES:
            groups = {}
            for category, population in summary[domain][side].items():
                targets = [r for r in entries if r["side"] == side and domain in r["targets"] and r["targets"][domain]["cohort"] == category]
                if len(targets) != population["sample"] or population["sample"] != min(15, population["population"]):
                    raise ValueError("各層の固定した抽出数が違う")
                counts = Counter()
                for row in targets:
                    ref = references[identity(row)]
                    target = row["targets"][domain]
                    if category == "unknown":
                        if target["known"]:
                            raise ValueError("不明の診断へ既知の正解を入れた")
                        counts["reference_unknown" if ref["status"] == "unreadable" else "reference_known"] += 1
                    else:
                        if not target["known"]:
                            raise ValueError("既知の監査へ不明の正解を入れた")
                        if ref["status"] == "unreadable":
                            counts["unresolved_reference"] += 1
                        elif audit.normalize(target["text"]) != audit.normalize(ref["text"]):
                            counts["different"] += 1
                        else:
                            counts["same"] += 1
                        if ref["status"] != "unreadable":
                            ref_error = hashlib.sha256(audit.normalize(ref["text"]).encode("utf-8")).hexdigest() != row["normalized_ocr_sha256"]
                            counts["error_label_changed" if ref_error != target["error"] else "error_label_same"] += 1
                groups[category] = {**population, **counts}
            known = [g for k, g in groups.items() if k != "unknown"]
            N = sum(g["population"] for g in known)
            different = sum(g.get("different", 0) for g in known)
            unresolved = sum(g.get("unresolved_reference", 0) for g in known)
            status = "fail" if different else ("inconclusive" if unresolved or not N else "pass")
            def weighted(include_unresolved):
                return math.fsum(g["population"] * (g.get("different", 0) + (g.get("unresolved_reference", 0) if include_unresolved else 0)) / g["sample"] for g in known if g["sample"]) / N if N else None
            sides[side] = {"groups": groups, "known_population": N, "different": different,
                "unresolved_reference": unresolved, "status": status,
                "weighted_difference": weighted(False), "weighted_difference_or_unresolved": weighted(True), "confidence_bound": False}
        result[domain] = {"sides": sides, "status": "fail" if any(r["status"] == "fail" for r in sides.values()) else
            ("inconclusive" if any(r["status"] == "inconclusive" for r in sides.values()) else "pass")}
    return result
