"""同一タブの連続描画と、描画回数を減らす試作の標本を集計する。"""

import argparse
import json
from pathlib import Path
from runpy import run_path


def read_json(path):
    return json.loads(path.read_text(encoding="utf-8-sig"))


def checked_case(case, directory, summarize_checkpoint):
    samples = read_json(directory / f'{case["id"]}-memory.json')
    assert len(samples) == case["memory"]["samples"]
    assert all(s["run_id"] == case["id"] and s["root_pid"] == case["pid"] for s in samples)
    indexed = {sample["sequence"]: sample for sample in samples}
    assert len(indexed) == len(samples)
    points = {}
    for checkpoint in case["checkpoints"]:
        assert checkpoint["sample"] == indexed[checkpoint["sample"]["sequence"]]
        points[checkpoint["phase"]] = summarize_checkpoint(checkpoint, case)
    assert len(points) == len(case["checkpoints"])
    return points, samples


def brief(point):
    web = point["process_groups"].get("WebKitWebProcess", {})
    return {
        "private_bytes": point["total_private_bytes"],
        "working_set_sum_bytes": point["total_working_set_bytes"],
        "web_private_bytes": web.get("private_bytes", 0),
        "web_working_set_bytes": web.get("working_set_bytes", 0),
        "web_pids": sorted(web.get("pids", [])),
    }


def summarize_rounds(case, points, expected_rounds, stopped):
    rounds = []
    planned = case.get("rounds", [])
    assert (len(planned) <= expected_rounds) if stopped else (len(planned) == expected_rounds)
    for number, round_data in enumerate(planned, 1):
        assert round_data["number"] == number
        retained_phase = f"round-{number}-retained"
        returned_phase = f"round-{number}-returned"
        revisit = case["condition"].endswith("-revisit")
        if stopped and (retained_phase not in points or (revisit and returned_phase not in points)):
            assert number == len(planned)
            break
        row = {"number": number, "document_id": round_data["documentId"]}
        for color in ("light", "dark"):
            drawing = round_data[color]
            assert case["count"] == drawing["images"] == drawing["successes"]
            assert drawing["peakFrames"] == 1 and drawing["active"] == 0
            assert drawing["created"] == drawing["disposed"]
            row[f"{color}_ms"] = drawing["decodeMs"]
        displayed = points[f"round-{number}-displayed"]
        retained = points[retained_phase]
        assert displayed["outer"]["images"] == case["count"]
        row["displayed"] = brief(displayed)
        row["retained"] = brief(retained)
        if revisit:
            assert retained["outer"] is None
            row["returned_same_document"] = round_data["returnedSameDocument"]
            row["returned"] = brief(points[returned_phase])
        else:
            assert retained["outer"]["images"] == case["count"]
        rounds.append(row)
    return rounds


def summarize_policy(case, points, samples, stopped):
    actions = []
    for action in case.get("policyActions", []):
        assert action["rendered"] + action["hits"] == action["targets"]
        phase = action["phase"]
        if f"{phase}-done" not in points:
            assert stopped
            break
        samples_during_action = [s for s in samples if s["phase"] == phase and s["stable"] and not s["missing_children"]]
        # 短いキャッシュヒットは監視周期より短い。終点は別に残し、区間ピークは欠測とする。
        actions.append({
            **action,
            "running_samples": len(samples_during_action),
            "observed_running_peak_private_bytes": max((s["private_bytes"] for s in samples_during_action), default=None),
            "observed_running_peak_working_set_bytes": max((s["working_set_sum_bytes"] for s in samples_during_action), default=None),
            "after": brief(points[f"{phase}-done"]),
            **({"retained": brief(points[f"{phase}-retained"])} if f"{phase}-retained" in points else {}),
        })
    return actions


