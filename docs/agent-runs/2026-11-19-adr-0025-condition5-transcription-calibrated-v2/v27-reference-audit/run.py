"""条件5を変えずに、固定した開発正解を別の二系統で監査する。"""

import argparse
from collections import Counter
import json
from pathlib import Path
import sys

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parent / "v19-reference-audit"))
import run as previous

module = previous.module
delivery_module = module("independent_audit_delivery", HERE / "delivery.py")
runner = module("audit_launch_boundary", HERE / "runner.py")
limits = module("audit_quota_suspicion", HERE / "limits.py")
ref = previous.ref
quota = module("image_request_quota_receipt", HERE.parent / "v22-list-mark-pilot/recover.py")
transport = delivery_module.Delivery(previous, quota.inspect_attempt, HERE / "launch-ledger", runner, limits)
load, sha, save_once, encoded = previous.load, previous.sha, previous.save_once, previous.encoded
baseline = previous.v14.old
CORPUS = previous.OUT.parent
OUT = CORPUS / "reference-audit-v27"
LOCK = HERE / "population-lock.json"
PLAN = HERE / "method.json"
SEEDS = {"region": 2026112005, "image": 2026112006}
EARLIER = previous.OLD_DRAWS + (previous.OUT / "selection.json",)
PYTHON_DEPS = (
    "v19-reference-audit/source.py", "v22-list-mark-pilot/recover.py", "v23-round-pixel-pilot/run.py",
    "v25-ellipsis-source-pilot/run.py", "v21-trail-source-pilot/run.py", "v20-trail-source-pilot/run.py",
    "v28-colored-point-source-pilot/run.py", "v35-coordinate-pilot/ruler.py",
)


def inputs(plan, report_path, labels):
    checked = previous.inputs()
    choices = tuple(HERE.parent / name for name in PYTHON_DEPS)
    paths = (Path(__file__), HERE / "delivery.py", HERE / "source.py", HERE / "protocol.md",
             HERE / "runner.py", HERE / "limits.py", PLAN, *choices, *EARLIER,
             previous.HERE / "result.json", previous.HERE / "diagnosis.json", report_path,
             labels / "public.json", labels / "scoring.json",
             *(HERE.parent / name for name in plan["development_results"]))
    return checked | {str(p.resolve()): sha(p) for p in paths}


def methods():
    plan = load(PLAN)
    if set(plan) != {"gold", "guides", "development_results", "direct_intake", "control_issues_seen", "ruler",
                     "transport_proof"}:
        raise ValueError("監査前に固定する方法の項目が異なる")
    if (any(k not in {"all", "x", "y"} or not isinstance(v, str) for k, v in plan["guides"].items())
            or any(not isinstance(row, list) or len(row) != 2 or type(row[1]) is not int for row in plan["direct_intake"])):
        raise ValueError("画像の指示または開発用行の記録が不明")
    if plan["ruler"] not in ("previous", "10-pixel-labels"):
        raise ValueError("固定画素の横座標の表示が不明")
    if plan["gold"] == "v19":
        return plan, previous.REPORT, previous.LABELS
    if plan["gold"] == "v26":
        return plan, HERE.parent / "v26-kanpo-name-candidate/candidate-score.json", previous.LABELS.with_name("v26-kanpo-name-candidate")
    if plan["gold"] == "v38":
        return plan, HERE.parent / "v38-reference-candidate/result.json", previous.LABELS.with_name("v38-reference-candidate")
    raise ValueError("既定の開発採点で確認していない正解")


