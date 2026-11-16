# 11 問 × 3 回を直列で流す。各回の費用を足し、上限を超えそうなら止める
# 記録の場所とプラグインは paths.py（環境変数 QC_RUNS_DIR、QC_PLUGIN_DIR）で決め、run_one.py と共有する
import json
import subprocess
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from paths import RUNS, SCRIPTS, plugin_dir  # noqa: E402

LIMIT = 15.0


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


plugin_dir()  # 子を起動する前に、プラグインの指定を確かめる
spent = cost_of("Q01", 0)  # 試しの 1 回（あれば）
qids = [f"Q{i:02d}" for i in range(1, 12)]
for rep in (1, 2, 3):
    for qid in qids:
        if (RUNS / f"{qid}-r{rep}.meta.json").exists():
            spent += cost_of(qid, rep)
            continue
        if spent + 0.8 > LIMIT:
            print(f"上限に近いので止めた: {spent:.2f} USD", flush=True)
            sys.exit(2)
        p = subprocess.run([sys.executable, str(SCRIPTS / "run_one.py"), qid, str(rep)])
        if p.returncode != 0:
            print(f"{qid} r{rep}: run_one.py が終了コード {p.returncode} で止まった", flush=True)
            sys.exit(p.returncode)
        c = cost_of(qid, rep)
        spent += c
        print(f"{qid} r{rep}: {c:.3f} USD 累計 {spent:.2f} USD", flush=True)
print(f"完了: {spent:.2f} USD", flush=True)
