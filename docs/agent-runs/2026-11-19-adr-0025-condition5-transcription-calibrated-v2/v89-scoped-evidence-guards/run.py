"""固定座標について審査した二件の補助証拠を、同じ原票と枠にだけ使う。"""

import argparse
from copy import deepcopy
from importlib.util import module_from_spec, spec_from_file_location
from pathlib import Path
import re
from collections import Counter

HERE = Path(__file__).resolve().parent
V85 = HERE.parent / "v85-scoped-reference-evidence"
spec = spec_from_file_location("scoped_evidence_replay_archive", V85 / "run.py")
previous = module_from_spec(spec)
spec.loader.exec_module(previous)
core, launch = previous.core, previous.launch
F_SHAPE, WHITE_POINT = previous.F_SHAPE, previous.WHITE_POINT
V64 = previous.V64
POLICY = HERE / "evidence-policy.json"
BODY_RANK = 5
SOURCE_REASON = "source-location-not-proven"


def reviewed(proof, review, receipt):
    recorded = core.load(receipt)
    verdict = re.findall(r"^Final Result:\s*([A-Z_]+)\s*$", review.read_text(encoding="utf-8"), re.M)
    if (verdict != ["APPROVED"] or recorded["state"] != "done"
            or recorded["model"] != "claude-opus-5-5" or recorded["effort"] != "high"
            or not recorded["session_id"] or Path(recorded["out"]).resolve() != review.resolve()
            or proof.stat().st_mtime > review.stat().st_mtime):
        raise ValueError("この証拠を承認したレビューを確認できない")


def freeze(shipment):
    index = previous.packet_index(shipment)
    catalog = launch.previous.packets.old.lookup()[1]
    method = core.load(core.LOCK)["inputs"]
    files = [Path(__file__), HERE / "protocol.md", V85 / "run.py", V64 / "result.json",
             shipment.folder / "packages.json", launch.OUT / "selection.json"]
    rules = {}
    for key, (relative, _) in previous.APPROVED.items():
        folder = HERE.parent / relative
        proof, review, receipt = (folder / name for name in ("result.json", "review-opus.md", "review-opus.md.status.json"))
        reviewed(proof, review, receipt)
        _, _, mapping, row = index[key]
        if mapping["partitions"]:
            raise ValueError("証拠の対象が区画に分かれている")
        assets = mapping["image_reference"]
        low = core.CORPUS / "probe-v4/png" / (row["key"] + ".png")
        high, _ = previous.file_geometry(shipment, assets)
        source, digest, page = catalog[row["key"]]
        bound = previous.image_binding(shipment, row, assets)
        if (core.sha(low) != assets["sha"]["150_dpi"] or core.sha(high) != bound["crop_png_sha256"]
                or core.sha(core.CORPUS / source) != digest or digest != assets["sha"]["pdf_sha256"]):
            raise ValueError("固定された画素とPDFの来歴が異なる")
        bound["verified_source"] = {"pdf": source, "sha256": digest, "page": page}
        fact = core.load(proof)
        if key == F_SHAPE:
            row_proof, = (entry for entry in fact["rows"] if f"{entry['page']}/{entry['line_index']}" == key)
            case, = row_proof["cases"]
            if not case["non_round"] or not case["isolated_450"]:
                raise ValueError("固定の先頭の筆画を丸から分けられない")
            bound["component_150"] = case["coarse"]
        else:
            command = fact["command"]
            if (f"{fact['page']}/{fact['line_index']}" != key or command["codepoint"] != "30FB"
                    or command["cid"] != 638 or fact["checks"]["150"]["outside_changed"]
                    or fact["checks"]["450"]["outside_max_channel_delta"] > 1):
                raise ValueError("白い小点の直接のCID証拠が足りない")
            bound["source_command"] = command
            bound["component_150"] = fact["checks"]["150"]["area"]
            bound["visual_rank"] = BODY_RANK
        rules[key] = bound
        files.extend((proof, review, receipt, low, high))
    return {"scope": "development-only-three-rows-recomputed", "evidence": rules,
            "inputs": method | previous.read_inputs(files)}


