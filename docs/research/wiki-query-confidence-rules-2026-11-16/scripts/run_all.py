# questions.json の全問を 3 回ずつ直列で流す。各回の費用を足し、上限を超えそうなら止める
# 記録先にある全ログの費用を足してから始める。記録の場所とプラグインは paths.py で決め、run_one.py と共有する
# 使い方: python run_all.py [--reps 1,2,3] [--only R01,R11]
import argparse
import json
import subprocess
import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from paths import QUESTIONS, RUNS, SCRIPTS, plugin_dir, wiki_base  # noqa: E402

LIMIT = 14.0
PER_RUN_MAX = 0.8


def cost_file(log: Path) -> float:
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
# 記録先にあるすべてのログ（今回の --reps と --only の外の回、試しの回、run_one.py が退避した失敗の回を含む）の
# 費用から始める。分けて流しても、上限は記録先の全体で効く。済んだ回を飛ばすときは足さない（二重に数えない）
spent = sum(cost_file(log) for log in RUNS.glob("R*.jsonl")) if RUNS.is_dir() else 0.0
print(f"記録先の既存の回の費用: {spent:.2f} USD", flush=True)
for rep in [r for r in args.reps.split(",") if r]:
    for qid in targets:
        if (RUNS / f"{qid}-r{rep}.meta.json").exists():
            continue
        if spent + PER_RUN_MAX > LIMIT:
            print(f"上限に近いので止めた: {spent:.2f} USD", flush=True)
            sys.exit(2)
        started = time.time() - 1
        p = subprocess.run([sys.executable, str(SCRIPTS / "run_one.py"), qid, str(rep)])
        # 成功した回は <qid>-r<rep>.jsonl に、失敗した回は run_one.py が退避した名前に残る。新しくできたログだけを足す
        c = sum(cost_file(log) for log in RUNS.glob(f"{qid}-r{rep}*.jsonl") if log.stat().st_mtime >= started)
        spent += c
        print(f"{qid} r{rep}: {c:.3f} USD 累計 {spent:.2f} USD", flush=True)
        if p.returncode != 0:
            print(f"{qid} r{rep}: run_one.py が終了コード {p.returncode} で止まった", flush=True)
            sys.exit(p.returncode)
print(f"完了: {spent:.2f} USD", flush=True)
