"""MCP サーバーの検索の基盤（wiki_index）で、意味の検索の距離の上限（MODEL["max_distance"]）を測り直す。

移植計画の P3 で決めた e5-small の 0.193 は、wiki 0.4.0 で検索の基盤が ruri-v3-130m の ONNX、usearch、
Tantivy の BM25 と RRF に移ったので、そのままでは使えない。ADR-0011 は追加測定 E8 で 0.208 を決めたが、
E8 は実装の前の試作で測った。ここでは、出荷している wiki_index をそのまま使い、次を測る。

1. 距離の分布: 評価セット（en、ja）の正例が、期待するページに届くのに要る距離と、負例のいちばん近い
   セクションまでの距離。評価セットの負例は 11 問しかないので、コーパスと関係のない話題の問い（PROBES）も
   負例として足して測る。PROBES は評価セットに入れない、この測定だけの問いである。
2. 上限を変えたときの成績: 上限を GRID の値と「上限なし」に変えて、run_eval.py と同じ指標（recall@5、
   recall@10、MRR、偽陽性率）を計算する。偽陽性率は、負例で上位 5 件に 1 件以上を返した割合である。
3. 任意で、手元の wiki（--extra-wiki）でページの題名を問いにしたときの距離と、PROBES の距離。

使い方（依存は wiki_mcp_server.py の宣言と同じ版にそろえる。モデルは取得済みのものを使い回す）:
    uv run --python 3.12 %DEPS% python -X utf8 tests/wiki/measure_dense_threshold.py [--extra-wiki <wiki>]

結果は docs/research/wiki-dense-threshold-2026-11-07/threshold.json に書く。
"""
from __future__ import annotations

import argparse
import functools
import json
import os
import platform
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
sys.path.insert(0, str(ROOT / "poc"))
from poc_data import poc_data_dir  # noqa: E402
EVAL = ROOT / "info-hive-wiki/eval/retrieval"
OUT = ROOT / "docs/research/wiki-dense-threshold-2026-11-07"
sys.path.insert(0, str(ROOT / "info-hive-wiki/skills/info-hive/scripts"))
sys.path.insert(0, str(EVAL))

# 上限の候補。0.16〜0.30 を 0.002 刻みで測る。None は上限なし。
GRID = [round(0.16 + 0.002 * i, 3) for i in range(71)] + [None]

# コーパス（en は機械学習、ja は税、出張、熱中症、検索）と関係のない話題の問い。意味の検索だけの距離を測る。
PROBES = {
    "en": [
        "how to bake sourdough bread at home", "best hiking trails in the Alps", "football world cup final score",
        "how to repair a leaking faucet", "symptoms of seasonal allergies in dogs", "history of the Roman empire",
        "watercolor painting techniques for beginners", "cheap flights to Hawaii in winter",
        "how to grow tomatoes on a balcony", "rules of contract bridge", "jazz saxophone players of the 1950s",
        "how to knit a wool scarf", "volcano eruption in Iceland", "wedding speech ideas for the best man",
        "fixing a flat bicycle tire", "chess opening for beginners", "skin care routine for dry skin",
        "how to train a puppy to sit", "recipe for vegetable curry", "the plot of a famous opera",
    ],
    "ja": [
        "自宅でのパンの焼き方", "アルプスの登山ルート", "サッカーのワールドカップの決勝", "水漏れする蛇口の直し方",
        "犬の花粉症の症状", "ローマ帝国の歴史", "初心者向けの水彩画の技法", "冬のハワイへの格安航空券",
        "ベランダでのトマトの育て方", "将棋の定跡", "1950 年代のジャズのサックス奏者", "毛糸のマフラーの編み方",
        "アイスランドの火山の噴火", "結婚式の友人代表のスピーチ", "自転車のパンクの直し方", "盆栽の剪定の時期",
        "乾燥肌のスキンケア", "子犬にお座りを教える方法", "野菜カレーの作り方", "オペラのあらすじ",
    ],
}


def poc_models() -> Path:
    base = poc_data_dir()
    return Path(base) / "wiki-mcp-20261106" / "data" / "models"


def git_head(path: Path) -> str:
    out = subprocess.run(["git", "-C", str(path), "rev-parse", "--short", "HEAD"], capture_output=True)
    return out.stdout.decode("utf-8", "replace").strip()


