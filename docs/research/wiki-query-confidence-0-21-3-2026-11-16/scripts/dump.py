# 判定を付けるために、各回の道具の呼び出しの順と、回答を短く書き出す
# 使い方: python dump.py R07 R08 ...（問いの番号。省くと全部）
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from summarize import summarize  # noqa: E402
from paths import require_runs  # noqa: E402

RUNS = require_runs()
want = set(sys.argv[1:])


def brief(t):
    inp = t.get("input") or {}
    name = t["name"].replace("mcp__plugin_wiki_wiki__", "mcp:")
    if name == "Read":
        return "Read " + Path(str(inp.get("file_path", ""))).name
    if name == "Bash":
        return "Bash " + str(inp.get("command", ""))[-110:]
    if name.startswith("mcp:"):
        return name + " " + json.dumps({k: v for k, v in inp.items() if k != "wiki"}, ensure_ascii=False)[:100]
    return name + " " + json.dumps(inp, ensure_ascii=False)[:80]


for log in sorted(RUNS.glob("R*-r[0-9].jsonl")):
    qid = log.name.split("-")[0]
    if want and qid not in want:
        continue
    s = summarize(log)
    print("=" * 30, log.name)
    for i, t in enumerate(s["tools"]):
        print(f"  {i:2d}", brief(t))
    print(s.get("result") or "(回答なし)")
