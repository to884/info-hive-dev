"""配布を止める条件、起動前後の台帳と、両CLIの実際の受領を試す。"""

import argparse
from pathlib import Path
import sys
from tempfile import TemporaryDirectory

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parent / "v19-reference-audit"))
import run as base

audit = base.module("next_independent_audit_preflight", HERE / "run.py")
factory = audit.delivery_module
ROOT = audit.CORPUS / "reference-v27-transport-preflight-final"


def denied(fn):
    try:
        fn()
    except (ValueError, FileExistsError):
        return
    raise ValueError("出典または再送の拒否を再現できない")


def controls(tmp):
    ledger, delivery = tmp / "ledger", tmp / "delivery"
    delivery.mkdir()
    shipment = factory.Shipment(delivery, "test", {"models": {"gpt": "gpt", "claude": "claude"},
        "packs": {f"pack-{i:02d}": {"request": {}} for i in range(12)}}, {"gpt": {}, "claude": {}})
    receiver = lambda *_a, **_k: {"availability": "received", "session": "synthetic"}
    job = factory.Delivery(base, receiver, ledger, audit.runner, audit.limits)
    first = "pack-00"
    home = ledger / first / "gpt"
    record = job.claim(shipment, first, "gpt", "gpt", {"availability": "unstarted"}, 1)
    claim = home / "attempt-0001-claim.json"
    job.runner.publish(claim, base.encoded(record))
    assert job.attempts(shipment, first, "gpt")[-1]["receipt"]["availability"] == "unlaunched-technical"
    raw = delivery / "attempts" / first / "gpt" / "attempt-0001" / "raw"
    job.runner.publish(raw / "schema.json", b"{}")
    (raw / ".write-interrupted").write_bytes(b"partial local preparation")
    assert job.attempts(shipment, first, "gpt")[-1]["receipt"]["availability"] == "unlaunched-technical"
    start = raw / "start.json"
    job.runner.publish(start, b"{}")
    job.runner.publish(home / "attempt-0001-launch.json", base.encoded({"claim": base.sha(claim), "start": base.sha(start)}))
    denied(lambda: job.send(shipment, first, "gpt"))
    start.rename(raw / "start-preserved-for-negative.json")
    denied(lambda: job.attempts(shipment, first, "gpt"))
    (raw / "start-preserved-for-negative.json").rename(start)
    assert job.attempts(shipment, first, "gpt")[-1]["receipt"]["availability"] == "received"

    quota = tmp / "quota"
    quota.mkdir()
    (quota / "response.jsonl").write_text(
        '[]\n{"type":"rate_limit_event","rate_limit_info":null}\n'
        '{"type":"turn.failed","error":{"message":"usage limit"}}\n', encoding="utf-8")
    rejected = audit.limits.suspected(quota, "gpt", {"availability": "failed-technical"})
    assert rejected["availability"] == "quota-unproven" and "resets_at" not in rejected
    answers = []
    job.send = lambda _shipment, pack, _role: answers.append(pack) or rejected
    job.send_queue(shipment, "gpt", list(shipment.document["packs"]))
    assert len(answers) == 1
    return {"unlaunched_recovery": True, "deleted_start_detected": True,
            "malformed_events_ignored": True, "unproved_quota_never_replayed": True,
            "sent_before_quota_stop": len(answers)}


def actual(codex, claude):
    older = audit.old_sessions()
    trial = HERE.parent / "v22-list-mark-pilot"
    sealed = base.load(trial / "lock.json")
    target, = (case for case, info in sealed["cases"].items() if info["purpose"] == "regular")
    request = sealed["tests"][target + "/old"]
    fixed = ROOT / "delivery"
    cards = fixed / "cards" / "pack-000"
    cards.mkdir(parents=True)
    for name, check in zip(request["request"]["images"], request["request"]["image_sha256"], strict=True):
        src = Path(request["cards"]) / name
        if base.sha(src) != check:
            raise ValueError("開発用の送付に使った固定画像が変わった")
        base.save_once(cards / name, src.read_bytes())
    manifest = fixed / "packages.json"
    base.save_once(manifest, base.encoded({"models": base.frame.trial.MODELS, "inputs": {},
                   "packs": {"pack-000": {"request": request["request"]}}}))
    launch = factory.Delivery(base, audit.quota.inspect_attempt, ROOT / "ledger", audit.runner, audit.limits)
    ship = launch.check(fixed, base.sha(manifest), {"gpt": codex, "claude": claude})
    for model in ship.document["models"]:
        launch.run_role(ship, model)
    counts = launch.close(ship, older)
    if any(r["received"] != 1 for r in counts.values()):
        raise ValueError("二系統の独立した正常な画像票がそろわない")
    restored, _ = launch.collect(ship, older)
    assert restored == base.load(fixed / "received.json")
    return base.sha(fixed / "received.json")


def main():
    cli = argparse.ArgumentParser(description=__doc__)
    cli.add_argument("--codex", type=Path, required=True)
    cli.add_argument("--claude", type=Path, required=True)
    args = cli.parse_args()
    result = HERE / "transport-preflight-final.json"
    if ROOT.exists() or result.exists():
        raise FileExistsError("配布の実地対照は既に固定されている")
    with TemporaryDirectory(prefix="adr0025-transport-fixtures-") as name:
        checked = controls(Path(name))
    receipt = actual(args.codex, args.claude)
    methods = (Path(__file__), HERE / "delivery.py", HERE / "runner.py", HERE / "limits.py")
    base.save_once(result, base.encoded({"scope": "development-only", "negative_controls": checked, "received_sha256": receipt,
                                         "methods": {p.name: base.sha(p) for p in methods}}))
    print(checked, "実地の画像票2件", receipt, flush=True)


if __name__ == "__main__":
    main()
