"""Sonnet で /wiki:overview の手順を測る。通常の unittest からは呼ばない。

    python -X utf8 -B tests/wiki/measure_overview_command.py --runs 3 --out <結果.json>

Claude の実行には費用がかかる。使い捨ての wiki だけを書き換え、思考とツールの結果本文は保存しない。
"""
from __future__ import annotations

import argparse
import json
import os
import re
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
PLUGIN = ROOT / "info-hive-wiki"
sys.path.insert(0, str(PLUGIN / "skills/info-hive/scripts"))
import wiki_overview

PAGE = "測定のページ"
SOURCE = """---
type: "concept"
title: "測定のページ"
tags: ["文書整理"]
created: 2026-11-17
updated: 2026-11-17
---

# 資料を整理する流れ

資料を集めたら、まず原本を残す。次に内容を読み、話題ごとに短いメモを作る。
同じ話題のメモがあれば、どこが共通しどこが違うかを比べてから追記する。
最後に一覧を更新し、次に探す人がメモを見つけられるようにする。
原本は資料を確かめ直すために残し、一覧は読む場所を案内するために使う。
メモの内容が変わったら、一覧の短い説明も実物に合わせて直す。
"""


def _texts(content) -> str:
    if isinstance(content, str):
        return content
    if not isinstance(content, list):
        return ""
    return "\n".join(block.get("text", "") for block in content
                     if isinstance(block, dict) and block.get("type") == "text")


def _json_objects(text: str) -> list:
    """ツールの結果にある JSON を読む。呼び出しの文字列を成功の証拠にしない。"""
    decoder = json.JSONDecoder()
    found = []
    position = 0
    while (start := text.find("{", position)) >= 0:
        try:
            value, end = decoder.raw_decode(text[start:])
        except ValueError:
            position = start + 1
            continue
        position = start + end
        if isinstance(value, dict):
            if "status" in value:
                found.append(value)
            elif isinstance(value.get("stdout"), str):
                found.extend(_json_objects(value["stdout"]))
    return found


def analyze_trace(stdout: str) -> dict:
    """呼び出しと結果を ID で結ぶ。結果の欠落、ツール失敗、rejected は成功に数えない。"""
    events, results, models, final = [], {}, set(), {}
    seen = set()
    for position, line in enumerate(stdout.splitlines()):
        try:
            row = json.loads(line)
        except ValueError:
            continue
        message = row.get("message", {})
        if row.get("type") == "assistant":
            if message.get("model"):
                models.add(message["model"])
            for block in message.get("content", []):
                if not isinstance(block, dict) or block.get("type") != "tool_use":
                    continue
                identifier = block.get("id")
                if not isinstance(identifier, str) or identifier in seen:
                    continue
                seen.add(identifier)
                event = {"tool": block.get("name", ""), "id": identifier, "position": position}
                for key in ("file_path", "command"):
                    value = block.get("input", {}).get(key)
                    if isinstance(value, str):
                        event[key] = value
                events.append(event)
        elif row.get("type") == "user":
            content = message.get("content", [])
            for block in content if isinstance(content, list) else []:
                if isinstance(block, dict) and block.get("type") == "tool_result":
                    results[block.get("tool_use_id")] = (block.get("is_error", False) is False, _texts(block.get("content")), position)
        elif row.get("type") == "result":
            final = row
    operations, request_writes, successful_begins = [], [], []
    guide_parts, copy_parts = [], []
    page_in_shell = direct_write = False
    for event in events:
        successful, text, result_position = results.get(event["id"], (False, "", -1))
        event["successful"] = successful
        event["result_position"] = result_position
        tool = event["tool"]
        path = event.get("file_path", "").replace("\\", "/")
        if tool == "Read" and successful:
            if path.endswith("/overview-workflow.md"):
                guide_parts.append(text)
            if "/overview/work/" in path and path.endswith("/page.md"):
                copy_parts.append(text)
        if tool == "Write":
            if path.endswith("/overview/request.json"):
                request_writes.append((event["position"], successful))
            direct_write |= "/assets/overview/" in path
        if tool == "Bash":
            command = event.get("command", "")
            page_in_shell |= PAGE in command
            values = _json_objects(text) if successful else []
            event["result_statuses"] = [value.get("status") for value in values]
            matches = list(re.finditer(r'wiki_overview\.py["\']?\s+(begin|prepare|check|write|status|remove)\b', command))
            for offset, match in enumerate(matches):
                op = match.group(1)
                value = values[offset] if offset < len(values) else {}
                expected = {"begin": "ready", "prepare": "ready", "check": "ok", "write": "written",
                            "remove": "removed"}.get(op)
                ok = successful and expected is not None and value.get("status") == expected
                operations.append({"order": len(operations), "operation": op, "successful": ok,
                                   "event": event["id"], "position": event["position"], "result_position": result_position})
                if op == "begin" and ok and isinstance(value.get("request_path"), str):
                    successful_begins.append(result_position)
    checks = {"guide_read": all(part in "\n".join(guide_parts) for part in ("SVG と Mermaid", "## 下書きの形", "## 図を書くときの目安")),
              "page_copy_read": all(part in "\n".join(copy_parts) for part in ("資料を整理する流れ", "原本は資料を確かめ直す", "メモの内容が変わったら")),
              "begin_before_request_write": any(ok for _, ok in request_writes) and all(any(begin < position for begin in successful_begins) for position, _ in request_writes),
              "check_then_write": any(c["operation"] == "check" and c["successful"] and w["operation"] == "write" and w["successful"] and c["order"] < w["order"]
                                      and (c["result_position"] < w["position"] or c["event"] == w["event"])
                                      for c in operations for w in operations),
              "page_not_in_shell": not page_in_shell, "no_direct_sidecar_write": not direct_write,
              "final_success": final.get("subtype") == "success" and final.get("is_error") is False,
              "sonnet_5_5": any(re.fullmatch(r"claude-sonnet-5-5(?:-\d+)?", model) for model in models)}
    return {"events": events, "models": sorted(models), "final": final, "checks": checks,
            "operations": [op["operation"] for op in operations]}


