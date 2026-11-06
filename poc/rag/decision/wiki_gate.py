"""E8: wiki の評価ゲートを、R-130（ONNX fp32）と Sudachi の分かち書きで通せるかを測る。

(a) 較正: wiki の en と ja の評価セットで、R-130 の正例の正解までの距離と、負例の最も近いセクションまでの距離を測り、
    偽陽性を 0 に保てる max_distance の範囲を求める。e5-small の 0.193 と同じ決め方（wiki_search.py の EMBED_MODELS の注記）。
    natural の wiki 47 問と負例 12 問でも同じ距離を測り、選んだ値で確かめる。
(b) ゲート: run_eval.py の evaluate を、SCRIPT を wiki_search_variant.py に差し替えて動かす。
    変種は e5（再現）、r130、r130 + sudachi の 3 つ。どれも --gate と --baseline（許容幅 0.05）で判定する。
(c) Sudachi: r130 + sudachi の page と section の行（埋め込みを使わない語彙だけの行）を、e5 の行（bigram）と比べる。
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
from pathlib import Path

import numpy as np

from decision_common import DWORK, HERE, R130_ONNX, WIKI_EVAL, WIKI_SCRIPTS, save
from common import WORK, limit_threads, load_natural

VARIANTS = {
    "e5": {"DECISION_EMBED": "e5", "DECISION_TOKENIZER": "bigram"},
    "r130": {"DECISION_EMBED": "r130", "DECISION_TOKENIZER": "bigram"},
    "r130-sudachi": {"DECISION_EMBED": "r130", "DECISION_TOKENIZER": "sudachi"},
    # 案 2: 語彙のエンジンだけを Tantivy にし、トークンは wiki の bigram のまま
    "r130-tantivy": {"DECISION_EMBED": "r130", "DECISION_TOKENIZER": "bigram", "DECISION_LEXICAL": "tantivy"},
}


def base_env():
    os.environ["DECISION_WIKI_SCRIPTS"] = str(WIKI_SCRIPTS)
    os.environ["DECISION_ONNX_DIR"] = str(R130_ONNX)
    os.environ["FASTEMBED_CACHE_PATH"] = str(DWORK / "fastembed-wiki")
    os.environ.setdefault("PYTHONUTF8", "1")


def import_run_eval():
    sys.path.insert(0, str(WIKI_EVAL))
    sys.path.insert(0, str(WIKI_SCRIPTS))
    import run_eval
    return run_eval


def calibrate(run_eval):
    """R-130 の距離の分布。フィルターは無視し、全セクションを候補にする（較正の近似。README に書く）。"""
    os.environ.update(VARIANTS["r130"], DECISION_MAX_DISTANCE="2")
    import wiki_search_variant as wv
    ws = wv.ws
    model, _, _ = ws.load_local_embedding_backend()
    result = {}
    for set_name, spec in run_eval.SETS.items():
        pages = ws.collect_pages(spec["corpus"])
        sections = ws.collect_sections(pages)
        vectors = np.array(ws.embed_passages(model, [s["searchable_text"] for s in sections]), dtype=np.float32)
        slugs = [s["page"]["slug"] for s in sections]
        queries = json.loads(spec["queries"].read_text(encoding="utf-8"))
        positives, negatives = [], []
        for q in queries:
            qv = np.array(ws.embed_query(model, q["query"]), dtype=np.float32)
            distance = 1 - vectors @ qv
            if q["kind"] == "negative":
                negatives.append({"id": q["id"], "nearest": float(distance.min())})
            else:
                needed = [float(min(d for d, slug in zip(distance, slugs) if slug == e)) for e in q["expected"] if e in slugs]
                positives.append({"id": q["id"], "kind": q["kind"], "needed_max": max(needed), "needed_min": min(needed)})
        result[set_name] = {"sections": len(sections), "positives": positives, "negatives": negatives,
                            "positive_needed_max": max(p["needed_max"] for p in positives),
                            "positive_needed_p90": float(np.percentile([p["needed_max"] for p in positives], 90)),
                            "negative_nearest_min": min(n["nearest"] for n in negatives)}
    # natural（rag の評価セット）の wiki 47 問と負例 12 問。既存の R-130 ベクトル（GPU）を使う。
    rows, queries = load_natural()
    vectors = np.load(WORK / "vectors/natural/R-130.npy")
    qvectors = np.load(WORK / "vectors/natural/R-130.queries.npy")
    labels = [r["label"] for r in rows]
    natural_pos, natural_neg = [], []
    for q, qv in zip(queries, qvectors):
        distance = 1 - vectors @ qv
        if not q["expected"]:
            natural_neg.append({"id": q["id"], "nearest": float(distance.min())})
        elif str(q["id"]).startswith("j"):  # j で始まる 47 問が wiki の問い（p は PDF、n は負例）
            hits = [d for d, label in zip(distance, labels) if label in set(q["expected"])]
            if hits:
                natural_pos.append({"id": q["id"], "needed": float(min(hits))})
    result["natural"] = {"positives": natural_pos, "negatives": natural_neg}
    return result


def choose(calibration):
    """正例の最大と負例の最小が分かれていれば中ほど、分かれていなければ負例の最小の直前（偽陽性 0 の上限）。"""
    pos = max(calibration[s]["positive_needed_max"] for s in ("en", "ja"))
    neg = min(calibration[s]["negative_nearest_min"] for s in ("en", "ja"))
    separable = pos < neg
    value = round((pos + neg) / 2, 3) if separable else round(neg - 0.002, 3)
    natural_neg = calibration["natural"]["negatives"]
    natural_pos = calibration["natural"]["positives"]
    return {"max_distance": value, "separable": separable, "positive_needed_max": pos, "negative_nearest_min": neg,
            "range": [pos, neg] if separable else None,
            "natural_negatives_within": sum(n["nearest"] <= value for n in natural_neg), "natural_negatives": len(natural_neg),
            "natural_positives_within": sum(p["needed"] <= value for p in natural_pos), "natural_positives": len(natural_pos)}


def run_gate(run_eval, variant, max_distance):
    os.environ.pop("DECISION_LEXICAL", None)
    os.environ.update(VARIANTS[variant], DECISION_MAX_DISTANCE=str(max_distance))
    run_eval.SCRIPT = HERE / "wiki_search_variant.py"
    out = {}
    for set_name, spec in run_eval.SETS.items():
        queries = json.loads(spec["queries"].read_text(encoding="utf-8"))
        saved = DWORK / f"wiki-gate/{variant}-{set_name}.json"
        buffer = io.StringIO()
        with tempfile.TemporaryDirectory() as tmp:
            # en のコーパスはリポジトリの中にあり、そのまま使うと .wiki-cache/ がサブモジュールに作られる。複製して使う。
            copied = dict(spec)
            if not spec.get("nfd_files"):
                copied["corpus"] = Path(tmp) / "corpus"
                shutil.copytree(spec["corpus"], copied["corpus"], ignore=shutil.ignore_patterns(".wiki-cache"))
            run_eval.CORPUS = run_eval.prepare_corpus(copied, tmp)
            args = argparse.Namespace(gate=True, baseline="AUTO", save=str(saved), set=set_name)
            with contextlib.redirect_stdout(buffer), contextlib.redirect_stderr(buffer):
                code = run_eval.evaluate(args, queries)
        report = json.loads(saved.read_text(encoding="utf-8"))
        baseline = json.loads((run_eval.BASELINES / f"{set_name}.json").read_text(encoding="utf-8"))["metrics"]
        out[set_name] = {"exit_code": code, "metrics": report["metrics"], "by_kind": report["by_kind"],
                         "baseline": baseline, "baseline_failures": run_eval.baseline_failures(report["metrics"], baseline),
                         "log": buffer.getvalue()[-3000:]}
        print(variant, set_name, "exit", code, {m: round(v["recall@10"], 3) for m, v in report["metrics"].items()}, flush=True)
    return out


def compare_lexical(gates, variant):
    """bigram の wiki の BM25（r130）と variant を、ページとセクションの行（語彙だけ）とハイブリッドの行で比べる。"""
    return {f"{s}-{m}": {k: {"wiki_bm25": gates["r130"][s]["metrics"][m][k], variant: gates[variant][s]["metrics"][m][k]}
                         for k in ("recall@10", "mrr", "fp_rate")}
            for s in ("en", "ja") for m in ("page", "section", "hybrid")}


def add_variant(run_eval, variant):
    """保存済みの wiki-gate.json に、variant のゲートだけを足す（較正は保存済みの値を使う）。"""
    from decision_common import load
    report = load("wiki-gate.json")
    report.pop("env", None)
    report["gates"][variant] = run_gate(run_eval, variant, report["chosen"]["max_distance"])
    report["passed"][variant] = all(g["exit_code"] == 0 for g in report["gates"][variant].values())
    report[f"{variant}_vs_wiki_bm25"] = compare_lexical(report["gates"], variant)
    save("wiki-gate.json", report)


def main():
    limit_threads()
    base_env()
    (DWORK / "wiki-gate").mkdir(parents=True, exist_ok=True)
    run_eval = import_run_eval()
    if len(sys.argv) > 2 and sys.argv[1] == "--add":
        return add_variant(run_eval, sys.argv[2])
    calibration = calibrate(run_eval)
    chosen = choose(calibration)
    print("較正", chosen, flush=True)
    gates = {variant: run_gate(run_eval, variant, chosen["max_distance"]) for variant in VARIANTS}
    sudachi = {}
    for set_name in ("en", "ja"):
        for mode in ("page", "section"):
            bigram = gates["e5"][set_name]["by_kind"][mode]
            sud = gates["r130-sudachi"][set_name]["by_kind"][mode]
            sudachi[f"{set_name}-{mode}"] = {kind: {"bigram_recall@10": bigram[kind]["recall@10"], "sudachi_recall@10": sud[kind]["recall@10"],
                                                    "bigram_fp_rate": bigram[kind]["fp_rate"], "sudachi_fp_rate": sud[kind]["fp_rate"]}
                                             for kind in bigram}
    passed = {variant: all(g["exit_code"] == 0 for g in result.values()) for variant, result in gates.items()}
    save("wiki-gate.json", {
        "purpose": "wiki の評価ゲートを R-130 と Sudachi で通せるか（max_distance の較正を含む）",
        "calibration": calibration, "chosen": chosen, "gates": gates, "sudachi_by_kind": sudachi, "passed": passed,
        "criterion": "較正で偽陽性 0 の範囲がある。--gate と --baseline（recall@10 と MRR の低下 ≤ 0.05、fp_rate の上昇 ≤ 0.05）に合格する"})


if __name__ == "__main__":
    main()