def prepare():
    if OUT.exists() or LOCK.exists():
        raise FileExistsError("母集団は固定済み")
    before, _ = previous.v14.prepared()
    _, flags = baseline.take_public_rows()
    plan, result_file, labels = methods()
    initial = HERE.parent / plan["transport_proof"]
    checked = load(initial)
    expected_methods = ("delivery.py", "limits.py", "runner.py", "preflight.py")
    if (initial != HERE / "transport-preflight-final.json" or checked["scope"] != "development-only"
            or checked["methods"] != {name: sha(HERE / name) for name in expected_methods}
            or checked["received_sha256"] != sha(CORPUS / "reference-v27-transport-preflight-final/delivery/received.json")
            or plan["transport_proof"] not in plan["development_results"]):
        raise ValueError("配布コードの最終版と二系統の実地確認が結び付かない")
    result = load(result_file)
    if (result.get("development_control_issues", []) != plan["control_issues_seen"]
            or any(c["status"] != "unresolved" for c in plan["control_issues_seen"])):
        raise ValueError("開発対照で一方が異なった行の判断を事前固定できない")
    if (not result["evaluation"]["all_pass"] or not result["evaluation"]["all_gates"]
            or result["same_predictions_sha256"] != sha(baseline.PREDICTIONS)
            or any(sha(Path(p)) != h for p, h in result["inputs"].items())
            or any(sha(labels / name) != h for name, h in result["artifacts"].items())):
        raise ValueError("既定の全配置で開発採点を通過した正解を確認できない")
    records = load(labels / "public.json")
    earlier = {baseline.identity(r): r for r in load(previous.LABELS / "public.json")}
    newer = {baseline.identity(r): r for r in records}
    amended = {id for id in newer if newer[id] != earlier.get(id)}
    expected = set() if plan["gold"] == "v19" else {(r["page"], r["line_index"]) for r in result["changed"]}
    if len(records) != 8822 or newer.keys() != earlier.keys() or amended != expected:
        raise ValueError("母集団または二読で確定した訂正と異なる")
    pools = baseline.populations(records, flags)
    audited = {baseline.identity(r) for path in EARLIER for r in load(path)["selected"]}
    developed = {baseline.identity(r) for rows in before.values() for r in rows if r["development_intake"]}
    developed.update(baseline.identity(r) for r in load(previous.frame.HERE / "result.json")["rows"].values())
    developed.update(tuple(record) for record in plan["direct_intake"])
    for rows in pools.values():
        for row in rows:
            id = baseline.identity(row)
            row["previously_audited"] |= id in audited
            row["development_intake"] |= id in developed
    pinned = inputs(plan, result_file, labels)
    OUT.mkdir()
    save_once(OUT / "population.json", encoded(pools))
    save_once(LOCK, encoded({"scope": "fixed-before-sampling", "seeds": SEEDS,
                            "population_sha256": sha(OUT / "population.json"), "strata": baseline.strata(pools),
                            "versions": previous.versions(), "inputs": pinned}))
    print(sha(LOCK), "母集団を固定。抽出は未実行", flush=True)


def draw(expected):
    selection = previous.v14
    selection.OUT, selection.LOCK, selection.SEEDS = OUT, LOCK, SEEDS
    selection.draw(expected)


def stage_rows(stage, folder, _name, values, archive):
    for item in values:
        stage(folder, f"pack-{len(archive):03d}", [item], archive)


def package(expected):
    plan = load(PLAN)
    guides = plan["guides"]
    ruler = module("qualified_coordinate_display", HERE.parent / "v35-coordinate-pilot/ruler.py")
    typeface = previous.packets.old.base.FONTS / "meiryo.ttc"

    def visual(row, original, origin, ident, font):
        pngs, guide, parts = previous.visual(row, original, origin, ident, font)
        if row["allocation_axis"] == "x" and plan["ruler"] == "10-pixel-labels":
            fixed = CORPUS / "probe-v4/png" / (row["key"] + ".png")
            if sha(fixed) != original["sha"]["150_dpi"]:
                raise ValueError("横座標の表示元が固定画素と異なる")
            replace = ruler.cards(row, fixed, ident, previous.packets.old.original.segments, typeface)
            pngs.update(replace)
        return pngs, guide + guides.get("all", "") + guides.get(row["allocation_axis"], ""), parts

    previous.packets.OUT, previous.packets.visual = OUT, visual
    previous.packets.population.LOCK = LOCK
    stage = previous.packets.stage_pack
    previous.packets.stage_pack = lambda *args: stage_rows(stage, *args)
    try:
        previous.packets.prepare(expected)
    finally:
        previous.packets.stage_pack = stage


def verify_methods():
    data = load(LOCK)
    if (data["versions"] != previous.versions() or data["seeds"] != SEEDS
            or any(sha(Path(name)) != digest for name, digest in data["inputs"].items())):
        raise ValueError("正解、監査の方法または実行環境が事前固定と異なる")


