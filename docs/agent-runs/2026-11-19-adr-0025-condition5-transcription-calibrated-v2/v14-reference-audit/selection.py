"""固定した採点と正解案から、独立監査の母集団を固定し一度だけ抽出する。"""

import argparse
import importlib.util
from pathlib import Path
import sys

HERE = Path(__file__).resolve().parent
OLD = HERE.parent / "v10-reference-audit/selection.py"
sys.path.insert(0, str(OLD.parent))
spec = importlib.util.spec_from_file_location("previous_audit_selection", OLD)
old = importlib.util.module_from_spec(spec)
spec.loader.exec_module(old)

from readers import encoded, save_once

OUT = old.CORPUS / "reference-audit-v14"
RESULT = HERE.parent / "v14-reference-candidate/result.json"
CANDIDATE = old.CANDIDATE.parent / "v14-reference-candidate"
LOCK = HERE / "population-lock.json"
SEEDS = {"region": 2026112001, "image": 2026112002}
load, sha = old.load, old.sha


def prepared():
    prior, flags = old.take_public_rows()
    report = load(RESULT)
    evaluation = report["evaluation"]
    if (report["same_predictions_sha256"] != sha(old.PREDICTIONS) or not evaluation["all_pass"]
            or not evaluation["all_gates"]):
        raise ValueError("同じ固定予測で開発6組と公開3組の条件を満たしていない")
    if any(sha(Path(p)) != h for p, h in (report["inputs"] | report["raw_receipts"]).items()):
        raise ValueError("事前固定に入れる採点または原票が変化")
    if any(sha(CANDIDATE / p) != h for p, h in report["artifacts"].items()):
        raise ValueError("訂正を反映した正解が変化")
    path = CANDIDATE / "public.json"
    records = load(path)
    before = {old.identity(r): r for r in prior}
    after = {old.identity(r): r for r in records}
    edits = {(x["page"], x["line_index"]) for x in report["changed"]}
    if before.keys() != after.keys() or len(before) != 8822 or {k for k in before if before[k] != after[k]} != edits:
        raise ValueError("訂正した行または全体の分母が異なる")
    pools = old.populations(records, flags)
    related = [old.OUT / "selection.json"]
    known = {old.identity(r) for r in load(related[0])["selected"]}
    studies = ("v11-ordered-image-pilot", "v11-column-slot-pilot", "v11-guided-image-pilot",
               "v12-readable-regions-pilot", "v13-layout-generalization")
    intake = set()
    for name in studies:
        artifact = HERE.parent / name / "result.json"
        related.append(artifact)
        intake.update(old.identity(row) for row in load(artifact)["rows"].values())
    for rows in pools.values():
        for row in rows:
            key = old.identity(row)
            row["previously_audited"] |= key in known
            row["development_intake"] |= key in intake
    return pools, related


def prepare():
    if OUT.exists() or LOCK.exists():
        raise FileExistsError("先に固定した独立監査の母集団がある")
    pools, related = prepared()
    files = (Path(__file__), OLD, HERE / "protocol.md", HERE / "packets.py", HERE / "resolve.py", HERE / "source.py",
             HERE.parent / "v12-reference-audit/delivery.py", old.LOCK, old.SCORE, old.SEAL,
             HERE.parent / "v11-visible-source-pilot/commands.py",
             HERE.parent / "v11-visible-source-pilot/round_overlap.py",
             HERE.parent / "v13-layout-generalization/run.py", HERE.parent / "v12-readable-regions-pilot/run.py",
             OLD.parent / "source_commands.py", OLD.parent / "resolve.py", OLD.parent / "readers.py",
             OLD.parent / "point_ink.py", OLD.parent / "cards.py",
             HERE.parent / "dot-layout-v2/independent-pdf-commands.py",
             HERE.parent / "dot-layout-v2/independent-pdf-commands-v2.json",
             Path(old.score.frozen.score_v4.__file__), Path(old.score.audit.__file__),
             old.PREDICTIONS, RESULT, CANDIDATE / "public.json", CANDIDATE / "scoring.json", *related)
    value = encoded(pools)
    OUT.mkdir()
    save_once(OUT / "population.json", value)
    save_once(LOCK, encoded({"scope": "fixed-before-sampling", "seeds": SEEDS,
                            "population_sha256": sha(OUT / "population.json"), "strata": old.strata(pools),
                            "inputs": {str(p): sha(p) for p in files}}))
    print(sha(LOCK), "母集団を固定。抽出は未実行", flush=True)


def draw(expected):
    lock = load(LOCK)
    manifest = OUT / "population.json"
    if lock["seeds"] != SEEDS or sha(LOCK) != expected or sha(manifest) != lock["population_sha256"]:
        raise ValueError("事前固定した母集団が異なる")
    if any(sha(Path(p)) != h for p, h in lock["inputs"].items()):
        raise ValueError("抽出前に固定した採点・正解・方法が変化")
    fixed = load(manifest)
    if old.strata(fixed) != lock["strata"]:
        raise ValueError("層の分母が異なる")
    save_once(OUT / "draw-started.json", encoded({"population_lock_sha256": expected}))
    merged, strata = {}, {}
    for domain, rows in fixed.items():
        cohorts = old.COHORTS + (("unknown",) if domain == "image" else ())
        sampled, strata[domain] = old.draw(rows, SEEDS[domain], cohorts)
        for row in sampled:
            target = {k: row[k] for k in ("cohort", "text", "known", "error")}
            shared = {k: v for k, v in row.items() if k not in target}
            entry = merged.setdefault(old.identity(row), {**shared, "targets": {}})
            if any(entry[k] != v for k, v in shared.items()):
                raise ValueError("領域正解と画像補充で同じ行の証跡が異なる")
            entry["targets"][domain] = target
    selected = OUT / "selection.json"
    save_once(selected, encoded({"population_lock_sha256": expected, "summary": strata,
                                 "selected": [merged[k] for k in sorted(merged)]}))
    print(sha(selected), len(merged), "行を抽出", flush=True)


if __name__ == "__main__":
    cli = argparse.ArgumentParser(description=__doc__)
    cli.add_argument("action", choices=("prepare", "draw"))
    cli.add_argument("--lock")
    args = cli.parse_args()
    if args.action == "prepare":
        prepare()
    else:
        draw(args.lock)
