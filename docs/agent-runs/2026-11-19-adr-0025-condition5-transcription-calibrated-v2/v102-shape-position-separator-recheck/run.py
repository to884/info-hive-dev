"""同じ開発画像で成分の形・位置・役割を再判定し、保存転記を採点する。"""

import argparse
from collections import Counter
from importlib.util import module_from_spec, spec_from_file_location
from pathlib import Path
import re
import sys


HERE = Path(__file__).resolve().parent
V100 = HERE.parent / "v100-separator-role-second-look"
V101 = HERE.parent / "v101-hold-rejected-comma-candidates"


def module(name, path):
    spec = spec_from_file_location(name, path)
    instance = module_from_spec(spec)
    spec.loader.exec_module(instance)
    return instance


previous = module("previous_role_read", V100 / "run.py")
hold = module("previous_hold_rules", V101 / "run.py")
core, launch, pilot = previous.core, previous.launch, previous.pilot
prior_out = pilot.OUT
pilot.HERE = HERE
pilot.OUT = core.CORPUS / "reference-v102-shape-position-separator-recheck"
pilot.LOCK, pilot.RESULT = HERE / "lock.json", HERE / "receipts.json"
MODELS = previous.MODELS
RULES = ("either_transcription", "both_transcriptions")
TARGETS = ("Z001", "Z003", "Z009", "Z010", "Z015")
TAG = re.compile(r"([0-9]+):([CDLOU]):([ABU]):([SXU])")
PROMPT = (
    "添付の画像だけを見て、{row}の指定番号 {ids} の各成分を順に確認してください。"
    "まず450 DPIの拡大図で輪郭を見ます。丸い点か、丸い頭部と下へ曲がる尾か、"
    "短い直線や斜線か、別の形かを記録してください。"
    "次に成分の中心・下端を前後の数字の共通の下端、横の間隔と見比べます。"
    "数字の間で文字列に沿う位置か、上下に離れるか隣の数字に不自然に寄る位置かを記録してください。"
    "形と位置の両方を見て、数字列に属する区切りか、数字列とは別の余分な筆画か、判別できないかを各成分で答えます。"
    "小さいことだけで除外せず、枠に入っていることだけで採用しません。点や直線が区切りでないとも決めつけません。"
    "個数や表記習慣、数字の意味から補わず、両方に見えるときは判別不能にしてください。"
    "枠の所属や数字列そのものは再判定しません。"
    "answersは1件、idは {row}、statusはreadable、textには指定した番号だけを一度ずつ、"
    "番号:形:位置:役割 の順で書き、複数は | でつなぎます。"
    "形はC=頭と尾、D=点、L=短い直線・斜線、O=その他、U=不明。"
    "位置はA=数字列に沿う、B=数字列からずれる、U=不明。"
    "役割はS=区切り、X=余分な筆画、U=判別不能。説明は付けません。"
)


def prior_data():
    before, replay, images = hold.fixed_inputs()
    baseline = core.load(V101 / "comparison.json")
    if (baseline["rows"] != hold.replay(before, replay) or
            baseline["counts"] != hold.counts(baseline["rows"])):
        raise ValueError("前回の再集計が保存票と一致しない")
    old_replay, original, old_lock = previous.baseline()
    if replay != old_replay:
        raise ValueError("元の転記の再集計が一致しない")
    return before, baseline, replay, original, old_lock, images


