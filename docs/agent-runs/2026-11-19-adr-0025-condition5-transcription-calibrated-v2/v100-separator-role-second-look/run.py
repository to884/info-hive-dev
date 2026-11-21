"""固定画像の成分の役割だけを新規二読し、保存転記を再照合する。"""

import argparse
from collections import Counter, defaultdict
from importlib.util import module_from_spec, spec_from_file_location
from pathlib import Path
import re
import sys

HERE = Path(__file__).resolve().parent
V99 = HERE.parent / "v99-filter-components-before-agreement"
V97 = HERE.parent / "v97-black-punctuation-lookalikes"
spec = spec_from_file_location("saved_numeric_filter", V99 / "run.py")
saved = module_from_spec(spec)
spec.loader.exec_module(saved)
trial = saved.trial
core, launch, pilot = trial.core, trial.launch, trial.pilot
archive = pilot.OUT
pilot.HERE = HERE
pilot.OUT = core.CORPUS / "reference-v100-separator-role-second-look"
pilot.LOCK, pilot.RESULT = HERE / "lock.json", HERE / "receipts.json"
MODELS = ("gpt", "claude")
TAG = re.compile(r"([0-9]+):([SXU])")
PROMPT = (
    "添付の画像だけを見て、識別子 {row} の指定した番号 {ids} の成分をそれぞれ判定してください。"
    "Sは画像の数字列に属する区切りの記号、Xは数字列に属さない余分な画、Uは画像では区別できない場合です。"
    "番号そのものに意味はありません。個々の成分の形、数字列との間隔・高さと周囲を見て判断します。"
    "区切りの記号や余分な画が何個あるかを前提にせず、数字列の意味や表記習慣だけから補いません。"
    "数字列の転記、文字の追加、枠の所属の再判定は行いません。"
    "answersは1件、idは {row}、statusはreadable、textに指定した番号ごとに 番号:判定 を | でつないで答えます。"
    "各番号を一度ずつ答えます。分からない番号の判定にはUを使います。説明は付けません。"
)


def baseline():
    ref = core.load(V99 / "replay-result.json")
    comparison = V99 / "comparison.json"
    old_lock = V97 / "lock.json"
    if core.sha(comparison) != ref["updated_sha256"] or core.sha(old_lock) != ref["lock_sha256"]:
        raise ValueError("v99の再集計とv97の固定が一致しない")
    plan = core.load(old_lock)
    if any(core.sha(Path(p)) != digest for p, digest in plan["files"].items()):
        raise ValueError("元の固定画像・採点・母集団が変わっている")
    return ref, core.load(comparison), plan


def component_ids(votes):
    return sorted({x[2] for ballot in votes.values() for x in ballot["kept"]})


def snapshot():
    core.verify_methods()
    frozen, comparison, plan = baseline()
    jobs, mapping = {}, {}
    files = dict(plan["files"])
    files.update({str(p): core.sha(p) for p in (
        Path(__file__), HERE / "protocol.md", V99 / "run.py", V99 / "replay-result.json",
        V99 / "comparison.json", V97 / "lock.json", Path(pilot.__file__),
    )})
    rows = core.load(archive / "display/selection.json")["selected"]
    selection = pilot.OUT / "display/selection.json"
    selection.parent.mkdir(parents=True)
    core.save_once(selection, core.encoded({"selected": rows}))
    files[str(selection)] = core.sha(selection)
    for name, raw in frozen["cases"].items():
        row, arm = name.split("/")
        if arm != "new" or set(raw["votes"]) != set(MODELS):
            raise ValueError("画像だけで予備照合した二票が揃わない")
        for vote in raw["votes"].values():
            if vote["status"] == "invalid-or-unreadable":
                raise ValueError("保存票に抽出できない枠内成分がある")
        ids = component_ids(raw["votes"])
        geometry = {item["id"]: item for item in plan["mapping"][row]["ink"]}
        if not ids or any(i not in geometry or not geometry[i]["cross_axis_center_inside"]
                          or 2 * geometry[i]["axis_overlap"] < geometry[i]["axis_length"] for i in ids):
            raise ValueError("枠内の候補番号が固定の成分にない")
        old_job = plan["jobs"][name]
        images = old_job["request"]["images"]
        hashes = old_job["request"]["image_sha256"]
        if [core.sha(Path(old_job["cards"]) / image) for image in images] != hashes:
            raise ValueError("元の固定画像と異なる")
        jobs[row + "/role"] = {
            "cards": old_job["cards"],
            "request": {"ids": [row], "images": images, "image_sha256": hashes,
                        "prompt": PROMPT.format(row=row, ids="、".join(map(str, ids)))},
        }
        mapping[row] = {"entry": plan["mapping"][row]["entry"], "category": raw["group"], "ids": ids}
    if len(mapping) != 16 or comparison["sessions"] != 64:
        raise ValueError("固定16枠と保存済み64票が揃わない")
    pilot.SAMPLES = rows
    return {"jobs": jobs, "mapping": mapping, "files": files}


