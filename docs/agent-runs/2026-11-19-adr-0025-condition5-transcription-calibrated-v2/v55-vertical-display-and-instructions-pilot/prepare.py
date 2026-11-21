"""固定した縦軸の開発画像で、表示と字形の指示を切り分ける。"""

import importlib.util
from pathlib import Path
import sys

HERE = Path(__file__).resolve().parent
BASE = HERE.parent / "v51-reading-physical-instructions-pilot/prepare.py"
spec = importlib.util.spec_from_file_location("visual_and_guidance_comparison", BASE)
earlier = importlib.util.module_from_spec(spec)
spec.loader.exec_module(earlier)
pilot = earlier.pilot
OLD_OUT, OLD_LOCK = pilot.OUT, pilot.LOCK
pilot.HERE = HERE
pilot.OUT = OLD_OUT.with_name("reference-v55-vertical-display-and-instructions-pilot")
pilot.LOCK, pilot.RESULT = HERE / "lock.json", HERE / "result.json"
DISPLAY = (
    "『列の字形』では、区間番号順に元の列を確認します。"
    "隣り合う区間は一部が重なるため、同じ字は一度だけ写します。"
)
ROTATION = (
    "字が横倒しに印刷されているときは、短い枠の90度の表示で同じ字を確認します。"
    "所属と読む順は元の向きで確認し、周囲の字を追加しません。"
)


def snapshot():
    sys.path.insert(0, str(HERE.parent / "v47-reference-audit"))
    import official
    core, audit = official.core, pilot.audit
    core.verify_methods()
    path = core.OUT / "delivery"
    manifest = path / "packages.json"
    original = core.load(manifest)["packs"]
    old = audit.load(OLD_LOCK)
    if any(audit.sha(Path(f)) != h for f, h in old["files"].items()):
        raise ValueError("固定して比較を済ませた画像が変わった")
    source = OLD_OUT / "display/selection.json"
    known = audit.load(source)["selected"]
    start = "縦の字の拡大では"
    hints = start + earlier.previous.VERTICAL.split(start, 1)[1] + earlier.VERTICAL
    rows, jobs, mapping = [], {}, {}
    for ident, item in old["mapping"].items():
        row = known[item["entry"]]
        if row["allocation_axis"] != "y":
            continue
        saved = item["baseline_packet"]
        first = original[saved]["request"]
        second = old["jobs"][ident + "/new"]
        note, sep, form = first["prompt"].partition(audit.packets.FORMAT)
        if not sep:
            raise ValueError("旧の縦軸の回答形式が変わった")
        show = DISPLAY + (ROTATION if row["box"][3] <= 120 else "")
        for arm, req, base, instruction in (
                ("guide", first, path / "cards" / saved, hints),
                ("display", second["request"], Path(second["cards"]), show)):
            if [audit.sha(base / name) for name in req["images"]] != req["image_sha256"]:
                raise ValueError("画像は対応する開発の固定表示と同じでなければならない")
            wanted = {**req, "prompt": note + instruction + sep + form}
            jobs[ident + "/" + arm] = {"cards": str(base), "request": wanted}
        mapping[ident] = {**item, "entry": len(rows)}
        rows.append(row)
    if len(rows) != 10:
        raise ValueError("縦軸の固定10行が異なる")
    positions = pilot.OUT / "display/selection.json"
    positions.parent.mkdir(parents=True)
    audit.save_once(positions, audit.encoded({"selected": rows}))
    locations = Path(__file__), HERE / "protocol.md", BASE, OLD_LOCK, source, manifest, positions
    pins = old["files"] | {str(p): audit.sha(p) for p in locations}
    pilot.SAMPLES = rows
    return {"jobs": jobs, "mapping": mapping, "files": pins}


if __name__ == "__main__":
    if len(sys.argv) > 1 and sys.argv[1] == "compare":
        del sys.argv[1]
        earlier.HERE = HERE
        earlier.compare()
    else:
        pilot.snapshot = snapshot
        pilot.main()
