"""監査の二つの母集団を先に固定し、別の操作で標本を一度抽出する。"""

import argparse
from collections import Counter
import hashlib
import inspect
import json
from pathlib import Path
import sys

HERE = Path(__file__).resolve().parent
PARENT = HERE.parent
sys.path.insert(0, str(PARENT / "v10-reference-candidate"))
from assemble import OUT as CANDIDATE, CORPUS, CANONICAL, load, np, score, sha
from seal import SEAL
from audit_selection_v9 import COHORTS, cohort, draw, identity

OUT = CORPUS / "reference-audit-v10"
CANDIDATE_FILES = PARENT / "v10-reference-candidate"
LOCK, SCORE = (CANDIDATE_FILES / name for name in ("candidate-lock.json", "candidate-score.json"))
PREDICTIONS = CORPUS / "neighbor-orientation-flag/predictions.npz"
POLICY = score.audit.ROOT / "docs/plans/adr-0025-condition5-source-anchored-reference-v10-2026-11-19.md"
PRIOR_POLICY = score.audit.ROOT / "docs/plans/adr-0025-condition5-image-evidence-next-2026-11-19.md"
SEEDS = {"region": 2026111901, "image": 2026111902}
MANIFEST = HERE / "population-lock.json"
PREVIOUS_AUDIT = CORPUS / "reference-audit-v9/start.json"


def digest(text):
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def take_public_rows():
    fixed, scored = load(LOCK), load(SCORE)
    prepared = load(SEAL)
    if (prepared["evaluation_sha256"] != sha(SCORE) or prepared["threshold"] != score.THRESHOLD
            or any(sha(Path(f)) != value for f, value in prepared["files"].items())):
        raise ValueError("正解、予測、採点器を結んだ事前固定が違う")
    if (scored["label_lock_sha256"] != sha(LOCK) or scored["prediction_sha256"] != sha(PREDICTIONS)
            or scored["threshold"] != score.THRESHOLD or not scored["evaluation"]["all_pass"]
            or not scored["evaluation"]["all_gates"]):
        raise ValueError("固定した候補の既定6組・公開の追加関門を結び付けられない")
    for name, expected in fixed["artifacts"].items():
        if sha(CANDIDATE / name) != expected:
            raise ValueError("凍結した正解か証跡が変化")
    identities = load(CORPUS / "flag-revalidation-v9/row-identities.json")
    records = load(CANDIDATE / "public.json")
    with np.load(PREDICTIONS, allow_pickle=False) as archive:
        probabilities = archive["probabilities"]
    if (probabilities.shape != (15658,) or len(identities) != 15658
            or not np.isfinite(probabilities).all() or np.any((probabilities < 0) | (probabilities > 1))):
        raise ValueError("固定し直した全行の予測ではない")
    flags = {identity(row): bool(probabilities[i] >= score.THRESHOLD)
             for i, row in enumerate(identities) if row["stratum"] == "public"}
    if len(flags) != 8822 or len(records) != 8822 or {identity(row) for row in records} != set(flags):
        raise ValueError("全公開の評価行と正解が対応しない")
    return records, flags


def populations(records, flags):
    pool = {"region": [], "image": []}
    previously_audited = {identity(r) for r in load(PREVIOUS_AUDIT)["entries"]}
    if len(previously_audited) != 380:
        raise ValueError("旧監査の全行ではない")
    for row in records:
        ident = identity(row)
        primary = row["ocr_normalized_sha256"]
        base = {k: row[k] for k in ("key", "line_index", "box", "ocr_text_sha256", "allocation_axis")}
        base.update(side=row["group"].rsplit("-", 1)[0], normalized_ocr_sha256=primary,
                    development_intake=bool(row["development_proof"]), previously_audited=ident in previously_audited)
        value = row["raw_region"]
        if value is not None:
            error = digest(CANONICAL(value)) != primary
            pool["region"].append({**base, "cohort": cohort(error, flags[ident]), "text": value,
                                   "known": True, "error": error})
        if row["image_population"]:
            effective = row["effective"]
            if effective is None:
                pool["image"].append({**base, "cohort": "unknown", "text": "?", "known": False, "error": None})
            else:
                error = digest(CANONICAL(effective)) != primary
                if error != row["ocr_error"]:
                    raise ValueError("画像正解の本文と主OCRの正誤が異なる")
                pool["image"].append({**base, "cohort": cohort(error, flags[ident]), "text": effective,
                                      "known": True, "error": error})
    if len(pool["region"]) != 5988 or len(pool["image"]) != 2865:
        raise ValueError("二つの母集団の対象が異なる")
    return pool


