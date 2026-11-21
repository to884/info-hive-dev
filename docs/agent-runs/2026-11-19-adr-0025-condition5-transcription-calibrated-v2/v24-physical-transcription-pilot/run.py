"""点のまとまり、縦書きの筆画と枠端を同じ固定画像で比較する。"""

import argparse
from collections import Counter
from concurrent.futures import FIRST_COMPLETED, ThreadPoolExecutor, wait
from pathlib import Path
import sys
import time

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parent / "v19-reference-audit"))
import run as audit
sys.path.insert(0, str(HERE.parent / "v22-list-mark-pilot"))
from recover import inspect_attempt

reference = audit.as_reference()
trial = audit.frame.trial
OUT = audit.OUT.with_name("reference-v24-physical-transcription-pilot")
LOCK = HERE / "lock.json"
RESULT = HERE / "result.json"
SAMPLES = {
    ("defense-p0006", 54): "trails", ("defense-p0007", 56): "trails",
    ("disaster-p0015", 16): "trails", ("disaster-p0015", 17): "trails",
    ("defense-p0335", 38): "round", ("disaster-p0034", 31): "round",
    ("defense-p0219", 32): "body-and-round", ("defense-p0523", 86): "boundary",
    ("wp-summary-p0004", 2): "boundary", ("kanpo1826-p4-p0001", 0): "boundary",
    ("kanpo1827-p2-p0001", 119): "short", ("kanpo1827-p2-p0001", 331): "short",
    ("kanpo1828-p3-p0001", 87): "short", ("kanpo1828-p1-p0001", 56): "vertical-glyph",
    ("kanpo1828-p3-p0001", 144): "vertical-glyph", ("kanpo1828-p3-p0001", 201): "vertical-glyph",
    ("kanpo1828-p3-p0001", 47): "control-boundary", ("kanpo1828-p3-p0001", 185): "control-boundary",
    ("kanpo1827-p2-p0001", 49): "control-short", ("defense-p0050", 37): "control-body",
}
HORIZONTAL = (
    "同じ高さに小さい塗り点が等間隔で3個以上続き、字の間隔が見えない場合は、全体を1個の trail として記録します。"
    "各点の round を並べたり、点の数を文字数に直したりしません。離れた単独の小さい塗り点は、"
    "本文の中で中黒のように使われていても、字種が画素から特定できない場合は round です。"
    "round は同じ中心の座標を2回書きます。trail の始点と終点は、横座標画像の小目盛りを使ってそれぞれ取り直します。"
    "点列の次の数字や本文の端を、点列の最後と混同しません。"
)
DETAILS = (
    "回答前に枠ありと枠なしの字形を照合します。枠の端にある句読点は字の全長を枠内外で確かめ、"
    "本文中の小さな読点と括弧はそれぞれ画素が見える場所で数えます。"
    "見慣れない字・異体字は、部首、交差する線、曲がりと点を拡大の字形から確かめ、同音語や普通の字体へ直しません。"
    "数字に見える縦書きも、画素にある漢数字と算用数字をその形のまま返します。"
    "短い枠の孤立した一画や、隣の列の端が少し見えるときは、元の枠への所属を確かめ、"
    "読める字を枠の短さや文として不完全なことだけで判読不能にしません。"
)


