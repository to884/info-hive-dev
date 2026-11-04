"""暫定 PDF 質問と既存の固定セットを分けて、検索結果を集計する。"""
import json
import statistics
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
OUT = ROOT / "docs/research/rag-poc-2026-11-04"
questions = json.loads((Path(__file__).parent / "pdf-queries.json").read_text(encoding="utf-8"))
pdf_ids = {question["id"] for question in questions}
english_ids = {question["id"] for question in questions if question["sample"] in {4, 9}}
results = []
for file in sorted(OUT.glob("benchmark-*.json")):
    data = json.loads(file.read_text(encoding="utf-8"))
    backends = {}
    for backend, values in data["backends"].items():
        groups = {}
        for name, select in (
            ("fixed_wiki", lambda identity: identity not in pdf_ids),
            ("provisional_pdf", lambda identity: identity in pdf_ids),
            ("english_pdf_japanese_query", lambda identity: identity in english_ids),
            ("japanese_pdf", lambda identity: identity in pdf_ids - english_ids),
        ):
            rows = [row for row in values["measurements"] if select(row["id"])]
            if not rows:
                continue
            groups[name] = {
                "count": len(rows),
                "recall30": statistics.mean(row["recall30"] for row in rows),
                "ndcg10": statistics.mean(row["ndcg10"] for row in rows),
                "before_rerank_ndcg10": statistics.mean(row["before_ndcg10"] for row in rows),
                "rerank_improved": sum(row["ndcg10"] > row["before_ndcg10"] for row in rows),
                "rerank_worsened": sum(row["ndcg10"] < row["before_ndcg10"] for row in rows),
            }
        backends[backend] = groups
    results.append({"file": file.name, "query_count": data["query_count"], "backends": backends})
(OUT / "subgroup-results.json").write_text(json.dumps(results, ensure_ascii=False, indent=2), encoding="utf-8")
print(json.dumps(results, ensure_ascii=False))
