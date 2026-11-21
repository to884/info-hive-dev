"""v50で固定した全画像を再利用し、読取指示だけを変える。"""

import importlib.util
from pathlib import Path
import sys

HERE = Path(__file__).resolve().parent
BASE = HERE.parent / "v50-reading-orientation-pilot/prepare.py"
spec = importlib.util.spec_from_file_location("fixed_views_and_adjusted_instructions", BASE)
previous = importlib.util.module_from_spec(spec)
spec.loader.exec_module(previous)
pilot = previous.pilot
BASE_OUT, BASE_LOCK = pilot.OUT, pilot.LOCK
pilot.HERE = HERE
pilot.OUT = BASE_OUT.with_name("reference-v51-reading-physical-instructions-pilot")
pilot.LOCK, pilot.RESULT = HERE / "lock.json", HERE / "result.json"
OLD_CIRCLE = "450 DPIで内側に白または地色の穴を持つ輪は、小さくても「。」です。"
CIRCLE = (
    "横書きで字より小さく下に寄り、内側に白または地色の穴を持つ輪は「。」です。"
    "本文と同じくらいの高さで行頭にある輪は、字の中央での大きさと位置を確認し、小さい句点に変えません。"
)
HORIZONTAL = (
    "上下の二本の横画が同じ列の一字を作る場合は、両端を含めた字の中心で所属を確かめます。"
    "枠内にある下の横画だけを別の一字として追加しません。各画は帯として別々に表示されることがあります。"
)
VERTICAL = (
    "「っ」と「つ」などは、同じ列の普通の仮名と比べて、文字の輪郭の大きさと位置で決めます。"
    "読みやすい表記に置き換えません。字体の確認では、隣の字や隣の列の画を一字の部品に取り込みません。"
)


def snapshot():
    audit = pilot.audit
    plan = audit.load(BASE_LOCK)
    if any(audit.sha(Path(p)) != h for p, h in plan["files"].items()):
        raise ValueError("横軸・縦軸の固定画素の来歴が変化")
    original = BASE_OUT / "display/selection.json"
    rows = audit.load(original)["selected"]
    jobs = {}
    for name, job in plan["jobs"].items():
        item = plan["mapping"][name.split("/")[0]]
        row = rows[item["entry"]]
        request = job["request"]
        cards = Path(job["cards"])
        if [audit.sha(cards / f) for f in request["images"]] != request["image_sha256"]:
            raise ValueError("以前に付けた固定画像が異なる")
        guide, form, close = request["prompt"].partition(audit.packets.FORMAT)
        if not form:
            raise ValueError("固定した回答形式を再現できない")
        if row["allocation_axis"] == "x":
            if guide.count(OLD_CIRCLE) != 1:
                raise ValueError("固定の句点の指示が一つに定まらない")
            guide = guide.replace(OLD_CIRCLE, CIRCLE) + HORIZONTAL
        else:
            guide += VERTICAL
        updated = {**request, "prompt": guide + form + close}
        jobs[name] = {**job, "request": updated}
    display = pilot.OUT / "display"
    display.mkdir(parents=True)
    selection = display / "selection.json"
    audit.save_once(selection, original.read_bytes())
    pins = {str(p): audit.sha(p) for p in (Path(__file__), HERE / "protocol.md", BASE, BASE_LOCK, original, selection)}
    pilot.SAMPLES = rows
    return {"jobs": jobs, "mapping": plan["mapping"], "files": plan["files"] | pins}


def compare():
    helper = HERE.parent / "v50-reading-orientation-pilot/compare.py"
    spec = importlib.util.spec_from_file_location("compare_adjusted_instructions", helper)
    report = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(report)
    report.HERE, report.pilot = HERE, pilot
    report.main()


if __name__ == "__main__":
    if len(sys.argv) > 1 and sys.argv[1] == "compare":
        del sys.argv[1]
        compare()
    else:
        pilot.snapshot = snapshot
        pilot.main()
