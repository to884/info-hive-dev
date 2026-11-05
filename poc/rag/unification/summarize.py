"""各計測の JSON から、組ごとの 3 つのスコア（検索スピード、DB サイズ、精度）と採用の判定を作る。

- 検索スピード = 製品の CPU 実行系でのクエリ埋め込みの p95 + 動作点での DB の p95（dense + 語彙 + RRF）。
  2 つの p95 の和なので、1 問ごとの合計の p95 より大きめに出る。
- DB サイズ = ベクトル索引 + 全文索引 + 最小限のメタデータ（id、世代）のディスク容量。
- 精度 = 端から端までの、60 問のページ再現率@30。
点数: 3 つとも「最良を 10 点、閾値を 3 点」として間を補間し、下限は 1 点とする。速度と容量は値が 2 桁以上に散らばるので
対数で補間し、精度は直線で補間する。閾値は検索 1 秒（件数によらない）、容量 30 GB × 件数 / 761,915（部分集合では約 3.96 GB）、
精度は現行（R-130 × LanceDB）− 0.05。閾値を外れたものは 3 点以下にする。最良は表の全行（閾値を外れた行も含む）から取る。
最初の実装では速度と容量を 10 × 最良 / 値 としていたが、閾値を大きく下回る値どうし（17 ms と 58 ms）にも 7 点の差が付き、
「閾値の内側で余裕がある」と「閾値すれすれ」を区別できなかったので置き換えた。
dense の recall@30（厳密解に対する）が目標 0.95 に届かなかった組は、有効な動作点がないので「3 つとも 7 点以上」と段階 2 の候補から外す。
60 問では 1 問の違いが再現率 0.017 にあたる。精度の 1〜2 点の差は 1 問の差と同じ程度でしかない。
"""
from __future__ import annotations

import math

from common import MODELS, OUT, read_json, write_json

SPEED_LIMIT_MS = 1000
SIZE_LIMIT_BYTES = 30 * 1024 ** 3
ACCURACY_MARGIN = .05
CURRENT = "R-130 × LanceDB IVF_SQ"
FULL_ROWS = 761_915


def log_score(value, best, limit):
    """値が best なら 10 点、limit なら 3 点。対数で補間し、1〜10 に収める。"""
    if limit <= best:
        return 10.0
    return max(1.0, min(10.0, 3 + 7 * (math.log(limit) - math.log(value)) / (math.log(limit) - math.log(best))))


def ratio_score(value, best):
    """置き換える前の点（参考に残す）。"""
    return round(max(1.0, 10 * best / value), 1)


def scores(rows, baseline_accuracy):
    best_speed = min(r["speed_ms"] for r in rows)
    best_size = min(r["size_bytes"] for r in rows)
    best_accuracy = max(r["accuracy"] for r in rows)
    for r in rows:
        size_limit = SIZE_LIMIT_BYTES * r["rows"] / FULL_ROWS
        speed = log_score(r["speed_ms"], best_speed, SPEED_LIMIT_MS)
        size = log_score(r["size_bytes"], best_size, size_limit)
        floor = baseline_accuracy - ACCURACY_MARGIN
        accuracy = max(1.0, min(10.0, 3 + 7 * (r["accuracy"] - floor) / max(1e-9, best_accuracy - floor)))
        r["ratio_score"] = {"speed": ratio_score(r["speed_ms"], best_speed), "size": ratio_score(r["size_bytes"], best_size)}
        r["size_limit_bytes"] = size_limit
        if r["speed_ms"] > SPEED_LIMIT_MS:
            speed = min(speed, 3.0)
        if r["size_bytes"] > size_limit:
            size = min(size, 3.0)
        if r["accuracy"] < baseline_accuracy - ACCURACY_MARGIN:
            accuracy = min(accuracy, 3.0)
        r["score"] = {"speed": round(speed, 1), "size": round(size, 1), "accuracy": round(accuracy, 1)}
        r["score"]["minimum"] = min(r["score"].values())
        r["all_high"] = r["score"]["minimum"] >= 7 and r["target_reached"]
    return rows


def tantivy_variants(dataset, rows, parity):
    """FTS5 を使う組について、語彙検索を Tantivy に置き換えた組を作る。

    dense の順位と時間は各組の実測、語彙の順位と時間は lexical_bench.py の Tantivy の実測。1 問ごとに足して p95 を取り、
    融合し直した順位で精度を測る。容量は FTS5 の実測の容量を引いて Tantivy の容量を足す（換算）。
    """
    import json
    from common import WORK, full_mapping, full_queries, metric, p95, rrf
    lexical_path = WORK / f"rankings/{dataset}/lexical__Tantivy.json"
    bench_path = OUT / f"lexical-bench-{dataset}.json"
    if not lexical_path.exists() or not bench_path.exists():
        return []
    engines = {r["engine"]: r for r in read_json(bench_path)["results"]}
    tantivy = json.loads(lexical_path.read_text(encoding="utf-8"))["lexical"]
    labels = {int(row[0]): f"{row[2]}:p{row[3]}" for row in full_mapping()}
    queries = full_queries()
    made = []
    for r in rows:
        source = read_json(OUT / f"db-bench-{dataset}.json")["results"][r["combination"]]
        if source.get("lexical_engine") != "SQLite FTS5" or r["candidate"] == "Qdrant local":
            continue
        if any(x["combination"] == r["combination"] + " + Tantivy" for x in rows):
            continue
        name = r["combination"].replace(" × ", "__").replace(" ", "_").replace("+", "_")
        path = WORK / f"rankings/{dataset}/{name}.json"
        if not path.exists():
            continue
        dense = json.loads(path.read_text(encoding="utf-8"))["dense"]
        totals, recalls, ndcgs = [], [], []
        for q, d, lx in zip(queries, dense, tantivy):
            fused = rrf(d["ids"], lx["ids"])
            totals.append(d["ms"] + lx["ms"])
            if q["expected"]:
                recall, ndcg = metric([labels[i] for i in fused], q["expected"])
                recalls.append(recall)
                ndcgs.append(ndcg)
        size = r["size_bytes"] - engines["SQLite FTS5"]["size_bytes"] + engines["Tantivy"]["size_bytes"]
        made.append({**r, "combination": r["combination"] + " + Tantivy", "candidate": r["candidate"] + " + Tantivy",
                     "db_p95_ms": p95(totals), "lexical_p95_ms": p95([x["ms"] for x in tantivy]), "speed_ms": r["query_embedding_p95_ms"] + p95(totals),
                     "size_bytes": size, "accuracy": sum(recalls) / len(recalls), "ndcg_at_10": sum(ndcgs) / len(ndcgs),
                     "measured": "部品の実測を合成（容量は換算）", "lexical_engine": "Tantivy"})
    return made


