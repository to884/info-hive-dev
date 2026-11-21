"""開発の両票が同じ位置を指した符号だけを元PDFで照合する。"""

from collections import Counter
from pathlib import Path
import sys

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parent / "v47-reference-audit"))
import official

core = official.core
implementation = official.audit.draft
previous = core.previous
proof = previous.module("approved_development_source_routes", HERE.parent / "v49-combined-frame-bullets-pilot/compare.py")
strict = previous.module("one_shape_at_each_threshold", implementation.raster_file)


def main():
    report = HERE / "source-comparison.json"
    if report.exists():
        raise FileExistsError("この開発の出典照合は確定済み")
    core.verify_methods()
    loc = core.CORPUS / "reference-v54-horizontal-mark-coordinates-pilot"
    lock, result = HERE / "lock.json", HERE / "result.json"
    plan, collected = core.load(lock), core.load(result)
    if (collected["lock_sha256"] != core.sha(lock) or set(collected["cases"]) != set(plan["jobs"])
            or any(core.sha(Path(p)) != h for p, h in plan["files"].items())):
        raise ValueError("開発の読取を事前固定へ結び付けられない")
    cases = collected["cases"]
    unresolved = {n: r for n, r in cases.items() if r["pair_result"] == "both-location-needs-source"}
    request, extracted = loc / "source-request.json", loc / "source-commands.json"
    allowed = core.encoded({"pages": sorted({r["page"] for r in unresolved.values()})})
    if not request.exists():
        core.save_once(request, allowed)
    elif request.read_bytes() != allowed:
        raise ValueError("二票が同じ位置を記録した箇所と異なる")
    if not extracted.exists():
        proof.old_source.initial.collect(request, extracted)
    source = core.load(extracted)
    previous.ref.checked_source(source, request)
    directory = core.OUT / "delivery"
    bound = core.load(directory / "packages.json")["source_assets"]
    rows = core.load(loc / "display/selection.json")["selected"]
    catalog, cache = previous.packets.old.lookup()[1], {}
    results = {n: {"result": r["pair_result"]} for n, r in cases.items()}
    for name, record in unresolved.items():
        part = plan["mapping"][name.split("/")[0]]
        epoch = plan["jobs"][name]
        images = epoch["request"]
        if any(core.sha(Path(epoch["cards"]) / f) != h for f, h in zip(images["images"], images["image_sha256"], strict=True)):
            raise ValueError("実際の二票の固定画像が変わった")
        row, assets, votes = rows[part["entry"]], part["image_reference"], record["readings"]
        target = {"row": row, "answer": votes["pair"], "assets": assets, "coordinates": votes["coordinates"]}
        answer, detail = previous.ref.v10.resolved(target, source)
        needs_confirmation = detail in ("source-location-not-proven", "source-unavailable")
        if needs_confirmation:
            supported = proof.baseline.fallback(core, target, source, catalog, cache, proof.ROUTES)
            if supported:
                answer, detail = supported
        page = row["key"]
        evidence = source["evidence"].get(page, {})
        if (answer["status"] == "unreadable" and needs_confirmation
                and evidence.get("pdf_sha256") == assets["sha"]["pdf_sha256"] and "unsupported" not in evidence):
            filename, pdf_sha, number = catalog[page]
            high = assets["source_view"]["views"][1]
            tag = next(t["image"] for t in high["images"] if t["kind"] == "plain")
            source_png = core.CORPUS / "probe-v4/png" / (page + ".png")
            supported = strict.confirm(target, directory / "source-assets" / tag, bound[tag], source_png,
                                       (core.CORPUS / filename).read_bytes(), pdf_sha, number,
                                       evidence.get("commands", []))
            if supported:
                answer, detail = supported
        if answer["status"] == "unreadable":
            decision = "insufficient-source"
        else:
            decision = "same" if answer["text"] == record["expected"] else "different"
        results[name] = {"result": decision, "page": row["key"], "line_index": row["line_index"], "proof": detail}
        print(row["key"], row["line_index"], decision, flush=True)
    counts = Counter(d["result"] for d in results.values())
    files = (Path(__file__), lock, result, extracted, implementation.raster_file, Path(proof.__file__))
    core.save_once(report, core.encoded({"scope": "development-only", "counts": counts, "cases": results,
                                         "inputs": {str(p.resolve()): core.sha(p) for p in files}}))
    print(dict(counts), flush=True)


if __name__ == "__main__":
    main()
