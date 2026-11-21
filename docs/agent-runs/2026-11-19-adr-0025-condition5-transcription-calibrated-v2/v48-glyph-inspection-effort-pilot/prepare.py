"""同じ規則・字形資料で考える量だけを変え、難しい字を読む。"""

import importlib.util
from pathlib import Path

HERE = Path(__file__).resolve().parent
BASE = HERE.parent / "v42-glyph-reference-pilot/prepare.py"
spec = importlib.util.spec_from_file_location("glyph_example_baseline", BASE)
old = importlib.util.module_from_spec(spec)
spec.loader.exec_module(old)
pilot = old.pilot
pilot.HERE = HERE
private = pilot.OUT
pilot.OUT = pilot.OUT.with_name("reference-v48-glyph-inspection-effort-pilot")
pilot.LOCK, pilot.RESULT = HERE / "lock.json", HERE / "result.json"
initial = pilot.audit.readers.command


def command(exe, folder, names, model, role, cwd):
    argv = initial(exe, folder, names, model, role, cwd)
    if role == "gpt":
        index = argv.index('model_reasoning_effort="medium"')
        argv[index] = 'model_reasoning_effort="high"'
    else:
        index = argv.index("--effort") + 1
        if argv[index] != "medium":
            raise ValueError("以前のモデルのeffortが異なる")
        argv[index] = "high"
    return argv


def snapshot():
    audit = pilot.audit
    source = BASE.parent / "lock.json"
    old_plan = audit.load(source)
    if any(audit.sha(Path(p)) != h for p, h in old_plan["files"].items()):
        raise ValueError("固定済みの字形・指示と異なる")
    original = private / "display/selection.json"
    data = audit.load(original)["selected"]
    current = pilot.OUT / "display/selection.json"
    current.parent.mkdir(parents=True)
    checks, jobs, rows = {}, {}, []
    for name, task in old_plan["jobs"].items():
        label = name.split("/")[0]
        item = old_plan["mapping"][label]
        row = data[item["entry"]]
        if row["effective"] is None:
            continue
        checks[label] = {**item, "entry": len(rows)}
        jobs[name] = task
        rows.append(row)
    audit.save_once(current, audit.encoded({"selected": rows}))
    pilot.SAMPLES = rows
    files = (Path(__file__), HERE / "protocol.md", BASE, source, current, original)
    return {"jobs": jobs, "mapping": checks,
            "files": old_plan["files"] | {str(p): audit.sha(p) for p in files}}


if __name__ == "__main__":
    pilot.audit.readers.command = command
    pilot.snapshot = snapshot
    pilot.main()