def collect_receipts(plan, runtimes, digest):
    counts = {m: Counter() for m in MODELS}
    seen = set()
    for name, job in plan["jobs"].items():
        for model in MODELS:
            history = pilot.outcome(digest, name, model, job, runtimes[model])
            label = history[-1]["availability"] if history else "unstarted"
            counts[model][label] += 1
            if label == "received":
                sid = history[-1]["session"]
                if sid in seen:
                    raise ValueError("新規セッションの識別子が重複")
                seen.add(sid)
    print(counts, flush=True)


def matched_receipts(plan, comparison, original_digest, runtime):
    seen = set()
    previous = pilot.OUT
    pilot.OUT = archive
    try:
        for name, job in plan["jobs"].items():
            row = name.split("/")[0]
            expected = comparison["cases"][name]
            for model in MODELS:
                history = pilot.outcome(original_digest, name, model, job, runtime[model])
                if not history or history[-1]["availability"] != "received":
                    raise ValueError("元の保存票が欠けている")
                record = history[-1]
                if (record["session"] in seen or record["session"] != expected["session_ids"][model]
                        or record["answers"][row] != expected["votes"][model]):
                    raise ValueError("元の原票の転記またはセッションと一致しない")
                seen.add(record["session"])
    finally:
        pilot.OUT = previous
    if len(seen) != 64:
        raise ValueError("元の原票64票を確認できない")
    return seen


def labels(ballot, ids):
    unknown = {i: "U" for i in ids}
    if ballot["status"] != "readable":
        return unknown, "unreadable"
    tags = [TAG.fullmatch(term.strip()) for term in ballot["text"].split("|")]
    if not all(tags) or len(tags) != len(ids):
        return unknown, "invalid-format"
    roles = {int(tag[1]): tag[2] for tag in tags}
    if roles.keys() != set(ids):
        return unknown, "invalid-format"
    return roles, "valid"


def apply_roles(digits, kept_candidates, roles, ink):
    adopted = {}
    for gap, glyph, ident in kept_candidates:
        label = roles[ident]
        if label == "U" or (label == "S" and gap in adopted):
            return core.ref.UNKNOWN, None, None
        if label == "S":
            adopted[gap] = (glyph, ident)
    structure = digits, adopted
    trace = [(gap, glyph, ident) for gap, (glyph, ident) in adopted.items()]
    return trial.measure.transcribe(structure, ink), trace, structure


def checks():
    ids = [6,7]
    ballot = {"status": "readable", "text": "6:X|7:S"}
    if labels(ballot, ids) != ({6: "X", 7: "S"}, "valid"):
        raise ValueError("判定の書式を読めない")
    ballot["text"] = "6:X|6:S"
    if labels(ballot, ids)[1] != "invalid-format":
        raise ValueError("重複番号を読んだ")
    choices = [(2,".",6),(2,",",7)]
    ink = [{"id": ident, "axis_overlap": 2, "axis_length": 2, "cross_axis_center_inside": True} for ident in ids]
    if apply_roles("12345",choices,{6:"X",7:"S"},ink)[0]["text"] != "12,345":
        raise ValueError("保存した字形を取り出せない")
    if apply_roles("12345",choices,{6:"X",7:"X"},ink)[0]["text"] != "12345":
        raise ValueError("余分な成分が残った")
    for roles in ({6:"U",7:"S"},{6:"S",7:"S"}):
        if apply_roles("12345",choices,roles,ink)[0] != core.ref.UNKNOWN:
            raise ValueError("候補の未決定が伝わらない")