def old_sessions():
    tokens = previous.previous_ids()
    roots = [r for r in CORPUS.glob("reference-*") if r != OUT]
    for root in roots:
        for file in root.rglob("response.jsonl"):
            with file.open("rb") as f:
                for line in f:
                    try:
                        e = json.loads(line)
                    except (ValueError, UnicodeError):
                        continue
                    t = e.get("thread_id") if e.get("type") == "thread.started" else (
                        e.get("session_id") if e.get("type") == "system" and e.get("subtype") == "init" else None)
                    if t:
                        tokens.add(t)
                        break
    return tokens


def image_cases(shipment, older):
    folder, manifest = shipment.folder, shipment.document
    selection = OUT / "selection.json"
    if manifest["source_sha256"] != sha(selection) or load(selection)["population_lock_sha256"] != sha(LOCK):
        raise ValueError("監査で読んだ行、母集団と画像が異なる")
    entries = load(selection)
    if any(len(batch["mapping"]) != 1 or len(batch["request"]["ids"]) != 1 for batch in manifest["packs"].values()):
        raise ValueError("開発用の二読と同じ一行単位で配布していない")
    archived, readings = transport.collect(shipment, older)
    if archived != load(folder / "received.json"):
        raise ValueError("確定時の原票・利用枠の証跡を再現できない")
    point_guard = module("verified_round_shape", HERE.parent / "v23-round-pixel-pilot/run.py")
    result = {}
    for name, batch in manifest["packs"].items():
        for ident, mapped in batch["mapping"].items():
            n = mapped["entry"]
            if n in result or not 0 <= n < len(entries["selected"]):
                raise ValueError("正式な行が重複しているか標本外")
            row, assets = entries["selected"][n], mapped["image_reference"]
            votes = [ref.decoded(v.get(ident, ref.UNKNOWN), mapped["partitions"]) for v in readings[name].values()]
            answer, at = ref.aligned(*votes, row["box"][2])
            reason = "plain-unresolved"
            if any(ident not in v for v in readings[name].values()):
                reason = "technical-incomplete"
            if point_guard.unverified_round(answer, row, assets["sha"], at):
                answer, reason = ref.UNKNOWN, "unverified-small-round"
            result[n] = {"row": row, "answer": answer, "coordinates": at, "assets": assets, "reason": reason}
    if len(result) != len(entries["selected"]):
        raise ValueError("正式な標本の全行を読取と結べない")
    return list(result.values()), entries["summary"]


def state(shipment):
    for role in shipment.document["models"]:
        counts, latest = Counter(), 0
        for name in shipment.document["packs"]:
            seen = transport.attempts(shipment, name, role)
            last = seen[-1]["receipt"] if seen else {"availability": "unstarted"}
            counts[last["availability"]] += len(shipment.document["packs"][name]["request"]["ids"])
            latest = max(latest, last.get("resets_at", 0))
        print(role, "行数", dict(counts), "利用枠", latest, flush=True)


def main():
    cli = argparse.ArgumentParser(description=__doc__)
    cli.add_argument("action", choices=("prepare", "draw", "package", "initialize", "gpt", "claude", "status", "close", "source"))
    cli.add_argument("--sha256")
    cli.add_argument("--codex", type=Path)
    cli.add_argument("--claude", type=Path)
    cli.add_argument("--continue-after-technical", action="store_true")
    args = cli.parse_args()
    if args.action == "prepare":
        prepare()
    elif args.action == "draw":
        verify_methods()
        draw(args.sha256)
    elif args.action == "package":
        verify_methods()
        package(args.sha256)
    else:
        verify_methods()
        folder = (OUT / "delivery").resolve(strict=True)
        start = {"gpt": args.codex, "claude": args.claude} if args.action in ("initialize", "gpt", "claude") else None
        shipment = transport.check(folder, args.sha256, start)
        if args.action in shipment.document["models"]:
            transport.run_role(shipment, args.action, args.continue_after_technical)
        elif args.action == "close":
            print(transport.close(shipment, old_sessions()), flush=True)
        elif args.action == "source":
            source = module("segregated_confirmed_pdf_source", HERE / "source.py")
            source.finish(sys.modules[__name__], shipment, old_sessions())
        elif args.action in ("status", "initialize"):
            state(shipment)


if __name__ == "__main__":
    main()
