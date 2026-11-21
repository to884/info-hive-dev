"""点線の二読で確認した開発ラベルに、既存の固定予測を当てて比べる。"""

from pathlib import Path

from refit_verified import DEVELOPMENT, RESULT, V9, BENCH, CORPUS, HERE, load, np, score, sha


def stored():
    results = BENCH / "results"
    variants = (
        ("v6-assisted", "flag-development-v6-mineru/predictions.npz", "v6-candidates.json", "v6-prediction-integrity.json"),
        ("v10-edge", "flag-edge-v10/predictions.npz", "v10-edge-results.json", "v10-edge-integrity.json"),
        ("v11-cross-axis", "flag-cross-axis-v11/predictions.npy", "v11-cross-axis-results.json", "v11-cross-axis-integrity.json"),
    )
    for label, path, meta, verified in variants:
        p, info, integrity = CORPUS / path, results / meta, results / verified
        raw, checked = load(info), load(integrity)
        expected_manifest = checked.get("result_sha256", checked.get("candidates_sha256"))
        if sha(info) != expected_manifest or raw["prediction_sha256"] != sha(p):
            raise ValueError("保存済みの予測は、再現した版と違う")
        if p.suffix == ".npz":
            with np.load(p, allow_pickle=False) as archive:
                if label == "v6-assisted":
                    arrays = {"v6-mineru-hgb": archive["v6-mineru-hgb"]}
                else:
                    arrays = {name: archive[name] for name in archive.files}
        else:
            arrays = {label: np.load(p, allow_pickle=False)}
        for name, values in arrays.items():
            yield name, values, tuple((f.relative_to(BENCH).as_posix(), sha(f)) for f in (p, info, integrity))


def main():
    path = HERE / "saved-prediction-comparison.json"
    if path.exists():
        raise FileExistsError("以前の比較を上書きしない")
    input_path = DEVELOPMENT / "scoring.json"
    summary = load(RESULT)
    if sha(input_path) != summary["artifacts"]["scoring.json"]:
        raise ValueError("原票で確認した開発用の採点と違う")
    data = score.unpack_scoring(load(input_path))
    outputs, provenance = {}, {}
    for name, prob, inputs in stored():
        if prob.shape != (15658,) or not np.isfinite(prob).all():
            raise ValueError("固定予測が全行分ない")
        outputs[name] = score.evaluate(data, prob)
        provenance.update(inputs)
        print(name, {k: v["pass"] for k, v in outputs[name]["robust"].items()}, flush=True)
    score.audit.save(path, {"scope": "development-only-existing-predictions-no-new-model",
                            "labels_report_sha256": sha(RESULT), "scoring_sha256": sha(input_path),
                            "files": provenance, "models": outputs})


if __name__ == "__main__":
    main()
