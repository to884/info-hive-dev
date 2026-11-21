"""画像読取前に利用上限で拒否された試行を識別し、同じ依頼を再送する。"""

import argparse
from collections import Counter
from concurrent.futures import FIRST_COMPLETED, ThreadPoolExecutor, wait
import json
from pathlib import Path
import time

import run as pilot


ZERO_USAGE = ("input_tokens", "output_tokens", "cache_creation_input_tokens", "cache_read_input_tokens")


def rejected_before_read(events):
    if [(e.get("type"), e.get("subtype")) for e in events[:2]] != [
        ("system", "ui_invalidate"), ("system", "init")
    ] or [e.get("type") for e in events[2:]] != ["rate_limit_event", "assistant", "result"]:
        return None
    limit, synthetic, result = events[2:]
    session = result.get("session_id")
    if not session or any(e.get("session_id") != session for e in events):
        return None
    info = limit.get("rate_limit_info", {})
    embedded = synthetic.get("api_error_params", {}).get("rate_limit_info", {})
    message = synthetic.get("message", {})
    content = message.get("content", [])
    reset = info.get("resetsAt")
    if (type(reset) is not int or reset <= 0 or info.get("status") != "rejected"
            or embedded.get("status") != "rejected" or embedded.get("resetsAt") != reset
            or embedded.get("rateLimitType") != info.get("rateLimitType")
            or synthetic.get("api_error_status") != 429 or synthetic.get("is_api_error_message") is not True
            or message.get("model") != "<synthetic>" or len(content) != 1
            or content[0].get("type") != "text" or result.get("api_error_status") != 429
            or result.get("terminal_reason") != "api_error" or result.get("is_error") is not True
            or result.get("duration_api_ms") != 0 or result.get("total_cost_usd") != 0
            or result.get("modelUsage") != {} or "structured_output" in result
            or any(usage.get(k) != 0 for usage in (message.get("usage", {}), result.get("usage", {})) for k in ZERO_USAGE)):
        return None
    return {"resets_at": reset, "session": session, "type": info.get("rateLimitType")}


def inspect_attempt(folder, role, task, runtime, *, audit=None, models=None):
    if audit is None:
        audit, models = pilot.audit, pilot.trial.MODELS
    checked = audit.receive(folder, role, models[role], task["request"], Path(task["cards"]), runtime)
    if role != "claude" or checked["availability"] != "failed-technical":
        return checked
    process = audit.load(folder / "process.json")
    if not process["returncode"] or process["last_sha256"] is not None:
        return checked
    lines = (folder / "response.jsonl").read_bytes().splitlines()
    try:
        events = [json.loads(l, object_pairs_hook=audit.readers.json_pairs) for l in lines if l.strip()]
        hold = rejected_before_read(events)
    except (ValueError, KeyError, TypeError, AttributeError, IndexError):
        return checked
    if hold:
        return {**checked, "availability": "quota-rejection", **hold}
    return checked


def attempts(name, role, task, runtime, lock_sha):
    root = pilot.OUT / "quota-recovery" / name / role
    first = pilot.OUT / "reads" / name / role
    receipts = [(first, inspect_attempt(first, role, task, runtime))]
    dirs = sorted(root.iterdir()) if root.exists() else []
    for n, path in enumerate(dirs, 1):
        earlier = receipts[-1][1]
        if path.name != f"attempt-{n:03d}" or earlier["availability"] != "quota-rejection":
            raise ValueError("上限拒否が証明されていない試行の再送を検出")
        mark = pilot.load(path / "claim.json")
        if (mark != claim(lock_sha, name, role, earlier, mark["authorized_at"])
                or mark["authorized_at"] < earlier["resets_at"]):
            raise ValueError("再送の理由、時刻または依頼が固定済みの記録と異なる")
        current = path / "raw"
        receipts.append((current, inspect_attempt(current, role, task, runtime)))
    return receipts


def claim(lock_sha, name, role, previous, now):
    return {"lock_sha256": lock_sha, "task": name, "role": role, "authorized_at": now,
            "previous_response_sha256": previous["response_sha256"], "previous_reset": previous["resets_at"]}


def try_again(name, task, runtime, lock_sha):
    role = "claude"
    prior = attempts(name, role, task, runtime, lock_sha)
    old = prior[-1][1]
    now = int(time.time())
    if old["availability"] != "quota-rejection" or now < old["resets_at"]:
        raise ValueError("証明できた利用枠の解除前に同じ読取を始めない")
    attempt = pilot.OUT / "quota-recovery" / name / role / f"attempt-{len(prior):03d}"
    attempt.mkdir(parents=True, exist_ok=False)
    pilot.save_once(attempt / "claim.json", pilot.encoded(claim(lock_sha, name, role, old, now)))
    raw = attempt / "raw"
    try:
        pilot.structured.read(role, pilot.trial.MODELS[role], Path(runtime["path"]),
                              task["request"], Path(task["cards"]), raw)
    except (ValueError, KeyError, TypeError, AttributeError, IndexError):
        if not (raw / "process.json").exists():
            raise
    return inspect_attempt(raw, role, task, runtime)


