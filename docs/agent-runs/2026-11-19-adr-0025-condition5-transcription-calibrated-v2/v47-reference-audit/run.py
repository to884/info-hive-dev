"""v27の固定と配送を使い、枠端の表示と小点の確認を加えた独立監査を行う。"""

import argparse
from pathlib import Path
import sys
from types import SimpleNamespace

from PIL import Image

HERE = Path(__file__).resolve().parent
PRIOR = HERE.parent / "v27-reference-audit"
sys.path.insert(0, str(HERE.parent / "v19-reference-audit"))
import run as previous

core = previous.module("same_audit_transport", PRIOR / "run.py")
core.OUT = core.CORPUS / "reference-audit-v47"
core.PLAN, core.LOCK = HERE / "method.json", HERE / "population-lock.json"
core.SEEDS = {"region": 2026112007, "image": 2026112008}
core.EARLIER += (core.CORPUS / "reference-audit-v27/selection.json",)
core.transport = core.delivery_module.Delivery(previous, core.quota.inspect_attempt, HERE / "launch-ledger",
                                                core.runner, core.limits)

edge_file = HERE.parent / "v45-edge-measurement-pilot/prepare.py"
bullet_file = HERE.parent / "v46-paragraph-circle-pilot/prepare.py"
raster_file = HERE.parent / "v44-small-point-pixel-pilot/run.py"
edge_stage = previous.module("boundaries_in_fixed_images", edge_file)
bullet_stage = previous.module("paragraph_mark_shapes", bullet_file)
edge_stage.earlier.panel = edge_stage.panel
source = previous.module("frozen_pdf_source_agreement", PRIOR / "source.py")
original_inputs, original_display = core.inputs, previous.visual


def inputs(plan, report, labels):
    files = (Path(__file__), HERE / "protocol.md", edge_file, bullet_file, raster_file, PRIOR / "result.json",
             PRIOR / "diagnosis.json", PRIOR / "population-lock.json",
             edge_file.parent.parent / "v43-frame-rectangle-pilot/prepare.py",
             edge_file.parent.parent / "v40-frame-edge-pilot/prepare.py",
             bullet_file.parent.parent / "v41-paragraph-bullets-pilot/prepare.py")
    return original_inputs(plan, report, labels) | {str(p): core.sha(p) for p in files}


def opened(row, original, origins):
    high = original["source_view"]["views"][1]
    n = next(v["image"] for v in high["images"] if v["kind"] == "plain")
    path = previous.packets.old.original.v1.REGION / "assets" / n
    low = core.CORPUS / "probe-v4/png" / (row["key"] + ".png")
    if core.sha(path) != origins["source_assets"][n] or core.sha(low) != original["sha"]["150_dpi"]:
        raise ValueError("枠端の表示元が固定した150 DPIと450 DPIに結び付かない")
    return low, path, high["target_rectangle"]


def frame(row, original, origins, ident, font):
    images, guide, parts = original_display(row, original, origins, ident, font)
    w, h = row["box"][2:]
    if min(w, h) > 35:
        return images, guide, parts
    low, high, transform = opened(row, original, origins)
    x, y, w, h = row["box"]
    with Image.open(low) as coarse, Image.open(high) as fine:
        borders = edge_stage.earlier.supplement(coarse, (x, y, x + w, y + h), fine, transform,
                                                row["allocation_axis"], ident, font)
    for name in [name for name in images if "-border-" in name]:
        del images[name]
    # 枠端の比較を同じ束から削らないよう、通常の大きい表示に続けて渡す。
    images = borders | images
    if row["allocation_axis"] == "x" and 120 < w <= 1200:
        images[ident + "-paragraph-margin.png"] = bullet_stage.old.margin(low, row["box"], ident, font)
    guide += edge_stage.earlier.GUIDE
    return images, guide, parts


def package(expected):
    previous.visual = frame
    try:
        core.package(expected)
    finally:
        previous.visual = original_display


def close_source(shipment):
    small = previous.module("visible_components_at_450", raster_file)
    old_fallback = source.fallback
    parts = shipment.document["source_assets"]
    folder = shipment.folder / "source-assets"

    def supplemental(mod, item, prior, catalog, loaded, routes):
        resolved = old_fallback(mod, item, prior, catalog, loaded, routes)
        if resolved:
            return resolved
        row, bound = item["row"], item["assets"]["source_view"]["views"][1]
        key = row["key"]
        source_map = prior["evidence"].get(key, {})
        if (not source_map or "unsupported" in source_map
                or source_map["pdf_sha256"] != item["assets"]["sha"]["pdf_sha256"]):
            return None
        basename, sha, number = catalog[key]
        if basename not in loaded:
            loaded[basename] = (core.CORPUS / basename).read_bytes()
        stem = next(v["image"] for v in bound["images"] if v["kind"] == "plain")
        low = core.CORPUS / "probe-v4/png" / (key + ".png")
        nearest = small.confirm(item, folder / stem, parts[stem], low, loaded[basename], sha, number,
                                source_map["commands"])
        if not nearest:
            return None
        value, proof = nearest
        return value, {"source-confirmed": proof, "route": "fixed-450-dpi-location-and-isolated-source"}

    bridge = SimpleNamespace(**{name: getattr(core, name) for name in (
        "verify_methods", "image_cases", "previous", "ref", "OUT", "encoded", "save_once", "load", "sha", "module", "CORPUS"
    )}, HERE=HERE)
    source.fallback = supplemental
    try:
        source.finish(bridge, shipment, core.old_sessions())
    finally:
        source.fallback = old_fallback


def main():
    cli = argparse.ArgumentParser(description=__doc__)
    cli.add_argument("action", choices=("prepare", "draw", "package", "initialize", "gpt", "claude", "status", "close", "source", "diagnose"))
    cli.add_argument("--sha256")
    cli.add_argument("--codex", type=Path)
    cli.add_argument("--claude", type=Path)
    cli.add_argument("--continue-after-technical", action="store_true")
    args = cli.parse_args()
    if args.action == "prepare":
        core.inputs = inputs
        core.prepare()
        return
    core.verify_methods()
    if args.action == "draw":
        core.draw(args.sha256)
    elif args.action == "package":
        package(args.sha256)
    elif args.action == "diagnose":
        diagnose = previous.module("final_reference_diagnosis", PRIOR / "diagnose.py")
        diagnose.audit, diagnose.HERE = core, HERE
        diagnose.main()
    else:
        d = (core.OUT / "delivery").resolve(strict=True)
        cli_roles = ("initialize", "gpt", "claude")
        exe = {"gpt": args.codex, "claude": args.claude} if args.action in cli_roles else None
        shipment = core.transport.check(d, args.sha256, exe)
        if args.action in shipment.document["models"]:
            core.transport.run_role(shipment, args.action, args.continue_after_technical)
        elif args.action == "close":
            print(core.transport.close(shipment, core.old_sessions()), flush=True)
        elif args.action == "source":
            close_source(shipment)
        else:
            core.state(shipment)


if __name__ == "__main__":
    main()
