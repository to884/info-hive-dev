"""M3: Ruri v3 を ONNX にできるかを確かめる。

1. Hugging Face 上の既存の書き出し（onnx-community）の有無とファイル構成
2. torch.onnx.export（TorchScript 方式、opset 17）での自前の書き出しと、fastembed で読んだときの torch との一致
"""
from __future__ import annotations

import os
import shutil
import sqlite3
import time

import numpy as np

from common import FULL, MODEL_CACHE, MODELS, OUT, WORK, limit_threads, write_json
from runtime_parity import ONNX_REPOS, ONNX_REVISIONS, Runtime, onnx_folder


def existing_exports():
    from huggingface_hub import HfApi
    api = HfApi()
    found = {}
    for key, repo in ONNX_REPOS.items():
        info = api.model_info(repo, revision=ONNX_REVISIONS[key], files_metadata=True)
        files = {s.rfilename: s.size for s in info.siblings}
        found[key] = {"repo": repo, "revision": ONNX_REVISIONS[key],
                      "onnx_files": {k: v for k, v in files.items() if k.endswith(".onnx")},
                      "has_tokenizer": "tokenizer.json" in files}
    original = {key: "tokenizer.json" in {s.rfilename for s in api.model_info(MODELS[key]["id"], revision=MODELS[key]["revision"]).siblings}
                for key in ONNX_REPOS}
    others = sorted({m.id for m in api.list_models(search="ruri-v3", limit=200) if "onnx" in m.id.lower()})
    return found, original, others


def self_export(key, texts):
    import torch
    from fastembed import TextEmbedding
    from fastembed.common.model_description import ModelSource, PoolingType
    from transformers import AutoModel
    spec = MODELS[key]
    model = AutoModel.from_pretrained(spec["id"], revision=spec["revision"], cache_dir=str(MODEL_CACHE), attn_implementation="eager").eval()
    folder = WORK / "onnx-self" / key
    shutil.rmtree(folder, ignore_errors=True)
    (folder / "onnx").mkdir(parents=True)
    for name in ("config.json", "tokenizer.json", "tokenizer_config.json", "special_tokens_map.json"):
        shutil.copyfile(onnx_folder(key, "onnx-fp32") / name, folder / name)
    sample = torch.ones(1, 16, dtype=torch.long)
    started = time.perf_counter()
    torch.onnx.export(model, (sample, sample), str(folder / "onnx/model.onnx"), input_names=["input_ids", "attention_mask"],
                      output_names=["last_hidden_state"], opset_version=17, dynamo=False,
                      dynamic_axes={"input_ids": {0: "batch", 1: "sequence"}, "attention_mask": {0: "batch", 1: "sequence"},
                                    "last_hidden_state": {0: "batch", 1: "sequence"}})
    seconds = time.perf_counter() - started
    del model
    name = f"self/{key}"
    TextEmbedding.add_custom_model(model=name, pooling=PoolingType.MEAN, normalization=True, sources=ModelSource(hf=spec["id"]),
                                   dim=spec["dimension"], model_file="onnx/model.onnx")
    onnx_model = TextEmbedding(model_name=name, specific_model_path=str(folder), threads=4)
    reference = Runtime(key, "torch-cpu")
    reference.load()
    inputs = [spec["passage"] + t for t in texts]
    a = np.array(list(onnx_model.passage_embed(inputs, batch_size=4)), dtype=np.float32)
    b = reference.model.encode(inputs, normalize_embeddings=True, batch_size=4)
    cosine = np.sum(a * b, axis=1)
    size = sum(p.stat().st_size for p in (folder / "onnx").iterdir())
    return {"export_seconds": seconds, "onnx_bytes": size, "texts": len(texts), "cosine_min_vs_torch_cpu": float(cosine.min()),
            "max_absolute_element_difference": float(np.abs(a - b).max()), "exporter": "torch.onnx.export（dynamo=False、opset 17）",
            "torch": __import__("torch").__version__, "transformers": __import__("transformers").__version__}


def main():
    limit_threads()
    os.environ.setdefault("HF_HUB_DISABLE_SHARED_BLOBS", "1")
    found, original, others = existing_exports()
    connection = sqlite3.connect(FULL / "corpus.sqlite")
    # 最長の 2 件（2,000 トークン前後）と短い 3 件。長い入力で注意の実装差が出ないかを見る。
    texts = [r[0] for r in connection.execute("SELECT embedding_text FROM chunks ORDER BY length(embedding_text) DESC LIMIT 2")]
    texts += [r[0] for r in connection.execute("SELECT embedding_text FROM chunks LIMIT 3")]
    connection.close()
    exports = {}
    for key in ONNX_REPOS:
        try:
            exports[key] = {"status": "ok", **self_export(key, texts)}
        except Exception as error:
            exports[key] = {"status": "failed", "error": f"{type(error).__name__}: {error}"}
        print(key, exports[key], flush=True)
    write_json(OUT / "onnx-feasibility.json", {
        "existing_exports": found, "original_repo_has_tokenizer": original, "other_ruri_onnx_repos": others,
        "note": "onnx-community の書き出しはトークナイザを含まないので、元の cl-nagoya の固定 revision から tokenizer.json などを足して 1 つのディレクトリにする。fastembed は tokenizer_config.json の model_max_length（8192）で切り詰める",
        "self_export": exports})


if __name__ == "__main__":
    main()
