"""抽出・配布・構造化受領の各段階を別に実行する。"""

import argparse
from importlib.metadata import version
import importlib.util
import inspect
import json
from pathlib import Path
import re
import sys

HERE = Path(__file__).resolve().parent


def module(name, path):
    spec = importlib.util.spec_from_file_location(name, path)
    value = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(value)
    return value


frame = module("v18_display", HERE.parent / "v18-frame-and-points-pilot/run.py")
v15, readers = frame.old, frame.trial.readers
v14, delivery = v15.prior.population, v15.base
packets, ref = v15.prior, v15.reference
load, sha, save_once, encoded = v15.load, v15.sha, v15.save_once, v15.encoded
OUT = v15.OUT.with_name("reference-audit-v19")
OLD_DRAWS = (v14.old.OUT / "selection.json", v15.OUT / "selection.json")
LOCK = HERE / "population-lock.json"
SEEDS = {"region": 2026112003, "image": 2026112004}
STAGE = HERE.parent / "v19-reference-candidate"
REPORT = STAGE / "result.json"
LABELS = v14.CANDIDATE.parent / STAGE.name
SCHEMA_READER = frame.trial.structured
V14_DISPLAY = packets.visual
ENDED = HERE / "result.json"
PNG_ERROR = re.compile(r"(?:cannot|could not|unable to|failed to) (?:locate|load|read|open) (?:the )?(?:attached )?image[^\r\n]*\.png", re.I)


def previous_ids():
    found = set()
    for root in (v15.OUT, v15.prior.OUT):
        for file in (root / "delivery/reads").glob("*/*/response.jsonl"):
            for line in file.read_bytes().splitlines():
                e = json.loads(line)
                if e.get("type") == "thread.started" or (e.get("type") == "system" and e.get("subtype") == "init"):
                    found.add(e.get("thread_id", e.get("session_id")))
    if len(found) < 380:
        raise ValueError("旧監査のセッションをすべて確認できない")
    return found | delivery.prior_sessions()


def inputs():
    paths = (
        Path(__file__), HERE / "protocol.md", HERE / "source.py", REPORT,
        LABELS / "public.json", LABELS / "scoring.json", v14.RESULT, v14.LOCK, v14.old.PREDICTIONS,
        Path(v14.__file__), Path(packets.__file__), Path(frame.__file__), Path(ref.__file__),
        Path(delivery.__file__), Path(readers.__file__), Path(SCHEMA_READER.__file__),
        Path(frame.receipt.__file__), Path(frame.receipt.trial.session_and_response.__code__.co_filename),
        HERE.parent / "v19-object-source-pilot/trace.py", v15.HERE / "result.json",
        frame.HERE / "result.json", v15.HERE / "transport-proof.json", *OLD_DRAWS,
        HERE.parent / "v14-reference-audit/source.py",
        HERE.parent / "v11-visible-source-pilot/commands.py",
        HERE.parent / "v10-reference-audit/source_commands.py",
        HERE.parent / "v10-reference-audit/point_ink.py",
        HERE.parent / "v11-visible-source-pilot/round_overlap.py",
        HERE.parent / "dot-layout-v2/independent-pdf-commands.py",
        HERE.parent / "dot-layout-v2/independent-pdf-commands-v2.json",
    )
    audit_methods = (ref.v10.resolved, ref.v10.identity, ref.v10.summarize, ref.NORMALIZE,
                     v14.old.draw, v14.old.strata, v14.old.score.frozen.score_v4.score_v2.score.normalize)
    local = Path(v14.old.score.audit.ROOT).resolve()
    own = set(Path(p).resolve() for p in paths) | {Path(inspect.getfile(f)).resolve() for f in audit_methods}
    for item in tuple(sys.modules.values()):
        file = getattr(item, "__file__", None)
        if file:
            path = Path(file).resolve()
            if path.suffix == ".py" and path.is_relative_to(local):
                own.add(path)
    inherited = {}
    for lock in (v14.LOCK, v14.old.MANIFEST):
        for name, digest in load(lock)["inputs"].items():
            path = str(Path(name).resolve())
            if inherited.setdefault(path, digest) != digest or sha(Path(path)) != digest:
                raise ValueError("前版で固定した実装または資料が相違")
    return inherited | {str(p): sha(p) for p in sorted(own)}


