"""Claude Code に製品プラグインを読み込ませ、wiki の取り込み経路を検証する。"""
import hashlib
import json
import os
import subprocess
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
OUT = ROOT / "docs/research/rag-pdf-job-integration-2026-11-04"
RUN = ROOT / ".rag-poc-data" / f"c{int(time.time())}"
RUN.mkdir(parents=True)
base = sorted((ROOT / ".rag-poc-data").glob("j*/config.json"))[-1]
config = json.loads(base.read_text(encoding="utf-8"))
source = next(Path(config["reference_roots"]["fixture"]).glob("*.pdf"))
before = hashlib.sha256(source.read_bytes()).hexdigest()
config["data_dir"] = str(RUN / "data")
config_path = RUN / "config.json"
config_path.write_text(json.dumps(config, ensure_ascii=False, indent=2), encoding="utf-8")
project = RUN / "project"
wiki = project / "wiki"
(wiki / "sources").mkdir(parents=True)
(wiki / "SCHEMA.md").write_text("# 検証用 wiki\n\n日本語で書く。原本は複製せず、raw は名前付き参照を使う。要約の出典とページ番号を示す。index.md と log.md を更新する。frontmatter の文字列は二重引用符で囲む。\n", encoding="utf-8")
(wiki / "index.md").write_text("# 検証用 wiki\n", encoding="utf-8")
(wiki / "log.md").write_text("# 操作記録\n", encoding="utf-8")
env = {**os.environ, "INFO_HIVE_RAG_CONFIG": str(config_path), "PYTHONUTF8": "1", "PYTHONIOENCODING": "utf-8", "PYTHONDONTWRITEBYTECODE": "1"}
command = ["claude", "-p", "--output-format", "stream-json", "--verbose", "--no-session-persistence",
           "--setting-sources", "", "--permission-mode", "acceptEdits", "--max-budget-usd", "5",
           "--plugin-dir", str(ROOT / "info-hive-wiki"), "--plugin-dir", str(ROOT / "info-hive-rag"),
           "--add-dir", str(RUN), "--add-dir", str(source.parent),
           "--allowedTools", "Read,Write,Edit,Grep,Glob,Skill,mcp__plugin_rag_rag__*"]


def invoke(label, prompt):
    path = RUN / f"{label}.jsonl"
    started = time.perf_counter()
    with path.open("w", encoding="utf-8") as log:
        result = subprocess.run(command[:2] + [prompt] + command[2:], cwd=project, stdout=log, stderr=log, encoding="utf-8", env=env, timeout=600)
    events = []
    for line in path.read_text(encoding="utf-8").splitlines():
        try: events.append(json.loads(line))
        except json.JSONDecodeError: pass
    tools = [item for event in events if isinstance(event.get("message"), dict)
             for item in event["message"].get("content", [])
             if isinstance(item, dict) and item.get("type") == "tool_use"]
    result_event = next((e for e in reversed(events) if e.get("type") == "result"), {})
    summary = {"returncode": result.returncode, "seconds": time.perf_counter()-started,
               "tools": [{"name": t["name"], "input": t.get("input")} for t in tools],
               "result": result_event.get("result"), "is_error": result_event.get("is_error"),
               "mcp_servers": next((e.get("mcp_servers") for e in events if e.get("type") == "system" and e.get("subtype") == "init"), None)}
    print(json.dumps({"phase": label, **summary}, ensure_ascii=False), flush=True)
    return summary


result = {"run_dir": str(RUN), "config": str(config_path), "wiki": str(wiki)}
try:
    result["command_ingest"] = invoke("register", f"/wiki:ingest {source}\n\n対象 wiki は {wiki}、RAW_ROOT は {project / 'raw'}。RAG 連携を使う。今回は register_pdf で取り込みを受け付け、ジョブ ID と受付状態を報告したら終了してください。OCR や索引化の完了は待たず、原本のコピーと要約ページの作成はしないでください。")
    if result["command_ingest"]["returncode"] or result["command_ingest"]["is_error"]:
        result["verification_status"] = "blocked_authentication" if "authenticate" in (result["command_ingest"].get("result") or "") else "failed"
        raise RuntimeError(result["command_ingest"].get("result") or "Claude Code の起動に失敗しました。")
    OUT.mkdir(parents=True, exist_ok=True)
    (OUT / "claude-results.json").write_text(json.dumps(result, ensure_ascii=False, indent=2), encoding="utf-8")
    # 登録の実行が確認できた場合だけ、自然言語から同じジョブの続きへ進む。
    import sqlite3
    with sqlite3.connect(RUN / "data/jobs.sqlite") as db:
        row = db.execute("SELECT id,status FROM ingest_jobs ORDER BY created_at LIMIT 1").fetchone()
    assert row, "Claude Code の取り込みでジョブが登録されていません。"
    identity, status = row
    result["after_first_exit"] = {"job_id": identity, "status": status}
    result["natural_language_resume"] = invoke("resume", f"先ほど受け付けた PDF の取り込みを続け、完了させてください。対象 wiki は {wiki}、ジョブ ID は {identity} です。info-hive スキルの取り込み手順を使い、job_status の wait_seconds=30 で完了を待ってから、抽出 Markdown を読み、sources の要約ページ、index.md、log.md を更新してください。原本のコピーはしないでください。これは自作の検証用資料なので、要点の事前確認は省略して進めてください。")
    result["source_pages"] = [str(p.relative_to(wiki)) for p in (wiki / "sources").glob("*.md")]
    result["raw_pdf_copies"] = [str(p) for p in project.rglob("*.pdf")]
    result["original_unchanged"] = hashlib.sha256(source.read_bytes()).hexdigest() == before
    with sqlite3.connect(RUN / "data/jobs.sqlite") as db:
        state = db.execute("SELECT status,attempts FROM ingest_jobs WHERE id=?", (identity,)).fetchone()
    result["final_job"] = {"status": state[0], "attempts": state[1]}
    pages = list((wiki / "sources").glob("*.md"))
    result["checks"] = [
        {"name": "wiki_command_calls_register_pdf", "passed": any(t["name"].endswith("__register_pdf") for t in result["command_ingest"]["tools"])},
        {"name": "first_exit_keeps_unfinished_job", "passed": status in {"queued", "running", "paused"}},
        {"name": "next_session_completes_same_job", "passed": state[0] == "completed" and state[1] >= 2},
        {"name": "source_page_has_reference_and_job", "passed": any(identity in p.read_text(encoding="utf-8") and "fixture:" in p.read_text(encoding="utf-8") for p in pages)},
        {"name": "wiki_index_and_log_updated", "passed": len((wiki / "index.md").read_text(encoding="utf-8").splitlines()) > 1 and len((wiki / "log.md").read_text(encoding="utf-8").splitlines()) > 1},
        {"name": "original_not_copied_or_changed", "passed": not result["raw_pdf_copies"] and result["original_unchanged"]},
    ]
    assert all(check["passed"] for check in result["checks"]), result["checks"]
    result["verification_status"] = "passed"
finally:
    OUT.mkdir(parents=True, exist_ok=True)
    (OUT / "claude-results.json").write_text(json.dumps(result, ensure_ascii=False, indent=2), encoding="utf-8")
