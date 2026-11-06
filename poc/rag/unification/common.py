"""埋め込みモデルとベクター DB の統一を比べる PoC の共通部品。配布対象ではない。"""
from __future__ import annotations

import hashlib
import json
import math
import os
import sqlite3
import time
import unicodedata
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
# 測定データは Git の管理外にある。作業ツリー（.claude/worktrees/...）から動かすときは、
# INFO_HIVE_POC_DATA でメインのチェックアウトの .rag-poc-data を指す。出力先（OUT）は ROOT のまま。
POC_DATA = Path(os.environ.get("INFO_HIVE_POC_DATA", ROOT / ".rag-poc-data"))
WORK = POC_DATA / "unification-20261105"
FULL = POC_DATA / "full-20261104"
NATURAL = POC_DATA / "natural-20261104"
MODEL_CACHE = POC_DATA / "model-cache"
OUT = ROOT / "docs/research/embedding-backend-unification-2026-11-05"
SUBSET_ROWS = 100_000
THREADS = 4

# 記号、Hugging Face の ID、固定した commit、次元、接頭辞、モデルが受け付ける最大トークン数。
MODELS = {
    "E-s": {"id": "intfloat/multilingual-e5-small", "revision": "614241f622f53c4eeff9890bdc4f31cfecc418b3", "dimension": 384,
            "query": "query: ", "passage": "passage: ", "max_tokens": 512},
    "E-l": {"id": "intfloat/multilingual-e5-large", "revision": "3d7cfbdacd47fdda877c5cd8a79fbcc4f2a574f3", "dimension": 1024,
            "query": "query: ", "passage": "passage: ", "max_tokens": 512},
    "R-30": {"id": "cl-nagoya/ruri-v3-30m", "revision": "24899e5de370b56d179604a007c0d727bf144504", "dimension": 256,
             "query": "検索クエリ: ", "passage": "検索文書: ", "max_tokens": 8192},
    "R-130": {"id": "cl-nagoya/ruri-v3-130m", "revision": "e3114c6ee10dbab8b4b235fbc6dcf9dd4d5ac1a6", "dimension": 512,
              "query": "検索クエリ: ", "passage": "検索文書: ", "max_tokens": 8192},
    "R-310": {"id": "cl-nagoya/ruri-v3-310m", "revision": "18b60fb8c2b9df296fb4212bb7d23ef94e579cd3", "dimension": 768,
              "query": "検索クエリ: ", "passage": "検索文書: ", "max_tokens": 8192},
    "S-ja": {"id": "hotchpotch/static-embedding-japanese", "revision": "95b3d9c80a7ccf604e2b5daee7b1b3eed6b1a9d3", "dimension": 1024,
             "query": "", "passage": "", "max_tokens": 1_000_000},
}


def limit_threads(count: int = THREADS) -> None:
    for name in ("OMP_NUM_THREADS", "OPENBLAS_NUM_THREADS", "MKL_NUM_THREADS", "RAYON_NUM_THREADS", "ORT_NUM_THREADS"):
        os.environ[name] = str(count)


def write_json(path: Path, value) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_suffix(path.suffix + ".tmp")
    temporary.write_text(json.dumps(value, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    temporary.replace(path)


def read_json(path: Path):
    return json.loads(path.read_text(encoding="utf-8"))


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1 << 20), b""):
            digest.update(block)
    return digest.hexdigest()


RESULT_LIMIT = 30


def metric(labels, expected):
    """poc/rag/remaining/evaluate_mcp.py の metric と同じ定義。上位 30 のページ再現率と上位 10 の nDCG。

    evaluate_mcp.py は limit=30 で検索した 30 チャンクを評価する。それに合わせ、先に上位 30 チャンクで打ち切ってから
    ページの重複を除く。打ち切らずに融合した最大 400 チャンクを渡すと、31 位以降のチャンクのページも数えてしまう。
    """
    relevant = set(expected)
    unique = list(dict.fromkeys(labels[:RESULT_LIMIT]))
    recall = len(set(unique[:30]) & relevant) / len(relevant)
    dcg = sum((label in relevant) / math.log2(i + 2) for i, label in enumerate(unique[:10]))
    ideal = sum(1 / math.log2(i + 2) for i in range(min(len(relevant), 10)))
    return recall, dcg / ideal


def p95(values):
    ordered = sorted(values)
    if not ordered:
        return None
    p = (len(ordered) - 1) * .95
    i = int(p)
    return ordered[i] + (ordered[min(i + 1, len(ordered) - 1)] - ordered[i]) * (p - i)


