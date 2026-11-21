"""固定した開発行の原票を復元し、点線を確認した行だけで固定予測を再採点する。"""

from collections import Counter, defaultdict
import hashlib
import importlib.util
import json
from pathlib import Path

import numpy as np

HERE = Path(__file__).resolve().parent


def import_script(name, path):
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


expansion = import_script("expansion", HERE / "run.py")
confirmed = expansion.confirmed
position = expansion.position
fixed = import_script("sensitivity", HERE.parent / "provisional-dot-transcriptions/sensitivity.py")
score, sha, load = fixed.score, fixed.sha, fixed.load
BENCH, CORPUS, V9 = fixed.BENCH, fixed.CORPUS, fixed.V9
ACCEPTED = "body-position-plus-image-count-and-source"


def check_json_lock(folder, material, result):
    lock = folder / "lock.json"
    if result["lock_sha256"] != sha(lock) or material != {
        k: value for k, value in load(lock).items() if k != "fixed_at"
    }:
        raise ValueError("事前固定と回答の対応が違う")


def ballot(root, pack, receipt, sessions, evidence):
    role, session = receipt["role"], receipt["session"]
    if expansion.pilot.MODELS[role] != receipt["model"] or session in sessions:
        raise ValueError("画像担当のモデルかセッションの独立性が違う")
    sessions.add(session)
    arm, model, attempt = receipt["arm"], receipt["model"], receipt.get("attempt")
    folder = root / "reads" / role / arm
    name = f"{arm}-read1-{model}-{attempt}.jsonl" if role == "sol" else f"{arm}-response.jsonl"
    response = folder / name
    if (sha(response) != receipt["response_sha256"]
            or hashlib.sha256(pack["prompt"].encode()).hexdigest() != receipt["prompt_sha256"]
            or pack["image_sha256"] != receipt["image_sha256"]):
        raise ValueError("原票または送付内容のハッシュが変わった")
    evidence[response.relative_to(CORPUS).as_posix()] = sha(response)
    payload = response.read_text(encoding="utf-8")
    if role == "sol":
        observed_session, _, votes = expansion.base.parse_response(payload, pack["ids"])
    else:
        votes, meta = expansion.pilot.opus.parse(payload, pack["ids"])
        observed_session = meta["session_id"]
    if observed_session != session or len(votes) != len(pack["ids"]):
        raise ValueError("原票から受領を復元できない")
    return votes


def check_cards(root, pack_name, pack, regenerated, evidence):
    if set(pack["images"]) != set(regenerated) or len(pack["images"]) != len(pack["image_sha256"]):
        raise ValueError("配布画像の対応が欠ける")
    for name, digest in zip(pack["images"], pack["image_sha256"], strict=True):
        actual = root / "cards" / pack_name / name
        if actual.read_bytes() != regenerated[name] or sha(actual) != digest:
            raise ValueError("配布した固定画像を再現できない")
        evidence[actual.relative_to(CORPUS).as_posix()] = digest


def add_labels(records, targets, expected, outcomes, stage, pack_name):
    for local_id, row in targets.items():
        if expected[local_id]["kind"] != "source-backed":
            continue
        address = fixed.identity(row)
        if address in records:
            raise ValueError("同一行の開発票を成績によって選べない")
        status = outcomes[local_id]
        label = expected[local_id]["exact"] if status == ACCEPTED else None
        records[address] = {"text": label, "result": status, "stage": stage, "pack": pack_name, "id": local_id}


