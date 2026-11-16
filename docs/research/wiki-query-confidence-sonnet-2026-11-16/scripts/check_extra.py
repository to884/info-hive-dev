# 外の知識の語と、MCP の結果の mode・warning・state を全回で抜き出す
import json
import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from paths import SUMMARY, require_runs  # noqa: E402

RUNS = require_runs()
rows = json.loads(SUMMARY.read_text(encoding="utf-8"))
pat = re.compile(r"AGENTS|CLAUDE\.md|wiki の外|補足|一般に|一般的|CSP|ADR-0010|Rust|astral|Fowler|Microsoft")
for r in rows:
    a = r["answer"] or ""
    hits = sorted(set(m.group(0) for m in pat.finditer(a)))
    if hits:
        print(r["qid"], r["rep"], hits)

print("=== mcp")
used = 0
for f in sorted(RUNS.glob("Q*.jsonl")):
    ids, out = {}, []
    for line in f.read_bytes().decode("utf-8", "replace").splitlines():
        try:
            d = json.loads(line)
        except json.JSONDecodeError:
            continue
        c = d.get("message", {}).get("content", []) if isinstance(d.get("message"), dict) else []
        if not isinstance(c, list):
            continue
        for x in c:
            if x.get("type") == "tool_use" and x["name"].startswith("mcp__plugin_wiki_wiki__"):
                ids[x["id"]] = x["name"].split("__")[-1]
            if x.get("type") == "tool_result" and x.get("tool_use_id") in ids:
                b = x.get("content")
                b = " ".join(y.get("text", "") for y in b) if isinstance(b, list) else (b or "")
                mo = re.search(r'"mode":\s*"(\w+)"', b)
                w = re.search(r'"warning":\s*(null|"[^"]*")', b)
                s = re.search(r'"state":\s*"(\w+)"', b)
                out.append((ids[x["tool_use_id"]], mo and mo.group(1), w and w.group(1)[:30], s and s.group(1)))
    if any(o[0] == "query" for o in out) and not f.name.endswith("r0.jsonl"):
        used += 1
    print(f.name, out)
print("query を使った本番の回:", used)