def rrf(*rankings, k: int = 60):
    """info-hive-rag/scripts/rag_index.py の Engine.search と同じ順位融合。"""
    scores = {}
    for ranking in rankings:
        for rank, key in enumerate(ranking, 1):
            scores[key] = scores.get(key, 0.0) + 1 / (k + rank)
    return sorted(scores, key=lambda key: (-scores[key], key))


class Tokenizer:
    """info-hive-rag/scripts/rag_index.py の Engine.tokenize と同じ Sudachi の分かち書き。"""

    def __init__(self):
        from sudachipy import dictionary
        self._tokenizer = dictionary.Dictionary().create()

    def __call__(self, text: str) -> str:
        from sudachipy import tokenizer
        normalized = unicodedata.normalize("NFKC", text).lower()
        return " ".join(word.normalized_form().lower() for word in
                        self._tokenizer.tokenize(normalized, tokenizer.Tokenizer.SplitMode.C)
                        if word.surface().strip() and word.part_of_speech()[0] != "補助記号")


# FTS5 の ascii トークナイザは ASCII 以外を語の文字として扱う。ASCII の記号も語の文字にすると、
# 空白だけで区切る LanceDB の whitespace トークナイザと同じ分割になる。
# 引用符の 2 文字は指定の入れ子が崩れるので区切りとして残す（差は README に書く）。
_ASCII_SYMBOLS = "".join(chr(c) for c in range(33, 127) if not chr(c).isalnum() and chr(c) not in "'\"")
FTS5_TOKENIZE = "ascii tokenchars '" + _ASCII_SYMBOLS + "'"
os.environ.setdefault("LANCE_LOG", "error")


def fts5_query(terms: str) -> str:
    unique = list(dict.fromkeys(term for term in terms.split() if term))
    return " OR ".join('"' + term.replace('"', '""') + '"' for term in unique)


def create_fts5(connection: sqlite3.Connection, table: str = "lexical") -> None:
    connection.execute(f"CREATE VIRTUAL TABLE {table} USING fts5(terms, tokenize=\"{FTS5_TOKENIZE}\")")


def fts5_search(connection: sqlite3.Connection, terms: str, limit: int, table: str = "lexical") -> list[int]:
    query = fts5_query(terms)
    if not query:
        return []
    return [row[0] for row in connection.execute(
        f"SELECT rowid FROM {table} WHERE {table} MATCH ? ORDER BY rank LIMIT ?", (query, limit))]


def load_natural():
    data = read_json(NATURAL / "corpus.json")
    return data["rows"], data["queries"]


def full_mapping():
    """poc/rag/remaining/full_ann_quality.py と同じく、完了した文書のチャンクと埋め込みの位置を対応づける。"""
    db = sqlite3.connect(FULL / "corpus.sqlite")
    db.execute("ATTACH DATABASE ? AS embeddings", (str(FULL / "embeddings-130m/ledger.sqlite"),))
    rows = db.execute("SELECT c.id,e.position,c.doc_id,c.page FROM chunks c JOIN embeddings.vectors e ON e.id=c.id "
                      "WHERE EXISTS (SELECT 1 FROM documents d WHERE d.doc_id=c.doc_id AND d.status='completed') ORDER BY c.id").fetchall()
    db.close()
    return rows


def full_queries():
    return read_json(FULL / "corpus.json")["queries"]


def subset_ids():
    """正解ラベルを持つ文書を必ず含め、残りを固定の乱数で文書単位に加えて 100,000 行前後にする。"""
    target = WORK / "subset-ids.json"
    if target.exists():
        return read_json(target)["ids"]
    import random
    mapping = full_mapping()
    by_doc = {}
    for chunk_id, _, doc_id, _ in mapping:
        by_doc.setdefault(doc_id, []).append(chunk_id)
    required = sorted({label.rsplit(":p", 1)[0] for q in full_queries() for label in q["expected"]})
    chosen = list(required)
    others = sorted(set(by_doc) - set(required))
    random.Random(20261105).shuffle(others)
    total = sum(len(by_doc[d]) for d in chosen)
    for doc_id in others:
        if total >= SUBSET_ROWS:
            break
        chosen.append(doc_id)
        total += len(by_doc[doc_id])
    ids = sorted(chunk_id for d in chosen for chunk_id in by_doc[d])
    write_json(target, {"seed": 20261105, "required_documents": required, "documents": len(chosen), "rows": len(ids), "ids": ids})
    return ids


class Timer:
    def __enter__(self):
        self.started = time.perf_counter()
        return self

    def __exit__(self, *_):
        self.seconds = time.perf_counter() - self.started


def directory_bytes(path: Path) -> int:
    if path.is_file():
        return path.stat().st_size
    return sum(p.stat().st_size for p in path.rglob("*") if p.is_file())
