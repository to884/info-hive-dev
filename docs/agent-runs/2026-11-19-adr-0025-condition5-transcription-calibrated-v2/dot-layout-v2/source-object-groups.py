"""三点リーダーの描画単位と固定画像の点を、文字の原点を仮定せずに照合する。"""

from collections import Counter
from contextlib import closing
import importlib.util
import json
import math
from pathlib import Path

HERE = Path(__file__).resolve().parent
V1 = HERE / "source-object-codes.py"
spec = importlib.util.spec_from_file_location("object_source", V1)
previous = importlib.util.module_from_spec(spec)
spec.loader.exec_module(previous)
load, sha = previous.load, previous.sha
CORPUS = previous.CORPUS


def pair_objects(commands, objects):
    paired = {}
    for i, cmd in enumerate(commands):
        eligible = [j for j, o in enumerate(objects) if cmd["font"] == o["font"]
                    and cmd["count"] == len(o["glyphs"])
                    and math.dist(cmd["matrix"], o["matrix"]) <= previous.TOLERANCE]
        if len(eligible) == 1:
            paired[i] = eligible[0]
    reuse = Counter(paired.values())
    groups = {}
    for i, j in paired.items():
        if reuse[j] != 1:
            continue
        cmd, rendered = commands[i], objects[j]
        boxes = [g["box"] for g in rendered["glyphs"]]
        if any(box is None for box in boxes):
            continue
        a, b, c, d = zip(*boxes, strict=True)
        groups[i] = {"box": [min(a), min(b), max(c), max(d)],
                     "expected_points": 3 * (cmd["count"] - 1),
                     "encoded_ellipsis_count": cmd["count"] - 1,
                     "raw_cid": cmd["raw_cid"], "cmap_sha256": cmd["cmap_sha256"],
                     "matrix": cmd["matrix"], "font": cmd["font"]}
    return groups


def associate(box, runs, groups):
    x, y, _, _ = box
    positions = [[x + l, y + t, x + r, y + b] for run in runs for l, t, r, b in run]
    assigned, missing, ambiguous = Counter(), 0, 0
    for p in positions:
        options = [i for i, obj in groups.items() if previous.source.overlaps(p, obj["box"])]
        if len(options) == 1:
            assigned[options[0]] += 1
        elif options:
            ambiguous += 1
        else:
            missing += 1
    mapping = {i: {"points": n, **groups[i]} for i, n in assigned.items()}
    return {"points": len(positions), "unmapped": missing, "ambiguous": ambiguous, "objects": mapping}


def main():
    target = HERE / "source-object-groups.json"
    if target.exists():
        raise FileExistsError("診断記録を上書きしない")
    scan_path = HERE / "result.json"
    truth_path = CORPUS / "public/defense.truth.json"
    truth = load(truth_path)
    pdf = (CORPUS / truth["file"]).read_bytes()
    if sha(pdf) != truth["pdf_sha256"]:
        raise ValueError("元のPDFのSHAと一致しない")
    diagnostics = [r for r in load(scan_path)["geometries"] if r["previous"] == "unknown"
                   and r["key"].startswith("defense-p") and r["runs"]]
    numbers = {int(r["key"].rsplit("-p", 1)[1]) for r in diagnostics}
    raw_commands = previous.commands(pdf, numbers)
    files = [scan_path, truth_path, Path(__file__), V1, previous.SOURCE]
    cases, pages = [], {}
    with previous.pdfium.PdfDocument(pdf) as document:
        for n in sorted(numbers):
            key = f"defense-p{n:04d}"
            old_geometry = CORPUS / "region-repair-v9/geometry" / (key + ".json")
            region_path = CORPUS / "public/region-v9" / (key + ".json")
            region = load(region_path)
            if sha(old_geometry.read_bytes()) != region["geometry_sha256"]:
                raise ValueError("保存した字形の幾何のSHAと違う")
            files.extend((old_geometry, region_path))
            with closing(document[n - 1]) as page:
                objects = previous.objects(page, load(old_geometry)["native_glyphs"])
            groups = pair_objects(raw_commands[n], objects)
            mapped = []
            for row in diagnostics:
                if row["key"] == key:
                    line_index = row["line_index"]
                    mapped.append({"key": key, "line_index": line_index,
                                   **associate(region["lines"][line_index]["box"], row["runs"], groups)})
            reuse = Counter(i for row in mapped for i in row["objects"])
            corroborated = 0
            for row in mapped:
                row["corroborated"] = (len(row["objects"]) == 1 and not row["unmapped"] and not row["ambiguous"]
                    and all(reuse[i] == 1 and value["points"] == value["expected_points"]
                            for i, value in row["objects"].items()))
                corroborated += row["corroborated"]
            cases.extend(mapped)
            pages[key] = {"source_commands": len(raw_commands[n]), "rendered_objects": len(objects),
                          "paired_objects": len(groups), "rows": len(mapped), "corroborated": corroborated}
    evidence = {"scope": "development-only-source-diagnosis", "pdf_sha256": sha(pdf),
                "files_sha256": {f.relative_to(HERE.parents[2]).as_posix(): sha(f.read_bytes()) for f in files},
                "pages": pages, "rows": cases}
    with target.open("x", encoding="utf-8") as stream:
        json.dump(evidence, stream, ensure_ascii=False, indent=2)
    print(json.dumps(pages, ensure_ascii=False), flush=True)


if __name__ == "__main__":
    main()
