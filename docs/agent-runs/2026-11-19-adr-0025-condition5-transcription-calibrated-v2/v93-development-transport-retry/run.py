"""開発用二試験で通信切替の記録がある無効票だけを新規セッションで再送する。"""

import argparse
from importlib.util import module_from_spec, spec_from_file_location
from pathlib import Path

HERE = Path(__file__).resolve().parent
STUDIES = {"91": "v91-column-context", "92": "v92-numbered-ink-membership"}
EXPECTED_FAILURES = {
    "91": {"87-72-pack-317/new", "87-72-pack-317/old", "87-72-pack-366/new"},
    "92": {"88-pack-373-outside/new", "88-pack-373-outside/old"},
}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("study", choices=STUDIES)
    parser.add_argument("--codex", required=True, type=Path)
    parser.add_argument("--claude", required=True, type=Path)
    args = parser.parse_args()
    path = HERE.parent / STUDIES[args.study] / "run.py"
    spec = spec_from_file_location("locked_development_retry", path)
    study = module_from_spec(spec)
    spec.loader.exec_module(study)
    core, pilot = study.core, study.pilot
    study.launch.configure()
    args.sha256 = core.sha(pilot.LOCK)
    plan = core.load(pilot.LOCK)
    if any(core.sha(Path(name)) != digest for name,digest in plan["files"].items()):
        raise ValueError("元の画像または依頼の固定が異なる")
    rundir = pilot.OUT
    retrydir = rundir / "recovery-https-fallback"
    original = pilot.outcome
    runtime = pilot.audit.delivery.runtime({"gpt": args.codex, "claude": args.claude})
    failed, replaced = {}, {}
    for name,job in plan["jobs"].items():
        for family in ("gpt","claude"):
            past = original(args.sha256, name, family, job, runtime[family])
            if not past:
                raise ValueError("元の試験でまだ着手していない束がある")
            if past[-1]["availability"] == "received":
                continue
            if family!="gpt" or past[-1]["availability"]!="invalid-technical":
                raise ValueError("対象外の受領障害が見つかった")
            raw = rundir / "reads" / name / family / f"attempt-{len(past):03d}" / "raw"
            process = core.load(raw/"process.json")
            events = (raw/"response.jsonl").read_text(encoding="utf-8")
            if not (process["returncode"]==0 and "Falling back from WebSockets to HTTPS transport." in events
                    and core.sha(raw/"response.jsonl")==process["response_sha256"]):
                raise ValueError("確認済みの経路切替とは異なる")
            failed[name] = process["response_sha256"]
    if set(failed) != EXPECTED_FAILURES[args.study]:
        raise ValueError("事前に確認した無効票と範囲が異なる")
    for name in sorted(failed):
        job = plan["jobs"][name]
        try:
            pilot.OUT = retrydir
            attempts = original(args.sha256, name, "gpt", job, runtime["gpt"])
            if not attempts:
                attempts = original(args.sha256, name, "gpt", job, runtime["gpt"], send=True)
        finally:
            pilot.OUT = rundir
        if not attempts or attempts[-1]["availability"]!="received":
            raise ValueError(f"新規の受領はまだ確認できない {name}")
        replaced[name] = attempts[-1]
        print(name, "受領", flush=True)
    core.save_once(HERE/f"recover-v{args.study}.json", core.encoded({
        "scope":"development-only", "fixed_lock_sha256":args.sha256, "invalid_response_sha256":failed,
        "receipt":{name:{"session":result["session"], "retry_process_sha256":core.sha(
            retrydir/"reads"/name/"gpt"/"attempt-001"/"raw/process.json")}
                   for name,result in replaced.items()}
    }))

    def checked(state, name, family, job, actual_runtime, send=False):
        if send:
            raise ValueError("採点中の再送は認めない")
        if family=="gpt" and name in replaced:
            return [replaced[name]]
        return original(state, name, family, job, actual_runtime)

    pilot.outcome = checked
    try:
        if args.study=="91":
            study.score(args)
        else:
            study.measure.HERE=study.HERE
            study.measure.decompose=study.identify
            study.measure.score(args)
    finally:
        pilot.outcome = original


if __name__=="__main__":
    main()
