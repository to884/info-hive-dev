"""開発用候補の正解をv9の別版として固定し、後続へ来歴を渡す。"""

from collections import Counter, defaultdict
import hashlib
import importlib.util
import json
from pathlib import Path
import sys

HERE = Path(__file__).resolve().parent
PARENT = HERE.parent
sys.path.insert(0, str(PARENT / "source-position-expansion"))
from verify_and_score import ballot, check_cards, CORPUS, load, np, score, sha
from verify_first_attempts import check_files

CANONICAL = score.audit.normalize
SHORT_REPORT = PARENT / "short-horizontal-followup/development-scores.json"
DEV = CORPUS / "transcription-calibrated-v2-2026-11-19"
SHORT_PRIVATE = DEV / "short-horizontal-followup"
V9 = CORPUS / "flag-revalidation-v9"
OUT = DEV / HERE.name
STUDY = PARENT / "known-audit-glyphs"


def candidate_from_new_balls():
    source = STUDY / "run.py"
    spec = importlib.util.spec_from_file_location("audit_diagnosis", source)
    trial = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(trial)
    manifest, cards = trial.material()
    fixed, result = STUDY / "lock.json", STUDY / "result.json"
    reported = load(result)
    if manifest != load(fixed) or reported["lock_sha256"] != sha(fixed) or reported["failures"]:
        raise ValueError("既知の診断事例の二票または固定画像が違う")
    receipts = {(r["arm"], r["role"]): r for r in reported["receipts"]}
    if len(receipts) != 2 * len(manifest["packs"]):
        raise ValueError("診断事例に二票がそろわない")
    entries = load(trial.AUDIT / "start.json")["entries"]
    matches, evidence, sessions = {}, {}, set()
    for name, pack in manifest["packs"].items():
        directory = trial.OUT / "cards" / name
        check_cards(trial.OUT, name, pack, cards[name], evidence)
        ballots = {}
        for role in ("sol", "opus"):
            receipt = receipts[name, role]
            check_files(trial.OUT, receipt, pack, directory, evidence)
            ballots[role] = ballot(trial.OUT, pack, receipt, sessions, evidence)
        for i, obj in manifest["rows"][name].items():
            case = obj["case"]
            a, b = (ballots[role][i] for role in ("sol", "opus"))
            if case not in ("M01", "M02", "U12"):
                continue
            if not a or a != b:
                raise ValueError("既知の診断例を二票で再現できない")
            row = entries[obj["entry"]]
            if case == "M01":
                if "))" not in a or "⟦" in a or not row["targets"]["image"]["known"]:
                    raise ValueError("二つ見える閉じ括弧の画像補充を確認できない")
            else:
                marker, spelling = ("⟦round⟧", "•") if case == "M02" else ("⟦trail⟧", "・" * 5)
                if a.count(marker) != 1:
                    raise ValueError("画像二読が同形の符号の位置に一致しない")
                a = CANONICAL(a.replace(marker, spelling))
                if a != CANONICAL(row["targets"]["region"]["text"]):
                    raise ValueError("画像と出典を結合した本文が以前の生の領域と異なる")
            matches[case] = {"key": row["key"], "line_index": row["line_index"], "normalized": a,
                             "stage": STUDY.name, "id": i, "pack": name}
    if set(matches) != {"M01", "M02", "U12"}:
        raise ValueError("診断の3行と一致しない")
    return matches, evidence, (source, fixed, result)


def updated_records():
    report = load(SHORT_REPORT)
    labels = SHORT_PRIVATE / "candidate-labels.json"
    scoring = SHORT_PRIVATE / "scoring.json"
    source = SHORT_PRIVATE / "provenance.json"
    provenance = load(source)
    for path, digest in provenance["inputs"].items():
        if sha(Path(path)) != digest:
            raise ValueError("白書までの試験に使った根拠が変化")
    if sha(scoring) != report["scoring_sha256"]:
        raise ValueError("直近の開発採点と違う")
    proofs = {(a["key"], a["line_index"]): a for a in load(labels)}
    if report["rows"] != len(proofs):
        raise ValueError("開発の正解記録に行の重複か欠落")
    current, evidence, deps = candidate_from_new_balls()
    repair = current["M01"]
    key = repair["key"], repair["line_index"]
    if key in proofs:
        raise ValueError("既知の脱落の修正が別の開発補充と重なる")
    proofs[key] = {"text": repair["normalized"], "result": "verified-original-repeat", "pack": repair["pack"],
                   "id": repair["id"], "stage": repair["stage"]}
    return proofs, current, evidence, (SHORT_REPORT, labels, scoring, source, *deps)


