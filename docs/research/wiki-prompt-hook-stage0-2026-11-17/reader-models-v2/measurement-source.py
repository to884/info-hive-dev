#!/usr/bin/env python3
"""読む段（wiki:wiki-reader）のモデルとエフォートを比べる（ADR-0032 の段階 0 の (f)）。

使い方:
    python tests/wiki/measure_reader_models.py run --out <新しいdir> [--runs 2] [--workers 4] [--only <組>]
    python tests/wiki/measure_reader_models.py run --out <同じdir> --retry-failed
    python tests/wiki/measure_reader_models.py summary --out <dir>

run は、fixtures/prompt_context/reader_questions.json の問いごとに、claude -p --agent wiki:wiki-reader を
組（モデル / エフォート）ごとに動かし、記録と生の出来事を <dir>/runs/ に書く。wiki とエージェントを固定し、
条件のハッシュを確かめて再開する。失敗は --retry-failed で履歴を残して再試行し、利用上限ではバッチを止める。
R0 には、メイン（opus/high）が自分でページを開く回も足す。測定は MCP なしの Read の経路で行う。
summary は、種類（R0〜R3）と組ごとの表を <dir>/summary.json に書く。旧形式の記録とは混ぜない。

採点:
- 事実の字句: 回答の「答え」「根拠」に事実の字句が現れ、根拠のページの読み取りに成功した割合。
- 引用: 未読、存在しないリンク、スコープが曖昧なリンクを分ける。呼び出しただけの Read は読んだと数えない。
- 時間と費用: claude -p の結果の duration_ms と total_cost_usd。
- 全組の測定がそろい、必読ページ、引用、字句の基準を満たす組を費用順に並べる。字句の一致は意味の正しさの
  証明ではないため、回答と根拠の読み合わせが済むまでモデル表は確定しない。

費用がかかる手元の道具なので、CI では動かさない。
"""
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
SLUG_RE = re.compile(r"\[\[([^\]|#]+)(?:#[^\]|]*)?(?:\|[^\]]*)?\]\]")
PROTOCOL = 2
SCRIPTS = PLUGIN / "skills/info-hive/scripts"


def digest(value: bytes) -> str:
    return hashlib.sha256(value).hexdigest()


def prepare(out: Path, runs: int) -> dict:
    """固定した wiki と読むエージェントを保存し、再開時も入力が変わっていないことを確かめる。"""
    from eval_prompt_context import materialize

    data = json.loads(DATA.read_text(encoding="utf-8"))
    agent = (PLUGIN / "agents/wiki-reader.md").read_bytes()
    spec = {"protocol": PROTOCOL, "wiki_commit": data["wiki_commit"], "data_sha256": digest(DATA.read_bytes()),
            "agent_sha256": digest(agent), "harness_sha256": digest(Path(__file__).read_bytes()),
            "page_rules_sha256": digest((SCRIPTS / "wiki_pages.py").read_bytes()),
            "runs": runs, "combos": [list(c) for c in COMBOS], "tools": TOOLS,
            "inline_effort": "high", "seed": 32,
            "cli_version": subprocess.run(["claude", "--version"], capture_output=True, check=True,
                                           encoding="utf-8", timeout=30).stdout.strip()}
    manifest = out / "experiment.json"
    if manifest.exists():
        saved = json.loads(manifest.read_text(encoding="utf-8"))
        if saved["spec"] != spec:
            raise ValueError("測定の条件が変わった。別の --out を使う")
        actual = {p.relative_to(out).as_posix() for directory in (out / "snapshot", out / "plugin")
                  for p in directory.rglob("*") if p.is_file()}
        if actual != set(saved["files"]):
            raise ValueError("固定した入力のファイル一覧が変わった")
        for rel, expected in saved["files"].items():
            if digest((out / rel).read_bytes()) != expected:
                raise ValueError(f"固定した入力が変わった: {rel}")
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
             "fingerprint": digest(json.dumps({"spec": spec, "files": files}, sort_keys=True).encode("utf-8"))}
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
            "答えは「## 答え」「## 根拠」「## 開いたページ」に分け、根拠には [[スラッグ]] とパスを付ける。")


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
    result, model_used = {}, None
    for event in events:
        if event.get("type") == "system" and event.get("subtype") == "init":
            model_used = event.get("model")
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
            "api_error_status": result.get("api_error_status"), "model_usage": result.get("modelUsage", {})}


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
        if previous.get("exit") == 0 and not previous.get("is_error") or not retry_failed:
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
    for scope, root in wiki_roots.items():
        if scope != "project":
            argv += ["--add-dir", str(root)]
    env = dict(os.environ, INFO_HIVE_PROMPT_CONTEXT="0")  # 測る回にフックの候補を混ぜない
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