class Probe:
    """1 つの wiki の索引と、問いごとの意味の検索の距離。"""

    def __init__(self, wiki_index, wiki_search, root: Path, embedder, embed):
        self.wi, self.ws = wiki_index, wiki_search
        self.index = wiki_index.WikiIndex(root)
        self.index.refresh()
        wiki_index.embed_pending(self.index.collection, embedder)
        self.embed = embed

    def close(self):
        self.index.close()

    def allowed(self, filters: dict | None):
        """search() と同じ絞り込みで、意味の検索に渡すセクションの鍵。絞り込みがなければ None。"""
        from argparse import Namespace
        filters = filters or {}
        tag = filters.get("tag")
        args = Namespace(type=filters.get("type"), tag=(tag if isinstance(tag, list) else [tag]) if tag else [],
                         since=None)
        pages = [p for p in self.index.pages if self.ws.passes_filters(p, args)]
        if len(pages) == len(self.index.pages):
            return None
        paths = {p["rel_path"] for p in pages}
        return {key for s in self.index.sections if s["page"]["rel_path"] in paths
                for key in [self.index.collection.key_of(self.wi.section_locator(s))] if key is not None}

    def distances(self, query: str, filters: dict | None = None) -> list[tuple[str, float]]:
        """(ページのスラッグ, 距離) を距離の近い順に、すべてのセクションについて返す。"""
        pairs = self.index.collection.search_dense(self.embed(query), self.allowed(filters), 10 ** 6, None)
        slugs = []
        for key, distance in pairs:
            section = self.index.by_locator.get(self.index.collection._keys.get(key, ""))
            if section is not None:
                slugs.append((section["page"]["slug"], distance))
        return slugs

    def search_slugs(self, query: str, filters: dict | None, max_distance) -> list[str]:
        self.wi.MODEL["max_distance"] = max_distance
        filters = filters or {}
        tag = filters.get("tag")
        result = self.index.search(query, top=10, type=filters.get("type"),
                                   tags=(tag if isinstance(tag, list) else [tag]) if tag else [],
                                   embedder=self)
        return [row["slug"] for row in result["results"]]

    # search() に渡す埋め込みの代わり。問いの埋め込みは使い回す。
    def query(self, text: str):
        return self.embed(text)


