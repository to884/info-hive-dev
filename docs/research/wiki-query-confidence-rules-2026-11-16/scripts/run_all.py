# questions.json の全問を 3 回ずつ直列で流す。各回の費用を足し、上限を超えそうなら止める
# 試しの回（rep 0）があれば、その費用も足す。記録の場所とプラグインは paths.py で決め、run_one.py と共有する
# 使い方: python run_all.py [--reps 1,2,3] [--only R01,R11]
import argparse
import json
import subprocess
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from paths import QUESTIONS, RUNS, SCRIPTS, plugin_dir, wiki_base  # noqa: E402

LIMIT = 14.0
PER_RUN_MAX = 0.8


def cost_of(qid, rep):
    log = RUNS / f"{qid}-r{rep}.jsonl"
    if not log.is_file():
        return 0.0
    for line in reversed(log.read_bytes().decode("utf-8", "replace").splitlines()):
        if '"type":"result"' in line.replace(" ", ""):
            try:
                return float(json.loads(line).get("total_cost_usd") or 0)
            except Exception:
                return 0.0
    return 0.0


ap = argparse.ArgumentParser()
ap.add_argument("--reps", default="1,2,3")
ap.add_argument("--only", default="")
args = ap.parse_args()
plugin_dir()  # 子を起動する前に、プラグインと wiki の指定を確かめる
wiki_base()
qids = [q["id"] for q in json.loads(QUESTIONS.read_text(encoding="utf-8"))]
only = [x for x in args.only.split(",") if x]
targets = [q for q in qids if not only or q in only]
spent = sum(cost_of(q, 0) for q in qids)
for rep in [r for r in args.reps.split(",") if r]:
    for qid in targets:
        if (RUNS / f"{qid}-r{rep}.meta.json").exists():
            spent += cost_of(qid, rep)
            continue
        if spent + PER_RUN_MAX > LIMIT:
            print(f"上限に近いので止めた: {spent:.2f} USD", flush=True)
            sys.exit(2)
        p = subprocess.run([sys.executable, str(SCRIPTS / "run_one.py"), qid, str(rep)])
        c = cost_of(qid, rep)
        spent += c
        print(f"{qid} r{rep}: {c:.3f} USD 累計 {spent:.2f} USD", flush=True)
        if p.returncode != 0:
            print(f"{qid} r{rep}: run_one.py が終了コード {p.returncode} で止まった", flush=True)
            sys.exit(p.returncode)
print(f"完了: {spent:.2f} USD", flush=True)
