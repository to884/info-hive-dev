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
import json
import random
import re
import sys
import threading
import unicodedata
from pathlib import Path

from reader_measurement_runtime import (ROOT, PLUGIN, DATA, COMBOS, INLINE, TOOLS, PROTOCOL, SCRIPTS,
    digest, verify_inputs, recorded_experiment, prepare, roots, scoped, reader_prompt, inline_prompt,
    parse_events, quota_error, run_once, valid_observation)

SLUG_RE = re.compile(r"\[\[([^\]|#]+)(?:#[^\]|]*)?(?:\|[^\]]*)?\]\]")


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


def citation_lines(text: str):
    """入れ子の箇条書きでは、親の行の所在も同じ引用の文脈に含める。隣の項目には引き継がない。"""
    parents = []
    heading = ""
    for line in text.splitlines():
        if not line.strip():
            continue
        if re.match(r"^#{1,6}\s", line):
            parents.clear()
            heading = line
        indent = len(line.expandtabs(4)) - len(line.expandtabs(4).lstrip())
        while parents and parents[-1][0] >= indent:
            parents.pop()
        context = "\n".join([heading, *(p[1] for p in parents), line])
        yield line, context
        if re.match(r"\s*(?:[-*+]|\d+[.)])\s", line):
            parents.append((indent, line))


def score(record: dict, question: dict, wiki_roots: dict[str, Path]) -> dict:
    scopes = {scoped(rel)[0] for rel in question["candidates"]}
    wiki_roots = {scope: root for scope, root in wiki_roots.items() if scope in scopes}
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
    for line, context in citation_lines(section(record["result"], "根拠")):
        for target in SLUG_RE.findall(line):
            target = unicodedata.normalize("NFC", target.strip().removesuffix(".md"))
            matches = list(dict.fromkeys(keys.get(target, [])))
            if len(matches) > 1:
                # 同名ページは、その行か親の箇条書きの絶対パスでスコープを決める。
                exact = []
                normalized_line = unicodedata.normalize("NFC", context.replace("\\", "/"))
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

    observation_ok = record.get("protocol") in (2, 3) and valid_observation(record)
    format_ok = bool(section(record["result"], "答え"))
    ok = observation_ok and format_ok
    return {"fact_rate": len(facts) / len(question["facts"]) if question["facts"] else 0.0,
            "matched_facts": facts, "unopened_citations": len(unopened), "unopened": sorted(unopened),
            "invalid_citations": sorted(invalid), "ambiguous_citations": sorted(ambiguous),
            "has_citations": bool(cited), "read_all_must": must <= opened, "model_matches": model_matches,
            "cost_usd": record["cost_usd"], "duration_ms": record["duration_ms"], "ok": ok,
            "observation_ok": observation_ok, "format_ok": format_ok}


def cmd_run(args) -> int:
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
    args.out = args.out.resolve()
    if getattr(args, "rescore", False):
        experiment, data = recorded_experiment(args.out)
    else:
        data = json.loads(DATA.read_bytes().decode("utf-8"))
        manifest = json.loads((args.out / "experiment.json").read_text(encoding="utf-8"))
        experiment = prepare(args.out, manifest["spec"]["runs"])
    questions = {q["id"]: q for q in data["questions"]}
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
                                                                 "invalid": 0, "ambiguous": 0, "uncited": 0, "format_fail": 0,
                                                                 "models": []})
        cell["n"] += 1
        cell["fact"] += s["fact_rate"]
        cell["unopened"] += s["unopened_citations"]
        cell["invalid"] += len(s["invalid_citations"])
        cell["ambiguous"] += len(s["ambiguous_citations"])
        cell["uncited"] += int(not s["has_citations"])
        cell["fail"] += 0 if s["observation_ok"] else 1
        cell["format_fail"] += 0 if s["format_ok"] else 1
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
                    and cell["must"] == 1.0 and cell["format_fail"] == 0]
        ordered = sorted(eligible, key=lambda name: (cells[name]["cost"], cells[name]["ms"], name))
        recommendations[cls] = {"status": "awaiting_semantic_review" if ordered else "no_eligible_combo",
                                "best_fact_token_rate": best, "eligible_by_cost": ordered}
    out = {"protocol": PROTOCOL, "fingerprint": experiment["fingerprint"], "table": table, "rows": rows,
           "grader_sha256": digest(Path(__file__).read_bytes()), "grading_question_scopes_only": True,
           "measurement_sha256": experiment["spec"].get("runtime_sha256", experiment["spec"].get("harness_sha256")),
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
    summary.add_argument("--rescore", action="store_true", help="測定時の入力と来歴を検証し、保存済みの回答を再採点する")
    args = parser.parse_args()
    if args.command == "run" and (args.runs < 1 or not 1 <= args.workers <= 4):
        parser.error("--runs は1以上、--workers は1〜4にする")
    code = cmd_run(args) if args.command == "run" else cmd_summary(args)
    raise SystemExit(code or 0)


if __name__ == "__main__":
    main()
