# 11 問 × 3 回を直列で流す。各回の費用を足し、上限を超えそうなら止める
import json
import subprocess
import sys
from pathlib import Path

SCRATCH = Path(__file__).resolve().parent
LIMIT = 15.0
spent = 0.246  # 試しの 1 回


def cost_of(qid, rep):
    log = SCRATCH / "runs" / f"{qid}-r{rep}.jsonl"
    for line in reversed(log.read_bytes().decode("utf-8", "replace").splitlines()):
        if '"type":"result"' in line.replace(" ", ""):
            try:
                return float(json.loads(line).get("total_cost_usd") or 0)
            except Exception:
                return 0.0
    return 0.0


qids = [f"Q{i:02d}" for i in range(1, 12)]
for rep in (1, 2, 3):
    for qid in qids:
        if (SCRATCH / "runs" / f"{qid}-r{rep}.meta.json").exists():
            spent += cost_of(qid, rep)
            continue
        if spent + 0.8 > LIMIT:
            print(f"上限に近いので止めた: {spent:.2f} USD", flush=True)
            sys.exit(2)
        subprocess.run([sys.executable, str(SCRATCH / "run_one.py"), qid, str(rep)])
        c = cost_of(qid, rep)
        spent += c
        print(f"{qid} r{rep}: {c:.3f} USD 累計 {spent:.2f} USD", flush=True)
print(f"完了: {spent:.2f} USD", flush=True)
