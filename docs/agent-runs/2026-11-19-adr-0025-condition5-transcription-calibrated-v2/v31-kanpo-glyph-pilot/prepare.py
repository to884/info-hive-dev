"""同じ固定画像を使い、混同しやすい字の部品を区別して転記する。"""

import importlib.util
from pathlib import Path

HERE = Path(__file__).resolve().parent
BASE = HERE.parent / "v24-physical-transcription-pilot/run.py"
PREVIOUS = HERE.parent / "v26-kanpo-name-candidate"
spec = importlib.util.spec_from_file_location("vertical_glyph_transcription", BASE)
pilot = importlib.util.module_from_spec(spec)
spec.loader.exec_module(pilot)
pilot.HERE = HERE
old = pilot.OUT.with_name("reference-v26-kanpo-name-candidate")
pilot.OUT = pilot.OUT.with_name("reference-v31-kanpo-glyph-pilot")
pilot.LOCK, pilot.RESULT = HERE / "lock.json", HERE / "result.json"
GUIDE = (
    "読める候補を増やすための部品の例です。枠内に該当する筆画が見える場合だけ使います。"
    "山の右が上に大、下に可なら「崎」、上に立の形、下に可なら「﨑」です。"
    "台（ムと口）の左が三水なら「治」、左から下へのしんにょうなら「迨」です。"
    "しんにょうの内側が𠂤（小さな箱を重ねた形）なら「追」、卣なら「逌」です。"
    "臼に似た両側と下が八の字に、独立した横画と縦画2本の草冠があれば「藇」、草冠がなければ「與」を確かめます。"
    "中央に車があれば「輿」と区別します。例にあっても画素にない字は書かず、一つずつ実際の筆画と照らします。"
)


def snapshot():
    audit = pilot.audit
    earlier = PREVIOUS / "lock.json"
    plan = audit.load(earlier)
    if any(audit.sha(Path(p)) != h for p, h in plan["files"].items()):
        raise ValueError("前の比較で固定した添付の来歴が異なる")
    selection = old / "display/selection.json"
    selected = audit.load(selection)["selected"]
    pilot.SAMPLES = {(r["key"], r["line_index"]): r["allocation_axis"] for r in selected}
    current = pilot.OUT / "display/selection.json"
    current.parent.mkdir(parents=True)
    audit.save_once(current, selection.read_bytes())
    jobs = {}
    for key, task in plan["jobs"].items():
        prompt = task["request"]["prompt"]
        start, delimiter, end = prompt.partition(audit.packets.FORMAT)
        if not delimiter:
            raise ValueError("前に固定した回答形式を確認できない")
        jobs[key] = {**task, "request": {**task["request"], "prompt": start + GUIDE + delimiter + end}}
    paths = (Path(__file__), BASE, HERE / "protocol.md", earlier, selection, current)
    return {"jobs": jobs, "mapping": plan["mapping"],
            "files": plan["files"] | {str(p): audit.sha(p) for p in paths}}


if __name__ == "__main__":
    pilot.snapshot = snapshot
    pilot.main()