def earlier(records, sessions, evidence, stage, builder, root):
    folder = HERE.parent / stage
    result = load(folder / "result.json")
    if stage == "source-anchored-position-pilot":
        targets, expected, cards, manifest = builder()
    else:
        expected, cards, manifest = builder()
        targets = manifest["targets"]
    check_json_lock(folder, manifest, result)
    by_pack = {(r["arm"], r["role"]): r for r in result["receipts"]}
    if len(by_pack) != len(result["receipts"]) or len(by_pack) != 2 * len(targets):
        raise ValueError("先行試験の各束の二票が対応しない")
    for name, rows in targets.items():
        pack = manifest["packs"][name]
        check_cards(root, name, pack, cards[name], evidence)
        left, right = (ballot(root, pack, by_pack[name, role], sessions, evidence) for role in ("sol", "opus"))
        decisions = {i: position.decision(left[i], right[i], expected[name][i]) for i in rows}
        saved = {i: row["result"] for i, row in result["outcomes"][name].items()}
        if {i: ACCEPTED if s == "physical-agreement-plus-source" else s for i, s in saved.items()} != decisions:
            raise ValueError("先行試験の判定が原票と異なる")
        add_labels(records, rows, expected[name], decisions, stage, name)
    return (folder / "lock.json", folder / "result.json")


def expanded(records, sessions, evidence):
    result_path = HERE / "result.json"
    result = load(result_path)
    cards, expected, manifest = expansion.materialize()
    root = expansion.OUT
    check_json_lock(HERE, manifest, result)
    before = len(sessions)
    total = Counter()
    for name, pack in manifest["packs"].items():
        check_cards(root, name, pack, cards[name], evidence)
        answers = {}
        for role in ("sol", "opus"):
            parent = root / "receipts" / name / role
            receipts = [load(path) for path in sorted(parent.glob("attempt-?.json"))]
            valid = [r["receipt"] for r in receipts if r["status"] == "received"]
            if len(valid) > 1 or not receipts or len(receipts) > (1 if role == "sol" else 2):
                raise ValueError("試行の回数または受領が重複している")
            if valid:
                if receipts[-1]["status"] != "received" or valid[0]["role"] != role:
                    raise ValueError("有効な票を受け取った後に再試行している")
                answers[role] = ballot(root, pack, valid[0], sessions, evidence)
            for path in sorted(parent.glob("attempt-*.json")):
                evidence[path.relative_to(CORPUS).as_posix()] = sha(path)
        outcomes = {i: position.decision(answers["sol"][i], answers["opus"][i], ref)
                    if len(answers) == 2 else "technical-unresolved" for i, ref in expected[name].items()}
        saved = root / "receipts" / name / "outcome.json"
        if outcomes != load(saved) or outcomes != result["results"][name]:
            raise ValueError("追加の二票から判定を再現できない")
        evidence[saved.relative_to(CORPUS).as_posix()] = sha(saved)
        total.update(outcomes.values())
        add_labels(records, pack["targets"], expected[name], outcomes, HERE.name, name)
    if result["counts"] != total or result["unique_sessions"] != len(sessions) - before:
        raise ValueError("二読の件数が原票に対応しない")
    return (HERE / "lock.json", result_path)


