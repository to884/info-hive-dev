"""比べるベクター DB を同じ形で扱う。どれも dense と語彙の候補を chunk の id で返す。

語彙の側は、LanceDB は native FTS、Qdrant は Sudachi の語から作る BM25 の sparse ベクトル、
それ以外は SQLite の FTS5 を使う。どれも同じ Sudachi の分かち書きを入力にする。
"""
from __future__ import annotations

import contextlib
import math
import os
import shutil
import socket
import sqlite3
import subprocess
import time
import urllib.request
from collections import Counter
from pathlib import Path

import numpy as np

from common import WORK, create_fts5, directory_bytes, fts5_search

BATCH = 2048
# 語彙検索のエンジン。db_bench.py の --lexical で "tantivy" に切り替える（FTS5 を使う DB だけに効く）。
LEXICAL_ENGINE = "fts5"


def _fts5_build(path: Path, ids, terms) -> None:
    if LEXICAL_ENGINE == "tantivy":
        from lexical_bench import Tantivy
        Tantivy(path.parent).build(ids, terms)
        return
    connection = sqlite3.connect(path)
    connection.execute("PRAGMA journal_mode=OFF")
    create_fts5(connection)
    connection.executemany("INSERT INTO lexical(rowid,terms) VALUES(?,?)", zip(map(int, ids), terms))
    connection.commit()
    connection.execute("INSERT INTO lexical(lexical) VALUES('optimize')")
    connection.commit()
    connection.execute("VACUUM")
    connection.close()


class Backend:
    """name は表に出す名前。variant ごとに別の保存先を使う。knobs はクエリ時の調整つまみの掃引値。"""
    name = ""
    knobs: list = [None]
    knob_name = ""
    filter_native = False

    def __init__(self, folder: Path, dimension: int, variant: str):
        self.folder = folder
        self.dimension = dimension
        self.variant = variant

    def reset(self):
        if self.folder.exists():
            shutil.rmtree(self.folder)
        self.folder.mkdir(parents=True)

    def build(self, ids, vectors, terms, generations):
        raise NotImplementedError

    def open(self):
        pass

    def dense(self, vector, k, knob, allowed):
        raise NotImplementedError

    def lexical(self, terms, k, allowed):
        raise NotImplementedError

    def _lexical_search(self, terms, k):
        if LEXICAL_ENGINE != "tantivy":
            return fts5_search(self.connection, terms, k)
        if not hasattr(self, "_tantivy"):
            from lexical_bench import Tantivy
            self._tantivy = Tantivy(self.folder)
            self._tantivy.open()
        return self._tantivy.search(terms, k)

    def size(self) -> dict:
        return {"total_bytes": directory_bytes(self.folder)}

    def close(self):
        pass