def policy(digest):
    if core.sha(POLICY) != digest:
        raise ValueError("固定した方針の指紋が異なる")
    plan = core.load(POLICY)
    if (plan["scope"] != "development-only-three-rows-recomputed"
            or set(plan["evidence"]) != set(previous.PAIRS)
            or any(core.sha(Path(path)) != sha for path, sha in plan["inputs"].items())):
        raise ValueError("固定した補助証拠か監査方法が異なる")
    return plan["evidence"]


def adopt(shipment, case, votes, rules, guard):
    key = previous.identity(case["row"])
    if key not in rules or case.get("partitions") != []:
        return None
    assets = case["assets"]
    views = assets.get("source_view", {}).get("views", [])
    if len(views) != 2 or sum(p.get("kind") == "plain" for p in views[1].get("images", [])) != 1:
        return None
    if not {"dpi", "display_scale", "crop_rectangle", "target_rectangle"}.issubset(views[1]):
        return None
    paired, coordinates = core.ref.aligned(*votes, case["row"]["box"][2])
    if paired["status"] != "readable" or (paired, coordinates) != (case["answer"], case["coordinates"]):
        return None
    if any("・" in core.ref.MARK.sub("", vote["text"]) for vote in votes):
        return None
    if key == F_SHAPE:
        if coordinates or case["earlier_reason"] != "unverified-small-round":
            return None
        if not guard.unverified_round(paired, case["row"], assets["sha"], coordinates):
            return None
        return previous.release_shape(shipment, case, votes, rules, guard)
    if case["earlier_reason"] != SOURCE_REASON:
        return None
    mark = core.ref.MARK.search(paired["text"])
    if not mark or mark.start() != rules[key]["visual_rank"]:
        return None
    return previous.resolve_white(shipment, case, votes, rules, SOURCE_REASON)


def controls(shipment, cases, votes, rules, guard):
    checks = {}
    for key in (F_SHAPE, WHITE_POINT):
        for scenario in ("wrong-box", "wrong-image", "partitioned", "short-view", "different-votes", "source-unavailable",
                         "stale-answer", "literal-dot", "literal-bullet", "two-marks", "shifted-mark", "wrong-glyph-rank"):
            if scenario in ("shifted-mark", "wrong-glyph-rank") and key == F_SHAPE:
                continue
            case = deepcopy(cases[key])
            a, b = deepcopy(votes[key])
            if scenario == "wrong-box":
                case["row"]["box"][0] += 1
            elif scenario == "wrong-image":
                case["assets"]["sha"]["450_dpi_rgb"] = "different"
            elif scenario == "partitioned":
                case["partitions"] = ["A"]
            elif scenario == "short-view":
                case["assets"]["source_view"]["views"].pop()
            elif scenario == "source-unavailable":
                case["earlier_reason"] = "source-unavailable"
            elif scenario == "stale-answer":
                case["answer"] = {"status": "readable", "text": "F"}
            elif scenario == "different-votes":
                b["text"] += "誤"
            else:
                for vote in (a, b):
                    body = vote["text"]
                    if scenario == "literal-dot":
                        vote["text"] = body + "・"
                    elif scenario == "literal-bullet":
                        vote["text"] = body[:1] + "•" + body[1:]
                    elif scenario == "two-marks":
                        vote["text"] = body + "⟦round:219-219⟧⟦round:219-219⟧"
                    elif scenario == "shifted-mark":
                        vote["text"] = core.ref.MARK.sub("⟦round:219-219⟧", body)
                    elif scenario == "wrong-glyph-rank":
                        vote["text"] = body[:4] + core.ref.MARK.search(body)[0] + core.ref.MARK.sub("", body)[4:]
                case["answer"], case["coordinates"] = core.ref.aligned(a, b, case["row"]["box"][2])
            if adopt(shipment, case, (a, b), rules, guard) is not None:
                raise ValueError(f"補助証拠を保留に戻せない {key}/{scenario}")
            checks[f"{key}/{scenario}"] = "held"
    key = "wp-summary-p0010/29"
    if adopt(shipment, cases[key], votes[key], rules, guard):
        raise ValueError("対象外の点に補助証拠がそろった")
    checks[f"{key}/out-of-scope"] = "held-by-row-identity"
    return checks


