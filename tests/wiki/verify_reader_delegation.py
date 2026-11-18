"""モデル表の代表例を、実際の Agent ツールの経路で確かめる。手元の有料の測定。"""
from __future__ import annotations
import json
import os
from pathlib import Path
import subprocess
import shutil
from datetime import datetime, timezone
import sys
import reader_measurement_runtime as capture

out = Path(sys.argv[1]).resolve()
experiment, data = capture.recorded_experiment(out)
if (out / "delegation.json").exists():
    attempts = out / "delegation-attempts"
    attempts.mkdir(exist_ok=True)
    stamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%S%fZ")
    for name in ("delegation.json", "delegation-validation.json"):
        if (out / name).exists():
            shutil.copyfile(out / name, attempts / (stamp + "-" + name))
wiki_roots = capture.roots(out)
selection = json.loads((out / "model-selection.json").read_text(encoding="utf-8"))["selection"]
cases = [(qid, *selection[cls]["selected"].rsplit("-", 1))
         for qid, cls in [("r1-powershell", "R1"), ("r2-two-wikis", "R2"), ("r3-confidence", "R3")]]
lines = ["これは読むサブエージェントの起動の契約の試験である。下の3件を実際の Agent ツールで各1回呼ぶ。",
         "subagent_type=wiki:wiki-reader と指定の model と effort を必ず渡す。メインはページを開かない。",
         "返答を受け取ったら各件の結果を1行で報告する。モデルやeffortを独自に変更しない。"]
for qid, model, effort in cases:
    q = next(q for q in data["questions"] if q["id"] == qid)
    lines.append(f"ケース {qid}: model={model}, effort={effort}\n" + capture.reader_prompt(q, wiki_roots))
argv = ["claude", "-p", "\n\n".join(lines), "--model", "opus", "--effort", "high",
        "--plugin-dir", str(out / "plugin"), "--tools", "Agent,Read,Glob,Grep", "--allowedTools", "Agent,Read,Glob,Grep",
        "--output-format", "stream-json", "--verbose", "--permission-mode", "auto", "--max-budget-usd", "3",
        "--no-session-persistence", "--setting-sources", "", "--strict-mcp-config", "--mcp-config", '{"mcpServers":{}}',
        "--settings", json.dumps(experiment["spec"]["settings"])]
for scope, root in wiki_roots.items():
    if scope != "project":
        argv += ["--add-dir", str(root)]
proc = subprocess.run(argv, cwd=wiki_roots["project"].parent, capture_output=True, timeout=900,
                      env=dict(os.environ, **experiment["spec"]["environment"]),
                      creationflags=subprocess.CREATE_NO_WINDOW if os.name == "nt" else 0)
events = capture.parse_events(proc.stdout, wiki_roots)
record = {"exit": proc.returncode, "argv": argv, "fingerprint": experiment["fingerprint"], **events,
          "stderr": proc.stderr.decode("utf-8", "replace"), "cases": cases}
(out / "delegation.json").write_text(json.dumps(record, ensure_ascii=False, indent=1), encoding="utf-8")

calls, replies, main_reads = [], set(), []
for event in events["events"]:
    blocks = event.get("message", {}).get("content", [])
    for block in blocks if isinstance(blocks, list) else []:
        if block.get("name") == "Agent":
            calls.append({"id": block["id"], **{k: block["input"].get(k) for k in
                          ("description", "subagent_type", "model", "effort")}})
        if block.get("type") == "tool_result" and not block.get("is_error"):
            replies.add(block.get("tool_use_id"))
        if block.get("name") == "Read" and not event.get("parent_tool_use_id"):
            main_reads.append(block["input"])
for call in calls:
    call["actual_models"] = sorted({e["message"]["model"] for e in events["events"]
        if e.get("parent_tool_use_id") == call["id"] and e.get("type") == "assistant" and e.get("message", {}).get("model")})
    call["returned"] = call["id"] in replies
expected = sorted((qid, model, effort) for qid, model, effort in cases)
actual = sorted((c["description"].split()[0], c["model"], c["effort"]) for c in calls)
passed = (proc.returncode == 0 and expected == actual and not main_reads and all(
    c["returned"] and c["subagent_type"] == "wiki:wiki-reader" and c["actual_models"]
    and all(m.startswith("claude-" + c["model"] + "-") for m in c["actual_models"]) for c in calls))
validation = {"passed": bool(passed), "fingerprint": experiment["fingerprint"], "calls": calls,
              "main_reads": main_reads, "cli_version": record["cli_version"], "auto_memory": record["memory_paths"],
              "total_usd": record["cost_usd"], "selection_sha256": capture.digest((out / "model-selection.json").read_bytes()),
              "effort_evidence": "引数の受理と戻りの成否はpassedで示す。バックエンドの実効effortの値は応答にないため直接の観測はない。",
              "scope": "MCPなしのRead経路。親の起動と3呼出を含む合計であり、全組の総費用の比較ではない。"}
(out / "delegation-validation.json").write_text(json.dumps(validation, ensure_ascii=False, indent=1), encoding="utf-8")
print(json.dumps(validation, ensure_ascii=False))
raise SystemExit(0 if passed else 1)
