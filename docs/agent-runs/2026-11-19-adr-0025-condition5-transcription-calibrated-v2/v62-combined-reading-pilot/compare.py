"""保存済みの監査票と新しい二票を、同じ既存正解で比較する。"""

import argparse
from collections import Counter, defaultdict
from difflib import SequenceMatcher
from pathlib import Path

from prepare import HERE, audit, core, identity, pilot, render

reference = core.ref
previous = render.previous


def verdict(vote, expected):
    if vote["status"] == "unreadable":
        return "unresolved"
    text = reference.NORMALIZE(vote["text"])
    if reference.MARK.search(text):
        return "source-pending"
    if text == expected:
        return "same"
    ops = {kind for kind, *_ in SequenceMatcher(None, expected, text, autojunk=False).get_opcodes()} - {"equal"}
    return {"delete": "omitted", "insert": "extra"}.get(next(iter(ops)), "different") if len(ops) == 1 else "different"


def preserved(path, doc):
    value = core.encoded(doc)
    if not path.exists():
        core.save_once(path, value)
    elif path.read_bytes() != value:
        raise ValueError("確定の証跡を別の結果で上書きできない")


def source_updates(pending, display):
    if not pending:
        return {}, {}
    stages = HERE.parent
    bridge = previous.module("approved_pdf_routes", stages / "v49-combined-frame-bullets-pilot/compare.py")
    strict = previous.module("verified_450_dpi_point", audit.draft.raster_file)
    vertical = previous.module("vertical_command_without_visible_text", stages / "v61-vertical-point-command-pilot/run.py")
    request, statements = (display / f"source-{part}.json" for part in ("request", "commands"))
    preserved(request, {"pages": sorted({t["row"]["key"] for t in pending.values()})})
    if not statements.exists():
        bridge.old_source.initial.collect(request, statements)
    data = core.load(statements)
    reference.checked_source(data, request)
    delivery = display / "delivery"
    hashes = core.load(delivery / "packages.json")["source_assets"]
    catalog, loaded = previous.packets.old.lookup()[1], {}
    checked = {}
    for name, item in pending.items():
        value, detail = reference.v10.resolved(item, data)
        if detail not in ("source-location-not-proven", "source-unavailable"):
            checked[name] = value, detail
            continue
        matched = bridge.baseline.fallback(core, item, data, catalog, loaded, bridge.ROUTES)
        if matched:
            checked[name] = matched
            continue
        row, assets = item["row"], item["assets"]
        key = row["key"]
        doc, sha, number = catalog[key]
        if doc not in loaded:
            loaded[doc] = (core.CORPUS / doc).read_bytes()
        high = assets["source_view"]["views"][1]
        frame = next(v["image"] for v in high["images"] if v["kind"] == "plain")
        fixed = delivery / "source-assets" / frame
        low = core.CORPUS / "probe-v4/png" / (key + ".png")
        record = data["evidence"].get(key, {})
        args = fixed, hashes[frame], low, loaded[doc], sha, number
        if record.get("pdf_sha256") == assets["sha"]["pdf_sha256"] and "unsupported" not in record:
            high_proof = strict.confirm(item, *args, record["commands"])
            if high_proof:
                value, proof = high_proof
                checked[name] = value, {"route": "fixed-450-dpi-location", "proof": proof}
                continue
        try:
            isolated = vertical.prove(item, *args)
        except ValueError as error:
            if str(error) not in {
                "固定した450 DPIと枠の対応が不明",
                "片方の閾値で両票の位置に同じ点を一つに絞れない",
                "二つの閾値で得た点が同じ位置にない",
            }:
                raise
            isolated = None
        if isolated:
            value, proof = isolated
            checked[name] = value, {"route": "single-vertical-source-command", "proof": proof}
        else:
            checked[name] = reference.UNKNOWN, detail
    return checked, {str(p): core.sha(p) for p in
                     (request, statements, Path(bridge.__file__), Path(strict.__file__), Path(vertical.__file__))}


