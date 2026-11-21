"""元PDFの点の照合と、凍結した二つの監査結果を作る。"""

from collections import Counter

import numpy as np
from PIL import Image
from scipy.ndimage import label, find_objects

import run

reference = run.as_reference()
initial = run.module("fixed_pdf_commands", run.HERE.parent / "v14-reference-audit/source.py")
proof = run.module("visible_object_reading", run.HERE.parent / "v19-object-source-pilot/trace.py")


def boxes(gray, rectangle, threshold):
    x, y, w, h = rectangle
    left, top = max(0, x - 12), max(0, y - 10)
    region = gray[top:y + h + 10, left:x + w + 12] < threshold
    groups, n = label(region, structure=np.ones((3, 3), dtype=int))
    result = []
    counts = np.bincount(groups.ravel())
    for i, location in enumerate(find_objects(groups, n), 1):
        v, u = location
        a, b, c, d = left + u.start, top + v.start, left + u.stop, top + v.stop
        width, height = c - a, d - b
        if (2 <= width <= 11 and 2 <= height <= 11 and abs(width - height) <= 2
                and counts[i] >= max(4, width * height * .50)
                and y <= (b + d) / 2 < y + h and 2 * (min(c, x + w) - max(a, x)) >= width):
            result.append((a, b, c, d))
    return result


def placement(row, image, coordinates):
    dark, broad = (boxes(image, row["box"], cutoff) for cutoff in (140, 186))
    paired = [a for a in broad if sum(max(abs(k - j) for k, j in zip(a, b, strict=True)) <= 1 for b in dark) == 1]
    result = []
    for readings in coordinates:
        nearby = [p for p in paired if max(abs((p[0] + p[2]) / 2 - row["box"][0] - v) for v in readings) <= 10]
        only, = nearby
        result.append(only)
    if len(set(result)) != len(result):
        raise ValueError("同じ点を二度数えた")
    return result


def isolated(case, catalog, loaded):
    markers = list(reference.MARK.finditer(case["answer"]["text"]))
    if not markers or any(m[1] != "round" for m in markers):
        return None
    row = case["row"]
    if row["allocation_axis"] != "x" or len(markers) != len(case["coordinates"]):
        return None
    key = row["key"]
    flags = case["assets"]["sha"]
    name, expected, page_no = catalog[key]
    if name not in loaded:
        loaded[name] = (run.packets.old.CORPUS / name).read_bytes()
    original = loaded[name]
    png = run.packets.old.CORPUS / "probe-v4/png" / (key + ".png")
    if proof.sha(original) != expected or expected != flags["pdf_sha256"] or run.sha(png) != flags["150_dpi"]:
        raise ValueError("出典と固定画像の不一致")
    with Image.open(png) as img:
        gray, rgb = np.array(img.convert("L")), np.array(img.convert("RGB"))
    try:
        spans = placement(row, gray, case["coordinates"])
        observations = [proof.trace(original, page_no, rgb, span, flags) for span in spans]
    except (ValueError, KeyError, TypeError, AttributeError, IndexError):
        return None
    if any(r["codepoint"] not in ("2022", "30FB") for r in observations):
        return None
    seen = iter(observations)
    text = reference.MARK.sub(lambda _: chr(int(next(seen)["codepoint"], 16)), case["answer"]["text"])
    result = {"status": "readable", "text": reference.NORMALIZE(text)}
    return result, {"source-confirmed": observations, "route": "pdfium-object-render-and-cmap"}


def main():
    if run.ENDED.exists():
        raise FileExistsError("確定した出典と監査結果はそのまま保持する")
    run.verify_before_source()
    if not reference.PROOF.exists():
        initial.collect(reference.REQUESTS, reference.PROOF)
    data = run.load(reference.PROOF)
    reference.checked_source(data, reference.REQUESTS)
    cases, summary = reference.cases()
    catalog, loaded = run.packets.old.lookup()[1], {}
    results, shadows, counts = {}, {}, Counter()
    for case in cases:
        row = case["row"]
        answer, reason = reference.v10.resolved(case, data)
        if reason == "plain-unresolved":
            reason = case["reason"]
        if reason in ("source-location-not-proven", "source-unavailable"):
            check = isolated(case, catalog, loaded)
            if check:
                counts["confirmed-by-isolated-render/" + reason] += 1
                answer, reason = check
        k = reference.v10.identity(row)
        results[k] = answer
        counts["source-confirmed" if isinstance(reason, dict) else reason] += 1
        shadows[f"{row['key']}/{row['line_index']}"] = {"answer": answer, "evidence": reason}
    rows = [v["row"] for v in cases]
    run.verify_before_source()
    final = reference.v10.summarize(rows, summary, results)
    details = run.OUT / "reference-evidence.json"
    packed = run.encoded(shadows)
    if not details.exists():
        run.save_once(details, packed)
    elif details.read_bytes() != packed:
        raise ValueError("集計を中断する前に確定した出典の証跡と異なる")
    overlap = {d: {k: sum(bool(r[k]) for r in rows if d in r["targets"]) for k in ("development_intake", "previously_audited")}
               for d in final}
    run.save_once(run.ENDED, run.encoded({"scope": "independent-audit-once", "summary": final, "overlap": overlap,
        "all_quality_checks_pass": all(r["status"] == "pass" for r in final.values()), "sources": counts,
        "receipts_sha256": run.sha(reference.READ), "source_sha256": run.sha(reference.PROOF),
        "reference_sha256": run.sha(details)}))
    print({k: r["status"] for k, r in final.items()}, dict(counts), flush=True)


if __name__ == "__main__":
    main()
