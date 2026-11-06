"""E6: 常駐するサーバーのメモリを、規模 × 索引の開き方 × モデルの有無で測る。

統一の測定の 5.18 GB（rss）には、db_bench.py 自身が持つ全量のベクトル（約 1.5 GB）と厳密解の計算が含まれていた。
ここでは構成ごとに新しいプロセスを起動し、サーバーが実際に持つものだけを読み込んで測る。

- 規模: wiki（natural の 8,275 行）と全量（761,915 行）
- 索引: usearch を view（メモリ写像）で開く、usearch を読み込む、FAISS IVF_SQ8 を読み込む。語彙は Tantivy
- モデル: R-130 の ONNX fp32 を読み込み、クエリを埋め込む。あり の構成では最長 20 件の文書も埋め込み、最大値を取る
rss、private（Windows のコミット済み専用メモリ）、peak_wset（作業セットの最大）を記録する。
"""
from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

import numpy as np

from decision_common import DWORK, read_json, save, write_json
from common import WORK, Tokenizer, full_queries, limit_threads, load_natural
from full_common import TANTIVY_FULL, USEARCH_KEPT

MEM = DWORK / "memory"
SCALES = ["wiki", "full"]
INDEXES = ["usearch-view", "usearch-load", "faiss"]


def paths(scale):
    if scale == "wiki":
        return {"usearch": MEM / "natural.usearch", "faiss": MEM / "natural.faiss", "tantivy": DWORK / "natural-tantivy"}
    # E3 で選んだ構成（usearch M16/ea256、FAISS nlist=4096 を IVF に直接 id を付けて作ったもの）
    return {"usearch": DWORK / "db-knobs/usearch-M16-ea256.usearch", "faiss": DWORK / "db-knobs/faiss-ivfsq8-4096-direct.faiss",
            "tantivy": TANTIVY_FULL}


def prepare():
    MEM.mkdir(parents=True, exist_ok=True)
    vectors = np.load(WORK / "vectors/natural/R-130.npy").astype(np.float32)
    if not (MEM / "natural.usearch").exists():
        from usearch.index import Index
        index = Index(ndim=512, metric="cos", dtype="f16", connectivity=16, expansion_add=128)
        index.add(np.arange(len(vectors), dtype=np.uint64), vectors, threads=4)
        index.save(str(MEM / "natural.usearch"))
    if not (MEM / "natural.faiss").exists():
        import faiss
        lists = int(np.ceil(np.sqrt(len(vectors))))
        quantizer = faiss.IndexFlatIP(512)
        inner = faiss.IndexIVFScalarQuantizer(quantizer, 512, lists, faiss.ScalarQuantizer.QT_8bit, faiss.METRIC_INNER_PRODUCT)
        inner.train(vectors)
        wrapped = faiss.IndexIDMap2(inner)
        wrapped.add_with_ids(vectors, np.arange(len(vectors), dtype=np.int64))
        faiss.write_index(wrapped, str(MEM / "natural.faiss"))
    texts = read_json(DWORK / "reembed-texts.json")
    longest = sorted(texts["natural"], key=len, reverse=True)[:20]
    write_json(MEM / "longest.json", longest)


def snapshot():
    import psutil
    info = psutil.Process().memory_info()
    return {"rss": info.rss, "private": getattr(info, "private", None), "peak_wset": getattr(info, "peak_wset", None)}


def worker(scale, index_kind, with_model):
    limit_threads()
    stages = {"start": snapshot()}
    p = paths(scale)
    if scale == "wiki":
        _, queries = load_natural()
        qvecs = np.load(WORK / "vectors/natural/R-130.queries.npy")
    else:
        queries = full_queries()
        qvecs = np.load(WORK / "runtime-queries/R-130__onnx-fp32.npy")
    texts = [q["query"] for q in queries]
    runtime = None
    if with_model:
        from runtime_parity import Runtime
        runtime = Runtime("R-130", "onnx-fp32")
        runtime.load()
        stages["model_loaded"] = snapshot()
    if index_kind.startswith("usearch"):
        from usearch.index import Index
        index = Index.restore(str(p["usearch"]), view=index_kind == "usearch-view")
        index.expansion_search = 1024

        def dense(v):
            return index.search(np.asarray(v, dtype=np.float32), 200, threads=1).keys
    else:
        import faiss
        faiss.omp_set_num_threads(1)
        index = faiss.read_index(str(p["faiss"]))
        if hasattr(index, "index"):
            faiss.downcast_index(index.index).nprobe = 128
        else:
            index.nprobe = 384

        def dense(v):
            return index.search(np.asarray(v, dtype=np.float32)[None, :], 200)[1][0]
    stages["index_opened"] = snapshot()
    from lexical_bench import Tantivy
    lexical = Tantivy(p["tantivy"])
    lexical.open()
    stages["lexical_opened"] = snapshot()
    tokenize = Tokenizer()
    for i, text in enumerate(texts):
        vector = runtime.queries([text])[0] if runtime else qvecs[i]
        dense(vector)
        lexical.search(tokenize(text), 200)
    stages["after_queries"] = snapshot()
    if runtime:
        runtime.passages(json.loads((MEM / "longest.json").read_text(encoding="utf-8")))
        stages["after_longest_passages"] = snapshot()
    final = snapshot()
    return {"scale": scale, "index": index_kind, "model": with_model, "stages": stages,
            "peak_wset_bytes": final["peak_wset"], "private_bytes": final["private"], "rss_bytes": final["rss"]}


def main():
    if len(sys.argv) > 1 and sys.argv[1] == "--worker":
        scale, index_kind, model = sys.argv[2:5]
        write_json(MEM / f"{scale}__{index_kind}__{model}.json", worker(scale, index_kind, model == "model"))
        return
    prepare()
    results = []
    for scale in SCALES:
        for index_kind in INDEXES:
            for model in ("model", "none"):
                completed = subprocess.run([sys.executable, "-X", "utf8", __file__, "--worker", scale, index_kind, model],
                                           capture_output=True, text=True, encoding="utf-8")
                if completed.returncode:
                    results.append({"scale": scale, "index": index_kind, "model": model == "model", "status": "failed",
                                    "error": completed.stderr[-1500:]})
                    print(scale, index_kind, model, "失敗", completed.stderr[-500:], flush=True)
                    continue
                result = read_json(MEM / f"{scale}__{index_kind}__{model}.json")
                results.append({**result, "status": "ok"})
                print(scale, index_kind, model, round(result["private_bytes"] / 2 ** 30, 2), "GiB private",
                      round(result["peak_wset_bytes"] / 2 ** 30, 2), "GiB peak", flush=True)
    gib = 2 ** 30
    limits = {"wiki": 1.0 * gib, "full": 2.5 * gib}
    verdict = {}
    for scale in SCALES:
        for index_kind in INDEXES:
            row = next((r for r in results if r["scale"] == scale and r["index"] == index_kind and r["model"] and r["status"] == "ok"), None)
            if row:
                verdict[f"{scale}/{index_kind}"] = {"private_gib": row["private_bytes"] / gib, "peak_wset_gib": row["peak_wset_bytes"] / gib,
                                                    "within_limit": row["private_bytes"] <= limits[scale]}
    save("server-memory.json", {"purpose": "常駐するサーバーのメモリ（規模 × 索引の開き方 × モデルの有無）",
                                "limits_private_gib": {k: v / gib for k, v in limits.items()}, "results": results, "verdict": verdict,
                                "criterion": "モデルありで、wiki 規模の private ≤ 1.0 GiB、全量 ≤ 2.5 GiB（提案値）"})


if __name__ == "__main__":
    main()
