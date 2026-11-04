"""既存の固定正解セットと実 PDF の抽出結果から、比較用の同一入力を作る。"""
import hashlib
import json
import os
import random
import re
import unicodedata
import argparse
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
parser = argparse.ArgumentParser()
parser.add_argument("--include-pdf", action="store_true")
args = parser.parse_args()
WORK = Path(os.environ["LOCALAPPDATA"]) / "info-hive/rag-poc/2026-11-04"
corpus = []
for path in sorted((ROOT / "info-hive-wiki/eval/retrieval/ja/corpus/wiki").rglob("*.md")):
    if path.name == "SCHEMA.md":
        continue
    try:
        text = path.read_text(encoding="utf-8-sig")
    except UnicodeError:
        continue
    text = re.sub(r"\A---.*?\n---\s*", "", text, flags=re.S)
    for offset in range(0, len(text), 700):
        chunk = text[offset:offset + 800].strip()
        if chunk:
            corpus.append({"label": unicodedata.normalize("NFC", path.stem), "text": chunk, "source": "fixed_wiki"})
fixed_count = len(corpus)
real_chunks = []
page_lookup = {}
for line in (WORK / "pages.jsonl").open(encoding="utf-8"):
    page = json.loads(line)
    page_lookup[(page["sample"], page["page"])] = page["text"]
    text = re.sub(r"[ \t]+", " ", page["text"]).strip()
    for offset in range(0, len(text), 700):
        chunk = text[offset:offset + 800].strip()
        if len(chunk) >= 100 and chunk.count("\ufffd") < 2:
            real_chunks.append({"label": f"sample-{page['sample']}:p{page['page']}", "page": page["page"], "text": chunk, "source": "real_pdf"})
random.Random(20261104).shuffle(real_chunks)
pdf_queries = []
if args.include_pdf:
    pdf_queries = json.loads((ROOT / "poc/rag/pdf-queries.json").read_text(encoding="utf-8"))
    for query in pdf_queries:
        text = page_lookup[(query["sample"], query["page"])]
        assert query["evidence"] in text, query["id"]
        position = text.index(query["evidence"])
        start = max(0, position - 250)
        corpus.append({"label": query["expected"][0], "page": query["page"], "text": text[start:start + 800], "source": "real_pdf_gold"})
corpus.extend(real_chunks[:512])
queries = json.loads((ROOT / "info-hive-wiki/eval/retrieval/ja/queries.json").read_text(encoding="utf-8"))
queries.extend(pdf_queries)
unique = {}
for row in corpus:
    unique.setdefault((row["label"], row["text"]), row)
corpus = list(unique.values())
labels = {row["label"] for row in corpus}
assert all(set(query["expected"]) <= labels for query in queries), "正解ラベルがコーパスにありません。"
data = {"corpus": corpus, "queries": queries, "fixed_chunks": fixed_count, "real_chunks": min(512, len(real_chunks)),
        "all_real_chunks": len(real_chunks), "seed": 20261104, "pdf_queries":len(pdf_queries),
        "dataset_version":2 if args.include_pdf else 1}
serialized = json.dumps(data, ensure_ascii=False)
(WORK / "corpus.json").write_text(serialized, encoding="utf-8")
print(json.dumps({"sha256": hashlib.sha256(serialized.encode()).hexdigest(), "chunks": len(corpus), "fixed_chunks": fixed_count,
                  "queries": len(queries), "positive_queries": sum(bool(q['expected']) for q in queries), "all_real_chunks": len(real_chunks)}))
