"""審査済みの二つの局所的な証拠を、監査の画像二票と結び付ける。"""

import argparse
from collections import Counter
from copy import deepcopy
from pathlib import Path
import sys

HERE = Path(__file__).resolve().parent
STAGES = HERE.parent
V64 = STAGES / "v64-reference-audit"
sys.path.insert(0, str(V64))
import launch

core = launch.core
POLICY = HERE / "evidence-policy.json"
F_SHAPE = "defense-p0500/84"
WHITE_POINT = "defense-p0438/13"
PAIRS = {F_SHAPE: "region", WHITE_POINT: "image"}
APPROVED = {
    F_SHAPE: ("v84-matched-round-shape-pilot", "review-coverage.json"),
    WHITE_POINT: ("v83-direct-white-point-proof", "text-underlay-control.json"),
}


def identity(row):
    return f"{row['key']}/{row['line_index']}"


def file_geometry(shipment, assets):
    view = assets["source_view"]["views"][1]
    (name,) = (x["image"] for x in view["images"] if x["kind"] == "plain")
    path = shipment.folder / "source-assets" / name
    return path, {key: view[key] for key in ("dpi", "display_scale", "crop_rectangle", "target_rectangle")}


def image_binding(shipment, row, assets):
    path, geometry = file_geometry(shipment, assets)
    return {
        "row": identity(row), "box": row["box"], "axis": row["allocation_axis"],
        "geometry": geometry, "input_sha": assets["sha"],
        "crop_png_sha256": shipment.document["source_assets"][path.name],
    }


def read_inputs(files):
    return {str(path): core.sha(path) for path in files}


def packet_index(shipment):
    archive = core.load(launch.OUT / "selection.json")["selected"]
    rows = {}
    for name, packet in shipment.document["packs"].items():
        (label, link), = packet["mapping"].items()
        row = archive[link["entry"]]
        rows[identity(row)] = (name, label, link, row)
    if len(rows) != len(archive):
        raise ValueError("監査の各枠と配布が一対一ではない")
    return rows


def snapshot(shipment):
    catalog = launch.previous.packets.old.lookup()[1]
    index = packet_index(shipment)
    policy = {}
    files = [Path(__file__), HERE / "protocol.md", V64 / "result.json", V64 / "population-lock.json",
             shipment.folder / "packages.json", launch.OUT / "selection.json"]
    for key, (folder, extension) in APPROVED.items():
        proof_dir = STAGES / folder
        proof = proof_dir / "result.json"
        review = proof_dir / "review-opus.md"
        followup = proof_dir / extension
        if "Final Result: APPROVED" not in review.read_text(encoding="utf-8"):
            raise ValueError("対象の固定証拠を承認したレビューがない")
        _, _, binding, row = index[key]
        if binding["partitions"]:
            raise ValueError("証拠の対象は区画に分かれていない固定枠に限る")
        assets = binding["image_reference"]
        source, document_hash, _ = catalog[row["key"]]
        low = core.CORPUS / "probe-v4/png" / (row["key"] + ".png")
        high, _ = file_geometry(shipment, assets)
        fixed = image_binding(shipment, row, assets)
        if (core.sha(low) != assets["sha"]["150_dpi"] or core.sha(high) != fixed["crop_png_sha256"]
                or core.sha(core.CORPUS / source) != document_hash or document_hash != assets["sha"]["pdf_sha256"]):
            raise ValueError("二つの解像度の画像と原本が固定された証拠に対応しない")
        fixed["verified_source"] = {"pdf": source, "sha256": document_hash, "page": catalog[row["key"]][2]}
        detail, recheck = core.load(proof), core.load(followup)
        if key == F_SHAPE:
            assessed, = (r for r in detail["rows"] if f"{r['page']}/{r['line_index']}" == key)
            case, = assessed["cases"]
            if not (case["non_round"] and case["isolated_450"] and recheck["formal_pair_equal"]):
                raise ValueError("先頭の成分について審査済みの証拠が足りない")
            confirms, = (r for r in recheck["case_records"] if f"{r['page']}/{r['line_index']}" == key)
            mark, = confirms["marks"]
            if not mark["in_original_candidates"] or mark["box"] != case["coarse"]:
                raise ValueError("丸として保留した固定150 DPIの成分に対応しない")
            fixed["component_150"] = case["coarse"]
        else:
            command = detail["command"]
            if (f"{detail['page']}/{detail['line_index']}" != key or command["codepoint"] != "30FB"
                    or command["cid"] != 638 or detail["checks"]["150"]["outside_changed"]
                    or detail["checks"]["450"]["outside_max_channel_delta"] > 1
                    or not recheck["same_context_when_all_text_is_hidden"]):
                raise ValueError("白い小点の描画と背景の直接証明が足りない")
            fixed["component_150"] = detail["checks"]["150"]["area"]
            fixed["source_command"] = command
        files.extend((proof, review, followup, low, high))
        policy[key] = fixed
    return {"scope": "preflight-only-two-reviewed-regions", "evidence": policy, "inputs": read_inputs(files)}