def snapshot():
    canonical = audit.OUT / "delivery"
    packages = canonical / "packages.json"
    selection = audit.OUT / "selection.json"
    audit.verify_before_source()
    old = audit.load(selection)["selected"]
    labels = audit.load(audit.LABELS / "public.json")
    all_rows = {(r["key"], r["line_index"]): r for r in labels}
    rows = []
    for identity in SAMPLES:
        row = all_rows[identity]
        if row["effective"] is None:
            raise ValueError("開発用の既存正解を確認できない")
        rows.append(row)
    if len(old) != 377:
        raise ValueError("比較元は確定済みの開発資料から抽出した監査に限る")

    display = OUT / "display"
    display.mkdir(parents=True)
    point = display / "grid.json"
    selected = display / "selection.json"
    audit.save_once(point, audit.encoded({"inputs": {}}))
    audit.save_once(selected, audit.encoded({"selected": rows, "population_lock_sha256": audit.sha(point)}))
    audit.OUT, audit.LOCK = display, point
    audit.package(audit.sha(selected))

    produced = display / "delivery/packages.json"
    mapping, jobs = {}, {}
    for pack, batch in audit.load(produced)["packs"].items():
        cards = display / "delivery/cards" / pack
        request = batch["request"]
        for ident, found in batch["mapping"].items():
            row = rows[found["entry"]]
            kind = SAMPLES[row["key"], row["line_index"]]
            current = next(l for l in request["prompt"].splitlines() if l.startswith(ident + "。"))
            prefix = audit.packets.INTRO + "\n" + current
            ending = audit.packets.FORMAT + ident + "。"
            pairs = [(f, h) for f, h in zip(request["images"], request["image_sha256"], strict=True)
                     if f.startswith(ident + "-")]
            images, hashes = map(list, zip(*pairs, strict=True))
            identifier = f"case-{len(mapping):02d}"
            mapping[identifier] = {**found, "category": kind}
            guide = DETAILS + (HORIZONTAL if row["allocation_axis"] == "x" else "")
            for arm, extra in (("old", ""), ("new", guide)):
                jobs[f"{identifier}/{arm}"] = {"cards": str(cards), "request": {
                    "images": images, "image_sha256": hashes, "ids": [ident], "prompt": prefix + extra + ending}}
    deps = (Path(__file__), HERE / "protocol.md", packages, selection, produced, selected, Path(audit.__file__),
            audit.LABELS / "public.json", HERE.parent / "v22-list-mark-pilot/recover.py")
    return {"jobs": jobs, "mapping": mapping, "files": {str(p): audit.sha(p) for p in deps}}


def outcome(state, name, role, job, runtime, send=False):
    root = OUT / "reads" / name / role
    paths = sorted(root.glob("attempt-*"))
    old = {"availability": "unstarted"}
    attempts = []
    for i, folder in enumerate(paths, 1):
        claim = audit.load(folder / "claim.json")
        if (folder.name != f"attempt-{i:03d}" or claim != {
                "lock_sha256": state, "name": name, "role": role, "unix_time": claim["unix_time"], "previous": old}
                or old["availability"] not in {"unstarted", "quota-rejection"}
                or claim["unix_time"] < old.get("resets_at", 0)):
            raise ValueError("新しい会話の着手の来歴が異なる")
        old = inspect_attempt(folder / "raw", role, job, runtime, audit=audit, models=trial.MODELS)
        attempts.append(old)
    if send:
        now = int(time.time())
        if old["availability"] not in {"unstarted", "quota-rejection"} or now < old.get("resets_at", 0):
            return attempts
        folder = root / f"attempt-{len(paths) + 1:03d}"
        folder.mkdir(parents=True)
        audit.save_once(folder / "claim.json", audit.encoded({
            "lock_sha256": state, "name": name, "role": role, "unix_time": now, "previous": old}))
        target = folder / "raw"
        try:
            audit.SCHEMA_READER.read(role, trial.MODELS[role], Path(runtime["path"]), job["request"], Path(job["cards"]), target)
        except (ValueError, KeyError, TypeError, AttributeError, IndexError):
            if not (target / "process.json").exists():
                raise
        attempts.append(inspect_attempt(target, role, job, runtime, audit=audit, models=trial.MODELS))
    return attempts


