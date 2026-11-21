"""図表の画像票を読み直して再現し、照合済みの点線の候補と一緒に再採点する。"""

from collections import Counter
import importlib.util
import inspect
import json
from pathlib import Path
import sys

HERE = Path(__file__).resolve().parent
SHARED = HERE.parent / "source-position-expansion"
sys.path.insert(0, str(SHARED))
from verify_first_attempts import check_files
from verify_and_score import ballot, check_cards, CORPUS, load, np, score, scoring, sha
from refit_verified import DEVELOPMENT, RESULT, V9


def import_run(folder):
    path = folder / "run.py"
    spec = importlib.util.spec_from_file_location(folder.name, path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def derived(init, value_a, value_b):
    if value_a is None or value_b is None:
        return "both-unknown" if value_a is value_b else "one-unknown"
    if value_a != value_b:
        return "disagreement"
    if not value_a:
        return "agreed-empty"
    if init["previous"] == "readable":
        return "matches-control" if value_a == init["old_normalized"] else "differs-from-control"
    return "new-agreement"


def verify_run(mod, manifest, requests, cards, subjects, first, files, sessions):
    if manifest != load(mod.LOCK):
        raise ValueError("事前に固定した元画像を再現できない")
    result = load(mod.HERE / "result.json")
    if result["lock_sha256"] != sha(mod.LOCK):
        raise ValueError("実行結果の固定SHAが違う")
    saved = result["rows" if first else "outcomes"]
    receipts = {(r["arm"], r["role"]): r for r in result["receipts"]}
    if len(receipts) != 2 * len(requests) or len(receipts) != len(result["receipts"]):
        raise ValueError("図表の二票が全部そろわない")
    outcomes, labels = {}, {}
    for name, pack in requests.items():
        card_path = mod.OUT / "cards" / name
        check_cards(mod.OUT, name, pack, cards[name], files)
        votes = []
        for role in ("sol", "opus"):
            receipt = receipts[name, role]
            check_files(mod.OUT, receipt, pack, card_path, files)
            votes.append(ballot(mod.OUT, pack, receipt, sessions, files))
        for ident, sample in subjects[name].items():
            a, b = (v[ident] for v in votes)
            status = derived(sample, a, b)
            if status != saved[name][ident]:
                raise ValueError("図表の判定を二票から再現できない")
            group = outcomes.setdefault(sample["previous"], Counter())
            group[status] += 1
            if sample["previous"] == "unreadable":
                labels[sample["line_index"]] = {"text": a if status == "new-agreement" else None,
                                                "result": "figure:" + status, "pack": name, "id": ident,
                                                "stage": mod.HERE.name}
    if (outcomes if first else outcomes["unreadable"]) != result["counts"]:
        raise ValueError("図表の集計が二票と違う")
    return labels, outcomes


def main():
    out = CORPUS / "transcription-calibrated-v2-2026-11-19" / "source-and-figure-development"
    result = HERE / "combined-fixed-scores.json"
    if out.exists() or result.exists():
        raise FileExistsError("開発用の正解や採点を上書きしない")
    old = import_run(HERE.parent / "raster-figure-pilot")
    expansion = import_run(HERE)
    files, sessions = {}, set()
    p_manifest, p_items, p_cards = old.material()
    p, p_count = verify_run(old, p_manifest, p_manifest["packs"], p_cards, p_items, True, files, sessions)
    e_manifest, e_cards = expansion.material()
    items = {name: {i: {"line_index": index, "previous": "unreadable"} for i, index in pack["targets"].items()}
             for name, pack in e_manifest["packs"].items()}
    e_requests = {name: pack["request"] for name, pack in e_manifest["packs"].items()}
    e, e_count = verify_run(expansion, e_manifest, e_requests, e_cards, items, False, files, sessions)
    if p.keys() & e.keys() or len(p | e) != 41:
        raise ValueError("図表の対象の重複または欠落")
    e_saved = expansion.OUT / "candidate-lines.json"
    e_summary = load(HERE / "result.json")
    if sha(e_saved) != e_summary["private_lines_sha256"]:
        raise ValueError("図表の転記候補が保存したものと異なる")
    for r in load(e_saved):
        if r["key"] != old.PAGE or e[r["line_index"]]["text"] != r["normalized_text"]:
            raise ValueError("保存候補の本文を二票から再現できない")
    dot_layer = DEVELOPMENT / "candidate-labels.json"
    if sha(dot_layer) != load(RESULT)["artifacts"]["candidate-labels.json"]:
        raise ValueError("点線の既存の検証結果が変わった")
    points = {(r["key"], r["line_index"]): r for r in load(dot_layer)}
    figure = {(old.PAGE, i): r for i, r in (p | e).items()}
    if points.keys() & figure.keys():
        raise ValueError("点線と図表の両方を同じ行に使っている")
    records = points | figure
    data, base_prob, y, updates, paths, ocr = scoring(records)
    files.update(ocr)
    benchmark = score.audit.BENCH
    bench_result = benchmark / "results/v11-cross-axis-results.json"
    bench_pred = CORPUS / "flag-cross-axis-v11/predictions.npy"
    extra_result = HERE.parent / "neighbor-orientation-flag/result.json"
    extra_pred = CORPUS / "neighbor-orientation-flag/predictions.npz"
    if (sha(bench_pred) != load(bench_result)["prediction_sha256"]
            or sha(extra_pred) != load(extra_result)["predictions_sha256"]):
        raise ValueError("開発で比較する保存予測が違う")
    with np.load(extra_pred, allow_pickle=False) as f:
        neighbor = f["probabilities"]
    out.mkdir()
    annotations = out / "candidate-labels.json"
    score.audit.save(annotations, [dict(key=k, line_index=i, **{a: b for a, b in r.items() if a not in {"key", "line_index"}})
                                  for (k, i), r in sorted(records.items())])
    score.audit.save(out / "scoring.json", score.pack_scoring(data))
    with (out / "labels.npz").open("xb") as f:
        np.savez_compressed(f, y=y)
    dependencies = (*paths, bench_result, bench_pred, extra_result, extra_pred, old.LOCK, expansion.LOCK, RESULT,
                    HERE / "result.json", old.HERE / "result.json", e_saved, Path(__file__), Path(old.__file__),
                    Path(expansion.__file__), Path(score.__file__), Path(score.frozen.score_v4.__file__),
                    Path(score.training.__file__), Path(inspect.getfile(score.audit.normalize)))
    score.audit.save(out / "provenance.json", {"fixed": {str(p): sha(p) for p in dependencies}, "corpus": files})
    results = {}
    for name, prob in ((score.SELECTED, base_prob), (load(extra_result)["candidate"], neighbor),
                       ("v11-cross-axis-hgb@0.15", np.load(bench_pred, allow_pickle=False))):
        if prob.shape != y.shape or not np.isfinite(prob).all():
            raise ValueError("固定予測が全行に対応しない")
        results[name] = score.evaluate(data, prob)
        results[name]["points"]["candidate"] = name
        print(name, {k: (v["assignments"], v["pass"]) for k, v in results[name]["robust"].items() if k.endswith("-public")}, flush=True)
    score.audit.save(result, {"scope": "development-only-point-and-raster-figure-agreements",
                             "counts": {"pilot": p_count, "expansion": e_count}, "new_sessions_verified": len(sessions),
                             "updates": updates, "artifacts": {p.name: sha(p) for p in out.iterdir()},
                             "limitation": "pilot-lock-had-a-filename-collision-results-recomputed",
                             "fixed_predictions": results})


if __name__ == "__main__":
    main()
