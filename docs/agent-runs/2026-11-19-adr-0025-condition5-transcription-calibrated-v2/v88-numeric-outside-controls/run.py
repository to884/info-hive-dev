"""同じ数値の固定画素を使い、小さい区切りがちょうど枠端とその外にある場合を比べる。"""

from copy import deepcopy
from importlib.util import module_from_spec, spec_from_file_location
from pathlib import Path
import sys

from PIL import ImageFont

HERE = Path(__file__).resolve().parent
BASE = HERE.parent / "v86-numeric-boundary-pilot"
spec = spec_from_file_location("numeric_boundary_trial", BASE / "run.py")
numeric = module_from_spec(spec)
spec.loader.exec_module(numeric)
core, launch, pilot, grade = numeric.core, numeric.launch, numeric.pilot, numeric.grade
pilot.HERE = HERE
pilot.OUT = core.CORPUS / "reference-v88-numeric-outside-controls"
pilot.LOCK, pilot.RESULT = HERE / "lock.json", HERE / "pair.json"

SIZES = (("outside", -1), ("edge", 0), ("inside", 1))
TASK = (
    "添付図の識別子 {label} にある横書きの小さい枠を画像だけで転記してください。"
    "二つの解像度の図は同じ枠を示しています。左右に付いた赤い線と字の上下の位置を見てください。"
    "回答のJSONは results の配列に1行だけです。idは {label}。"
    "statusは readable または unreadable、textは実際の転記、判読不能なら ? です。"
    "外側から読める前後の字を加えず、分からない字を推測しません。"
)


def snapshot():
    core.verify_methods()
    physical = core.load(BASE / "physical.json")
    files = [
        Path(__file__), HERE / "protocol.md", BASE / "run.py", BASE / "lock.json",
        BASE / "physical.json", Path(pilot.__file__), Path(grade.__file__),
    ]
    if any(core.sha(Path(path)) != sha for path, sha in physical["inputs"].items()):
        raise ValueError("固定画素に基づく枠端の測定の来歴が異なる")
    lock = core.load(BASE / "lock.json")
    manifest = numeric.study.delivery / "packages.json"
    source = core.load(manifest)
    archive = core.load(launch.OUT / "selection.json")["selected"]
    image_root = pilot.OUT / "display"
    output = image_root / "selection.json"
    font = ImageFont.truetype(launch.render.typeface, size=16)
    inputs = dict(physical["inputs"])
    jobs, mappings, rows = {}, {}, []
    for pack, record in physical["rows"].items():
        packet = source["packs"][pack]
        original_label, binding = next(iter(packet["mapping"].items()))
        row = archive[binding["entry"]]
        assets = binding["image_reference"]
        high = assets["source_view"]["views"][1]
        image = next(r["image"] for r in high["images"] if r["kind"] == "plain")
        paths = (core.CORPUS / "probe-v4/png" / f"{row['key']}.png",
                 numeric.study.delivery / "source-assets" / image)
        measured = record["measurements"]["150"]["191"]
        if (not measured or not all(v["relative_vertical_center_to_bottom"] == 0.0
                                    and v["included_by_existing_geometry"] for v in measured)
                or [core.sha(p) for p in paths] != [assets["sha"]["150_dpi"], source["source_assets"][image]]):
            raise ValueError("数値の小さい区切りと枠端を固定の画像で結び付けられない")
        expected, = {core.ref.NORMALIZE(v["text"]) for v in row["targets"].values() if v["known"]}
        if expected.count(",") != len(measured):
            raise ValueError("固定した枠端の成分を正解の区切りと結び付けられない")
        for group, shift in SIZES:
            key = pack + "-" + group
            label = f"D{len(rows) + 1:03d}"
            x, y, w, h = row["box"]
            altered = {**row, "box": [x, y, w, h + shift],
                       "effective": expected.replace(",", "") if shift < 0 else expected}
            source_view = deepcopy(assets)
            rectangle = source_view["source_view"]["views"][1]["target_rectangle"]
            rectangle[3] += shift * (rectangle[3] - rectangle[1]) / h
            card = image_root / "cards" / key
            card.mkdir(parents=True, exist_ok=True)
            file = card / f"{label}-boundary.png"
            core.save_once(file, numeric.view_pair(altered, source_view, paths, label, font))
            inputs[str(file)] = core.sha(file)
            request = {**lock["jobs"][f"{pack}/old"]["request"], "ids": [label],
                       "images": [file.name], "image_sha256": [inputs[str(file)]]}
            instructions = TASK.format(label=label) + launch.neutral.HORIZONTAL + numeric.NOTE
            for arm, suffix in (("old", ""), ("new", numeric.GUIDE)):
                jobs[f"{key}/{arm}"] = {"cards": str(card), "request": {**request, "prompt": instructions + suffix}}
            mapping = {**binding, "entry": len(rows)}
            mappings[key] = {**mapping, "category": group, "group": group,
                             "arms": {"old": mapping, "new": mapping}}
            rows.append(altered)
    if len(rows) != 6:
        raise ValueError("元の二行について境界の内・上・外の6枠を固定できない")
    core.save_once(output, core.encoded({"selected": rows}))
    pilot.SAMPLES = rows
    return {"jobs": jobs, "mapping": mappings,
            "files": core.load(core.LOCK)["inputs"] | inputs | {str(p): core.sha(p) for p in (*files, output)}}


if __name__ == "__main__":
    launch.configure()
    if len(sys.argv) > 1 and sys.argv[1] == "compare":
        grade.main(core, pilot)
    else:
        pilot.snapshot = snapshot
        pilot.main()
