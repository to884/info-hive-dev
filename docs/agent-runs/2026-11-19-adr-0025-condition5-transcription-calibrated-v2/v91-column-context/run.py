"""隣の列とのつながりを確認する指示を、列順と曖昧な横書きの開発画像で比較する。"""

import argparse
from collections import Counter, defaultdict
from importlib.util import module_from_spec, spec_from_file_location
from pathlib import Path
import sys

HERE = Path(__file__).resolve().parent
STAGES = HERE.parent
BASE = STAGES / "v87-independent-column-order-pilot"
AMBIGUOUS = STAGES / "v79-order-repeat-pilot"
spec = spec_from_file_location("separate_image_columns", BASE / "run.py")
columns = module_from_spec(spec)
spec.loader.exec_module(columns)
core, launch, pilot, grade = columns.core, columns.launch, columns.pilot, columns.grade
pilot.HERE = HERE
pilot.OUT = core.CORPUS / "reference-v91-column-context"
pilot.LOCK, pilot.RESULT = HERE / "lock.json", HERE / "pair.json"

CONTEXT = (
    "最初に『行と列のつながり』の広い画像で、枠の上下の近い文字も観察します。"
    "枠内の字から同じ横位置で上または下に続く字が周囲にあるときは、縦書きを支持する配置として確認します。"
    "周囲で文字が横方向に続くまとまりは横書きを支持します。"
    "枠の所属を測る割当軸の向きと、紙面の書字方向は別に判定します。"
    "一字とする前に枠の左右の端にかかる字の全体も確認します。"
    "枠外の文字は向きを確かめるためだけに見て、転記しません。"
)


def snapshot():
    files = {Path(__file__), HERE / "protocol.md", Path(columns.__file__), Path(pilot.__file__), Path(grade.__file__)}
    selected, jobs, layout = [], {}, {}
    for directory, corpus, study in (
        (BASE, "reference-v87-independent-column-order-pilot", "87"),
        (AMBIGUOUS, "reference-v79-order-repeat-pilot", "79"),
    ):
        lock = directory / "lock.json"
        selection = core.CORPUS / corpus / "display/selection.json"
        study_plan = core.load(lock)
        if any(core.sha(Path(p)) != h for p, h in study_plan["files"].items()):
            raise ValueError("前の開発画像の固定資料が変わっている")
        files.update((lock, selection))
        rows = core.load(selection)["selected"]
        for name, bound in study_plan["mapping"].items():
            group = bound["category"]
            if study == "79" and (not name.endswith("-r1") or not group.startswith("horizontal")):
                continue
            key = f"{study}-{name}"
            entry = study_plan["jobs"][f"{name}/" + ("new" if study == "87" else "old")]
            req = entry["request"]
            folder = Path(entry["cards"])
            if [core.sha(folder / f) for f in req["images"]] != req["image_sha256"]:
                raise ValueError("前の開発で凍結した添付と異なる")
            files.update(folder / f for f in req["images"])
            old = req["prompt"]
            if study == "79":
                if old.count(launch.neutral.SHORT) != 1:
                    raise ValueError("列順の案内を一意に置き換えられない")
                old = old.replace(launch.neutral.SHORT, columns.GUIDE, 1)
                group = "ambiguous-" + group
            if old.count(columns.GUIDE) != 1:
                raise ValueError("旧と新の両方で方向と列を回答できない")
            layout[key] = {"entry": len(selected), "category": group, "partitions": []}
            selected.append(rows[bound["entry"]])
            for version, extra in (("old", ""), ("new", CONTEXT)):
                prompt = old.replace(columns.GUIDE, extra + columns.GUIDE, 1)
                jobs[f"{key}/{version}"] = {**entry, "request": {**req, "prompt": prompt}}
    if len(selected) != 27:
        raise ValueError("列順7行と対照20行をすべて固定できない")
    output = pilot.OUT / "display/selection.json"
    output.parent.mkdir(parents=True)
    core.save_once(output, core.encoded({"selected": selected}))
    files.add(output)
    pilot.SAMPLES = selected
    return {"jobs": jobs, "mapping": layout, "files": core.load(core.LOCK)["inputs"] |
            {str(path): core.sha(path) for path in sorted(files)}}


def score(args):
    locked = core.load(pilot.LOCK)
    if core.sha(pilot.LOCK) != args.sha256 or any(core.sha(Path(p)) != h for p, h in locked["files"].items()):
        raise ValueError("固定画像と依頼の来歴が異なる")
    selection = core.load(pilot.OUT / "display/selection.json")["selected"]
    runtimes = pilot.audit.delivery.runtime({"gpt": args.codex, "claude": args.claude})
    seen, output = set(), {}
    totals = defaultdict(lambda: defaultdict(Counter))
    for task, job in locked["jobs"].items():
        name, arm = task.split("/")
        bound = locked["mapping"][name]
        row = selection[bound["entry"]]
        ident, = job["request"]["ids"]
        raw, sessions = {}, {}
        for model in ("gpt", "claude"):
            history = pilot.outcome(args.sha256, task, model, job, runtimes[model])
            if not history or history[-1]["availability"] != "received" or history[-1]["session"] in seen:
                raise ValueError("異系統・新規セッションから独立した二票がそろわない")
            last = history[-1]
            seen.add(last["session"])
            raw[model] = last["answers"][ident]
            sessions[model] = last["session"]
        sol, opus = map(columns.parts, raw.values())
        reading = columns.compiled(sol) if sol == opus else core.ref.UNKNOWN
        expected = core.ref.NORMALIZE(row["effective"])
        verdict = grade.verdict(core.ref, reading, expected)
        totals[bound["category"]][arm][verdict] += 1
        output[task] = {"group": bound["category"], "page": row["key"], "line_index": row["line_index"],
                        "raw": raw, "sessions": sessions, "structure": [sol, opus], "expected": expected, "state": verdict}
    core.save_once(HERE / "comparison.json", core.encoded({"scope":"development-only","lock_sha256":args.sha256,
                                                          "counts":totals,"cases":output}))
    print({g:{a:dict(v) for a,v in arms.items()} for g,arms in totals.items()}, flush=True)


if __name__ == "__main__":
    launch.configure()
    if len(sys.argv) > 1 and sys.argv[1] == "compare":
        parser = argparse.ArgumentParser(description=__doc__)
        parser.add_argument("action", choices=("compare",))
        parser.add_argument("--sha256", required=True)
        parser.add_argument("--codex", required=True, type=Path)
        parser.add_argument("--claude", required=True, type=Path)
        score(parser.parse_args())
    else:
        pilot.snapshot = snapshot
        pilot.main()
