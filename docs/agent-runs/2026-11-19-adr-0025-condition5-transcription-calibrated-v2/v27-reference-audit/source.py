"""一致した画像票の符号だけを原本で確認し、既定の二つの監査を確定する。"""

from collections import Counter

import numpy as np
from PIL import Image


def compatible_bounds(prior, added):
    return all(not (max(a, p) < min(c, r) and max(b, q) < min(d, s))
               for a, b, c, d in prior for p, q, r, s in added)


def close_round(old_source, png, frame, location):
    """周囲に別の成分があるとき、両票から3画素以内の候補だけを確認する。"""
    with Image.open(png) as im:
        gray = np.array(im.convert("L"))
    a, b = (old_source.boxes(gray, frame, cutoff) for cutoff in (140, 186))
    leading = frame[0]
    candidates = [
        p for p in b if max(abs((p[0] + p[2]) / 2 - leading - n) for n in location) <= 3
        and sum(max(abs(x - y) for x, y in zip(p, q, strict=True)) <= 1 for q in a) == 1
    ]
    if len(candidates) != 1:
        return None
    return candidates[0]


def fallback(mod, case, source_data, catalog, loaded, routes):
    ref = mod.ref
    row, answer, coordinates = case["row"], case["answer"], case["coordinates"]
    markers = list(ref.MARK.finditer(answer["text"]))
    if row["allocation_axis"] != "x" or not markers or len(markers) != len(coordinates):
        return None
    commands = source_data["evidence"].get(row["key"], {})
    flags = case["assets"]["sha"]
    collection = []
    if commands.get("pdf_sha256") == flags["pdf_sha256"] and "unsupported" not in commands:
        collection = commands["commands"]
    key = row["key"]
    name, expected, number = catalog[key]
    if name not in loaded:
        loaded[name] = (mod.CORPUS / name).read_bytes()
    original = loaded[name]
    png = mod.CORPUS / "probe-v4/png" / (key + ".png")
    if routes["trace"].sha(original) != expected or expected != flags["pdf_sha256"] or mod.sha(png) != flags["150_dpi"]:
        raise ValueError("元のPDFと固定150 DPIの来歴が異なる")
    with Image.open(png) as im:
        pixels = np.array(im.convert("RGB"))
    intervals, symbols, anchors, evidence = set(), [], [], []
    for marker, location in zip(markers, coordinates, strict=True):
        physical = marker.group()
        short = {**case, "answer": {"status": "readable", "text": physical}, "coordinates": [location]}
        outcome, record = ref.v10.resolved(short, source_data)
        if outcome["status"] == "readable" and isinstance(record, dict):
            item, = record["source-confirmed"]
            bounds, text = item["bounds"], outcome["text"]
            proof = {"route": "positioned-original-command", "detail": item}
        elif marker[1] == "round":
            isolated = routes["old_source"].isolated(short, catalog, loaded)
            if isolated is None:
                isolated = routes["background"].isolated(short, catalog, loaded)
            if isolated:
                value, record = isolated
                item, = record["source-confirmed"]
                bounds, text = [item["box"]], value["text"]
                proof = {"route": "pdfium-isolated-round", "detail": item}
            else:
                chosen = close_round(routes["old_source"], png, row["box"], location)
                if chosen is None:
                    return None
                try:
                    item = routes["trace"].trace(original, number, pixels, chosen, flags)
                except (ValueError, KeyError, TypeError, AttributeError, IndexError):
                    return None
                if item["codepoint"] not in ("2022", "30FB"):
                    return None
                bounds, text = [chosen], chr(int(item["codepoint"], 16))
                proof = {"route": "isolated-round-within-three-pixels", "detail": item}
        elif collection:
            try:
                bounds = routes["trail"].old.dot_groups(short, png, marker, location)
            except (ValueError, KeyError, TypeError, AttributeError, IndexError):
                return None
            try:
                ellipsis = routes["ellipsis"].spell(original, number, pixels, bounds, flags, collection)
            except (ValueError, KeyError, TypeError, AttributeError, IndexError):
                try:
                    cids = routes["trail"].spell(original, number, pixels, bounds, flags, collection)
                except (ValueError, KeyError, TypeError, AttributeError, IndexError):
                    return None
                text = "".join(chr(int(entry["codepoint"], 16)) for entry in cids)
                proof = {"route": "point-origins-and-font", "detail": cids}
            else:
                text = "…" * ellipsis["glyphs"]
                proof = {"route": "isolated-ellipsis-drawing", "detail": ellipsis}
        else:
            return None
        boxes = {tuple(box) for box in bounds}
        if not boxes or not compatible_bounds(intervals, boxes):
            return None
        left, right = min(box[0] for box in boxes), max(box[2] for box in boxes)
        if anchors and anchors[-1] > left:
            return None
        anchors.append(right)
        intervals.update(boxes)
        symbols.append(text)
        evidence.append({**proof, "relative_positions": location, "physical_boxes": sorted(boxes)})
    parts = iter(symbols)
    output = ref.MARK.sub(lambda _: next(parts), answer["text"])
    return {"status": "readable", "text": ref.NORMALIZE(output)}, {"source-confirmed": evidence, "route": "isolated-fallback"}


