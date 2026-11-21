"""開発の二票を、元の固定画像と許可された出典で確認する。"""

import importlib.util
from pathlib import Path

HERE = Path(__file__).resolve().parent
BASE = HERE.parent / "v33-horizontal-guide-pilot/compare.py"
spec = importlib.util.spec_from_file_location("bounded_image_source_comparison", BASE)
previous = importlib.util.module_from_spec(spec)
spec.loader.exec_module(previous)


def cases(stage, root):
    plan = previous.load(stage / "lock.json")
    data = previous.load(stage / "result.json")
    if (data["lock_sha256"] != previous.sha(stage / "lock.json") or data["scope"] != "development-only"
            or set(data["cases"]) != set(plan["jobs"])
            or any(previous.sha(Path(p)) != h for p, h in plan["files"].items())):
        raise ValueError("事前固定の画像と二票の来歴を確認できない")
    rows = previous.load(root / "display/selection.json")["selected"]
    confirmed = []
    for label, item in data["cases"].items():
        if item["pair_result"] != "both-location-needs-source":
            continue
        rowinfo = plan["mapping"][label.split("/")[0]]
        row = rows[rowinfo["entry"]]
        job, vote = plan["jobs"][label], item["readings"]
        cards = Path(job["cards"])
        req = job["request"]
        if any(previous.sha(cards / filename) != h for filename, h in zip(req["images"], req["image_sha256"], strict=True)):
            raise ValueError("二票に渡した添付が異なる")
        binding = rowinfo.get("image_reference")
        if binding is None:
            catalog = previous.load(cards.parent.parent / "packages.json")
            ident, = req["ids"]
            binding = catalog["packs"][cards.name]["mapping"][ident]["image_reference"]
        if (item["page"], item["line_index"]) != (row["key"], row["line_index"]):
            raise ValueError("画像票の対象枠が同じであることを確認できない")
        confirmed.append((label, {"row": row, "assets": binding, "answer": vote["pair"],
                                  "coordinates": vote["coordinates"]}, item["expected"]))
    return data, confirmed


if __name__ == "__main__":
    previous.STAGES = {"37": HERE}
    previous.cases = cases
    previous.main()
