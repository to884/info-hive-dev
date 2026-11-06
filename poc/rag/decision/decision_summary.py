"""E11: E1〜E10 の結果をまとめ、推奨が覆る条件（計画の「停止の規則」）を判定する。

- 速度の採点は統一の測定（summarize.scores）と同じ式。クエリの埋め込みの p95 は、ほかの仕事がない状態で測り直す
  （統一の測定は GPU の埋め込みと並べて測った 38.4 ms を使っていた）。
- DB の p95 は E3 の動作点（dense + 語彙 + RRF）に、E4 の世代の絞り込み（5% を無効にしたとき）の増分を足す。
- 精度は E3 の動作点の再現率@30（統一の測定と同じ RRF k=60）。E1 の融合の設定は全ての組に同じように効くので、別に示す。
"""
from __future__ import annotations

import copy
import time

import numpy as np

from decision_common import OUT_D, load, read_json, save
from common import OUT as UNIFICATION_OUT, full_queries, limit_threads, p95
from summarize import scores

GIB = 2 ** 30
RELAY_LIMIT_MS = 15.0


def relay_ok(report, limit_ms):
    return (report["server_survived_relay_exit"] and report["overhead_p95_ms"]["relay"] <= limit_ms and report["security_ok"]
            and report["concurrent_summary"]["distinct_server_pids"] == 1 and report["concurrent_summary"]["max_servers_seen"] == 1
            and report["idle_shutdown"]["servers_after_idle"] == 0)


def query_p95():
    limit_threads()
    from runtime_parity import Runtime
    runtime = Runtime("R-130", "onnx-fp32")
    runtime.load()
    texts = [q["query"] for q in full_queries()]
    runtime.queries(texts[:3])
    times = []
    for text in texts:
        started = time.perf_counter()
        runtime.queries([text])
        times.append((time.perf_counter() - started) * 1000)
    return p95(times), float(np.median(times))


