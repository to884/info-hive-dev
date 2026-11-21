"""横座標を変えた開発の二票を、既定の出典照合と同じ手順で比較する。"""

import importlib.util
from pathlib import Path

HERE = Path(__file__).resolve().parent
PREVIOUS = HERE.parent / "v33-horizontal-guide-pilot/compare.py"
spec = importlib.util.spec_from_file_location("same_pdf_proof", PREVIOUS)
base = importlib.util.module_from_spec(spec)
spec.loader.exec_module(base)


def cases(stage, root):
    plan = base.load(stage / "lock.json")
    data = base.load(stage / "result.json")
    baseline = base.load(PREVIOUS.parent / "lock.json")
    old_results = base.load(PREVIOUS.parent / "source-comparison.json")
    if (data["lock_sha256"] != base.sha(stage / "lock.json") or data["scope"] != "development-only"
            or set(data["cases"]) != set(plan["jobs"])
            or any(base.sha(Path(p)) != h for p, h in plan["files"].items())):
        raise ValueError("固定した表示と独立な読取を結び付けられない")
    rows = base.load(root / "display/selection.json")["selected"]
    frames = []
    for name, finding in data["cases"].items():
        case = name.split("/")[0]
        selected, item = plan["jobs"][name], plan["mapping"][case]
        row = rows[item["entry"]]
        old, new = baseline["jobs"][name]["request"], selected["request"]
        same = [a == b or "-coordinate-" in f for a, b, f in
                zip(old["image_sha256"], new["image_sha256"], old["images"], strict=True)]
        if old["images"] != new["images"] or not all(same) or name not in old_results["cases"]:
            raise ValueError("横座標のほかの添付を変更した可能性がある")
        if any(base.sha(Path(selected["cards"]) / f) != h
               for f, h in zip(new["images"], new["image_sha256"], strict=True)):
            raise ValueError("配布済みの画像が変わった")
        if finding["pair_result"] != "both-location-needs-source":
            continue
        if (finding["page"], finding["line_index"]) != (row["key"], row["line_index"]):
            raise ValueError("画像票が対象枠と異なる")
        vote = finding["readings"]
        checked = {"row": row, "assets": item["image_reference"], "answer": vote["pair"],
                   "coordinates": vote["coordinates"]}
        frames.append((name, checked, finding["expected"]))
    return data, frames


if __name__ == "__main__":
    base.STAGES = {"35": HERE}
    base.cases = cases
    base.main()
