"""実測 JSON から比較表を再生成する。"""
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
OUT = ROOT / "docs/research/rag-poc-2026-11-04"
rows = []
for file in sorted(OUT.glob("benchmark-*.json")):
    data = json.loads(file.read_text(encoding="utf-8"))
    rows.append({"file": file.name, "model": data["model"].split("-")[-1],
                 "reranker":data["reranker"].split("/")[-1],"backend":data.get("reranker_backend","fp32"),
                 "rerank_limit":data.get("rerank_limit",30),"questions":data["query_count"],"chunks":data["chunks"],
                 "corpus_sha256":data.get("corpus_sha256","599a1afe8834a10f17f0c33461b1df51ca5a2dd94310f5089f31a074c8557839"),
                 "embedding_seconds":data["embedding_seconds"],"chunks_per_second":data["chunks_per_second"],
                 "python_peak_gib":data["python_peak_rss_bytes"]/(1024**3),
                 "lancedb":{k:v for k,v in data["backends"]["lancedb"].items() if k!="measurements"},
                 "qdrant":{k:v for k,v in data["backends"]["qdrant"].items() if k!="measurements"}})
(OUT / "summary.json").write_text(json.dumps(rows,ensure_ascii=False,indent=2),encoding="utf-8")
lines = ["# 検索の実測比較", "", "同じコーパス SHA と質問数の行だけを直接比較する。", "", "| 入力 | 埋め込み | リランカー | 件数 | Python peak GiB | LanceDB p95 ms | Qdrant p95 ms | Recall@30 | nDCG@10 |", "| --- | --- | --- | --- | --- | --- | --- | --- | --- |"]
for row in rows:
    lines.append(f"| [{row['questions']} 問 / {row['chunks']} チャンク]({row['file']}) | Ruri {row['model']} | {row['reranker']} {row['backend']} | {row['rerank_limit']} | {row['python_peak_gib']:.2f} | {row['lancedb']['p95_ms']:.1f} | {row['qdrant']['p95_ms']:.1f} | {row['lancedb']['recall30']:.4f} | {row['lancedb']['ndcg10']:.4f} |")
lines += ["", "Recall と nDCG はこの表では LanceDB の値。Qdrant の個別値は各 JSON を参照。", "", "## 同じ 107 問の埋め込み速度", "", "| モデル | チャンク数 | 秒 | チャンク / 秒 |", "| --- | --- | --- | --- |"]
seen = set()
for row in rows:
    if row['questions']!=107 or row['model'] in seen: continue
    seen.add(row['model'])
    lines.append(f"| {row['model']} | {row['chunks']} | {row['embedding_seconds']:.2f} | {row['chunks_per_second']:.2f} |")
(OUT / "measurements.md").write_text("\n".join(lines)+"\n",encoding="utf-8")
print(json.dumps(rows,ensure_ascii=False))