def assemble(proofs, corrections):
    plan = score.audit.RESULTS / "v9-revalidation-plan.json"
    bound = load(plan)
    identity_path, scoring_path = V9 / "row-identities.json", V9 / "scoring-data.json"
    coverage_file = score.audit.RESULTS / "region-v9-coverage.json"
    image_file = CORPUS / "region-visual-v9/final.json"
    image_receipt = score.audit.RESULTS / "region-visual-v9-result.json"
    if (sha(identity_path) != bound["identities_sha256"] or sha(scoring_path) != bound["scoring_data_sha256"]
            or sha(image_file) != load(image_receipt)["final_sha256"]):
        raise ValueError("旧版の固定を検査できない")
    image = load(image_file)["rows"]
    visual = {(r["key"], r["line_index"]): r for r in image}
    if len(visual) != len(image) or len(visual) != 2865:
        raise ValueError("元の画像正解の全母集団と異なる")
    by_key = {}
    coverage = load(coverage_file)["files"]
    for name, digest in coverage.items():
        path = CORPUS / "public" / "region-v9" / name
        if sha(path) != digest:
            raise ValueError("旧版の生の領域正解が変化")
        page = load(path)
        by_key[page["key"]] = page["lines"]
    data = score.unpack_scoring(load(scoring_path))
    identity = load(identity_path)
    private, transitions, all_sources, seen = [], defaultdict(Counter), {}, set()
    cursor = 0
    for name, sample in data.items():
        for line in sample["lines"]:
            row = identity[cursor]
            cursor += 1
            key, i = row["key"], row["line_index"]
            ident = key, i
            if (key, i, name) != (line["key"], line["line_index"], line["group"]):
                raise ValueError("採点行とOCRの対応が異なる")
            if row["stratum"] != "public":
                continue
            if key not in all_sources:
                primary = CORPUS / "ocr3" / (key + ".json")
                all_sources[key] = (sha(primary), load(primary)["lines"])
            primary = all_sources[key][1][i]
            region = by_key[key][i]
            if (hashlib.sha256(primary["text"].encode()).hexdigest() != row["ocr_text_sha256"]
                    or primary["box"] != row["box"] or row["box"] != region["box"]):
                raise ValueError("主OCRの本文か枠が異なる")
            old, proof = visual.get(ident), proofs.get(ident)
            origin = line["label_source"]
            old_exact = line["rule"] == "exact"
            effective = None
            if old_exact:
                if origin == "fresh-image":
                    if old is None or old["status"] == "unreadable":
                        raise ValueError("画像正解が旧採点と異なる")
                    effective = CANONICAL(old["text"])
                else:
                    if "undecided" in region:
                        raise ValueError("生の正解が旧採点と異なる")
                    effective = CANONICAL(region["text"])
                if bool(line["error"]) != (effective != CANONICAL(primary["text"])):
                    raise ValueError("旧正解の本文を旧採点に戻せない")
            state = "unknown" if not old_exact else ("error" if line["error"] else "correct")
            previous = effective
            if proof is not None:
                seen.add(ident)
                if old is None or (old_exact and proof["result"] != "verified-original-repeat"):
                    raise ValueError("開発補充が旧画像の未決定または既知の括弧修正に一致しない")
                if proof["text"] is not None:
                    effective = proof["text"]
                    if CANONICAL(effective) != effective:
                        raise ValueError("補充の正規化が既定と違う")
                    line.update(rule="exact", error=effective != CANONICAL(primary["text"]),
                                eye=True, label_source="v10-image-candidate")
                    origin = "v10-image-candidate"
            now = "unknown" if effective is None else ("error" if line["error"] else "correct")
            transitions[name][state + "->" + now] += 1
            transitions[name]["changed-body"] += previous is not None and effective is not None and previous != effective
            private.append({**row, "allocation_axis": "y" if primary.get("vertical") else "x",
                            "ocr_normalized_sha256": hashlib.sha256(CANONICAL(primary["text"]).encode()).hexdigest(),
                            "raw_region": None if "undecided" in region else region["text"],
                            "effective": effective, "image_population": ident in visual, "source": origin,
                            "ocr_error": line["error"] if effective is not None else None,
                            "development_proof": None if proof is None else {k: proof[k] for k in ("stage", "pack", "id", "result")}})
    if cursor != len(identity) or len(private) != 8822 or seen != proofs.keys():
        raise ValueError("次版と既存の全行の対応が異なる")
    if sum(r["raw_region"] is not None for r in private) != 5988 or sum(r["image_population"] for r in private) != 2865:
        raise ValueError("二つの母集団の分母を変えた")
    deps = (plan, identity_path, scoring_path, coverage_file, image_file, image_receipt)
    inputs = {key: value[0] for key, value in all_sources.items()}
    return private, data, transitions, inputs, deps


def main():
    out = HERE / "candidate-lock.json"
    if OUT.exists() or out.exists():
        raise FileExistsError("固定済みの次版を上書きしない")
    proofs, corrections, receipts, deps = updated_records()
    rows, data, transitions, primary, dependencies = assemble(proofs, corrections)
    paths = (*deps, *dependencies, Path(__file__), HERE / "protocol.md", Path(score.__file__),
             Path(score.frozen.score_v4.__file__))
    inputs = {str(p): sha(p) for p in paths}
    OUT.mkdir()
    score.audit.save(OUT / "public.json", rows)
    score.audit.save(OUT / "scoring.json", score.pack_scoring(data))
    y = np.asarray([int(r["error"]) if r["rule"] == "exact" else np.nan
                    for sample in data.values() for r in sample["lines"]])
    with (OUT / "labels.npz").open("xb") as stream:
        np.savez_compressed(stream, y=y)
    score.audit.save(OUT / "candidate-proof.json", {"inputs": inputs, "diagnostic_receipts": receipts,
                                                   "ocr_pages": primary, "corrections": corrections})
    score.audit.save(out, {"scope": "frozen-development-reference-candidate-not-audited",
                           "public_rows": len(rows), "region_population": 5988, "image_population": 2865,
                           "updated_or_rechecked": len(proofs), "transitions": transitions,
                           "artifacts": {p.name: sha(p) for p in OUT.iterdir()}, "separate_prediction_required": True})
    print(sha(out), dict(transitions), flush=True)


if __name__ == "__main__":
    main()