def strata(pool):
    result = {}
    for domain, rows in pool.items():
        counts = Counter((r["side"], r["cohort"]) for r in rows)
        tags = COHORTS + (("unknown",) if domain == "image" else ())
        if set(counts) - {(s, k) for s in score.audit.SIDES for k in tags}:
            raise ValueError("既定以外の層")
        result[domain] = {s: {label: counts[s, label] for label in tags} for s in score.audit.SIDES}
    return result


def prepare():
    if OUT.exists() or MANIFEST.exists():
        raise FileExistsError("監査の母集団を上書きしない")
    rows, flags = take_public_rows()
    pools = populations(rows, flags)
    if not all(str(seed) in PRIOR_POLICY.read_text(encoding="utf-8") for seed in SEEDS.values()):
        raise ValueError("抽出種が以前の事前計画と異なる")
    methods = tuple(HERE / p for p in ("protocol.md", "cards.py", "readers.py", "runner.py", "resolve.py", "point_ink.py", "source_commands.py"))
    paths = (Path(__file__), POLICY, PRIOR_POLICY, LOCK, SCORE, SEAL, PREVIOUS_AUDIT, PREDICTIONS, CANDIDATE / "public.json",
             CANDIDATE / "candidate-proof.json", CANDIDATE / "scoring.json", Path(sys.modules[draw.__module__].__file__),
             Path(score.audit.__file__), Path(inspect.getfile(CANONICAL)),
             HERE.parent / "dot-layout-v2/independent-pdf-commands.py",
             HERE.parent / "dot-layout-v2/independent-pdf-commands-v2.json", *methods)
    inputs = {str(p): sha(p) for p in paths}
    OUT.mkdir()
    population_path = OUT / "population.json"
    score.audit.save(population_path, pools)
    score.audit.save(MANIFEST, {"scope": "fixed-before-sampling", "seeds": SEEDS, "inputs": inputs,
                                "population_sha256": sha(population_path), "strata": strata(pools),
                                "sampling_rule": "min-15-per-original-stratum",
                                "selection_executed": False})
    print(sha(MANIFEST), "母集団固定。抽出は未実行。", flush=True)


def draw_once(expected):
    path = OUT / "selection.json"
    started = OUT / "draw-started.json"
    if path.exists() or started.exists():
        raise FileExistsError("同じ版の監査をもう一度抽出できない")
    manifest = load(MANIFEST)
    population_file = OUT / "population.json"
    if expected != sha(MANIFEST) or SEEDS != manifest["seeds"] or sha(population_file) != manifest["population_sha256"]:
        raise ValueError("抽出前に固定した母集団と異なる")
    if any(sha(Path(k)) != v for k, v in manifest["inputs"].items()):
        raise ValueError("抽出前に固定した正解・予測・方法が変化")
    pools = load(population_file)
    if strata(pools) != manifest["strata"]:
        raise ValueError("固定した層の分母が異なる")
    with started.open("x", encoding="utf-8") as stream:
        json.dump({"population_lock_sha256": expected}, stream)
    chosen, summary = {}, {}
    for domain, rows in pools.items():
        tags = COHORTS + (("unknown",) if domain == "image" else ())
        selected, summary[domain] = draw(rows, SEEDS[domain], tags)
        for row in selected:
            ident = identity(row)
            base = {k: row[k] for k in ("side", "key", "line_index", "box", "ocr_text_sha256", "allocation_axis",
                                       "normalized_ocr_sha256", "development_intake", "previously_audited")}
            both = chosen.setdefault(ident, {**base, "targets": {}})
            if any(both[k] != v for k, v in base.items()):
                raise ValueError("両母集団に入る同じ行で共通の証跡が異なる")
            both["targets"][domain] = {k: row[k] for k in ("cohort", "text", "known", "error")}
    score.audit.save(path, {"population_lock_sha256": expected, "summary": summary,
                            "selected": [chosen[k] for k in sorted(chosen)]})
    print(sha(path), len(chosen), "行を一度抽出", flush=True)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("action", choices=("prepare", "draw"))
    parser.add_argument("--population-lock-sha256")
    args = parser.parse_args()
    if args.action == "prepare":
        prepare()
    else:
        draw_once(args.population_lock_sha256)
