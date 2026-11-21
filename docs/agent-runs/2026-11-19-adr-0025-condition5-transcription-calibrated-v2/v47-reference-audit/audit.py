"""旧の配布を保ち、正式配布で必要な確認画像と出典の一意性を検査する。"""

from io import BytesIO
from pathlib import Path
import sys

from PIL import Image

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parent / "v19-reference-audit"))
import run as previous

draft = previous.module("planned_frame_audit", HERE / "run.py")
core = draft.core
packets = previous.packets
original_inputs = draft.inputs
draft.raster_file = HERE / "strict_points.py"
LIMIT = 24
LEGACY_DESCRIPTION = (
    previous.frame.FRAME_GUIDE
    + "『枠への入り方』の最短目盛りは元の150 DPIの1画素で、長い目盛りは5画素です。"
    "この細かい目盛りは枠に入る長さの確認に使います。丸印の座標を返すときは『横座標』画像だけを使ってください。"
)
EDGE_NOTE = (
    "枠端の数値は条件に合う成分の一部に付きます。"
    "番号がない小さな点や字も、両方の枠端画像と元の字形で確認してください。"
    "丸印の位置は『横座標』画像で記録してください。"
)
COORDINATE_NOTE = "枠への入り方の目盛りとは分けて、印の座標は横座標で読みます。"
PREFLIGHT = HERE / "preflight-complete.json"


def inputs(plan, report, labels):
    evidence = core.load(PREFLIGHT)
    if (evidence["scope"] != "development-only" or evidence["attachments"]["rows"] != 27
            or not evidence["attachments"]["paired_coordinate_rows"]
            or evidence["rounds"]["ambiguous_control"] != "rejected"
            or any(core.sha(Path(name)) != digest for name, digest in evidence["inputs"].items())):
        raise ValueError("正式な配布と出典の手順が開発試験と結び付かない")
    files = (Path(__file__), HERE.parent / "v44-small-point-pixel-pilot/run.py",
             HERE.parent / "v24-physical-transcription-pilot/run.py",
             HERE.parent / "v10-reference-audit/diagnose.py",
             draft.PRIOR / "diagnose.py", PREFLIGHT)
    return original_inputs(plan, report, labels) | {str(p.resolve()): core.sha(p) for p in files}


def required_supplements(row, ident):
    w, h = row["box"][2:]
    if min(w, h) > 35:
        return set()
    names = {f"{ident}-edge-start.png", f"{ident}-edge-end.png"}
    if row["allocation_axis"] == "x" and 120 < w <= 1200:
        names.add(f"{ident}-paragraph-margin.png")
    return names


def combine(first, second):
    with Image.open(BytesIO(first)) as a, Image.open(BytesIO(second)) as b:
        a, b = a.convert("RGB"), b.convert("RGB")
        canvas = Image.new("RGB", (max(a.width, b.width), a.height + 8 + b.height), "white")
        for image, top in ((a, 0), (b, a.height + 8)):
            canvas.paste(image, (0, top))
            if canvas.crop((0, top, image.width, top + image.height)).tobytes() != image.tobytes():
                raise ValueError("目盛り画像の固定画素が結合時に変わった")
        out = BytesIO()
        canvas.save(out, "PNG")
        return out.getvalue()


def fit(primary, extra, required):
    if not required <= extra.keys():
        raise ValueError("枠端か段落の必須画像が作成されていない")
    merged = primary | extra
    coords = [name for name in merged if "-coordinate-" in name]
    keep = primary.keys() | required | set(coords)
    if len(keep) > LIMIT:
        excess = len(keep) - LIMIT
        if len(coords) < 2 * excess:
            raise ValueError("必須画像を結合しても一行の添付上限以下にできない")
        extra = extra.copy()
        for offset in range(len(coords) - 2 * excess, len(coords), 2):
            first, second = coords[offset:offset + 2]
            name = first.removesuffix(".png") + "+" + second.rsplit("-", 1)[1]
            extra[name] = combine(merged[first], merged[second])
            for old_name in (first, second):
                primary.pop(old_name, None)
                extra.pop(old_name, None)
            keep.difference_update((first, second))
            keep.add(name)
    if len(keep) > LIMIT:
        raise ValueError("必須画像だけで一行の添付上限を超える")
    overflow = len(primary.keys() | extra.keys()) - LIMIT
    if overflow <= 0:
        return extra
    optional = [name for name in extra if name not in keep]
    discard = set((optional[1:] + optional[:1])[:overflow])
    return {name: image for name, image in extra.items() if name not in discard}


