"""条件を固定した残りの画像補充を個別に受領し、途中から再現できるようにする。"""

import argparse
from collections import Counter
from concurrent.futures import ThreadPoolExecutor, as_completed
from contextlib import contextmanager
import hashlib
import importlib.util
import inspect
import json
import os
from pathlib import Path
import subprocess

from PIL import Image, ImageFont

HERE = Path(__file__).resolve().parent
BEFORE = HERE.parent / "source-position-batches/run.py"
spec = importlib.util.spec_from_file_location("confirmation", BEFORE)
confirmed = importlib.util.module_from_spec(spec)
spec.loader.exec_module(confirmed)
previous, position, base = confirmed.old, confirmed.position, confirmed.base
v1, v2, pilot = previous.v1, previous.v2, previous.pilot
OUT = previous.OUT.parent / HERE.name
CARDS = OUT / "cards"
LOCK = HERE / "lock.json"
MAX_ROWS, MAX_IMAGES = 4, 22
WORKERS = 6


def raw_sha(data):
    return hashlib.sha256(data).hexdigest()


def prior_gate():
    old_root = BEFORE.parent
    lock_file, result_file = old_root / "lock.json", old_root / "result.json"
    lock, result = base.load(lock_file), base.load(result_file)
    if result["lock_sha256"] != base.sha(lock_file) or not result["advance"]:
        raise ValueError("同じ位置のみの確認が通過していない")
    cases = {previous.old.identity(r) for rows in lock["targets"].values() for r in rows.values()}
    return cases, {p.name + ":" + old_root.name: base.sha(p) for p in (lock_file, result_file)}


def add_package(name, cards, trace, labels, sources):
    images = sorted(n for n in cards if not n.endswith("-position-aux.png")) + sorted(
        n for n in cards if n.endswith("-position-aux.png"))
    ids = list(labels)
    prompt = (v1.INTRO + v2.NOTICE + previous.old.v3.shared + position.TASK
              + base.FORMAT + "、".join(ids) + "\n")
    return {"images": images, "ids": ids, "image_sha256": [raw_sha(cards[n]) for n in images],
            "prompt": prompt, "source_tiles": trace, "targets": sources}


def materialize():
    done, transition = prior_gate()
    historical, point_runs, projection, entries, image_index, old_rows, anchors, inputs = previous.inventory()
    del historical, point_runs, old_rows
    font_path = base.FONTS / "meiryo.ttc"
    primary_font, small = (ImageFont.truetype(font_path, size=n) for n in (17, 13))
    current, cards, private = {}, {}, {}
    grouped = {}
    for ident, bundle in sorted(anchors.items()):
        if ident not in done:
            grouped.setdefault(ident[0], []).append((ident, bundle))
    for page_key, selected in grouped.items():
        page = base.BENCH / "corpus/probe-v4/png" / (page_key + ".png")
        region = base.load(base.BENCH / "corpus/public/region-v9" / (page_key + ".json"))
        if base.sha(page) != region["image_sha256"]:
            raise ValueError("補助の固定画素と異なる")
        inputs[page.name] = region["image_sha256"]
        with Image.open(page) as png:
            full_image = png.convert("RGB")
        buffer, trace, labels, sources = {}, {}, {}, {}
        for ident, (record, truth) in selected:
            entry, measurement = entries[ident], projection[ident]
            if truth["dots"] != measurement["points"]:
                raise ValueError("二つの画像計測と出典の点数が異なる")
            i = f"Q{len(labels) + 1:02d}"
            primary, crops = v2.make_cards(entry, image_index, i, primary_font)
            if labels and (len(labels) == MAX_ROWS or len(buffer) + len(primary) + 1 > MAX_IMAGES):
                name = f"pack-{len(current):03d}"
                current[name] = add_package(name, buffer, trace, labels, sources)
                cards[name], private[name] = buffer, labels
                buffer, trace, labels, sources = {}, {}, {}, {}
                i = "Q01"
                primary, crops = v2.make_cards(entry, image_index, i, primary_font)
            if len(primary) + 1 > MAX_IMAGES:
                raise ValueError("固定行の元画像が一束の画像上限を超える")
            aid = position.position_card(full_image, entry["box"], measurement, i, small)
            first, last = position.expected_panels(i, entry, measurement, crops)
            qualification = dict(truth, position_signature=previous.old.MARKER.sub(
                f"⟦dotspan:{first}-{last}⟧", truth["signature"]))
            buffer.update(primary)
            buffer[f"{i}-position-aux.png"] = aid
            trace.update(crops)
            labels[i] = qualification
            sources[i] = {"key": page_key, "line_index": record["line_index"]}
        if labels:
            name = f"pack-{len(current):03d}"
            current[name] = add_package(name, buffer, trace, labels, sources)
            cards[name], private[name] = buffer, labels
    pins = (Path(__file__), HERE / "protocol.md", BEFORE, confirmed.FORMER, confirmed.POSITION,
            Path(v2.__file__), Path(v1.__file__), Path(base.__file__), Path(pilot.opus.__file__),
            Path(inspect.getfile(base.normalize)), font_path)
    inputs.update({p.parent.name + "/" + p.name: base.sha(p) for p in pins})
    signature_sha = raw_sha(json.dumps(private, ensure_ascii=False, sort_keys=True).encode())
    selected_count = sum(len(p["targets"]) for p in current.values())
    if selected_count != len(set(anchors) - done):
        raise ValueError("対象の対応が漏れている")
    contract = {"method": "position-only-source-backed", "inputs": inputs, "previous_confirmation": transition,
                "models": pilot.MODELS, "effort": "medium", "pack_limit": MAX_ROWS,
                "max_images": MAX_IMAGES, "count": selected_count, "packs": current,
                "scoring_reference_sha256": signature_sha}
    return cards, private, contract


