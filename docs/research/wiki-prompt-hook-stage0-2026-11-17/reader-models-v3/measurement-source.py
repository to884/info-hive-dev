"""読むモデルの測定の実行側。採点器と分け、再採点で入力の指紋を変えない。"""
from __future__ import annotations


import argparse


import concurrent.futures


import hashlib


import json


import math


import os


import random


import re


import subprocess


import sys


import threading


import unicodedata


from datetime import datetime, timezone


from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]


PLUGIN = ROOT / "info-hive-wiki"


DATA = Path(__file__).resolve().parent / "fixtures" / "prompt_context" / "reader_questions.json"


COMBOS = [("haiku", "low"), ("haiku", "medium"), ("sonnet", "low"), ("sonnet", "medium"), ("opus", "high"),
          ("fable", "medium")]


INLINE = ("opus", "inline")   # R0 の境目: メインが自分で開く


TOOLS = ["Read", "Glob", "Grep"]


PROTOCOL = 3


SCRIPTS = PLUGIN / "skills/info-hive/scripts"


def digest(value: bytes) -> str:
    return hashlib.sha256(value).hexdigest()


def verify_inputs(out: Path, saved: dict) -> None:
    actual = {p.relative_to(out).as_posix() for directory in (out / "snapshot", out / "plugin")
              for p in directory.rglob("*") if p.is_file()}
    if actual != set(saved["files"]):
        raise ValueError("固定した入力のファイル一覧が変わった")
    for rel, expected in saved["files"].items():
        if digest((out / rel).read_bytes()) != expected:
            raise ValueError(f"固定した入力が変わった: {rel}")


def recorded_experiment(out: Path) -> tuple[dict, dict]:
    """再採点では当時の入力と来歴を検証し、現在の製品の定義や CLI の版を混ぜない。"""
    saved = json.loads((out / "experiment.json").read_text(encoding="utf-8"))
    source_key = "runtime_sha256" if saved["spec"]["protocol"] == 3 else "harness_sha256"
    for name, key in (("measurement-source.py", source_key), ("measurement-questions.json", "data_sha256")):
        if digest((out / name).read_bytes()) != saved["spec"][key]:
            raise ValueError(f"測定時の記録が変わった: {name}")
    verify_inputs(out, saved)
    if saved["spec"]["protocol"] not in (2, 3):
        raise ValueError("対応していない測定の形式")
    return saved, json.loads((out / "measurement-questions.json").read_text(encoding="utf-8"))


def prepare(out: Path, runs: int) -> dict:
    """固定した wiki と読むエージェントを保存し、再開時も入力が変わっていないことを確かめる。"""
    from eval_prompt_context import materialize

    data = json.loads(DATA.read_text(encoding="utf-8"))
    agent = (PLUGIN / "agents/wiki-reader.md").read_bytes()
    spec = {"protocol": PROTOCOL, "wiki_commit": data["wiki_commit"], "data_sha256": digest(DATA.read_bytes()),
            "agent_sha256": digest(agent), "runtime_sha256": digest(Path(__file__).read_bytes()),
            "runs": runs, "combos": [list(c) for c in COMBOS], "tools": TOOLS,
            "inline_effort": "high", "seed": 32,
            "environment": {"INFO_HIVE_PROMPT_CONTEXT": "0", "CLAUDE_CODE_DISABLE_AUTO_MEMORY": "1", "DISABLE_AUTOUPDATER": "1"},
            "settings": {"autoMemoryEnabled": False, "claudeMdExcludes": ["**/CLAUDE.md", "**/CLAUDE.local.md", "**/AGENTS.md", "**/.claude/rules/**"]}}
    manifest = out / "experiment.json"
    if manifest.exists():
        saved = json.loads(manifest.read_text(encoding="utf-8"))
        if saved["spec"] != spec:
            raise ValueError("測定の条件が変わった。別の --out を使う")
        verify_inputs(out, saved)
        return saved
    if (out / "runs").exists():
        raise ValueError("旧形式の記録には読み取り成功の証拠がない。別の --out を使う")
    out.mkdir(parents=True, exist_ok=True)
    materialize(data["wiki_commit"], out / "snapshot/project")
    for scope, pages in data.get("extra_wikis", {}).items():
        root = out / "snapshot" / scope / "wiki"
        root.mkdir(parents=True, exist_ok=True)
        (root / "SCHEMA.md").write_text("# SCHEMA\n", encoding="utf-8", newline="\n")
        for rel, text in pages.items():
            path = root / rel
            if not path.resolve().is_relative_to(root.resolve()):
                raise ValueError(f"wiki の外のパス: {rel}")
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_text(text, encoding="utf-8", newline="\n")
    # 測るのは読むエージェントだけ。MCP とフックのない固定コピーで Read の経路を比べる。
    plugin = out / "plugin"
    (plugin / "agents").mkdir(parents=True, exist_ok=True)
    (plugin / ".claude-plugin").mkdir(parents=True, exist_ok=True)
    (plugin / "agents/wiki-reader.md").write_bytes(agent)
    (plugin / ".claude-plugin/plugin.json").write_bytes(b'{"name":"wiki","version":"0.0.0"}\n')
    files = {p.relative_to(out).as_posix(): digest(p.read_bytes())
             for directory in (out / "snapshot", plugin) for p in sorted(directory.rglob("*")) if p.is_file()}
    saved = {"spec": spec, "files": files,
             "fingerprint": digest(json.dumps({"spec": spec, "files": files}, sort_keys=True).encode("utf-8")),
             "initial_cli_version": subprocess.run(["claude", "--version"], capture_output=True, check=True,
                                                    encoding="utf-8", timeout=30).stdout.strip()}
    (out / "measurement-source.py").write_bytes(Path(__file__).read_bytes())
    (out / "measurement-questions.json").write_bytes(DATA.read_bytes())
    manifest.write_text(json.dumps(saved, ensure_ascii=False, indent=2) + "\n", encoding="utf-8", newline="\n")
    return saved


