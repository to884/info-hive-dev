# 全回の要約を 1 つの JSON にまとめる（判定の抽出、手順 5b を開いたか、検索の使い方、費用）
import json
import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from summarize import summarize  # noqa: E402
from paths import require_runs  # noqa: E402

RUNS = require_runs()
rows = []
for meta in sorted(RUNS.glob("Q*-r[1-3].meta.json")):
    m = json.loads(meta.read_text(encoding="utf-8"))
    s = summarize(meta.with_name(meta.name.replace(".meta.json", ".jsonl")))
    tools = s["tools"]
    names = [t["name"] for t in tools]
    read_paths = [json.dumps(t["input"], ensure_ascii=False) for t in tools if t["name"] in ("Read", "Bash", "Grep", "Glob")]
    mcp_q = [t for t in tools if t["name"].endswith("__query")]
    warnings = []
    for t in mcp_q:
        h = t.get("result_head", "")
        w = re.search(r'"state":\s*"(\w+)"', h)
        if w:
            warnings.append(w.group(1))
    rows.append({
        "qid": m["qid"], "rep": m["rep"], "seconds": m["seconds"], "cost": s.get("cost"),
        "turns": s.get("turns"), "subtype": s.get("subtype"),
        "marks": s["confidence_marks"],
        "opened_workflow": s["opened_workflow"],
        "read_skill": any("SKILL.md" in p for p in read_paths),
        "read_index": any("index.md" in p for p in read_paths),
        "used_skill_tool": "Skill" in names,
        "mcp_queries": len(mcp_q), "mcp_states": warnings,
        "cli_search": any("wiki_search.py" in p for p in read_paths),
        "read_raw": any(("docs/research" in p or "docs\\\\research" in p or "raw/" in p or "docs/agent-runs" in p) for p in read_paths),
        "tool_names": names,
        "denials": s.get("denials"),
        "wiki_status": m["wiki_status"],
        "result": s.get("result"),
    })
(RUNS / "aggregate.json").write_bytes(json.dumps(rows, ensure_ascii=False, indent=1).encode("utf-8"))
for r in rows:
    print(r["qid"], r["rep"], r["marks"], "wf" if r["opened_workflow"] else "--",
          f"mcp={r['mcp_queries']}{r['mcp_states']}", f"${r['cost']:.3f}" if r["cost"] else "", r["seconds"], "s",
          "WIKI-CHANGED" if r["wiki_status"] else "")
