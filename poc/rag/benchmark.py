"""同じチャンクとベクトルで LanceDB と Qdrant サーバーを比較する。"""
from __future__ import annotations

import argparse
import collections
import contextlib
import hashlib
import json
import math
import os
import socket
import subprocess
import sys
import threading
import time
import urllib.request
from pathlib import Path

import numpy as np
import psutil
import torch
import yaml
from sentence_transformers import SentenceTransformer, CrossEncoder

ROOT = Path(__file__).resolve().parents[2]
WORK = (Path(os.environ["LOCALAPPDATA"]) / "info-hive/rag-poc/2026-11-04").resolve()
OUT = ROOT / "docs/research/rag-poc-2026-11-04"
MODEL_REVISIONS = {
    "cl-nagoya/ruri-v3-30m": "24899e5de370b56d179604a007c0d727bf144504",
    "cl-nagoya/ruri-v3-70m": "07a8b0aba47d29d2ca21f89b915c1efe2c23d1cc",
    "cl-nagoya/ruri-v3-130m": "e3114c6ee10dbab8b4b235fbc6dcf9dd4d5ac1a6",
    "hotchpotch/japanese-reranker-xsmall-v2": "de99fd2f16c7b5df1df1bcc1d9ad2c16d88ce93a",
    "hotchpotch/japanese-reranker-tiny-v2": "ba95175a4d53058816b971f31929f10c5cad8560",
}


def quantile(values, q):
    return float(np.quantile(values, q))


def size(path):
    return sum(file.stat().st_size for file in path.rglob("*") if file.is_file())


def revision(model):
    return MODEL_REVISIONS[model]


def tokens(text, tokenizer):
    import unicodedata
    from sudachipy import tokenizer as kinds
    return [word.normalized_form().lower() for word in tokenizer.tokenize(unicodedata.normalize("NFKC", text).lower(), kinds.Tokenizer.SplitMode.C)
            if word.surface().strip() and word.part_of_speech()[0] not in {"補助記号", "記号"}]


@contextlib.contextmanager
def qdrant_process(folder):
    # この PoC 専用の loopback ポートを使い、終了時に起動したプロセスだけを止める。
    with socket.socket() as listener:
        listener.bind(("127.0.0.1", 0))
        port = listener.getsockname()[1]
    folder.mkdir(parents=True, exist_ok=True)
    config = {"storage": {"storage_path": str(folder / "storage")}, "service": {"host": "127.0.0.1", "http_port": port, "grpc_port": None}, "telemetry_disabled": True}
    (folder / "config.yaml").write_text(yaml.safe_dump(config), encoding="utf-8")
    flags = subprocess.CREATE_NO_WINDOW if os.name == "nt" else 0
    with (folder / "server.log").open("w", encoding="utf-8") as log:
        process = subprocess.Popen([str(WORK / "qdrant-bin/qdrant.exe"), "--config-path", str(folder / "config.yaml")], cwd=folder,
                                   stdout=log, stderr=log, creationflags=flags)
        url = f"http://127.0.0.1:{port}"
        try:
            for _ in range(100):
                if process.poll() is not None:
                    raise RuntimeError((folder / "server.log").read_text(encoding="utf-8"))
                try:
                    with urllib.request.urlopen(url + "/readyz", timeout=.2):
                        break
                except Exception:
                    time.sleep(.1)
            else:
                raise TimeoutError("Qdrant の起動待ち")
            yield url, process
        finally:
            process.terminate()
            process.wait(timeout=15)


def rrf(a, b):
    scores = {}
    for ranking in (a, b):
        for rank, item in enumerate(ranking, 1):
            scores[item] = scores.get(item, 0) + 1 / (60 + rank)
    return sorted(scores, key=lambda item: (-scores[item], item))