def load_policy(expected):
    if core.sha(POLICY) != expected:
        raise ValueError("事前に固定した補助証拠または照合手順が異なる")
    record = core.load(POLICY)
    if (record["scope"] != "preflight-only-two-reviewed-regions"
            or set(record["evidence"]) != set(APPROVED)
            or any(core.sha(Path(name)) != sha for name, sha in record["inputs"].items())):
        raise ValueError("固定済みの補助証拠の来歴が異なる")
    return record["evidence"]


def exact_evidence(shipment, row, assets, evidence):
    fixed = evidence.get(identity(row))
    if not fixed:
        return None
    observed = image_binding(shipment, row, assets)
    if any(fixed[key] != value for key, value in observed.items()):
        return None
    high, _ = file_geometry(shipment, assets)
    low = core.CORPUS / "probe-v4/png" / (row["key"] + ".png")
    source = fixed["verified_source"]
    if (core.sha(high) != fixed["crop_png_sha256"] or core.sha(low) != fixed["input_sha"]["150_dpi"]
            or core.sha(core.CORPUS / source["pdf"]) != source["sha256"]):
        raise ValueError("補助証拠に結び付けた画像か原本の実体が異なる")
    return fixed


def release_shape(shipment, case, votes, evidence, point_guard):
    row, assets = case["row"], case["assets"]
    if identity(row) != F_SHAPE or case["reason"] != "unverified-small-round":
        return None
    gpt, claude = votes
    if (gpt != claude or gpt["status"] != "readable" or not gpt["text"].startswith("F")
            or core.ref.MARK.search(gpt["text"]) or "⟦" in gpt["text"] or "⟧" in gpt["text"]):
        return None
    fixed = exact_evidence(shipment, row, assets, evidence)
    if not fixed:
        return None
    x, y, w, h = row["box"]
    gray = point_guard.reference.png_checked(row, assets["sha"])
    boxes = [list(box) for box in point_guard.reference.small_round(gray, (x, y, min(w, 24), h))
             if 9 <= max(box[2]-box[0], box[3]-box[1]) <= 10
             and abs((box[0]+box[2])/2-x) <= 12 and not point_guard.closed_hole(gray, box)]
    if boxes != [fixed["component_150"]]:
        return None
    return gpt, {"route": "matched-fixed-leading-stroke", "component_150": boxes[0]}


def resolve_white(shipment, case, votes, evidence, earlier_reason):
    row, assets = case["row"], case["assets"]
    if identity(row) != WHITE_POINT or earlier_reason not in ("source-location-not-proven", "source-unavailable"):
        return None
    if any(v["status"] != "readable" for v in votes):
        return None
    for vote in votes:
        marks = list(core.ref.MARK.finditer(vote["text"]))
        outside = core.ref.MARK.sub("", vote["text"])
        if (len(marks) != 1 or marks[0][1] != "round" or "⟦" in outside or "⟧" in outside
                or core.ref.v10.LITERAL_POINT.search(outside)):
            return None
    paired, coordinates = core.ref.aligned(*votes, row["box"][2])
    if paired != case["answer"] or coordinates != case["coordinates"] or len(coordinates) != 1:
        return None
    fixed = exact_evidence(shipment, row, assets, evidence)
    if not fixed:
        return None
    x, _, _, _ = row["box"]
    l, _, r, _ = fixed["component_150"]
    center = (l+r)/2-x
    a, b, c, d = coordinates[0]
    if a != b or c != d or max(abs(pos-center) for pos in (a, c)) > 3:
        return None
    body = core.ref.MARK.sub(chr(int(fixed["source_command"]["codepoint"], 16)), paired["text"])
    return {"status": "readable", "text": core.ref.NORMALIZE(body)}, {
        "route": "matched-fixed-white-point-command", "component_150": fixed["component_150"],
        "coordinates": coordinates, "source_command": fixed["source_command"],
    }


