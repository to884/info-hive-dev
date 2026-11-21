"""固定した短い枠の画像で、列順を先に確認する指示を比較する。"""

from collections import defaultdict
from hashlib import sha256
from importlib.util import module_from_spec, spec_from_file_location
from pathlib import Path
import sys

HERE = Path(__file__).resolve().parent
effort = HERE.parent / "v71-audit-effort-pilot"
spec = spec_from_file_location("effort_for_order_pilot", effort / "run.py")
fixed = module_from_spec(spec)
spec.loader.exec_module(fixed)
core, launch, pilot, grade = fixed.core, fixed.launch, fixed.pilot, fixed.judge
pilot.HERE = HERE
pilot.OUT = core.CORPUS / "reference-v72-short-frame-order-pilot"
pilot.LOCK, pilot.RESULT = HERE / "lock.json", HERE / "pair.json"
pilot.audit.readers.command = fixed.high

GUIDE = (
    "文字を転記する前に『行と列のつながり』で、枠の上と下へ続く字の並びを確認します。"
    "元の紙面の実際の行または列を使って読む順序を決めます。"
    "上下に字が連なる複数の縦列を枠が横切る場合は、枠に字が二つだけでも、右の列から左の列へ移ります。"
    "同じ縦列では上から下へ進みます。元の紙面で一つの横書きの行なら左から右へ進みます。"
    "枠への所属を個々の字で確かめ、所属する字だけを決めた順に連結します。"
    "枠の外の字や、列の目印と区切りを転記に含めません。順序を決められない場合は既定の判読不能の形式を使います。"
)
AUDIT = HERE.parent / "v64-reference-audit"


def snapshot():
    core.verify_methods()
    result_path, diagnosis_path = (AUDIT / f"{n}.json" for n in ("result", "diagnosis"))
    result, diagnosis = core.load(result_path), core.load(diagnosis_path)
    if diagnosis["result_sha256"] != core.sha(result_path):
        raise ValueError("監査と行別診断が一致しない")
    issues = {(r["page"], r["line_index"]) for r in diagnosis["issues"] if r["reason"] == "reading-order"}
    if len(issues) != 7:
        raise ValueError("列順で割れた7行がそろわない")
    receipt = fixed.delivery / "received.json"
    evidence = launch.OUT / "reference-evidence.json"
    if result["receipts_sha256"] != core.sha(receipt) or result["reference_sha256"] != core.sha(evidence):
        raise ValueError("固定監査の原票と判定が異なる")
    refs = core.load(evidence)
    original, manifest = launch.OUT / "selection.json", fixed.delivery / "packages.json"
    rows = core.load(original)["selected"]
    matches, controls = {}, defaultdict(list)
    for pack, batch in core.load(manifest)["packs"].items():
        (label, binding), = batch["mapping"].items()
        row = rows[binding["entry"]]
        if not launch.render.short_frame(row) or f"{label}-layout.png" not in batch["request"]["images"]:
            continue
        identity = fixed.key(row)
        known = {core.ref.NORMALIZE(t["text"]) for t in row["targets"].values() if t["known"]}
        if len(known) != 1:
            continue
        expected = known.pop()
        matches[identity] = pack, batch, binding, {**row, "effective": expected}
        proof = refs[f"{identity[0]}/{identity[1]}"]
        if identity not in issues and proof["evidence"] == "image-only" and proof["answer"]["text"] == expected:
            category = "control-kanpo" if row["key"].startswith("kanpo") else "control-other"
            rank = sha256(f"adr0025-v72-control\0{identity[0]}\0{identity[1]}".encode()).hexdigest()
            controls[category].append((rank, identity))
    if not issues <= matches.keys() or len(controls) != 2 or any(len(c) < 4 for c in controls.values()):
        raise ValueError("固定画像の対象か対照が不足")
    groups = {i: "reading-order" for i in issues}
    groups.update({i: group for group, candidates in controls.items() for _, i in sorted(candidates)[:4]})
    ready, mapping, jobs = [], {}, {}
    for identity, group in sorted(groups.items()):
        pack, batch, binding, row = matches[identity]
        cards, request = fixed.delivery / "cards" / pack, batch["request"]
        if [core.sha(cards / f) for f in request["images"]] != request["image_sha256"]:
            raise ValueError("新旧で使う固定画像が監査の画像と合わない")
        guide = launch.neutral.SHORT
        if request["prompt"].count(guide) != 1:
            raise ValueError("列順の旧指示を一か所だけ置き換えられない")
        entry = {**binding, "entry": len(ready)}
        ready.append(row)
        mapping[pack] = {**entry, "group": group, "category": group, "arms": {"old": entry, "new": entry}}
        jobs[f"{pack}/old"] = {"cards": str(cards), "request": request}
        new = {**request, "prompt": request["prompt"].replace(guide, GUIDE, 1)}
        jobs[f"{pack}/new"] = {"cards": str(cards), "request": new}
    selected = pilot.OUT / "display/selection.json"
    selected.parent.mkdir(parents=True)
    core.save_once(selected, core.encoded({"selected": ready}))
    pins = (Path(__file__), HERE / "protocol.md", effort / "run.py", Path(grade.__file__),
            Path(pilot.__file__), selected, manifest, original, receipt, result_path, diagnosis_path, evidence)
    pilot.SAMPLES = ready
    return {"jobs": jobs, "mapping": mapping,
            "files": core.load(core.LOCK)["inputs"] | {str(p): core.sha(p) for p in pins}}


if __name__ == "__main__":
    launch.configure()
    if len(sys.argv) > 1 and sys.argv[1] == "compare":
        grade.main(core, pilot)
    else:
        pilot.snapshot = snapshot
        pilot.main()