def snapshot():
    core.verify_methods()
    before, baseline, replay, _, _, _ = prior_data()
    locked = core.load(V100 / "lock.json")
    selected = tuple(sorted(row for row, case in baseline["rows"].items() if
                           "extra" in case["both_transcriptions"] or
                           (case["group"] in {"inside", "edge"}
                            and "same" in case["both_transcriptions"])))
    if selected != TARGETS:
        raise ValueError("比較する5枠が前回の確定と一致しない")
    files = dict(locked["files"])
    pins = (Path(__file__), HERE / "protocol.md", V100 / "lock.json", V100 / "comparison.json",
            V100 / "integrity.json", V101 / "run.py", V101 / "comparison.json")
    files.update({str(path): core.sha(path) for path in pins})
    jobs, mapping = {}, {}
    for row in TARGETS:
        job = locked["jobs"][row + "/role"]
        meta = locked["mapping"][row]
        request = job["request"]
        ids = previous.component_ids(replay["cases"][row + "/new"]["votes"])
        if ids != meta["ids"] or set(map(str, ids)) != set(before["cases"][row]["agreed_roles"]):
            raise ValueError(f"保存済みの候補番号が一致しない: {row}")
        jobs[row + "/role"] = {
            "cards": job["cards"],
            "request": {**request, "prompt": PROMPT.format(row=row, ids="、".join(map(str, ids)))},
        }
        mapping[row] = meta
    rows = core.load(previous.archive / "display/selection.json")["selected"]
    pilot.SAMPLES = [rows[mapping[row]["entry"]] for row in TARGETS]
    return {"files": files, "jobs": jobs, "mapping": mapping}


def read_tags(ballot, ids):
    unknown = {ident: ("U", "U", "U") for ident in ids}
    if ballot["status"] != "readable":
        return unknown, "unreadable"
    tags = [TAG.fullmatch(term.strip()) for term in ballot["text"].split("|")]
    if not all(tags) or len(tags) != len(ids):
        return unknown, "invalid-format"
    cues = {int(tag[1]): (tag[2], tag[3], tag[4]) for tag in tags}
    if set(cues) != set(ids):
        return unknown, "invalid-format"
    return cues, "valid"


def agreed_roles(votes, ids):
    roles = {}
    for ident in ids:
        a, b = (votes[model][ident][2] for model in MODELS)
        roles[ident] = a if a == b else "U"
    return roles


def original_sessions(original, old_lock, saved_before, runtime):
    replay = core.load(previous.V99 / "replay-result.json")
    seen = previous.matched_receipts(old_lock, original, replay["lock_sha256"], runtime)
    latest_out = pilot.OUT
    pilot.OUT = prior_out
    try:
        lock = core.load(V100 / "lock.json")
        digest = core.sha(V100 / "lock.json")
        for name, job in lock["jobs"].items():
            row = name.split("/")[0]
            prior = saved_before["cases"][row]
            for model in MODELS:
                history = pilot.outcome(digest, name, model, job, runtime[model])
                if not history or history[-1]["availability"] != "received":
                    raise ValueError("前回の画像票が欠けている")
                record = history[-1]
                if (record["session"] in seen or record["session"] != prior["role_sessions"][model]
                        or record["answers"][row] != prior["role_votes"][model]):
                    raise ValueError("前回の画像票と照合できない")
                seen.add(record["session"])
    finally:
        pilot.OUT = latest_out
    if len(seen) != 96:
        raise ValueError("元の転記64票と役割32票のセッションが揃わない")
    return seen


def evaluate(row, roles, kept, original, geometry, box):
    blocked = hold.blocked_components(kept, {str(key): value for key, value in roles.items()})
    results = {}
    for rule in RULES:
        adjusted = {**roles, **{int(ident): "U" for ident in blocked[rule]}}
        votes = []
        for model in MODELS:
            digits, candidates = previous.saved.candidates(
                original["votes"][model], geometry["ink"], box[0], box[2])
            source = [item[:3] for item in candidates if item[3]]
            if [list(item) for item in source] != kept[model]:
                raise ValueError(f"元の枠判定と保存転記が一致しない: {row}")
            votes.append(previous.apply_roles(digits, source, adjusted, geometry["ink"]))
        first, second = votes
        answer = first[0] if first[2] == second[2] else core.ref.UNKNOWN
        trace = first[1] if first[2] == second[2] else None
        results[rule] = {
            "classification": previous.trial.base.changes(core.ref, answer, original["target"]),
            "answer": answer, "trace": trace, "held_commas": blocked[rule],
        }
    return results


