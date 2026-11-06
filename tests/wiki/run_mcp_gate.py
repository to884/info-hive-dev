"""wiki の評価ゲートを、MCP サーバーの検索の基盤（wiki_index）で通せるかを測る。

info-hive-wiki/eval/retrieval/run_eval.py の evaluate を、SCRIPT を mcp_eval_search.py に差し替えて動かす。
en と ja のそれぞれで --gate と --baseline（許容幅 0.05）を判定し、追加測定 E8 の r130-tantivy の行と比べる。
融合は ADR-0011 の設定（k 30、語彙の重み 0.5、候補 200）と、E8 が測った wiki の既定（k 60、重み 1.0、候補 50）の
両方で測る。

使い方（依存は wiki_mcp_server.py の宣言と同じ版にそろえる）:
    set INFO_HIVE_POC_DATA=C:\\Works\\info-hive-dev\\.rag-poc-data
    uv run --python 3.12 --with mcp==1.30.0 --with numpy==2.5.4 --with usearch==2.26.6 --with tantivy==0.27.0 ^
        --with fastembed==0.8.0 --with onnxruntime==1.31.1 python -X utf8 tests/wiki/run_mcp_gate.py

結果は docs/research/wiki-mcp-server-2026-11-06/gate.json に書く。
"""
from __future__ import annotations

import argparse
import contextlib
import io
import json
import os
import shutil
import sys
import tempfile
import time
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
EVAL = ROOT / "info-hive-wiki/eval/retrieval"
OUT = ROOT / "docs/research/wiki-mcp-server-2026-11-06"
E8 = ROOT / "docs/research/embedding-backend-decision-2026-11-06/wiki-gate.json"
FUSIONS = {"adr-0011": "30,0.5,200", "e8-wiki-default": "60,1.0,50"}


def data_dir() -> Path:
    base = os.environ.get("INFO_HIVE_POC_DATA")
    if not base:
        raise SystemExit("INFO_HIVE_POC_DATA（作業データの置き場所）を設定する")
    return Path(base) / "wiki-mcp-20261106" / "data"


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--fusion", choices=sorted(FUSIONS), action="append")
    args = parser.parse_args()
    os.environ["INFO_HIVE_DATA_DIR"] = str(data_dir())
    os.environ.setdefault("PYTHONUTF8", "1")
    sys.path.insert(0, str(EVAL))
    import run_eval
    original_script = run_eval.SCRIPT
    original_cache_invariant = run_eval.cache_invariant

    def cache_invariant(cache_queries):
        # --cache は今の CLI（wiki_search.py）の機能で、MCP の索引は使わない。3 回とも今の CLI で比べる。
        run_eval.SCRIPT = original_script
        try:
            return original_cache_invariant(cache_queries)
        finally:
            run_eval.SCRIPT = HERE / "mcp_eval_search.py"

    run_eval.cache_invariant = cache_invariant
    run_eval.SCRIPT = HERE / "mcp_eval_search.py"
    e8 = json.loads(E8.read_text(encoding="utf-8"))["gates"]["r130-tantivy"]
    report = {"purpose": "wiki の評価ゲートを MCP サーバーの検索の基盤（R-130 ONNX、usearch、Tantivy + bigram）で測る",
              "criterion": "--gate と --baseline（recall@10 と MRR の低下 ≤ 0.05、fp_rate の上昇 ≤ 0.05）に合格する",
              "python": sys.version.split()[0], "runs": {}}
    for name in args.fusion or list(FUSIONS):
        os.environ["MCP_EVAL_FUSION"] = FUSIONS[name]
        runs = {}
        for set_name, spec in run_eval.SETS.items():
            queries = json.loads(spec["queries"].read_text(encoding="utf-8"))
            buffer = io.StringIO()
            started = time.perf_counter()
            with tempfile.TemporaryDirectory() as tmp:
                copied = dict(spec)
                if not spec.get("nfd_files"):
                    copied["corpus"] = Path(tmp) / "corpus"
                    shutil.copytree(spec["corpus"], copied["corpus"], ignore=shutil.ignore_patterns(".wiki-cache"))
                run_eval.CORPUS = run_eval.prepare_corpus(copied, tmp)
                saved = Path(tmp) / "report.json"
                gate_args = argparse.Namespace(gate=True, baseline="AUTO", save=str(saved), set=set_name)
                with contextlib.redirect_stdout(buffer), contextlib.redirect_stderr(buffer):
                    code = run_eval.evaluate(gate_args, queries)
                result = json.loads(saved.read_text(encoding="utf-8"))
            baseline = json.loads((run_eval.BASELINES / f"{set_name}.json").read_text(encoding="utf-8"))["metrics"]
            runs[set_name] = {
                "exit_code": code, "seconds": round(time.perf_counter() - started, 1),
                "metrics": result["metrics"], "by_kind": result["by_kind"], "baseline": baseline,
                "baseline_failures": run_eval.baseline_failures(result["metrics"], baseline),
                "e8_r130_tantivy": e8[set_name]["metrics"], "log": buffer.getvalue()[-2500:]}
            print(name, set_name, "exit", code,
                  {m: (round(v["recall@10"], 3), round(v["mrr"], 3), round(v["fp_rate"], 3))
                   for m, v in result["metrics"].items()}, flush=True)
        report["runs"][name] = {"fusion": FUSIONS[name], "sets": runs,
                                "passed": all(r["exit_code"] == 0 for r in runs.values())}
    OUT.mkdir(parents=True, exist_ok=True)
    path = OUT / "gate.json"
    if path.exists() and args.fusion:
        previous = json.loads(path.read_text(encoding="utf-8"))
        previous["runs"].update(report["runs"])
        report["runs"] = previous["runs"]
    path.write_text(json.dumps(report, ensure_ascii=False, indent=1) + "\n", encoding="utf-8", newline="\n")
    print("保存した:", path)


if __name__ == "__main__":
    main()
