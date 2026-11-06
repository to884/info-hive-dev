"""E9: ruri-v3-130m の ONNX を、公開版から空のキャッシュで取得できるかを確かめる。

製品は onnx-community の書き出し（重み）と cl-nagoya の固定 revision（トークナイザと設定）を組み立てて使う。
ここでは空のキャッシュから取得し、容量、sha256、時間、ライセンスを記録する。取得したファイルが
統一の測定で使った組み立て済みのファイルと同じか（sha256）と、同じ 300 チャンクの埋め込みが一致するかを見る。
"""
from __future__ import annotations

import shutil
import time

import numpy as np

from decision_common import DWORK, R130_ONNX, save
from common import MODELS, THREADS, WORK, limit_threads, sha256_file
from runtime_parity import ONNX_FILES, ONNX_REPOS, ONNX_REVISIONS

TOKENIZER_FILES = ("config.json", "tokenizer.json", "tokenizer_config.json", "special_tokens_map.json")


def main():
    limit_threads()
    import os
    os.environ["HF_HUB_DISABLE_SHARED_BLOBS"] = "1"
    from huggingface_hub import hf_hub_download, model_info
    cache = DWORK / "hf-fresh"
    if cache.exists():
        shutil.rmtree(cache)
    folder = DWORK / "onnx-fresh/R-130"
    if folder.exists():
        shutil.rmtree(folder)
    (folder / "onnx").mkdir(parents=True)
    files = []
    started = time.perf_counter()
    sources = [(ONNX_REPOS["R-130"], ONNX_REVISIONS["R-130"], ONNX_FILES["onnx-fp32"])]
    sources += [(MODELS["R-130"]["id"], MODELS["R-130"]["revision"], name) for name in TOKENIZER_FILES]
    for repo, revision, name in sources:
        t = time.perf_counter()
        path = hf_hub_download(repo, name, revision=revision, cache_dir=str(cache))
        target = folder / name
        shutil.copyfile(path, target)
        reference = R130_ONNX / name
        files.append({"repo": repo, "revision": revision, "file": name, "bytes": target.stat().st_size,
                      "sha256": sha256_file(target), "seconds": time.perf_counter() - t,
                      "same_as_measured": reference.exists() and sha256_file(reference) == sha256_file(target)})
    total_seconds = time.perf_counter() - started
    licenses = {}
    for repo, revision in {(ONNX_REPOS["R-130"], ONNX_REVISIONS["R-130"]), (MODELS["R-130"]["id"], MODELS["R-130"]["revision"])}:
        info = model_info(repo, revision=revision)
        licenses[repo] = (info.card_data or {}).get("license") if info.card_data else None

    from fastembed import TextEmbedding
    from fastembed.common.model_description import ModelSource, PoolingType
    name = "info-hive/ruri-v3-130m-onnx-fresh"
    TextEmbedding.add_custom_model(model=name, pooling=PoolingType.MEAN, normalization=True,
                                   sources=ModelSource(hf=ONNX_REPOS["R-130"]), dim=MODELS["R-130"]["dimension"],
                                   model_file=ONNX_FILES["onnx-fp32"])
    model = TextEmbedding(model_name=name, cache_dir=str(DWORK / "fastembed-fresh"), threads=THREADS, specific_model_path=str(folder))
    from embed_models import parity_rows
    texts = [t for _, t in parity_rows()]
    passages = np.array(list(model.passage_embed([MODELS["R-130"]["passage"] + t for t in texts], batch_size=16)), dtype=np.float32)
    reference = np.load(WORK / "vectors/parity/R-130.npy")
    cosine = np.sum(passages * reference, axis=1) / (np.linalg.norm(passages, axis=1) * np.linalg.norm(reference, axis=1))
    top = np.argsort(-(passages @ passages.T), axis=1)[:, :30]
    top_ref = np.argsort(-(reference @ reference.T), axis=1)[:, :30]
    overlap = float(np.mean([len(set(a) & set(b)) / 30 for a, b in zip(top, top_ref)]))
    weights = next(f for f in files if f["file"].endswith(".onnx"))
    passed = all(f["same_as_measured"] for f in files) and float(cosine.min()) >= 0.9999 and overlap == 1.0
    save("onnx-distribution.json", {
        "purpose": "公開版の ONNX（onnx-community）とトークナイザ（cl-nagoya）を空のキャッシュから取得できるか",
        "files": files, "download_seconds": total_seconds, "weights_bytes": weights["bytes"],
        "total_bytes": sum(f["bytes"] for f in files), "licenses": licenses,
        "parity": {"texts": len(texts), "reference": "GPU の sentence-transformers（統一の測定の vectors/parity/R-130.npy）",
                   "cosine_min": float(cosine.min()), "cosine_mean": float(cosine.mean()), "top30_overlap_within_parity": overlap},
        "criterion": "全ファイルの sha256 が測定に使ったものと同じ、cosine の最小 ≥ 0.9999、上位 30 件の一致 1.0",
        "passed": passed})


if __name__ == "__main__":
    main()
