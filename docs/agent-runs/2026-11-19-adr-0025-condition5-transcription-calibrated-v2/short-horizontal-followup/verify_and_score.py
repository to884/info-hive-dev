"""白書の短い枠の原票をたどり、採点への影響を開発診断として確認する。"""

import importlib.util
import json
from pathlib import Path
import sys

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parent / "source-position-expansion"))
from verify_and_score import ballot, check_cards, CORPUS, load, np, score, scoring, sha
from verify_first_attempts import check_files

COMBINED = CORPUS / "transcription-calibrated-v2-2026-11-19/source-and-figure-development"
COMBINED_REPORT = HERE.parent / "raster-figure-expansion/combined-fixed-scores.json"
SELECT = ("defense-p0089", "disaster-p0092")
OUT = COMBINED.parent / HERE.name


def imported(name, path):
    spec = importlib.util.spec_from_file_location(name, path)
    loaded = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(loaded)
    return loaded


def derive(module, files, sessions):
    cards, expected, manifest = module.material()
    result_path = module.HERE / "result.json"
    report = load(result_path)
    if manifest != load(module.LOCK) or report["lock_sha256"] != sha(module.LOCK) or report["errors"]:
        raise ValueError("固定画像か受領に未確認がある")
    if len(report["receipts"]) != 2 * len(manifest["packs"]):
        raise ValueError("二票がそろっていない")
    by_reader = {(r["arm"], r["role"]): r for r in report["receipts"]}
    if len(by_reader) != len(report["receipts"]):
        raise ValueError("二票が重複")
    saved_path = module.OUT / "decisions.json"
    if sha(saved_path) != report["decisions_sha256"]:
        raise ValueError("決定した記録と保存した版が異なる")
    saved = load(saved_path)
    rows, additions = [], {}
    for name, pack in manifest["packs"].items():
        place = module.OUT / "cards" / name
        check_cards(module.OUT, name, pack, cards[name], files)
        votes = {}
        for role in ("sol", "opus"):
            receipt = by_reader[name, role]
            check_files(module.OUT, receipt, pack, place, files)
            votes[role] = ballot(module.OUT, pack, receipt, sessions, files)
        for i, subject in expected[name].items():
            rule = getattr(module, "short", module).outcome
            a, b = (votes[role][i] for role in ("sol", "opus"))
            state = rule(a, b, subject)
            text = a if state == "new-agreement" else None
            key, index = subject["key"], subject["line_index"]
            rows.append({"key": key, "line_index": index, "result": state, "text": text})
            if key in SELECT and subject["previous"] == "unreadable":
                additions[key, index] = {"result": "short-figure:" + state, "text": text,
                                         "stage": module.HERE.name, "pack": name, "id": i}
    if rows != saved:
        raise ValueError("保存した判定は二票の全文から復元できない")
    return additions, (module.LOCK, result_path, Path(module.__file__))


def main():
    result_path = HERE / "development-scores.json"
    if result_path.exists() or (OUT / "scoring.json").exists():
        raise FileExistsError("開発用の採点を上書きしない")
    stage = imported("followup", HERE / "run.py")
    sessions, blobs = set(), {}
    initial, p1 = derive(stage.short, blobs, sessions)
    followup, p2 = derive(stage, blobs, sessions)
    if initial.keys() & followup.keys() or len(initial | followup) != 9:
        raise ValueError("白書で読んだ9行が一致しない")
    meta = load(COMBINED_REPORT)
    path = COMBINED / "candidate-labels.json"
    if sha(path) != meta["artifacts"]["candidate-labels.json"]:
        raise ValueError("先行の正解補充と違う")
    old = {(r["key"], r["line_index"]): r for r in load(path)}
    if old.keys() & (initial.keys() | followup.keys()):
        raise ValueError("新旧の補充対象が重複")
    records = old | initial | followup
    sample, base, y, updates, fixed_paths, file_metadata = scoring(records)
    blobs.update(file_metadata)
    neighbor = CORPUS / "neighbor-orientation-flag/predictions.npz"
    n_result = HERE.parent / "neighbor-orientation-flag/result.json"
    v11 = CORPUS / "flag-cross-axis-v11/predictions.npy"
    v_info = score.audit.RESULTS / "v11-cross-axis-results.json"
    if sha(neighbor) != load(n_result)["predictions_sha256"] or sha(v11) != load(v_info)["prediction_sha256"]:
        raise ValueError("比較元の予測の版が違う")
    with np.load(neighbor, allow_pickle=False) as f:
        prob = f["probabilities"]
    scorer = imported("counted", HERE.parent / "counted-assignments/counted.py")
    compare = HERE.parent / "counted-assignments/crosscheck.json"
    crosschecked = load(compare)["inputs"]
    for s in (Path(scorer.__file__), Path(score.frozen.score_v4.__file__), Path(score.frozen.score_v4.score_v2.__file__)):
        if crosschecked[str(s)] != sha(s):
            raise ValueError("元の採点と比較したコードが異なる")
    dependencies = (Path(__file__), *p1, *p2, *fixed_paths, path, COMBINED_REPORT, neighbor, n_result, v11, v_info,
                    Path(scorer.__file__), compare, Path(score.training.__file__))
    dependencies = {str(s): sha(s) for s in dependencies}
    cache = OUT / "scoring.json"
    score.audit.save(OUT / "candidate-labels.json", [{"key": k, "line_index": i} | r for (k, i), r in sorted(records.items())])
    score.audit.save(cache, score.pack_scoring(sample))
    with (OUT / "labels.npz").open("xb") as stream:
        np.savez_compressed(stream, y=y)
    score.audit.save(OUT / "provenance.json", {"inputs": dependencies, "files": blobs})
    evaluations = {}
    for name, raw in ((load(n_result)["candidate"], prob), (score.SELECTED, base),
                      ("v11-cross-axis-hgb@0.15", np.load(v11, allow_pickle=False))):
        if raw.shape != y.shape or not np.isfinite(raw).all():
            raise ValueError("全行の予測がそろわない")
        flags = raw >= score.THRESHOLD
        points = score.training.evaluate(sample, flags, name)
        results = {}
        for g, s in score.training.predicted_samples(sample, flags).items():
            val = scorer.robust(s, score.frozen.score_v4.score_v2, public_margin=g.endswith("-public"))
            results[g] = val
            print(name, g, val["assignments"], val["checked"], val["pass"], val["gate"], flush=True)
        evaluations[name] = {"points": points, "robust": results}
    score.audit.save(result_path, {"scope": "development-diagnostic-paper-only-no-official-label-change",
                                  "rows": len(records), "sessions": len(sessions), "new_public_rows_by_group": updates,
                                  "pilot": [{"group": name, "result": load(folder)["counts"]} for name, folder in
                                            (("mixed", p1[1]), ("whitepapers", p2[1]))],
                                  "inputs": dependencies, "scoring_sha256": sha(cache), "fixed_predictions": evaluations})


if __name__ == "__main__":
    main()