class SqliteVec(Backend):
    """sqlite-vec の vec0 は総当たり。f32 と int8 はそのまま、bit は float32 の再スコアを付ける。"""
    name = "sqlite-vec"
    knob_name = "oversample"

    def __init__(self, folder, dimension, variant):
        super().__init__(folder, dimension, variant)
        # vec0 の KNN は k が 4,096 まで。候補 200 件 × 20 倍で 4,000 になる。
        self.knobs = [2, 5, 10, 20] if variant == "bit" else [None]
        self.filter_native = True
        self.path = folder / "index.sqlite"

    def _connect(self):
        import sqlite_vec
        connection = sqlite3.connect(self.path)
        connection.enable_load_extension(True)
        sqlite_vec.load(connection)
        connection.enable_load_extension(False)
        return connection

    def build(self, ids, vectors, terms, generations):
        self.reset()
        connection = self._connect()
        connection.execute("PRAGMA journal_mode=OFF")
        column = {"f32": f"float[{self.dimension}] distance_metric=cosine",
                  "int8": f"int8[{self.dimension}] distance_metric=cosine",
                  "bit": f"bit[{self.dimension}]"}[self.variant]
        connection.execute(f"CREATE VIRTUAL TABLE vectors USING vec0(embedding {column}, generation text)")
        if self.variant == "bit":
            connection.execute(f"CREATE VIRTUAL TABLE full_vectors USING vec0(embedding float[{self.dimension}] distance_metric=cosine)")
        # 量子化は numpy で先に行う。SQL の vec_quantize_* を 1 行ずつ呼ぶと 1 万件で数分かかった（M0）。
        wrap = {"f32": "?", "int8": "vec_int8(?)", "bit": "vec_bit(?)"}[self.variant]
        for start in range(0, len(ids), BATCH):
            stop = start + BATCH
            block = np.asarray(vectors[start:stop], dtype=np.float32)
            encoded = self._encode(block)
            rows = [(int(i), e, g) for i, e, g in zip(ids[start:stop], encoded, generations[start:stop])]
            connection.executemany(f"INSERT INTO vectors(rowid,embedding,generation) VALUES(?,{wrap},?)", rows)
            if self.variant == "bit":
                connection.executemany("INSERT INTO full_vectors(rowid,embedding) VALUES(?,?)", [(int(i), v.tobytes()) for i, v in zip(ids[start:stop], block)])
        if LEXICAL_ENGINE == "tantivy":
            from lexical_bench import Tantivy
            Tantivy(self.folder).build(ids, terms)
        else:
            create_fts5(connection)
            connection.executemany("INSERT INTO lexical(rowid,terms) VALUES(?,?)", zip(map(int, ids), terms))
            connection.commit()
            connection.execute("INSERT INTO lexical(lexical) VALUES('optimize')")
        connection.commit()
        connection.execute("VACUUM")
        connection.close()

    def _encode(self, block):
        if self.variant == "f32":
            return [v.tobytes() for v in block]
        if self.variant == "int8":
            return [v.tobytes() for v in np.clip(np.rint(block * 127), -127, 127).astype(np.int8)]
        return [v.tobytes() for v in np.packbits(block > 0, axis=1, bitorder="little")]

    def open(self):
        self.connection = self._connect()

    def _filter(self, allowed):
        if not allowed:
            return "", []
        return " AND generation IN (" + ",".join("?" * len(allowed)) + ")", list(allowed)

    def dense(self, vector, k, knob, allowed):
        clause, values = self._filter(allowed)
        query = np.asarray(vector, dtype=np.float32)[None, :]
        blob = query[0].tobytes()
        wrap = {"f32": "?", "int8": "vec_int8(?)", "bit": "vec_bit(?)"}[self.variant]
        encoded = self._encode(query)[0]
        if self.variant != "bit":
            sql = f"SELECT rowid FROM vectors WHERE embedding MATCH {wrap} AND k = ?{clause} ORDER BY distance"
            return [r[0] for r in self.connection.execute(sql, [encoded, k, *values])]
        candidates = [r[0] for r in self.connection.execute(
            f"SELECT rowid FROM vectors WHERE embedding MATCH vec_bit(?) AND k = ?{clause} ORDER BY distance",
            [encoded, k * knob, *values])]
        if not candidates:
            return []
        marks = ",".join("?" * len(candidates))
        rescored = self.connection.execute(
            f"SELECT rowid, vec_distance_cosine(embedding, ?) AS d FROM full_vectors WHERE rowid IN ({marks}) ORDER BY d LIMIT ?",
            [blob, *candidates, k]).fetchall()
        return [r[0] for r in rescored]

    def lexical(self, terms, k, allowed):
        return self._lexical_search(terms, k)

    def close(self):
        with contextlib.suppress(Exception):
            self.connection.close()


