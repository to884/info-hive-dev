"""固定済み開発画像で、縦列と枠境界の確認指示を二系統で比較する。"""

import argparse
from collections import Counter
from concurrent.futures import ThreadPoolExecutor
import importlib.util
import json
from pathlib import Path
from shutil import copyfile

HERE = Path(__file__).resolve().parent
PREVIOUS = HERE.parent / "sol-bracket-scope-repeats/run.py"
spec = importlib.util.spec_from_file_location("saved_scope_repeats", PREVIOUS)
prior = importlib.util.module_from_spec(spec)
spec.loader.exec_module(prior)
base, trial = prior.base, prior.trial
opus = prior.prior.prior.fable.sol_run.opus_run
OUT = trial.ROOT / HERE.name
ARMS = ("control", "geometry")
MODELS = {"sol": prior.MODEL, "opus": opus.MODEL}
LABELS = ("correct", "wrong", "unresolved")
EXTRA = (
    "縦書きは枠と周辺から先に列を見分け、右の列から順に、列内は上から下へ読んでください。"
    "枠の端にかかる字は450 DPIの枠なし画像で隣の字と区別し、同じ字の離れた点や線を含む"
    "字全体を見つけてから、150 DPIで指定軸の半分以上と直交方向の中心を確認してください。"
    "字の識別、所属、順序を確認しても決まらない場合は判読不能としてください。\n"
)


def material():
    rows, _, images, past, source = prior.original()
    past |= {r["session"] for r in base.load(PREVIOUS.parent / "result.json")["receipts"]}
    targets = [r for r in rows if r["case"] == "edge" or r["case"].startswith("v")]
    groups = {"vertical": [r["id"] for r in targets if r["case"].startswith("v")],
              "edge": [r["id"] for r in targets if r["case"] == "edge"]}
    if [len(g) for g in groups.values()] != [12, 4]:
        raise ValueError("固定対象の内訳が異なる")
    control = trial.prompt("old", [r["id"] for r in targets])
    if control.count(base.FORMAT) != 1:
        raise ValueError("指示と回答形式の境界を一意に決められない")
    geometry = control.replace(base.FORMAT, EXTRA + base.FORMAT, 1)
    image_pack = {k: source["packs"]["32-old"][k] for k in ("images", "image_sha256")}
    sheets = dict.fromkeys(str(r["sheet"]) for r in targets)
    study, _, _ = trial.check("comparison", source["comparison_lock_sha256"])
    if [n for s in sheets for n in study["image_order_by_sheet"][s]] != image_pack["images"]:
        raise ValueError("16行の画像の順序が対象によって変わる")
    packs = {arm: {**image_pack, "ids": [r["id"] for r in targets], "prompt": prompt}
             for arm, prompt in zip(ARMS, (control, geometry), strict=True)}
    frozen = {"script_sha256": base.sha(Path(__file__)), "protocol_sha256": base.sha(HERE / "protocol.md"),
              "comparison_lock_sha256": source["comparison_lock_sha256"],
              "models": MODELS, "effort": "medium", "groups": groups, "packs": packs}
    return targets, images, study, past, frozen


def read(exe, who, arm, pack, rows, images, study):
    dst = OUT / who / arm
    dst.mkdir(parents=True, exist_ok=True)
    if who == "sol":
        reader = prior.prior.prior.fable.load_module(f"geometry_{who}_{arm}", base.__file__)
        reader.PRIVATE = dst
        reader.prompt_for = lambda unused_arm, ids: pack["prompt"] if ids == pack["ids"] else None
        for name, digest in zip(pack["images"], pack["image_sha256"], strict=True):
            copyfile(images / name, dst / name)
            if base.sha(dst / name) != digest:
                raise ValueError("配布画像のSHAが変化")
        answers, receipt = reader.read_images(exe, study, rows, arm, 1, MODELS[who])
        request = base.load(dst / f"{arm}-read1-{MODELS[who]}-request.json")
        if request["model"] != MODELS[who] or any(request[k] != v for k, v in pack.items()):
            raise ValueError("Solに配った入力が変化")
    else:
        reader = prior.prior.prior.fable.load_module(f"geometry_{who}_{arm}", opus.__file__)
        reader.MODEL, reader.OUT = MODELS[who], dst
        answers, receipt = reader.read_opus(exe, arm, pack, images)
    return answers, dict(receipt, role=who)


def summarize(rows, frozen, votes):
    ids = [r["id"] for r in rows]
    final = {arm: {i: base.consensus([votes[arm, who][i] for who in MODELS]) for i in ids} for arm in ARMS}
    outcomes = {}
    for group, members in frozen["groups"].items():
        subset = [r for r in rows if r["id"] in members]
        measures = {arm: {k: prior.trial.rep.metrics(subset, v) for k, v in
                         [("agreement", final[arm]), *((who, votes[arm, who]) for who in MODELS)]}
                    for arm in ARMS}
        transitions = Counter(
            tuple(prior.prior.prior.old.saved.status(base.normalize(r["gold"]), final[a][r["id"]]) for a in ARMS)
            for r in subset
        )
        outcomes[group] = {"metrics": measures, "transitions": {f"{a}->{b}": count for (a, b), count in transitions.items()}}
    vert, edge = ([outcomes[group]["metrics"][a]["agreement"] for a in ARMS] for group in ("vertical", "edge"))
    advance = (vert[1]["exact"] > vert[0]["exact"] and vert[1]["unknown"] < vert[0]["unknown"]
               and all(vert[1][k] <= vert[0][k] for k in ("wrong", "missing_chars", "extra_chars"))
               and edge[1]["exact"] >= edge[0]["exact"])
    return {"groups": outcomes, "advance": advance}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("action", choices=("prepare", "run"))
    parser.add_argument("--codex", type=Path)
    parser.add_argument("--claude", type=Path)
    parser.add_argument("--lock-sha256")
    args = parser.parse_args()
    lock = HERE / "lock.json"
    rows, images, study, past, frozen = material()
    if args.action == "prepare":
        if lock.exists():
            raise FileExistsError(lock)
        base.write_json(lock, dict(frozen, fixed_at=base.utc_now()))
        print(base.sha(lock), flush=True)
        return
    if base.sha(lock) != args.lock_sha256 or {k: v for k, v in base.load(lock).items() if k != "fixed_at"} != frozen:
        raise ValueError("固定済みの入力と一致しない")
    executables = {"sol": args.codex.resolve(), "opus": args.claude.resolve()}
    with ThreadPoolExecutor(max_workers=4) as pool:
        tasks = {(a, w): pool.submit(read, exe, w, a, frozen["packs"][a], rows, images, study)
                 for a in ARMS for w, exe in executables.items()}
        records = {key: task.result() for key, task in tasks.items()}
    receipts = [receipt for _, receipt in records.values()]
    sessions = {r["session"] for r in receipts}
    if len(sessions) != len(records) or sessions & past:
        raise ValueError("読取セッションが重複")
    if material()[-1] != frozen or base.sha(lock) != args.lock_sha256:
        raise ValueError("読取中に固定済みの入力が変化")
    scores = summarize(rows, frozen, {key: values for key, (values, _) in records.items()})
    base.write_json(HERE / "result.json", dict(scores, receipts=receipts, lock_sha256=args.lock_sha256))
    print(json.dumps(scores, ensure_ascii=False), flush=True)


if __name__ == "__main__":
    main()