def nearest(pairs: list[tuple[str, float]], slug: str) -> float | None:
    return next((d for s, d in pairs if s == slug), None)


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--extra-wiki", type=Path, help="題名を問いにして距離を測る手元の wiki（読むだけ。写しを索引にする）")
    args = parser.parse_args()
    work = Path(tempfile.mkdtemp(prefix="wiki-threshold-"))
    os.environ["INFO_HIVE_DATA_DIR"] = str(work / "data")
    shutil.copytree(poc_models(), work / "data" / "models")
    import run_eval
    import wiki_index
    import wiki_mcp_common
    import wiki_search

    embedder = wiki_index.get_embedder()
    embed = functools.lru_cache(maxsize=None)(embedder.query)
    original = wiki_index.MODEL["max_distance"]
    report = {"purpose": "MCP の検索の基盤（ruri-v3-130m、usearch、Tantivy、RRF）での意味の検索の距離の上限",
              "env": {"python": sys.version.split()[0], "platform": platform.platform(),
                      "dev_commit": git_head(ROOT), "wiki_commit": git_head(ROOT / "info-hive-wiki"),
                      "model": wiki_index.MODEL["name"], "runtime": wiki_index.MODEL["runtime"],
                      "fusion": dict(wiki_index.FUSION), "current_max_distance": original},
              "sets": {}}
    try:
        for name in ("en", "ja"):
            spec = run_eval.SETS[name]
            queries = json.loads(spec["queries"].read_text(encoding="utf-8"))
            corpus = work / "corpus" / name
            copied = dict(spec, corpus=corpus)
            shutil.copytree(spec["corpus"], corpus, ignore=shutil.ignore_patterns(".wiki-cache"))
            corpus = Path(run_eval.prepare_corpus(copied, str(work / f"nfd-{name}")))
            probe = Probe(wiki_index, wiki_search, wiki_mcp_common.normalize_wiki_root(corpus), embedder, embed)
            try:
                rows = []
                for q in queries:
                    pairs = probe.distances(q["query"], q.get("filters"))
                    row = {"id": q["id"], "kind": q["kind"], "nearest": round(pairs[0][1], 4) if pairs else None}
                    if q["kind"] != "negative":
                        need = {slug: nearest(pairs, slug) for slug in q["expected"]}
                        row["expected"] = {k: (round(v, 4) if v is not None else None) for k, v in need.items()}
                        found = [v for v in need.values() if v is not None]
                        row["needed_min"] = round(min(found), 4) if found else None  # 1 つでも届く距離
                        row["needed_max"] = round(max(found), 4) if found else None  # 全部に届く距離
                    rows.append(row)
                probes = [{"query": text, "nearest": round(probe.distances(text)[0][1], 4)} for text in PROBES[name]]
                sweep = []
                for value in GRID:
                    runs = [{"id": q["id"], "kind": q["kind"],
                             "slugs": probe.search_slugs(q["query"], q.get("filters"), value)} for q in queries]
                    metrics = run_eval.aggregate(queries, runs)
                    probe_fp = sum(1 for text in PROBES[name] if probe.search_slugs(text, None, value)[:5])
                    sweep.append({"max_distance": value, **{k: round(v, 4) for k, v in metrics.items()},
                                  "probe_fp_rate": round(probe_fp / len(PROBES[name]), 4)})
                lexical = run_eval.aggregate(queries, [
                    {"id": q["id"], "kind": q["kind"],
                     "slugs": [r["slug"] for r in probe.index.search(
                         q["query"], top=10, type=(q.get("filters") or {}).get("type"),
                         tags=[t for t in [(q.get("filters") or {}).get("tag")] if t])["results"]]} for q in queries])
                probe_lexical_fp = sum(1 for text in PROBES[name] if probe.index.search(text, top=10)["results"][:5])
            finally:
                probe.close()
            positives = [r for r in rows if r["kind"] != "negative"]
            negatives = [r for r in rows if r["kind"] == "negative"]
            report["sets"][name] = {
                "summary": {
                    "positives": len(positives), "negatives": len(negatives), "probes": len(probes),
                    "positive_needed_min_max": max(r["needed_min"] for r in positives if r["needed_min"] is not None),
                    "positive_needed_max_max": max(r["needed_max"] for r in positives if r["needed_max"] is not None),
                    "negative_nearest_min": min(r["nearest"] for r in negatives),
                    "probe_nearest_min": min(p["nearest"] for p in probes),
                    "lexical_only": {k: round(v, 4) for k, v in lexical.items()},
                    "lexical_only_probe_fp_rate": round(probe_lexical_fp / len(probes), 4),
                },
                "queries": rows, "probes": probes, "sweep": sweep}
        if args.extra_wiki:
            extra = work / "extra"
            shutil.copytree(args.extra_wiki, extra, ignore=shutil.ignore_patterns(".wiki-cache", ".obsidian", ".git"))
            probe = Probe(wiki_index, wiki_search, wiki_mcp_common.normalize_wiki_root(extra), embedder, embed)
            try:
                titles = []
                for page in probe.index.pages:
                    title = str(page["meta"].get("title") or "").strip()
                    if not title:
                        continue
                    pairs = probe.distances(title)
                    own = nearest(pairs, page["slug"])
                    if own is None:  # 埋め込んだセクションがないページ（本文が空など）
                        continue
                    other = next((d for s, d in pairs if s != page["slug"]), None)
                    titles.append({"slug": page["slug"], "title_distance": round(own, 4),
                                   "nearest_other": round(other, 4) if other is not None else None})
                probes = {name: [round(probe.distances(t)[0][1], 4) for t in texts] for name, texts in PROBES.items()}
                report["extra_wiki"] = {
                    "pages": len(probe.index.pages), "sections": len(probe.index.sections),
                    "title_queries": len(titles),
                    "title_distance_max": max(t["title_distance"] for t in titles) if titles else None,
                    "titles_over_current": sum(1 for t in titles if t["title_distance"] > original),
                    "probe_nearest_min": {k: min(v) for k, v in probes.items()},
                    "probes_under_current": {k: sum(1 for d in v if d <= original) for k, v in probes.items()},
                    "title_distances": sorted(t["title_distance"] for t in titles),
                    "probe_distances": probes}
            finally:
                probe.close()
    finally:
        wiki_index.MODEL["max_distance"] = original
        shutil.rmtree(work, ignore_errors=True)
    OUT.mkdir(parents=True, exist_ok=True)
    (OUT / "threshold.json").write_text(json.dumps(report, ensure_ascii=False, indent=1) + "\n", encoding="utf-8",
                                        newline="\n")
    print(json.dumps({k: v["summary"] for k, v in report["sets"].items()}, ensure_ascii=False, indent=1))
    if "extra_wiki" in report:
        print(json.dumps({k: v for k, v in report["extra_wiki"].items()
                          if k not in ("title_distances", "probe_distances")}, ensure_ascii=False, indent=1))


if __name__ == "__main__":
    main()