class Lance(Backend):
    """info-hive-rag の製品と同じ IVF_SQ、whitespace の FTS、generation の BITMAP。"""
    name = "LanceDB"
    knob_name = "nprobes"
    knobs = [5, 10, 20, 40, 80, 128]
    filter_native = True

    def build(self, ids, vectors, terms, generations):
        import lancedb
        import pyarrow as pa
        self.reset()
        db = lancedb.connect(self.folder / "lance")
        schema = pa.schema([("id", pa.int64()), ("generation", pa.string()), ("terms", pa.string()),
                            ("vector", pa.list_(pa.float32(), self.dimension))])
        table = db.create_table("chunks", schema=schema)
        steps, started = {}, time.perf_counter()

        def step(name):
            nonlocal started
            steps[name] = time.perf_counter() - started
            started = time.perf_counter()
        for start in range(0, len(ids), 50_000):
            stop = start + 50_000
            flat = pa.array(np.ascontiguousarray(vectors[start:stop]).reshape(-1), type=pa.float32())
            table.add(pa.table({"id": pa.array(ids[start:stop], type=pa.int64()), "generation": generations[start:stop],
                                "terms": terms[start:stop],
                                "vector": pa.FixedSizeListArray.from_arrays(flat, self.dimension)}, schema=schema))
        step("add")
        table.create_fts_index("terms", base_tokenizer="whitespace", stem=False, remove_stop_words=False, ascii_folding=False)
        step("fts")
        table.create_scalar_index("generation", index_type="BITMAP", replace=False)
        step("bitmap")
        partitions = max(1, min(4096, math.ceil(math.sqrt(len(ids)))))
        table.create_index(vector_column_name="vector", metric="cosine", index_type="IVF_SQ", num_partitions=partitions, name="vector_idx", replace=True)
        step("ivf_sq")
        from datetime import timedelta
        table.optimize(cleanup_older_than=timedelta(seconds=0), delete_unverified=True)
        step("optimize")
        self.build_steps = steps

    def open(self):
        import lancedb
        self.table = lancedb.connect(self.folder / "lance").open_table("chunks")

    def _where(self, allowed):
        return "generation IN (" + ",".join("'" + g + "'" for g in allowed) + ")" if allowed else None

    def dense(self, vector, k, knob, allowed):
        query = self.table.search(np.asarray(vector, dtype=np.float32)).distance_type("cosine")
        where = self._where(allowed)
        if where:
            query = query.where(where, prefilter=True)
        return [r["id"] for r in query.nprobes(knob).refine_factor(4).select(["id"]).limit(k).to_list()]

    def lexical(self, terms, k, allowed):
        if not terms:
            return []
        query = self.table.search(terms, query_type="fts", fts_columns="terms")
        where = self._where(allowed)
        if where:
            query = query.where(where, prefilter=True)
        return [r["id"] for r in query.select(["id"]).limit(k).to_list()]


def _free_port():
    with socket.socket() as sock:
        sock.bind(("127.0.0.1", 0))
        return sock.getsockname()[1]


