"""二人の採点と本文に基づく裁定を結び、最終の採点を作る。"""
from __future__ import annotations
import argparse
from pathlib import Path
import grade_reader_models as semantic
import reader_measurement_runtime as capture


def compare(out):
    primary_map = semantic.read(out / "blind/map.json")
    secondary_map = semantic.read(out / "second-judge-map.json")
    primary = semantic.read(out / "semantic-grades-opus.json")
    secondary = semantic.read(out / "semantic-grades-sol.json")
    if set(primary) != set(primary_map["records"]) or set(secondary) != set(secondary_map["records"]):
        raise ValueError("採点者の回答が欠けている")
    by_file = {v["file"]: (key, v["sha256"]) for key, v in secondary_map["records"].items()}
    rows, required, agreed = {}, [], 0
    for blind, identity in primary_map["records"].items():
        sid, sha = by_file[identity["file"]]
        if sha != identity["sha256"] or capture.digest((out / "runs" / identity["file"]).read_bytes()) != sha:
            raise ValueError("採点した回答の対応が変わった")
        one, two = primary[blind], secondary[sid]
        if (len(one["labels"]) != len(two["labels"])
                or any(label not in ("supported", "omitted", "wrong") for grade in (one, two) for label in grade["labels"])
                or any(not isinstance(grade[k], list) for grade in (one, two) for k in ("citation_errors", "unsupported_claims"))):
            raise ValueError("採点者の命題や指摘の形が違う")
        same = one["labels"] == two["labels"]
        agreed += sum(a == b for a, b in zip(one["labels"], two["labels"]))
        if (not same or any(one[k] or two[k] for k in ("citation_errors", "unsupported_claims"))):
            required.append(blind)
        rows[blind] = {"file": identity["file"], "sha256": sha, "opus": one, "sol": two}
    return {"rows": rows, "requires_adjudication": required, "agreed_labels": agreed,
            "total_labels": sum(len(v["labels"]) for v in primary.values())}


def reconcile(out):
    comparison = compare(out)
    adjudication = semantic.read(out / "semantic-adjudications.json")
    expected_sources = {name: capture.digest((out / name).read_bytes()) for name in
                        ("semantic-grades-opus.json", "semantic-grades-sol.json", "blind/map.json", "second-judge-map.json")}
    if adjudication["sources"] != expected_sources:
        raise ValueError("裁定と採点の来歴が一致しない")
    resolutions = adjudication["resolutions"]
    if not set(comparison["requires_adjudication"]) <= set(resolutions) or not set(resolutions) <= set(comparison["rows"]):
        raise ValueError("判定の違いや指摘に未裁定がある")
    result = {}
    for blind, row in comparison["rows"].items():
        if blind in resolutions:
            resolution = resolutions[blind]
            if not resolution.get("reason"):
                raise ValueError("本文に基づく裁定の根拠がない")
            result[blind] = {key: resolution[key] for key in ("labels", "citation_errors", "unsupported_claims", "notes")}
        else:
            result[blind] = row["opus"]
    semantic.write(out / "semantic-grades.json", result)
    semantic.write(out / "semantic-comparison.json", comparison)
    files = ["semantic-grades-opus.json", "semantic-grades-sol.json", "second-judge-map.json",
             "semantic-adjudications.json", "semantic-comparison.json", "semantic-grading-sol-app.json",
             "blind-sol/input-manifest.json", "semantic-grading-opus-status.json", "rubric-clarifications.json",
             "link-resolution-check.json", "blind-sol/task.md"]
    files += ["blind-sol/" + rel for rel in semantic.read(out / "second-judge-map.json")["files"]]
    semantic.write(out / "semantic-provenance.json", {
        "fingerprint": semantic.read(out / "experiment.json")["fingerprint"],
        "input_map_sha256": capture.digest((out / "blind/map.json").read_bytes()),
        "final_grades_sha256": capture.digest((out / "semantic-grades.json").read_bytes()),
        "judge_models": ["claude-opus-5-5", "gpt-6.1-sol"],
        "files": {name: capture.digest((out / name).read_bytes()) for name in files},
        "independence_limit": "Opusは採点後にsummaryとmanual-spotcheckの改行の形式を読んだと報告した。Solは隔離した別のディレクトリで先行判定を見ずに採点。完全な匿名性や採点の正しさの証明とはしない。"})
    print(f"命題の一致 {comparison['agreed_labels']}/{comparison['total_labels']}、裁定 {len(resolutions)}件")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("command", choices=["compare", "reconcile"])
    parser.add_argument("--out", type=Path, required=True)
    args = parser.parse_args()
    if args.command == "compare":
        semantic.write(args.out / "semantic-comparison.json", compare(args.out))
    else:
        reconcile(args.out)
