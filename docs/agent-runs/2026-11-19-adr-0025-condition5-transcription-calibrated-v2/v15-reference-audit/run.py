"""固定した表示をそのまま使い、絶対パスで独立に配布する。"""

import argparse
from collections import Counter
import importlib.util
import json
import os
from pathlib import Path
import re
import sys
import tempfile

HERE = Path(__file__).resolve().parent
PREVIOUS = HERE.parent / "v14-reference-audit"


def module(name, path):
    spec = importlib.util.spec_from_file_location(name, path)
    result = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(result)
    return result


prior = module("v14_packets", PREVIOUS / "packets.py")
sys.path.insert(0, str(PREVIOUS))
reference = module("v14_resolve", PREVIOUS / "resolve.py")
base = module("delivery_checked", HERE.parent / "v12-reference-audit/delivery.py")
old_receive = base.receive
OUT = prior.OUT.with_name("reference-audit-v15")
SOURCE_SHA = "52bad13bb0efecd23319dd3038b2c79bf7cceb10ff6b77b53da1b412d52daeb0"
CARDS_SHA = "d8c7297c2edf69cb43d5b290ce1111ae44b6cef0246f6ec2a2955e5486f942fe"
load, sha, save_once, encoded = prior.load, prior.sha, prior.save_once, prior.encoded
MISSING = re.compile(r"unable to (?:locate|load|read) image at `([^`]+)`")


def receive(directory, family, model, pack, cards, runtime):
    verdict = old_receive(directory, family, model, pack, cards, runtime)
    if family != "gpt" or verdict["availability"] != "received":
        return verdict
    log = (directory / "stderr.txt").read_text(encoding="utf-8", errors="replace")
    attached = {cards / filename for filename in pack["images"]}
    errors = {Path(path) for path in MISSING.findall(log)}
    if errors & attached:
        return {k: v for k, v in verdict.items() if k not in {"availability", "answers", "session"}} | {
            "availability": "technical-image-load-failure"}
    return verdict


def old_session_ids():
    ids = set()
    pattern = re.compile(r'"(?:thread_id|session_id)"\s*:\s*"([0-9a-f-]{36})"')
    old_delivery = prior.OUT / "delivery/reads"
    for log in old_delivery.glob("*/*/response.jsonl"):
        ids.update(pattern.findall(log.read_text(encoding="utf-8", errors="replace")))
    return ids


def prepare():
    if OUT.exists():
        raise FileExistsError("同じ版の配布を作成済み")
    source = prior.OUT / "selection.json"
    packets = prior.OUT / "delivery/packages.json"
    if sha(source) != SOURCE_SHA or sha(packets) != CARDS_SHA:
        raise ValueError("固定した標本か画像の配布が異なる")
    manifest = base.checked(packets.parent, CARDS_SHA)
    evidence = PREVIOUS / "interruption-2026-11-20.json"
    if not evidence.is_file():
        raise ValueError("中断した版の技術障害の証跡が未確定")
    with tempfile.TemporaryDirectory(dir=OUT.parent, prefix="audit-v15-prepare-") as temp:
        root = Path(temp) / OUT.name
        target = root / "delivery"
        target.mkdir(parents=True)
        os.link(source, root / "selection.json")
        for name, data in manifest["packs"].items():
            folder = target / "cards" / name
            folder.mkdir(parents=True)
            for filename in data["request"]["images"]:
                os.link(packets.parent / "cards" / name / filename, folder / filename)
        additions = (Path(__file__), HERE / "protocol.md", evidence, source, packets)
        manifest["inputs"].update({str(p): sha(p) for p in additions})
        save_once(target / "packages.json", encoded(manifest))
        base.checked(target, sha(target / "packages.json"))
        root.rename(OUT)
    print(sha(OUT / "delivery/packages.json"), len(manifest["packs"]), "束、379行を保持", flush=True)


def delivery(folder, packages, action, executables):
    absolute = folder.resolve(strict=True)
    original_prior = base.prior_sessions
    base.prior_sessions = lambda: original_prior() | old_session_ids()
    base.receive = receive
    base.run(absolute, packages, action, executables)


def proofs(action):
    reference.HERE = HERE
    reference.OUT = OUT
    reference.DELIVERY = OUT / "delivery"
    reference.READ = reference.DELIVERY / "received.json"
    reference.START = reference.DELIVERY / "delivery-started.json"
    reference.PACKS = reference.DELIVERY / "packages.json"
    reference.REQUESTS = OUT / "source-requests.json"
    reference.PROOF = OUT / "source-commands.json"
    reference.receive = receive
    if action == "source-requests":
        reference.prepare_source()
    else:
        reference.collect()


def main():
    cli = argparse.ArgumentParser(description=__doc__)
    cli.add_argument("action", choices=("prepare", "deliver", "status", "close", "source-requests", "collect"))
    cli.add_argument("--folder", type=Path, default=OUT / "delivery")
    cli.add_argument("--packages")
    cli.add_argument("--codex", type=Path)
    cli.add_argument("--claude", type=Path)
    args = cli.parse_args()
    if args.action == "prepare":
        prepare()
    elif args.action in {"source-requests", "collect"}:
        proofs(args.action)
    else:
        executables = {"gpt": args.codex, "claude": args.claude}
        if args.action == "deliver" and any(value is None for value in executables.values()):
            cli.error("両系統の実行ファイルを指定する")
        if not args.packages:
            cli.error("固定した配布のSHA-256を指定する")
        delivery(args.folder, args.packages, args.action, executables)


if __name__ == "__main__":
    main()
