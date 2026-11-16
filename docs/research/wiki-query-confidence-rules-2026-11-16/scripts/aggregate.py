# 全回の要約を 1 つの JSON にまとめ、1 回 1 行で表示する
# 試験用の wiki とプラグインの外のパスを読んだ回（リポジトリやプロジェクトの wiki に漏れた回）に印を付ける
import json
import os
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from summarize import summarize  # noqa: E402
from paths import QUESTIONS, plugin_dir, require_runs, wiki_base  # noqa: E402

RUNS = require_runs()
BASE, PLUGIN = wiki_base(), plugin_dir()
qs = {q["id"]: q for q in json.loads(QUESTIONS.read_text(encoding="utf-8"))}


def norm(s: str) -> str:
    return s.replace("\\\\", "/").replace("\\", "/").lower()


ALLOWED_ROOTS = [norm(str(BASE)), norm(str(PLUGIN)), "${claude_plugin_root}", "/c/userdata/" + norm(str(BASE)).split(":/", 1)[-1]]


def outside(tools) -> list:
    """試験用の wiki とプラグインの外のパスを指した呼び出しを返す"""
    hits = []
    for t in tools:
        inp = t.get("input") or {}
        vals = [inp.get(k) for k in ("file_path", "path", "wiki", "command", "pattern") if isinstance(inp.get(k), str)]
        for v in vals:
            low = norm(v)
            if ("/" in low or ":" in low) and any(m in low for m in ("c:/", "/c/", "~/", "wiki/", "docs/")):
                if not any(r in low for r in ALLOWED_ROOTS) and not low.startswith(("wiki/", "./wiki")):
                    hits.append(f"{t['name']}: {v[:120]}")
    return hits


rows = []
for meta in sorted(RUNS.glob("R*-r[0-9].meta.json")):
    m = json.loads(meta.read_text(encoding="utf-8"))
    s = summarize(meta.with_name(meta.name.replace(".meta.json", ".jsonl")))
    rows.append({
        "qid": m["qid"], "rep": m["rep"], "condition": m["condition"], "expect": qs[m["qid"]]["expect"],
        "final": s["final_marks"], "inline": s["inline_marks"], "any": s["any_marks"],
        "opened_confidence": s["opened_confidence"], "searches": s["searches"], "graph_calls": s["graph_calls"],
        "tool_names": [t["name"] for t in s["tools"]], "outside": outside(s["tools"]),
        "cost": s.get("cost"), "seconds": m["seconds"], "turns": s.get("turns"), "subtype": s.get("subtype"),
        "denials": s.get("denials"), "wiki_changed": m["wiki_changed"], "result": s.get("result"),
    })
(RUNS / "aggregate.json").write_bytes(json.dumps(rows, ensure_ascii=False, indent=1).encode("utf-8"))
total = 0.0
for r in rows:
    total += r["cost"] or 0
    print(r["qid"], r["rep"], r["condition"][:5], "exp", r["expect"], "final", r["final"], "inline", r["inline"],
          "cf" if r["opened_confidence"] else "--", "graph" if r["graph_calls"] else "",
          [(x.get("via"), x.get("mode"), (x.get("warning") or "")[:12]) for x in r["searches"]],
          f"${(r['cost'] or 0):.3f}", r["seconds"], "s", "OUTSIDE" if r["outside"] else "",
          "WIKI-CHANGED" if r["wiki_changed"] else "")
print(f"{len(rows)} 回 {total:.2f} USD", file=sys.stderr if os.environ.get("QC_QUIET") else sys.stdout)