def norm(text: str) -> str:
    return re.sub(r"\s+", "", unicodedata.normalize("NFKC", text).casefold())


def section(text: str, *names: str) -> str:
    """指定の節だけを返す。ないときに全文や候補一覧を採点しない。"""
    parts = re.split(r"^##\s+", text, flags=re.MULTILINE)
    picked = [p.partition("\n")[2] for p in parts[1:] if p.partition("\n")[0].strip() in names]
    return "\n".join(picked)


def page_keys(wiki_roots: dict[str, Path]) -> dict[str, list[str]]:
    sys.path.insert(0, str(SCRIPTS))
    import wiki_pages

    keys = {}
    for scope, root in wiki_roots.items():
        for file in wiki_pages.walk_pages(root).files:
            rel = unicodedata.normalize("NFC", file.rel)
            key = f"{scope}:{rel}"
            for target in (Path(rel).stem, rel[:-3]):
                keys.setdefault(target, []).append(key)
    return keys


def score(record: dict, question: dict, wiki_roots: dict[str, Path]) -> dict:
    answer = norm(section(record["result"], "答え", "根拠"))
    opened = {unicodedata.normalize("NFC", p) for p in record["opened"]}
    facts = []
    for fact in question["facts"]:
        source = question["fact_sources"][fact].partition(" L")[0]
        scope, rel = scoped(source)
        if norm(fact) in answer and unicodedata.normalize("NFC", f"{scope}:{rel}") in opened:
            facts.append(fact)
    keys = page_keys(wiki_roots)
    unopened, invalid, ambiguous, cited = set(), set(), set(), set()
    for line in section(record["result"], "根拠").splitlines():
        for target in SLUG_RE.findall(line):
            target = unicodedata.normalize("NFC", target.strip().removesuffix(".md"))
            matches = list(dict.fromkeys(keys.get(target, [])))
            if len(matches) > 1:
                # 同名ページは、その行に書かれた絶対パスでしかスコープを決めない。
                exact = []
                normalized_line = unicodedata.normalize("NFC", line.replace("\\", "/"))
                for key in matches:
                    scope, rel = scoped(key)
                    absolute = unicodedata.normalize("NFC", (wiki_roots[scope] / rel).as_posix())
                    if absolute in normalized_line:
                        exact.append(key)
                matches = exact
                if len(matches) != 1:
                    ambiguous.add(target)
                    continue
            if not matches:
                invalid.add(target)
            else:
                cited.add(matches[0])
                if matches[0] not in opened:
                    unopened.add(matches[0])
    must = {unicodedata.normalize("NFC", ":".join(scoped(p))) for p in question.get("must_read", [])}
    model_prefix = f"claude-{record['model']}-"
    model_matches = (str(record.get("model_used") or "").startswith(model_prefix)
                     and bool(record.get("model_usage"))
                     and all(m.startswith(model_prefix) for m in record["model_usage"]))
    def valid_number(value):
        return isinstance(value, (int, float)) and not isinstance(value, bool) and math.isfinite(value) and value >= 0

    ok = (record.get("protocol") == PROTOCOL and record["exit"] == 0 and not record.get("is_error", True)
          and bool(section(record["result"], "答え")) and model_matches
          and valid_number(record.get("cost_usd")) and valid_number(record.get("duration_ms")))
    return {"fact_rate": len(facts) / len(question["facts"]) if question["facts"] else 0.0,
            "matched_facts": facts, "unopened_citations": len(unopened), "unopened": sorted(unopened),
            "invalid_citations": sorted(invalid), "ambiguous_citations": sorted(ambiguous),
            "has_citations": bool(cited), "read_all_must": must <= opened, "model_matches": model_matches,
            "cost_usd": record["cost_usd"], "duration_ms": record["duration_ms"], "ok": ok}


