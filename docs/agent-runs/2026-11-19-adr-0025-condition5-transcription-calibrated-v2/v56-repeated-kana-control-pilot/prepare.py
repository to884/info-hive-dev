"""小書き仮名と同じ縦軸の対照を、元の束のまま各3回読む。"""

import importlib.util
from pathlib import Path
import sys

HERE = Path(__file__).resolve().parent
BASE = HERE.parent / "v51-reading-physical-instructions-pilot/prepare.py"
spec = importlib.util.spec_from_file_location("repeat_exact_vertical_conditions", BASE)
earlier = importlib.util.module_from_spec(spec)
spec.loader.exec_module(earlier)
pilot = earlier.pilot
OLD_OUT, OLD_LOCK = pilot.OUT, pilot.LOCK
pilot.HERE = HERE
pilot.OUT = OLD_OUT.with_name("reference-v56-repeated-kana-control-pilot")
pilot.LOCK, pilot.RESULT = HERE / "lock.json", HERE / "result.json"
TAGS = {"case-09", "case-10", "case-11"}


def snapshot():
    sys.path.insert(0, str(HERE.parent / "v47-reference-audit"))
    import official
    core, audit = official.core, pilot.audit
    core.verify_methods()
    delivery = core.OUT / "delivery"
    manifest = delivery / "packages.json"
    prior = core.load(manifest)["packs"]
    locked = audit.load(OLD_LOCK)
    source = OLD_OUT / "display/selection.json"
    seed_rows = audit.load(source)["selected"]
    if any(audit.sha(Path(f)) != h for f, h in locked["files"].items()):
        raise ValueError("開発で実際に読んだ旧の方法が変化")
    rows, jobs, mapping = [], {}, {}
    for tag in sorted(TAGS):
        item = locked["mapping"][tag]
        pack = item["baseline_packet"]
        old = {"cards": str(delivery / "cards" / pack), "request": prior[pack]["request"]}
        new = locked["jobs"][tag + "/new"]
        for bundle in (old, new):
            req = bundle["request"]
            if [audit.sha(Path(bundle["cards"]) / f) for f in req["images"]] != req["image_sha256"]:
                raise ValueError("保存票に送った画像を再現できない")
        for repeat in range(1, 4):
            name = f"{tag}-r{repeat}"
            mapping[name] = {**item, "entry": len(rows)}
            jobs[name + "/original"] = old
            jobs[name + "/changed"] = new
        rows.append(seed_rows[item["entry"]])
    positions = pilot.OUT / "display/selection.json"
    positions.parent.mkdir(parents=True)
    audit.save_once(positions, audit.encoded({"selected": rows}))
    files = (Path(__file__), BASE, HERE / "protocol.md", OLD_LOCK, source, manifest, positions)
    pilot.SAMPLES = rows
    return {"jobs": jobs, "mapping": mapping, "files": locked["files"] | {str(p): audit.sha(p) for p in files}}


if __name__ == "__main__":
    if len(sys.argv) > 1 and sys.argv[1] == "compare":
        del sys.argv[1]
        earlier.HERE = HERE
        earlier.compare()
    else:
        pilot.snapshot = snapshot
        pilot.main()
