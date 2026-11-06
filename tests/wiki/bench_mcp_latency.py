"""wiki の検索の速さを、今の CLI、中継経由の MCP、関数の直接呼び出しで比べる。

- cli_hybrid      `uv run --script wiki_search.py <q> --json --cache`（e5-small + sqlite-vec。1 回ごとに起動する）
- cli_lexical     `python wiki_search.py <q> --json --cache --no-embed`（MCP が使えないときの戻り道）
- mcp_cold        サーバーが動いていない状態からの最初の query（サーバーの起動とモデルの読み込みを含む）
- mcp_relay       stdio の中継から query を呼ぶ（サーバーは起動済み、モデルは読み込み済み）
- direct          サーバーの query と同じ処理（WikiIndex.refresh と search）を同じプロセスで呼ぶ（MCP の上乗せのない下限）

コーパスは wiki の評価セット（en と ja）で、クエリは評価セットのクエリ全部を使う。
ADR-0012 の上乗せの目安は、mcp_relay と direct の p95 の差が 15 ms 以内。

    set INFO_HIVE_POC_DATA=C:\\Works\\info-hive-dev\\.rag-poc-data
    uv run --python 3.12 --with mcp==1.30.0 --with numpy==2.5.4 --with usearch==2.26.6 --with tantivy==0.27.0 ^
        --with fastembed==0.8.0 --with onnxruntime==1.31.1 --with psutil==7.2.2 ^
        python -X utf8 tests/wiki/bench_mcp_latency.py

結果は docs/research/wiki-mcp-server-2026-11-06/latency.json に書く。
"""
from __future__ import annotations

import json
import os
import platform
import shutil
import statistics
import subprocess
import sys
import tempfile
import time
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
sys.path.insert(0, str(HERE))
sys.path.insert(0, str(ROOT / "info-hive-wiki/skills/info-hive/scripts"))
from mcp_stdio import StdioClient, relay_command  # noqa: E402

EVAL = ROOT / "info-hive-wiki/eval/retrieval"
SEARCH = ROOT / "info-hive-wiki/skills/info-hive/scripts/wiki_search.py"
OUT = ROOT / "docs/research/wiki-mcp-server-2026-11-06"
CLI_SAMPLE = 15   # 1 回に数秒かかるので、CLI は各セットの先頭からこの数だけ測る
ROUNDS = 3        # MCP と直接呼び出しは、全クエリをこの回数まわす


def summary(samples_ms: list[float]) -> dict:
    ordered = sorted(samples_ms)
    p95 = ordered[min(len(ordered) - 1, max(0, round(0.95 * len(ordered)) - 1))]
    return {"n": len(ordered), "median_ms": round(statistics.median(ordered), 2), "p95_ms": round(p95, 2),
            "max_ms": round(ordered[-1], 2)}


def timed(fn) -> float:
    started = time.perf_counter()
    fn()
    return (time.perf_counter() - started) * 1000


