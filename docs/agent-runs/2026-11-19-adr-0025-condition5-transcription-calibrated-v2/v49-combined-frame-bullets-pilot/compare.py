"""開発の二票で同じ位置を記録した小点だけを、既存の範囲で出典照合する。"""

import argparse
from collections import Counter
from pathlib import Path
import sys

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parent / "v19-reference-audit"))
import run as previous

core = previous.module("separate_source_comparison", HERE.parent / "v47-reference-audit/run.py")
small = previous.module("higher_resolution_components", core.raster_file)
baseline = core.source
old_source = previous.module("prior_round_and_trail", previous.HERE / "source.py")
ellipsis = previous.module("isolated_leaders", HERE.parent / "v25-ellipsis-source-pilot/run.py")
background = previous.module("isolated_uniform_color", HERE.parent / "v28-colored-point-source-pilot/run.py")
ROUTES = {"old_source": old_source, "ellipsis": ellipsis, "trail": ellipsis.trail,
          "trace": ellipsis.trace, "background": background}
WAS = core.core.CORPUS / "reference-audit-v27/delivery"
KINDS = {"46": HERE.parent / "v46-paragraph-circle-pilot", "49": HERE}


def main():
    cli = argparse.ArgumentParser(description=__doc__)
    cli.add_argument("stage", choices=KINDS)
    args = cli.parse_args()
    group = KINDS[args.stage]
    private = core.core.CORPUS / ("reference-" + group.name)
    path, locked = group / "result.json", group / "lock.json"
    final = group / "source-comparison.json"
    if final.exists():
        raise FileExistsError("確定した開発の照合を上書きしない")
    result, plan = previous.load(path), previous.load(locked)
    if (result["lock_sha256"] != previous.sha(locked) or set(result["cases"]) != set(plan["jobs"])
            or any(previous.sha(Path(f)) != h for f, h in plan["files"].items())):
        raise ValueError("固定した開発依頼と原票の集計が一致しない")
    rows = previous.load(private / "display/selection.json")["selected"]
    outcome = {n: {"result": r["pair_result"]} for n, r in result["cases"].items()}
    located = {n: r for n, r in result["cases"].items() if r["pair_result"] == "both-location-needs-source"}
    request, proof = (private / f"bounded-source-{label}.json" for label in ("request", "evidence"))
    agenda = previous.encoded({"pages": sorted({r["page"] for r in located.values()})})
    if not request.exists():
        previous.save_once(request, agenda)
    elif request.read_bytes() != agenda:
        raise ValueError("二票で確認した出典箇所が既定の証跡と違う")
    if not proof.exists():
        old_source.initial.collect(request, proof)
    evidence = previous.load(proof)
    previous.ref.checked_source(evidence, request)
    root = WAS if args.stage == "46" else private / "display/delivery"
    official = previous.load(root / "packages.json")["source_assets"]
    catalog, loaded = previous.packets.old.lookup()[1], {}
    for name, found in located.items():
        link = plan["mapping"][name.split("/")[0]]
        selected = rows[link["entry"]]
        assets, job = link["image_reference"], plan["jobs"][name]
        if any(previous.sha(Path(job["cards"]) / f) != d for f, d in
               zip(job["request"]["images"], job["request"]["image_sha256"], strict=True)):
            raise ValueError("二票を得た固定画像が変化")
        texts = found["readings"]
        item = {"row": selected, "answer": texts["pair"], "assets": assets, "coordinates": texts["coordinates"]}
        value, reason = previous.ref.v10.resolved(item, evidence)
        if reason in ("source-location-not-proven", "source-unavailable"):
            added = baseline.fallback(core.core, item, evidence, catalog, loaded, ROUTES)
            if added:
                value, reason = added
        if value["status"] == "unreadable":
            key = found["page"]
            doc, expected, number = catalog[key]
            if doc not in loaded:
                loaded[doc] = (core.core.CORPUS / doc).read_bytes()
            f = next(v["image"] for v in assets["source_view"]["views"][1]["images"] if v["kind"] == "plain")
            if f in official:
                img = root / "source-assets" / f
                png = core.core.CORPUS / "probe-v4/png" / (key + ".png")
                extra = small.confirm(item, img, official[f], png, loaded[doc], expected, number,
                                      evidence["evidence"][key].get("commands", []))
                if extra:
                    value, asserted = extra
                    reason = {"route": "450-dpi-location", "evidence": asserted}
        if value["status"] == "unreadable":
            verdict = "insufficient-source"
        elif value["text"] == found["expected"]:
            verdict = "same"
        elif value["text"] in found["expected"]:
            verdict = "omitted"
        elif found["expected"] in value["text"]:
            verdict = "extra"
        else:
            verdict = "different"
        outcome[name] = {"result": verdict, "proof": reason}
        print(found["page"], found["line_index"], verdict, flush=True)
    counts = Counter(r["result"] for r in outcome.values())
    files = (Path(__file__), locked, path, proof, Path(small.__file__), Path(baseline.__file__))
    previous.save_once(final, previous.encoded({"scope": "development-only", "counts": counts, "cases": outcome,
                                               "inputs": {str(f): previous.sha(f) for f in files}}))
    print(dict(counts), flush=True)


if __name__ == "__main__":
    main()