def roots(out: Path) -> dict[str, Path]:
    return {p.name: p / "wiki" for p in sorted((out / "snapshot").iterdir()) if (p / "wiki").is_dir()}


def scoped(rel: str) -> tuple[str, str]:
    return tuple(rel.split(":", 1)) if ":" in rel else ("project", rel)


def reader_prompt(question: dict, wiki_roots: dict[str, Path]) -> str:
    lines = [f"問い: {question['prompt']}"]
    for scope, root in wiki_roots.items():
        candidates = [scoped(rel)[1] for rel in question["candidates"] if scoped(rel)[0] == scope]
        if not candidates:
            continue
        lines.append(f'{scope} の wiki（root: {json.dumps(root.as_posix(), ensure_ascii=False)}）')
        for rel in candidates:
            lines.append(json.dumps({"slug": Path(rel).stem, "path": rel}, ensure_ascii=False))
    return "\n".join(lines)


def inline_prompt(question: dict, wiki_roots: dict[str, Path]) -> str:
    return (reader_prompt(question, wiki_roots) + "\n\n候補のページを自分で開いて読み、wiki に書かれていることだけで問いに答える。"
            "答えは「## 答え」「## 根拠」「## 開いたページ」に分け、根拠には開いたページの [[スラッグ]] と絶対パスを付ける。"
            "開いていない出典に触れる必要があれば「## 未確認の出典」に分け、根拠の節には置かない。")


def parse_events(stdout: bytes, wiki_roots: dict[str, Path]) -> dict:
    events = []
    for line in stdout.decode("utf-8", "replace").splitlines():
        try:
            event = json.loads(line)
            if isinstance(event, dict):
                events.append(event)
        except ValueError:
            pass
    calls, opened = {}, []
    result, model_used, cli_version, memory_paths = {}, None, None, {}
    for event in events:
        if event.get("type") == "system" and event.get("subtype") == "init":
            model_used = event.get("model")
            cli_version = event.get("claude_code_version")
            memory_paths = event.get("memory_paths", {})
        for block in event.get("message", {}).get("content", []) if isinstance(event.get("message", {}).get("content"), list) else []:
            if not isinstance(block, dict):
                continue
            if block.get("type") == "tool_use" and block.get("name") == "Read":
                target = block.get("input", {}).get("file_path")
                if isinstance(target, str):
                    path = Path(target)
                    if not path.is_absolute():
                        path = wiki_roots["project"].parent / path
                    for scope, root in wiki_roots.items():
                        if path.resolve().is_relative_to(root.resolve()):
                            calls[block.get("id")] = f"{scope}:{path.resolve().relative_to(root.resolve()).as_posix()}"
            if (block.get("type") == "tool_result" and block.get("tool_use_id") in calls
                    and not block.get("is_error") and block.get("content")):
                opened.append(calls[block["tool_use_id"]])
        if event.get("type") == "result":
            result = event
    return {"events": events, "opened": list(dict.fromkeys(opened)), "model_used": model_used,
            "result": result.get("result") or "", "cost_usd": result.get("total_cost_usd"),
            "duration_ms": result.get("duration_ms"), "is_error": result.get("is_error", True),
            "terminal_reason": result.get("terminal_reason"), "api_error": result.get("api_error"),
            "api_error_status": result.get("api_error_status"), "model_usage": result.get("modelUsage", {}),
            "cli_version": cli_version, "memory_paths": memory_paths}