def main():
    knobs = load("db-knobs-full.json")["results"]
    generation = load("generation-filter.json")
    fusion = load("fusion-sweep.json")
    deep = load("fusion-deep.json")
    wiki_gate = load("wiki-gate.json")
    reembed = load("wiki-reembed.json")
    write = load("write-safety.json")
    retry = load("tantivy-commit-retry.json")
    memory = load("server-memory.json")
    relay = load("mcp-relay.json")
    relay_variants = {name: load(f"{name}.json") for name in ("mcp-relay", "mcp-relay-quiet", "mcp-relay-quiet-json",
                                                                    "mcp-relay-quiet-json-asgi", "mcp-relay-quiet-json-noauth")}
    claude_job = load("claude-job-check.json")
    onnx = load("onnx-distribution.json")
    q95, q50 = query_p95()
    five = next(r for r in generation["filtering"] if r["fraction_documents"] == 0.05)
    usearch_filter = (five["usearch_smallest_ok"] or {}).get("p95_increase_ms")
    faiss_filter = five["faiss_selector"]["p95_increase_ms"]
    rows = []
    for key, result in knobs.items():
        point = result["operating_point"]
        filter_ms = max(0.0, faiss_filter if key.startswith("FAISS") else (usearch_filter if usearch_filter is not None else 1e9))
        rows.append({"key": key, "rows": 761_915, "speed_ms": q95 + point["db_p95_ms"] + filter_ms, "db_p95_ms": point["db_p95_ms"],
                     "filter_ms": filter_ms, "size_bytes": result["size"]["vector_bytes"] + result["size"]["lexical_bytes"],
                     "accuracy": point["recall_at_30"], "ndcg_at_10": point["ndcg_at_10"], "knob": point["knob"],
                     "dense_recall_vs_exact_at_30": point["dense_recall_vs_exact_at_30"], "target_reached": result["target_reached"],
                     "build_seconds": result.get("build_seconds")})
    old = read_json(UNIFICATION_OUT / "db-bench-full.json")["results"]["R-130 × LanceDB IVF_SQ"]
    rows.append({"key": "LanceDB IVF_SQ（現行 rag、統一の測定）", "rows": 761_915,
                 "speed_ms": q95 + old["operating_point"]["db_p95_ms"], "db_p95_ms": old["operating_point"]["db_p95_ms"], "filter_ms": 0.0,
                 "size_bytes": old["size"]["total_bytes"], "accuracy": old["operating_point"]["recall_at_30"],
                 "ndcg_at_10": old["operating_point"]["ndcg_at_10"], "knob": old["operating_point"]["knob"],
                 "dense_recall_vs_exact_at_30": old["operating_point"]["dense_recall_vs_exact_at_30"], "target_reached": old["target_reached"],
                 "build_seconds": old["build_seconds"], "note": "世代の絞り込みは native（費用を含む）"})
    baseline = rows[-1]["accuracy"]
    scored = scores(copy.deepcopy(rows), baseline)
    usearch_rows = [r for r in scored if r["key"].startswith("usearch")]
    faiss_rows = [r for r in scored if r["key"].startswith("FAISS")]
    best_usearch = max(usearch_rows, key=lambda r: (r["score"]["minimum"], -r["speed_ms"]))
    best_faiss = max(faiss_rows, key=lambda r: (r["score"]["minimum"], -r["speed_ms"]))
    gates = {
        "E8_wiki_gate_r130": wiki_gate["passed"]["r130"],
        "E8_calibration_separable": wiki_gate["chosen"]["separable"],
        "E8_sudachi": wiki_gate["passed"]["r130-sudachi"],
        # 案 2: 語彙のエンジンだけを Tantivy にし、wiki のトークン（bigram）はそのまま
        "E8_tantivy_bigram": wiki_gate["passed"]["r130-tantivy"],
        "E7_reembed": reembed["passed"],
        "E1_fusion_keep": not fusion["dense_beats_fusion_everywhere"],
        "E3_faiss_not_better_by_0_5": best_faiss["score"]["minimum"] < best_usearch["score"]["minimum"] + 0.5,
        "E5_write_safe": write["passed"],
        # Tantivy は Windows で commit が失敗することがあり、失敗の後も writer を使うと文書が失われる。
        # rollback して入れ直す規則を守れば失われない（tantivy-commit-retry.json）。語彙エンジンを替えるかの判定に使う
        "E5_tantivy_with_retry": retry["passed"],
        "E4_filter_ok": generation["criteria"]["postfilter_5pct_increase_le_20ms"],
        # 計画の停止の規則: usearch が上限を超え、かつ FAISS が収まるときだけ索引の選択が変わる
        "E6_memory_not_favoring_faiss": not (
            any(not v["within_limit"] for k, v in memory["verdict"].items() if k.endswith("usearch-view"))
            and all(v["within_limit"] for k, v in memory["verdict"].items() if k.endswith("faiss"))),
        # 認証なしの行は上乗せの下限を見るためだけのもので、合否には使わない
        # 2026-11-06 の判断で、上乗せの目安を 10 ms から 15 ms に緩めた。上乗せ以外の条件（サーバーが残る、重複 0、
        # 防御、idle での停止）は変えない
        "E10_relay": any(relay_ok(v, RELAY_LIMIT_MS) for n, v in relay_variants.items() if not n.endswith("noauth")),
        # Claude Code（CLI）はサーバーをジョブに入れず、DETACHED_PROCESS の孫はセッションの後も残る
        "E10_claude_code_keeps_detached": bool(claude_job["summary"]["detached_grandchild_survives_claude"]),
        "E9_onnx": onnx["passed"],
    }
    overturn = {name: not ok for name, ok in gates.items()}
    gib_limits = memory["limits_private_gib"]
    memory_note = {k: {"private_gib": v["private_gib"], "within_limit": v["within_limit"]} for k, v in memory["verdict"].items()}
    relay_parts = {"function_p95_ms": relay["function_p95_ms"], "direct_http_p95_ms": relay["direct_http"]["query_p95_ms"],
                   "relay_p95_ms": relay["relay_warm"]["query_p95_ms"],
                   "relay_hop_ms": relay["relay_warm"]["query_p95_ms"] - relay["direct_http"]["query_p95_ms"],
                   "http_mcp_ms": relay["direct_http"]["query_p95_ms"] - relay["function_p95_ms"]}
    notes = {
        "E6": {"limits_private_gib": gib_limits, "with_model": memory_note,
               "summary": "モデルありの構成はどの索引でも提案値を超えた。FAISS も収まらないので索引の選択は変わらない。提案値を見直す"},
        "E10": {"overhead_parts_ms": relay_parts, "server_survived_relay_exit": relay["server_survived_relay_exit"],
                "variants": {name: {"log_level": v.get("log_level"), "json_response": v.get("json_response"), "auth": v.get("auth", "starlette"),
                                    "function_p95_ms": v["function_p95_ms"], "direct_http_p95_ms": v["direct_http"]["query_p95_ms"],
                                    "relay_p95_ms": v["relay_warm"]["query_p95_ms"], "overhead_relay_ms": v["overhead_p95_ms"]["relay"]}
                             for name, v in relay_variants.items()},
                "summary": "中継の 1 段は数 ms で、上乗せの大半は HTTP 上の MCP（JSON と uvicorn）にある"},
    }
    save("decision-scores.json", {
        "purpose": "E1〜E10 をまとめた最終の採点と、推奨が覆る条件の判定",
        "query_embedding": {"model": "R-130 onnx-fp32", "p95_ms": q95, "median_ms": q50, "note": "ほかの仕事がない状態で 72 問"},
        "rows": scored, "best_usearch": best_usearch["key"], "best_faiss": best_faiss["key"],
        "fusion_chosen": fusion["chosen"], "fusion_deep_best": deep["best"], "gates": gates, "overturned": [k for k, v in overturn.items() if v], "notes": notes,
        "decisions": {"date": "2026-11-06", "E7_reembed": "目安の 20 分を緩め、初回だけ時間がかかることを upgrade の案内に書く",
                      "E8_lexical": "案 2（Tantivy に wiki の bigram を登録する）を測ってから決める",
                      "E10_relay": "上乗せをもう 1 回測る。その後、認証の書き方を変えて測る",
                      "E10_relay_final": "上乗せの目安を 15 ms に緩める。応答は JSON、認証は ASGI のミドルウェアで書く", "E10_spawn": "先に Claude Code がサーバーをジョブに入れるかを確かめる",
                      "E8_lexical_final": "案 2: 語彙のエンジンを Tantivy にそろえ、wiki には bigram、rag には Sudachi のトークンを入れる"}})


if __name__ == "__main__":
    main()
