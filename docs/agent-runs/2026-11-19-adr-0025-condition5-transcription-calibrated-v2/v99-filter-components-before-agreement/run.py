"""v97の64票で、同じ数字間の複数候補を枠で絞ってから照合する。"""

import argparse
from collections import defaultdict
from importlib.util import module_from_spec, spec_from_file_location
from pathlib import Path
import re

HERE = Path(__file__).resolve().parent
V97 = HERE.parent / "v97-black-punctuation-lookalikes"
V98 = HERE.parent / "v98-checked-component-annotation"
spec = spec_from_file_location("validated_saved_votes", V98 / "run.py")
saved = module_from_spec(spec)
spec.loader.exec_module(saved)
trial = saved.test
core = trial.core
measure = trial.measure
TUPLE = trial.prior.TUPLE


def candidates(vote, ink, frame_left, width):
    if vote["status"] != "readable":
        return None
    digits, *terms = vote["text"].split("|")
    if not re.fullmatch(r"[0-9]+", digits):
        return None
    by_id = {item["id"]: item for item in ink}
    seen = set()
    previous_x, previous_gap = -1, 0
    choices = []
    for term in terms:
        tag = TUPLE.fullmatch(term)
        if not tag:
            return None
        gap, ident = int(tag[1]), int(tag[2])
        item = by_id.get(ident)
        if item is None or ident in seen or not previous_gap <= gap < len(digits) or gap == 0:
            return None
        x = (item["bounds"][0] + item["bounds"][2]) / 2 - frame_left
        if not previous_x < x < width or x <= 0:
            return None
        previous_x, previous_gap = x, gap
        seen.add(ident)
        inside = item["cross_axis_center_inside"] and item["axis_overlap"] * 2 >= item["axis_length"]
        choices.append((gap, measure.SYMBOL[tag[3]], ident, inside))
    return digits, choices


def after_filter(vote, link, frame_left, width):
    parsed = candidates(vote, link["ink"], frame_left, width)
    if parsed is None:
        return core.ref.UNKNOWN, None, None
    digits, choices = parsed
    by_gap = defaultdict(list)
    for gap, glyph, ident, inside in choices:
        if inside:
            by_gap[gap].append((glyph, ident))
    if any(len(interval) > 1 for interval in by_gap.values()):
        return core.ref.UNKNOWN, None, None
    adopted = {gap: interval[0] for gap, interval in by_gap.items()}
    trace = [(gap, glyph, ident) for gap, (glyph, ident) in adopted.items()]
    structure = digits, adopted
    return measure.transcribe(structure, link["ink"]), trace, structure


def test_cases():
    def stroke(ident, center, inside, overlap=3):
        return {"id": ident, "bounds": [center - 1, 10, center + 1, 13],
                "cross_axis_center_inside": inside, "axis_overlap": overlap, "axis_length": 3}

    def run(text, *ink):
        return after_filter({"status": "readable", "text": text}, {"ink": ink}, 0, 60)

    inside, outside = stroke(1, 17, True), stroke(2, 21, False)
    same_gap = "12345|2:1:C|2:2:D"
    answer, trace, picked = run(same_gap, inside, outside)
    if answer["text"] != "12,345" or trace != [(2, ",", 1)]:
        raise ValueError("枠外の候補だけを除けない")
    if run("12345|2:1:C", inside, outside)[2] != picked:
        raise ValueError("枠外候補の有無で枠内候補の一致が変わった")
    if run(same_gap, inside, stroke(2, 21, True))[0] != core.ref.UNKNOWN:
        raise ValueError("同じ数字間に複数の枠内候補が残った")
    if run(same_gap, stroke(1, 17, False), outside)[1] != []:
        raise ValueError("枠外候補だけなのに記号を採用した")
    if run("12345|2:1:C|4:2:D", inside, stroke(2, 21, True))[0]["text"] != "12,34.5":
        raise ValueError("別の数字間に一つずつある候補を採用できない")
    if run("12345|2:1:C|2:1:D", inside)[0] != core.ref.UNKNOWN:
        raise ValueError("同じ成分の重複指定を受け付けた")
    if run("12345|2:3:C", inside)[0] != core.ref.UNKNOWN:
        raise ValueError("画像にない成分番号を受け付けた")
    if run("12345|2:1:C", stroke(1, 17, True, overlap=1))[1] != []:
        raise ValueError("横方向の重なりの条件を適用していない")


def measure_transitions(initial, updated, plan):
    rows = core.load(trial.pilot.OUT / "display/selection.json")["selected"]
    output = {}
    for case, newer in updated["cases"].items():
        earlier = initial["cases"][case]
        for field in ("votes", "session_ids", "target", "category", "component_ids"):
            if earlier[field] != newer[field]:
                raise ValueError(f"{case}: 保存票または照合の条件が変わった")
        if case.endswith("/old"):
            if earlier != newer:
                raise ValueError(f"{case}: 旧の集計が変わった")
            continue
        link = plan["mapping"][case.split("/")[0]]
        left, _, width, _ = rows[link["entry"]]["box"]
        detail = {}
        for model, vote in newer["votes"].items():
            parsed = candidates(vote, link["ink"], left, width)
            if parsed is None:
                detail[model] = {"status": "invalid-or-unreadable"}
            else:
                _, choices = parsed
                counts = defaultdict(int)
                for gap, _, _, inside in choices:
                    counts[gap] += inside
                detail[model] = {"status": "multiple-inside" if any(n > 1 for n in counts.values()) else "resolved-after-filter",
                                 "kept": [c[:3] for c in choices if c[3]], "outside": [c[:3] for c in choices if not c[3]]}
        output[case] = {"group": newer["category"], "previous_classification": earlier["classification"],
                        "updated_classification": newer["classification"], "previous_source": earlier["source"],
                        "updated_source": newer["source"], "votes": detail}
    return output


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--codex", required=True, type=Path)
    parser.add_argument("--claude", required=True, type=Path)
    args = parser.parse_args()
    trial.launch.configure()
    test_cases()
    args.sha256 = core.sha(V97 / "lock.json")
    baseline_path = V98 / "comparison.json"
    lock = core.load(V98 / "recheck.json")
    if lock["original_lock_sha256"] != args.sha256 or lock["recheck_comparison_sha256"] != core.sha(baseline_path):
        raise ValueError("検証済みの保存票と集計が一致しない")
    baseline = core.load(baseline_path)
    draft = core.load(trial.pilot.LOCK)
    trial.trace_old = saved.trace_checked
    trial.trace_new = after_filter
    trial.HERE = HERE
    trial.score(args)
    updated = core.load(HERE / "comparison.json")
    if baseline["sessions"] != 64 or updated["sessions"] != 64:
        raise ValueError("同じ64原票が揃わない")
    cases = measure_transitions(baseline, updated, draft)
    core.save_once(HERE / "replay-result.json", core.encoded({
        "scope": "development-only-saved-v97-votes",
        "lock_sha256": args.sha256,
        "baseline_sha256": core.sha(baseline_path),
        "updated_sha256": core.sha(HERE / "comparison.json"),
        "test_cases": 8,
        "sessions": updated["sessions"],
        "baseline_counts": baseline["counts"],
        "updated_counts": updated["counts"],
        "baseline_sources": baseline["adopted_components"],
        "updated_sources": updated["adopted_components"],
        "cases": cases,
    }))


if __name__ == "__main__":
    main()
