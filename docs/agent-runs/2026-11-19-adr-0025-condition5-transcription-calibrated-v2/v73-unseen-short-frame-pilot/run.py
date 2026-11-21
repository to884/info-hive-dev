"""未使用の開発短枠を事前に固定し、二つの列順の指示を比べる。"""

from collections import defaultdict
from hashlib import sha256
from importlib.util import module_from_spec, spec_from_file_location
from pathlib import Path
import sys

HERE = Path(__file__).resolve().parent
ORDER = HERE.parent / "v72-short-frame-order-pilot/run.py"
spec = spec_from_file_location("frozen_short_frame_order", ORDER)
order = module_from_spec(spec)
spec.loader.exec_module(order)
launch, core, pilot, grade = order.launch, order.core, order.pilot, order.grade
pilot.HERE = HERE
pilot.OUT = core.CORPUS / "reference-v73-unseen-short-frame-pilot"
pilot.LOCK, pilot.RESULT = HERE / "lock.json", HERE / "pair.json"
reference_prep = launch.previous.module("unseen_neutral_packets", HERE.parent / "v67-neutral-transcription-pilot/prepare.py")
GROUPS = ("kanpo-35-or-less", "kanpo-36-to-120", "other-publication")


def key(row):
    return row["key"], row["line_index"]


def choose(pools, history):
    candidates, sorted_groups = {}, defaultdict(list)
    for domain, rows in pools.items():
        for entry in rows:
            identity = key(entry)
            if (identity in history or entry["development_intake"] or entry["previously_audited"]
                    or not launch.render.short_frame(entry)):
                continue
            target = {k: entry[k] for k in ("cohort", "text", "known", "error")}
            row = candidates.setdefault(identity, {k: v for k, v in entry.items() if k not in target})
            row.setdefault("targets", {})[domain] = target
    for identity, row in candidates.items():
        targets = row["targets"].values()
        texts = {core.ref.NORMALIZE(t["text"]) for t in targets if t["known"]}
        if len(texts) != 1 or not all(t["known"] for t in targets):
            continue
        group = "other-publication"
        if identity[0].startswith("kanpo"):
            group = GROUPS[0 if row["box"][2] <= 35 else 1]
        rank = sha256(f"adr0025-v73-unseen-order\0{identity[0]}\0{identity[1]}".encode()).hexdigest()
        sorted_groups[group].append((rank, {**row, "effective": texts.pop()}))
    if any(len(sorted_groups[g]) < 6 for g in GROUPS):
        raise ValueError(f"未使用の短枠が不足: { {g: len(sorted_groups[g]) for g in GROUPS} }")
    rank_lists = {g: sorted(sorted_groups[g], key=lambda item: (item[0], key(item[1]))) for g in GROUPS}
    selection = [(g, row) for g in GROUPS for _, row in rank_lists[g][:6]]
    eligible = {g: [(rank, key(row)) for rank, row in rank_lists[g]] for g in GROUPS}
    return selection, eligible


