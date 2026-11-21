"""正式抽出の前に、開発行と固定画像で配布・許可済みの符号を確認する。"""

from pathlib import Path
from tempfile import TemporaryDirectory

import launch

core, audit, render = launch.core, launch.audit, launch.render
pilot = core.CORPUS / "reference-v62-combined-reading-pilot/display"


def packets(method):
    labels = launch.candidate()
    rows = core.load(pilot / "selection.json")["selected"]
    extreme, = [r for r in core.load(labels / "public.json")
                if r["allocation_axis"] == "x" and r["box"][2:] == [1726, 34]]
    vertical = [r for r in core.load(labels / "public.json") if r["allocation_axis"] == "y"]
    extremes = (extreme, max(vertical, key=lambda r: r["box"][3]), max(vertical, key=lambda r: r["box"][2]))
    used = {(r["key"], r["line_index"]): r for r in (*rows, *extremes)}
    with TemporaryDirectory(prefix="adr0025-v64-develop-", dir=core.CORPUS.resolve()) as directory:
        target = Path(directory).resolve()
        if target.parent != core.CORPUS.resolve():
            raise ValueError("開発用の配布先が固定資料の作業場所にない")
        prior = core.OUT, core.LOCK, core.PLAN
        core.OUT, core.LOCK, core.PLAN = target, target / "population.json", target / "method.json"
        try:
            core.save_once(core.PLAN, core.encoded(method))
            core.save_once(core.LOCK, core.encoded({"inputs": {}}))
            selected = core.OUT / "selection.json"
            core.save_once(selected, core.encoded({
                "population_lock_sha256": core.sha(core.LOCK), "selected": list(used.values())
            }))
            proof = launch.package(core.sha(selected))
            manifest = core.OUT / "delivery/packages.json"
            batches = core.load(manifest)["packs"]
            if (proof["rows"] != len(used) or proof["cross_rows"] <= 0 or proof["paired_coordinate_rows"] <= 0
                    or max(len(p["request"]["images"]) for p in batches.values()) != audit.LIMIT):
                raise ValueError("枠の上下、座標の結合、添付上限を開発用に確かめられない")
            return proof
        finally:
            core.OUT, core.LOCK, core.PLAN = prior


def marks():
    stage = "v69-neutral-rounded-source-pilot"
    baseline = launch.HERE.parent / stage
    lock, comparison = baseline / "lock.json", baseline / "comparison.json"
    checked, plan = core.load(comparison), core.load(lock)
    if (checked["lock_sha256"] != core.sha(lock)
            or any(core.sha(Path(f)) != h for f, h in plan["files"].items())):
        raise ValueError("小点の別の開発証拠と原票が事前固定と異なる")
    reference = core.load(baseline / "source-result.json")["cases"]
    display = core.CORPUS / ("reference-" + stage) / "display"
    rows = core.load(display / "selection.json")["selected"]
    asset_path = display / "new/delivery"
    manifest = core.load(asset_path / "packages.json")
    data = core.load(pilot / "source-commands.json")
    root = asset_path / "source-assets"
    catalog, loaded = launch.previous.packets.old.lookup()[1], {}
    counts = {}
    for name, expected in checked["cases"].items():
        key = expected["page"], expected["line_index"]
        marker = plan["mapping"][name.split("/")[0]]["arms"]["new"]
        row, assets = rows[marker["entry"]], marker["image_reference"]
        paired, coords = expected["answers"]["pair"], expected["coordinates"]
        if not core.ref.MARK.search(paired["text"]) or len(coords) != 1:
            raise ValueError("独立した二票による小点の位置を取り出せない")
        item = {"row": row, "assets": assets, "answer": paired, "coordinates": coords}
        points = manifest["source_assets"]
        notes = {}
        confirmation = launch.source.mark_from_source(item, data, catalog, loaded, root, points, notes)
        if key in {("kanpo1828-p1-p0001", 117), ("kanpo1828-p1-p0001", 120)}:
            if (not confirmation or notes or confirmation[0]["text"] != "・"
                    or confirmation[1]["route"] != "single-vertical-source-command"
                    or core.encoded(confirmation[1]["source-confirmed"]) != core.encoded(reference[name]["evidence"])):
                raise ValueError("許可された中黒を新しい正式の入口で確認できない")
            name_450 = next(f["image"] for f in assets["source_view"]["views"][1]["images"] if f["kind"] == "plain")
            try:
                launch.source.mark_from_source(item, data, catalog, loaded, root, points | {name_450: "0" * 64})
            except ValueError as error:
                if str(error) != "元PDFまたは固定画像の来歴が異なる":
                    raise
                counts["bad-sha"] = "rejected"
            else:
                raise ValueError("来歴の異なる画素から符号を確定した")
            counts[f"point-{key[1]}"] = confirmation[1]["source-confirmed"]
        elif (key != ("defense-p0089", 88) or confirmation
              or notes.get("defense-p0089/88", {}).get("type") != "no-proof"):
            raise ValueError("承認された範囲にない大きな項目の丸から小点を確定した")
        else:
            counts["large-bullet"] = "rejected"
    if set(counts) != {"point-117", "point-120", "large-bullet", "bad-sha"}:
        raise ValueError("小点の開発用の現物と対照に不足がある")
    return counts


