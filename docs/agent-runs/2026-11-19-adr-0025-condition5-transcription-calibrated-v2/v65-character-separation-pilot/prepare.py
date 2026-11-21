"""既存の表示を変えずに、一字ずつ確認する指示を加える。"""

import importlib.util
from pathlib import Path
import sys

HERE = Path(__file__).resolve().parent
HELPER = HERE.parent / "v63-contiguous-pixel-strips-pilot/prepare.py"
sys.path.insert(0, str(HELPER.parent))
spec = importlib.util.spec_from_file_location("character_separation_development", HELPER)
trial = importlib.util.module_from_spec(spec)
spec.loader.exec_module(trial)
core, audit, pilot = trial.core, trial.audit, trial.pilot
pilot.HERE = trial.HERE = HERE
pilot.OUT = core.CORPUS / "reference-v65-character-separation-pilot"
pilot.LOCK, pilot.RESULT = HERE / "lock.json", HERE / "result.json"

CHECK = (
    "所属を確認できた字を最初から最後まで、一字ずつ隣の字との境目を確かめて、"
    "text欄では字と字の間に半角の空白を一つずつ置きます。たとえば三字なら「日 本 語」の形です。"
    "同じ一字に付く濁点や仮名の曲線は分けません。"
    "同じ字を再び写さず、読み慣れた語に直さず、先頭・途中・末尾の見える一字を飛ばしません。"
    "曖昧な点や点列の ⟦ ⟧ の中は途中に空白を入れず、一つの印を一字と同じように扱います。"
)


def snapshot():
    previous = trial.old.pilot
    table = previous.OUT / "display/selection.json"
    old = core.load(previous.LOCK)
    saved = trial.PREVIOUS / "comparison.json"
    grades = core.load(saved)
    if (grades["lock_sha256"] != core.sha(previous.LOCK)
            or any(core.sha(Path(f)) != h for f, h in old["files"].items())):
        raise ValueError("指示を比較する固定画像と以前の原票が異なる")
    rows = core.load(table)["selected"]
    selected, mapping, jobs = [], {}, {}
    for name in trial.subset(old, rows, grades):
        tag = name.split("/")[0]
        entry = old["mapping"][tag]
        job = old["jobs"][name]
        request, directory = job["request"], Path(job["cards"])
        if [core.sha(directory / filename) for filename in request["images"]] != request["image_sha256"]:
            raise ValueError("指示だけを変える比較で元の画像が異なる")
        prefix, form, ending = request["prompt"].partition(audit.packets.FORMAT)
        if not form or entry["partitions"]:
            raise ValueError("同じ全文の形式で転記比較できない")
        jobs[name] = {**job, "request": {**request, "prompt": prefix + CHECK + form + ending}}
        mapping[tag] = {**entry, "entry": len(selected)}
        selected.append(rows[entry["entry"]])
    new = pilot.OUT / "display/selection.json"
    new.parent.mkdir(parents=True)
    core.save_once(new, core.encoded({"selected": selected}))
    sources = (Path(__file__), HELPER, HERE / "protocol.md", previous.LOCK, table, saved, new)
    pilot.SAMPLES = selected
    return {"jobs": jobs, "mapping": mapping, "files": {str(f): core.sha(f) for f in sources}}


if __name__ == "__main__":
    if len(sys.argv) > 1 and sys.argv[1] == "compare":
        trial.compare()
    else:
        pilot.snapshot = snapshot
        pilot.main()
