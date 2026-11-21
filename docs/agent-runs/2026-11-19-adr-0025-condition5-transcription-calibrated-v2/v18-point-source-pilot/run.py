"""位置が確定しなかった丸印を、保存した二票と隔離描画から再検査する。"""

from collections import Counter
import importlib.util
from pathlib import Path

import numpy as np
from PIL import Image

HERE = Path(__file__).resolve().parent
PREVIOUS = HERE.parent / "v15-reference-audit"


def module(name, path):
    spec = importlib.util.spec_from_file_location(name, path)
    value = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(value)
    return value


audit = module("audited_v15", PREVIOUS / "run.py")
pilot = module("isolated_point_example", HERE.parent / "v16-point-placement-pilot/run.py")
visible = module("rounded_ink", HERE.parent / "v11-visible-source-pilot/round_overlap.py")
ref = audit.reference
out = pilot.corpus / "reference-v18-point-source-pilot"


def candidates(box, gray, coordinates):
    ordinary = {b[0] for b in pilot.groups(gray, box).get("round", [])}
    divided = set(visible.marks(gray, box))
    selected = []
    for readings in coordinates:
        near = {ink for ink in ordinary | divided if max(abs((ink[0] + ink[2]) / 2 - box[0] - v) for v in readings) <= 10}
        ideas = sorted(near)
        if len(ideas) == 2:
            a, b = ideas
            if all(abs(u - v) <= 1 for u, v in zip(a, b, strict=True)):
                ideas = [max(ideas, key=lambda k: (k[2] - k[0]) * (k[3] - k[1]))]
        if len(ideas) != 1:
            raise ValueError("二票と二つの画素測定から一つの丸印に絞れない")
        selected.append(ideas[0])
    if len(set(selected)) != len(selected):
        raise ValueError("同じ点が複数の記号に重なった")
    return selected


def rows():
    ref.OUT, ref.DELIVERY = audit.OUT, audit.OUT / "delivery"
    ref.PACKS, ref.READ = ref.DELIVERY / "packages.json", ref.DELIVERY / "received.json"
    ref.START, ref.receive = ref.DELIVERY / "delivery-started.json", audit.receive
    final = audit.load(PREVIOUS / "result.json")
    proof = audit.OUT / "reference-evidence.json"
    if audit.sha(proof) != final["reference_sha256"]:
        raise ValueError("正式な監査の照合が異なる")
    checked, _ = ref.cases()
    evidence = audit.load(proof)
    result = []
    for case in checked:
        row = case["row"]
        address = f"{row['key']}/{row['line_index']}"
        if evidence[address]["evidence"] == "source-location-not-proven":
            result.append(case)
    if len(result) != final["sources"]["source-location-not-proven"]:
        raise ValueError("保留として確定した全行と一致しない")
    return result


def main():
    if out.exists():
        raise FileExistsError("保存した出典の開発結果を上書きしない")
    tested = []
    catalog = audit.prior.old.lookup()[1]
    docs = {}
    for case in rows():
        row, marking = case["row"], case["answer"]["text"]
        key, i = row["key"], row["line_index"]
        matches = list(ref.MARK.finditer(marking))
        meta = {"page": key, "line_index": i, "marks": len(matches), "known": any(v["known"] for v in row["targets"].values())}
        if row["allocation_axis"] != "x" or not matches or any(m[1] != "round" for m in matches):
            tested.append({**meta, "outcome": "outside-round-only"})
            continue
        flags = case["assets"]["sha"]
        filename, digest, page_no = catalog[key]
        if filename not in docs:
            docs[filename] = (pilot.corpus / filename).read_bytes()
        blob = docs[filename]
        png = pilot.corpus / "probe-v4/png" / (key + ".png")
        if pilot.isolation.layer.sha(blob) != digest or digest != flags["pdf_sha256"] or audit.sha(png) != flags["150_dpi"]:
            raise ValueError("固定された元PDFまたは固定150 DPIが違う")
        with Image.open(png) as im:
            gray, rgb = np.array(im.convert("L")), np.array(im.convert("RGB"))
        if not np.array_equal(pilot.isolation.layer.render_pixels(blob, page_no - 1), rgb):
            raise ValueError("固定150 DPIが元PDFに対応しない")
        try:
            blocks = candidates(row["box"], gray, case["coordinates"])
            relation = [pilot.isolate(blob, page_no, b, rgb, flags) for b in blocks]
        except (ValueError, IndexError, KeyError, TypeError) as error:
            tested.append({**meta, "outcome": "insufficient", "cause": str(error)[:100]})
            continue
        points = iter(relation)
        answer = ref.MARK.sub(lambda _: chr(int(next(points)["codepoint"], 16)), marking)
        compared = {k: ref.NORMALIZE(v["text"]) == ref.NORMALIZE(answer) for k, v in row["targets"].items() if v["known"]}
        tested.append({**meta, "outcome": "source-confirmed", "evidence": relation, "same_as_existing_label": compared})
        print(key, i, compared, flush=True)
    out.mkdir()
    paths = (Path(__file__), Path(pilot.__file__), Path(visible.__file__), PREVIOUS / "result.json", audit.OUT / "reference-evidence.json")
    result = {"scope": "development-only", "inputs": {str(p): audit.sha(p) for p in paths},
              "counts": Counter(record["outcome"] for record in tested), "cases": tested}
    audit.save_once(HERE / "result.json", audit.encoded(result))
    print(result["counts"], flush=True)


if __name__ == "__main__":
    main()
