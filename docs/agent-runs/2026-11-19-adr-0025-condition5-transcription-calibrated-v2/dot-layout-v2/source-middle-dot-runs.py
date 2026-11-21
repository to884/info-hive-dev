"""個別原点が合わない中黒を、連続した同一符号の列単位で照合する。"""

from collections import Counter
import importlib.util
import itertools
import json
from pathlib import Path

HERE = Path(__file__).resolve().parent
SOURCE = HERE / "source-codes.py"
spec = importlib.util.spec_from_file_location("source_codes", SOURCE)
source = importlib.util.module_from_spec(spec)
spec.loader.exec_module(source)
load, sha = source.load, source.sha
CORPUS = source.CORPUS
GLYPH = "・"


def points_match(box, runs, native):
    x, y, _, _ = box
    points = [(x + l, y + t, x + r, y + b) for run in runs for l, t, r, b in run]
    found = []
    for point in points:
        hits = [g for g in native if g["box"] and not g["map_error"] and g["text"] == GLYPH
                and source.overlaps(point, g["box"])]
        if len(hits) != 1:
            return []
        found.append(hits[0]["index"])
    return found if len(set(found)) == len(found) else []


def compare(box, runs, recorded):
    if len(runs) != 1:
        return {"covered": False, "reason": "more-than-one-visual-run"}
    native = points_match(box, runs, recorded["native_glyphs"])
    if len(native) < 3:
        return {"covered": False, "reason": "nonunique-native-dot"}
    used = set(native)
    related = [m for m in recorded["matches"] if m["native"] in used]
    if len(native) - len(related) > 1 or len({m["line"] for m in related}) != 1:
        return {"covered": False, "reason": "source-run-not-anchored"}
    line = related[0]["line"]
    leading = 0
    spans = []
    for is_dot, consecutive in itertools.groupby(recorded["source_lines"][line]["chars"],
                                                   key=lambda c: c["text"] == GLYPH):
        n = len(list(consecutive))
        if is_dot and n == len(native):
            spans.append(range(leading, leading + n))
        leading += n
    valid = [span for span in spans if all(m["char"] in span for m in related)
             and not any(m["line"] == line and m["char"] in span and m["native"] not in used
                         for m in recorded["matches"])]
    return {"covered": len(valid) == 1, "native_points": len(native),
            "pairwise_source_anchors": len(related), "complete_source_runs": len(valid)}


def main():
    output = HERE / "source-middle-dot-runs.json"
    if output.exists():
        raise FileExistsError("既存の診断結果を上書きしない")
    scan_path = HERE / "result.json"
    earlier_path = HERE / "source-codes.json"
    scan = load(scan_path)
    known = {(r["key"], r["line_index"]): r for r in load(earlier_path)["rows"]}
    results, counts = [], Counter()
    inputs = {p.name: sha(p.read_bytes()) for p in (scan_path, earlier_path, Path(__file__), SOURCE)}
    for key in sorted({x["key"] for x in scan["geometries"] if x["key"].startswith("disaster-p")}):
        path = CORPUS / "region-repair-v9/geometry" / (key + ".json")
        region = load(CORPUS / "public/region-v9" / (key + ".json"))
        if sha(path.read_bytes()) != region["geometry_sha256"]:
            raise ValueError("保存した幾何が固定と異なる")
        inputs[key + ".json"] = sha(path.read_bytes())
        geometry = load(path)
        for row in scan["geometries"]:
            if row["key"] != key or row["previous"] != "unknown" or not row["runs"]:
                continue
            i = row["line_index"]
            data = compare(region["lines"][i]["box"], row["runs"], geometry)
            seen = known[key, i]["covered"]
            results.append({"key": key, "line_index": i, "pairwise_covered": seen, **data})
            counts["rows"] += 1
            counts["with_all_pairwise_anchors"] += seen
            counts["with_missing_origin_recovered"] += data["covered"] and not seen
            counts["combined_covered"] += data["covered"] or seen
    with output.open("x", encoding="utf-8") as stream:
        json.dump({"scope": "development-only-source-diagnosis", "inputs": inputs,
                   "counts": counts, "rows": results}, stream, ensure_ascii=False, indent=2)
    print(json.dumps(counts, ensure_ascii=False), flush=True)


if __name__ == "__main__":
    main()