class Qdrant(Backend):
    """Qdrant サーバーを専用のポートで起動する。語彙は Sudachi の語から作る BM25 の sparse ベクトル（IDF は Qdrant 側）。"""
    name = "Qdrant"
    knob_name = "hnsw_ef"
    knobs = [16, 64, 256, 512, 1024, 2048, 4096]
    filter_native = True
    binary = WORK / "qdrant-bin/qdrant.exe"
    k1, b = 1.2, .75

    def _start(self):
        import yaml
        from qdrant_client import QdrantClient
        self.http, self.grpc = _free_port(), _free_port()
        config = {"storage": {"storage_path": str(self.folder / "storage"), "on_disk_payload": True},
                  "service": {"host": "127.0.0.1", "http_port": self.http, "grpc_port": self.grpc},
                  "telemetry_disabled": True, "log_level": "WARN"}
        # 既定ではセグメントを CPU 数だけ作り、それぞれ 32 MB ずつ事前に確保する。1 万件で 1 GB になった（M0）。
        config["storage"]["optimizers"] = {"default_segment_number": 2}
        config["storage"]["wal"] = {"wal_capacity_mb": 8, "wal_segments_ahead": 0}
        path = self.folder / "qdrant.yaml"
        path.write_text(yaml.safe_dump(config), encoding="utf-8")
        self.log = (self.folder / "qdrant.log").open("a", encoding="utf-8")
        env = {**os.environ, "QDRANT__STORAGE__PERFORMANCE__MAX_SEARCH_THREADS": "4", "QDRANT__STORAGE__PERFORMANCE__MAX_OPTIMIZATION_THREADS": "4"}
        self.process = subprocess.Popen([str(self.binary), "--config-path", str(path)], cwd=self.folder, stdout=self.log, stderr=self.log, env=env,
                                        creationflags=subprocess.CREATE_NO_WINDOW if os.name == "nt" else 0)
        for _ in range(300):
            try:
                with urllib.request.urlopen(f"http://127.0.0.1:{self.http}/readyz", timeout=.2):
                    break
            except Exception:
                time.sleep(.1)
        else:
            raise TimeoutError("Qdrant が起動しません。")
        self.client = QdrantClient(host="127.0.0.1", port=self.http, grpc_port=self.grpc, prefer_grpc=True, timeout=600)

    def _stop(self):
        with contextlib.suppress(Exception):
            self.client.close()
        with contextlib.suppress(Exception):
            self.process.terminate()
            self.process.wait(timeout=30)
        with contextlib.suppress(Exception):
            self.log.close()

    def _vocabulary(self):
        import json
        return json.loads((self.folder / "vocabulary.json").read_text(encoding="utf-8"))

    def build(self, ids, vectors, terms, generations):
        import json
        from qdrant_client import models as qm
        self.reset()
        vocabulary = {}
        tokenized = [t.split() for t in terms]
        for words in tokenized:
            for word in words:
                vocabulary.setdefault(word, len(vocabulary))
        average = sum(map(len, tokenized)) / max(1, len(tokenized))
        (self.folder / "vocabulary.json").write_text(json.dumps(vocabulary, ensure_ascii=False), encoding="utf-8")
        self._start()
        try:
            quantization = {"f32": None,
                            "sq": qm.ScalarQuantization(scalar=qm.ScalarQuantizationConfig(type=qm.ScalarType.INT8, always_ram=True)),
                            "bq": qm.BinaryQuantization(binary=qm.BinaryQuantizationConfig(always_ram=True))}[self.variant]
            self.client.create_collection(
                "chunks",
                vectors_config={"dense": qm.VectorParams(size=self.dimension, distance=qm.Distance.COSINE, on_disk=self.variant != "f32")},
                sparse_vectors_config={"bm25": qm.SparseVectorParams(modifier=qm.Modifier.IDF, index=qm.SparseIndexParams(on_disk=True))},
                hnsw_config=qm.HnswConfigDiff(m=16, ef_construct=100),
                quantization_config=quantization,
                optimizers_config=qm.OptimizersConfigDiff(indexing_threshold=0))
            self.client.create_payload_index("chunks", "generation", qm.PayloadSchemaType.KEYWORD)
            for start in range(0, len(ids), 1000):
                points = []
                for i in range(start, min(start + 1000, len(ids))):
                    counts = Counter(tokenized[i])
                    length = len(tokenized[i])
                    indices = [vocabulary[w] for w in counts]
                    values = [c * (self.k1 + 1) / (c + self.k1 * (1 - self.b + self.b * length / average)) for c in counts.values()]
                    sparse = {"bm25": qm.SparseVector(indices=indices, values=values)} if indices else {}
                    points.append(qm.PointStruct(id=int(ids[i]), vector={"dense": vectors[i].tolist(), **sparse}, payload={"generation": generations[i]}))
                self.client.upsert("chunks", points, wait=False)
            # 一括投入の後で HNSW を作らせ、索引化が終わるまで待つ。
            self.client.update_collection("chunks", optimizer_config=qm.OptimizersConfigDiff(indexing_threshold=10000))
            while True:
                info = self.client.get_collection("chunks")
                if info.status == qm.CollectionStatus.GREEN and (info.indexed_vectors_count or 0) >= len(ids) * .99:
                    break
                time.sleep(2)
        finally:
            self._stop()

    def open(self):
        self.vocabulary = self._vocabulary()
        self._start()

    def _filter(self, allowed):
        from qdrant_client import models as qm
        if not allowed:
            return None
        return qm.Filter(must=[qm.FieldCondition(key="generation", match=qm.MatchAny(any=list(allowed)))])

    def dense(self, vector, k, knob, allowed):
        from qdrant_client import models as qm
        quant = None if self.variant == "f32" else qm.QuantizationSearchParams(rescore=True, oversampling=2.0)
        points = self.client.query_points("chunks", query=np.asarray(vector, dtype=np.float32).tolist(), using="dense", limit=k,
                                          query_filter=self._filter(allowed),
                                          search_params=qm.SearchParams(hnsw_ef=knob, quantization=quant), with_payload=False).points
        return [p.id for p in points]

    def lexical(self, terms, k, allowed):
        from qdrant_client import models as qm
        indices = sorted({self.vocabulary[w] for w in terms.split() if w in self.vocabulary})
        if not indices:
            return []
        points = self.client.query_points("chunks", query=qm.SparseVector(indices=indices, values=[1.0] * len(indices)), using="bm25",
                                          limit=k, query_filter=self._filter(allowed), with_payload=False).points
        return [p.id for p in points]

    def size(self):
        storage = self.folder / "storage"
        return {"total_bytes": directory_bytes(storage) + (self.folder / "vocabulary.json").stat().st_size}

    def close(self):
        self._stop()


