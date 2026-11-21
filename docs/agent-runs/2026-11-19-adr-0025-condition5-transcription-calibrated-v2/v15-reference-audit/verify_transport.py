"""正式な原票を変更せず、画像の配送と旧会話からの独立性を照合する。"""

import argparse
import json
from pathlib import Path, PureWindowsPath
import re

import run

TRANSPORT_ERROR = re.compile(r"(?:unable to|failed to|could not|cannot) (?:locate|load|read|open) (?:the )?(?:attached )?image", re.I)
BACKTICK_PATH = re.compile(r"`([^`]+)`")


def events(path):
    return [json.loads(line) for line in path.read_bytes().splitlines() if line.strip()]


def session_id(log, family):
    if family == "gpt":
        found, = (e["thread_id"] for e in log if e.get("type") == "thread.started")
    else:
        found, = (e["session_id"] for e in log if e.get("type") == "system" and e.get("subtype") == "init")
    return found


def verified_earlier():
    proof = run.load(run.PREVIOUS / "interruption-2026-11-20.json")
    archived = run.prior.OUT / "delivery"
    if proof["packages_sha256"] != run.sha(archived / "packages.json"):
        raise ValueError("中断した版の配布と証跡の紐付けが異なる")
    known = {"gpt": set(), "claude": set()}
    for path, digest in proof["file_sha256"].items():
        file = archived / path
        if run.sha(file) != digest:
            raise ValueError("中断した版の原票が変化")
        if file.name == "response.jsonl":
            family = file.parent.name
            known[family].add(session_id(events(file), family))
    if len(known["gpt"]) != proof["gpt"]["completed"] or len(known["claude"]) != proof["claude"]["received_packs"]:
        raise ValueError("前版の既知の会話の全件を確認できない")
    observed = known["gpt"] | known["claude"]
    if not observed or not observed <= run.old_session_ids():
        raise ValueError("前版の会話が配送側の除外集合にそろわない")
    return observed | run.base.prior_sessions()


def attachment_error(log, pngs):
    for line in log.splitlines():
        if TRANSPORT_ERROR.search(line):
            locations = BACKTICK_PATH.findall(line)
            if not locations:
                return True
            for location in locations:
                filename = PureWindowsPath(location).name.casefold()
                if filename in pngs or filename.endswith(".png"):
                    return True
    return False


def inspect_all(snapshot=False):
    delivery = run.OUT / "delivery"
    manifest = run.load(delivery / "packages.json")
    prior = verified_earlier()
    seen, missing, failed = set(), [], []
    captured = {k: {"packs": 0, "rows": 0} for k in manifest["models"]}
    received = {k: {"packs": 0, "rows": 0} for k in manifest["models"]}
    accepted = {k: set() for k in manifest["models"]}
    runtimes = run.load(delivery / "delivery-started.json")["runtime"]
    for pack, content in manifest["packs"].items():
        request = content["request"]
        cards = delivery / "cards" / pack
        pngs = {name.casefold() for name in request["images"]}
        for role, model in manifest["models"].items():
            folder = delivery / "reads" / pack / role
            start, process = folder / "start.json", folder / "process.json"
            if not process.is_file():
                missing.append([pack, role])
                continue
            try:
                status = run.load(process)["status"]
            except json.JSONDecodeError:
                if snapshot:
                    missing.append([pack, role])
                    continue
                raise
            if status != "success":
                failed.append([pack, role, "CLIの異常終了"])
                continue
            state = run.load(start)
            log = events(folder / "response.jsonl")
            identity = session_id(log, role)
            if identity in seen or identity in prior:
                raise ValueError(f"以前の会話を含む重複を検出: {pack} {role}")
            seen.add(identity)
            if role == "gpt":
                paths = [Path(term.removeprefix("--image=")) for term in state["argv"] if term.startswith("--image=")]
                if paths != [cards / filename for filename in request["images"]] or any(not p.is_absolute() for p in paths):
                    raise ValueError(f"絶対パスと配送対象が違う: {pack} {role}")
            err = (folder / "stderr.txt").read_text(encoding="utf-8", errors="replace")
            if attachment_error(err, pngs):
                failed.append([pack, role, "添付画像を開けない"])
                continue
            captured[role]["packs"] += 1
            captured[role]["rows"] += len(request["ids"])
            if run.receive(folder, role, model, request, cards, runtimes[role])["availability"] == "received":
                received[role]["packs"] += 1
                received[role]["rows"] += len(request["ids"])
                accepted[role].add(pack)
    paired = sum(len(manifest["packs"][k]["request"]["ids"]) for k in accepted["gpt"] & accepted["claude"])
    proof = {"scope": "read-only-transport-cross-check", "previous_sessions": len(prior),
             "runtime_completed": captured, "verified_ballot": received, "paired_rows": paired,
             "incomplete": missing, "technical_errors": failed,
             "packages_sha256": run.sha(delivery / "packages.json")}
    print(json.dumps({**received, "paired_rows": paired, "unfinished": len(missing), "errors": len(failed)}, ensure_ascii=False), flush=True)
    if not snapshot:
        if missing or failed:
            raise ValueError("全束の配送を検証できない")
        run.save_once(run.HERE / "transport-proof.json", run.encoded(proof))


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--snapshot", action="store_true")
    inspect_all(parser.parse_args().snapshot)