def verify_controls(shipment, cases, votes, original, evidence, guard):
    gpt, claude = votes[F_SHAPE]
    targets = {
        "shape-altered-reading": (F_SHAPE, deepcopy(cases[F_SHAPE]), [gpt, {**claude, "text": claude["text"][1:]}]),
        "shape-altered-first-letter": (F_SHAPE, deepcopy(cases[F_SHAPE]), [
            {**v, "text": "E" + v["text"][1:]} for v in votes[F_SHAPE]]),
        "shape-different-frame": (F_SHAPE, deepcopy(cases[F_SHAPE]), votes[F_SHAPE]),
        "white-different-image": (WHITE_POINT, deepcopy(cases[WHITE_POINT]), votes[WHITE_POINT]),
        "white-other-position": (WHITE_POINT, deepcopy(cases[WHITE_POINT]), [
            {**v, "text": core.ref.MARK.sub("⟦round:219-219⟧", v["text"])} for v in votes[WHITE_POINT]]),
        "white-added-dot": (WHITE_POINT, deepcopy(cases[WHITE_POINT]), [
            {**v, "text": v["text"] + "⟦round:260-260⟧"} for v in votes[WHITE_POINT]]),
        "white-other-mark": (WHITE_POINT, deepcopy(cases[WHITE_POINT]), [
            {**v, "text": core.ref.MARK.sub("⟦trail:214-216⟧", v["text"])} for v in votes[WHITE_POINT]]),
        "embedded-dot": ("wp-summary-p0010/29", cases["wp-summary-p0010/29"], votes["wp-summary-p0010/29"]),
    }
    targets["white-different-image"][1]["assets"]["sha"]["450_dpi_rgb"] = "changed"
    targets["shape-different-frame"][1]["row"]["box"][0] += 1
    checks = {}
    for name, (key, case, readings) in targets.items():
        if key == F_SHAPE:
            found = release_shape(shipment, case, readings, evidence, guard)
        else:
            if name in ("white-other-position", "white-added-dot", "white-other-mark"):
                case["answer"], case["coordinates"] = core.ref.aligned(*readings, case["row"]["box"][2])
            found = resolve_white(shipment, case, readings, evidence, original[key]["evidence"])
        if found is not None:
            raise ValueError(f"補助証拠を認めない対照で確定した {name}")
        checks[name] = "held"
    return checks


def replay(shipment, expected):
    evidence = load_policy(expected)
    result = core.load(V64 / "result.json")
    old = launch.OUT / "reference-evidence.json"
    received = shipment.folder / "received.json"
    if result["reference_sha256"] != core.sha(old) or result["receipts_sha256"] != core.sha(received):
        raise ValueError("保存済みv64の判定か受領台帳が異なる")
    archived, raw = core.transport.collect(shipment, core.old_sessions())
    if archived != core.load(received) or {k: v["received"] for k,v in archived["counts"].items()} != {"gpt":379, "claude":379}:
        raise ValueError("各379行の独立した二票が揃わない")
    guard = core.module("scoped_leading_point", STAGES / "v23-round-pixel-pilot/run.py")
    old_reference = core.load(old)
    index = packet_index(shipment)
    cases, votes, answers, changes = {}, {}, dict(old_reference), {}
    for key in (*PAIRS, "wp-summary-p0010/29"):
        packet, label, mapping, row = index[key]
        values = tuple(core.ref.decoded(raw[packet][role][label], mapping["partitions"]) for role in ("gpt","claude"))
        paired, coordinates = core.ref.aligned(*values, row["box"][2])
        reason = "unverified-small-round" if guard.unverified_round(
            paired, row, mapping["image_reference"]["sha"], coordinates) else "plain-unresolved"
        case = {"row": row, "answer": paired, "coordinates": coordinates,
                "assets": mapping["image_reference"], "reason": reason}
        cases[key], votes[key] = case, values
        earlier = old_reference[key]
        if earlier["answer"]["status"] != "unreadable":
            raise ValueError("既に正式監査で確定した行には補助証拠を追加しない")
        proof = (release_shape(shipment, case, values, evidence, guard) if key == F_SHAPE
                 else resolve_white(shipment, case, values, evidence, earlier["evidence"]))
        if proof:
            answer, detail = proof
            answers[key] = {"answer": answer, "evidence": detail}
            changes[key] = {**answers[key], "domain": PAIRS[key], "earlier_reason": earlier["evidence"]}
    if set(changes) != set(PAIRS):
        raise ValueError("保存済みの二票と二つの審査済み証拠を結び付けられない")
    checks = verify_controls(shipment, cases, votes, old_reference, evidence, guard)
    totals = {"region": Counter(), "image": Counter()}
    for key, (_, _, _, row) in index.items():
        for domain, target in row["targets"].items():
            if target["known"]:
                answer = answers[key]["answer"]
                state = ("insufficient" if answer["status"] == "unreadable" else
                         "same" if answer["text"] == core.ref.NORMALIZE(target["text"]) else "different")
                totals[domain][state] += 1
    if totals != {"region": Counter(same=151, insufficient=7), "image": Counter(same=162, insufficient=18)}:
        raise ValueError("二つの枠以外の判定が変わったか、追加証拠が既存正解と一致しない")
    return {"scope": "development-only-archived-v64", "rows": len(index), "summary": totals,
            "changes": changes, "controls": checks, "policy_sha256": expected,
            "inputs": read_inputs((V64/"result.json", received, old, shipment.folder/"packages.json"))}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("action", choices=("freeze", "replay"))
    parser.add_argument("--sha256")
    args = parser.parse_args()
    launch.configure()
    core.verify_methods()
    archives = launch.OUT / "delivery"
    shipment = core.transport.check(archives, core.sha(archives / "packages.json"))
    if args.action == "freeze":
        core.save_once(POLICY, core.encoded(snapshot(shipment)))
        print(core.sha(POLICY), flush=True)
    else:
        summary = replay(shipment, args.sha256)
        core.save_once(HERE / "replay-result.json", core.encoded(summary))
        print(summary["summary"], summary["controls"], flush=True)


if __name__ == "__main__":
    main()