def versions():
    return {key: version(key) for key in ("numpy", "scipy", "Pillow", "pypdf", "pypdfium2")}


def verify_before_source():
    lock = load(LOCK)
    if lock["versions"] != versions() or any(sha(Path(p)) != h for p, h in lock["inputs"].items()):
        raise ValueError("抽出時に固定した監査の実装、正規化または実行環境が変化")


def prepare():
    before, _ = v14.prepared()
    prior, flags = v14.old.take_public_rows()
    report = load(REPORT)
    if (not report["evaluation"]["all_pass"] or not report["evaluation"]["all_gates"]
            or report["same_predictions_sha256"] != sha(v14.old.PREDICTIONS)
            or any(sha(Path(p)) != h for p, h in report["inputs"].items())
            or any(sha(LABELS / k) != h for k, h in report["artifacts"].items())):
        raise ValueError("既定の採点を通過した訂正と来歴がそろわない")
    records = load(LABELS / "public.json")
    v14_by_id = {v14.old.identity(r): r for r in load(v14.CANDIDATE / "public.json")}
    newest = {v14.old.identity(r): r for r in records}
    if (len(prior) != 8822 or len(newest) != 8822 or newest.keys() != v14_by_id.keys()
            or {i for i in newest if newest[i] != v14_by_id[i]} != {(r["page"], r["line_index"]) for r in report["changed"]}):
        raise ValueError("既定の全評価行か今回の訂正が異なる")
    pools = v14.old.populations(records, flags)
    older = {v14.old.identity(r) for path in OLD_DRAWS for r in load(path)["selected"]}
    intake = {v14.old.identity(r) for items in before.values() for r in items if r["development_intake"]}
    intake.update(v14.old.identity(r) for r in load(frame.HERE / "result.json")["rows"].values())
    for group in pools.values():
        for r in group:
            ident = v14.old.identity(r)
            r["previously_audited"] |= ident in older
            r["development_intake"] |= ident in intake
    pinned = inputs()
    OUT.mkdir()
    save_once(OUT / "population.json", encoded(pools))
    save_once(LOCK, encoded({"scope": "fixed-before-sampling", "seeds": SEEDS,
                            "population_sha256": sha(OUT / "population.json"),
                            "strata": v14.old.strata(pools), "versions": versions(), "inputs": pinned}))
    print(sha(LOCK), "母集団を固定。抽出は未実行", flush=True)


def draw(expected):
    v14.OUT, v14.LOCK, v14.SEEDS = OUT, LOCK, SEEDS
    v14.draw(expected)


def visual(row, original, origin, ident, font):
    extra, _, names = V14_DISPLAY(row, original, origin, ident, font)
    axis = row["allocation_axis"]
    x, y, w, h = row["box"]
    if axis == "y":
        guide = packets.VERTICAL
    else:
        guide = packets.HORIZONTAL + frame.POINT_GUIDE.replace("枠の左を0とした点の中心です。", "固定150 DPIで枠の左を0とした点の中心です。")
        if h > 45:
            entry = {"asset": original["source_view"], "box": row["box"], "allocation_axis": "x"}
            view = original["source_view"]["views"][0]
            target = next(p["image"] for p in view["images"] if p["kind"] == "plain")
            path = packets.old.original.v1.REGION / "assets" / target
            extra.update(packets.old.x_coordinates(entry, ident, {path.resolve().as_posix(): origin["source_assets"][target]}, font))
    if names:
        guide += packets.SHORT
    if min(w, h) <= 35:
        guide += frame.FRAME_GUIDE + (
            "『枠への入り方』の最短目盛りは元の150 DPIの1画素で、長い目盛りは5画素です。"
            "この細かい目盛りは枠に入る長さの確認に使います。丸印の座標を返すときは『横座標』画像だけを使ってください。"
        )
        extra.update(frame.magnified(row, original["sha"], ident, font))
    return extra, guide, names