class QdrantLocal(Backend):
    """qdrant-client の local mode（プロセス内、純 Python）。規模に耐えるかだけを見る。"""
    name = "Qdrant local"
    filter_native = True

    def build(self, ids, vectors, terms, generations):
        from qdrant_client import QdrantClient, models as qm
        self.reset()
        client = QdrantClient(path=str(self.folder / "local"))
        client.create_collection("chunks", vectors_config=qm.VectorParams(size=self.dimension, distance=qm.Distance.COSINE))
        for start in range(0, len(ids), 1000):
            client.upsert("chunks", [qm.PointStruct(id=int(ids[i]), vector=vectors[i].tolist(), payload={"generation": generations[i]})
                                     for i in range(start, min(start + 1000, len(ids)))])
        client.close()
        _fts5_build(self.folder / "lexical.sqlite", ids, terms)

    def open(self):
        from qdrant_client import QdrantClient
        self.client = QdrantClient(path=str(self.folder / "local"))
        self.connection = sqlite3.connect(self.folder / "lexical.sqlite")

    def dense(self, vector, k, knob, allowed):
        from qdrant_client import models as qm
        flt = qm.Filter(must=[qm.FieldCondition(key="generation", match=qm.MatchAny(any=list(allowed)))]) if allowed else None
        return [p.id for p in self.client.query_points("chunks", query=np.asarray(vector).tolist(), limit=k, query_filter=flt).points]

    def lexical(self, terms, k, allowed):
        return self._lexical_search(terms, k)

    def close(self):
        with contextlib.suppress(Exception):
            self.client.close()
            self.connection.close()


class Usearch(Backend):
    """usearch の HNSW を単一ファイルに保存し、検索時はメモリ写像で開く。語彙は FTS5。"""
    name = "usearch"
    knob_name = "expansion_search"
    knobs = [16, 64, 256, 512, 1024, 2048]

    def build(self, ids, vectors, terms, generations):
        from usearch.index import Index
        self.reset()
        index = Index(ndim=self.dimension, metric="cos", dtype=self.variant, connectivity=16, expansion_add=128)
        index.add(np.asarray(ids, dtype=np.uint64), np.asarray(vectors, dtype=np.float32), threads=4)
        index.save(str(self.folder / "vectors.usearch"))
        _fts5_build(self.folder / "lexical.sqlite", ids, terms)

    def open(self):
        from usearch.index import Index
        self.index = Index.restore(str(self.folder / "vectors.usearch"), view=True)
        self.connection = sqlite3.connect(self.folder / "lexical.sqlite")

    def dense(self, vector, k, knob, allowed):
        self.index.expansion_search = knob
        matches = self.index.search(np.asarray(vector, dtype=np.float32), k, threads=1)
        return [int(key) for key in matches.keys]

    def lexical(self, terms, k, allowed):
        return self._lexical_search(terms, k)

    def close(self):
        with contextlib.suppress(Exception):
            self.connection.close()


class Faiss(Backend):
    """FAISS の IVF + int8 スカラー量子化、または HNSW（float32）。正規化済みなので内積で cosine になる。語彙は FTS5。"""
    name = "FAISS"

    def __init__(self, folder, dimension, variant):
        super().__init__(folder, dimension, variant)
        self.knob_name = "nprobe" if variant == "ivf_sq8" else "efSearch"
        self.knobs = [5, 10, 20, 40, 80, 128] if variant == "ivf_sq8" else [16, 64, 256, 512, 1024, 2048]

    def build(self, ids, vectors, terms, generations):
        import faiss
        faiss.omp_set_num_threads(4)
        self.reset()
        data = np.ascontiguousarray(vectors, dtype=np.float32)
        if self.variant == "ivf_sq8":
            lists = max(1, min(4096, math.ceil(math.sqrt(len(ids)))))
            quantizer = faiss.IndexFlatIP(self.dimension)
            index = faiss.IndexIVFScalarQuantizer(quantizer, self.dimension, lists, faiss.ScalarQuantizer.QT_8bit, faiss.METRIC_INNER_PRODUCT)
            index.train(data[np.random.default_rng(0).choice(len(data), min(len(data), 256 * lists), replace=False)])
        else:
            index = faiss.IndexHNSWFlat(self.dimension, 32, faiss.METRIC_INNER_PRODUCT)
            index.hnsw.efConstruction = 100
        wrapped = faiss.IndexIDMap2(index)
        wrapped.add_with_ids(data, np.asarray(ids, dtype=np.int64))
        faiss.write_index(wrapped, str(self.folder / "vectors.faiss"))
        _fts5_build(self.folder / "lexical.sqlite", ids, terms)

    def open(self):
        import faiss
        faiss.omp_set_num_threads(1)
        # IVF をメモリ写像で開く IO_FLAG_MMAP は IndexIDMap2 で包んだ索引を読めないので、全体を読み込む。
        self.index = faiss.read_index(str(self.folder / "vectors.faiss"))
        self.inner = faiss.downcast_index(self.index.index)
        self.connection = sqlite3.connect(self.folder / "lexical.sqlite")

    def dense(self, vector, k, knob, allowed):
        if self.variant == "ivf_sq8":
            self.inner.nprobe = knob
        else:
            self.inner.hnsw.efSearch = knob
        _, labels = self.index.search(np.asarray(vector, dtype=np.float32)[None, :], k)
        return [int(i) for i in labels[0] if i >= 0]

    def lexical(self, terms, k, allowed):
        return self._lexical_search(terms, k)

    def close(self):
        with contextlib.suppress(Exception):
            self.connection.close()