def finish(mod, shipment, older):
    ref, previous = mod.ref, mod.previous
    path = mod.HERE / "result.json"
    if path.exists():
        raise FileExistsError("正式な監査の判定は確定済み")
    cases, summary = mod.image_cases(shipment, older)
    req, recorded = mod.OUT / "source-requests.json", mod.OUT / "source-commands.json"
    wanted = mod.encoded({"pages": sorted({c["row"]["key"] for c in cases
                                         if ref.MARK.search(c["answer"]["text"])})})
    if not req.exists():
        mod.save_once(req, wanted)
    elif req.read_bytes() != wanted:
        raise ValueError("二系統の独立票が合意した出典の依頼と異なる")

    old_source = mod.module("original_pdf_source", previous.HERE / "source.py")
    ellipsis = mod.module("isolated_ellipsis", mod.HERE.parent / "v25-ellipsis-source-pilot/run.py")
    background = mod.module("isolated_with_ground_color", mod.HERE.parent / "v28-colored-point-source-pilot/run.py")
    routes = {"ellipsis": ellipsis, "old_source": old_source, "trail": ellipsis.trail,
              "trace": ellipsis.trace, "background": background}
    if not recorded.exists():
        old_source.initial.collect(req, recorded)
    data = mod.load(recorded)
    ref.checked_source(data, req)
    catalog, loaded = previous.packets.old.lookup()[1], {}
    by_row, trace, counts = {}, {}, Counter()
    for case in cases:
        row = case["row"]
        answer, reason = ref.v10.resolved(case, data)
        if reason == "plain-unresolved":
            reason = case["reason"]
        if reason in ("source-location-not-proven", "source-unavailable"):
            proof = fallback(mod, case, data, catalog, loaded, routes)
            if proof:
                answer, evidence = proof
                reason = {**evidence, "earlier_reason": reason}
        by_row[ref.v10.identity(row)] = answer
        counts["source-confirmed" if isinstance(reason, dict) else reason] += 1
        trace[f"{row['key']}/{row['line_index']}"] = {"answer": answer, "evidence": reason}
    mod.verify_methods()
    mod.image_cases(shipment, older)
    details = mod.OUT / "reference-evidence.json"
    blob = mod.encoded(trace)
    if not details.exists():
        mod.save_once(details, blob)
    elif details.read_bytes() != blob:
        raise ValueError("再現した参照の証跡が以前に保存したものと異なる")
    rows = [v["row"] for v in cases]
    scores = ref.v10.summarize(rows, summary, by_row)
    overlaps = {side: {tag: sum(bool(r[tag]) for r in rows if side in r["targets"])
                      for tag in ("development_intake", "previously_audited")} for side in scores}
    mod.save_once(path, mod.encoded({
        "scope": "independent-audit-once", "summary": scores, "overlap": overlaps,
        "all_quality_checks_pass": all(t["status"] == "pass" for t in scores.values()), "sources": counts,
        "receipts_sha256": mod.sha(shipment.folder / "received.json"), "source_sha256": mod.sha(recorded),
        "reference_sha256": mod.sha(details),
    }))
    print({k: s["status"] for k, s in scores.items()}, dict(counts), flush=True)