def metrics(ranking, corpus, expected):
    # 同じページの複数チャンクが指標を水増ししないよう、文書ラベルでまとめる。
    labels = list(dict.fromkeys(corpus[index]["label"] for index in ranking))
    relevant = set(expected)
    recall = len(set(labels[:30]) & relevant) / len(relevant)
    dcg = sum((1 if label in relevant else 0) / math.log2(rank + 2) for rank, label in enumerate(labels[:10]))
    ideal = sum(1 / math.log2(rank + 2) for rank in range(min(10, len(relevant))))
    return recall, dcg / ideal


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--model", choices=["30m", "70m", "130m"], required=True)
    parser.add_argument("--vectors", default="")
    parser.add_argument("--reranker", choices=["fp32", "int8"], default="fp32")
    parser.add_argument("--reranker-size", choices=["xsmall", "tiny"], default="xsmall")
    parser.add_argument("--rerank-limit", type=int, choices=[8, 10, 20, 30], default=30)
    parser.add_argument("--tag", default="")
    args = parser.parse_args()
    model_id = f"cl-nagoya/ruri-v3-{args.model}"
    os.environ["HF_HUB_DISABLE_TELEMETRY"] = "1"
    torch.set_num_threads(4)
    torch.set_num_interop_threads(1)
    corpus_bytes = (WORK / "corpus.json").read_bytes()
    corpus_sha = hashlib.sha256(corpus_bytes).hexdigest()
    data = json.loads(corpus_bytes)
    corpus = data["corpus"]
    queries = [query for query in data["queries"] if query["expected"]]
    folder = ROOT / ".rag-poc-data" / f"bench-{args.model}-{time.time_ns()}"
    folder.mkdir(parents=True)
    peak = [0]
    stopped = threading.Event()
    phase = ["model_load"]
    def monitor():
        last = time.monotonic()
        while not stopped.wait(.05):
            peak[0] = max(peak[0], psutil.Process().memory_info().rss)
            if time.monotonic() - last >= 30:
                print(json.dumps({"phase":phase[0],"model":args.model,"peak_rss_bytes":peak[0]}),flush=True)
                last = time.monotonic()
    thread = threading.Thread(target=monitor, daemon=True)
    thread.start()
    pin = revision(model_id)
    started = time.perf_counter()
    model = SentenceTransformer(model_id, revision=pin, device="cpu", cache_folder=str(WORK / "models"), model_kwargs={"attn_implementation": "sdpa"})
    model.max_seq_length = 2048
    token_lengths = [len(row) for row in model.tokenizer(["検索文書: " + row["text"] for row in corpus], truncation=False, padding=False)["input_ids"]]
    truncated = sum(length > model.max_seq_length for length in token_lengths)
    if truncated:
        raise ValueError(f"入力上限を超えるチャンクが {truncated} 件あります。")
    model.encode(["検索文書: 日本語の検索"], show_progress_bar=False)
    load_seconds = time.perf_counter() - started
    if args.vectors:
        vectors_path = Path(args.vectors)
        vectors = np.load(vectors_path)
        previous = json.loads(vectors_path.with_name("embedding-meta.json").read_text(encoding="utf-8"))
        encode_seconds = previous["seconds"]
        assert previous["model"] == model_id and previous["revision"] == pin
        if "corpus_sha256" in previous: assert previous["corpus_sha256"] == corpus_sha
        assert vectors.shape[0] == len(corpus)
    else:
        phase[0] = "embedding"
        started = time.perf_counter()
        vectors = model.encode(["検索文書: " + row["text"] for row in corpus], normalize_embeddings=True, show_progress_bar=False, batch_size=8).astype(np.float32)
        encode_seconds = time.perf_counter() - started
    np.save(folder / "vectors.npy", vectors)
    (folder / "embedding-meta.json").write_text(json.dumps({"model":model_id,"revision":pin,"seconds":encode_seconds,"corpus_sha256":corpus_sha}),encoding="utf-8")
    print(json.dumps({"phase": "embedded", "model": args.model, "chunks": len(corpus), "seconds": encode_seconds}), flush=True)
    from sudachipy import dictionary
    tokenizer = dictionary.Dictionary().create()
    doc_tokens = [tokens(row["text"], tokenizer) for row in corpus]
    counters = [collections.Counter(items) for items in doc_tokens]
    vocabulary = {token: i for i, token in enumerate(sorted({token for items in doc_tokens for token in items}))}
    df = collections.Counter(token for counter in counters for token in counter)
    average = sum(map(len, doc_tokens)) / len(corpus)
    import lancedb
    import pyarrow as pa
    db = lancedb.connect(str(folder / "lance"))
    rows = [{"id": i, "label": row["label"], "terms": " ".join(doc_tokens[i]), "vector": vector.tolist()} for i, (row, vector) in enumerate(zip(corpus, vectors))]
    schema = pa.schema([("id", pa.int64()), ("label", pa.string()), ("terms", pa.string()), ("vector", pa.list_(pa.float32(), vectors.shape[1]))])
    started = time.perf_counter()
    table = db.create_table("chunks", data=pa.Table.from_pylist(rows, schema=schema))
    table.create_fts_index("terms", base_tokenizer="whitespace", stem=False, remove_stop_words=False, ascii_folding=False)
    lance_build = time.perf_counter() - started
    from qdrant_client import QdrantClient, models as qm
    outputs = {}
    reranker_id = f"hotchpotch/japanese-reranker-{args.reranker_size}-v2"
    reranker_pin = revision(reranker_id)
    if args.reranker == "int8":
        from int8_reranker import Int8Reranker
        reranker = Int8Reranker(WORK, reranker_id, reranker_pin)
    else:
        reranker = CrossEncoder(reranker_id, revision=reranker_pin, device="cpu", max_length=512, cache_folder=str(WORK / "models"), model_kwargs={"attn_implementation": "sdpa"})
    reranker.predict([("検索", "日本語の検索")], show_progress_bar=False)
    with qdrant_process(folder / "qdrant") as (url, process):
        client = QdrantClient(url=url, timeout=60)
        client.create_collection("chunks", vectors_config={"dense": qm.VectorParams(size=vectors.shape[1], distance=qm.Distance.COSINE)},
                                 sparse_vectors_config={"bm25": qm.SparseVectorParams()})
        points = []
        for i, vector in enumerate(vectors):
            pairs = sorted((vocabulary[token], count / (count + 1.2 * (.25 + .75 * len(doc_tokens[i]) / average))) for token, count in counters[i].items())
            points.append(qm.PointStruct(id=i, vector={"dense": vector.tolist(), "bm25": qm.SparseVector(indices=[a for a,b in pairs], values=[b for a,b in pairs])}, payload={"id": i}))
        started = time.perf_counter()
        client.upload_points("chunks", points, wait=True, batch_size=64)
        qdrant_build = time.perf_counter() - started
        for backend in ("lancedb", "qdrant"):
            phase[0] = "search_" + backend
            measurements = []
            query_vectors = []
            for query in queries:
                start = time.perf_counter()
                vector = model.encode(["検索クエリ: " + query["query"]], normalize_embeddings=True, show_progress_bar=False)[0]
                query_vectors.append(vector)
                encode_ms = (time.perf_counter() - start) * 1000
                qt = tokens(query["query"], tokenizer)
                start = time.perf_counter()
                if backend == "lancedb":
                    dense = [item["id"] for item in table.search(vector).distance_type("cosine").select(["id", "_distance"]).limit(200).to_list()]
                    lexical = [item["id"] for item in table.search(" ".join(qt), query_type="fts", fts_columns="terms").select(["id", "_score"]).limit(200).to_list()] if qt else []
                else:
                    dense = [item.id for item in client.query_points("chunks", query=vector.tolist(), using="dense", limit=200, with_payload=False).points]
                    pairs = sorted((vocabulary[token], math.log(1 + (len(corpus) - df[token] + .5) / (df[token] + .5))) for token in set(qt) if token in vocabulary)
                    lexical = [item.id for item in client.query_points("chunks", query=qm.SparseVector(indices=[a for a,b in pairs], values=[b for a,b in pairs]), using="bm25", limit=200, with_payload=False).points] if pairs else []
                fused = rrf(dense, lexical)
                seen = set()
                fused = [index for index in fused if not (corpus[index]["label"] in seen or seen.add(corpus[index]["label"]))]
                search_ms = (time.perf_counter() - start) * 1000
                recall, before_ndcg = metrics(fused, corpus, query["expected"])
                start = time.perf_counter()
                top = fused[:args.rerank_limit]
                scores = reranker.predict([(query["query"], corpus[index]["text"]) for index in top], show_progress_bar=False, batch_size=8)
                ranked = [index for _,index in sorted(zip(map(float, scores),top), reverse=True)]
                ranked += fused[args.rerank_limit:]
                rerank_ms = (time.perf_counter() - start) * 1000
                _, ndcg = metrics(ranked, corpus, query["expected"])
                measurements.append({"id": query["id"], "encode_ms": encode_ms, "search_ms": search_ms, "rerank_ms": rerank_ms,
                                     "total_ms": encode_ms + search_ms + rerank_ms, "recall30": recall, "ndcg10": ndcg, "before_ndcg10": before_ndcg})
                if len(measurements) % 20 == 0:
                    print(json.dumps({"phase":"progress","model":args.model,"backend":backend,"queries":len(measurements)}),flush=True)
            outputs[backend] = {"recall30": float(np.mean([m["recall30"] for m in measurements])), "ndcg10": float(np.mean([m["ndcg10"] for m in measurements])),
                                "p50_ms": quantile([m["total_ms"] for m in measurements], .5), "p95_ms": quantile([m["total_ms"] for m in measurements], .95),
                                "measurements": measurements}
            if backend == "lancedb":
                np.save(folder / "query-vectors.npy", np.asarray(query_vectors))
            print(json.dumps({"phase": "searched", "model": args.model, "backend": backend, "p95_ms": outputs[backend]["p95_ms"]}), flush=True)
        qdrant_rss = psutil.Process(process.pid).memory_info().rss
        client.close()
    stopped.set()
    thread.join()
    result = {"model": model_id, "revision": pin, "reranker": reranker_id, "reranker_revision": reranker_pin, "reranker_backend":args.reranker,"rerank_limit":args.rerank_limit,"corpus_sha256":corpus_sha,"cpu_threads":4,
              "max_sequence":2048,"query_count":len(queries),"chunks":len(corpus),"dimension":vectors.shape[1],
              "max_input_tokens":max(token_lengths),"truncated_chunks":truncated,
              "model_load_and_download_seconds":load_seconds,"embedding_seconds":encode_seconds,"chunks_per_second":len(corpus)/encode_seconds,
              "python_peak_rss_bytes":peak[0],"qdrant_final_rss_bytes":qdrant_rss,"lancedb_build_seconds":lance_build,"qdrant_build_seconds":qdrant_build,
              "lancedb_bytes":size(folder/'lance'),"qdrant_bytes":size(folder/'qdrant/storage'),"run_dir":str(folder),"backends":outputs,
              "dataset_version":data.get("dataset_version",1),"pdf_queries":data.get("pdf_queries",0),
              "notes":["固定 wiki 正解セットと、指定がある場合は実資料の暫定 QA を使用。実 PDF から 512 チャンクを妨害文書として追加。",
                       "LanceDB は native BM25、Qdrant は共通 Sudachi 語彙から計算した BM25 疎ベクトル。スコア式は完全同一ではない。",
                       "max_length=512 の CPU リランカーを含む。少数データの全件走査で、大規模 ANN の試験ではない。"]}
    OUT.mkdir(parents=True, exist_ok=True)
    suffix = "" if args.reranker == "fp32" else "-int8"
    if args.reranker_size != "xsmall": suffix += "-" + args.reranker_size
    if args.rerank_limit != 30: suffix += "-r" + str(args.rerank_limit)
    prefix = args.tag + "-" if args.tag else ""
    (OUT / f"benchmark-{prefix}{args.model}{suffix}.json").write_text(json.dumps(result, ensure_ascii=False, indent=2), encoding="utf-8")
    print(json.dumps({k:v for k,v in result.items() if k!='backends'}, ensure_ascii=False), flush=True)


if __name__ == "__main__":
    main()
