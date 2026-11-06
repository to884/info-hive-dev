"""wiki の評価（info-hive-wiki/eval/retrieval/run_eval.py）から、新しい検索の基盤を呼ぶための入口。

run_eval.py はクエリごとに `python <SCRIPT> <query> --wiki ... --json ...` を起動する。SCRIPT をこのファイルに
差し替えると、セクション単位の検索（--no-embed の語彙だけと、ハイブリッド）を wiki_index（Tantivy、usearch、
ruri-v3-130m）で答える。MCP サーバーが持つものと同じ WikiIndex を使う。
ページ単位（--granularity page）と --cache の確認は、MCP に移さない今の CLI の機能なので、wiki_search.py に任せる。

環境変数:
- INFO_HIVE_DATA_DIR       索引とモデルの置き場所（呼び出しをまたいで同じ索引を使う）
- MCP_EVAL_FUSION          融合の設定を変えて比べるときに "k,語彙の重み,候補数"（既定は ADR-0011 の 30,0.5,200）
"""
from __future__ import annotations

import argparse
import json
import os
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "info-hive-wiki/skills/info-hive/scripts"))
import wiki_index  # noqa: E402
import wiki_mcp_common  # noqa: E402
import wiki_search  # noqa: E402


def main() -> None:
    if "--granularity" in sys.argv and "page" in sys.argv or "--cache" in sys.argv:
        wiki_search.main()
        return
    parser = argparse.ArgumentParser()
    parser.add_argument("query")
    parser.add_argument("--wiki", type=Path, required=True)
    parser.add_argument("--json", action="store_true")
    parser.add_argument("--top", type=int, default=10)
    parser.add_argument("--no-embed", action="store_true")
    parser.add_argument("--type")
    parser.add_argument("--tag", action="append", default=[])
    parser.add_argument("--granularity", default="section")
    args = parser.parse_args()
    if os.environ.get("MCP_EVAL_FUSION"):
        k, weight, n = os.environ["MCP_EVAL_FUSION"].split(",")
        wiki_index.FUSION.update(k=float(k), lexical_weight=float(weight), candidates=int(n))
    index = wiki_index.WikiIndex(wiki_mcp_common.normalize_wiki_root(args.wiki))
    try:
        index.refresh()
        embedder = None
        if not args.no_embed:
            embedder = wiki_index.get_embedder()
            wiki_index.embed_pending(index.collection, embedder)
        result = index.search(args.query, top=args.top, type=args.type, tags=args.tag, embedder=embedder)
    finally:
        index.close()
    payload = {key: result[key] for key in ("query", "wiki", "granularity", "mode", "results")}
    print(json.dumps(payload, ensure_ascii=False))


if __name__ == "__main__":
    for stream in (sys.stdin, sys.stdout, sys.stderr):
        if hasattr(stream, "reconfigure"):
            stream.reconfigure(encoding="utf-8")
    main()
