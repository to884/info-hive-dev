"""E7 の推定の確かめ: natural から無作為に選んだ 1,000 行を実際に埋め込み、区間ごとの推定と比べる。

wiki_reembed.py は長さの区間ごとに 48 件を測って全体を推定した。推定の式が実測と合うかを確かめる。
"""
from __future__ import annotations

import random
import subprocess
import sys
import time

from decision_common import DWORK, load, read_json, save, write_json
from common import limit_threads
from wiki_reembed import BUCKETS, bucket_of, prepare

ROWS = 1000


def worker(key, kind):
    limit_threads()
    from runtime_parity import Runtime
    data = prepare()
    rng = random.Random(20261107)
    chosen = rng.sample(range(len(data["natural"])), ROWS)
    texts = [data["natural"][i] for i in chosen]
    tokens = [data["natural_tokens"][i] for i in chosen]
    runtime = Runtime(key, kind)
    runtime.load()
    spec = runtime.spec
    list(runtime.model.passage_embed([spec["passage"] + t for t in texts[:8]], batch_size=16))
    started = time.perf_counter()
    list(runtime.model.passage_embed([spec["passage"] + t for t in texts], batch_size=16))
    return {"model": key, "runtime": kind, "rows": ROWS, "seconds": time.perf_counter() - started, "tokens": tokens}


def main():
    if len(sys.argv) > 1 and sys.argv[1] == "--worker":
        key, kind = sys.argv[2].split(":")
        write_json(DWORK / f"reembed-check/{key}__{kind}.json", worker(key, kind))
        return
    estimates = {(r["model"], r["runtime"]): r for r in load("wiki-reembed.json")["results"] if r["status"] == "ok"}
    results = []
    for key, kind in (("R-130", "onnx-fp32"), ("E-s", "fastembed-fp16")):
        completed = subprocess.run([sys.executable, "-X", "utf8", __file__, "--worker", f"{key}:{kind}"], capture_output=True, text=True, encoding="utf-8")
        if completed.returncode:
            results.append({"model": key, "runtime": kind, "status": "failed", "error": completed.stderr[-1500:]})
            continue
        measured = read_json(DWORK / f"reembed-check/{key}__{kind}.json")
        buckets = estimates[(key, kind)]["buckets"]
        estimate = sum(buckets[bucket_of(n)]["seconds_per_text_batch16"] for n in measured["tokens"])
        results.append({"model": key, "runtime": kind, "rows": measured["rows"], "measured_seconds": measured["seconds"],
                        "estimated_seconds": estimate, "ratio_measured_to_estimate": measured["seconds"] / estimate, "status": "ok"})
        print(results[-1], flush=True)
    save("wiki-reembed-check.json", {"purpose": "E7 の区間ごとの推定を、無作為の 1,000 行の実測で確かめる", "results": results})


if __name__ == "__main__":
    main()
