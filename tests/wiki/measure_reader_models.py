#!/usr/bin/env python3
"""読む段（wiki:wiki-reader）のモデルとエフォートを比べる（ADR-0031 の段階 0 の (f)）。

使い方:
    python tests/wiki/measure_reader_models.py run --out <dir> [--runs 2] [--workers 4] [--only <組>]
    python tests/wiki/measure_reader_models.py summary --out <dir>

run は、fixtures/prompt_context/reader_questions.json の問いごとに、claude -p --agent wiki:wiki-reader を
組（モデル / エフォート）ごとに動かし、記録を <dir>/runs/ に 1 回 1 ファイルで書く。書いた回は飛ばすので、
止めても続きから動かせる。R0 の問いには、メイン（opus）が自分でページを開く回も足す（R0 の境目）。
summary は、記録を採点して、種類（R0〜R3）と組ごとの表を <dir>/summary.json に書く。

採点:
- 事実: 回答（「答え」と「根拠」の節）に、事実の字句が NFKC、小文字、空白の除去のあとで含まれる割合。
- 開いていない引用: 「根拠」の [[スラッグ]] のうち、その回の道具の呼び出しで開いていないページの数。
- 時間と費用: claude -p の結果の duration_ms と total_cost_usd。

費用がかかる手元の道具なので、CI では動かさない。
"""
from __future__ import annotations

import argparse
import concurrent.futures
import json
import os
import re
import subprocess
import sys
import unicodedata
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
PLUGIN = ROOT / "info-hive-wiki"
WIKI = ROOT / "wiki"
DATA = Path(__file__).resolve().parent / "fixtures" / "prompt_context" / "reader_questions.json"
COMBOS = [("haiku", "low"), ("haiku", "medium"), ("sonnet", "low"), ("sonnet", "medium"), ("opus", "high"),
          ("fable", "medium")]
INLINE = ("opus", "inline")   # R0 の境目: メインが自分で開く
TOOLS = ["Read", "Glob", "Grep", "mcp__plugin_wiki_wiki__get_page", "mcp__plugin_wiki_wiki__list_index",
         "mcp__plugin_wiki_wiki__graph"]
SLUG_RE = re.compile(r"\[\[([^\]|#]+)")


def reader_prompt(question: dict) -> str:
    lines = [f"問い: {question['prompt']}", f"wiki のルート: {WIKI.as_posix()}", "候補:"]
    for rel in question["candidates"]:
        lines.append(f"- [[{Path(rel).stem}]]  {rel}")
    return "\n".join(lines)


def inline_prompt(question: dict) -> str:
    return (reader_prompt(question) + "\n\n候補のページを自分で開いて読み、wiki に書かれていることだけで問いに答える。"
            "答えの根拠には [[スラッグ]] とパスを付ける。")


def run_once(question: dict, model: str, effort: str, run: int, out: Path) -> Path:
    path = out / "runs" / f"{question['id']}__{model}-{effort}__{run}.json"
    if path.is_file():
        return path
    if effort == "inline":
        argv = ["claude", "-p", inline_prompt(question), "--model", model]
    else:
        argv = ["claude", "-p", reader_prompt(question), "--agent", "wiki:wiki-reader", "--model", model,
                "--effort", effort]
    argv += ["--plugin-dir", str(PLUGIN), "--output-format", "stream-json", "--verbose",
             "--allowedTools", ",".join(TOOLS), "--max-budget-usd", "2"]
    env = dict(os.environ, INFO_HIVE_PROMPT_CONTEXT="0")  # 測る回にフックの候補を混ぜない
    proc = subprocess.run(argv, cwd=str(ROOT), capture_output=True, timeout=900, env=env)
    events = []
    for line in proc.stdout.decode("utf-8", "replace").splitlines():
        try:
            events.append(json.loads(line))
        except ValueError:
            pass
    opened, result, cost, duration, model_used = [], "", None, None, None
    for ev in events:
        if ev.get("type") == "system" and ev.get("subtype") == "init":
            model_used = ev.get("model")
        if ev.get("type") == "assistant":
            for block in ev.get("message", {}).get("content", []):
                if block.get("type") == "tool_use":
                    inp = block.get("input", {})
                    target = inp.get("file_path") or inp.get("page") or ""
                    if target:
                        opened.append(str(target))
        if ev.get("type") == "result":
            result = ev.get("result") or ""
            cost = ev.get("total_cost_usd")
            duration = ev.get("duration_ms")
    record = {"id": question["id"], "class": question["class"], "model": model, "effort": effort, "run": run,
              "model_used": model_used, "exit": proc.returncode, "opened": opened, "result": result,
              "cost_usd": cost, "duration_ms": duration}
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes(json.dumps(record, ensure_ascii=False, indent=1).encode("utf-8"))
    return path


