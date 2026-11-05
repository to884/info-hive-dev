"""M1 の補足: 語彙検索のエンジンを、同じ Sudachi の語と同じ 72 問で比べる。

FTS5 は上位 k 件で打ち切る仕組みを持たず、頻出語（「の」「は」など）を含む OR の検索で一致した全行の BM25 を計算する。
Tantivy は block-max WAND で上位 k 件を打ち切る。ネイティブの全文検索を持たない DB（sqlite-vec、usearch、FAISS、Chroma）は、
どちらかを組み合わせて使う。順位は summarize.py が dense の順位と融合して、組の精度と速度を作り直す。
"""
from __future__ import annotations

import argparse
import json
import math
import shutil
import sqlite3
import time

import numpy as np

from common import FULL, OUT, WORK, Timer, Tokenizer, create_fts5, directory_bytes, fts5_search, full_mapping, full_queries, p95, subset_ids, write_json

CANDIDATES = 200


def load_terms(dataset):
    ids = [row[0] for row in full_mapping()]
    if dataset == "subset":
        wanted = set(subset_ids())
        ids = [i for i in ids if i in wanted]
    connection = sqlite3.connect(FULL / "terms.sqlite")
    connection.execute("CREATE TEMP TABLE wanted(id INTEGER PRIMARY KEY)")
    connection.executemany("INSERT INTO wanted VALUES(?)", ((i,) for i in ids))
    rows = connection.execute("SELECT t.id,t.terms FROM terms t JOIN wanted w ON w.id=t.id ORDER BY t.id").fetchall()
    connection.close()
    return [r[0] for r in rows], [r[1] for r in rows]


class Fts5:
    name = "SQLite FTS5"

    def __init__(self, folder):
        self.path = folder / "lexical.sqlite"

    def build(self, ids, terms):
        connection = sqlite3.connect(self.path)
        connection.execute("PRAGMA journal_mode=OFF")
        create_fts5(connection)
        connection.executemany("INSERT INTO lexical(rowid,terms) VALUES(?,?)", zip(ids, terms))
        connection.commit()
        connection.execute("INSERT INTO lexical(lexical) VALUES('optimize')")
        connection.commit()
        connection.execute("VACUUM")
        connection.close()

    def open(self):
        self.connection = sqlite3.connect(self.path)

    def search(self, terms, k):
        return fts5_search(self.connection, terms, k)


class Tantivy:
    name = "Tantivy"

    def __init__(self, folder):
        self.folder = folder / "tantivy"

    def _index(self):
        import tantivy
        builder = tantivy.SchemaBuilder()
        builder.add_integer_field("id", stored=True, fast=True)
        builder.add_text_field("terms", stored=False, tokenizer_name="ws", index_option="freq")
        self.schema = builder.build()
        index = tantivy.Index(self.schema, path=str(self.folder))
        index.register_tokenizer("ws", tantivy.TextAnalyzerBuilder(tantivy.Tokenizer.whitespace()).build())
        return index

    def build(self, ids, terms):
        import tantivy
        self.folder.mkdir(parents=True)
        index = self._index()
        writer = index.writer(heap_size=1_000_000_000, num_threads=4)
        for i, t in zip(ids, terms):
            writer.add_document(tantivy.Document(id=int(i), terms=t))
        writer.commit()
        writer.wait_merging_threads()

    def open(self):
        import tantivy
        self.tantivy = tantivy
        index = self._index()
        index.reload()
        self.searcher = index.searcher()

    def search(self, terms, k):
        words = list(dict.fromkeys(terms.split()))
        if not words:
            return []
        # Tantivy の IDF は log(1 + (N - n + 0.5) / (n + 0.5)) で常に正なので、「の」「は」のような頻出語も点を稼ぐ。
        # FTS5（と元の BM25）の IDF は log((N - n + 0.5) / (n + 0.5)) で、半数以上の行にある語はほぼ 0 になる。
        # 語ごとに比で重みを付け、FTS5 と同じ BM25 にそろえる。重みを付けないと、全量の語彙だけの再現率が 0.461 から 0.306 に落ちた。
        tq = self.tantivy.Query
        total = self.searcher.num_docs
        clauses = []
        for w in words:
            df = self.searcher.doc_freq("terms", w)
            if df == 0:
                continue
            fts5_idf = max(1e-6, math.log((total - df + .5) / (df + .5)))
            tantivy_idf = math.log(1 + (total - df + .5) / (df + .5))
            clauses.append((self.tantivy.Occur.Should, tq.boost_query(tq.term_query(self.schema, "terms", w), fts5_idf / tantivy_idf)))
        if not clauses:
            return []
        query = tq.boolean_query(clauses)
        return [self.searcher.doc(address)["id"][0] for _, address in self.searcher.search(query, limit=k).hits]


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--dataset", required=True, choices=["subset", "full"])
    args = parser.parse_args()
    ids, terms = load_terms(args.dataset)
    tokenize = Tokenizer()
    queries = full_queries()
    query_terms = [tokenize(q["query"]) for q in queries]
    out = OUT / f"lexical-bench-{args.dataset}.json"
    results = []
    for cls in (Fts5, Tantivy):
        folder = WORK / "lexical" / args.dataset / cls.__name__
        shutil.rmtree(folder, ignore_errors=True)
        folder.mkdir(parents=True)
        engine = cls(folder)
        with Timer() as build:
            engine.build(ids, terms)
        engine.open()
        for t in query_terms[:5]:
            engine.search(t, CANDIDATES)
        runs = []
        for t in query_terms:
            started = time.perf_counter()
            found = engine.search(t, CANDIDATES)
            runs.append({"ids": [int(i) for i in found], "ms": (time.perf_counter() - started) * 1000})
        size = directory_bytes(folder)
        ranking_folder = WORK / "rankings" / args.dataset
        ranking_folder.mkdir(parents=True, exist_ok=True)
        (ranking_folder / f"lexical__{cls.__name__}.json").write_text(json.dumps({"queries": [q["id"] for q in queries], "lexical": runs}), encoding="utf-8")
        record = {"engine": engine.name, "rows": len(ids), "build_seconds": build.seconds, "size_bytes": size,
                  "p95_ms": p95([r["ms"] for r in runs]), "median_ms": float(np.median([r["ms"] for r in runs])), "max_ms": max(r["ms"] for r in runs)}
        print(record, flush=True)
        results.append(record)
    write_json(out, {"dataset": args.dataset, "queries": len(queries), "candidates": CANDIDATES,
                     "tokenization": "Sudachi SplitMode C の正規化形（Engine.tokenize と同じ）を空白で区切って索引する。検索は質問の語の OR",
                     "filter": "世代の絞り込みなし（全世代が有効なので結果は同じ）", "results": results})


if __name__ == "__main__":
    main()
