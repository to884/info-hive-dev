"""M3 と M6 の確認: 製品で動かす CPU の実行系が、GPU の sentence-transformers のベクトルと一致するかを測る。

対象は wiki の fastembed（e5）、rag の torch（Ruri）、Ruri の ONNX 書き出し（onnx-community、fastembed で読む）。
あわせて、CPU 4 スレッドでのモデル読み込み時間、1 クエリの埋め込み時間、文書の処理速度を記録する。
"""
from __future__ import annotations

import argparse
import os
import sys
import time

import numpy as np

from common import FULL, MODEL_CACHE, MODELS, OUT, ROOT, THREADS, WORK, full_mapping, full_queries, limit_threads, p95, read_json, subset_ids, write_json
from embed_models import parity_rows

ONNX_REPOS = {"R-30": "onnx-community/ruri-v3-30m-ONNX", "R-130": "onnx-community/ruri-v3-130m-ONNX", "R-310": "onnx-community/ruri-v3-310m-ONNX"}
ONNX_REVISIONS = {"R-30": "1b41a27f31213fc55a9c4653c067770e39406408", "R-130": "cbd305d39c17cc58375ceb29586996e7d98d48c0",
                  "R-310": "fcf9f60dcb54b4271358de97c0688ec2b97325a6"}
ONNX_FILES = {"onnx-fp32": "onnx/model.onnx", "onnx-fp16": "onnx/model_fp16.onnx", "onnx-int8": "onnx/model_quantized.onnx"}
FASTEMBED_CACHE = WORK / "fastembed-cache"
RUNTIMES = [("E-s", "fastembed-fp16"), ("E-l", "fastembed"), ("S-ja", "st-cpu"),
            ("R-30", "torch-cpu"), ("R-30", "onnx-fp32"), ("R-30", "onnx-fp16"), ("R-30", "onnx-int8"),
            ("R-130", "torch-cpu"), ("R-130", "onnx-fp32"), ("R-130", "onnx-fp16"), ("R-130", "onnx-int8"),
            ("R-310", "torch-cpu"), ("R-310", "onnx-fp32"), ("R-310", "onnx-fp16")]


def onnx_folder(key, kind):
    """ONNX の重みは onnx-community、トークナイザと設定は元の cl-nagoya の固定 revision から取り、1 つのディレクトリにまとめる。

    onnx-community の書き出しにはトークナイザのファイルがない。製品で使うときも同じ組み立てが要る。
    """
    from huggingface_hub import hf_hub_download
    import shutil
    folder = WORK / "onnx" / key / kind
    (folder / "onnx").mkdir(parents=True, exist_ok=True)
    target = folder / ONNX_FILES[kind]
    if not target.exists():
        shutil.copyfile(hf_hub_download(ONNX_REPOS[key], ONNX_FILES[kind], revision=ONNX_REVISIONS[key], cache_dir=str(WORK / "hf-cache")), target)
    for name in ("config.json", "tokenizer.json", "tokenizer_config.json", "special_tokens_map.json"):
        if not (folder / name).exists():
            shutil.copyfile(hf_hub_download(MODELS[key]["id"], name, revision=MODELS[key]["revision"], cache_dir=str(MODEL_CACHE)), folder / name)
    return folder