def snapshot():
    core.verify_methods()
    method_file = core.PLAN
    method = core.load(method_file)
    _, prior_files = reference_prep.exposed(method)
    display = pilot.OUT / "display"
    prior_files = [f for f in prior_files if pilot.OUT not in f.parents]
    history = {tuple(v) for v in method["direct_intake"]}
    for path in prior_files:
        saved = core.load(path)
        for row in saved.get("selected", saved.get("entries", [])):
            page = row.get("key") or row.get("page")
            if page and "line_index" in row:
                history.add((page, row["line_index"]))
    _, _, label_dir = core.methods()
    labels = label_dir / "public.json"
    _, flags = core.baseline.take_public_rows()
    chosen, eligible = choose(core.baseline.populations(core.load(labels), flags), history)
    rows = [row for _, row in chosen]
    same = display / "same"
    selection, exclusions = (display / f"{name}.json" for name in ("selection", "eligible"))
    expected = {selection: {"selected": rows}, exclusions: {"excluded": sorted(history), "eligible": eligible}}
    if same.exists():
        for path, value in expected.items():
            if path.read_bytes() != core.encoded(value):
                raise ValueError("先に決めた18行の選定は再現できない")
        files = tuple(same / f for f in ("selection.json", "method.json", "population.json",
                                        "delivery/packages.json", "retained.json"))
        manifest = core.load(files[3])
        if (manifest["source_sha256"] != core.sha(files[0]) or
                any(core.sha(Path(f)) != h for f, h in manifest["inputs"].items())):
            raise ValueError("準備済みの画像の来歴が異なる")
        batches = manifest["packs"]
    else:
        batches, files = reference_prep.build(same, rows, method, True)
        for path, value in expected.items():
            core.save_once(path, core.encoded(value))
    layout = launch.audit.packets.trial.base
    from PIL import ImageFont
    font_path = launch.render.typeface
    font = ImageFont.truetype(font_path, size=17)
    jobs, mapping = {}, {}
    extra_inputs = []
    for pack, batch in batches.items():
        (label, binding), = batch["mapping"].items()
        request = batch["request"]
        cards = same / "delivery/cards" / pack
        if ([core.sha(cards / f) for f in request["images"]] != request["image_sha256"]
                or request["prompt"].count(launch.neutral.SHORT) != 1):
            raise ValueError("中立の固定画像・列順の旧指示の組がそろわない")
        index = binding["entry"]
        if f"{label}-layout.png" not in request["images"]:
            row = rows[index]
            assets = binding["image_reference"]
            supplement = layout.framed_context(row, assets, {}, label, font)
            (name, pixels), = supplement.items()
            output = display / "paired/cards" / pack
            output.mkdir(parents=True)
            for filename in request["images"]:
                core.save_once(output / filename, (cards / filename).read_bytes())
            core.save_once(output / name, pixels)
            low = core.CORPUS / "probe-v4/png" / f"{row['key']}.png"
            extra_inputs.append(low)
            request = {**request, "images": [*request["images"], name],
                       "image_sha256": [*request["image_sha256"], core.sha(output / name)]}
            cards = output
        if len(request["images"]) > launch.audit.LIMIT:
            raise ValueError("共通の固定画像が一束で渡せない")
        group = chosen[index][0]
        mapping[pack] = {**binding, "category": group, "group": group, "arms": {"old": binding, "new": binding}}
        jobs[f"{pack}/old"] = {"cards": str(cards), "request": request}
        new = {**request, "prompt": request["prompt"].replace(launch.neutral.SHORT, order.GUIDE, 1)}
        jobs[f"{pack}/new"] = {"cards": str(cards), "request": new}
    pins = (Path(__file__), HERE / "protocol.md", ORDER, ORDER.parent / "lock.json", ORDER.parent / "comparison.json",
            Path(reference_prep.__file__), Path(grade.__file__), Path(pilot.__file__), method_file, labels,
            selection, exclusions, Path(layout.__file__), font_path, *files, *prior_files, *extra_inputs)
    pilot.SAMPLES = rows
    return {"jobs": jobs, "mapping": mapping,
            "files": core.load(core.LOCK)["inputs"] | {str(p): core.sha(p) for p in pins}}


if __name__ == "__main__":
    launch.configure()
    if len(sys.argv) > 1 and sys.argv[1] == "finish-preparing":
        if pilot.LOCK.exists():
            raise FileExistsError("既に比較を固定した")
        core.save_once(pilot.LOCK, core.encoded(snapshot()))
        print(core.sha(pilot.LOCK), len(pilot.SAMPLES), "行、同じ画素で二指示", flush=True)
    elif len(sys.argv) > 1 and sys.argv[1] == "compare":
        grade.main(core, pilot)
    else:
        pilot.snapshot = snapshot
        pilot.main()