def summarize_static_images(case, points, result, stopped):
    rounds = []
    planned = case.get("rounds", [])
    assert len(planned) <= result["rounds"]
    if not stopped:
        assert len(planned) == result["rounds"]
    for number, recorded in enumerate(planned, 1):
        retained_phase = f"round-{number}-retained"
        if stopped and retained_phase not in points:
            assert number == len(planned)
            break
        assert recorded["number"] == number
        assert recorded["documentId"] == planned[0]["documentId"]
        row = {"number": number}
        for color, phase in (("light", f"round-{number}-light-decoded"), ("dark", f"round-{number}-displayed")):
            draw = recorded[color]
            assert draw["documentId"] == recorded["documentId"]
            assert draw["images"] == case["count"] and 0 <= draw["firstDecodeMs"] <= draw["decodeMs"]
            outer = points[phase]["outer"]
            assert outer["images"] == case["count"] and outer["frames"] == 0
            row[color] = {"first_decode_ms": draw["firstDecodeMs"], "all_decode_ms": draw["decodeMs"]}
        assert points[retained_phase]["outer"]["images"] == case["count"]
        row["retained"] = brief(points[retained_phase])
        rounds.append(row)
    return rounds


def summarize(path):
    result = read_json(path)
    assert result["design"] in ("repeat-tab", "figure-policy", "static-image")
    assert result["inputsUnchanged"] and result["requestsGC"] is False
    external_stop = path.with_name("resource-stop.json")
    external_stop = read_json(external_stop) if external_stop.exists() else None
    if external_stop is None:
        assert len(result["cases"]) == result["repeats"] * len(result["counts"]) * len(result["browsers"]) * len(result["conditions"])
    validate = run_path(str(Path(__file__).with_name("analyze-retention.py")))["summarize_checkpoint"]
    rows = []
    for case in result["cases"]:
        stop = case.get("resourceStop")
        if external_stop and external_stop["id"] == case["id"]:
            stop = external_stop
            assert stop["pid"] == case["pid"]
        assert (case["ok"] or stop) and case["cleanupMethod"] == "owned-browser-kill"
        points, samples = checked_case(case, path.parent, validate)
        peak_samples = [sample for sample in samples if sample["stable"] and not sample["missing_children"]]
        if result["design"] == "static-image":
            peak_samples = [sample for sample in peak_samples if sample["phase"].startswith("round-")]
        row = {
            "condition": case["condition"],
            "browser": case["browser"],
            "version": case["version"],
            "id": case["id"],
            "empty": brief(points["empty"]) if "empty" in points else None,
            "context_closed": brief(points["context_closed"]) if "context_closed" in points else None,
            "resource_stop": stop,
            "observed_peak_private_bytes": max((s["private_bytes"] for s in peak_samples), default=None),
            "observed_peak_working_set_bytes": max((s["working_set_sum_bytes"] for s in peak_samples), default=None),
        }
        if result["design"] == "repeat-tab":
            row["rounds"] = summarize_rounds(case, points, result["rounds"], bool(stop))
        elif result["design"] == "static-image":
            row["rounds"] = summarize_static_images(case, points, result, bool(stop))
            row["repeat"] = case["repeat"]
            row["peak_sample_count"] = len(peak_samples)
        else:
            row["actions"] = summarize_policy(case, points, samples, bool(stop))
            if "full-scroll" in points:
                row["full_scroll"] = brief(points["full-scroll"])
        rows.append(row)
    summary = {"design": result["design"], "counts": result["counts"], "idle_ms": result["idleMs"], "cases": rows}
    if result["design"] == "static-image":
        count, = result["counts"]
        images = result["staticImage"]["images"]
        summary["asset_bytes"] = {
            kind: {color: sum(row[kind]["bytes"] for row in colored[:count]) for color, colored in images.items()}
            for kind in ("svg", "png")
        }
    return summary


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("results", type=Path)
    args = parser.parse_args()
    print(json.dumps(summarize(args.results), ensure_ascii=False, indent=2))
