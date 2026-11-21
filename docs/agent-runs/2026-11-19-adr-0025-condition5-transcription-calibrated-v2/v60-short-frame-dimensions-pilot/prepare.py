"""短枠の二案を、固定画像の寸法だけで使い分ける。"""

import importlib.util
from pathlib import Path
import sys

HERE = Path(__file__).resolve().parent
BASE = HERE.parent / "v53-short-column-order-pilot/prepare.py"
spec = importlib.util.spec_from_file_location("short_frame_layout_by_dimensions", BASE)
earlier = importlib.util.module_from_spec(spec)
spec.loader.exec_module(earlier)
pilot = earlier.pilot
pilot.HERE = earlier.HERE = HERE
pilot.OUT = pilot.OUT.with_name("reference-v60-short-frame-dimensions-pilot")
pilot.LOCK, pilot.RESULT = HERE / "lock.json", HERE / "result.json"
earlier.SAMPLES = earlier.SAMPLES | {
    ("kanpo1828-p1-p0001", 24): "new-control-single-one",
    ("kanpo1828-p1-p0001", 177): "new-control-single-two",
    ("kanpo1827-p2-p0001", 370): "new-control-short-vertical",
    ("disaster-p0079", 211): "new-control-number",
    ("defense-p0500", 64): "new-control-latin",
}


def snapshot():
    plan = earlier.snapshot()
    audit = pilot.audit
    table = pilot.OUT / "display/selection.json"
    rows = audit.load(table)["selected"]
    chosen = {}
    for tag, marker in plan["mapping"].items():
        row = rows[marker["entry"]]
        w, h = row["box"][2:]
        detailed = w <= 30 and h <= 20
        name = f"{tag}/" + ("visual" if detailed else "plain")
        packet = plan["jobs"][name]
        cards = packet["request"]["images"]
        if detailed and (not any("-short-context.png" in f for f in cards) or not any("-quarter-turns.png" in f for f in cards)):
            raise ValueError("一字の枠に必要な固定画像の表示がそろわない")
        chosen[name] = packet
    if len(chosen) != 17 or sum(name.endswith("/visual") for name in chosen) != 6:
        raise ValueError("比較に使う二つの寸法帯がそろわない")
    plan["jobs"] = chosen
    plan["files"][str(Path(__file__))] = audit.sha(Path(__file__))
    return plan


if __name__ == "__main__":
    if len(sys.argv) > 1 and sys.argv[1] == "compare":
        del sys.argv[1]
        helper = BASE.parent.parent / "v50-reading-orientation-pilot/compare.py"
        spec = importlib.util.spec_from_file_location("fixed_short_frame_comparison", helper)
        report = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(report)
        report.HERE, report.pilot = HERE, pilot
        report.main()
    else:
        pilot.snapshot = snapshot
        pilot.main()
