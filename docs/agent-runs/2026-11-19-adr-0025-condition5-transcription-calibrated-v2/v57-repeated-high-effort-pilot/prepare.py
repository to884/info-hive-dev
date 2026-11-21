"""保存した同じ18回分の開発依頼を、highの新規セッションで読む。"""

import importlib.util
from pathlib import Path
import sys

HERE = Path(__file__).resolve().parent
BASE = HERE.parent / "v56-repeated-kana-control-pilot/prepare.py"
spec = importlib.util.spec_from_file_location("repeat_higher_effort", BASE)
earlier = importlib.util.module_from_spec(spec)
spec.loader.exec_module(earlier)
pilot = earlier.pilot
OLD_OUT, OLD_LOCK = pilot.OUT, pilot.LOCK
pilot.HERE = HERE
pilot.OUT = OLD_OUT.with_name("reference-v57-repeated-high-effort-pilot")
pilot.LOCK, pilot.RESULT = HERE / "lock.json", HERE / "result.json"
medium = pilot.audit.readers.command
outcome = pilot.outcome


def high(exe, folder, names, model, role, cwd):
    command = medium(exe, folder, names, model, role, cwd)
    if role == "gpt":
        switch = command.index('model_reasoning_effort="medium"')
        command[switch] = 'model_reasoning_effort="high"'
    else:
        switch = command.index("--effort") + 1
        if command[switch] != "medium":
            raise ValueError("読取の労力の元の版が異なる")
        command[switch] = "high"
    return command


def produced(*args, **kwargs):
    pilot.audit.readers.command = high
    try:
        return outcome(*args, **kwargs)
    finally:
        pilot.audit.readers.command = medium


def snapshot():
    audit = pilot.audit
    plan = audit.load(OLD_LOCK)
    if any(audit.sha(Path(f)) != h for f, h in plan["files"].items()):
        raise ValueError("固定した比較の18回の依頼が変わった")
    source = OLD_OUT / "display/selection.json"
    position = pilot.OUT / "display/selection.json"
    position.parent.mkdir(parents=True)
    audit.save_once(position, source.read_bytes())
    for job in plan["jobs"].values():
        images = job["request"]["images"]
        if [audit.sha(Path(job["cards"]) / f) for f in images] != job["request"]["image_sha256"]:
            raise ValueError("画像の画素が元の開発依頼から変化")
    pilot.SAMPLES = audit.load(position)["selected"]
    files = (Path(__file__), BASE, HERE / "protocol.md", OLD_LOCK, source, position)
    return {**plan, "files": plan["files"] | {str(p): audit.sha(p) for p in files}}


if __name__ == "__main__":
    if len(sys.argv) > 1 and sys.argv[1] == "compare":
        del sys.argv[1]
        pilot.outcome = produced
        earlier.earlier.HERE = HERE
        earlier.earlier.compare()
    else:
        pilot.audit.readers.command = high
        pilot.snapshot = snapshot
        pilot.main()
