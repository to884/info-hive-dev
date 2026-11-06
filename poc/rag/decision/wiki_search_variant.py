"""E8 用: wiki の wiki_search.py を、埋め込みモデルか分かち書きだけを差し替えて動かす包み。

wiki の評価（eval/retrieval/run_eval.py）はクエリごとに `python <SCRIPT> <query> ...` を起動するので、
SCRIPT をこのファイルに差し替えて使う。wiki のコードは変えない。環境変数で切り替える。

- DECISION_WIKI_SCRIPTS  wiki_search.py のあるディレクトリ（必須）
- DECISION_EMBED         e5（既定、wiki のまま）か r130（ruri-v3-130m の ONNX fp32）
- DECISION_MAX_DISTANCE  r130 のときのコサイン距離の上限
- DECISION_ONNX_DIR      r130 の組み立て済み ONNX のディレクトリ
- DECISION_TOKENIZER     bigram（既定、wiki のまま）か sudachi（rag と同じ SplitMode C の normalized_form）
- DECISION_LEXICAL       wiki（既定、wiki の BM25）か tantivy（同じトークンを Tantivy の BM25 で採点する）
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


def use_tantivy():
    """語彙のスコアを Tantivy の BM25 で出す。トークンは wiki の tokenize のまま（案 2: エンジンだけをそろえる）。

    wiki の build_bm25 が作る索引から、文書ごとの語の頻度をそのまま Tantivy の RAM の索引に入れる。
    問い合わせは、クエリのトークンごとの term_query を Should で並べる（重複したトークンは wiki と同じく重ねて数える）。
    IDF の式は wiki と同じ ln(1 + (N - df + 0.5) / (df + 0.5))。違いは k1（wiki 1.5、Tantivy 1.2）と、
    Tantivy が文書の長さを 1 バイトに丸めて持つことである。
    """
    import tantivy

    built = {}

    def index_for(idx):
        key = id(idx)
        if key not in built:
            builder = tantivy.SchemaBuilder()
            builder.add_integer_field("id", stored=True, fast=True)
            builder.add_text_field("terms", stored=False, tokenizer_name="ws", index_option="freq")
            schema = builder.build()
            index = tantivy.Index(schema)
            index.register_tokenizer("ws", tantivy.TextAnalyzerBuilder(tantivy.Tokenizer.whitespace()).build())
            writer = index.writer(heap_size=50_000_000, num_threads=1)
            for i, tf in enumerate(idx["term_freqs"]):
                writer.add_document(tantivy.Document(id=i, terms=" ".join(t for term, f in tf.items() for t in [term] * f)))
            writer.commit()
            writer.wait_merging_threads()
            index.reload()
            built[key] = (schema, index.searcher(), idx)
        return built[key]

    def lexical_ranking(query_tokens, idx, keep=None):
        schema, searcher, _ = index_for(idx)
        q = tantivy.Query
        clauses = [(tantivy.Occur.Should, q.term_query(schema, "terms", t)) for t in query_tokens if t in idx["df"]]
        if not clauses or not idx["N"]:
            return []
        hits = searcher.search(q.boolean_query(clauses), limit=idx["N"]).hits
        ranked = []
        for score, address in hits:
            i = searcher.doc(address)["id"][0]
            if score > 0 and (keep is None or keep(i)):
                ranked.append((float(score), i))
        ranked.sort(key=lambda item: -item[0])
        return ranked

    ws.lexical_ranking = lexical_ranking


if os.environ.get("DECISION_EMBED", "e5") == "r130":
    use_r130()
if os.environ.get("DECISION_LEXICAL", "wiki") == "tantivy":
    use_tantivy()
if os.environ.get("DECISION_TOKENIZER", "bigram") == "sudachi":
    use_sudachi()

if __name__ == "__main__":
    ws.main()
