"""検証した箇条書きと点列の説明を合わせ、固定済みの画像で確認する。"""

import importlib.util
from pathlib import Path

HERE = Path(__file__).resolve().parent
BASE = HERE.parent / "v24-physical-transcription-pilot/run.py"
spec = importlib.util.spec_from_file_location("horizontal_guide_transcription", BASE)
pilot = importlib.util.module_from_spec(spec)
spec.loader.exec_module(pilot)
pilot.HERE = HERE
pilot.OUT = pilot.OUT.with_name("reference-v33-horizontal-guide-pilot")
pilot.LOCK, pilot.RESULT = HERE / "lock.json", HERE / "result.json"
GUIDE = (
    "紙面の本文と位置がそろう先頭の箇条書きは、枠内に所属する文字の形として写します。"
    "上が白く下が黒い右向きの矢じりは「➢」です。本文の四角や星と、図表の色見本や装飾を周囲で区別します。"
    "青などの色付きで隣の字の半分ほどの塗り丸が同じ行の中に複数並び、"
    "それぞれ独立した本文項目の直前にあると確かめた時は「●」です。"
    "黒い単独の塗り点は行の先頭や本文の中で字種が画像から決まらない場合、位置を ⟦round:X-X⟧ と書きます。"
    "文中で中黒を置くのが自然に見える場合も、字種を区別できない塗り点は座標を返します。"
    "単独の round は横座標で読んだ同じ中心値を2回書きます。"
    "同じ高さに等間隔の塗り点が3個以上続き、字の区切りが見えない場合は、全体を1個の ⟦trail:X-Y⟧ と書きます。"
    "点列の両端は横座標の小目盛りで別々に確認します。後続の数字や本文を点列に含めないでください。"
)


def snapshot():
    audit = pilot.audit
    sources = [
        ("v22-list-mark-pilot", "reference-v22-list-mark-pilot", "tests", "cases",
         {"arrow", "square", "regular"}),
        ("v29-typographic-round-pilot", "reference-v29-typographic-round-pilot", "jobs", "mapping",
         {"colored-bullet", "small-mark", "legend", "arrow-and-small-mark"}),
        ("v24-physical-transcription-pilot", "reference-v24-physical-transcription-pilot", "jobs", "mapping",
         {"trails", "round", "body-and-round"}),
    ]
    files, rows, jobs, mapping, addresses = {}, [], {}, {}, set()
    for directory, private, plan_key, cases_key, categories in sources:
        lock = HERE.parent / directory / "lock.json"
        plan = audit.load(lock)
        if any(audit.sha(Path(p)) != sha for p, sha in plan["files"].items()):
            raise ValueError("固定済みの開発画像の来歴が異なる")
        source = pilot.OUT.with_name(private) / "display/selection.json"
        known = audit.load(source)["selected"]
        for name, raw in plan[plan_key].items():
            if not name.endswith("/old"):
                continue
            entry = plan[cases_key][name.split("/")[0]]
            category = entry.get("category", entry.get("purpose"))
            if category not in categories:
                continue
            row = known[entry["entry"]]
            identity = row["key"], row["line_index"]
            if identity in addresses or row["allocation_axis"] != "x":
                raise ValueError("開発対象が重複したか横軸以外を含む")
            addresses.add(identity)
            prefix, contract, suffix = raw["request"]["prompt"].partition(audit.packets.FORMAT)
            if not contract:
                raise ValueError("旧指示の回答形式が異なる")
            tag = f"case-{len(rows):02d}"
            mapping[tag] = {**entry, "entry": len(rows), "category": category}
            rows.append(row)
            jobs[tag + "/new"] = {**raw, "request": {**raw["request"], "prompt": prefix + GUIDE + contract + suffix}}
        files.update({str(p): audit.sha(p) for p in (lock, source)})
        files.update(plan["files"])
    output = pilot.OUT / "display/selection.json"
    output.parent.mkdir(parents=True)
    audit.save_once(output, audit.encoded({"selected": rows}))
    files.update({str(p): audit.sha(p) for p in (Path(__file__), BASE, HERE / "protocol.md", output)})
    pilot.SAMPLES = addresses
    return {"jobs": jobs, "mapping": mapping, "files": files}


if __name__ == "__main__":
    pilot.snapshot = snapshot
    pilot.main()