def collect_from_attempts(plan, all_attempts, lock_sha):
    origins, sessions = {}, set()
    for name, by_role in all_attempts.items():
        origins[name] = {}
        for role, receipts in by_role.items():
            for _, row in receipts:
                session = row.get("session")
                if session and session in sessions:
                    raise ValueError("開発の比較で同じセッションを再利用")
                if session:
                    sessions.add(session)
            path, final = receipts[-1]
            if final["availability"] != "received":
                return
            origins[name][role] = {"selected": str(path), "attempts": [
                {"path": str(p), **{k: v for k, v in value.items() if k != "answers"}} for p, value in receipts]}

    # 元の集計と同じ判定を使う。採用原票の実体と来歴は改変せず別の表に記録する。
    view = pilot.OUT / "quota-recovery/collection"
    for name in plan["tests"]:
        for role in pilot.trial.MODELS:
            source = Path(origins[name][role]["selected"])
            dst = view / "reads" / name / role
            dst.mkdir(parents=True, exist_ok=True)
            for leaf in ("process.json", "response.jsonl", "last-message.json"):
                file = source / leaf
                if file.exists():
                    target = dst / leaf
                    if not target.exists():
                        pilot.save_once(target, file.read_bytes())
                    elif target.read_bytes() != file.read_bytes():
                        raise ValueError("再現した集計用の原票が変化した")
    selection = view / "display/selection.json"
    selection.parent.mkdir(parents=True, exist_ok=True)
    payload = (pilot.OUT / "display/selection.json").read_bytes()
    if not selection.exists():
        pilot.save_once(selection, payload)
    elif selection.read_bytes() != payload:
        raise ValueError("集計用の対象行が変化した")
    record = pilot.HERE / "recovery-provenance.json"
    prepared = pilot.encoded({"lock_sha256": lock_sha, "origins": origins})
    if not record.exists():
        pilot.save_once(record, prepared)
    elif record.read_bytes() != prepared:
        raise ValueError("利用枠解除後の来歴が変化した")
    if not (pilot.HERE / "result.json").exists():
        pilot.OUT = view
        pilot.collect(plan)


def resume(due, jobs, runtime, lock_sha):
    # 保留が返った時点で新規の投入を止める。既に着手した回答は最後まで保存する。
    with ThreadPoolExecutor(max_workers=3) as pool:
        running = {}
        names = iter(due)
        halted = False
        while True:
            while not halted and len(running) < 3 and (name := next(names, None)):
                running[pool.submit(try_again, name, jobs[name], runtime, lock_sha)] = name
            if not running:
                break
            done, _ = wait(running, return_when=FIRST_COMPLETED)
            for f in done:
                name = running.pop(f)
                received = f.result()
                print(name, received["availability"], received.get("resets_at", ""), flush=True)
                halted |= received["availability"] == "quota-rejection"


def main():
    cli = argparse.ArgumentParser(description=__doc__)
    cli.add_argument("action", choices=("status", "resume"))
    cli.add_argument("--sha256", required=True)
    cli.add_argument("--codex", type=Path, required=True)
    cli.add_argument("--claude", type=Path, required=True)
    args = cli.parse_args()
    plan = pilot.load(pilot.LOCK)
    if (pilot.sha(pilot.LOCK) != args.sha256
            or any(pilot.sha(Path(p)) != h for p, h in plan["files"].items())):
        raise ValueError("開発比較の固定済み依頼または資料が変化した")
    runtimes = pilot.audit.delivery.runtime({"gpt": args.codex, "claude": args.claude})
    jobs = plan["tests"]
    with pilot.audit.delivery.lease(pilot.OUT / "quota-recovery.lease"):
        def all_attempts():
            return {name: {role: attempts(name, role, task, runtimes[role], args.sha256)
                           for role in pilot.trial.MODELS} for name, task in jobs.items()}

        records = all_attempts()
        if args.action == "resume":
            due = [name for name, attempts_by_role in records.items()
                   if (old := attempts_by_role["claude"][-1][1])["availability"] == "quota-rejection"
                   and time.time() >= old["resets_at"]]
            resume(due, jobs, runtimes["claude"], args.sha256)
            records = all_attempts()
            collect_from_attempts(plan, records, args.sha256)
        for role in pilot.trial.MODELS:
            print(role, Counter(values[role][-1][1]["availability"] for values in records.values()), flush=True)


if __name__ == "__main__":
    main()
