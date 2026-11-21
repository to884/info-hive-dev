"""固定した束を各系統に一度配り、読取前の利用枠拒否だけを再送する。"""

from collections import Counter
from concurrent.futures import FIRST_COMPLETED, ThreadPoolExecutor, wait
from dataclasses import dataclass
from pathlib import Path
import time


@dataclass(frozen=True)
class Shipment:
    folder: Path
    sha256: str
    document: dict
    runtime: dict


class Delivery:
    def __init__(self, audit, inspect_attempt, ledger, runner, limits):
        self.audit = audit
        self.inspect_attempt = inspect_attempt
        self.ops = audit.delivery
        self.ledger = ledger
        self.runner = runner
        self.limits = limits

    def check(self, folder, expected, executables=None):
        manifest = self.ops.checked(folder, expected)
        if executables is not None:
            with self.ops.lease(folder / "start.lease"):
                runtime = self.ops.commitment(folder, expected, executables, "deliver")
        else:
            runtime = self.ops.commitment(folder, expected, {}, "status")
        return Shipment(folder, expected, manifest, runtime)

    def attempts(self, shipment, pack, role):
        model = shipment.document["models"][role]
        job = shipment.document["packs"][pack]["request"]
        cards = shipment.folder / "cards" / pack
        root = shipment.folder / "attempts" / pack / role
        history = self.ledger / pack / role
        runtime = shipment.runtime[role]
        previous, results = {"availability": "unstarted"}, []
        labels = sorted(history.glob("*-claim.json"))
        approved = {p.name.removesuffix("-claim.json") for p in labels}
        ledger_files = {name + suffix for name in approved for suffix in ("-claim.json", "-launch.json", "-completed.json")}
        ledger_files.add("technical-reviewed.json")
        if history.exists() and any(
                p.name not in ledger_files and not p.name.startswith(".write-") for p in history.iterdir()):
            raise ValueError("台帳の着手記録が欠けている")
        if root.exists() and any(folder.name not in approved for folder in root.iterdir()):
            raise ValueError("独立した台帳に存在しない試行がある")
        for index, label in enumerate(labels, 1):
            name = f"attempt-{index:04d}"
            folder = root / name
            if label.name != name + "-claim.json" or (folder.exists() and (
                    not folder.is_dir() or {p.name for p in folder.iterdir()} - {"raw"})):
                raise ValueError("固定した着手記録の構造が異なる")
            claim = self.audit.load(label)
            if (type(claim["at"]) is not int or claim["at"] < previous.get("resets_at", 0)
                    or previous["availability"] not in ("unstarted", "quota-rejection", "unlaunched-technical")
                    or claim != self.claim(shipment, pack, role, model, previous, claim["at"])):
                raise ValueError("画像を読んだ試行または解除前の試行を再送した可能性")
            raw = folder / "raw"
            files = {p.name: self.audit.sha(p) for p in raw.iterdir()} if raw.exists() else {}
            launch, ended = (history / (name + suffix) for suffix in ("-launch.json", "-completed.json"))
            launch_sha = self.audit.sha(launch) if launch.exists() else None
            ended_sha = self.audit.sha(ended) if ended.exists() else None
            claim_sha = self.audit.sha(label)
            if ended.exists() and self.audit.load(ended) != {"launch": launch_sha, "files": files}:
                raise ValueError("完了を外部台帳に記録した原票が変化")
            if launch.exists():
                if self.audit.load(launch) != {"claim": claim_sha, "start": files.get("start.json")} or "start.json" not in files:
                    raise ValueError("起動を台帳に記録した試行が削除または変更された")
                receipt = self.inspect_attempt(raw, role, {"cards": cards, "request": job}, runtime,
                                               audit=self.audit, models=shipment.document["models"])
                receipt = self.limits.suspected(raw, role, receipt)
            else:
                published = {name for name in files if not name.startswith(".write-")}
                if ended.exists() or published - {"schema.json", "start.json"}:
                    raise ValueError("起動していない試行に原票がある")
                receipt = {"availability": "unlaunched-technical"}
            previous = {k: v for k, v in receipt.items() if k != "answers"}
            results.append({"dir": folder.relative_to(shipment.folder).as_posix(), "receipt": receipt,
                            "files": files, "claim_sha256": claim_sha, "launch_sha256": launch_sha,
                            "completion_sha256": ended_sha})
        return results

    @staticmethod
    def claim(shipment, pack, role, model, previous, now):
        return {"package_sha256": shipment.sha256, "pack": pack, "role": role,
                "model": model, "at": now, "previous": previous}

    def send(self, shipment, pack, role):
        plans = shipment.document
        model = plans["models"][role]
        job = plans["packs"][pack]["request"]
        prior = self.attempts(shipment, pack, role)
        last = {k: v for k, v in prior[-1]["receipt"].items() if k != "answers"} if prior else {"availability": "unstarted"}
        now = int(time.time())
        if last["availability"] not in ("unstarted", "quota-rejection", "unlaunched-technical") or now < last.get("resets_at", 0):
            raise ValueError("正式な読取は開始済みか、利用制限が続いている")
        name = f"attempt-{len(prior) + 1:04d}"
        history = self.ledger / pack / role
        label, launch, ended = (history / (name + suffix) for suffix in ("-claim.json", "-launch.json", "-completed.json"))
        self.runner.publish(label, self.audit.encoded(self.claim(shipment, pack, role, model, last, now)))
        folder = shipment.folder / "attempts" / pack / role / name
        folder.mkdir(parents=True, exist_ok=False)

        def mark_started(start):
            self.runner.publish(launch, self.audit.encoded({"claim": self.audit.sha(label), "start": start}))

        raw = folder / "raw"
        self.runner.read(self.audit, shipment.runtime[role], role, model, job, shipment.folder / "cards" / pack, raw, mark_started)
        files = {p.name: self.audit.sha(p) for p in raw.iterdir()}
        self.runner.publish(ended, self.audit.encoded({"launch": self.audit.sha(launch), "files": files}))
        return self.attempts(shipment, pack, role)[-1]["receipt"]

    def run_role(self, shipment, role, continue_after_technical=False):
        with self.ops.lease(shipment.folder / f"{role}.lease"):
            if (shipment.folder / "received.json").exists():
                raise FileExistsError("正式な原票は確定済み")
            todo = []
            hold, technical = 0, {}
            for pack in shipment.document["packs"]:
                attempts = self.attempts(shipment, pack, role)
                if not attempts:
                    todo.append(pack)
                    continue
                value = attempts[-1]["receipt"]
                if value["availability"] == "quota-rejection":
                    todo.append(pack)
                    hold = max(hold, value["resets_at"])
                elif value["availability"] == "unlaunched-technical":
                    todo.append(pack)
                elif value["availability"] != "received":
                    attempt = attempts[-1]
                    note = self.ledger / pack / role / "technical-reviewed.json"
                    identity = {k: attempt[k] for k in ("claim_sha256", "launch_sha256", "completion_sha256")}
                    if note.exists():
                        if self.audit.load(note)["attempt"] != identity:
                            raise ValueError("技術障害の確認対象が変化")
                    else:
                        technical[pack] = (note, identity, value["availability"])
            if hold > time.time():
                print(role, "利用枠解除待ち", hold, len(todo), flush=True)
                return
            if technical and not continue_after_technical:
                print(role, "技術障害の原票を確認するまで追加配布を保留",
                      {name: detail[2] for name, detail in technical.items()}, flush=True)
                return
            for note, identity, classification in technical.values():
                self.runner.publish(note, self.audit.encoded({
                    "attempt": identity, "classification": classification, "reviewed_at": int(time.time()),
                    "decision": "keep-attempt-and-continue-unstarted-only",
                }))
            self.send_queue(shipment, role, todo)

    def send_queue(self, shipment, role, todo):
        pending, running, holds = iter(todo), {}, []
        slots = 4 if role == "claude" else 6
        with ThreadPoolExecutor(max_workers=slots) as pool:
            first_for_gpt = role == "gpt"
            while True:
                while not holds and len(running) < (1 if first_for_gpt else slots) and (pack := next(pending, None)):
                    running[pool.submit(self.send, shipment, pack, role)] = pack
                if not running:
                    break
                done, _ = wait(running, return_when=FIRST_COMPLETED)
                for job in done:
                    pack = running.pop(job)
                    value = job.result()
                    if value["availability"] != "received":
                        holds.append(value.get("resets_at", 0))
                    print(pack, role, value["availability"], flush=True)
                first_for_gpt = False
        if holds:
            print(role, "追加配布を停止", max(holds), flush=True)

    def collect(self, shipment, old_sessions):
        roles, packs = shipment.document["models"], shipment.document["packs"]
        root = shipment.folder / "attempts"
        for directory in (root, self.ledger):
            if directory.exists():
                for pack in directory.iterdir():
                    if not pack.is_dir() or pack.name not in packs or {r.name for r in pack.iterdir()} - roles.keys():
                        raise ValueError("固定した配布にない着手記録を検出")
        counts = {role: Counter() for role in roles}
        seen, votes, answers = set(), {}, {}
        for pack in packs:
            votes[pack], answers[pack] = {}, {}
            for role in roles:
                chain = self.attempts(shipment, pack, role)
                record = chain[-1]["receipt"] if chain else {"availability": "unstarted"}
                votes[pack][role] = [{**v, "receipt": {k: x for k, x in v["receipt"].items() if k != "answers"}} for v in chain]
                note = self.ledger / pack / role / "technical-reviewed.json"
                if note.exists():
                    expected = {k: chain[-1][k] for k in ("claim_sha256", "launch_sha256", "completion_sha256")}
                    if self.audit.load(note)["attempt"] != expected:
                        raise ValueError("技術障害の確認記録と原票が異なる")
                    votes[pack][role][-1]["technical_review_sha256"] = self.audit.sha(note)
                counts[role][record["availability"]] += 1
                answers[pack][role] = record.get("answers", {})
                for a in chain:
                    token = a["receipt"].get("session")
                    if token is None:
                        continue
                    if token in seen or token in old_sessions:
                        raise ValueError("同じ独立の読取セッションが使われている")
                    seen.add(token)
        return {"packages_sha256": shipment.sha256,
                "delivery_sha256": self.audit.sha(shipment.folder / "delivery-started.json"),
                "counts": counts, "votes": votes, "unique_sessions": len(seen)}, answers

    def close(self, shipment, old_sessions):
        folder = shipment.folder
        with self.ops.lease(folder / "gpt.lease"), self.ops.lease(folder / "claude.lease"):
            result, _ = self.collect(shipment, old_sessions)
            if any(counter["unstarted"] or counter["quota-rejection"] or counter["unlaunched-technical"]
                   for counter in result["counts"].values()):
                raise ValueError("未着手の束か、利用枠解除後に再送する束が残る")
            self.audit.save_once(folder / "received.json", self.audit.encoded(result))
        return result["counts"]