def norm(text: str) -> str:
    return re.sub(r"\s+", "", unicodedata.normalize("NFKC", text).casefold())


def section(text: str, *names: str) -> str:
    """「## 答え」などの節の本文を返す。節がなければ全文を返す（インラインの回など）。"""
    parts = re.split(r"^##\s+", text, flags=re.MULTILINE)
    picked = [p for p in parts if any(p.startswith(n) for n in names)]
    return "\n".join(picked) if picked else text


def opened_slugs(record: dict) -> set[str]:
    slugs = set()
    for target in record["opened"]:
        name = Path(target.replace("\\", "/")).name
        slugs.add(unicodedata.normalize("NFC", name[:-3] if name.endswith(".md") else name))
    return slugs


def score(record: dict, question: dict) -> dict:
    answer = norm(section(record["result"], "答え", "根拠"))
    facts = [f for f in question["facts"] if norm(f) in answer]
    cited = {unicodedata.normalize("NFC", s.strip()) for s in SLUG_RE.findall(section(record["result"], "根拠"))}
    unopened = sorted(cited - opened_slugs(record))
    must = {Path(p).stem for p in question.get("must_read", [])}
    return {"fact_rate": len(facts) / len(question["facts"]) if question["facts"] else 0.0,
            "unopened_citations": len(unopened), "unopened": unopened,
            "read_all_must": must <= opened_slugs(record), "cost_usd": record["cost_usd"],
            "duration_ms": record["duration_ms"], "ok": record["exit"] == 0 and bool(record["result"])}


def cmd_run(args) -> None:
    data = json.loads(DATA.read_bytes().decode("utf-8"))
    jobs = []
    for question in data["questions"]:
        combos = list(COMBOS) + ([INLINE] if question["class"] == "R0" else [])
        for model, effort in combos:
            if args.only and f"{model}-{effort}" not in args.only:
                continue
            for run in range(1, args.runs + 1):
                jobs.append((question, model, effort, run))
    with concurrent.futures.ThreadPoolExecutor(max_workers=args.workers) as pool:
        futures = [pool.submit(run_once, q, m, e, r, args.out) for q, m, e, r in jobs]
        for done, future in enumerate(concurrent.futures.as_completed(futures), 1):
            try:
                print(f"[{done}/{len(jobs)}] {future.result().name}", flush=True)
            except Exception as exc:  # noqa: BLE001 - 1 回の失敗で全体を止めない
                print(f"[{done}/{len(jobs)}] 失敗: {exc!r}", flush=True)


def cmd_summary(args) -> None:
    data = json.loads(DATA.read_bytes().decode("utf-8"))
    questions = {q["id"]: q for q in data["questions"]}
    table: dict = {}
    rows = []
    for path in sorted((args.out / "runs").glob("*.json")):
        record = json.loads(path.read_bytes().decode("utf-8"))
        s = score(record, questions[record["id"]])
        rows.append({**{k: record[k] for k in ("id", "class", "model", "effort", "run", "model_used")}, **s})
        cell = table.setdefault(record["class"], {}).setdefault(f"{record['model']}-{record['effort']}",
                                                                {"n": 0, "fact": 0.0, "unopened": 0, "fail": 0,
                                                                 "must": 0, "cost": 0.0, "ms": 0})
        cell["n"] += 1
        cell["fact"] += s["fact_rate"]
        cell["unopened"] += s["unopened_citations"]
        cell["fail"] += 0 if s["ok"] else 1
        cell["must"] += 1 if s["read_all_must"] else 0
        cell["cost"] += s["cost_usd"] or 0.0
        cell["ms"] += s["duration_ms"] or 0
    for cls in table.values():
        for cell in cls.values():
            n = cell["n"] or 1
            cell["fact"] = round(cell["fact"] / n, 3)
            cell["must"] = round(cell["must"] / n, 3)
            cell["cost"] = round(cell["cost"] / n, 4)
            cell["ms"] = round(cell["ms"] / n)
    out = {"table": table, "rows": rows}
    (args.out / "summary.json").write_bytes(json.dumps(out, ensure_ascii=False, indent=1).encode("utf-8"))
    print(json.dumps(table, ensure_ascii=False, indent=1))


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
    summary = sub.add_parser("summary")
    summary.add_argument("--out", type=Path, required=True)
    args = parser.parse_args()
    cmd_run(args) if args.command == "run" else cmd_summary(args)


if __name__ == "__main__":
    main()
