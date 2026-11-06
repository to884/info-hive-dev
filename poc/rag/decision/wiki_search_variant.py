"""E8 用: wiki の wiki_search.py を、埋め込みモデルか分かち書きだけを差し替えて動かす包み。

wiki の評価（eval/retrieval/run_eval.py）はクエリごとに `python <SCRIPT> <query> ...` を起動するので、
SCRIPT をこのファイルに差し替えて使う。wiki のコードは変えない。環境変数で切り替える。

- DECISION_WIKI_SCRIPTS  wiki_search.py のあるディレクトリ（必須）
- DECISION_EMBED         e5（既定、wiki のまま）か r130（ruri-v3-130m の ONNX fp32）
- DECISION_MAX_DISTANCE  r130 のときのコサイン距離の上限
- DECISION_ONNX_DIR      r130 の組み立て済み ONNX のディレクトリ
- DECISION_TOKENIZER     bigram（既定、wiki のまま）か sudachi（rag と同じ SplitMode C の normalized_form）
"""
from __future__ import annotations

import os
import sys
import unicodedata

sys.path.insert(0, os.environ["DECISION_WIKI_SCRIPTS"])
import wiki_search as ws  # noqa: E402

R130 = "cl-nagoya/ruri-v3-130m"


def use_r130():
    ws.EMBED_MODELS[R130] = {
        "max_distance": float(os.environ["DECISION_MAX_DISTANCE"]),
        "query_prefix": "検索クエリ: ",
        "passage_prefix": "検索文書: ",
        "custom": {"hf": "onnx-community/ruri-v3-130m-ONNX", "model_file": "onnx/model.onnx", "dim": 512,
                   "size_in_gb": 0.53, "license": "apache-2.0"},
    }
    ws.DEFAULT_EMBED_MODEL = R130
    os.environ.pop(ws.EMBED_MODEL_ENV, None)

    def load_local_embedding_backend():
        os.environ.setdefault("HF_HUB_DISABLE_SHARED_BLOBS", "1")
        import sqlite_vec
        from fastembed import TextEmbedding
        ws.register_custom_model(TextEmbedding, R130, ws.EMBED_MODELS[R130])
        model = TextEmbedding(model_name=R130, cache_dir=os.environ.get("FASTEMBED_CACHE_PATH", ""), threads=4,
                              specific_model_path=os.environ["DECISION_ONNX_DIR"])
        return model, sqlite_vec, 512

    ws.load_local_embedding_backend = load_local_embedding_backend


def use_sudachi():
    from sudachipy import dictionary, tokenizer
    analyzer = dictionary.Dictionary().create()
    mode = tokenizer.Tokenizer.SplitMode.C

    def tokenize(text: str) -> list[str]:
        normalized = unicodedata.normalize("NFKC", text).lower()
        tokens = []
        # Sudachi は 1 回の入力を 49,149 バイトまでしか受け付けないので、行でまとめて区切る。
        block, size = [], 0
        lines = normalized.splitlines() or [normalized]
        for line in lines + [None]:
            if line is None or size + len(line.encode("utf-8")) > 40_000:
                text_block = "\n".join(block)
                if text_block.strip():
                    tokens.extend(word.normalized_form().lower() for word in analyzer.tokenize(text_block, mode)
                                  if word.surface().strip() and word.part_of_speech()[0] != "補助記号")
                block, size = [], 0
            if line is not None:
                block.append(line[:12_000])
                size += len(line[:12_000].encode("utf-8"))
        return tokens

    ws.tokenize = tokenize


if os.environ.get("DECISION_EMBED", "e5") == "r130":
    use_r130()
if os.environ.get("DECISION_TOKENIZER", "bigram") == "sudachi":
    use_sudachi()

if __name__ == "__main__":
    ws.main()
