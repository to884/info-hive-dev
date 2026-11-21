"""v101の確定に残った成分だけを保存字形票と照合する。"""

from importlib.util import module_from_spec, spec_from_file_location
from pathlib import Path


HERE = Path(__file__).resolve().parent
V103 = HERE.parent / "v103-hold-shape-disagreements"
spec = spec_from_file_location("saved_shape_guard", V103 / "run.py")
shape = module_from_spec(spec)
spec.loader.exec_module(shape)
previous = shape.previous
core = previous.core


def retained_conflicts(result, conflicts):
    if result["classification"] == ["unresolved"] or result["answer"]["status"] != "readable":
        return set()
    trace = result["trace"]
    if trace is None:
        raise ValueError("確定した転記の成分番号がそろわない")
    retained = {ident for _, _, ident in trace}
    if any(type(ident) is not int for ident in retained | conflicts.keys()):
        raise ValueError("成分番号は整数で照合する")
    return conflicts.keys() & retained


def main():
    saved, plan = shape.checked_inputs()
    role_source, baseline, replay, original, old_lock, attachments = previous.prior_data()
    prior_shapes = core.load(V103 / "comparison.json")
    if prior_shapes["prior_comparison_sha256"] != core.sha(shape.V102 / "comparison.json"):
        raise ValueError("前回の字形保留の集計と元の票が一致しない")
    archived = core.load(previous.previous.archive / "display/selection.json")["selected"]
    rows = {}
    for row, case in saved["rows"].items():
        ids = plan["mapping"][row]["ids"]
        name = row + "/new"
        kept = {m: replay["cases"][name]["votes"][m]["kept"] for m in previous.MODELS}
        cues = {}
        for model in previous.MODELS:
            parsed, status = previous.read_tags(case["received"][model]["answer"], ids)
            if status != "valid" or parsed != {int(i): tuple(v) for i, v in case["cues"][model].items()}:
                raise ValueError(f"保存した字形票と合わない: {row} {model}")
            cues[model] = parsed
        roles = {int(i): label for i, label in role_source["cases"][row]["agreed_roles"].items()}
        geometry = old_lock["mapping"][row]
        box = archived[plan["mapping"][row]["entry"]]["box"]
        before = previous.evaluate(row, roles, kept, original["cases"][name], geometry, box)
        if (core.encoded(before) != core.encoded(case["scores_before"]) or
                any(before[rule]["classification"] != baseline["rows"][row][rule]
                    for rule in previous.RULES)):
            raise ValueError(f"v101の確定を再現できない: {row}")
        conflicts = shape.mismatches(cues, kept)
        if core.encoded(conflicts) != core.encoded(prior_shapes["rows"][row]["conflicts"]):
            raise ValueError(f"前回の字形照合と合わない: {row}")
        after, used = {}, {}
        for rule in previous.RULES:
            used[rule] = sorted(retained_conflicts(before[rule], conflicts))
            after[rule] = before[rule]
            if used[rule]:
                adjusted = {**roles, **dict.fromkeys(used[rule], "U")}
                after[rule] = previous.evaluate(
                    row, adjusted, kept, original["cases"][name], geometry, box)[rule]
                if after[rule]["classification"] != ["unresolved"]:
                    raise ValueError(f"最終転記に残った不一致を保留できない: {row} {rule}")
        rows[row] = {"before": before, "after": after, "all_shape_conflicts": conflicts,
                     "held_shape_components": used,
                     "v103": {rule: prior_shapes["rows"][row]["after"][rule]["classification"]
                              for rule in previous.RULES}}
    compared_v103 = {row: dict(case) for row, case in baseline["rows"].items()}
    for row, case in rows.items():
        compared_v103[row].update(case["v103"])
    result = {"rows": rows, "counts": previous.counts(rows, baseline["rows"]),
              "relative_to_v103": previous.counts(rows, compared_v103),
              "saved_shape_votes": 10, "new_image_reads": 0, "formal_attachments_verified": attachments}
    output = HERE / "comparison.json"
    data = core.encoded(result)
    if output.exists():
        if output.read_bytes() != data:
            raise ValueError("再集計が保存済みの結果と一致しない")
    else:
        core.save_once(output, data)
    print(result["counts"], flush=True)


if __name__ == "__main__":
    main()