def counts(rows, prior):
    scopes = {
        "selected": list(rows),
        "extra-controls": ["Z010", "Z015"],
        "real-comma-controls": ["Z001", "Z003", "Z009"],
        "all-16": list(prior),
    }
    fields = ("same", "omitted", "extra", "unresolved")
    summary = {}
    for group, ids in scopes.items():
        summary[group] = {}
        for rule in RULES:
            before = Counter(v for row in ids for v in prior[row][rule])
            after = Counter(v for row in ids for v in (
                rows[row]["after"][rule]["classification"] if row in rows else prior[row][rule]))
            summary[group][rule] = {
                "before": {f: before[f] for f in fields},
                "after": {f: after[f] for f in fields},
            }
    return summary


def score(args):
    plan = core.load(pilot.LOCK)
    if (core.sha(pilot.LOCK) != args.sha256 or
            any(core.sha(Path(path)) != digest for path, digest in plan["files"].items())):
        raise ValueError("事前に固定した比較と異なる")
    old, baseline, replay, original, old_lock, formal_images = prior_data()
    runtime = pilot.audit.delivery.runtime({"gpt": args.codex, "claude": args.claude})
    seen = original_sessions(original, old_lock, old, runtime)
    archived = core.load(previous.archive / "display/selection.json")["selected"]
    rows = {}
    for name, job in plan["jobs"].items():
        row = name.split("/")[0]
        meta = plan["mapping"][row]
        ids = meta["ids"]
        cues, received, formats = {}, {}, {}
        for model in MODELS:
            history = pilot.outcome(args.sha256, name, model, job, runtime[model])
            if not history or history[-1]["availability"] != "received":
                raise ValueError(f"新規票が欠けている: {row} {model}")
            record = history[-1]
            if record["session"] in seen:
                raise ValueError(f"新規票の会話が重複している: {row} {model}")
            seen.add(record["session"])
            raw = record["answers"][row]
            cues[model], formats[model] = read_tags(raw, ids)
            received[model] = {"answer": raw, "session": record["session"]}
        kept = {m: replay["cases"][row + "/new"]["votes"][m]["kept"] for m in MODELS}
        geometry = old_lock["mapping"][row]
        base = original["cases"][row + "/new"]
        box = archived[meta["entry"]]["box"]
        prior_roles = {int(ident): value for ident, value in old["cases"][row]["agreed_roles"].items()}
        restored = evaluate(row, prior_roles, kept, base, geometry, box)
        if any(restored[rule]["classification"] != baseline["rows"][row][rule] for rule in RULES):
            raise ValueError(f"前回の結果を同じ採点で再現できない: {row}")
        roles = agreed_roles(cues, ids)
        rows[row] = {
            "scores_before": restored, "after": evaluate(row, roles, kept, base, geometry, box),
            "roles_before": prior_roles, "roles_after": roles, "cues": cues,
            "format": formats, "received": received, "expected": base["target"],
            "component_ids": {"comma": geometry["comma_id"], "stroke": geometry["stroke_id"]},
        }
    if len(seen) != 106:
        raise ValueError("元の96票と新規10票の独立した会話が揃わない")
    result = {
        "scope": "development-only", "lock_sha256": args.sha256, "new_reads": 10,
        "formal_attachments_verified": formal_images,
        "counts": counts(rows, baseline["rows"]), "rows": rows,
    }
    core.save_once(HERE / "comparison.json", core.encoded(result))
    print(result["counts"], flush=True)


if __name__ == "__main__":
    launch.configure()
    if len(sys.argv) > 1 and sys.argv[1] == "compare":
        parser = argparse.ArgumentParser(description=__doc__)
        parser.add_argument("action", choices=("compare",))
        parser.add_argument("--sha256", required=True)
        parser.add_argument("--codex", required=True, type=Path)
        parser.add_argument("--claude", required=True, type=Path)
        score(parser.parse_args())
    else:
        pilot.collect = previous.collect_receipts
        pilot.snapshot = snapshot
        pilot.main()

