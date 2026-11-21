"""保存した字形二票と転記の不一致を未決定にする。"""

from importlib.util import module_from_spec, spec_from_file_location
from pathlib import Path


HERE = Path(__file__).resolve().parent
V102 = HERE.parent / "v102-shape-position-separator-recheck"
spec = spec_from_file_location("saved_shape_votes", V102 / "run.py")
previous = module_from_spec(spec)
spec.loader.exec_module(previous)
core = previous.core

SHAPE_MARKS = {"C": {","}, "D": {"."}, "L": {"-", "/"}}


def mismatches(cues, kept):
    conflicts = {}
    for model, candidates in kept.items():
        for _, mark, ident in candidates:
            first, second = (cues[reader][ident][0] for reader in previous.MODELS)
            if first == second and first in SHAPE_MARKS and mark not in SHAPE_MARKS[first]:
                conflicts.setdefault(ident, {"shape": first, "saved": {}})["saved"][model] = mark
    return conflicts


def checked_inputs():
    integrity = core.load(V102 / "integrity.json")
    plan_path = V102 / "lock.json"
    result_path = V102 / "comparison.json"
    previous.hold.verify(plan_path, integrity["lock_sha256"])
    previous.hold.verify(result_path, integrity["comparison_sha256"])
    plan = core.load(plan_path)
    for file, digest in plan["files"].items():
        previous.hold.verify(Path(file), digest)
    saved = core.load(result_path)
    if (set(saved["rows"]) != set(previous.TARGETS)
            or saved["new_reads"] != 10 or saved["lock_sha256"] != integrity["lock_sha256"]):
        raise ValueError("前回の5枠の固定と役割票が一致しない")
    return saved, plan


def main():
    saved, plan = checked_inputs()
    _, old_baseline, replay, original, old_lock, attachments = previous.prior_data()
    archived = core.load(previous.previous.archive / "display/selection.json")["selected"]
    base = old_baseline["rows"]
    before_for_counts = {row: dict(case) for row, case in base.items()}
    rows = {}
    for row, case in saved["rows"].items():
        ids = plan["mapping"][row]["ids"]
        name = row + "/new"
        kept = {m: replay["cases"][name]["votes"][m]["kept"] for m in previous.MODELS}
        cues = {}
        for model in previous.MODELS:
            parsed, status = previous.read_tags(case["received"][model]["answer"], ids)
            expected = {int(i): tuple(v) for i, v in case["cues"][model].items()}
            if status != "valid" or case["format"][model] != status or parsed != expected:
                raise ValueError(f"保存した字形票の記録が一致しない: {row} {model}")
            cues[model] = parsed
        roles = previous.agreed_roles(cues, ids)
        if roles != {int(key): value for key, value in case["roles_after"].items()}:
            raise ValueError(f"前回の役割の二票一致と合わない: {row}")
        geometry = old_lock["mapping"][row]
        box = archived[plan["mapping"][row]["entry"]]["box"]
        recorded = previous.evaluate(row, roles, kept, original["cases"][name], geometry, box)
        if core.encoded(recorded) != core.encoded(case["after"]):
            raise ValueError(f"前回の採点と合わない: {row}")
        conflicts = mismatches(cues, kept)
        if not conflicts.keys() <= roles.keys():
            raise ValueError(f"枠内の既存成分だけを保留できる: {row}")
        adjusted = {**roles, **dict.fromkeys(conflicts, "U")}
        after = previous.evaluate(row, adjusted, kept, original["cases"][name], geometry, box)
        if conflicts and any(entry["classification"] != ["unresolved"] for entry in after.values()):
            raise ValueError(f"字形の食い違いがある枠が保留されていない: {row}")
        before_for_counts[row].update({
            rule: recorded[rule]["classification"] for rule in previous.RULES})
        rows[row] = {"before": recorded, "after": after, "conflicts": conflicts,
                     "roles_before": roles, "roles_after": adjusted}
    if previous.counts({
        row: {"after": item["after"]} for row, item in saved["rows"].items()
    }, base) != saved["counts"]:
        raise ValueError("前回の集計が元の採点と合わない")
    result = {"rows": rows, "counts": previous.counts(rows, before_for_counts),
              "saved_shape_votes": 10, "new_image_reads": 0,
              "formal_attachments_verified": attachments,
              "prior_comparison_sha256": core.sha(V102 / "comparison.json")}
    data = core.encoded(result)
    output = HERE / "comparison.json"
    if output.exists():
        if output.read_bytes() != data:
            raise ValueError("保存済みの再集計と一致しない")
    else:
        core.save_once(output, data)
    print(result["counts"], flush=True)


if __name__ == "__main__":
    main()