def cmd_run(args) -> None:
    data = json.loads(DATA.read_bytes().decode("utf-8"))
    args.out = args.out.resolve()
    experiment = prepare(args.out, args.runs)
    jobs = []
    for question in data["questions"]:
        if args.question and question["id"] not in args.question:
            continue
        combos = list(COMBOS) + ([INLINE] if question["class"] == "R0" else [])
        for model, effort in combos:
            if args.only and f"{model}-{effort}" not in args.only:
                continue
            for run in range(1, args.runs + 1):
                jobs.append((question, model, effort, run))
    random.Random(experiment["spec"]["seed"]).shuffle(jobs)
    if not jobs:
        raise ValueError("測る組がない")
    stop = threading.Event()
    first = run_once(*jobs[0], args.out, experiment, args.retry_failed, stop)
    print(f"[1/{len(jobs)}] {first.name}", flush=True)
    if stop.is_set():
        print("利用上限のため中断した。解除後に --retry-failed で続行する。", file=sys.stderr)
        return 3
    with concurrent.futures.ThreadPoolExecutor(max_workers=args.workers) as pool:
        futures = [pool.submit(run_once, q, m, e, r, args.out, experiment, args.retry_failed, stop)
                   for q, m, e, r in jobs[1:]]
        for done, future in enumerate(concurrent.futures.as_completed(futures), 2):
            try:
                result = future.result()
                if result is not None:
                    print(f"[{done}/{len(jobs)}] {result.name}", flush=True)
            except Exception as exc:  # noqa: BLE001 - 1 回の失敗で全体を止めない
                print(f"[{done}/{len(jobs)}] 失敗: {exc!r}", flush=True)
    return 3 if stop.is_set() else 0