def valid_observation(record: dict) -> bool:
    """通信・モデル・計量の失敗と、モデルの回答の形式の失敗を区別する。"""
    prefix = f"claude-{record['model']}-"
    usage = record.get("model_usage") or {}
    def number(value):
        return isinstance(value, (int, float)) and not isinstance(value, bool) and math.isfinite(value) and value >= 0
    return (record.get("exit") == 0 and not record.get("is_error", True)
            and str(record.get("model_used") or "").startswith(prefix) and bool(usage)
            and all(m.startswith(prefix) for m in usage)
            and number(record.get("cost_usd")) and number(record.get("duration_ms"))
            and (record.get("protocol") != 3 or not record.get("memory_paths", {}).get("auto")))


def quota_error(record: dict) -> bool:
    return (record.get("api_error_status") == 429 or record.get("api_error") == "usage_limit_reached"
            or "hit your" in record.get("result", "").lower() and "limit" in record.get("result", "").lower())


def run_once(question: dict, model: str, effort: str, run: int, out: Path, experiment: dict,
             retry_failed: bool = False, stop: threading.Event | None = None) -> Path | None:
    if stop is not None and stop.is_set():
        return None
    path = out / "runs" / f"{question['id']}__{model}-{effort}__{run}.json"
    if path.is_file():
        previous = json.loads(path.read_text(encoding="utf-8"))
        if previous.get("fingerprint") != experiment["fingerprint"]:
            raise ValueError(f"測定の条件が違う: {path}")
        if valid_observation(previous) or not retry_failed:
            if quota_error(previous) and stop is not None:
                stop.set()
            return path
        attempts = out / "attempts"
        attempts.mkdir(exist_ok=True)
        stamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%S%fZ")
        (attempts / f"{path.stem}__{stamp}.json").write_bytes(path.read_bytes())
    wiki_roots = roots(out)
    prompt = inline_prompt(question, wiki_roots) if effort == "inline" else reader_prompt(question, wiki_roots)
    actual_effort = "high" if effort == "inline" else effort
    if effort == "inline":
        argv = ["claude", "-p", prompt, "--model", model, "--effort", actual_effort]
    else:
        argv = ["claude", "-p", prompt, "--agent", "wiki:wiki-reader", "--model", model, "--effort", actual_effort]
    argv += ["--plugin-dir", str(out / "plugin"), "--output-format", "stream-json", "--verbose",
             "--tools", ",".join(TOOLS), "--allowedTools", ",".join(TOOLS), "--max-budget-usd", "2",
             "--permission-mode", "auto", "--no-session-persistence", "--setting-sources", "",
             "--strict-mcp-config", "--mcp-config", '{"mcpServers":{}}']
    argv += ["--settings", json.dumps(experiment["spec"].get("settings", {}))]
    for scope, root in wiki_roots.items():
        if scope != "project":
            argv += ["--add-dir", str(root)]
    env = dict(os.environ, **experiment["spec"].get("environment", {}))
    for key in ("CLAUDE_CODE_SUBAGENT_MODEL_FORCE", "CLAUDE_CODE_EFFORT_LEVEL"):
        if env.get(key):
            raise ValueError(f"測定を上書きする環境変数を解除する: {key}")
    try:
        proc = subprocess.run(argv, cwd=str(wiki_roots["project"].parent), capture_output=True, timeout=900, env=env,
                              creationflags=subprocess.CREATE_NO_WINDOW if os.name == "nt" else 0)
        observed = parse_events(proc.stdout, wiki_roots)
        observed.update({"exit": proc.returncode, "stderr": proc.stderr.decode("utf-8", "replace")})
    except (OSError, subprocess.TimeoutExpired) as exc:
        observed = {"exit": -1, "is_error": True, "result": "", "opened": [], "events": [],
                    "model_used": None, "cost_usd": None, "duration_ms": None, "error": str(exc)}
    record = {"protocol": PROTOCOL, "fingerprint": experiment["fingerprint"], "id": question["id"],
              "class": question["class"], "model": model, "effort": effort, "run": run,
              "requested_effort": actual_effort, "prompt_sha256": digest(prompt.encode("utf-8")),
              "argv": argv, **observed}
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes(json.dumps(record, ensure_ascii=False, indent=1).encode("utf-8"))
    if quota_error(record) and stop is not None:
        stop.set()
    return path

