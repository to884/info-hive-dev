"""二票が位置に一致した曖昧な符号だけを、固定元資料で確かめる。"""

import json
from collections import Counter
from pathlib import Path
from types import SimpleNamespace

from pypdf.errors import PdfReadError

import render

HERE = Path(__file__).resolve().parent
core, draft, previous = render.core, render.draft, render.previous
vertical_path = HERE.parent / "v61-vertical-point-command-pilot/run.py"
verify_vertical = previous.module("independently_visible_vertical_point", vertical_path)
strict_450 = previous.module("verified_450_dpi_point_in_audit", draft.raster_file)

INTEGRITY_FAILURE = {
    "二票の固定画素と元PDFの来歴が異なる",
    "非表示にする一つの描画命令が異なる",
    "登録済みの中黒のCIDと符号が異なる",
    "元の描画と固定した画素が異なる",
    "描画命令の切り分けに失敗",
}


def mark_from_source(item, data, catalog, loaded, folder, assets, notes=None):
    row, bound = item["row"], item["assets"]
    key = row["key"]
    basename, expected, page = catalog[key]
    if basename not in loaded:
        loaded[basename] = (core.CORPUS / basename).read_bytes()
    high = bound["source_view"]["views"][1]
    name = next(v["image"] for v in high["images"] if v["kind"] == "plain")
    fixed = folder / name
    low = core.CORPUS / "probe-v4/png" / (key + ".png")
    pdf = loaded[basename]
    if (core.sha(fixed) != assets[name] or core.sha(low) != bound["sha"]["150_dpi"]
            or verify_vertical.trace.sha(pdf) != expected or expected != bound["sha"]["pdf_sha256"]):
        raise ValueError("元PDFまたは固定画像の来歴が異なる")
    args = fixed, assets[name], low, pdf, expected, page
    record = data["evidence"].get(key, {})
    attempted = []
    if record.get("pdf_sha256") == bound["sha"]["pdf_sha256"] and "unsupported" not in record:
        nearest = strict_450.confirm(item, *args, record["commands"])
        if nearest:
            value, proof = nearest
            return value, {"source-confirmed": proof, "route": "fixed-450-dpi-location-and-isolated-source"}
        attempted.append("fixed-450-dpi-location")

    def record_insufficient(kind, message):
        if notes is not None:
            notes[f"{key}/{row['line_index']}"] = {"route": "single-vertical-source-command",
                                                    "type": kind, "message": message,
                                                    "prior_routes_without_proof": attempted}

    try:
        isolated = verify_vertical.prove(item, *args)
    except (PdfReadError, ValueError) as error:
        if str(error) in INTEGRITY_FAILURE:
            raise
        record_insufficient(type(error).__name__, str(error))
        return None
    if isolated:
        value, proof = isolated
        return value, {"source-confirmed": proof, "route": "single-vertical-source-command"}
    record_insufficient("no-proof", "対象の一つの小点を証明できない")
    return None


def close(shipment):
    reader = draft.source
    fallback = reader.fallback
    folder = shipment.folder / "source-assets"
    asset_hashes = shipment.document["source_assets"]
    unsupported = {}

    def development_overlap():
        result = core.load(HERE.parent / "v70-reference-candidate/result.json")
        changed = {(r["page"], r["line_index"]) for r in result["changed"]}
        rows = core.load(core.OUT / "selection.json")["selected"]
        readings = core.load(core.OUT / "reference-evidence.json")
        summary = {"region": Counter(), "image": Counter()}
        overlaps = {"region": 0, "image": 0}
        for row in rows:
            key = row["key"], row["line_index"]
            vote = readings[f"{key[0]}/{key[1]}"]["answer"]
            for domain, target in row["targets"].items():
                if not target["known"]:
                    continue
                if key in changed:
                    overlaps[domain] += 1
                    continue
                status = "insufficient"
                if vote["status"] != "unreadable":
                    status = "same" if vote["text"] == core.ref.NORMALIZE(target["text"]) else "different"
                summary[domain][status] += 1
        return {"known_without_revised_development_rows": summary, "revised_rows": overlaps}

    def after_old(mod, item, data, catalog, loaded, routes):
        found = fallback(mod, item, data, catalog, loaded, routes)
        if found:
            return found
        answer = mark_from_source(item, data, catalog, loaded, folder, asset_hashes, unsupported)
        if answer is None:
            row = item["row"]
            key = f"{row['key']}/{row['line_index']}"
            unsupported[key]["prior_routes_without_proof"].insert(0, "isolated-fallback")
        return answer

    def save_with_source_notes(path, value):
        if path == HERE / "result.json":
            notes = core.OUT / "unsupported-point-sources.json"
            serialized = core.encoded(unsupported)
            if not notes.exists():
                core.save_once(notes, serialized)
            elif notes.read_bytes() != serialized:
                raise ValueError("出典を確定できなかった記録が前回の保存と異なる")
            result = json.loads(value)
            value = core.encoded({**result, "unsupported_point_sources_sha256": core.sha(notes),
                                  "supplemental_overlap": development_overlap()})
        core.save_once(path, value)

    bridge = SimpleNamespace(**{n: getattr(core, n) for n in (
        "verify_methods", "image_cases", "previous", "ref", "OUT", "encoded", "load", "sha", "module", "CORPUS"
    )}, HERE=HERE, save_once=save_with_source_notes)
    reader.fallback = after_old
    try:
        reader.finish(bridge, shipment, core.old_sessions())
    finally:
        reader.fallback = fallback
