"""事前に固定した画像表示と出典で二つの監査を一度実行する。"""

import argparse
from pathlib import Path
import sys

from PIL import Image

import provenance

provenance.install()
HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parent / "v67-neutral-transcription-pilot"))
import neutral

from capacity import capacity

render = neutral.render
audit, core, previous = render.audit, render.core, render.previous
source = previous.module("scoped_audit_source", HERE / "source.py")
PRIOR = audit.HERE
PILOT = Path(render.__file__).parent
NEUTRAL = Path(neutral.__file__).parent
CANDIDATE = HERE.parent / "v70-reference-candidate"
OUT = core.CORPUS / "reference-audit-v64"
LOCK, PLAN = HERE / "population-lock.json", HERE / "method.json"
PREFLIGHT = HERE / "preflight.json"
REVIEW = HERE / "review-source-regression-opus.md"
SEEDS = {"region": 2026112009, "image": 2026112010}
primitives = core.inputs
TRACE = "display-evidence.json"
DEFERRED = (
    "v19-reference-audit/source.py",
    "v23-round-pixel-pilot/run.py",
    "v25-ellipsis-source-pilot/run.py",
    "v27-reference-audit/diagnose.py",
    "v28-colored-point-source-pilot/run.py",
    "v35-coordinate-pilot/ruler.py",
)


def loaded_dependencies():
    for name in DEFERRED:
        previous.module("verified_" + name.removesuffix(".py").replace("/", "_").replace("-", "_"), HERE.parent / name)
    return provenance.snapshot()


def dependencies():
    archive = core.CORPUS / "reference-audit-v47"
    files = (Path(__file__), Path(source.__file__), Path(provenance.__file__),
             HERE / "capacity.py", HERE / "preflight.py", HERE / "protocol.md",
             REVIEW, HERE / "review-qualification-opus.md", HERE / "review-qualification-followup-opus.md",
             Path(render.__file__), Path(render.orientation.__file__), Path(render.instructions.__file__),
             Path(render.short.__file__), Path(render.horizontal.__file__), render.typeface, source.vertical_path,
             source.vertical_path.parent / "result.json", PRIOR / "population-lock.json", PRIOR / "method.json",
             PRIOR / "result.json", PRIOR / "diagnosis.json", PRIOR / "preflight-final.json",
             Path(audit.__file__), Path(render.draft.__file__), render.draft.raster_file, render.draft.edge_file,
             render.draft.bullet_file,
             PILOT / "comparison.json", PILOT / "lock.json", PILOT / "review-opus.md",
             NEUTRAL / "comparison.json", NEUTRAL / "lock.json", Path(neutral.__file__),
             NEUTRAL / "prepare.py", NEUTRAL / "grade.py",
             HERE.parent / "v68-neutral-kanpo-confirmation/comparison.json",
             HERE.parent / "v69-neutral-rounded-source-pilot/lock.json",
             HERE.parent / "v69-neutral-rounded-source-pilot/comparison.json",
             HERE.parent / "v69-neutral-rounded-source-pilot/source-result.json",
             core.CORPUS / "reference-v62-combined-reading-pilot/display/source-commands.json",
             archive / "selection.json", archive / "source-commands.json",
             archive / "delivery/packages.json", archive / "delivery/received.json",
             CANDIDATE / "result.json", CANDIDATE / "score.py")
    prior = core.load(PRIOR / "preflight-final.json")["inputs"]
    if any(core.sha(Path(f)) != h for f, h in prior.items()):
        raise ValueError("既存の配布・出典の事前検査で固定した入力が変わった")
    return prior | loaded_dependencies() | {str(p.resolve()): core.sha(p) for p in files}


def trial_method():
    old = core.load(PRIOR / "method.json")
    table = list(old["development_results"])
    used = {tuple(row) for row in old["direct_intake"]}
    for index in range(50, 70):
        for file in core.CORPUS.glob(f"reference-v{index}-*/display/selection.json"):
            used.update((r["key"], r["line_index"]) for r in core.load(file)["selected"])
    table.extend(("v61-vertical-point-command-pilot/result.json", "v62-combined-reading-pilot/comparison.json",
                  "v63-contiguous-pixel-strips-pilot/comparison.json", "v65-character-separation-pilot/comparison.json",
                  "v67-neutral-transcription-pilot/comparison.json", "v68-neutral-kanpo-confirmation/comparison.json",
                  "v69-neutral-rounded-source-pilot/source-result.json", "v70-reference-candidate/result.json"))
    return {**old, **render.plan(old), "gold": "v70", "direct_intake": sorted(used), "development_results": table}


def candidate():
    data = core.load(CANDIDATE / "result.json")
    labels = previous.LABELS.with_name(CANDIDATE.name)
    if (not data["evaluation"]["all_pass"] or not data["evaluation"]["all_gates"]
            or any(core.sha(Path(f)) != h for f, h in data["inputs"].items())
            or any(core.sha(labels / f) != h for f, h in data["artifacts"].items())):
        raise ValueError("固定した開発の評価を通った画像正解が確認できない")
    return labels


def methods():
    plan = core.load(PLAN)
    if plan["gold"] != "v70" or plan["guides"] != render.plan(core.load(PRIOR / "method.json"))["guides"]:
        raise ValueError("固定された正解の版と画像指示が準備した方法と異なる")
    return plan, CANDIDATE / "result.json", candidate()