def main() -> None:
    base = os.environ.get("INFO_HIVE_POC_DATA")
    if not base:
        raise SystemExit("INFO_HIVE_POC_DATA を設定する")
    work = Path(base) / "wiki-mcp-20261106"
    os.environ["INFO_HIVE_DATA_DIR"] = str(work / "data-bench")
    shutil.rmtree(work / "data-bench", ignore_errors=True)
    # モデルは取得済みのものを使い回す（取得の時間は測らない）。
    shutil.copytree(work / "data" / "models", work / "data-bench" / "models")
    env_cli = {**os.environ, "PYTHONUTF8": "1", "FASTEMBED_CACHE_PATH": str(work / "fastembed-e5")}
    import wiki_index
    import wiki_mcp_common

    report = {"purpose": "wiki の検索の速さ（今の CLI、中継経由の MCP、直接呼び出し）",
              "env": {"python": sys.version.split()[0], "platform": platform.platform(),
                      "cpu_count": os.cpu_count()}, "sets": {}}
    with tempfile.TemporaryDirectory() as tmp:
        corpora = {}
        for name, folder in (("en", EVAL / "corpus/wiki"), ("ja", EVAL / "ja/corpus/wiki")):
            corpora[name] = Path(tmp) / name
            shutil.copytree(folder, corpora[name], ignore=shutil.ignore_patterns(".wiki-cache"))
        queries = {"en": json.loads((EVAL / "queries.json").read_text(encoding="utf-8")),
                   "ja": json.loads((EVAL / "ja/queries.json").read_text(encoding="utf-8"))}

        # MCP: 最初の呼び出し（サーバーの起動、モデルの読み込み、初回の埋め込みを含む）と、温まった後。
        client = StdioClient(relay_command(), {"INFO_HIVE_DATA_DIR": os.environ["INFO_HIVE_DATA_DIR"]})
        cold = {}
        initialize_ms = timed(lambda: client.initialize())
        tools_ms = timed(lambda: client.tools())
        for name, corpus in corpora.items():
            cold[name] = timed(lambda: client.call("query", {"wiki": str(corpus), "query": queries[name][0]["query"]}))
            # 埋め込みが裏に回った場合に備え、終わるまで待つ。
            while client.call("query", {"wiki": str(corpus), "query": "x"})["index"]["state"] != "ready":
                time.sleep(1)
        report["mcp_cold"] = {"initialize_ms": round(initialize_ms, 1), "tools_list_ms": round(tools_ms, 1),
                              "first_query_ms": {k: round(v, 1) for k, v in cold.items()},
                              "note": "initialize にサーバーの起動（依存の確認、待ち受けまで）を含む。最初の query に"
                                      "モデルの読み込みと、コーパス全体の初回の埋め込みを含む"}
        for name, corpus in corpora.items():
            result = {}
            samples = []
            for _ in range(ROUNDS):
                for q in queries[name]:
                    samples.append(timed(lambda: client.call("query", {"wiki": str(corpus), "query": q["query"]})))
            result["mcp_relay"] = summary(samples)
            report["sets"][name] = result
        info = json.loads((Path(os.environ["INFO_HIVE_DATA_DIR"]) / "server.json").read_text(encoding="utf-8"))
        client.close()
        import psutil
        server = psutil.Process(info["pid"])
        report["server_rss_bytes"] = server.memory_info().rss
        report["server_private_bytes"] = getattr(server.memory_info(), "private", None)
        server.terminate()
        server.wait(60)

        # 直接呼び出し（同じ索引と同じモデル）。
        embedder = wiki_index.get_embedder()
        for name, corpus in corpora.items():
            index = wiki_index.WikiIndex(wiki_mcp_common.normalize_wiki_root(corpus))
            try:
                index.refresh()
                samples = []
                for _ in range(ROUNDS):
                    for q in queries[name]:
                        # サーバーの query と同じく、毎回 wiki の変更を確かめてから検索する。
                        samples.append(timed(lambda: (index.refresh(), index.search(q["query"], embedder=embedder))))
            finally:
                index.close()
            direct = summary(samples)
            report["sets"][name]["direct"] = direct
            report["sets"][name]["overhead_p95_ms"] = round(report["sets"][name]["mcp_relay"]["p95_ms"] - direct["p95_ms"], 2)

        # 今の CLI。
        for name, corpus in (corpora.items() if "--skip-cli" not in sys.argv else []):
            for label, command in (
                    ("cli_hybrid", ["uv", "run", "--quiet", "--script", str(SEARCH)]),
                    ("cli_lexical", [sys.executable, str(SEARCH)])):
                extra = ["--no-embed"] if label == "cli_lexical" else []
                run = lambda q: subprocess.run(command + [q, "--wiki", str(corpus), "--json", "--cache"] + extra,
                                               capture_output=True, env=env_cli, check=True)
                run(queries[name][0]["query"])  # 依存とモデルの取得、索引の作成を測らない
                samples = [timed(lambda: run(q["query"])) for q in queries[name][:CLI_SAMPLE]]
                report["sets"][name][label] = summary(samples)
    OUT.mkdir(parents=True, exist_ok=True)
    report["embed_threads"] = os.environ.get("INFO_HIVE_EMBED_THREADS") or "onnxruntime の既定"
    out_name = os.environ.get("BENCH_OUT", "latency.json")
    (OUT / out_name).write_text(json.dumps(report, ensure_ascii=False, indent=1) + "\n", encoding="utf-8",
                                      newline="\n")
    print(json.dumps(report, ensure_ascii=False, indent=1))


if __name__ == "__main__":
    main()