def score(args):
    checks()
    plan = core.load(pilot.LOCK)
    if core.sha(pilot.LOCK) != args.sha256 or any(core.sha(Path(p)) != digest for p,digest in plan["files"].items()):
        raise ValueError("事前固定された票・画像・判定が異なる")
    replay, old_comp, original = baseline()
    runtime = pilot.audit.delivery.runtime({"gpt": args.codex, "claude": args.claude})
    seen = matched_receipts(original, old_comp, replay["lock_sha256"], runtime)
    rows = core.load(pilot.OUT / "display/selection.json")["selected"]
    counts = defaultdict(lambda: defaultdict(lambda: defaultdict(Counter)))
    causes, cases = Counter(), {}
    for name, job in plan["jobs"].items():
        row = name.split("/")[0]
        meta, old_name = plan["mapping"][row], row + "/new"
        geom = original["mapping"][row]
        bound = rows[meta["entry"]]
        old = old_comp["cases"][old_name]
        previous = replay["cases"][old_name]["votes"]
        role_votes, sources, reported, formats = {}, {}, {}, {}
        for model in MODELS:
            history = pilot.outcome(args.sha256, name, model, job, runtime[model])
            if not history or history[-1]["availability"] != "received" or history[-1]["session"] in seen:
                raise ValueError("別の新規画像セッションから二票が揃わない")
            record = history[-1]
            seen.add(record["session"])
            raw = record["answers"][row]
            role_votes[model], sources[model] = raw, record["session"]
            reported[model], formats[model] = labels(raw,meta["ids"])
        agreement = {i: reported["gpt"][i] if reported["gpt"][i] == reported["claude"][i] else "U" for i in meta["ids"]}
        results, traces, structures = {}, {}, {}
        for model in MODELS:
            parsed = saved.candidates(old["votes"][model],geom["ink"],bound["box"][0],bound["box"][2])
            if parsed is None or [list(v[:3]) for v in parsed[1] if v[3]] != previous[model]["kept"]:
                raise ValueError("元の各票が報告した枠内成分と一致しない")
            results[model], traces[model], structures[model] = apply_roles(parsed[0],previous[model]["kept"],agreement,geom["ink"])
        results["pair"] = results["gpt"] if structures["gpt"] == structures["claude"] else core.ref.UNKNOWN
        traces["pair"] = traces["gpt"] if traces["gpt"] == traces["claude"] else None
        expected = old["target"]
        checked = {m: trial.base.changes(core.ref,a,expected) for m,a in results.items()}
        verified_source = {m: trial.attribution(a,traces[m],geom) for m,a in results.items()}
        scopes = {"all", meta["category"]}
        if "extra" in old["classification"]["pair"]:
            scopes.add("previously-extra")
        for group in scopes:
            for model in (*MODELS,"pair"):
                counts[group]["before"][model].update(old["classification"][model])
                counts[group]["after"][model].update(checked[model])
        coma = geom["comma_id"]
        if coma in agreement:
            causes["included-real-comma/" + agreement[coma]] += 1
        causes["black-stroke/" + agreement[geom["stroke_id"]]] += 1
        cases[row] = {"group": meta["category"], "expected": expected, "saved": old["classification"],
                      "verdict": checked, "final": results, "source": verified_source,
                      "role_votes": role_votes, "role_sessions": sources, "parsed": reported,
                      "formats": formats, "agreed_roles": agreement, "traces": traces,
                      "component_ids": {"comma": coma, "stroke": geom["stroke_id"]}}
    if len(seen) != 96:
        raise ValueError("元の64票と新規32票が揃わない")
    core.save_once(HERE / "comparison.json",core.encoded({
        "scope": "development-only","lock_sha256": args.sha256,"saved_votes": 64,"new_role_votes": 32,
        "counts": counts,"component_role_agreement": causes,
        "cases": cases,"saved_comparison_sha256": core.sha(V99 / "comparison.json")}))
    for group, fields in counts.items():
        print(group,{label:dict(values["pair"]) for label,values in fields.items()},flush=True)
    print(dict(causes),flush=True)


if __name__ == "__main__":
    launch.configure()
    if len(sys.argv) > 1 and sys.argv[1] == "compare":
        cli = argparse.ArgumentParser(description=__doc__)
        cli.add_argument("command", choices=("compare",))
        cli.add_argument("--sha256", required=True)
        cli.add_argument("--codex", required=True, type=Path)
        cli.add_argument("--claude", required=True, type=Path)
        score(cli.parse_args())
    else:
        pilot.collect = collect_receipts
        pilot.snapshot = snapshot
        pilot.main()
