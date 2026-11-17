"""固定した命題を、モデル名と費用を伏せた回答に照合して選定する。採点自体はレビュアーが行う。"""
from __future__ import annotations
import argparse
import ast
import hashlib
import json
from pathlib import Path
import random
import re
import reader_measurement_runtime as capture


def read(path):
    return json.loads(path.read_text(encoding="utf-8"))


def write(path, value):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, ensure_ascii=False, indent=1) + "\n", encoding="utf-8", newline="\n")


def bundle(out):
    experiment, data = capture.recorded_experiment(out)
    questions = {q["id"]: q for q in data["questions"]}
    paths = sorted((out / "runs").glob("*.json"))
    random.Random(3203).shuffle(paths)
    mapping, grouped = {}, {}
    for i, path in enumerate(paths, 1):
        record = read(path)
        if record["fingerprint"] != experiment["fingerprint"] or not capture.valid_observation(record):
            raise ValueError(f"測定が無効: {path}")
        blind = f"A{i:03d}"
        mapping[blind] = {"file": path.name, "sha256": capture.digest(path.read_bytes())}
        # 自分のモデル名を報告する節を採点者へ渡さない。モデルと費用の対応表も別に置く。
        answer = re.sub(r"^## モデル\s*\n.*?(?=^## |\Z)", "", record["result"], flags=re.M | re.S)
        grouped.setdefault(record["id"], []).append({"id": blind, "answer": answer, "opened": record["opened"]})
    manifest = {}
    for qid, answers in grouped.items():
        question = questions[qid]
        pages = {}
        for key in sorted({p for a in answers for p in a["opened"]}):
            scope, rel = capture.scoped(key)
            root = capture.roots(out)[scope]
            path = root / rel
            if not path.resolve().is_relative_to(root.resolve()):
                raise ValueError("wiki の外のパス")
            pages[key] = path.read_text(encoding="utf-8")
        value = {"question": question["prompt"], "assertions": question["assertions"], "pages": pages, "answers": answers}
        path = out / "blind" / "questions" / f"{qid}.json"
        write(path, value)
        manifest[path.name] = capture.digest(path.read_bytes())
    write(out / "blind/map.json", {"fingerprint": experiment["fingerprint"], "records": mapping, "bundles": manifest})
    print(f"{len(paths)} 回の回答を伏せた")


