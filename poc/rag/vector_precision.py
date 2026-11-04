"""保存ベクトルの丸めだけによる順位変化を測る。ANN の量子化試験とは分ける。"""
import json
import math
import os
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parents[2]
OUT = ROOT / "docs/research/rag-poc-2026-11-04"
WORK = (Path(os.environ["LOCALAPPDATA"]) / "info-hive/rag-poc/2026-11-04").resolve()
data = json.loads((WORK / "corpus.json").read_text(encoding="utf-8"))
queries = [q for q in data["queries"] if q["expected"]]
corpus = data["corpus"]
outputs = []
seen_models = set()
for file in sorted(OUT.glob("benchmark-v2-*.json")):
    result = json.loads(file.read_text(encoding="utf-8"))
    if result["model"] in seen_models:
        continue
    seen_models.add(result["model"])
    folder = Path(result["run_dir"])
    original = np.load(folder / "vectors.npy")
    query_vectors = np.load(folder / "query-vectors.npy")
    scales = np.maximum(np.max(np.abs(original), axis=1, keepdims=True) / 127, 1e-12)
    quantized = np.round(original / scales).clip(-127, 127).astype(np.int8)
    variants = {"float32": original, "float16": original.astype(np.float16).astype(np.float32), "scalar_int8": quantized.astype(np.float32) * scales}
    scores = {}
    for kind, vectors in variants.items():
        vectors = vectors / np.maximum(np.linalg.norm(vectors, axis=1, keepdims=True), 1e-12)
        similarities = query_vectors @ vectors.T
        recalls, ndcgs = [], []
        for query, distances in zip(queries, similarities):
            indices = np.argsort(-distances)
            labels = list(dict.fromkeys(corpus[index]["label"] for index in indices))
            relevant = set(query["expected"])
            recalls.append(len(set(labels[:30]) & relevant) / len(relevant))
            dcg = sum((label in relevant) / math.log2(rank + 2) for rank, label in enumerate(labels[:10]))
            ideal = sum(1 / math.log2(rank + 2) for rank in range(min(len(relevant), 10)))
            ndcgs.append(dcg / ideal)
        scores[kind] = {"dense_recall30":float(np.mean(recalls)),"dense_ndcg10":float(np.mean(ndcgs))}
    outputs.append({"model": result["model"],"scores": scores,"notes":"float16 と scalar int8 の保存丸めを、復元後の全件走査で比較。IVF-PQ、Qdrant の 1.5/2bit、ANN の再スコア性能を検証したものではない。"})
(OUT / "vector-precision.json").write_text(json.dumps(outputs,ensure_ascii=False,indent=2),encoding="utf-8")
print(json.dumps(outputs,ensure_ascii=False))