def package(expected):
    packets.OUT, packets.visual = OUT, visual
    packets.population.LOCK = LOCK
    packets.prepare(expected)


def receive(folder, family, model, request, cards, runtime):
    packet, process = folder / "start.json", folder / "process.json"
    if not process.exists():
        return {"availability": "technical-unresolved"}
    state, ended = load(packet), load(process)
    raw, err = (folder / "response.jsonl").read_bytes(), (folder / "stderr.txt").read_bytes()
    if ended["response_sha256"] != readers.sha(raw) or ended["stderr_sha256"] != readers.sha(err):
        raise ValueError("新しい読取の原票が変更された")
    schema = folder / "schema.json"
    last = folder / "last-message.json"
    contract = readers.encoded(SCHEMA_READER.schema(request["ids"]))
    expected = readers.command(runtime["path"], cards, request["images"], model, family, state["cwd"])
    if family == "gpt":
        expected[-1:-1] = ["--output-schema", str(schema), "--output-last-message", str(last)]
    else:
        expected.extend(["--json-schema", contract.decode("utf-8").strip()])
    payload = readers.request_payload(request, cards, family)
    if state != {"family": family, "model": model, "cwd": state["cwd"], "packet_sha256": readers.sha(payload),
                  "argv": expected, "executable_sha256": runtime["sha256"], "image_sha256": request["image_sha256"],
                  "schema_sha256": readers.sha(contract)} or schema.read_bytes() != contract:
        raise ValueError("原票の起動に使った条件と画像を確認できない")
    common = {"response_sha256": ended["response_sha256"]}
    if ended["returncode"] or PNG_ERROR.search(err.decode("utf-8", errors="replace")):
        return {"availability": "failed-technical", **common}
    if ended["last_sha256"] != (sha(last) if last.is_file() else None):
        raise ValueError("最終応答の保存が異なる")
    try:
        stream = [json.loads(line, object_pairs_hook=readers.json_pairs) for line in raw.splitlines() if line.strip()]
        session, payload = frame.receipt.validated(stream, family, model, last.read_text(encoding="utf-8") if last.is_file() else None)
        answers = frame.trial.entries(payload, request["ids"])
    except (ValueError, AttributeError, TypeError, KeyError, IndexError):
        return {"availability": "invalid-technical", **common}
    return {"availability": "received", "session": session, "answers": answers, **common}


def read(runtime, family, model, request, cards, folder):
    try:
        SCHEMA_READER.read(family, model, Path(runtime["path"]), request, cards, folder)
    except (ValueError, KeyError, TypeError, AttributeError, IndexError):
        if not (folder / "process.json").exists():
            raise
    final = receive(folder, family, model, request, cards, runtime)
    print(folder.parent.name, family, final["availability"], flush=True)
    return final


def as_reference():
    ref.OUT, ref.DELIVERY = OUT, OUT / "delivery"
    ref.PACKS, ref.READ = ref.DELIVERY / "packages.json", ref.DELIVERY / "received.json"
    ref.START, ref.REQUESTS, ref.PROOF = ref.DELIVERY / "delivery-started.json", OUT / "source-requests.json", OUT / "source-commands.json"
    ref.receive = receive
    return ref


def main():
    cli = argparse.ArgumentParser(description=__doc__)
    cli.add_argument("action", choices=("prepare", "draw", "package", "deliver", "status", "close", "source-requests"))
    cli.add_argument("--sha256")
    cli.add_argument("--codex", type=Path)
    cli.add_argument("--claude", type=Path)
    args = cli.parse_args()
    if args.action == "prepare":
        prepare()
    elif args.action == "draw":
        draw(args.sha256)
    elif args.action == "package":
        package(args.sha256)
    elif args.action == "source-requests":
        as_reference().prepare_source()
    else:
        delivery.read, delivery.receive = read, receive
        existing = previous_ids()
        delivery.prior_sessions = lambda: existing
        delivery.run((OUT / "delivery").resolve(strict=True), args.sha256, args.action, {"gpt": args.codex, "claude": args.claude})


if __name__ == "__main__":
    main()