def replay(shipment, expected):
    rules = policy(expected)
    old_results = core.load(V64 / "result.json")
    evidence_path = launch.OUT / "reference-evidence.json"
    receipts = shipment.folder / "received.json"
    if old_results["reference_sha256"] != core.sha(evidence_path) or old_results["receipts_sha256"] != core.sha(receipts):
        raise ValueError("保存済みの判定または受領台帳が異なる")
    archived, raw = core.transport.collect(shipment, core.old_sessions())
    if archived != core.load(receipts) or {k: v["received"] for k, v in archived["counts"].items()} != {"gpt": 379, "claude": 379}:
        raise ValueError("379行分の独立した原票が二系統でそろわない")
    guard = core.module("extended_leading_point_guard", HERE.parent / "v23-round-pixel-pilot/run.py")
    reference = core.load(evidence_path)
    index = previous.packet_index(shipment)
    cases, votes, changes = {}, {}, {}
    for key in (*rules, "wp-summary-p0010/29"):
        name, label, mapping, row = index[key]
        if reference[key]["answer"]["status"] != "unreadable":
            raise ValueError("保存した判定ですでに確定している")
        values = tuple(core.ref.decoded(raw[name][role][label], mapping["partitions"]) for role in ("gpt", "claude"))
        answer, positions = core.ref.aligned(*values, row["box"][2])
        case = {"row": row, "partitions": mapping["partitions"], "assets": mapping["image_reference"],
                "answer": answer, "coordinates": positions, "earlier_reason": reference[key]["evidence"],
                "reason": reference[key]["evidence"]}
        cases[key], votes[key] = case, values
        decision = adopt(shipment, case, values, rules, guard)
        if decision:
            reading, proof = decision
            changes[key] = {"answer": reading, "evidence": proof, "domain": previous.PAIRS[key]}
    if set(changes) != set(rules):
        raise ValueError("審査対象二件の画像の二票と証拠を結び付けられない")
    unknown = Counter()
    totals = {"region": Counter(), "image": Counter()}
    for key, (_, _, _, row) in index.items():
        answer = changes.get(key, reference[key])["answer"]
        for domain, target in row["targets"].items():
            if target["known"]:
                status = ("insufficient" if answer["status"] == "unreadable" else
                          "same" if answer["text"] == core.ref.NORMALIZE(target["text"]) else "different")
                totals[domain][status] += 1
            else:
                unknown["insufficient" if answer["status"] == "unreadable" else "reference"] += 1
    if totals != {"region": Counter(same=151, insufficient=7), "image": Counter(same=162, insufficient=18)}:
        raise ValueError("二つの再判定と既存の採点が一致しない")
    return {"scope": "development-only-archived-v64", "verified_raw_rows": len(index), "recomputed_cases": list(cases),
            "archived_only_rows": len(index) - len(cases), "summary": totals, "unknown": unknown,
            "changes": changes, "controls": controls(shipment, cases, votes, rules, guard), "policy_sha256": expected}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("action", choices=("freeze", "replay"))
    parser.add_argument("--sha256")
    args = parser.parse_args()
    launch.configure()
    core.verify_methods()
    archive = launch.OUT / "delivery"
    shipment = core.transport.check(archive, core.sha(archive / "packages.json"))
    if args.action == "freeze":
        core.save_once(POLICY, core.encoded(freeze(shipment)))
        print(core.sha(POLICY), flush=True)
    else:
        report = replay(shipment, args.sha256)
        core.save_once(HERE / "replay-result.json", core.encoded(report))
        print(report["summary"], report["unknown"], len(report["controls"]), flush=True)


if __name__ == "__main__":
    main()