class Runtime:
    def __init__(self, key, kind):
        self.key, self.kind, self.spec = key, kind, MODELS[key]

    def load(self):
        if self.kind.startswith("fastembed"):
            # wiki の実装をそのまま使う（info-hive-wiki/skills/info-hive/scripts/wiki_search.py）。
            sys.path.insert(0, str(ROOT / "info-hive-wiki/skills/info-hive/scripts"))
            os.environ["INFO_HIVE_EMBED_MODEL"] = self.spec["id"]
            import wiki_search
            self.module = wiki_search
            self.model, _, _ = wiki_search.load_local_embedding_backend()
            self.wiki = True
        elif self.kind.startswith("onnx"):
            os.environ.setdefault("HF_HUB_DISABLE_SHARED_BLOBS", "1")
            from fastembed import TextEmbedding
            from fastembed.common.model_description import ModelSource, PoolingType
            folder = onnx_folder(self.key, self.kind)
            name = f"{ONNX_REPOS[self.key]}:{self.kind}"
            if name.lower() not in {m["model"].lower() for m in TextEmbedding.list_supported_models()}:
                TextEmbedding.add_custom_model(model=name, pooling=PoolingType.MEAN, normalization=True,
                                               sources=ModelSource(hf=ONNX_REPOS[self.key]), dim=self.spec["dimension"],
                                               model_file=ONNX_FILES[self.kind])
            self.model = TextEmbedding(model_name=name, cache_dir=str(FASTEMBED_CACHE), threads=THREADS, specific_model_path=str(folder))
            self.wiki = False
        else:
            import torch
            from sentence_transformers import SentenceTransformer
            torch.set_num_threads(THREADS)
            kwargs = {"model_kwargs": {"attn_implementation": "sdpa"}} if self.key.startswith("R-") else {}
            self.model = SentenceTransformer(self.spec["id"], revision=self.spec["revision"], cache_folder=str(MODEL_CACHE), device="cpu", **kwargs)
            if self.key != "S-ja":
                self.model.max_seq_length = min(self.spec["max_tokens"], 8192)
            self.wiki = False

    def queries(self, texts):
        if self.kind.startswith(("fastembed", "onnx")):
            return np.array([next(self.model.query_embed(self.spec["query"] + t)) for t in texts], dtype=np.float32)
        return self.model.encode([self.spec["query"] + t for t in texts], normalize_embeddings=True, convert_to_numpy=True, show_progress_bar=False)

    def passages(self, texts):
        if self.kind.startswith(("fastembed", "onnx")):
            return np.array(list(self.model.passage_embed([self.spec["passage"] + t for t in texts], batch_size=16)), dtype=np.float32)
        return self.model.encode([self.spec["passage"] + t for t in texts], normalize_embeddings=True, convert_to_numpy=True,
                                 batch_size=16, show_progress_bar=False)