def deliver(role, plan, runtimes, state):
    runtime = runtimes[role]
    queue = []
    for name, job in plan["jobs"].items():
        issued = outcome(state, name, role, job, runtime)
        if not issued or (issued[-1]["availability"] == "quota-rejection" and time.time() >= issued[-1]["resets_at"]):
            queue.append((name, job))
    waiting = iter(queue)
    running = {}
    halted = False
    slots = 6 if role == "gpt" else 3
    with ThreadPoolExecutor(max_workers=slots) as pool:
        while True:
            while not halted and len(running) < slots and (item := next(waiting, None)):
                name, job = item
                running[pool.submit(outcome, state, name, role, job, runtime, True)] = name
            if not running:
                break
            done, _ = wait(running, return_when=FIRST_COMPLETED)
            for f in done:
                last = f.result()[-1]
                print(running.pop(f), role, last["availability"], flush=True)
                halted |= last["availability"] == "quota-rejection"


def collect(plan, runtimes, state):
    outcomes = {}
    sessions = set()
    counts = {role: Counter() for role in trial.MODELS}
    for name, job in plan["jobs"].items():
        outcomes[name] = {}
        for role in trial.MODELS:
            attempts = outcome(state, name, role, job, runtimes[role])
            letter = attempts[-1]["availability"] if attempts else "unstarted"
            counts[role][letter] += 1
            for attempt in attempts:
                session = attempt.get("session")
                if session and session in sessions:
                    raise ValueError("開発の読み取りの会話が重複する")
                if session:
                    sessions.add(session)
            outcomes[name][role] = attempts
    print(counts, flush=True)
    if RESULT.exists() or any(s["received"] != len(plan["jobs"]) for s in counts.values()):
        return
    rows = audit.load(OUT / "display/selection.json")["selected"]
    comparisons = {}
    for name, job in plan["jobs"].items():
        case, arm = name.split("/")
        option = plan["mapping"][case]
        row = rows[option["entry"]]
        ident, = job["request"]["ids"]
        answers = [reference.decoded(o[-1]["answers"][ident], option["partitions"]) for o in outcomes[name].values()]
        expected = reference.NORMALIZE(row["effective"])
        paired, coordinates = reference.aligned(*answers, row["box"][2])
        tests = {"pair": paired, "coordinates": coordinates, "gpt": answers[0], "claude": answers[1]}
        if paired["status"] == "unreadable":
            category = "unresolved"
        elif coordinates:
            category = "both-location-needs-source"
        elif paired["text"] == expected:
            category = "same"
        elif paired["text"] and paired["text"] in expected:
            category = "omitted"
        elif expected in paired["text"]:
            category = "extra"
        else:
            category = "different"
        comparisons[name] = {
            "page": row["key"], "line_index": row["line_index"], "category": option["category"], "arm": arm,
            "pair_result": category, "readings": tests, "expected": expected,
        }
    audit.save_once(RESULT, audit.encoded({"scope": "development-only", "lock_sha256": state, "cases": comparisons}))


def main():
    cli = argparse.ArgumentParser(description=__doc__)
    cli.add_argument("action", choices=("prepare", "gpt", "claude", "collect"))
    cli.add_argument("--sha256")
    cli.add_argument("--codex", type=Path)
    cli.add_argument("--claude", type=Path)
    args = cli.parse_args()
    if args.action == "prepare":
        if LOCK.exists() or OUT.exists():
            raise FileExistsError("この開発用の比較は固定済み")
        audit.save_once(LOCK, audit.encoded(snapshot()))
        print(audit.sha(LOCK), len(SAMPLES), "行、同じ画素で二指示", flush=True)
        return
    plan = audit.load(LOCK)
    if (audit.sha(LOCK) != args.sha256 or
            any(audit.sha(Path(p)) != h for p, h in plan["files"].items())):
        raise ValueError("事前に固定した比較と異なる")
    runtimes = audit.delivery.runtime({"gpt": args.codex, "claude": args.claude})
    with audit.delivery.lease(OUT / "delivery.lease"):
        if args.action in trial.MODELS:
            deliver(args.action, plan, runtimes, args.sha256)
        collect(plan, runtimes, args.sha256)


if __name__ == "__main__":
    main()
