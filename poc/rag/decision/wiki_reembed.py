"""E7: wiki 規模の再埋め込みの時間を、CPU 4 スレッドで測る。

統一レポートの §12 は「数千セクションで CPU 数分〜十数分」と見積もっただけだった。runtime-parity.json の
R-130 ONNX fp32 は 1.33 件/秒（最長 20 件を含む 300 チャンク）で、そのまま割ると 8,275 件で約 1.7 時間になる。

- 長さの分布: natural の 8,275 行（rag のチャンク、800 字）と、wiki の Markdown のセクション
  （wiki の en/ja の評価コーパスと ~/info-hive/W0_Wiki）を、R-130 のトークナイザで数える。
- 区間ごとの速度: トークン数の区間（≤256、≤512、≤1024、≤2048、≤4096、>4096）から最大 48 件を選び、
  実行系 × バッチ（16、64）で 1 件あたりの秒を測る。分布に掛けて全体の時間を推定する。
- 全量の実測: 推定が 45 分以内なら、R-130 で natural の 8,275 行を実際に埋め込む。
- 1 ページの更新: wiki のページのセクション数の中央値ぶんを埋め込み、クエリを 1 つ埋め込む時間。
"""
from __future__ import annotations

import argparse
import json
import os
import random
import subprocess
import sys
import time
from pathlib import Path

import numpy as np

from decision_common import DWORK, HERE, R130_ONNX, WIKI_EVAL, WIKI_SCRIPTS, read_json, save, write_json
from common import load_natural, limit_threads

RUNTIMES = [("R-130", "onnx-fp32"), ("R-30", "onnx-fp32"), ("E-s", "fastembed-fp16")]
BATCHES = [16, 64]
BUCKETS = [256, 512, 1024, 2048, 4096, 10 ** 9]
PER_BUCKET = 48
FULL_RUN_LIMIT_SECONDS = 45 * 60


def wiki_sections():
    sys.path.insert(0, str(WIKI_SCRIPTS))
    import wiki_search as ws
    roots = [WIKI_EVAL / "corpus/wiki", WIKI_EVAL / "ja/corpus/wiki", Path.home() / "info-hive/W0_Wiki"]
    texts, per_page = [], []
    for root in roots:
        if not root.exists():
            continue
        pages = ws.collect_pages(root)
        sections = ws.collect_sections(pages)
        texts.extend(s["searchable_text"] for s in sections)
        counts = {}
        for s in sections:
            counts[s["page"]["rel_path"]] = counts.get(s["page"]["rel_path"], 0) + 1
        per_page.extend(counts.values())
    return texts, per_page


def token_counter():
    from tokenizers import Tokenizer
    tokenizer = Tokenizer.from_file(str(R130_ONNX / "tokenizer.json"))
    tokenizer.no_truncation()
    return lambda text: len(tokenizer.encode(text).ids)


def bucket_of(tokens):
    return next(i for i, upper in enumerate(BUCKETS) if tokens <= upper)


def prepare():
    target = DWORK / "reembed-texts.json"
    if target.exists():
        return read_json(target)
    count = token_counter()
    rows, _ = load_natural()
    natural = [r["embedding_text"] for r in rows]
    wiki, per_page = wiki_sections()
    natural_tokens = [count(t) for t in natural]
    wiki_tokens = [count(t) for t in wiki]
    rng = random.Random(20261106)
    samples = []
    for b in range(len(BUCKETS)):
        pool = [i for i, n in enumerate(natural_tokens) if bucket_of(n) == b]
        rng.shuffle(pool)
        samples.append([natural[i] for i in pool[:PER_BUCKET]])
    value = {"natural": natural, "natural_tokens": natural_tokens, "wiki_tokens": wiki_tokens, "wiki_sections": wiki,
             "sections_per_page": per_page, "samples": samples}
    write_json(target, value)
    return value


