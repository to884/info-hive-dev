"""一度固定した監査の束を配布し、技術未決定も原票とともに残す。"""

import argparse
from collections import Counter
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path
import subprocess

from cards import HERE, OUT, PACKS, inputs, load, sha
from readers import encoded, read, receive, save_once
from selection import PREVIOUS_AUDIT

WORKERS = 6
START = HERE / "delivery-started.json"


def prior_sessions():
    before = load(PREVIOUS_AUDIT)
    nonreusable = set(before["forbidden_agents"]) | set(before["forbidden_sessions"])
    for r in PREVIOUS_AUDIT.parent.glob("receipt-*.json"):
        record = load(r)
        for key in ("session_id", "agent_id"):
            if record.get(key):
                nonreusable.add(record[key])
    return nonreusable


def checked(expected):
    manifest = load(PACKS)
    if sha(PACKS) != expected or manifest["inputs"] != inputs():
        raise ValueError("固定した監査の配布が異なる")
    for name, value in manifest["packs"].items():
        request = value["request"]
        directory = OUT / "cards" / name
        if {p.name for p in directory.iterdir()} != set(request["images"]):
            raise ValueError("元カードが増減した")
        for label, digest in zip(request["images"], request["image_sha256"], strict=True):
            if sha(directory / label) != digest:
                raise ValueError("添付が固定と異なる")
    return manifest


def run(expected, executables, collect_only=False):
    destination = HERE / "received.json"
    if destination.exists():
        raise FileExistsError("正式監査の二票を受領済み")
    if not collect_only and any(p is None or not p.is_file() for p in executables.values()):
        raise ValueError("二つの監査用CLIが必要")
    manifest = checked(expected)
    if collect_only:
        commitment = load(START)
        if commitment["packages_sha256"] != expected:
            raise ValueError("最初の配布と異なる原票を受領できない")
        runtime = commitment["runtime"]
    else:
        if START.exists():
            raise FileExistsError("監査の呼び出しは一回。保存した原票の受領だけできる")
        runtime = {}
        for family, exe in executables.items():
            exe = exe.resolve()
            version = subprocess.run([str(exe), "--version"], capture_output=True, check=True, timeout=20)
            runtime[family] = {"path": str(exe), "sha256": sha(exe), "version": version.stdout.decode("utf-8").strip(),
                               "reader_sha256": sha(HERE / "readers.py")}
        commitment = {"packages_sha256": expected, "runtime": runtime}
    lock = OUT / "delivery-running.json"
    save_once(lock, encoded({"packages_sha256": expected}))
    try:
        if not collect_only:
            save_once(START, encoded(commitment))
        readers = OUT / "reads"
        if readers.exists() and {p.name for p in readers.iterdir()} - manifest["packs"].keys():
            raise ValueError("当初の束以外の原票を検出")
        failures, observed = [], {}
        if not collect_only:
            with ThreadPoolExecutor(max_workers=WORKERS) as pool:
                calls = {}
                for name, job in manifest["packs"].items():
                    for family, model in manifest["models"].items():
                        read_dir = OUT / "reads" / name / family
                        show = OUT / "cards" / name
                        future = pool.submit(read, runtime[family], family, model, job["request"], show, read_dir)
                        calls[future] = name, family
                for task in as_completed(calls):
                    name, family = calls[task]
                    try:
                        received = task.result()
                    except (OSError, TypeError, ValueError, KeyError) as e:
                        failures.append({"pack": name, "family": family, "error": type(e).__name__})
                    else:
                        observed[name, family] = received
        if failures:
            save_once(OUT / "delivery-or-integrity-errors.json", encoded(failures))
            raise ValueError("監査の受領中に配布の整合性を確認できない束がある")
        used, nonreusable = set(), prior_sessions()
        report, counts = {}, {}
        for name, job in manifest["packs"].items():
            report[name] = {}
            for family, model in manifest["models"].items():
                folder = OUT / "reads" / name / family
                if folder.parent.exists() and {p.name for p in folder.parent.iterdir()} - manifest["models"].keys():
                    raise ValueError("同じ束に当初と異なる担当の票がある")
                again = receive(folder, family, model, job["request"], OUT / "cards" / name, runtime[family])
                if not collect_only and again != observed[name, family]:
                    raise ValueError("監査の原票が受領中に変化")
                session = again.get("session")
                if session is not None:
                    if session in used or session in nonreusable:
                        raise ValueError("旧版、別の役割または別の束のセッションを使った")
                    used.add(session)
                report[name][family] = {k: v for k, v in again.items() if k != "answers"}
                report[name][family]["files"] = {p.name: sha(p) for p in folder.iterdir()} if folder.exists() else {}
                counts.setdefault(family, Counter())[again["availability"]] += 1
        if manifest != checked(expected):
            raise ValueError("監査の配布が途中で変化")
        save_once(destination, encoded({"packages_sha256": expected, "delivery_sha256": sha(START), "votes": report,
                                       "counts": counts, "unique_sessions": len(used)}))
        print(counts, flush=True)
    finally:
        lock.unlink()


if __name__ == "__main__":
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--codex", type=Path)
    p.add_argument("--claude", type=Path)
    p.add_argument("--packages-sha256", required=True)
    p.add_argument("--collect-only", action="store_true")
    args = p.parse_args()
    run(args.packages_sha256, {"gpt": args.codex, "claude": args.claude}, args.collect_only)
