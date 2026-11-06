"""保存した動作点の順位から、db-bench-<dataset>.json の精度を、metric の現在の定義で計算し直す。

2026-11-06 のレビューで、融合した最大 400 チャンクを打ち切らずに metric に渡していたことが分かった。
動作点の選び方（厳密解に対する dense の recall）は精度の定義に関係しないので、動作点はそのままにする。
保存した順位がない掃引の各点と、絞り込みなしの行の精度は計算し直せないので、キーの名前を変えて旧定義と明記する。
"""
from __future__ import annotations

import argparse
import json

from common import OUT, WORK, full_mapping, full_queries, metric, read_json, rrf, write_json


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--dataset", required=True, choices=["subset", "full"])
    args = parser.parse_args()
    path = OUT / f"db-bench-{args.dataset}.json"
    report = read_json(path)
    labels = {int(row[0]): f"{row[2]}:p{row[3]}" for row in full_mapping()}
    queries = full_queries()
    for key, record in report["results"].items():
        if record.get("status") != "ok":
            continue
        name = key.replace(" × ", "__").replace(" ", "_").replace("+", "_")
        saved = json.loads((WORK / f"rankings/{args.dataset}/{name}.json").read_text(encoding="utf-8"))
        assert saved["knob"] == record["operating_point"]["knob"], key
        recalls, ndcgs = [], []
        by_id = {m["id"]: m for m in record["operating_point_measurements"]}
        for q, d, lx in zip(queries, saved["dense"], saved["lexical"]):
            if not q["expected"]:
                continue
            recall, ndcg = metric([labels[i] for i in rrf(d["ids"], lx["ids"])], q["expected"])
            by_id[q["id"]]["recall_at_30"], by_id[q["id"]]["ndcg_at_10"] = recall, ndcg
            recalls.append(recall)
            ndcgs.append(ndcg)
        point = record["operating_point"]
        point["recall_at_30_before_cutoff_fix"] = point.pop("recall_at_30_before_cutoff_fix", point["recall_at_30"])
        point["recall_at_30"] = sum(recalls) / len(recalls)
        point["ndcg_at_10"] = sum(ndcgs) / len(ndcgs)
        for entry in record["sweep"] + ([record["unfiltered"]] if record.get("unfiltered") else []):
            for field in ("recall_at_30", "ndcg_at_10"):
                if field in entry:
                    entry[f"{field}_before_cutoff_fix"] = entry.pop(field)
        print(f"{key:<44} {point['recall_at_30_before_cutoff_fix']:.3f} -> {point['recall_at_30']:.3f}")
    report["accuracy_definition"] = ("融合した順位の上位 30 チャンクで打ち切ってからページの重複を除き、上位 30 ページの再現率を測る"
                                     "（evaluate_mcp.py の limit=30 と同じ）。*_before_cutoff_fix は打ち切る前の旧定義の値")
    write_json(path, report)


if __name__ == "__main__":
    main()
