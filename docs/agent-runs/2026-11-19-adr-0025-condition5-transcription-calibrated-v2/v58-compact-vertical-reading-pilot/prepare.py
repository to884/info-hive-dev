"""既存の固定表示から、縦列を読むための少数の画像を選ぶ。"""

import importlib.util
from pathlib import Path
import re
import sys

HERE = Path(__file__).resolve().parent
BASE = HERE.parent / "v51-reading-physical-instructions-pilot/prepare.py"
spec = importlib.util.spec_from_file_location("compact_vertical_delivery", BASE)
earlier = importlib.util.module_from_spec(spec)
spec.loader.exec_module(earlier)
pilot = earlier.pilot
OLD_OUT, OLD_LOCK = pilot.OUT, pilot.LOCK
pilot.HERE = HERE
pilot.OUT = OLD_OUT.with_name("reference-v58-compact-vertical-reading-pilot")
pilot.LOCK, pilot.RESULT = HERE / "lock.json", HERE / "result.json"
GUIDE = (
    "固定150 DPIと450 DPIの、同じ一つの縦の枠から読んでください。枠の中の字を上から下の順に写し、"
    "元の字の異体字、仮名の大小、筆画、括弧もそのまま書きます。隣の列の字を入れません。"
    "上下のインクの長さが半分以上枠内にあり、左右の中心も元の枠内にある字だけを写します。"
    "『列の字形』は元と同じ画素です。区間の上から順に確認し、同じ字の重なりは一度だけ写します。"
    "字形と所属を確かめ、空の枠には空文字、判読できない枠には指定の未決定を返してください。"
)
TURN = "横倒しの字だけ90度の表示で読みます。所属と順序は元の向きで確認してください。"


def snapshot():
    audit = pilot.audit
    plan = audit.load(OLD_LOCK)
    if any(audit.sha(Path(p)) != h for p, h in plan["files"].items()):
        raise ValueError("以前と同じ固定表示を確認できない")
    table = OLD_OUT / "display/selection.json"
    existing = audit.load(table)["selected"]
    rows, mapping, jobs = [], {}, {}
    for tag, item in plan["mapping"].items():
        row = existing[item["entry"]]
        if row["allocation_axis"] != "y":
            continue
        saved = plan["jobs"][tag + "/new"]
        request = saved["request"]
        label, = request["ids"]
        names = [str(name) for name in request["images"] if (
            re.fullmatch(re.escape(label) + r"-[0-9]+\.png", name)
            or any(s in name for s in ("-edge-", "-column-shapes-", "-turn-preview")))]
        whole = [name for name in request["images"] if re.fullmatch(re.escape(label) + r"-[0-9]+\.png", name)]
        pairs = dict(zip(request["images"], request["image_sha256"], strict=True))
        if not whole or not set(whole) <= set(names) or not any("-column-shapes-" in n for n in names):
            raise ValueError("元の全区間と列の字形を保持できない")
        if any(audit.sha(Path(saved["cards"]) / name) != pairs[name] for name in names):
            raise ValueError("再配布する表示の画素が変わった")
        _, sep, answer = request["prompt"].partition(audit.packets.FORMAT)
        if not sep:
            raise ValueError("固定した回答形式と異なる")
        turn = TURN if any("-turn-preview" in name for name in names) else ""
        jobs[tag + "/new"] = {**saved, "request": {**request, "images": names,
            "image_sha256": [pairs[name] for name in names], "prompt": label + "。" + GUIDE + turn + sep + answer}}
        mapping[tag] = {**item, "entry": len(rows)}
        rows.append(row)
    if len(rows) != 10:
        raise ValueError("同じ縦軸の固定10行が揃わない")
    target = pilot.OUT / "display/selection.json"
    target.parent.mkdir(parents=True)
    audit.save_once(target, audit.encoded({"selected": rows}))
    positions = Path(__file__), BASE, HERE / "protocol.md", OLD_LOCK, table, target
    pilot.SAMPLES = rows
    return {"jobs": jobs, "mapping": mapping, "files": plan["files"] | {str(p): audit.sha(p) for p in positions}}


if __name__ == "__main__":
    if len(sys.argv) > 1 and sys.argv[1] == "compare":
        del sys.argv[1]
        earlier.HERE = HERE
        earlier.compare()
    else:
        pilot.snapshot = snapshot
        pilot.main()