def index_vectors(key):
    """検索の一致を見るための文書ベクトル。R-130 は既存の全量、ほかは 100,000 行の部分集合。"""
    if key == "R-130":
        mapping = full_mapping()
        raw = FULL / "embeddings-130m/vectors.f32"
        mapped = np.memmap(raw, mode="r", dtype=np.float32, shape=(raw.stat().st_size // 2048, 512))
        return np.array(mapped[[r[1] for r in mapping]], dtype=np.float32), "全量 761,915 行"
    path = WORK / f"vectors/subset/{key}.npy"
    if path.exists():
        return np.load(path, mmap_mode="r"), f"部分集合 {len(subset_ids()):,} 行"
    return None, None


def overlap_at_30(index, a, b):
    if index is None:
        return None
    top_a = np.argpartition(-(a @ index.T), 29, axis=1)[:, :30]
    top_b = np.argpartition(-(b @ index.T), 29, axis=1)[:, :30]
    return float(np.mean([len(set(x) & set(y)) / 30 for x, y in zip(top_a, top_b)]))


def run(key, kind):
    limit_threads()
    gpu_meta = WORK / "vectors/parity" / f"{key}.json"
    if not gpu_meta.exists():
        raise RuntimeError(f"{key} の GPU 基準ベクトルがありません。embed_models.py --dataset parity を先に実行してください。")
    rows = parity_rows()
    texts = [t for _, t in rows]
    longest = set(read_json(WORK / "parity-ids.json")["longest_included"])
    is_longest = np.array([i in longest for i, _ in rows])
    reference = np.load(WORK / f"vectors/parity/{key}.npy")
    reference_queries = np.load(WORK / f"vectors/parity/{key}.queries.npy")
    queries = [q["query"] for q in full_queries()]
    runtime = Runtime(key, kind)
    started = time.perf_counter()
    runtime.load()
    load_seconds = time.perf_counter() - started
    runtime.queries(queries[:3])
    timings = []
    query_vectors = []
    for text in queries:
        started = time.perf_counter()
        query_vectors.append(runtime.queries([text])[0])
        timings.append((time.perf_counter() - started) * 1000)
    query_vectors = np.array(query_vectors, dtype=np.float32)
    started = time.perf_counter()
    passages = runtime.passages(texts)
    passage_seconds = time.perf_counter() - started
    cosine = np.sum(passages * reference, axis=1) / (np.linalg.norm(passages, axis=1) * np.linalg.norm(reference, axis=1))
    query_cosine = np.sum(query_vectors * reference_queries, axis=1) / (np.linalg.norm(query_vectors, axis=1) * np.linalg.norm(reference_queries, axis=1))
    index, scope = index_vectors(key)
    np.save(WORK / f"runtime-queries/{key}__{kind}.npy", query_vectors) if (WORK / "runtime-queries").mkdir(exist_ok=True) is None else None
    return {"model": key, "runtime": kind, "load_seconds": load_seconds,
            "query_p95_ms": p95(timings), "query_median_ms": float(np.median(timings)),
            "passages": len(texts), "passage_seconds": passage_seconds, "passages_per_second": len(texts) / passage_seconds,
            "cosine_min": float(cosine.min()), "cosine_mean": float(cosine.mean()),
            "cosine_min_longest_20": float(cosine[is_longest].min()), "cosine_min_others": float(cosine[~is_longest].min()),
            "max_absolute_element_difference": float(np.max(np.abs(passages - reference))),
            "query_cosine_min": float(query_cosine.min()),
            "query_top30_overlap_with_gpu_queries": overlap_at_30(index, query_vectors, reference_queries), "overlap_index": scope,
            "onnx_source": {"repo": ONNX_REPOS[key], "revision": ONNX_REVISIONS[key], "file": ONNX_FILES[kind]} if kind.startswith("onnx") else None}


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--only", nargs="*", help="model:runtime の形で絞る")
    parser.add_argument("--worker", help="1 つの model:runtime を別プロセスで測る")
    args = parser.parse_args()
    if args.worker:
        key, kind = args.worker.split(":")
        write_json(WORK / f"runtime-parity/{key}__{kind}.json", run(key, kind))
        return
    import subprocess
    results = []
    for key, kind in RUNTIMES:
        label = f"{key}:{kind}"
        if args.only and label not in args.only:
            continue
        target = WORK / f"runtime-parity/{key}__{kind}.json"
        if not target.exists():
            # モデルごとに別プロセスにして、読み込み時間とメモリを互いに混ぜない。
            completed = subprocess.run([sys.executable, "-X", "utf8", __file__, "--worker", label], capture_output=True, text=True, encoding="utf-8")
            if completed.returncode:
                results.append({"model": key, "runtime": kind, "status": "failed", "error": completed.stderr[-1500:]})
                print(label, "failed", completed.stderr[-500:], flush=True)
                continue
        result = read_json(target)
        results.append({**result, "status": "ok"})
        print(label, {k: result[k] for k in ("cosine_min", "query_p95_ms", "passages_per_second", "query_top30_overlap_with_gpu_queries")}, flush=True)
    write_json(OUT / "runtime-parity.json", {
        "reference": "GPU の sentence-transformers（TF32 なし）で作った同じ 300 チャンク（最長 20 件を含む）と 72 問のクエリ",
        "cpu_threads": THREADS, "fastembed_cache": "wiki の既定（~/.cache/info-hive/fastembed）。ONNX 書き出しは作業領域のキャッシュ",
        "note": "query_top30_overlap_with_gpu_queries は、製品の実行系で作ったクエリと GPU のクエリで、同じ文書ベクトルに対する厳密な上位 30 件がどれだけ重なるか。1 なら索引を作り直さずに使い回せる",
        "results": results})


if __name__ == "__main__":
    main()
