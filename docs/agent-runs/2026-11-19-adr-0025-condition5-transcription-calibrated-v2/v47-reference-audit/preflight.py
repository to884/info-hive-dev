"""開発画像だけで、行末の添付欠落と小点の複数候補を回帰検査する。"""

from pathlib import Path
from tempfile import TemporaryDirectory

import numpy as np

import audit

HERE, core = audit.HERE, audit.core
load, sha = core.load, core.sha
artifacts = core.CORPUS
previous = audit.previous
strict = previous.module("strict_round_regression", audit.draft.raster_file)
OLDER = previous.module("saved_development_sources", audit.draft.PRIOR / "run.py")
OVERSIZED = (86, 177, 282, 304, 327, 331, 362, 364)


def check_packets():
    pilot = artifacts / "reference-v49-combined-frame-bullets-pilot/display/selection.json"
    past = artifacts / "reference-audit-v27"
    select, manifest = past / "selection.json", past / "delivery/packages.json"
    evidence, packages = load(select)["selected"], load(manifest)["packs"]
    render = load(pilot)["selected"]
    cases = {(r["key"], r["line_index"]): r for r in render}
    for index in OVERSIZED:
        (item,) = packages[f"pack-{index:03d}"]["mapping"].values()
        row = evidence[item["entry"]]
        cases.setdefault((row["key"], row["line_index"]), row)
    _, _, labels = core.methods()
    extreme_source = labels / "public.json"
    extreme, = [r for r in load(extreme_source) if r["box"][2:] == [1726, 34] and r["allocation_axis"] == "x"]
    cases[extreme["key"], extreme["line_index"]] = extreme
    rows = list(cases.values())
    with TemporaryDirectory(prefix="adr0025-development-delivery-") as temp:
        saved = core.OUT, core.LOCK
        core.OUT = Path(temp).resolve()
        core.LOCK = core.OUT / "preflight-lock.json"
        selection = core.OUT / "selection.json"
        core.save_once(core.LOCK, core.encoded({"inputs": {}}))
        core.save_once(selection, core.encoded({"population_lock_sha256": sha(core.LOCK), "selected": rows}))
        try:
            audit.package(sha(selection))
            package_file = core.OUT / "delivery/packages.json"
            counts = audit.verify_delivery(sha(package_file))
            del counts["packages_sha256"]
            attached = load(package_file)["packs"]
            capped = sum(len(item["request"]["images"]) == audit.LIMIT for item in attached.values())
            if counts["rows"] != len(cases) or counts["rows"] != 27 or capped < 8 or counts["paired_coordinate_rows"] != 1:
                raise ValueError("上限に達した開発対照が配布の検査に足りない")
        finally:
            core.OUT, core.LOCK = saved
    return {**counts, "capped_rows": capped}, (pilot, select, manifest, extreme_source)


def check_rounds():
    pixels = np.full((140, 240), 255, dtype=np.uint8)
    pixels[40:46, 56:62] = 32
    rect = (30, 30, 180, 90)
    box = (100, 100, 50, 20)
    place = (12, 12, 12, 12)
    strict.physical(pixels, rect, box, place)
    pixels[40:46, 69:75] = 32
    pixels[40:46, 75:105] = 170
    original = previous.module("original_coordinate_counter", HERE.parent / "v44-small-point-pixel-pilot/run.py")
    original.physical(pixels, rect, box, place)
    try:
        strict.physical(pixels, rect, box, place)
    except ValueError:
        pass
    else:
        raise ValueError("片方の閾値で二つの点がある曖昧な画素を受理した")

    OLDER.verify_methods()
    folder = OLDER.OUT / "delivery"
    bound = folder / "packages.json"
    ship = OLDER.transport.check(folder, sha(bound))
    recorded = OLDER.OUT / "source-commands.json"
    old_result = OLDER.HERE / "result.json"
    if load(old_result)["source_sha256"] != sha(recorded):
        raise ValueError("以前の確定と元PDFの証跡が対応しない")
    src = load(recorded)["evidence"]
    found, _ = OLDER.image_cases(ship, OLDER.old_sessions())
    catalog = previous.packets.old.lookup()[1]
    tested = []
    for item in found:
        row = item["row"]
        key, idx = row["key"], row["line_index"]
        if (key, idx) not in {("defense-p0136", 79), ("disaster-p0015", 10)}:
            continue
        view = item["assets"]["source_view"]["views"][1]
        name = next(v["image"] for v in view["images"] if v["kind"] == "plain")
        file, digest, number = catalog[key]
        fixed = artifacts / "probe-v4/png" / (key + ".png")
        proof = strict.confirm(item, folder / "source-assets" / name, ship.document["source_assets"][name], fixed,
                               (artifacts / file).read_bytes(), digest, number, src[key]["commands"])
        if not proof:
            raise ValueError("開発で確認済みの本物の小点が受理されない")
        tested.append((key, idx, [e["statement"]["codepoint"] for e in proof[1]]))
    if len(tested) != 2:
        raise ValueError("小点の開発用の実資料が不足")
    return {"ambiguous_control": "rejected", "confirmed": sorted(tested)}, (bound, recorded, old_result)


def main():
    res = audit.PREFLIGHT
    if res.exists():
        raise FileExistsError("確定した開発用の配布確認は上書きしない")
    results, first = check_packets()
    source, second = check_rounds()
    files = (Path(__file__), HERE / "audit.py", HERE / "run.py", audit.draft.raster_file,
             HERE.parent / "v44-small-point-pixel-pilot/run.py", core.PLAN, *first, *second)
    core.save_once(res, core.encoded({"scope": "development-only",
                                      "attachments": results, "rounds": source,
                                      "inputs": {str(p.resolve()): sha(p) for p in files}}))
    print(results, source, flush=True)


if __name__ == "__main__":
    main()