@contextmanager
def worker_lock():
    path = OUT / "driver.lock"
    with path.open("x", encoding="utf-8") as stream:
        json.dump({"pid": os.getpid(), "started": base.utc_now()}, stream)
    try:
        yield
    finally:
        path.unlink()


def record(path, message):
    with path.open("x", encoding="utf-8") as stream:
        json.dump(message, stream, ensure_ascii=False, indent=2)


def raw_reply(reader, handle):
    arm, model, step = handle["arm"], handle["model"], handle.get("attempt")
    folder = OUT / "reads" / reader / arm
    basename = f"{arm}-read1-{model}"
    path = folder / (f"{basename}-{step}.jsonl" if reader == "sol" else f"{arm}-response.jsonl")
    if base.sha(path) != handle["response_sha256"]:
        raise ValueError("保存した原票が変わった")
    return path


def parse_saved(reader, receipt, request):
    if (receipt["prompt_sha256"] != raw_sha(request["prompt"].encode())
            or receipt["image_sha256"] != request["image_sha256"]):
        raise ValueError("保存した原票が同じ依頼のものではない")
    payload = raw_reply(reader, receipt).read_text(encoding="utf-8")
    if reader == "sol":
        membership, _, answer = base.parse_response(payload, request["ids"])
    else:
        answer, meta = pilot.opus.parse(payload, request["ids"])
        membership = meta["session_id"]
    if membership != receipt["session"]:
        raise ValueError("原票のセッションと受領のセッションが違う")
    return answer


def saved_or_fresh(exe, name, reader, pack):
    work = OUT / "receipts" / name / reader
    work.mkdir(parents=True, exist_ok=True)
    send = {k: v for k, v in pack.items() if k not in ("targets", "source_tiles")}
    # Solの下位処理は形式不正・技術障害に限って最大2試行を保持する。
    for n in ((1,) if reader == "sol" else (1, 2)):
        prefix = work / f"attempt-{n}.json"
        if prefix.exists():
            prior = base.load(prefix)
            if prior["status"] == "received":
                receipt = prior["receipt"]
                return parse_saved(reader, receipt, send), receipt
            continue
        handle = f"{name}-a{n}"
        started = work / f"attempt-{n}-started.json"
        if started.exists():
            folder = OUT / "reads" / reader / handle
            filename = (f"{handle}-read1-{pilot.MODELS[reader]}-receipt.json" if reader == "sol"
                        else f"{handle}-receipt.json")
            if (folder / filename).is_file():
                receipt = dict(base.load(folder / filename), role=reader)
                answer = parse_saved(reader, receipt, send)
                record(prefix, {"status": "received", "receipt": receipt})
                return answer, receipt
            record(prefix, {"status": "interrupted-technical", "arm": handle})
            continue
        record(started, {"status": "started", "arm": handle, "started": base.utc_now()})
        study = {"image_order_by_sheet": {"1": send["images"]},
                 "image_sha256": dict(zip(send["images"], send["image_sha256"], strict=True))}
        rows = [{"id": i, "sheet": 1} for i in send["ids"]]
        try:
            answer, receipt = pilot.read(exe, reader, handle, send, rows, CARDS / name, study)
        except (RuntimeError, OSError, subprocess.TimeoutExpired) as error:
            record(prefix, {"status": "failed-technical", "arm": handle, "error_type": type(error).__name__})
            continue
        raw_reply(reader, receipt)
        record(prefix, {"status": "received", "receipt": receipt})
        return answer, receipt
    return None, None


