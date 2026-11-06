"""全量（761,915 チャンク）の測定の共通部品。E2、E3、E4、E6 で使う。"""
from __future__ import annotations

import math
import time

import numpy as np

from decision_common import DWORK  # noqa: F401  (sys.path を整える)
from common import WORK, Tokenizer, full_queries, p95
from db_bench import load_data, query_vectors

USEARCH_KEPT = WORK / "db/full/R-130/usearch_HNSW_f16___Tantivy/vectors.usearch"
TANTIVY_FULL = WORK / "lexical/full/Tantivy"


class ScoredTantivy:
    """lexical_bench.Tantivy と同じ問い合わせ（IDF を BM25 にそろえる）で、スコアも返す。"""

    def __init__(self, folder=TANTIVY_FULL):
        from lexical_bench import Tantivy
        self.inner = Tantivy(folder)
        self.inner.open()

    def search(self, terms, k):
        inner = self.inner
        words = list(dict.fromkeys(terms.split()))
        tq = inner.tantivy.Query
        total = inner.searcher.num_docs
        clauses = []
        for w in words:
            df = inner.searcher.doc_freq("terms", w)
            if df == 0:
                continue
            fts5_idf = max(1e-6, math.log((total - df + .5) / (df + .5)))
            tantivy_idf = math.log(1 + (total - df + .5) / (df + .5))
            clauses.append((inner.tantivy.Occur.Should, tq.boost_query(tq.term_query(inner.schema, "terms", w), fts5_idf / tantivy_idf)))
        if not clauses:
            return [], []
        hits = inner.searcher.search(tq.boolean_query(clauses), limit=k).hits
        return [inner.searcher.doc(address)["id"][0] for _, address in hits], [float(score) for score, _ in hits]


def load_full():
    """ids、vectors、terms、generations、labels、queries、クエリのベクトル、クエリの語、厳密な上位 30 件。"""
    ids, vectors, terms, generations, labels = load_data("R-130", "full")
    queries = full_queries()
    qvecs = query_vectors("R-130", "onnx-fp32")
    tokenize = Tokenizer()
    query_terms = [tokenize(q["query"]) for q in queries]
    return ids, vectors, terms, generations, labels, queries, qvecs, query_terms


def exact_top(qvecs, vectors, ids, k=30, mask=None):
    out = []
    for q in qvecs:
        scores = vectors @ q
        if mask is not None:
            scores = np.where(mask, scores, -np.inf)
        top = np.argpartition(-scores, k - 1)[:k]
        out.append(set(ids[top].tolist()))
    return out


def timed(function, *args):
    started = time.perf_counter()
    value = function(*args)
    return value, (time.perf_counter() - started) * 1000


__all__ = ["USEARCH_KEPT", "TANTIVY_FULL", "ScoredTantivy", "load_full", "exact_top", "timed", "p95"]