def measure(executable: str, number: int, timeout: int) -> dict:
    with tempfile.TemporaryDirectory(prefix="overview-sonnet-") as tmp:
        fixture = Path(tmp)
        wiki = fixture / "wiki"
        wiki.mkdir()
        (fixture / "raw").mkdir()
        (wiki / "concepts").mkdir()
        schema = "# スキーマ\n\nこの wiki は使い捨ての測定用である。日本語で書く。\n"
        (wiki / "SCHEMA.md").write_bytes(schema.encode("utf-8"))
        source = wiki / "concepts" / f"{PAGE}.md"
        original = SOURCE.encode("utf-8")
        source.write_bytes(original)
        (fixture / ".info-hive.json").write_bytes(json.dumps({"dirs": {"wiki": "wiki", "raw": "raw"}}).encode("utf-8"))
        extra = (f"この依頼は使い捨ての wiki のコマンドの測定である。プロジェクトの wiki は {wiki.as_posix()}、"
                 f"raw は {(fixture / 'raw').as_posix()} である。この wiki だけを対象にする。"
                 "指定した /wiki:overview を手順どおりに行い、必要な場合以外はファイルを読まない。"
                 "プロジェクトの承認・公開・Git 操作は不要である。")
        command = [executable, "--plugin-dir", str(PLUGIN), "--model", "sonnet", "--effort", "high",
                   "--print", f"/wiki:overview {PAGE}", "--output-format", "stream-json", "--verbose",
                   "--permission-mode", "auto", "--permission-prompts", "none", "--no-session-persistence",
                   "--strict-mcp-config", "--mcp-config", '{"mcpServers":{}}',
                   "--tools", "Read,Write,Bash", "--allowedTools", "Read,Write,Bash(python:*)",
                   "--append-system-prompt", extra]
        try:
            done = subprocess.run(command, cwd=fixture, capture_output=True, encoding="utf-8", errors="replace",
                                  timeout=timeout, env={**os.environ, "PYTHONUTF8": "1"})
        except subprocess.TimeoutExpired:
            return {"run": number, "status": "timeout", "passed": False}
        trace = analyze_trace(done.stdout)
        events, final = trace['events'], trace['final']
        error = str(final.get('result', '')) if final.get('is_error') else ''
        if not final:
            error = done.stderr[-2000:] or '最終イベントがない'
        blocked = '5-hour limit' in error or 'usage limit' in error.lower() or 'rate limit' in error.lower()
        try:
            inspection = wiki_overview.status(wiki)
            saved = len(inspection['overviews']) == 1 and inspection['overviews'][0]['state'] == 'fresh'
        except (OSError, wiki_overview.OverviewError):
            saved = False
        checks = {**trace['checks'], 'saved_fresh': saved, 'source_preserved': source.read_bytes() == original}
        safe_events = []
        for event in events:
            safe = {key: (value.replace(str(fixture), "<fixture>").replace(fixture.as_posix(), "<fixture>")
                    .replace(str(PLUGIN), "<plugin>").replace(PLUGIN.as_posix(), "<plugin>") if isinstance(value, str) else value)
                    for key, value in event.items()}
            safe_events.append(safe)
        return {"run": number, "status": "blocked" if blocked else "completed", "exit_code": done.returncode,
                "models": trace["models"], "checks": checks, "operations": trace["operations"], "events": safe_events,
                "error": error[:2000], "permission_denials": final.get("permission_denials", []),
                "passed": not error and done.returncode == 0 and all(checks.values())}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--runs", type=int, default=3)
    parser.add_argument("--timeout", type=int, default=600)
    parser.add_argument("--out", type=Path, required=True)
    args = parser.parse_args()
    executable = shutil.which("claude") or str(Path.home() / ".local/bin/claude.exe")
    results = []
    for number in range(1, args.runs + 1):
        result = measure(executable, number, args.timeout)
        results.append(result)
        summary = {"requested_model": "sonnet", "runs": results, "passed": all(r["passed"] for r in results),
                   "complete": len(results) == args.runs and not any(r["status"] == "blocked" for r in results)}
        args.out.parent.mkdir(parents=True, exist_ok=True)
        args.out.write_bytes((json.dumps(summary, ensure_ascii=False, indent=2) + "\n").encode("utf-8"))
        print(json.dumps({"run": number, "status": result["status"], "passed": result["passed"]}, ensure_ascii=False), flush=True)
        if result["status"] == "blocked" or result.get("permission_denials"):
            return 3
    return 0 if all(r["passed"] for r in results) else 1


if __name__ == "__main__":
    raise SystemExit(main())