class Chroma(Backend):
    """Chroma の組み込み版（HNSW）。ローカル版に BM25 がないので語彙は FTS5。"""
    name = "Chroma"
    knob_name = "ef_search"
    knobs = [16, 64, 256, 512, 1024, 2048]
    filter_native = True

    def build(self, ids, vectors, terms, generations):
        import chromadb
        self.reset()
        client = chromadb.PersistentClient(path=str(self.folder / "chroma"), settings=chromadb.Settings(anonymized_telemetry=False))
        collection = client.create_collection("chunks", configuration={"hnsw": {"space": "cosine", "ef_construction": 100, "max_neighbors": 16}})
        step = min(5000, client.get_max_batch_size())
        for start in range(0, len(ids), step):
            stop = start + step
            collection.add(ids=[str(int(i)) for i in ids[start:stop]], embeddings=np.asarray(vectors[start:stop], dtype=np.float32),
                           metadatas=[{"generation": g} for g in generations[start:stop]])
        del collection, client
        _fts5_build(self.folder / "lexical.sqlite", ids, terms)

    def open(self):
        import chromadb
        self.client = chromadb.PersistentClient(path=str(self.folder / "chroma"), settings=chromadb.Settings(anonymized_telemetry=False))
        self.collection = self.client.get_collection("chunks")
        self.knob = None
        self.connection = sqlite3.connect(self.folder / "lexical.sqlite")

    def dense(self, vector, k, knob, allowed):
        if knob != self.knob:
            # 実行中の modify はプロセス内の索引に反映されない。キャッシュを捨てて開き直す（M0 の確認）。
            import chromadb
            from chromadb.api.shared_system_client import SharedSystemClient
            self.collection.modify(configuration={"hnsw": {"ef_search": knob}})
            del self.collection, self.client
            SharedSystemClient.clear_system_cache()
            self.client = chromadb.PersistentClient(path=str(self.folder / "chroma"), settings=chromadb.Settings(anonymized_telemetry=False))
            self.collection = self.client.get_collection("chunks")
            self.knob = knob
        where = {"generation": {"$in": list(allowed)}} if allowed else None
        found = self.collection.query(query_embeddings=[np.asarray(vector, dtype=np.float32)], n_results=k, where=where, include=[])
        return [int(i) for i in found["ids"][0]]

    def lexical(self, terms, k, allowed):
        return self._lexical_search(terms, k)

    def close(self):
        with contextlib.suppress(Exception):
            self.connection.close()


# 名前、クラス、variant。M0 で動かないものはここから外す。
CANDIDATES = [
    ("sqlite-vec f32", SqliteVec, "f32"),
    ("sqlite-vec int8", SqliteVec, "int8"),
    ("sqlite-vec bit+rescore", SqliteVec, "bit"),
    ("LanceDB IVF_SQ", Lance, "ivf_sq"),
    ("Qdrant HNSW f32", Qdrant, "f32"),
    ("Qdrant HNSW SQ", Qdrant, "sq"),
    ("Qdrant HNSW BQ", Qdrant, "bq"),
    ("Qdrant local", QdrantLocal, "f32"),
    ("usearch HNSW f16", Usearch, "f16"),
    ("usearch HNSW i8", Usearch, "i8"),
    ("FAISS IVF_SQ8", Faiss, "ivf_sq8"),
    ("FAISS HNSW", Faiss, "hnsw"),
    ("Chroma HNSW", Chroma, "hnsw"),
]
