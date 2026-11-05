"""M2 と M6: 評価用の文書とクエリを、モデルごとに GPU の sentence-transformers で埋め込む。

製品の実行系（CPU の fastembed や torch）との差は runtime_parity.py で別に確かめる。
全量は時間がかかるので、長さ順のブロックごとに保存して途中から再開できるようにする。
"""
from __future__ import annotations

import argparse
import sqlite3
import time

import numpy as np

from common import FULL, MODEL_CACHE, MODELS, WORK, full_mapping, full_queries, load_natural, read_json, subset_ids, write_json

BLOCK = 4096


def texts_for(dataset: str):
    if dataset == "natural":
        rows, queries = load_natural()
        return [row["embedding_text"] for row in rows], [q["query"] for q in queries]
    if dataset == "parity":
        return [t for _, t in parity_rows()], [q["query"] for q in full_queries()]
    ids = subset_ids() if dataset == "subset" else [row[0] for row in full_mapping()]
    connection = sqlite3.connect(FULL / "corpus.sqlite")
    connection.execute("CREATE TEMP TABLE wanted(id INTEGER PRIMARY KEY)")
    connection.executemany("INSERT INTO wanted VALUES(?)", ((i,) for i in ids))
    texts = [row[0] for row in connection.execute("SELECT c.embedding_text FROM chunks c JOIN wanted w ON w.id=c.id ORDER BY c.id")]
    connection.close()
    assert len(texts) == len(ids)
    return texts, [q["query"] for q in full_queries()]


def parity_rows():
    """全量から固定の乱数で 300 チャンクを選ぶ。最長の 20 件を必ず含める。

    計画では 1,000 件としたが、CPU の torch で R-310 を 1,000 件埋め込むと 1 時間を超えるので 300 件にした。
    """
    target = WORK / "parity-ids.json"
    if target.exists():
        ids = read_json(target)["ids"]
    else:
        connection = sqlite3.connect(FULL / "corpus.sqlite")
        everything = [row[0] for row in full_mapping()]
        longest = [row[0] for row in connection.execute(
            "SELECT id FROM chunks ORDER BY length(embedding_text) DESC LIMIT 200") if row[0] in set(everything)][:20]
        rest = sorted(set(np.random.default_rng(20261105).choice(everything, 400, replace=False).tolist()) - set(longest))[:280]
        ids = sorted(longest + rest)
        write_json(target, {"seed": 20261105, "longest_included": longest, "ids": ids})
        connection.close()
    connection = sqlite3.connect(FULL / "corpus.sqlite")
    rows = [(i, connection.execute("SELECT embedding_text FROM chunks WHERE id=?", (i,)).fetchone()[0]) for i in ids]
    connection.close()
    return rows


def load_model(key: str, device: str):
    import torch
    from sentence_transformers import SentenceTransformer
    spec = MODELS[key]
    torch.backends.cuda.matmul.allow_tf32 = False
    torch.backends.cudnn.allow_tf32 = False
    kwargs = {"model_kwargs": {"attn_implementation": "sdpa"}} if key.startswith("R-") else {}
    model = SentenceTransformer(spec["id"], revision=spec["revision"], cache_folder=str(MODEL_CACHE), device=device, **kwargs)
    if key != "S-ja":
        model.max_seq_length = min(spec["max_tokens"], 8192)
    return model


def token_lengths(model, texts, prefix):
    if not hasattr(model, "tokenizer") or model.tokenizer is None:
        return np.array([len(t) for t in texts])
    if not callable(model.tokenizer):
        # 静的埋め込み（S-ja）は tokenizers.Tokenizer をそのまま持つ。
        return np.array([len(e.ids) for e in model.tokenizer.encode_batch([prefix + t for t in texts])])
    lengths = []
    for start in range(0, len(texts), 10_000):
        lengths.extend(len(ids) for ids in model.tokenizer([prefix + t for t in texts[start:start + 10_000]], truncation=False, padding=False)["input_ids"])
    return np.array(lengths)


def encode(model, texts, prefix, order, lengths, result, progress_path=None, done=0, device="cuda", budget=65_536):
    started = time.perf_counter()
    position = done
    while position < len(order):
        block = order[position:position + BLOCK]
        longest = int(min(lengths[block].max(), model.max_seq_length or 10 ** 9))
        # 1 バッチのトークン数を予算で抑える。E-l（1024 次元、24 層）で 256 件 × 512 トークンにすると
        # 10 GB の GPU からあふれ、Windows の共有メモリに落ちて止まったように遅くなった。
        batch = max(1, min(256, budget // max(1, longest), (8 * 2048 ** 2) // max(1, longest ** 2))) if device == "cuda" else 16
        result[block] = model.encode([prefix + texts[i] for i in block], normalize_embeddings=True, batch_size=batch,
                                     show_progress_bar=False, convert_to_numpy=True)
        position += len(block)
        if progress_path is not None:
            result.flush()
            write_json(progress_path, {"done": position, "total": len(order), "seconds_this_run": time.perf_counter() - started})
            print(f"{position}/{len(order)} {time.perf_counter() - started:.0f}s", flush=True)
    return time.perf_counter() - started


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--model", required=True, choices=sorted(MODELS))
    parser.add_argument("--dataset", required=True, choices=["natural", "subset", "full", "parity"])
    parser.add_argument("--device", default="cuda")
    parser.add_argument("--budget", type=int, help="1 バッチのトークン数の上限。GPU のメモリが足りないときに下げる")
    args = parser.parse_args()
    spec = MODELS[args.model]
    folder = WORK / "vectors" / args.dataset
    folder.mkdir(parents=True, exist_ok=True)
    meta_path = folder / f"{args.model}.json"
    if meta_path.exists() and read_json(meta_path).get("complete"):
        print("完成済み", meta_path)
        return
    texts, queries = texts_for(args.dataset)
    model = load_model(args.model, args.device)
    lengths_path = folder / f"{args.model}.lengths.npy"
    if lengths_path.exists():
        lengths = np.load(lengths_path)
    else:
        lengths = token_lengths(model, texts, spec["passage"])
        np.save(lengths_path, lengths)
    order = np.argsort(lengths, kind="stable")
    target = folder / f"{args.model}.npy"
    progress_path = folder / f"{args.model}.progress.json"
    done = read_json(progress_path)["done"] if progress_path.exists() and target.exists() else 0
    result = np.lib.format.open_memmap(target, mode="r+" if done else "w+", dtype=np.float32, shape=(len(texts), spec["dimension"]))
    previous = read_json(meta_path).get("passage_seconds", 0.0) if meta_path.exists() else 0.0
    budget = args.budget or (16_384 if spec["dimension"] >= 768 and args.model != "S-ja" else 65_536)
    seconds = encode(model, texts, spec["passage"], order, lengths, result, progress_path, done, args.device, budget)
    result.flush()
    del result
    query_vectors = model.encode([spec["query"] + q for q in queries], normalize_embeddings=True, batch_size=32, show_progress_bar=False, convert_to_numpy=True)
    np.save(folder / f"{args.model}.queries.npy", query_vectors.astype(np.float32))
    write_json(meta_path, {"model": spec["id"], "revision": spec["revision"], "dimension": spec["dimension"], "dataset": args.dataset,
                           "rows": len(texts), "device": args.device, "passage_seconds": previous + seconds,
                           "max_tokens": int(lengths.max()), "over_model_limit": int((lengths > spec["max_tokens"]).sum()),
                           "over_model_limit_ratio": float((lengths > spec["max_tokens"]).mean()), "complete": True})


if __name__ == "__main__":
    main()