def package(expected):
    original_prepare = packets.prepare

    def prepare(selection):
        made, visual, stage = packets.old.made, packets.visual, packets.stage_pack
        counts = {}
        primary = {}

        def remember(entry, ident, hashes, font):
            result = made(entry, ident, hashes, font)
            primary[ident] = result[0]
            return result

        def display(row, reference, origin, ident, font):
            extra, guide, parts = visual(row, reference, origin, ident, font)
            required = required_supplements(row, ident)
            if required:
                if LEGACY_DESCRIPTION not in guide:
                    raise ValueError("差し替え前の枠端画像の説明が見つからない")
                guide = guide.replace(LEGACY_DESCRIPTION, EDGE_NOTE, 1).replace(COORDINATE_NOTE, "")
            first = primary.pop(ident)
            selected = fit(first, extra, required)
            counts[ident] = set(first) | set(selected)
            return selected, guide, parts

        def verify(folder, name, items, archive):
            for ident, _, _, _, _, images in items:
                if set(images) != counts.pop(ident) or len(images) > LIMIT:
                    raise ValueError("添付する固定画像が途中で欠けた")
            return stage(folder, name, items, archive)

        packets.old.made, packets.visual, packets.stage_pack = remember, display, verify
        try:
            original_prepare(selection)
        finally:
            packets.old.made, packets.visual, packets.stage_pack = made, visual, stage

    packets.prepare = prepare
    try:
        original_package(expected)
    finally:
        packets.prepare = original_prepare


def verify_delivery(expected):
    """モデルへ渡す前に、固定された全束の必須画像と説明の対応を確かめる。"""
    path = core.OUT / "delivery/packages.json"
    content = core.load(path)
    if core.sha(path) != expected:
        raise ValueError("画像を確認する配布の固定値が違う")
    selection = core.OUT / "selection.json"
    rows = core.load(selection)["selected"]
    if content["source_sha256"] != core.sha(selection) or len(content["packs"]) != len(rows):
        raise ValueError("事前固定した正式な全行の束がない")
    seen, with_edge, with_margin, paired_coords = set(), 0, 0, 0
    for item in content["packs"].values():
        (ident, target), = item["mapping"].items()
        index = target["entry"]
        if index in seen or not 0 <= index < len(rows):
            raise ValueError("同じ行を複数回配ろうとしている")
        seen.add(index)
        names = item["request"]["images"]
        guide = item["request"]["prompt"]
        required = required_supplements(rows[index], ident)
        if (not required <= set(names) or len(set(names)) != len(names) or len(names) > LIMIT
                or (required and (EDGE_NOTE not in guide or "枠への入り方" in guide))):
            raise ValueError("正式な画像に必須の添付や説明がない")
        if any("-paragraph-margin" in n for n in required):
            if draft.bullet_stage.old.GUIDE not in guide:
                raise ValueError("段落の画像に必要な説明がない")
            with_margin += 1
        if rows[index]["allocation_axis"] == "x":
            width = rows[index]["box"][2]
            segments = packets.old.original.segments(3 * width)
            present = [int(n.removesuffix(".png").split("-coordinate-", 1)[1].split("+")[0])
                       for n in names if "-coordinate-" in n]
            joined = [int(n.removesuffix(".png").split("+")[1])
                      for n in names if "-coordinate-" in n and "+" in n]
            if sorted(present + joined) != list(range(1, len(segments) + 1)):
                raise ValueError("固定した横座標の一部が添付されていない")
            paired_coords += bool(joined)
        with_edge += bool(required)
    return {"rows": len(seen), "edge_rows": with_edge, "margin_rows": with_margin,
            "paired_coordinate_rows": paired_coords, "packages_sha256": expected}


def main():
    action = sys.argv[1] if len(sys.argv) > 1 else None
    if action == "package":
        draft.package = package
        try:
            draft.main()
        finally:
            draft.package = original_package
        print(verify_delivery(core.sha(core.OUT / "delivery/packages.json")), flush=True)
        return
    if action in ("initialize", "gpt", "claude"):
        verify_delivery(core.sha(core.OUT / "delivery/packages.json"))
    draft.inputs = inputs
    draft.main()


original_package = draft.package


if __name__ == "__main__":
    main()