def check_preflight():
    proof = core.load(PREFLIGHT)
    expected = proof["inputs"]
    if (proof["scope"] != "development-only-before-sampling"
            or any(expected.get(f) != h for f, h in dependencies().items())
            or any(core.sha(Path(f)) != h for f, h in expected.items())
            or proof["method_sha256"] != core.sha(PLAN)
            or proof["versions"] != previous.versions()):
        raise ValueError("抽出前に固定した方法と事前確認が異なる")
    provenance.enforce(expected)
    return proof


def inputs(plan, report, labels):
    proof = check_preflight()
    return primitives(plan, report, labels) | proof["inputs"] | {
        str(p): core.sha(p) for p in (PLAN, PREFLIGHT, labels / "public.json")
    }


def configure():
    core.OUT, core.LOCK, core.PLAN, core.SEEDS = OUT, LOCK, PLAN, SEEDS
    core.EARLIER += (core.CORPUS / "reference-audit-v47/selection.json",)
    core.inputs = inputs
    core.methods = methods
    core.transport = core.delivery_module.Delivery(previous, core.quota.inspect_attempt, HERE / "launch-ledger",
                                                    core.runner, core.limits)


def verify_packages(expected):
    files = core.OUT / "delivery"
    with render.active():
        meta = audit.verify_delivery(expected)
        rows = core.load(core.OUT / "selection.json")["selected"]
        delivery = core.load(files / "packages.json")
        render.verify(rows, delivery["packs"])
    evidence = core.load(core.OUT / TRACE)
    if evidence["packages_sha256"] != expected or len(evidence["rows"]) != len(rows):
        raise ValueError("固定した全行の表示と省いた補助画像の証跡がない")
    crosses = 0
    for item in delivery["packs"].values():
        (ident, row_info), = item["mapping"].items()
        row = rows[row_info["entry"]]
        pictures = set(item["request"]["images"])
        display = evidence["rows"][f"{row['key']}/{row['line_index']}"]
        if (set(display["sizes"]) != pictures or not set(display["required_close_or_layout"]) <= pictures
                or not any("-close-" in p for p in pictures)):
            raise ValueError("枠端の細部や補助画像の証跡が添付した画像と異なる")
        guide = item["request"]["prompt"]
        if any(phrase in guide for phrase in neutral.REMOVED):
            raise ValueError("最終の画像依頼に除いた字体例が残る")
        if row["allocation_axis"] != "x":
            continue
        w, h = row["box"][2:]
        rule = render.horizontal.NEW_RULER if w > 120 else render.horizontal.OLD_RULER
        if rule not in guide:
            raise ValueError("横の座標画像と目盛りの説明が対応しない")
        if w < 90 or h > 35:
            continue
        view = row_info["image_reference"]["source_view"]["views"][1]
        name = next(entry["image"] for entry in view["images"] if entry["kind"] == "plain")
        src = files / "source-assets" / name
        if core.sha(src) != delivery["source_assets"][name]:
            raise ValueError("横枠の上下端の元画像が配布時の固定画像と異なる")
        with Image.open(src) as high:
            needed = bool(render.cross(high, view["target_rectangle"]))
        attached = f"{ident}-cross-frame.png" in item["request"]["images"]
        if needed != attached or needed != (render.orientation.HORIZONTAL in guide):
            raise ValueError("横枠の上下端の画像と説明が揃わない")
        crosses += needed
    meta["cross_rows"] = crosses
    provenance.snapshot()
    return meta


def package(expected):
    shown = {}
    with neutral.active(shown):
        audit.package(expected)
    digest = core.sha(core.OUT / "delivery/packages.json")
    core.save_once(core.OUT / TRACE, core.encoded({"packages_sha256": digest, "rows": shown}))
    return verify_packages(digest)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("action", choices=("prepare", "draw", "package", "initialize", "gpt", "claude",
                                           "status", "close", "source", "diagnose"))
    parser.add_argument("--sha256")
    parser.add_argument("--codex", type=Path)
    parser.add_argument("--claude", type=Path)
    parser.add_argument("--continue-after-technical", action="store_true")
    args = parser.parse_args()
    configure()
    check_preflight()
    action = args.action
    if action == "prepare":
        core.prepare()
        return
    core.verify_methods()
    if action == "draw":
        core.draw(args.sha256)
        return
    if action == "package":
        print(package(args.sha256), flush=True)
        return
    if action == "diagnose":
        report = core.load(HERE / "result.json")
        if report["unsupported_point_sources_sha256"] != core.sha(OUT / "unsupported-point-sources.json"):
            raise ValueError("確定した出典の不足記録が元の記録と異なる")
        diagnosis = previous.module("fixed_three_way_diagnosis", core.HERE / "diagnose.py")
        diagnosis.audit, diagnosis.HERE = core, HERE
        diagnosis.main()
        return
    directory = OUT / "delivery"
    roles = ("initialize", "gpt", "claude")
    if action in roles:
        verify_packages(args.sha256)
        commands = {"gpt": args.codex, "claude": args.claude}
    else:
        commands = None
    shipment = core.transport.check(directory, args.sha256, commands)
    if action in shipment.document["models"]:
        core.transport.run_role(shipment, action, args.continue_after_technical)
    elif action == "close":
        print(core.transport.close(shipment, core.old_sessions()), flush=True)
    elif action == "source":
        source.close(shipment)
    else:
        core.state(shipment)


if __name__ == "__main__":
    main()