def replay_archived_marks():
    archive = core.CORPUS / "reference-audit-v47"
    if core.OUT != archive:
        raise ValueError("開発の回帰検査で新しい正式標本を使おうとした")
    folder = archive / "delivery"
    source = core.load(archive / "source-commands.json")
    old_result = core.load(launch.PRIOR / "result.json")
    if old_result["source_sha256"] != core.sha(archive / "source-commands.json"):
        raise ValueError("回帰試験の出典が以前の正式判定と異なる")
    shipment = core.transport.check(folder, core.sha(folder / "packages.json"))
    cases, _ = core.image_cases(shipment, core.old_sessions())
    catalog, loaded = launch.previous.packets.old.lookup()[1], {}
    selected, notes = {}, {}
    for item in cases:
        row = item["row"]
        marks = core.ref.MARK.findall(item["answer"]["text"])
        if (row["allocation_axis"] != "x" or len(item["coordinates"]) != 1
                or len(marks) != 1 or marks[0][0] != "round"):
            continue
        name = f"{row['key']}/{row['line_index']}"
        answer = launch.source.mark_from_source(item, source, catalog, loaded, folder / "source-assets",
                                                shipment.document["source_assets"], notes)
        selected[name] = "confirmed" if answer else "insufficient"
    overlap = "wp-summary-p0010/34"
    if (len(selected) != 16 or selected.get(overlap) != "insufficient"
            or notes.get(overlap, {}).get("message") != "同じ画素の位置に文字以外の描画がある"):
        raise ValueError("文字以外の描画が重なる固定の出典不足を再現できない")
    return {"states": selected, "notes": notes}


def main():
    if launch.PREFLIGHT.exists() or launch.PLAN.exists():
        raise FileExistsError("事前確認または方法はすでに固定した")
    decisions = [line.strip() for line in launch.REVIEW.read_text(encoding="utf-8").splitlines()
                 if line.strip().startswith("Final Result: ")]
    if not decisions or decisions[-1] != "Final Result: APPROVED":
        raise ValueError("正式な入口のレビューの承認を確認できない")
    core.verify_methods()
    dependencies = launch.dependencies()
    plan = launch.trial_method()
    launch.primitives(plan, launch.CANDIDATE / "result.json", launch.candidate())
    packet_proof = packets(plan)
    point_proof = marks()
    past_points = replay_archived_marks()
    labels = launch.candidate()
    _, flags = core.baseline.take_public_rows()
    dimensions = launch.capacity(core.baseline.populations(core.load(labels / "public.json"), flags))
    exercised = launch.dependencies()
    if any(exercised.get(f) != h for f, h in dependencies.items()):
        raise ValueError("試験の途中で正式に実行するコードが変わった")
    core.save_once(launch.PLAN, core.encoded(plan))
    core.save_once(launch.PREFLIGHT, core.encoded({
        "scope": "development-only-before-sampling", "inputs": exercised, "method_sha256": core.sha(launch.PLAN),
        "delivery": packet_proof, "marks": point_proof, "archived_round_regression": past_points,
        "capacity": dimensions, "versions": launch.previous.versions(),
    }))
    print(packet_proof, {k: (v["rows"], max(v["mandatory_counts"])) for k, v in dimensions.items()}, flush=True)


if __name__ == "__main__":
    main()