def cmd_summary(args) -> None:
    data = json.loads(DATA.read_bytes().decode("utf-8"))
    questions = {q["id"]: q for q in data["questions"]}
    args.out = args.out.resolve()
    manifest = json.loads((args.out / "experiment.json").read_text(encoding="utf-8"))
    experiment = prepare(args.out, manifest["spec"]["runs"])
    wiki_roots = roots(args.out)
    table: dict = {}
    rows = []
    seen = set()
    for path in sorted((args.out / "runs").glob("*.json")):
        record = json.loads(path.read_bytes().decode("utf-8"))
        if record.get("fingerprint") != experiment["fingerprint"]:
            raise ValueError(f"測定の条件が違う: {path}")
        key = (record["id"], record["model"], record["effort"], record["run"])
        if (key in seen or record["id"] not in questions or not 1 <= record["run"] <= experiment["spec"]["runs"]
                or record["class"] != questions[record["id"]]["class"]
                or (record["model"], record["effort"]) not in COMBOS + ([INLINE] if record["class"] == "R0" else [])):
            raise ValueError(f"重複か、計画にない測定: {path}")
        seen.add(key)
        s = score(record, questions[record["id"]], wiki_roots)
        rows.append({**{k: record[k] for k in ("id", "class", "model", "effort", "run", "model_used")}, **s})
        cell = table.setdefault(record["class"], {}).setdefault(f"{record['model']}-{record['effort']}",
                                                                {"n": 0, "fact": 0.0, "unopened": 0, "fail": 0,
                                                                 "must": 0, "cost": 0.0, "ms": 0,
                                                                 "invalid": 0, "ambiguous": 0, "uncited": 0,
                                                                 "models": []})
        cell["n"] += 1
        cell["fact"] += s["fact_rate"]
        cell["unopened"] += s["unopened_citations"]
        cell["invalid"] += len(s["invalid_citations"])
        cell["ambiguous"] += len(s["ambiguous_citations"])
        cell["uncited"] += int(not s["has_citations"])
        cell["fail"] += 0 if s["ok"] else 1
        cell["must"] += 1 if s["read_all_must"] else 0
        cell["cost"] += s["cost_usd"] or 0.0
        cell["ms"] += s["duration_ms"] or 0
        if record["model_used"] not in cell["models"]:
            cell["models"].append(record["model_used"])
    for cls in table.values():
        for cell in cls.values():
            n = cell["n"] or 1
            cell["fact"] /= n
            cell["must"] /= n
            cell["cost"] /= n
            cell["ms"] = round(cell["ms"] / n)
    recommendations = {}
    for cls in sorted({q["class"] for q in questions.values()}):
        combinations = list(COMBOS) + ([INLINE] if cls == "R0" else [])
        expected = sum(q["class"] == cls for q in questions.values()) * experiment["spec"]["runs"]
        cells = table.get(cls, {})
        complete = all(cells.get(f"{m}-{e}", {}).get("n") == expected
                       and cells[f"{m}-{e}"]["fail"] == 0
                       and len(cells[f"{m}-{e}"]["models"]) == 1 for m, e in combinations)
        if not complete:
            recommendations[cls] = {"status": "incomplete", "expected_per_combo": expected}
            continue
        best = max(c["fact"] for c in cells.values())
        eligible = [name for name, cell in cells.items() if best > 0 and cell["fact"] >= .95 * best
                    and cell["unopened"] == cell["invalid"] == cell["ambiguous"] == cell["uncited"] == 0
                    and cell["must"] == 1.0]
        ordered = sorted(eligible, key=lambda name: (cells[name]["cost"], cells[name]["ms"], name))
        recommendations[cls] = {"status": "awaiting_semantic_review" if ordered else "no_eligible_combo",
                                "best_fact_token_rate": best, "eligible_by_cost": ordered}
    out = {"protocol": PROTOCOL, "fingerprint": experiment["fingerprint"], "table": table, "rows": rows,
           "recommendations": recommendations,
           "note": "事実の字句と読む成功の照合は意味の正しさの判定ではない。採用前に回答と根拠を読んで確かめる。"}
    (args.out / "summary.json").write_bytes(json.dumps(out, ensure_ascii=False, indent=1).encode("utf-8"))
    print(json.dumps({"table": table, "recommendations": recommendations}, ensure_ascii=False, indent=1))


def main() -> None:
    for stream in (sys.stdout, sys.stderr):
        stream.reconfigure(encoding="utf-8")
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    sub = parser.add_subparsers(dest="command", required=True)
    run = sub.add_parser("run")
    run.add_argument("--out", type=Path, required=True)
    run.add_argument("--runs", type=int, default=2)
    run.add_argument("--workers", type=int, default=4)
    run.add_argument("--only", action="append", help="モデル-エフォート（例: haiku-low）。複数指定できる")
    run.add_argument("--question", action="append", help="問いの id。複数指定できる")
    run.add_argument("--retry-failed", action="store_true", help="失敗した回を履歴に保存して再測定する")
    summary = sub.add_parser("summary")
    summary.add_argument("--out", type=Path, required=True)
    args = parser.parse_args()
    if args.command == "run" and (args.runs < 1 or not 1 <= args.workers <= 4):
        parser.error("--runs は1以上、--workers は1〜4にする")
    code = cmd_run(args) if args.command == "run" else cmd_summary(args)
    raise SystemExit(code or 0)


if __name__ == "__main__":
    main()
