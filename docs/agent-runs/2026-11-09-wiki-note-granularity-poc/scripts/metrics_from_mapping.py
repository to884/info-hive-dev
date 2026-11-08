"""人が埋めた対応づけの表から、一致の指標と必須条件を計算する。

人が埋める列（tabulate.py が作る PRIVATE/mapping/ の表）:
    <資料>-candidates.csv
        cluster_id       同じ知見に同じ ID を付ける（例 R01）。知見でない候補（ソースにない、知見と呼べない）は "-"
        faithful         ソースに忠実なら "o"、ソースにないことを述べていれば "x"（捏造）
        conditions_kept  成り立つ条件を保っていれば "o"、落としていれば "x"、条件のない知見は空でよい
    <資料>-pages.csv
        page_cluster     新しく作るページのうち、同じページとみなすものに同じ ID を付ける（例 P01）
    <資料>-gold.csv（任意）
        cluster_id の列に、その資料から抜き出すべき知見を並べる。なければ、2 件以上の実行が出した知見を正解とみなす

使い方:
    python metrics_from_mapping.py [--mapping-dir <dir>] [--out ../metrics/agreement.md]

合格の目安（レポートの第 8 節。提案値）: 知見の recall 90%、配置先の一致率 85%、同居の F1 0.90。
出典への忠実さ（捏造 0 件）と条件の保持（脱落 0 件）は、加重点で相殺しない必須条件である。
"""
from __future__ import annotations

import argparse
import csv
import os
import statistics
from collections import defaultdict
from itertools import combinations
from pathlib import Path

HERE = Path(__file__).resolve().parent
RUN_DIR = HERE.parent
PRIVATE = Path(os.environ.get("POC_PRIVATE_DIR") or Path.home() / "info-hive-dev-private" / RUN_DIR.name)
SOURCES = ("O", "R", "V")
METHODS = ("current", "hybrid")
TARGET = {"recall": 0.90, "placement": 0.85, "colocation_f1": 0.90}


def read_csv(p: Path) -> list[dict]:
    with p.open(encoding="utf-8-sig", newline="") as f:
        return list(csv.DictReader(f))


def mean(xs):
    xs = [x for x in xs if x is not None]
    return round(statistics.mean(xs), 3) if xs else None


def place_key(row: dict, page_cluster: dict) -> str:
    a = row["action"]
    if a == "source_only":
        return "source"
    kind = f"{row['page_type']}/{row['page_kind'] or '-'}"
    if a == "update":
        return f"existing:{row['page_slug']}|{kind}"
    pc = page_cluster.get((row["blind_id"], row["page_slug"]))
    return f"new:{pc or '未対応:' + row['page_slug']}|{kind}"