def finalize(out):
    experiment, data = capture.recorded_experiment(out)
    mapping = read(out / "blind/map.json")
    if mapping["fingerprint"] != experiment["fingerprint"]:
        raise ValueError("入力の指紋が違う")
    questions = {q["id"]: q for q in data["questions"]}
    if set(mapping["bundles"]) != {qid + ".json" for qid in questions}:
        raise ValueError("採点に渡した問いの写しが欠けている")
    bundle_ids = set()
    for name, expected in mapping["bundles"].items():
        if capture.digest((out / "blind/questions" / name).read_bytes()) != expected:
            raise ValueError("採点に渡した写しが変わった")
        value = read(out / "blind/questions" / name)
        question = questions[Path(name).stem]
        if value["question"] != question["prompt"] or value["assertions"] != question["assertions"]:
            raise ValueError("採点の問いと命題が固定した入力と違う")
        opened_union = set()
        for answer in value["answers"]:
            blind = answer["id"]
            if blind in bundle_ids or blind not in mapping["records"]:
                raise ValueError("採点の写しのIDが重複か不正")
            bundle_ids.add(blind)
            identity = mapping["records"][blind]
            record_path = out / "runs" / identity["file"]
            if capture.digest(record_path.read_bytes()) != identity["sha256"]:
                raise ValueError("採点後に回答が変わった")
            record = read(record_path)
            normalized = re.sub(r"^## モデル\s*\n.*?(?=^## |\Z)", "", record["result"], flags=re.M | re.S)
            if (record["id"] != question["id"] or answer["answer"] != normalized
                    or answer["opened"] != record["opened"]):
                raise ValueError("採点の写しが実際の回答と違う")
            opened_union.update(answer["opened"])
        if set(value["pages"]) != opened_union:
            raise ValueError("採点の写しに本文が欠けている")
        for key, body in value["pages"].items():
            scope, rel = capture.scoped(key)
            root = capture.roots(out)[scope].resolve()
            path = (root / rel).resolve()
            if not path.is_relative_to(root) or path.read_text(encoding="utf-8") != body:
                raise ValueError("採点の本文が固定したwikiと違う")
    if bundle_ids != set(mapping["records"]):
        raise ValueError("採点の写しに回答が欠けている")
    grades = read(out / "semantic-grades.json")
    if set(grades) != set(mapping["records"]):
        raise ValueError("採点が欠けているか、計画にない採点がある")
    provenance = read(out / "semantic-provenance.json")
    if (provenance["fingerprint"] != experiment["fingerprint"]
            or provenance["input_map_sha256"] != capture.digest((out / "blind/map.json").read_bytes())
            or provenance["final_grades_sha256"] != capture.digest((out / "semantic-grades.json").read_bytes())
            or len(set(provenance["judge_models"])) < 2 or len(provenance["files"]) < 2):
        raise ValueError("意味の採点の入力・結果・複数の採点者の来歴が結び付かない")
    for rel, expected in provenance["files"].items():
        path = (out / rel).resolve()
        if not path.is_relative_to(out.resolve()) or capture.digest(path.read_bytes()) != expected:
            raise ValueError("採点者の記録が変わった")
    table, rows, seen = {}, [], set()
    for blind, identity in mapping["records"].items():
        path = out / "runs" / identity["file"]
        if capture.digest(path.read_bytes()) != identity["sha256"]:
            raise ValueError("採点後に回答が変わった")
        record, grade = read(path), grades[blind]
        q = questions[record["id"]]
        labels = grade["labels"]
        if len(labels) != len(q["assertions"]) or any(v not in ("supported", "omitted", "wrong") for v in labels):
            raise ValueError(f"命題の採点が不正: {blind}")
        if not isinstance(grade["citation_errors"], list) or not isinstance(grade["unsupported_claims"], list):
            raise ValueError(f"引用の採点が不正: {blind}")
        key = (record["id"], record["model"], record["effort"], record["run"])
        if key in seen or not capture.valid_observation(record):
            raise ValueError("重複か無効な測定")
        seen.add(key)
        name = f"{record['model']}-{record['effort']}"
        cell = table.setdefault(record["class"], {}).setdefault(name, {
            "n": 0, "semantic": 0.0, "cost": 0.0, "duration_ms": 0.0, "quality_fail": 0,
            "wrong": 0, "citation_errors": 0, "unsupported_claims": 0, "must_missing": 0, "models": []})
        must = {":".join(capture.scoped(p)) for p in q.get("must_read", [])}
        missing = must - set(record["opened"])
        cell["n"] += 1
        cell["semantic"] += labels.count("supported") / len(labels)
        cell["wrong"] += labels.count("wrong")
        cell["cost"] += record["cost_usd"]
        cell["duration_ms"] += record["duration_ms"]
        cell["citation_errors"] += len(grade["citation_errors"])
        cell["unsupported_claims"] += len(grade["unsupported_claims"])
        cell["must_missing"] += bool(missing)
        cell["quality_fail"] += not bool(re.search(r"^## 答え\s*\n\S", record["result"], re.M))
        if record["model_used"] not in cell["models"]:
            cell["models"].append(record["model_used"])
        rows.append({"blind": blind, "file": path.name, "sha256": identity["sha256"], **grade})
    cli_versions = {read(out / "runs" / entry["file"]).get("cli_version") for entry in mapping["records"].values()}
    if len(cli_versions) != 1 or not all(isinstance(v, str) and v for v in cli_versions):
        raise ValueError("測定のCLIの版がそろっていない")
    expected = {(q["id"], m, e, r) for q in questions.values()
                for m, e in capture.COMBOS + ([capture.INLINE] if q["class"] == "R0" else [])
                for r in range(1, experiment["spec"]["runs"] + 1)}
    if expected != seen:
        raise ValueError("全組の測定がそろっていない")
    selected = {}
    for cls, cells in table.items():
        for cell in cells.values():
            for metric in ("semantic", "cost", "duration_ms"):
                cell[metric] /= cell["n"]
        best = max(c["semantic"] for c in cells.values())
        eligible = [name for name, c in cells.items() if best > 0 and c["semantic"] >= .95 * best
                    and not any(c[k] for k in ("quality_fail", "wrong", "citation_errors", "unsupported_claims", "must_missing"))
                    and len(c["models"]) == 1]
        eligible.sort(key=lambda name: (cells[name]["cost"], cells[name]["duration_ms"], name))
        selected[cls] = {"best": best, "threshold": .95 * best, "eligible": eligible,
                         "selected": eligible[0] if eligible else None}
        if cls == "R0":
            selected[cls].update(reader_comparison_lowest_cost=selected[cls]["selected"],
                                 selected=None, policy="main-inherit")
    result = {"status": "semantic_adjudicated", "fingerprint": experiment["fingerprint"],
              "rubric_sha256": experiment["spec"]["data_sha256"], "grades_sha256": capture.digest((out / "semantic-grades.json").read_bytes()),
              "grader_sha256": capture.digest(Path(__file__).read_bytes()), "table": table, "selection": selected, "rows": rows,
              "semantic_provenance_sha256": capture.digest((out / "semantic-provenance.json").read_bytes()),
              "cli_versions": sorted(cli_versions),
              "r0_policy": "現在のメインが直接読む。新規CLIの費用では既存のメインの追加費用を比較できない。"}
    write(out / "model-selection.json", result)
    print(json.dumps({"table": table, "selection": selected}, ensure_ascii=False, indent=1))


def verify_product(out):
    decision = read(out / "model-selection.json")
    expected = {cls: tuple(decision["selection"][cls]["selected"].rsplit("-", 1)) for cls in ("R1", "R2", "R3")}
    path = capture.PLUGIN / "skills/info-hive/scripts/wiki_prompt_context.py"
    tree = ast.parse(path.read_text(encoding="utf-8"))
    actual = next(ast.literal_eval(node.value) for node in tree.body if isinstance(node, ast.Assign)
                  and any(isinstance(target, ast.Name) and target.id == "TIERS" for target in node.targets))
    if actual != expected:
        raise ValueError("製品のモデル表が意味の採点の選定と違う")
    print("製品のモデル表と意味の採点の選定が一致した")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("command", choices=["bundle", "finalize", "verify-product"])
    parser.add_argument("--out", type=Path, required=True)
    args = parser.parse_args()
    {"bundle": bundle, "finalize": finalize, "verify-product": verify_product}[args.command](args.out.resolve())