def execute(args, cards, expected, manifest):
    if base.sha(LOCK) != args.lock_sha256 or {k: v for k, v in base.load(LOCK).items() if k != "fixed_at"} != manifest:
        raise ValueError("固定の版と違う")
    for pack, items in cards.items():
        if any((CARDS / pack / name).read_bytes() != value for name, value in items.items()):
            raise ValueError("配布画像が固定と異なる")
    destination = HERE / "result.json"
    if destination.exists():
        raise FileExistsError("開発用の二読結果はすでに確定している")
    pilot.OUT = OUT / "reads"
    executables = {"sol": args.codex.resolve(), "opus": args.claude.resolve()}
    totals, outcome, sessions = Counter(), {}, set()
    names = list(manifest["packs"])
    with worker_lock(), ThreadPoolExecutor(max_workers=WORKERS) as pool:
        for offset in range(0, len(names), WORKERS // 2):
            batch = names[offset:offset + WORKERS // 2]
            tasks = {pool.submit(saved_or_fresh, exe, name, who, manifest["packs"][name]): (name, who)
                     for name in batch for who, exe in executables.items()}
            incoming = {}
            for task in as_completed(tasks):
                address = tasks[task]
                ballots, receipt = task.result()
                if receipt is not None:
                    session = receipt["session"]
                    if session in sessions:
                        raise ValueError("同じセッションが複数の票に入った")
                    sessions.add(session)
                incoming[address] = ballots
            for name in batch:
                sol, opus = (incoming[name, who] for who in ("sol", "opus"))
                if sol is None or opus is None:
                    rows = {i: "technical-unresolved" for i in expected[name]}
                else:
                    rows = {i: position.decision(sol[i], opus[i], ref) for i, ref in expected[name].items()}
                path = OUT / "receipts" / name / "outcome.json"
                if path.exists():
                    if base.load(path) != rows:
                        raise ValueError("既存の評価と今回の原票からの再現が異なる")
                else:
                    record(path, rows)
                outcome[name] = rows
                totals.update(rows.values())
                print(f"{name} {len(outcome)}/{len(names)}", dict(Counter(rows.values())), flush=True)
        if materialize()[-1] != manifest or base.sha(LOCK) != args.lock_sha256:
            raise ValueError("読取の前後で対象と手順が変化")
        record(destination, {"lock_sha256": args.lock_sha256, "results": outcome, "counts": totals,
                             "unique_sessions": len(sessions), "scope": "development-label-intake"})
    print(json.dumps(totals, ensure_ascii=False), flush=True)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("action", choices=("prepare", "run"))
    parser.add_argument("--codex", type=Path)
    parser.add_argument("--claude", type=Path)
    parser.add_argument("--lock-sha256")
    args = parser.parse_args()
    cards, expected, manifest = materialize()
    if args.action == "prepare":
        if LOCK.exists() or CARDS.exists():
            raise FileExistsError("事前固定を上書きしない")
        for name, images in cards.items():
            dst = CARDS / name
            dst.mkdir(parents=True)
            for n, data in images.items():
                (dst / n).write_bytes(data)
        record(LOCK, dict(manifest, fixed_at=base.utc_now()))
        print(base.sha(LOCK), manifest["count"], "行", len(manifest["packs"]), "束", flush=True)
    else:
        execute(args, cards, expected, manifest)


if __name__ == "__main__":
    main()