def f1(a: set, b: set) -> float | None:
    if not a and not b:
        return None
    return 2 * len(a & b) / (len(a) + len(b))


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--mapping-dir", type=Path, default=PRIVATE / "mapping")
    ap.add_argument("--out", type=Path, default=RUN_DIR / "metrics" / "agreement.md")
    args = ap.parse_args()
    key = {r["blind_id"]: r for r in read_csv(RUN_DIR / "mapping" / "blind-key.csv")}
    L = ["# 人の対応づけからの指標", "", f"対応づけの表: `{args.mapping_dir}`", ""]
    L += ["| 資料 | 方式 | 捏造 | 条件の脱落 | 未記入の行 | 正解の知見 | recall（平均） | precision（平均） "
          "| 配置先の一致率 | うち別モデル | うち同モデルの別の回 | 同居の F1 | 判定 |",
          "| --- | --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | --- |"]
    for s in SOURCES:
        cpath = args.mapping_dir / f"{s}-candidates.csv"
        if not cpath.exists():
            L.append(f"| {s} | | | | | | | | | | | | 表がない |")
            continue
        rows = read_csv(cpath)
        pages = read_csv(args.mapping_dir / f"{s}-pages.csv") if (args.mapping_dir / f"{s}-pages.csv").exists() else []
        page_cluster = {(p["blind_id"], p["slug"]): p["page_cluster"].strip() for p in pages if p["page_cluster"].strip()}
        gold_p = args.mapping_dir / f"{s}-gold.csv"
        for m in METHODS:
            mrows = [r for r in rows if key[r["blind_id"]]["method"] == m]
            blank = sum(1 for r in mrows if not r["cluster_id"].strip())
            fabricated = sum(1 for r in mrows if r["faithful"].strip().lower() == "x")
            dropped = sum(1 for r in mrows if r["conditions_kept"].strip().lower() == "x")
            runs = sorted({r["blind_id"] for r in mrows})
            per_run_clusters = defaultdict(set)
            per_run_place = defaultdict(lambda: defaultdict(set))
            for r in mrows:
                cid = r["cluster_id"].strip()
                if not cid or cid == "-":
                    continue
                per_run_clusters[r["blind_id"]].add(cid)
                per_run_place[r["blind_id"]][cid].add(place_key(r, page_cluster))
            all_runs_of_source = sorted({r["blind_id"] for r in rows})
            if gold_p.exists():
                gold = {g["cluster_id"].strip() for g in read_csv(gold_p) if g["cluster_id"].strip()}
                gold_note = "gold.csv"
            else:
                cnt = defaultdict(int)
                for b in all_runs_of_source:
                    for cid in {r["cluster_id"].strip() for r in rows if r["blind_id"] == b}:
                        if cid and cid != "-":
                            cnt[cid] += 1
                gold = {c for c, n in cnt.items() if n >= 2}
                gold_note = "2 件以上"
            recall = [len(per_run_clusters[b] & gold) / len(gold) if gold else None for b in runs]
            precision = [len(per_run_clusters[b] & gold) / len(per_run_clusters[b]) if per_run_clusters[b] else None
                         for b in runs]
            agree = {"all": [], "cross": [], "same": []}
            f1s = []
            for a, b in combinations(runs, 2):
                kind = "same" if key[a]["model"] == key[b]["model"] else "cross"
                common = per_run_clusters[a] & per_run_clusters[b]
                for cid in common:
                    ok = per_run_place[a][cid] == per_run_place[b][cid]
                    agree["all"].append(ok)
                    agree[kind].append(ok)

                def pairs(run):
                    out = set()
                    for c1, c2 in combinations(sorted(common), 2):
                        k1 = {k for k in per_run_place[run][c1] if k != "source"}
                        k2 = {k for k in per_run_place[run][c2] if k != "source"}
                        if k1 & k2:
                            out.add((c1, c2))
                    return out
                f1s.append(f1(pairs(a), pairs(b)))
            rate = lambda xs: round(sum(xs) / len(xs), 3) if xs else None
            rec, pla, col = mean(recall), rate(agree["all"]), mean(f1s)
            if blank:
                verdict = "対応づけが終わっていない"
            elif fabricated or dropped:
                verdict = "不合格（必須条件）"
            elif None in (rec, pla) or rec < TARGET["recall"] or pla < TARGET["placement"] or (
                    col is not None and col < TARGET["colocation_f1"]):
                verdict = "目安に届かない"
            else:
                verdict = "目安を満たす"
            L.append(f"| {s} | {m} | {fabricated} | {dropped} | {blank} | {len(gold)}（{gold_note}） | {rec} | "
                     f"{mean(precision)} | {pla} | {rate(agree['cross'])} | {rate(agree['same'])} | {col} | {verdict} |")
    L += ["", "- 配置先は、`source_only`、既存ページのスラッグ、新規ページの `page_cluster` と、`type` と `kind` の組で比べた。"
          "`###` の節の見出しは比べていない。",
          "- 同居の F1 は、2 つの実行が共通に出した知見の組について、「source 以外の同じページに置く」の判定を比べた。"
          "すべての知見が別々のページか source に置かれると正例がなく、値は空になる。",
          f"- 目安: recall {TARGET['recall']}、配置先の一致率 {TARGET['placement']}、同居の F1 {TARGET['colocation_f1']}（提案値）。"]
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text("\n".join(L) + "\n", encoding="utf-8", newline="\n")
    print(args.out.read_text(encoding="utf-8"))


if __name__ == "__main__":
    main()