def component_recall(dataset, combination):
    """保存した順位から、語彙だけと dense だけの再現率@30 を出す。"""
    import json
    from common import WORK, full_mapping, full_queries, metric
    path = WORK / f"rankings/{dataset}/{combination.replace(' × ', '__').replace(' ', '_').replace('+', '_')}.json"
    if not path.exists():
        return None
    saved = json.loads(path.read_text(encoding="utf-8"))
    labels = {int(row[0]): f"{row[2]}:p{row[3]}" for row in full_mapping()}
    result = {}
    for side in ("lexical", "dense"):
        values = [metric([labels[i] for i in run["ids"]], q["expected"])[0] for q, run in zip(full_queries(), saved[side]) if q["expected"]]
        result[f"{side}_only_recall_at_30"] = sum(values) / len(values)
    return result


def table(dataset):
    path = OUT / f"db-bench-{dataset}.json"
    if not path.exists():
        return []
    parity = {(r["model"], r["runtime"]): r for r in read_json(OUT / "runtime-parity.json")["results"] if r.get("status") == "ok"}
    rows = []
    for key, r in read_json(path)["results"].items():
        if r.get("status") != "ok":
            rows.append({"combination": key, "status": "failed", "error": r.get("error")})
            continue
        point = r["operating_point"]
        embed = parity[(r["model"], r["query_runtime"])]["query_p95_ms"]
        rows.append({"combination": key, "model": r["model"], "candidate": r["candidate"], "dimension": r["dimension"], "rows": r["rows"],
                     "query_runtime": r["query_runtime"], "query_embedding_p95_ms": embed, "db_p95_ms": point["db_p95_ms"],
                     "dense_p95_ms": point["dense_p95_ms"], "lexical_p95_ms": point["lexical_p95_ms"],
                     "speed_ms": embed + point["db_p95_ms"], "size_bytes": r["size"]["total_bytes"], "accuracy": point["recall_at_30"],
                     "ndcg_at_10": point["ndcg_at_10"], "dense_recall_vs_exact_at_30": point["dense_recall_vs_exact_at_30"],
                     "knob": f"{r['knob_name']}={point['knob']}" if r.get("knob_name") else "なし（総当たり）", "target_reached": r["target_reached"],
                     "build_seconds": r["build_seconds"], "unfiltered_db_p95_ms": (r.get("unfiltered") or {}).get("db_p95_ms"),
                     "rss_bytes": r.get("rss_bytes_after_search"), "status": "ok", "measured": "実測", "lexical_engine": r.get("lexical_engine")})
    rows += tantivy_variants(dataset, [r for r in rows if r["status"] == "ok"], parity)
    if dataset == "full":
        for r in rows:
            if r["status"] == "ok" and r["measured"] == "実測":
                r["component_recall"] = component_recall(dataset, r["combination"])
    ok = [r for r in rows if r["status"] == "ok"]
    current = next((r for r in ok if r["combination"] == CURRENT), None)
    if ok and current:
        scores(ok, current["accuracy"])
    return rows


def main():
    subset = table("subset")
    full = table("full")
    report = {"rules": __doc__, "speed_limit_ms": SPEED_LIMIT_MS, "size_limit_bytes": SIZE_LIMIT_BYTES, "accuracy_margin": ACCURACY_MARGIN,
              "current": CURRENT, "subset": subset, "full": full}
    for name, rows in (("subset", subset), ("full", full)):
        ok = [r for r in rows if r["status"] == "ok"]
        if not ok:
            continue
        high = [r for r in ok if r["all_high"]]
        valid = [r for r in ok if r["target_reached"]] or ok
        chosen = max(high or valid, key=lambda r: (r["score"]["minimum"], sum(v for k, v in r["score"].items() if k != "minimum")))
        report[f"{name}_decision"] = {"rule": "3 つとも 7 点以上" if high else "最小の点が最も高い（バランス）", "combination": chosen["combination"],
                                      "score": chosen["score"], "all_high_combinations": [r["combination"] for r in high]}
        print(name, report[f"{name}_decision"])
        for r in sorted(ok, key=lambda r: -r["score"]["minimum"]):
            mark = "" if r["target_reached"] else " 未達"
            print(f"  {r['combination']:<44} {r['speed_ms']:7.1f}ms {r['size_bytes'] / 2 ** 20:8.1f}MiB {r['accuracy']:.3f} {r['score']}{mark}")
    write_json(OUT / "scores.json", report)


if __name__ == "__main__":
    main()