def worker(key, kind, full_run):
    limit_threads()
    from runtime_parity import Runtime
    data = prepare()
    runtime = Runtime(key, kind)
    started = time.perf_counter()
    runtime.load()
    load_seconds = time.perf_counter() - started
    spec = runtime.spec

    def embed(texts, batch):
        if runtime.wiki or kind.startswith("onnx"):
            return list(runtime.model.passage_embed([spec["passage"] + t for t in texts], batch_size=batch))
        raise RuntimeError(kind)

    embed(data["samples"][0][:4], 16)
    buckets = []
    for b, texts in enumerate(data["samples"]):
        row = {"upper_tokens": BUCKETS[b], "samples": len(texts)}
        for batch in BATCHES:
            if not texts:
                continue
            t = time.perf_counter()
            embed(texts, batch)
            row[f"seconds_per_text_batch{batch}"] = (time.perf_counter() - t) / len(texts)
        buckets.append(row)

    def estimate(tokens, batch):
        counts = [0] * len(BUCKETS)
        for n in tokens:
            counts[bucket_of(n)] += 1
        return sum(c * buckets[b].get(f"seconds_per_text_batch{batch}", 0) for b, c in enumerate(counts))

    best_batch = min(BATCHES, key=lambda batch: estimate(data["natural_tokens"], batch))
    result = {"model": key, "runtime": kind, "load_seconds": load_seconds, "buckets": buckets, "best_batch": best_batch,
              "estimate_natural_seconds": {str(b): estimate(data["natural_tokens"], b) for b in BATCHES},
              "estimate_wiki_sections_seconds": {str(b): estimate(data["wiki_tokens"], b) for b in BATCHES}}
    # 1 ページの更新: セクション数の中央値ぶんの wiki のセクション + クエリ 1 つ。
    median_sections = int(np.median(data["sections_per_page"])) or 1
    page_texts = data["wiki_sections"][:median_sections]
    t = time.perf_counter()
    embed(page_texts, best_batch)
    next(runtime.model.query_embed(spec["query"] + "消費税の軽減税率"))
    result["page_update"] = {"sections": median_sections, "seconds": time.perf_counter() - t}
    if full_run and result["estimate_natural_seconds"][str(best_batch)] <= FULL_RUN_LIMIT_SECONDS:
        t = time.perf_counter()
        embed(data["natural"], best_batch)
        result["full_natural_seconds"] = time.perf_counter() - t
        result["full_natural_rows"] = len(data["natural"])
    import psutil
    result["peak_wset_bytes"] = getattr(psutil.Process().memory_info(), "peak_wset", None)
    return result


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--worker")
    parser.add_argument("--full-run", action="store_true")
    args = parser.parse_args()
    if args.worker:
        key, kind = args.worker.split(":")
        write_json(DWORK / f"reembed/{key}__{kind}.json", worker(key, kind, args.full_run))
        return
    data = prepare()
    results = []
    for key, kind in RUNTIMES:
        command = [sys.executable, "-X", "utf8", __file__, "--worker", f"{key}:{kind}"]
        if key == "R-130":
            command.append("--full-run")
        completed = subprocess.run(command, capture_output=True, text=True, encoding="utf-8", env=os.environ)
        if completed.returncode:
            results.append({"model": key, "runtime": kind, "status": "failed", "error": completed.stderr[-2000:]})
            print(key, kind, "失敗", completed.stderr[-800:], flush=True)
            continue
        result = read_json(DWORK / f"reembed/{key}__{kind}.json")
        results.append({**result, "status": "ok"})
        print(key, kind, result["estimate_natural_seconds"], result.get("full_natural_seconds"), flush=True)
    distribution = {}
    for name in ("natural_tokens", "wiki_tokens"):
        tokens = data[name]
        counts = [0] * len(BUCKETS)
        for n in tokens:
            counts[bucket_of(n)] += 1
        distribution[name] = {"count": len(tokens), "p50": float(np.percentile(tokens, 50)), "p95": float(np.percentile(tokens, 95)),
                              "max": int(max(tokens)), "buckets": dict(zip(map(str, BUCKETS), counts))}
    r130 = next((r for r in results if r["model"] == "R-130" and r["status"] == "ok"), None)
    initial = r130.get("full_natural_seconds", r130["estimate_natural_seconds"][str(r130["best_batch"])]) if r130 else None
    save("wiki-reembed.json", {
        "purpose": "wiki 規模（8,275 セクション）の再埋め込みの時間と、1 ページの更新の時間",
        "distribution": distribution, "sections_per_page_median": float(np.median(data["sections_per_page"])),
        "results": results, "r130_initial_seconds": initial,
        "r130_page_update_seconds": r130["page_update"]["seconds"] if r130 else None,
        "criterion": "初回 8,275 セクション ≤ 20 分、1 ページの更新 ≤ 5 秒（CPU 4 スレッド）",
        "passed": bool(r130 and initial <= 20 * 60 and r130["page_update"]["seconds"] <= 5)})


if __name__ == "__main__":
    main()
