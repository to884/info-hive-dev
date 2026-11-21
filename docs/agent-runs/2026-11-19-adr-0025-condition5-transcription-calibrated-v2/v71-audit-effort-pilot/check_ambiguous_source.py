"""開発用highの両票で位置がそろった曖昧な符号だけを出典で確かめる。"""

from collections import Counter
from importlib.util import module_from_spec, spec_from_file_location
from pathlib import Path

HERE = Path(__file__).resolve().parent
STAGES = HERE.parent
spec = spec_from_file_location("source_for_effort_pilot", HERE / "run.py")
fixed = module_from_spec(spec)
spec.loader.exec_module(fixed)
core, launch, judge, previous = fixed.core, fixed.launch, fixed.judge, fixed.previous


def main():
    launch.configure()
    core.verify_methods()
    lock, comparison = HERE / "lock.json", HERE / "comparison.json"
    plan, archive = core.load(lock), core.load(comparison)
    if (archive["lock_sha256"] != core.sha(lock)
            or any(core.sha(Path(p)) != h for p, h in plan["files"].items())):
        raise ValueError("固定した開発試験と比較結果を結べない")
    rows = core.load(fixed.pilot.OUT / "display/selection.json")["selected"]
    if set(archive["cases"]) != set(plan["mapping"]):
        raise ValueError("固定した開発試験の行がそろわない")
    pending = {}
    for pack, case in archive["cases"].items():
        if case["outcomes"]["high"]["pair"] != "source-pending":
            continue
        binding = plan["mapping"][pack]
        row = rows[binding["entry"]]
        pair = case["readings"]["high"]
        answer, places = core.ref.aligned(pair["gpt"], pair["claude"], row["box"][2])
        if pair["pair"] != answer or pair["coordinates"] != [list(p) for p in places] or not places or not core.ref.MARK.search(answer["text"]):
            raise ValueError("二票の本文と符号の位置の一致を再現できない")
        pending[pack] = {"row": row, "answer": answer, "coordinates": places, "assets": binding["image_reference"]}

    display = fixed.pilot.OUT / "display"
    req, source = (display / f"high-source-{kind}.json" for kind in ("requests", "commands"))
    asked = core.encoded({"pages": sorted({item["row"]["key"] for item in pending.values()})})
    if not req.exists():
        core.save_once(req, asked)
    elif req.read_bytes() != asked:
        raise ValueError("二票の一致から抽出したページと異なる")

    official = launch.source
    reader = official.draft.source
    original = previous.module("effort_pilot_original", previous.HERE / "source.py")
    ellipsis = previous.module("effort_pilot_ellipsis", STAGES / "v25-ellipsis-source-pilot/run.py")
    background = previous.module("effort_pilot_round", STAGES / "v28-colored-point-source-pilot/run.py")
    routes = {"ellipsis": ellipsis, "old_source": original, "trail": ellipsis.trail,
              "trace": ellipsis.trace, "background": background}
    if not source.exists():
        original.initial.collect(req, source)
    data = core.load(source)
    core.ref.checked_source(data, req)
    assets = core.load(fixed.delivery / "packages.json")["source_assets"]
    catalog, loaded = previous.packets.old.lookup()[1], {}
    cases, notes, counts = {}, {}, Counter()
    for pack, item in pending.items():
        answer, proof = core.ref.v10.resolved(item, data)
        if proof in ("source-location-not-proven", "source-unavailable"):
            confirmed = reader.fallback(core, item, data, catalog, loaded, routes) or official.mark_from_source(
                item, data, catalog, loaded, fixed.delivery / "source-assets", assets, notes)
            if confirmed:
                answer, proof = confirmed
        verdict = judge.verdict(core.ref, answer, item["row"]["effective"])
        counts[verdict] += 1
        cases[pack] = {"page": item["row"]["key"], "line_index": item["row"]["line_index"],
                       "outcome": verdict, "answer": answer, "evidence": proof}
    core.save_once(HERE / "source-followup.json", core.encoded({
        "scope": "development-only", "cases": cases, "notes": notes, "counts": counts,
        "inputs": {str(p): core.sha(p) for p in (Path(__file__), comparison, lock, req, source)},
    }))
    print(dict(counts), flush=True)


if __name__ == "__main__":
    main()
