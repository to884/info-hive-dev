"""固定画素の対象行だけを並べ直し、同じ指示で画像提示の違いを比較する。"""

import argparse
from concurrent.futures import ThreadPoolExecutor
import hashlib
import importlib.util
import io
import json
from pathlib import Path

from PIL import Image


HERE = Path(__file__).resolve().parent
GEOMETRY = HERE.parent / "geometry-pilot/run.py"
spec = importlib.util.spec_from_file_location("pilot_geometry", GEOMETRY)
pilot = importlib.util.module_from_spec(spec)
spec.loader.exec_module(pilot)
base = pilot.base
OUT = pilot.trial.ROOT / HERE.name
DERIVED = OUT / "assets"
LOCK = HERE / "lock.json"
ARMS = ("full", "crops")


def compact(path, slots):
    scale = 3
    with Image.open(path) as src:
        if src.mode != "RGB" or src.size != (960, 1014):
            raise ValueError("元画像の寸法か形式が異なる")
        height = 36 * scale
        width = 300 * scale
        dst = Image.new("RGB", (width, 65 + len(slots) * (height + 12)), (128,) * 3)
        dst.paste(src.crop((0, 0, width, 60)), (0, 0))
        for i, slot in enumerate(slots):
            top = (26 + 37 * slot - 2) * scale
            dst.paste(src.crop((0, top, width, top + height)), (0, 65 + i * (height + 12)))
    encoded = io.BytesIO()
    dst.save(encoded, format="PNG")
    return encoded.getvalue()


def source():
    rows, original, study, past, previous = pilot.material()
    outcome_path = GEOMETRY.parent / "result.json"
    previous_result = base.load(outcome_path)
    previous_lock = GEOMETRY.parent / "lock.json"
    if ({k: v for k, v in base.load(previous_lock).items() if k != "fixed_at"} != previous
            or previous_result["lock_sha256"] != base.sha(previous_lock) or previous_result["advance"]):
        raise ValueError("前試験の入力、結果、進行判定を再現できない")
    past |= {r["session"] for r in previous_result["receipts"]}
    all_rows = pilot.prior.original()[0]
    targets = {r["id"] for r in rows}
    slots = {sheet: [i for i, row in enumerate([r for r in all_rows if r["sheet"] == sheet])
                     if row["id"] in targets] for sheet in range(1, 5)}
    full = previous["packs"]["geometry"]
    if any(len(selected) != 4 for selected in slots.values()) or len(full["images"]) != 16:
        raise ValueError("元版の4原稿から各4行を再現できない")
    outputs = {}
    for name, digest in zip(full["images"], full["image_sha256"], strict=True):
        path = original / name
        if base.sha(path) != digest:
            raise ValueError("元画像のSHAが変化")
        sheet = int(name.split("-")[1])
        outputs[name] = compact(path, slots[sheet])
    crops = dict(full, image_sha256=[hashlib.sha256(outputs[name]).hexdigest() for name in full["images"]])
    frozen = {"script_sha256": base.sha(Path(__file__)), "protocol_sha256": base.sha(HERE / "protocol.md"),
              "pilot_lock_sha256": base.sha(previous_lock), "pilot_result_sha256": base.sha(outcome_path),
              "models": pilot.MODELS, "effort": "medium", "groups": previous["groups"],
              "packs": {"full": full, "crops": crops}, "slots": {str(k): v for k, v in slots.items()}}
    return rows, original, study, past, outputs, frozen


def prepare(outputs, frozen):
    if LOCK.exists() or DERIVED.exists():
        raise FileExistsError("切り出しの画像か固定済みの指定がすでにある")
    DERIVED.mkdir(parents=True)
    for name, raw in outputs.items():
        (DERIVED / name).write_bytes(raw)
    base.write_json(LOCK, dict(frozen, fixed_at=base.utc_now()))
    print(base.sha(LOCK), flush=True)


def run(args, rows, original, study, past, outputs, frozen):
    if base.sha(LOCK) != args.lock_sha256 or {k: v for k, v in base.load(LOCK).items() if k != "fixed_at"} != frozen:
        raise ValueError("固定済みの入力と一致しない")
    if any((DERIVED / name).read_bytes() != value for name, value in outputs.items()):
        raise ValueError("派生画像が固定と異なる")
    executables = {"sol": args.codex.resolve(), "opus": args.claude.resolve()}
    pilot.OUT = OUT / "reads"
    with ThreadPoolExecutor(max_workers=4) as pool:
        jobs = {}
        for arm, directory in zip(ARMS, (original, DERIVED), strict=True):
            pack = frozen["packs"][arm]
            image_index = dict(zip(pack["images"], pack["image_sha256"], strict=True))
            read_study = dict(study, image_sha256=image_index)
            for who, exe in executables.items():
                jobs[arm, who] = pool.submit(pilot.read, exe, who, arm, pack, rows, directory, read_study)
        records = {key: job.result() for key, job in jobs.items()}
    receipts = [receipt for _, receipt in records.values()]
    ids = {r["session"] for r in receipts}
    if len(ids) != 4 or ids & past or source()[-1] != frozen or base.sha(LOCK) != args.lock_sha256:
        raise ValueError("新規セッションか固定入力を再確認できない")
    pilot.ARMS = ARMS
    outcome = pilot.summarize(rows, frozen, {key: votes for key, (votes, _) in records.items()})
    base.write_json(HERE / "result.json", dict(outcome, receipts=receipts, lock_sha256=args.lock_sha256))
    print(json.dumps(outcome, ensure_ascii=False), flush=True)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("action", choices=("prepare", "run"))
    parser.add_argument("--codex", type=Path)
    parser.add_argument("--claude", type=Path)
    parser.add_argument("--lock-sha256")
    args = parser.parse_args()
    rows, original, study, past, outputs, frozen = source()
    if args.action == "prepare":
        prepare(outputs, frozen)
    else:
        run(args, rows, original, study, past, outputs, frozen)


if __name__ == "__main__":
    main()
