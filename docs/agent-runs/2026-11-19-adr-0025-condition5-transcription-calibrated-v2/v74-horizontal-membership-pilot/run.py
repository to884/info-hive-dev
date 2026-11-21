"""横枠の字や記号の所属を、同じ画像を読む二つの指示で比較する。"""

from collections import defaultdict
from hashlib import sha256
from importlib.util import module_from_spec, spec_from_file_location
from pathlib import Path
import sys

HERE = Path(__file__).resolve().parent
EFFORT = HERE.parent / "v71-audit-effort-pilot"
spec = spec_from_file_location("effort_for_horizontal_membership", EFFORT / "run.py")
fixed = module_from_spec(spec)
spec.loader.exec_module(fixed)
core, launch, pilot, grade = fixed.core, fixed.launch, fixed.pilot, fixed.judge
pilot.HERE = HERE
pilot.OUT = core.CORPUS / "reference-v74-horizontal-membership-pilot"
pilot.LOCK, pilot.RESULT = HERE / "lock.json", HERE / "pair.json"
pilot.audit.readers.command = fixed.high

GUIDE = (
    "枠の両端を確認し、所属する文字を一つずつ確かめます。色が異なっていても、前の文章に続く参照や番号を作る字なら、"
    "同じ枠内の長さとインク中心の基準で含めるかを決めます。凡例の見本など文字でない図形は除きます。"
    "振り仮名や括弧、数字の間の区切りも、それぞれの字の全体と画素が見える位置で確かめます。"
    "字を写すかは色や意味のつながりで決めず、枠の外の字を足しません。"
    "曖昧な小点の形や位置は既定の方法で記録します。"
)


def snapshot():
    core.verify_methods()
    comparison_file, lock_file = EFFORT / "comparison.json", EFFORT / "lock.json"
    comparison, previous = core.load(comparison_file), core.load(lock_file)
    if (comparison["lock_sha256"] != core.sha(lock_file)
            or any(core.sha(Path(p)) != h for p, h in previous["files"].items())):
        raise ValueError("開発用の高エフォート比較が事前固定と異なる")
    selected = {pack: case["category"] for pack, case in comparison["cases"].items()
                if case["category"] not in {"reading-order", "control"} and case["shape"].startswith("horizontal")
                and case["outcomes"]["high"]["pair"] in {"unresolved", "omitted", "extra", "different"}}
    if not selected:
        raise ValueError("追試する横枠がない")
    selection, manifest = launch.OUT / "selection.json", fixed.delivery / "packages.json"
    reference = launch.OUT / "reference-evidence.json"
    result_path = HERE.parent / "v64-reference-audit/result.json"
    if core.load(result_path)["reference_sha256"] != core.sha(reference):
        raise ValueError("一致対照の正式な来歴が異なる")
    rows, original = core.load(selection)["selected"], core.load(manifest)["packs"]
    refs = core.load(reference)
    canonical, controls = {}, defaultdict(list)
    for pack, batch in original.items():
        (label, binding), = batch["mapping"].items()
        row = rows[binding["entry"]]
        if row["allocation_axis"] != "x":
            continue
        identity = fixed.key(row)
        known = {core.ref.NORMALIZE(t["text"]) for t in row["targets"].values() if t["known"]}
        if len(known) != 1:
            continue
        expected = known.pop()
        canonical[pack] = {**row, "effective": expected}, batch, binding
        proof = refs[f"{identity[0]}/{identity[1]}"]
        if proof["evidence"] == "image-only" and proof["answer"]["text"] == expected:
            group = "control-short" if row["box"][2] <= 120 else "control-wide"
            rank = sha256(f"adr0025-v74-control\0{identity[0]}\0{identity[1]}".encode()).hexdigest()
            controls[group].append((rank, pack))
    if not selected.keys() <= canonical.keys() or len(controls) != 2 or any(len(g) < 3 for g in controls.values()):
        raise ValueError("対象と対照がそろわない")
    selected.update({pack: group for group, candidates in controls.items() for _, pack in sorted(candidates)[:3]})
    jobs, mappings, ready = {}, {}, []
    for pack, group in sorted(selected.items()):
        row, batch, raw = canonical[pack]
        cards, request = fixed.delivery / "cards" / pack, batch["request"]
        if [core.sha(cards / f) for f in request["images"]] != request["image_sha256"]:
            raise ValueError("新旧で使う固定画像が監査の画像と合わない")
        guide = launch.neutral.HORIZONTAL
        if request["prompt"].count(guide) != 1:
            raise ValueError("新指示を同じ箇所に追加できない")
        binding = {**raw, "entry": len(ready)}
        ready.append(row)
        mappings[pack] = {**binding, "category": group, "group": group, "arms": {"old": binding, "new": binding}}
        jobs[f"{pack}/old"] = {"cards": str(cards), "request": request}
        new = {**request, "prompt": request["prompt"].replace(guide, guide + GUIDE, 1)}
        jobs[f"{pack}/new"] = {"cards": str(cards), "request": new}
    picked = pilot.OUT / "display/selection.json"
    picked.parent.mkdir(parents=True)
    core.save_once(picked, core.encoded({"selected": ready}))
    inputs = (Path(__file__), HERE / "protocol.md", Path(pilot.__file__), Path(grade.__file__),
              EFFORT / "run.py", comparison_file, lock_file, selection, manifest, reference, result_path, picked)
    pilot.SAMPLES = ready
    return {"jobs": jobs, "mapping": mappings,
            "files": core.load(core.LOCK)["inputs"] | {str(p): core.sha(p) for p in inputs}}


if __name__ == "__main__":
    launch.configure()
    if len(sys.argv) > 1 and sys.argv[1] == "compare":
        grade.main(core, pilot)
    else:
        pilot.snapshot = snapshot
        pilot.main()
