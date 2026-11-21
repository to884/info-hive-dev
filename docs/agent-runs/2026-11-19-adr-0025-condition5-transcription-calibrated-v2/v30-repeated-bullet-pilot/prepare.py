"""前の開発比較と同じ添付に、色付きの項目記号を区別する指示を加える。"""

import importlib.util
from pathlib import Path

HERE = Path(__file__).resolve().parent
BASE = HERE.parent / "v24-physical-transcription-pilot/run.py"
PREVIOUS = HERE.parent / "v29-typographic-round-pilot"
spec = importlib.util.spec_from_file_location("repeated_bullet_transcription", BASE)
pilot = importlib.util.module_from_spec(spec)
spec.loader.exec_module(pilot)
pilot.HERE = HERE
old = pilot.OUT.with_name("reference-v29-typographic-round-pilot")
pilot.OUT = pilot.OUT.with_name("reference-v30-repeated-bullet-pilot")
pilot.LOCK, pilot.RESULT = HERE / "lock.json", HERE / "result.json"
GUIDE = (
    "固定450 DPIで枠内の図形と文字を区別します。同じ行の中で、隣の文字の高さの半分ほどある青などの色付きの塗り丸が"
    "同じ形と色で複数並び、それぞれが独立した本文項目のすぐ前にある場合は、その箇条書きの形を「●」と写します。"
    "単独の小さな塗り点や語の途中の小さな点は、字種が区別できなければ元のroundの形式で、色見本は転記しません。"
    "他の行の箇条書きと位置がそろう、上が白く下が黒い右向き矢じりは「➢」です。"
)


def snapshot():
    audit = pilot.audit
    earlier = PREVIOUS / "lock.json"
    plan = audit.load(earlier)
    if any(audit.sha(Path(p)) != h for p, h in plan["files"].items()):
        raise ValueError("前の旧・新の比較に使った添付の来歴が異なる")
    selection = old / "display/selection.json"
    selected = audit.load(selection)["selected"]
    pilot.SAMPLES = {(r["key"], r["line_index"]): r["allocation_axis"] for r in selected}
    current = pilot.OUT / "display/selection.json"
    current.parent.mkdir(parents=True)
    audit.save_once(current, selection.read_bytes())
    jobs = {}
    for key, task in plan["jobs"].items():
        if not key.endswith("/old"):
            continue
        prompt = task["request"]["prompt"]
        start, delimiter, end = prompt.partition(audit.packets.FORMAT)
        if not delimiter:
            raise ValueError("先に固定した指示の回答形式を確認できない")
        name = key.split("/")[0] + "/new"
        jobs[name] = {**task, "request": {**task["request"], "prompt": start + GUIDE + delimiter + end}}
    paths = (Path(__file__), BASE, HERE / "protocol.md", earlier, selection, current)
    return {"jobs": jobs, "mapping": plan["mapping"],
            "files": plan["files"] | {str(p): audit.sha(p) for p in paths}}


if __name__ == "__main__":
    pilot.snapshot = snapshot
    pilot.main()
