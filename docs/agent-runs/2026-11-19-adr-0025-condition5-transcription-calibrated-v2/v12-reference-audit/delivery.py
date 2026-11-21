"""中断後に未着手の束だけを配布できる監査用の配送。"""

import argparse
from collections import Counter
from concurrent.futures import ThreadPoolExecutor, as_completed
from contextlib import contextmanager
import json
import os
from pathlib import Path
import subprocess
import sys

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parent / "v10-reference-audit"))
from readers import encoded, read, receive, request_payload, save_once
from runner import prior_sessions
from selection import load, sha

WORKERS = 6


@contextmanager
def lease(path):
    """OSがプロセスの終了時に解放する同時実行防止のロック。"""
    with path.open("a+b") as stream:
        if os.name == "nt":
            import msvcrt

            stream.seek(0)
            msvcrt.locking(stream.fileno(), msvcrt.LK_NBLCK, 1)
        else:
            import fcntl

            fcntl.flock(stream, fcntl.LOCK_EX | fcntl.LOCK_NB)
        yield


def checked(folder, expected):
    path = folder / "packages.json"
    manifest = load(path)
    if sha(path) != expected or any(sha(Path(p)) != digest for p, digest in manifest["inputs"].items()):
        raise ValueError("抽出後に固定した配布または方法が異なる")
    for name, data in manifest["packs"].items():
        if Path(name).name != name:
            raise ValueError("束のIDが不正")
        cards = folder / "cards" / name
        job = data["request"]
        if {p.name for p in cards.iterdir()} != set(job["images"]):
            raise ValueError("配布する画像に過不足")
        for family in manifest["models"]:
            request_payload(job, cards, family)
    reads = folder / "reads"
    if reads.exists() and {p.name for p in reads.iterdir()} - manifest["packs"].keys():
        raise ValueError("固定した束以外の原票がある")
    return manifest


def runtime(executables):
    values = {}
    for family, exe in executables.items():
        exe = exe.resolve(strict=True)
        version = subprocess.run([str(exe), "--version"], capture_output=True, check=True, timeout=20)
        script = HERE.parent / "v10-reference-audit/readers.py"
        values[family] = {"path": str(exe), "sha256": sha(exe), "version": version.stdout.decode("utf-8").strip(),
                          "reader_sha256": sha(script)}
    return values


def commitment(folder, expected, executables, action):
    path = folder / "delivery-started.json"
    live = runtime(executables) if action == "deliver" else None
    if not path.exists():
        if action != "deliver":
            raise FileNotFoundError("開始済みの監査の記録がない")
        save_once(path, encoded({"packages_sha256": expected, "runtime": live}))
    value = load(path)
    if value["packages_sha256"] != expected:
        raise ValueError("初回に配布した束と異なる")
    if action == "deliver" and value["runtime"] != live:
        raise ValueError("CLIまたは読取処理が初回と異なる")
    return value["runtime"]


def claimed(folder, name, family):
    return folder / "launches" / name / (family + ".json")


def claim_value(expected, name, family, model):
    return {"packages_sha256": expected, "pack": name, "family": family, "model": model}


def launch_one(folder, name, family, model, job, runtime, expected):
    mark = claimed(folder, name, family)
    mark.parent.mkdir(parents=True, exist_ok=True)
    # 原票と別に先に保存する。中断時に読み手への露出の有無を推測しない。
    save_once(mark, encoded(claim_value(expected, name, family, model)))
    return read(runtime, family, model, job, folder / "cards" / name, folder / "reads" / name / family)


def available(folder, manifest, runtimes, expected):
    seen, old = set(), prior_sessions()
    votes, states = {}, {}
    allowed = {claimed(folder, name, family) for name in manifest["packs"] for family in manifest["models"]}
    if any(p.is_file() and p not in allowed for p in (folder / "launches").glob("*/*")):
        raise ValueError("固定した配布にない着手記録を検出")
    for name, job in manifest["packs"].items():
        cards = folder / "cards" / name
        pack = folder / "reads" / name
        if pack.exists() and {p.name for p in pack.iterdir()} - manifest["models"].keys():
            raise ValueError("読み手の識別子が固定された配布と異なる")
        votes[name] = {}
        for family, model in manifest["models"].items():
            outcome = pack / family
            mark = claimed(folder, name, family)
            if mark.exists():
                if load(mark) != claim_value(expected, name, family, model):
                    raise ValueError("着手記録が初回の配布と異なる")
                if (outcome / "start.json").exists():
                    found = receive(outcome, family, model, job["request"], cards, runtimes[family])
                elif not outcome.exists() or not any(outcome.iterdir()):
                    found = {"availability": "technical-unresolved"}
                else:
                    raise ValueError("起動記録のない回答を検出")
            elif outcome.exists() and any(outcome.iterdir()):
                raise ValueError("着手記録のない票を検出")
            else:
                found = {"availability": "unstarted"}
            session = found.get("session")
            if session is not None:
                if session in old or session in seen:
                    raise ValueError("以前の会話または同じ版の別の会話を再利用している")
                seen.add(session)
            votes[name][family] = {k: v for k, v in found.items() if k != "answers"}
            votes[name][family]["files"] = {p.name: sha(p) for p in outcome.iterdir()} if outcome.exists() else {}
            states.setdefault(family, Counter())[found["availability"]] += 1
    return votes, states, len(seen)


def launch(folder, manifest, runtimes, expected):
    with ThreadPoolExecutor(max_workers=WORKERS) as pool:
        pending = []
        for name, job in manifest["packs"].items():
            for family, model in manifest["models"].items():
                if not claimed(folder, name, family).exists():
                    pending.append(pool.submit(launch_one, folder, name, family, model, job["request"], runtimes[family], expected))
        for task in as_completed(pending):
            task.result()


def run(folder, expected, action, executables):
    final = folder / "received.json"
    with lease(folder / "delivery.lease"):
        manifest = checked(folder, expected)
        if final.exists() and action != "status":
            raise FileExistsError("正式な集計のために原票を確定済み")
        runtimes = commitment(folder, expected, executables, action)
        available(folder, manifest, runtimes, expected)
        if action == "deliver":
            launch(folder, manifest, runtimes, expected)
        votes, counts, seen = available(folder, manifest, runtimes, expected)
        if action == "close":
            if any(count["unstarted"] for count in counts.values()):
                raise ValueError("配布前の束が残っている")
            if checked(folder, expected) != manifest:
                raise ValueError("原票の確定までに配布が変化した")
            save_once(final, encoded({"packages_sha256": expected, "delivery_sha256": sha(folder / "delivery-started.json"),
                                      "votes": votes, "unique_sessions": seen, "counts": counts,
                                      "launches": {p.relative_to(folder).as_posix(): sha(p)
                                                   for p in sorted((folder / "launches").glob("*/*.json"))}}))
        print(json.dumps(counts, ensure_ascii=False), flush=True)


if __name__ == "__main__":
    cli = argparse.ArgumentParser(description=__doc__)
    cli.add_argument("action", choices=("deliver", "status", "close"))
    cli.add_argument("--folder", type=Path, required=True)
    cli.add_argument("--packages", required=True)
    cli.add_argument("--codex", type=Path)
    cli.add_argument("--claude", type=Path)
    args = cli.parse_args()
    executables = {"gpt": args.codex, "claude": args.claude}
    if args.action == "deliver" and any(v is None for v in executables.values()):
        cli.error("二系統のCLIの絶対パスを指定する")
    run(args.folder, args.packages, args.action, executables)