def main():
    cli = argparse.ArgumentParser(description=__doc__)
    cli.add_argument("--sha256", required=True)
    cli.add_argument("--codex", required=True, type=Path)
    cli.add_argument("--claude", required=True, type=Path)
    args = cli.parse_args()
    digest, plan = core.sha(pilot.LOCK), core.load(pilot.LOCK)
    if digest != args.sha256 or any(core.sha(Path(name)) != h for name, h in plan["files"].items()):
        raise ValueError("固定した開発行と画像が異なる")
    core.verify_methods()
    old = core.OUT / "delivery"
    shipment = core.transport.check(old, core.sha(old / "packages.json"))
    source_file = core.OUT / "reference-evidence.json"
    result = core.load(audit.HERE / "result.json")
    if result["reference_sha256"] != core.sha(source_file):
        raise ValueError("出典の確認を済ませた旧の二票が変わった")
    grades = core.load(source_file)
    display = pilot.OUT / "display"
    rows = core.load(display / "selection.json")["selected"]
    guard = previous.module("archived_point_shape_ownership", HERE.parent / "v23-round-pixel-pilot/run.py")
    runtimes = pilot.audit.delivery.runtime({"gpt": args.codex, "claude": args.claude})
    fresh_sessions, saved_sessions = set(), set()
    cases, pending = {}, {}
    roles = ("gpt", "claude")
    for name, job in plan["jobs"].items():
        link = plan["mapping"][name.split("/")[0]]
        row = rows[link["entry"]]
        page, index = identity(row)
        expected, assets = row["effective"], link["image_reference"]
        label, = job["request"]["ids"]
        cached, opened = {}, {}
        for role in roles:
            prior = core.transport.attempts(shipment, link["baseline_packet"], role)[-1]["receipt"]
            new = pilot.outcome(digest, name, role, job, runtimes[role])
            if not new or new[-1]["availability"] != "received" or prior["availability"] != "received":
                raise ValueError(f"原票がそろわない {page}:{index} {role}")
            answer = new[-1]
            if answer["session"] in fresh_sessions:
                raise ValueError("開発用の読取セッションを再利用した")
            fresh_sessions.add(answer["session"])
            saved_sessions.add(prior["session"])
            cached[role] = reference.decoded(prior["answers"][link["baseline_label"]], link["baseline_partitions"])
            opened[role] = reference.decoded(answer["answers"][label], link["partitions"])
        paired, points = reference.aligned(*(opened[r] for r in roles), row["box"][2])
        if guard.unverified_round(paired, row, assets["sha"], points):
            paired = reference.UNKNOWN
        elif points:
            pending[name] = {"row": row, "answer": paired, "coordinates": points, "assets": assets}
        before = grades[f"{page}/{index}"]["answer"]
        cases[name] = {"page": page, "line_index": index, "category": link["category"], "expected": expected,
                       "before": {**cached, "pair": before}, "after": {**opened, "pair": paired}}
    if fresh_sessions & saved_sessions:
        raise ValueError("前回の票と開発で作った票に同一のセッションがある")
    source, inputs = source_updates(pending, display)
    counts = defaultdict(lambda: defaultdict(Counter))
    for name, case in cases.items():
        if name in source:
            case["after"]["pair"], case["source"] = source[name]
        case["outcomes"] = {}
        for stage in ("before", "after"):
            decisions = {role: verdict(vote, case["expected"]) for role, vote in case[stage].items()}
            case["outcomes"][stage] = decisions
            for role, value in decisions.items():
                counts[stage][role][value] += 1
        print(case["page"], case["line_index"], case["category"], case["outcomes"], flush=True)
    preserved(HERE / "comparison.json", {"scope": "development-only", "lock_sha256": digest, "cases": cases,
                                         "counts": counts, "source_inputs": inputs})
    print({s: {r: dict(v) for r, v in c.items()} for s, c in counts.items()}, flush=True)


if __name__ == "__main__":
    main()
