"""固定450 DPIの縦列で、細かい連続拡大だけを変更する。"""

from collections import defaultdict
from hashlib import sha256
from importlib.util import module_from_spec, spec_from_file_location
from pathlib import Path
import sys

from PIL import Image, ImageDraw, ImageFont

HERE = Path(__file__).resolve().parent
EFFORT = HERE.parent / "v71-audit-effort-pilot"
spec = spec_from_file_location("effort_for_vertical_detail", EFFORT / "run.py")
fixed = module_from_spec(spec)
spec.loader.exec_module(fixed)
core, launch, pilot, grade = fixed.core, fixed.launch, fixed.pilot, fixed.judge
pilot.HERE = HERE
pilot.OUT = core.CORPUS / "reference-v75-vertical-detail-pilot"
pilot.LOCK, pilot.RESULT = HERE / "lock.json", HERE / "pair.json"
pilot.audit.readers.command = fixed.high


def panels(frozen, rect, label, font):
    orientation = launch.render.orientation
    body, (_, top) = orientation.cropped(frozen, rect, 7, 9)
    spans = [(start, min(body.height, start + 108)) for start in range(0, body.height, 84)]
    if len(spans) > 1 and spans[-2][1] == body.height:
        spans.pop()
    if spans[0][0] != 0 or spans[-1][1] != body.height or any(
            prior[1] - after[0] != 24 for prior, after in zip(spans, spans[1:])):
        raise ValueError("拡大表示で列の画素の一部がなくなる")
    width = max(150, 3 * body.width + 12)
    result = {}
    for first in range(0, len(spans), 8):
        window = spans[first:first + 8]
        height = 372
        sheet = Image.new("RGB", (4 * width, 44 + height * ((len(window) + 3) // 4)), "white")
        draw = ImageDraw.Draw(sheet)
        draw.text((5, 4), f"{label}　固定450 DPI　列の字形（区間番号順）", font=font, fill="black")
        draw.text((5, 24), "上下に重なる画素を含む。位置は元画像の上端からの画素。", font=font, fill="black")
        for cells, (a, b) in enumerate(window):
            x, y = (cells % 4) * width + 5, (cells // 4) * height + 49
            draw.text((x, y), f"{first + cells + 1}  [{top+a}, {top+b})", font=font, fill="black")
            part = body.crop((0, a, body.width, b))
            enlarged = part.resize((3 * part.width, 3 * part.height), Image.Resampling.NEAREST)
            sheet.paste(enlarged, (x, y + 22))
            retrieved = sheet.crop((x, y + 22, x + enlarged.width, y + 22 + enlarged.height)).resize(
                part.size, Image.Resampling.NEAREST)
            if retrieved.tobytes() != part.tobytes():
                raise ValueError("固定450 DPIの字形の画素をそのまま保っていない")
        name = f"{label}-column-shapes-{first // 8 + 1:02d}.png"
        result[name] = orientation.blob(sheet)
    return result


def snapshot():
    core.verify_methods()
    comparison_file, lock_file = EFFORT / "comparison.json", EFFORT / "lock.json"
    comparison, previous = core.load(comparison_file), core.load(lock_file)
    if (comparison["lock_sha256"] != core.sha(lock_file)
            or any(core.sha(Path(p)) != h for p, h in previous["files"].items())):
        raise ValueError("開発用の高エフォート比較が事前固定と異なる")
    chosen = {pack: ("control-recheck" if c["category"] == "control" else c["category"])
              for pack, c in comparison["cases"].items() if c["shape"].startswith("vertical")
              and c["outcomes"]["high"]["pair"] in {"unresolved", "omitted", "extra", "different"}}
    if not chosen:
        raise ValueError("追試する縦列がない")
    selection, manifest = launch.OUT / "selection.json", fixed.delivery / "packages.json"
    reference = launch.OUT / "reference-evidence.json"
    result_path = HERE.parent / "v64-reference-audit/result.json"
    if core.load(result_path)["reference_sha256"] != core.sha(reference):
        raise ValueError("一致対照の正式な来歴が異なる")
    subjects, inputs = core.load(selection)["selected"], core.load(manifest)
    refs = core.load(reference)
    canonical, controls = {}, defaultdict(list)
    for pack, batch in inputs["packs"].items():
        (label, binding), = batch["mapping"].items()
        row = subjects[binding["entry"]]
        if row["allocation_axis"] != "y":
            continue
        identity = fixed.key(row)
        known = {core.ref.NORMALIZE(t["text"]) for t in row["targets"].values() if t["known"]}
        if len(known) != 1:
            continue
        text = known.pop()
        canonical[pack] = {**row, "effective": text}, batch, label, binding
        proof = refs[f"{identity[0]}/{identity[1]}"]
        if (pack not in chosen and identity[0].startswith("kanpo") and proof["evidence"] == "image-only"
                and proof["answer"]["text"] == text):
            group = "control-short" if row["box"][3] <= 120 else "control-long"
            rank = sha256(f"adr0025-v75-control\0{identity[0]}\0{identity[1]}".encode()).hexdigest()
            controls[group].append((rank, pack))
    if not chosen.keys() <= canonical.keys() or len(controls) != 2 or any(len(g) < 3 for g in controls.values()):
        raise ValueError("縦軸の対象と対照がそろわない")
    chosen.update({pack: group for group, candidates in controls.items() for _, pack in sorted(candidates)[:3]})
    jobs, mappings, ready, source_assets = {}, {}, [], []
    font_path = launch.render.typeface
    font = ImageFont.truetype(font_path, size=16)
    display = pilot.OUT / "display"
    for pack, group in sorted(chosen.items()):
        row, batch, label, raw = canonical[pack]
        cards, request = fixed.delivery / "cards" / pack, batch["request"]
        if [core.sha(cards / f) for f in request["images"]] != request["image_sha256"]:
            raise ValueError("旧の固定画像が監査の画像と合わない")
        view = raw["image_reference"]["source_view"]["views"][1]
        asset = next(v["image"] for v in view["images"] if v["kind"] == "plain")
        source = fixed.delivery / "source-assets" / asset
        if core.sha(source) != inputs["source_assets"][asset]:
            raise ValueError("縦の字形の元の固定450 DPIが異なる")
        source_assets.append(source)
        with Image.open(source) as im:
            enhanced = panels(im, view["target_rectangle"], label, font)
        images = {}
        inserted = False
        for filename in request["images"]:
            if "-column-shapes-" not in filename:
                images[filename] = (cards / filename).read_bytes()
            elif not inserted:
                images.update(enhanced)
                inserted = True
        if not inserted or len(images) > launch.audit.LIMIT:
            raise ValueError("列の字形を置き換えた添付の構成が異なる")
        newer = display / "paired/cards" / pack
        newer.mkdir(parents=True)
        for filename, data in images.items():
            core.save_once(newer / filename, data)
        new = {**request, "images": list(images), "image_sha256": [core.sha(newer / n) for n in images]}
        binding = {**raw, "entry": len(ready)}
        ready.append(row)
        mappings[pack] = {**binding, "category": group, "group": group, "arms": {"old": binding, "new": binding}}
        jobs[f"{pack}/old"] = {"cards": str(cards), "request": request}
        jobs[f"{pack}/new"] = {"cards": str(newer), "request": new}
    picked = display / "selection.json"
    core.save_once(picked, core.encoded({"selected": ready}))
    pins = (Path(__file__), HERE / "protocol.md", Path(pilot.__file__), Path(grade.__file__), font_path,
            EFFORT / "run.py", comparison_file, lock_file, selection, manifest, reference, result_path, picked, *source_assets)
    pilot.SAMPLES = ready
    return {"jobs": jobs, "mapping": mappings,
            "files": core.load(core.LOCK)["inputs"] | {str(p): core.sha(p) for p in pins}}


if __name__ == "__main__":
    launch.configure()
    if len(sys.argv) > 1 and sys.argv[1] == "compare":
        grade.main(core, pilot)
    else:
        pilot.snapshot = snapshot
        pilot.main()