def scoring(records):
    plan_path = BENCH / "results/v9-revalidation-plan.json"
    prior_path = BENCH / "results/v9-fixed-revalidation.json"
    data_path, ids_path = V9 / "scoring-data.json", V9 / "row-identities.json"
    prediction_path, cache_path = V9 / "predictions.npz", V9 / "cache.npz"
    plan, prior = load(plan_path), load(prior_path)
    if (sha(plan_path) != prior["plan_sha256"] or sha(prediction_path) != prior["prediction_sha256"]
            or sha(ids_path) != plan["identities_sha256"] or sha(data_path) != plan["scoring_data_sha256"]
            or sha(cache_path) != plan["cache_sha256"] or plan["threshold"] != score.THRESHOLD):
        raise ValueError("元の採点、モデルまたは教師の固定が違う")
    with np.load(prediction_path, allow_pickle=False) as f:
        probabilities = f["probabilities"]
    with np.load(cache_path, allow_pickle=False) as f:
        labels = f["y"]
    if probabilities.shape != labels.shape or labels.shape != (15658,) or not np.isfinite(probabilities).all():
        raise ValueError("元の予測と採点の行数が違う")
    data, identities = score.unpack_scoring(load(data_path)), load(ids_path)
    updates, evidence, primary, seen = defaultdict(Counter), {}, {}, set()
    cursor = 0
    for group, sample in data.items():
        for row in sample["lines"]:
            identity = fixed.identity(row)
            attached = identities[cursor]
            if identity != fixed.identity(attached) or row["unit"] != attached["unit"] or row["group"] != group:
                raise ValueError("固定の採点と予測の順が違う")
            if identity in records:
                state = records[identity]
                if (identity in seen or row["stratum"] != "public" or row["rule"] != "unresolved"
                        or np.isfinite(labels[cursor])):
                    raise ValueError("補充の候補が以前の未決定公開行と対応しない")
                seen.add(identity)
                updates[group][state["result"]] += 1
                if state["text"] is not None:
                    key, index = identity
                    if key not in primary:
                        path = CORPUS / "ocr3" / (key + ".json")
                        primary[key] = load(path)["lines"]
                        evidence[path.relative_to(CORPUS).as_posix()] = sha(path)
                    ocr = primary[key][index]
                    if (hashlib.sha256(ocr["text"].encode()).hexdigest() != attached["ocr_text_sha256"]
                            or ocr["box"] != attached["box"]):
                        raise ValueError("元のOCR本文か枠が変わった")
                    error = score.audit.normalize(ocr["text"]) != state["text"]
                    row.update(rule="exact", error=error, eye=True, label_source="position-plus-source-development")
                    labels[cursor] = int(error)
                    updates[group]["confirmed_ocr_error"] += error
                    updates[group]["flagged_ocr_error"] += error and bool(probabilities[cursor] >= score.THRESHOLD)
            cursor += 1
    if cursor != len(labels) or seen != records.keys():
        raise ValueError("固定された評価行に補充が対応しない")
    paths = (plan_path, prior_path, data_path, ids_path, prediction_path, cache_path)
    return data, probabilities, labels, updates, paths, evidence


def main():
    OUT = expansion.OUT.parent / "source-position-verified-development"
    REPORT = HERE / "verified-fixed-score.json"
    if OUT.exists() or REPORT.exists():
        raise FileExistsError("照合済みの採点を上書きしない")
    records, sessions, evidence, paths = {}, set(), {}, [Path(__file__)]
    paths.extend(earlier(records, sessions, evidence, position.HERE.name, position.material, position.OUT))
    paths.extend(earlier(records, sessions, evidence, confirmed.HERE.name, confirmed.compose, confirmed.OUT))
    paths.extend(expanded(records, sessions, evidence))
    data, probabilities, labels, updates, scoring_paths, scoring_files = scoring(records)
    evidence.update(scoring_files)
    inputs = {p.relative_to(BENCH.parents[1]).as_posix(): sha(p) for p in (*paths, *scoring_paths)}
    OUT.mkdir()
    layer = OUT / "candidate-labels.json"
    with layer.open("x", encoding="utf-8") as stream:
        json.dump([dict(key=k, line_index=i, **r) for (k, i), r in sorted(records.items())],
                  stream, ensure_ascii=False, indent=2)
    with (OUT / "file-provenance.json").open("x", encoding="utf-8") as stream:
        json.dump({"workspace": inputs, "corpus": evidence}, stream, indent=2)
    archive = OUT / "scoring.json"
    with archive.open("x", encoding="utf-8") as stream:
        json.dump(score.pack_scoring(data), stream, ensure_ascii=False)
    with (OUT / "labels.npz").open("xb") as stream:
        np.savez_compressed(stream, y=labels)
    result = score.evaluate(data, probabilities)
    with REPORT.open("x", encoding="utf-8") as stream:
        json.dump({"scope": "development-only-verified-receipts-and-fixed-predictions",
                   "rows": len(records), "reader_sessions": len(sessions), "updates": updates,
                   "artifacts": {f.name: sha(f) for f in OUT.iterdir()}, "evaluation": result},
                  stream, ensure_ascii=False, indent=2)
    print(json.dumps({"updates": updates, "pass": {k: v["pass"] for k, v in result["robust"].items()}},
                     ensure_ascii=False), flush=True)


if __name__ == "__main__":
    main()
