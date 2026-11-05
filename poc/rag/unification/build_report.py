"""計測の JSON から HTML のレポートを作る。数値はすべて JSON から読み、手で書き写さない。

出力: docs/research/embedding-backend-unification-2026-11-05.html
"""
from __future__ import annotations

import html
import math
from datetime import date

from common import OUT, read_json

REPORT = OUT.parent / "embedding-backend-unification-2026-11-05.html"
MIB = 2 ** 20


def e(value) -> str:
    return html.escape(str(value))


def mib(value) -> str:
    return f"{value / MIB:,.0f} MiB" if value < 10 * 1024 * MIB else f"{value / 1024 ** 3:,.1f} GiB"


def ms(value) -> str:
    return f"{value:,.0f} ms" if value >= 100 else f"{value:,.1f} ms"


def score_cell(value) -> str:
    level = "hi" if value >= 7 else "mid" if value > 3 else "lo"
    return f'<td class="num score {level}">{value:.1f}</td>'


def load():
    return {name: read_json(OUT / f"{name}.json") for name in
            ("scores", "model-accuracy", "runtime-parity", "wiki-scale", "install-results", "lexical-bench-subset", "lexical-bench-full", "candidates", "onnx-feasibility")}


def rows_table(rows, caption, show_knob=True):
    ok = sorted([r for r in rows if r["status"] == "ok"], key=lambda r: (-r["score"]["minimum"], r["speed_ms"]))
    out = [f'<table class="data"><caption>{e(caption)}</caption><thead><tr><th>組（モデル × DB + 語彙）</th><th>計測</th>'
           '<th class="num">検索 p95</th><th class="num">容量</th><th class="num">再現率@30</th>'
           '<th class="num">速度</th><th class="num">容量</th><th class="num">精度</th><th class="num">最小</th>'
           + ('<th>動作点</th>' if show_knob else '') + '</tr></thead><tbody>']
    for r in ok:
        flags = []
        if r["all_high"]:
            flags.append('<span class="tag good">3 つとも 7 以上</span>')
        if not r["target_reached"]:
            flags.append('<span class="tag warn">目標未達</span>')
        measured = "実測" if r["measured"] == "実測" else "合成"
        out.append(f'<tr class="{"best" if r["all_high"] else ""}"><td>{e(r["combination"])} {" ".join(flags)}</td>'
                   f'<td><span class="mark {"m" if measured == "実測" else "c"}">{measured}</span></td>'
                   f'<td class="num">{ms(r["speed_ms"])}</td><td class="num">{mib(r["size_bytes"])}</td><td class="num">{r["accuracy"]:.3f}</td>'
                   + score_cell(r["score"]["speed"]) + score_cell(r["score"]["size"]) + score_cell(r["score"]["accuracy"])
                   + f'<td class="num"><strong>{r["score"]["minimum"]:.1f}</strong></td>'
                   + (f'<td class="small">{e(r.get("knob", ""))}</td>' if show_knob else '') + '</tr>')
    failed = [r for r in rows if r["status"] != "ok"]
    for r in failed:
        out.append(f'<tr><td>{e(r["combination"])}</td><td colspan="{9 if show_knob else 8}">失敗: {e(r.get("error", ""))[:200]}</td></tr>')
    out.append("</tbody></table>")
    return "\n".join(out)


def scatter(rows):
    """全量の組を、x = 検索 p95（対数）、y = 容量（対数）に置く。色は精度の点、形は実測（丸）と合成（菱形）。"""
    ok = [r for r in rows if r["status"] == "ok"]
    width, height, left, bottom, top, right = 760, 440, 70, 50, 30, 30
    xs = [math.log10(r["speed_ms"]) for r in ok]
    ys = [math.log10(r["size_bytes"] / MIB) for r in ok]
    x0, x1 = math.floor((min(xs) - .05) * 2) / 2, math.ceil((max(xs) + .05) * 2) / 2
    y0, y1 = math.floor((min(ys) - .08) * 4) / 4, math.ceil((max(ys) + .08) * 4) / 4

    def px(x):
        return left + (x - x0) / (x1 - x0) * (width - left - right)

    def py(y):
        return height - bottom - (y - y0) / (y1 - y0) * (height - bottom - top)

    parts = [f'<svg viewBox="0 0 {width} {height}" role="img" aria-labelledby="scatter-title scatter-desc" class="chart">',
             '<title id="scatter-title">全量の組の検索 p95 と容量</title>',
             '<desc id="scatter-desc">横軸は検索 p95（対数）、縦軸は容量（対数）。左下ほど良い。色は精度の点。</desc>']
    # 閾値 1 秒の線
    if x0 <= 3 <= x1:
        parts.append(f'<line x1="{px(3):.1f}" y1="{top}" x2="{px(3):.1f}" y2="{height - bottom}" class="limit"/>'
                     f'<text x="{px(3) + 4:.1f}" y="{top + 12}" class="axis">閾値 1 秒</text>')
    for tick in [10, 30, 100, 300, 1000, 3000, 10000]:
        x = math.log10(tick)
        if x0 <= x <= x1:
            parts.append(f'<line x1="{px(x):.1f}" y1="{height - bottom}" x2="{px(x):.1f}" y2="{height - bottom + 5}" class="tick"/>'
                         f'<text x="{px(x):.1f}" y="{height - bottom + 18}" text-anchor="middle" class="axis">{tick:,} ms</text>')
    for tick in [256, 512, 1024, 2048, 4096, 8192]:
        y = math.log10(tick)
        if y0 <= y <= y1:
            parts.append(f'<line x1="{left - 5}" y1="{py(y):.1f}" x2="{left}" y2="{py(y):.1f}" class="tick"/>'
                         f'<text x="{left - 8}" y="{py(y) + 4:.1f}" text-anchor="end" class="axis">{tick / 1024:g} GiB</text>' if tick >= 1024 else
                         f'<line x1="{left - 5}" y1="{py(y):.1f}" x2="{left}" y2="{py(y):.1f}" class="tick"/>'
                         f'<text x="{left - 8}" y="{py(y) + 4:.1f}" text-anchor="end" class="axis">{tick} MiB</text>')
    parts.append(f'<line x1="{left}" y1="{height - bottom}" x2="{width - right}" y2="{height - bottom}" class="frame"/>'
                 f'<line x1="{left}" y1="{top}" x2="{left}" y2="{height - bottom}" class="frame"/>'
                 f'<text x="{(width + left) / 2}" y="{height - 8}" text-anchor="middle" class="axis">検索 p95（クエリ埋め込み + DB、対数）</text>'
                 f'<text x="16" y="{(height - bottom + top) / 2}" transform="rotate(-90 16 {(height - bottom + top) / 2})" text-anchor="middle" class="axis">容量（対数）</text>')
    for r, x, y in zip(ok, xs, ys):
        level = "hi" if r["score"]["accuracy"] >= 7 else "mid" if r["score"]["accuracy"] > 3 else "lo"
        cx, cy = px(x), py(y)
        label = r["combination"].replace(" + Tantivy", " +T")
        if r["measured"] == "実測":
            parts.append(f'<circle cx="{cx:.1f}" cy="{cy:.1f}" r="7" class="pt {level}"><title>{e(r["combination"])}</title></circle>')
        else:
            parts.append(f'<rect x="{cx - 6:.1f}" y="{cy - 6:.1f}" width="12" height="12" transform="rotate(45 {cx:.1f} {cy:.1f})" class="pt {level}"><title>{e(r["combination"])}</title></rect>')
        anchor = "end" if cx > width * .7 else "start"
        dx = -10 if anchor == "end" else 10
        parts.append(f'<text x="{cx + dx:.1f}" y="{cy - 9:.1f}" text-anchor="{anchor}" class="lbl">{e(label)}</text>')
    parts.append("</svg>")
    return "\n".join(parts)


def main():
    d = load()
    s = d["scores"]
    subset, full = s["subset"], s["full"]
    full_ok = {r["combination"]: r for r in full if r["status"] == "ok"}
    sub_ok = {r["combination"]: r for r in subset if r["status"] == "ok"}
    rec = full_ok["R-130 × usearch HNSW f16 + Tantivy"]
    alt = full_ok["R-130 × FAISS IVF_SQ8 + Tantivy"]
    cur = full_ok["R-130 × LanceDB IVF_SQ"]
    qd = full_ok["R-130 × Qdrant HNSW f32"]
    wiki_now = full_ok["E-s × sqlite-vec f32"]
    lex_full = {r["engine"]: r for r in d["lexical-bench-full"]["results"]}
    lex_sub = {r["engine"]: r for r in d["lexical-bench-subset"]["results"]}
    ws = d["wiki-scale"]
    runtimes = {(r["model"], r["runtime"]): r for r in ws["runtimes"]}
    parity = {(r["model"], r["runtime"]): r for r in d["runtime-parity"]["results"]}
    cli = ws["current_wiki_cli"]
    install = {r["configuration"]: r for r in d["install-results"]["results"]}
    models = d["model-accuracy"]["models"]
    dbs = {r["candidate"]: r for r in ws["databases"]}
    conc = {r["candidate"]: r for r in ws["concurrency"]}

    model_rows = []
    names = {"E-s": "multilingual-e5-small", "E-l": "multilingual-e5-large", "R-30": "ruri-v3-30m", "R-130": "ruri-v3-130m", "R-310": "ruri-v3-310m", "S-ja": "static-embedding-japanese"}
    for key in ("R-310", "R-130", "R-30", "S-ja", "E-l", "E-s"):
        m = models[key]
        hy = m["hybrid"]
        note = f"{m['over_model_limit_ratio'] * 100:.1f}% のチャンクが 512 トークンで切られる" if m["over_model_limit_ratio"] else ""
        model_rows.append(f'<tr><td><strong>{key}</strong> {e(names[key])}</td><td class="num">{m["dimension"]}</td>'
                          f'<td class="num">{hy["pdf"]["recall_at_30"]:.3f}</td><td class="num">{hy["wiki"]["recall_at_30"]:.3f}</td>'
                          f'<td class="num">{m["dense_only"]["pdf"]["recall_at_30"]:.3f}</td><td class="small">{e(note)}</td></tr>')
    lexical_only = d["model-accuracy"]["lexical_only"]["pdf"]["recall_at_30"]

    runtime_rows = []
    for key, kind, label in (("R-30", "onnx-fp32", "ONNX fp32"), ("R-130", "onnx-fp32", "ONNX fp32"), ("R-130", "torch-cpu", "torch CPU"),
                             ("R-310", "onnx-fp32", "ONNX fp32"), ("E-s", "fastembed-fp16", "fastembed fp16")):
        idle = runtimes.get((key, kind))
        par = parity.get((key, kind))
        runtime_rows.append(f'<tr><td>{key} {label}</td><td class="num">{idle["cold_total_seconds_median"]:.1f} 秒</td>'
                            f'<td class="num">{idle["warm_query_p95_ms_median"]:.1f} ms</td>'
                            f'<td class="num">{par["query_p95_ms"]:.1f} ms</td>'
                            f'<td class="num">{(par["query_top30_overlap_with_gpu_queries"] or 0):.3f}</td>'
                            f'<td class="num">{idle["trials"][0]["rss_bytes"] / MIB:,.0f} MiB</td></tr>')

    db_rows = []
    for name in ("sqlite-vec f32", "sqlite-vec int8", "LanceDB IVF_SQ", "Qdrant HNSW f32", "usearch HNSW f16", "FAISS IVF_SQ8", "FAISS HNSW", "Chroma HNSW"):
        r = dbs[name]
        c = conc[name]
        writer_ok = c["writer"]["returncode"] == 0
        visible = "開き直さずに見える" if c["new_row_visible_without_reopen"] else "開き直すと見える" if c["new_row_visible_after_reopen"] else "見えない"
        if not writer_ok:
            visible = "書き込みが失敗（Permission denied）"
        db_rows.append(f'<tr><td>{e(name)}</td><td class="num">{r["build"]["size_bytes"] / MIB:,.1f} MiB</td>'
                       f'<td class="num">{r["cold_open_seconds_median"]:.2f} 秒</td><td class="num">{r["warm_search_p95_ms_median"]:.1f} ms</td>'
                       f'<td class="num">{c["writer"].get("append_seconds", float("nan")):.2f} 秒</td><td>{visible}</td></tr>')

    install_rows = []
    for name in ("現行 rag（torch + LanceDB）", "torch のみ", "共通のみ", "fastembed のみ", "fastembed + LanceDB", "fastembed + sqlite-vec",
                 "fastembed + Qdrant", "fastembed + usearch", "fastembed + FAISS", "fastembed + Chroma", "fastembed + usearch + Tantivy", "fastembed + FAISS + Tantivy"):
        r = install[name]
        install_rows.append(f'<tr><td>{e(name)}</td><td class="num">{r["runs"][0]["seconds"]:.0f} 秒</td><td class="num">{r["cache_bytes"] / MIB:,.0f} MiB</td></tr>')

    component_rows = "".join(
        f'<tr><td>{e(r["combination"])}</td><td class="num">{r["component_recall"]["lexical_only_recall_at_30"]:.3f}</td>'
        f'<td class="num">{r["component_recall"]["dense_only_recall_at_30"]:.3f}</td><td class="num">{r["accuracy"]:.3f}</td></tr>'
        for r in sorted(full_ok.values(), key=lambda r: -r["accuracy"]) if r.get("component_recall"))
    excluded = "".join(f'<li><strong>{e(x["candidate"])}</strong>: {e(x["reason"])}</li>' for x in d["candidates"]["excluded"])
    today = date.today().isoformat()

    body = f"""<!doctype html>
<html lang="ja">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>埋め込みモデルとベクター DB の統一</title>
<style>
:root {{
  --bg: #f7f6f2; --paper: #ffffff; --ink: #1d2326; --muted: #5b6468; --line: #d9d6cc; --accent: #1f5f8b;
  --good: #1e7a4f; --good-bg: #e3f3ea; --mid: #8a6a12; --mid-bg: #fbf1d6; --bad: #a33a2c; --bad-bg: #f8e3df;
  --code: #eef1f2; --mono: "Cascadia Code", "Consolas", "Menlo", monospace;
  --sans: "BIZ UDPGothic", "Yu Gothic UI", "Hiragino Sans", "Noto Sans JP", system-ui, sans-serif;
}}
* {{ box-sizing: border-box; }}
body {{ margin: 0; background: var(--bg); color: var(--ink); font: 15px/1.75 var(--sans); }}
.layout {{ display: grid; grid-template-columns: 240px minmax(0, 1fr); gap: 32px; max-width: 1280px; margin: 0 auto; padding: 24px; }}
nav.toc {{ position: sticky; top: 16px; align-self: start; font-size: 13px; border-left: 3px solid var(--accent); padding-left: 12px; }}
nav.toc a {{ display: block; color: var(--muted); text-decoration: none; padding: 2px 0; }}
nav.toc a:hover, nav.toc a:focus {{ color: var(--accent); outline: none; text-decoration: underline; }}
main {{ min-width: 0; }}
header h1 {{ font-size: 28px; line-height: 1.35; margin: 0 0 6px; }}
header p.lede {{ color: var(--muted); margin: 0 0 20px; }}
section {{ background: var(--paper); border: 1px solid var(--line); border-radius: 6px; padding: 20px 24px; margin: 0 0 20px; }}
h2 {{ font-size: 20px; margin: 0 0 12px; border-bottom: 1px solid var(--line); padding-bottom: 6px; }}
h3 {{ font-size: 16px; margin: 20px 0 8px; }}
.tldr {{ border-left: 6px solid var(--good); }}
.verdict {{ display: grid; grid-template-columns: repeat(auto-fit, minmax(200px, 1fr)); gap: 12px; margin: 12px 0; }}
.card {{ border: 1px solid var(--line); border-radius: 6px; padding: 10px 14px; background: #fbfbf9; }}
.card .k {{ font-size: 12px; color: var(--muted); }}
.card .v {{ font-size: 18px; font-weight: 700; }}
table.data {{ border-collapse: collapse; width: 100%; font-size: 13px; margin: 8px 0 16px; }}
table.data caption {{ text-align: left; font-weight: 700; padding: 4px 0; }}
table.data th, table.data td {{ border-bottom: 1px solid var(--line); padding: 5px 8px; vertical-align: top; }}
table.data th {{ background: #f0efe9; text-align: left; position: sticky; top: 0; }}
.num {{ text-align: right; font-variant-numeric: tabular-nums; white-space: nowrap; }}
.small {{ font-size: 12px; color: var(--muted); }}
tr.best td {{ background: var(--good-bg); }}
.score.hi {{ color: var(--good); font-weight: 700; }}
.score.mid {{ color: var(--mid); }}
.score.lo {{ color: var(--bad); }}
.tag {{ display: inline-block; font-size: 11px; border-radius: 3px; padding: 0 5px; margin-left: 4px; border: 1px solid; white-space: nowrap; }}
.tag.good {{ color: var(--good); border-color: var(--good); }}
.tag.warn {{ color: var(--bad); border-color: var(--bad); }}
.mark {{ font-size: 11px; padding: 0 5px; border-radius: 3px; }}
.mark.m {{ background: #e5edf3; color: var(--accent); }}
.mark.c {{ background: var(--mid-bg); color: var(--mid); }}
.wrap {{ overflow-x: auto; }}
code, pre {{ font-family: var(--mono); font-size: 13px; background: var(--code); border-radius: 3px; }}
code {{ padding: 0 4px; }}
pre {{ padding: 10px 12px; overflow-x: auto; }}
.note {{ border-left: 4px solid var(--mid); background: var(--mid-bg); padding: 8px 12px; margin: 10px 0; }}
.key {{ border-left: 4px solid var(--accent); background: #e9f0f6; padding: 8px 12px; margin: 10px 0; }}
svg.chart, svg.diagram {{ width: 100%; height: auto; background: #fcfcfa; border: 1px solid var(--line); border-radius: 4px; }}
svg .axis {{ font-size: 11px; fill: var(--muted); }}
svg .lbl {{ font-size: 11px; fill: var(--ink); }}
svg .frame, svg .tick {{ stroke: #8b9295; stroke-width: 1; }}
svg .limit {{ stroke: var(--bad); stroke-dasharray: 4 3; }}
svg .pt {{ stroke: #263238; stroke-width: 1; }}
svg .pt.hi {{ fill: #4caf7d; }} svg .pt.mid {{ fill: #e0b64a; }} svg .pt.lo {{ fill: #d0705f; }}
svg .box {{ fill: #ffffff; stroke: #59656b; stroke-width: 1.2; rx: 6; }}
svg .box.acc {{ fill: #e9f0f6; stroke: var(--accent); }}
svg .box.good {{ fill: var(--good-bg); stroke: var(--good); }}
svg .box.bad {{ fill: var(--bad-bg); stroke: var(--bad); }}
svg .t {{ font-size: 13px; fill: var(--ink); }}
svg .ts {{ font-size: 11px; fill: var(--muted); }}
svg .arrow {{ stroke: #59656b; stroke-width: 1.4; fill: none; marker-end: url(#ah); }}
details summary {{ cursor: pointer; color: var(--accent); }}
footer {{ color: var(--muted); font-size: 12px; padding: 8px 0 24px; }}
ul.tight li {{ margin: 2px 0; }}
@media (max-width: 760px) {{
  .layout {{ grid-template-columns: 1fr; padding: 12px; }}
  nav.toc {{ position: static; }}
  section {{ padding: 14px; }}
}}
@media print {{ nav.toc {{ display: none; }} .layout {{ display: block; }} section {{ break-inside: avoid; }} }}
</style>
</head>
<body>
<div class="layout">
<nav class="toc" aria-label="目次">
<a href="#tldr">1. 要約</a><a href="#req">2. 目的と要件</a><a href="#now">3. 現状</a><a href="#cand">4. 候補</a>
<a href="#model">5. モデルの精度</a><a href="#runtime">6. 実行系</a><a href="#stage1">7. 段階 1（10 万件）</a><a href="#lexical">8. 語彙検索</a>
<a href="#stage2">9. 段階 2（全量）と決定</a><a href="#wiki">10. wiki 規模</a><a href="#install">11. 導入の重さ</a><a href="#paths">12. 統一の形と移行</a>
<a href="#mcp">13. wiki の MCP 化</a><a href="#lose">14. 失うものと代替</a><a href="#adr">15. ADR 案</a><a href="#repro">16. 再現と出典</a>
</nav>
<main>
<header>
<h1>wiki と rag の埋め込みモデル・ベクター DB を統一する</h1>
<p class="lede">埋め込みモデル 6 種とベクター DB 13 方式の組を、検索スピード、DB の容量、精度の 3 つのスコアで実測して比べた。</p>
</header>

<section id="tldr" class="tldr">
<h2>1. 要約</h2>
<p><strong>wiki と rag の両方を、<code>cl-nagoya/ruri-v3-130m</code>（ONNX fp32）+ usearch（HNSW、f16）+ Tantivy（BM25）にそろえる。</strong>
全量 761,915 チャンクで 3 つのスコアがすべて 7 点以上になった組は 2 つあった。この組はそのうち最小の点が最も高い（{rec["score"]["minimum"]:.1f} 点）。
もう 1 つの FAISS IVF_SQ8 + Tantivy（{alt["score"]["minimum"]:.1f} 点）も要件を満たす。2 つの差は 60 問のうちの約 1 問と十数 ms で、実質的に同等である。</p>
<div class="verdict">
<div class="card"><div class="k">検索 p95（全量）</div><div class="v">{ms(rec["speed_ms"])}</div><div class="small">現行 rag {ms(cur["speed_ms"])}、現行 wiki の組 {ms(wiki_now["speed_ms"])}</div></div>
<div class="card"><div class="k">索引の容量（全量）</div><div class="v">{mib(rec["size_bytes"])}</div><div class="small">現行 rag {mib(cur["size_bytes"])}</div></div>
<div class="card"><div class="k">再現率@30（全量 60 問）</div><div class="v">{rec["accuracy"]:.3f}</div><div class="small">現行 rag {cur["accuracy"]:.3f}、現行 wiki の組 {wiki_now["accuracy"]:.3f}</div></div>
<div class="card"><div class="k">スコア（速度 / 容量 / 精度）</div><div class="v">{rec["score"]["speed"]:.1f} / {rec["score"]["size"]:.1f} / {rec["score"]["accuracy"]:.1f}</div><div class="small">採用の規則: 3 つとも 7 点以上</div></div>
</div>
<ul>
<li><strong>精度を決めるのは語彙検索のエンジンで、速度と容量を決めるのはベクトルの索引である。</strong>同じ R-130 の dense でも、LanceDB の全文検索と Qdrant の BM25 は語彙だけの再現率@30 が {cur['component_recall']['lexical_only_recall_at_30']:.3f} で、Tantivy（IDF を BM25 にそろえたもの）は {rec['component_recall']['lexical_only_recall_at_30']:.3f} だった。この差がそのまま組の精度の差になった。</li>
<li><strong>モデルは Ruri v3 に限られる。</strong>e5 系は PDF の質問で現行から 0.05 以上下がる（e5-small {models['E-s']['hybrid']['pdf']['recall_at_30']:.3f}、e5-large {models['E-l']['hybrid']['pdf']['recall_at_30']:.3f}、ruri-v3-130m {models['R-130']['hybrid']['pdf']['recall_at_30']:.3f}）。Ruri v3 は ONNX に書き出せ、torch と同じ出力（cosine ≥ 0.9999998）を torch の半分の時間で出す。wiki も torch を入れずに Ruri を使える。</li>
<li><strong>wiki は 127.0.0.1 の MCP サーバーとして常駐させる。</strong>今の wiki は検索のたびに <code>uv run --script</code> で起動し、1 回に約 {cli["warm_cli_median_seconds"]:.1f} 秒かかる（小さい wiki の複製で測った）。常駐すれば、クエリの埋め込み（{runtimes[("R-130", "onnx-fp32")]["warm_query_p95_ms_median"]:.0f} ms）と DB を合わせて数十 ms で済む。モデルと索引は 1 つのサーバーが持ち、rag はそのサーバーに検索と索引の更新を頼む。</li>
<li>Qdrant は全量で最も速い（{ms(qd["speed_ms"])}）が、容量が {mib(qd["size_bytes"])} と大きく、BM25 の精度も低い。サーバーのバイナリの配布と起動の管理も要る。sqlite-vec は総当たりなので全量で {ms(full_ok["R-130 × sqlite-vec f32 + Tantivy"]["speed_ms"])} かかり、rag の規模に合わない。</li>
</ul>
</section>

<section id="req">
<h2>2. 目的と要件</h2>
<p>info-hive-wiki は fastembed + <code>multilingual-e5-small</code> + sqlite-vec、info-hive-rag は sentence-transformers（torch）+ <code>ruri-v3-130m</code> + LanceDB を使っている。利用者の PC に埋め込みモデルとベクター DB が 2 組ずつ並ぶ。依頼は、どちらかに統一するか、別の方式に移すかを決めることである。</p>
<table class="data"><thead><tr><th>スコア</th><th>指標</th><th>閾値（3 点）</th></tr></thead><tbody>
<tr><td>検索スピード</td><td>製品の CPU 実行系でのクエリ埋め込みの p95 + DB の p95（dense 200 件 + 語彙 200 件 + RRF）。CPU 4 スレッド、72 問</td><td>1 秒</td></tr>
<tr><td>DB の容量</td><td>ベクトル索引 + 全文索引 + id と世代のディスク容量</td><td>30 GB × 件数 / 761,915</td></tr>
<tr><td>精度</td><td>融合した上位 30 件のページ再現率（人手で承認した 60 問）</td><td>現行（R-130 × LanceDB）− 0.05</td></tr>
</tbody></table>
<p>点数は、最良の値を 10 点、閾値を 3 点として間を補間し、下限を 1 点とした（速度と容量は対数、精度は直線）。<strong>3 つとも 7 点以上の組を採り、なければ最小の点が最も高い組を採る。</strong>各 DB のクエリ時のつまみは、厳密解に対する dense の recall@30 が 0.95 に届く最も速い設定に合わせ、同じ取りこぼしの水準で速度を比べた。届かなかった組は「目標未達」とし、採用の判定から外した。</p>
<p>計測は 2 段階で行った。段階 1 では全組を 100,682 チャンクの部分集合で測り、段階 2 では上位の組と現行の組を全量 761,915 チャンクで測った。wiki の MCP 化は必須の要件として、設計を第 13 節に書く（実装は次の作業）。導入の重さは副次の情報として添える。</p>
<div class="note">再現率@30 は、融合した順位の上位 30 チャンクで打ち切ってからページの重複を除いて測る（既存の <code>evaluate_mcp.py</code> の <code>limit=30</code> と同じ）。PR のレビューで、最初の集計が打ち切らずに最大 400 チャンクを数えていたことが分かり、保存した動作点の順位から計算し直した。全組の値が 1〜2 問ぶん下がったが、判定は変わらない。60 問の正解ラベルは 4 文書から作ったもので、網羅的ではない。1 問の違いは再現率 0.017 にあたり、精度の 1〜2 点の差は 1 問の差と同じ程度でしかない。</div>
</section>

<section id="now">
<h2>3. 現状</h2>
<table class="data"><thead><tr><th></th><th>info-hive-wiki</th><th>info-hive-rag</th></tr></thead><tbody>
<tr><td>埋め込みモデル</td><td><code>intfloat/multilingual-e5-small</code>（384 次元、fp16 ONNX）</td><td><code>cl-nagoya/ruri-v3-130m</code>（512 次元）</td></tr>
<tr><td>実行系</td><td>fastembed 0.8.0（ONNX Runtime）</td><td>sentence-transformers + torch 2.8 CPU</td></tr>
<tr><td>ベクトル索引</td><td>sqlite-vec 0.1.9 の vec0（総当たり）</td><td>LanceDB（IVF_SQ、世代の BITMAP 索引）</td></tr>
<tr><td>語彙検索</td><td>純 Python の BM25</td><td>LanceDB の全文検索（Sudachi の語を空白で区切る）</td></tr>
<tr><td>起動の形</td><td>検索のたびに <code>uv run --script</code>。MCP なし</td><td>stdio の MCP サーバー（子ワーカーで処理）</td></tr>
<tr><td>索引の置き場所</td><td><code>&lt;wiki&gt;/.wiki-cache/embeddings.sqlite</code></td><td><code>%LOCALAPPDATA%/info-hive/rag/data/wikis/&lt;hash&gt;/</code></td></tr>
</tbody></table>
</section>

<section id="cand">
<h2>4. 候補</h2>
<p>埋め込みモデルは e5-small（E-s）、e5-large（E-l）、ruri-v3-30m / 130m / 310m（R-30 / R-130 / R-310）、static-embedding-japanese（S-ja、速度の参考）の 6 種である。ベクター DB は次の 13 方式を、Windows ネイティブ・Python 3.12 で 10,000 件の投入と検索が通ることを確かめてから測った。</p>
<ul class="tight">
<li>sqlite-vec（f32、int8、bit + float32 の再スコア）</li>
<li>LanceDB IVF_SQ（現行 rag）</li>
<li>Qdrant 1.20 サーバー（HNSW の f32、SQ、BQ。BM25 は sparse ベクトル + IDF modifier）、Qdrant のローカルモード</li>
<li>usearch（HNSW の f16、i8）</li>
<li>FAISS（IVF_SQ8、HNSW）</li>
<li>Chroma（HNSW）</li>
</ul>
<p>全文検索を持たない DB（sqlite-vec、usearch、FAISS、Chroma、Qdrant のローカルモード）は、SQLite FTS5 か Tantivy を語彙側に組み合わせた。どちらも同じ Sudachi の語を使うので、分かち書きの差は入らない。</p>
<p>除外した候補:</p><ul class="tight">{excluded}</ul>
</section>

<section id="model">
<h2>5. モデルの精度（8,275 チャンク、119 問）</h2>
<p>dense は厳密解、語彙は全モデル共通の Sudachi + FTS5 BM25、RRF（k = 60、候補 200 件）で測った。精度の差がモデルだけから出るようにするためである。</p>
<div class="wrap"><table class="data"><thead><tr><th>モデル</th><th class="num">次元</th><th class="num">PDF 60 問（ハイブリッド）</th><th class="num">wiki 47 問（ハイブリッド）</th><th class="num">PDF（dense のみ）</th><th>注</th></tr></thead>
<tbody>{"".join(model_rows)}</tbody></table></div>
<p>語彙だけでは PDF の再現率は {lexical_only:.3f} である。現行の R-130 から 0.05 以内に入るのは Ruri の 3 つだけだった。e5 系は Ruri より短い 512 トークンで切られ、PDF のチャンクの 12.8% が途中で切れる。wiki の 47 問はどのモデルでもほぼ満点で、差が出ない。</p>
</section>

<section id="runtime">
<h2>6. 実行系（CPU 4 スレッド）</h2>
<p>Ruri v3（ModernBERT）は ONNX に書き出せた。<code>onnx-community</code> の fp32 の重みに元のリポジトリのトークナイザーを足すと、torch と同じ出力（cosine ≥ 0.9999998、上位 30 件の一致 1.0）になる。fp16 の ONNX は CPU の ONNX Runtime で読み込めず、int8 は出力が崩れる（R-130 で cosine 0.92、上位 30 件の一致 0.71）。</p>
<div class="wrap"><table class="data"><thead><tr><th>実行系</th><th class="num">起動から最初のクエリまで</th><th class="num">クエリ p95（他の処理なし）</th><th class="num">クエリ p95（GPU の処理と並行）</th><th class="num">GPU のベクトルと上位 30 件の一致</th><th class="num">メモリ</th></tr></thead>
<tbody>{"".join(runtime_rows)}</tbody></table></div>
<p class="small">スコアの計算には並行時の値を使ったので、速度は上限の値として読む。R-130 の組はすべて同じだけずれるので、順位は変わらない。</p>
</section>

<section id="stage1">
<h2>7. 段階 1: 全組 × 100,682 チャンク</h2>
<p>容量の閾値は件数に比例させて約 3.96 GB とした。「合成」の行は、dense の実測の順位と Tantivy の実測の順位を 1 問ごとに足して融合し直した値で、容量は FTS5 の分を Tantivy の分に置き換えた換算である。</p>
<details><summary>全 {len([r for r in subset if r["status"] == "ok"])} 行の表を開く</summary>
<div class="wrap">{rows_table(subset, "段階 1 の全組（最小の点の高い順）")}</div>
</details>
<p>段階 1 で 3 つとも 7 点以上になったのは {"、".join(e(x) for x in s["subset_decision"]["all_high_combinations"])} である。R-30 はどの DB でも精度が閾値を下回り、R-310 は精度が R-130 と同程度（1〜2 問の差）で、クエリの埋め込みが 2〜4 倍遅い。</p>
</section>

<section id="lexical">
<h2>8. 語彙検索: FTS5 と Tantivy</h2>
<table class="data"><thead><tr><th>エンジン</th><th class="num">部分集合 p95</th><th class="num">全量 p95</th><th class="num">全量 最悪</th><th class="num">全量 容量</th></tr></thead><tbody>
<tr><td>SQLite FTS5</td><td class="num">{ms(lex_sub["SQLite FTS5"]["p95_ms"])}</td><td class="num">{ms(lex_full["SQLite FTS5"]["p95_ms"])}</td><td class="num">{ms(lex_full["SQLite FTS5"]["max_ms"])}</td><td class="num">{mib(lex_full["SQLite FTS5"]["size_bytes"])}</td></tr>
<tr><td>Tantivy</td><td class="num">{ms(lex_sub["Tantivy"]["p95_ms"])}</td><td class="num">{ms(lex_full["Tantivy"]["p95_ms"])}</td><td class="num">{ms(lex_full["Tantivy"]["max_ms"])}</td><td class="num">{mib(lex_full["Tantivy"]["size_bytes"])}</td></tr>
</tbody></table>
<p>FTS5 は上位 k 件で打ち切る仕組みを持たず、「の」「は」を含む OR の検索で一致したすべての行の BM25 を計算する。全量では p95 が 1 秒の閾値を大きく超えるので、FTS5 を語彙側に使う組は全量で採れない。Tantivy は block-max WAND で打ち切り、全量でも数十 ms で返す。</p>
<div class="key"><strong>IDF のそろえ方。</strong>Tantivy の IDF は <code>log(1 + (N − n + 0.5) / (n + 0.5))</code> で常に正なので、頻出語も点を稼ぐ。BM25 と FTS5 の IDF は <code>log((N − n + 0.5) / (n + 0.5))</code> で、半数以上の行にある語はほぼ 0 になる。語ごとに 2 つの IDF の比を重みとして掛けると、全量の語彙だけの再現率@30 が 0.306（README に記録）から {rec['component_recall']['lexical_only_recall_at_30']:.3f} に上がり、FTS5 の {wiki_now['component_recall']['lexical_only_recall_at_30']:.3f} とほぼ同じになった。自由に選べる値はない。頻出語を文書頻度で切る案も試したが、評価の質問で値を選ぶことになるので採らなかった。そろえる前の値でも Tantivy の組は 3 つとも 7 点以上で、判定は変わらない。</div>
</section>

<section id="stage2">
<h2>9. 段階 2: 全量 761,915 チャンクと決定</h2>
<p>段階 1 の上位から DB の系統が重ならないように選び、現行の 2 組を加えて全量で測った。</p>
<div class="wrap">{rows_table(full, "段階 2（全量）の組")}</div>
<p class="small">LanceDB、Qdrant、sqlite-vec の行は世代の絞り込み（<code>generation IN ...</code>）の費用を含む。usearch と FAISS の行は含まない（LanceDB では絞り込みなしで DB の p95 が {cur["unfiltered_db_p95_ms"]:.0f} ms、ありで {cur["db_p95_ms"]:.0f} ms）。Qdrant の容量は、BM25 の sparse ベクトル、payload の索引、WAL を含む。</p>
<h3>速度と容量の散布図（全量）</h3>
{scatter(full)}
<p class="small">左下ほど良い。色は精度の点（緑 7 以上、黄 3〜7、赤 3 以下）、丸は実測、菱形は合成。</p>
<h3>語彙側だけ、dense 側だけの再現率@30（全量）</h3>
<table class="data"><thead><tr><th>組</th><th class="num">語彙だけ</th><th class="num">dense だけ</th><th class="num">融合</th></tr></thead><tbody>
{component_rows}
</tbody></table>
<p>現行の rag では、融合した結果（{cur["accuracy"]:.3f}）が dense だけ（{cur["component_recall"]["dense_only_recall_at_30"]:.3f}）を下回る。語彙側が弱いと、RRF で混ぜるほど順位が悪くなる。Tantivy の組でも、融合（{rec['accuracy']:.3f}）は dense だけ（{rec['component_recall']['dense_only_recall_at_30']:.3f}）をわずかに下回った（1 問未満の差）。この評価の質問では、語彙側を混ぜる利点は確かめられていない。融合の重みや候補数の見直しは、次の検証の課題とする。</p>
<h3>決定の流れ</h3>
<svg viewBox="0 0 760 300" class="diagram" role="img" aria-label="採用の決定の流れ">
<defs><marker id="ah" viewBox="0 0 10 10" refX="9" refY="5" markerWidth="7" markerHeight="7" orient="auto-start-reverse"><path d="M0,0 L10,5 L0,10 z" fill="#59656b"/></marker></defs>
<rect x="10" y="20" width="200" height="56" class="box acc"/><text x="110" y="44" text-anchor="middle" class="t">モデル 6 種</text><text x="110" y="62" text-anchor="middle" class="ts">精度 ≥ 現行 − 0.05</text>
<rect x="10" y="120" width="200" height="56" class="box good"/><text x="110" y="144" text-anchor="middle" class="t">Ruri v3 30m / 130m / 310m</text><text x="110" y="162" text-anchor="middle" class="ts">e5 系はここで外れる</text>
<rect x="10" y="220" width="200" height="56" class="box good"/><text x="110" y="244" text-anchor="middle" class="t">R-130</text><text x="110" y="262" text-anchor="middle" class="ts">R-30 は DB 込みで閾値割れ、R-310 は遅い</text>
<rect x="280" y="20" width="200" height="56" class="box acc"/><text x="380" y="44" text-anchor="middle" class="t">DB 13 方式 × 語彙 2 種</text><text x="380" y="62" text-anchor="middle" class="ts">dense recall ≥ 0.95 の動作点</text>
<rect x="280" y="120" width="200" height="56" class="box bad"/><text x="380" y="144" text-anchor="middle" class="t">FTS5 の組、総当たりの組</text><text x="380" y="162" text-anchor="middle" class="ts">全量で 1 秒を超える</text>
<rect x="280" y="220" width="200" height="56" class="box bad"/><text x="380" y="244" text-anchor="middle" class="t">LanceDB、Qdrant</text><text x="380" y="262" text-anchor="middle" class="ts">容量と BM25 の精度で 7 点未満</text>
<rect x="550" y="120" width="200" height="56" class="box good"/><text x="650" y="144" text-anchor="middle" class="t">usearch / FAISS + Tantivy</text><text x="650" y="162" text-anchor="middle" class="ts">全量で 3 つとも 7 点以上</text>
<rect x="550" y="220" width="200" height="56" class="box good"/><text x="650" y="244" text-anchor="middle" class="t">usearch HNSW f16 + Tantivy</text><text x="650" y="262" text-anchor="middle" class="ts">最小の点 {rec["score"]["minimum"]:.1f}、副次の理由でも優位</text>
<path d="M110 76 V118" class="arrow"/><path d="M110 176 V218" class="arrow"/><path d="M380 76 V118" class="arrow"/><path d="M380 176 V218" class="arrow"/>
<path d="M480 48 H515 V148 H548" class="arrow"/><path d="M650 176 V218" class="arrow"/>
</svg>
<h3>usearch と FAISS の選び方</h3>
<p>3 つのスコアでは同等なので、副次の事実で選ぶ。<strong>usearch を推奨し、FAISS IVF_SQ8 を代替とする。</strong></p>
<table class="data"><thead><tr><th>観点</th><th>usearch HNSW f16</th><th>FAISS IVF_SQ8</th></tr></thead><tbody>
<tr><td>全量の構築（埋め込みを除く）</td><td class="num">{rec["build_seconds"]:,.0f} 秒</td><td class="num">{alt["build_seconds"]:,.0f} 秒</td></tr>
<tr><td>全量の容量</td><td class="num">{mib(rec["size_bytes"])}</td><td class="num">{mib(alt["size_bytes"])}</td></tr>
<tr><td>持っているベクトル</td><td>f16（取り出したベクトルと元の cosine 0.99997）。量子化や索引の設定は索引から作り直せる</td><td>8 ビットの量子化値だけ。設定を変えるには元のベクトルか再埋め込みが要る</td></tr>
<tr><td>件数が増えたとき</td><td>HNSW なので追加だけで済む</td><td>IVF の中心（リスト数 √N）を学習し直す必要がある。wiki の数千件から rag の数十万件まで同じ設定では合わない</td></tr>
<tr><td>削除</td><td><code>remove</code></td><td><code>remove_ids</code>（IVF では線形の走査）</td></tr>
<tr><td>Windows での同時アクセス（M5）</td><td>読み手がメモリ写像（<code>view=True</code>）で開いている間、別プロセスの <code>save</code> が Permission denied</td><td>索引をメモリに読み込むので、書き手は保存できる。読み手は開き直すまで古い索引を見る</td></tr>
<tr><td>導入の容量（M4）</td><td class="num">{install["fastembed + usearch + Tantivy"]["cache_bytes"] / MIB:,.0f} MiB</td><td class="num">{install["fastembed + FAISS + Tantivy"]["cache_bytes"] / MIB:,.0f} MiB</td></tr>
</tbody></table>
<p>usearch の同時アクセスの問題は、索引を 1 つのプロセス（第 13 節の wiki MCP サーバー）だけが持ち、そのプロセスが読み書きすることで避けられる。保存は一時ファイルに書いてから置き換え、置き換えの前に写像を閉じる。FAISS の構築の速さは魅力だが、wiki の規模から rag の規模まで同じ実装で扱うには、学習の要らない HNSW のほうが簡単である。</p>
</section>

<section id="wiki">
<h2>10. wiki 規模（8,275 チャンク、MCP で常駐する前提）</h2>
<p>評価セットの 8,275 チャンクを大きめの wiki とみなし、R-130 のベクトルで DB を作った。起動は別プロセスで 3 回測った中央値である。語彙側はこの規模では FTS5 でも数 ms〜数十 ms で返る。</p>
<div class="wrap"><table class="data"><thead><tr><th>DB</th><th class="num">容量</th><th class="num">開いて最初の検索まで</th><th class="num">ウォーム検索 p95（dense + 語彙）</th><th class="num">500 行の追記</th><th>追記した行が読み手から</th></tr></thead>
<tbody>{"".join(db_rows)}</tbody></table></div>
<p>現行の wiki の CLI（<code>uv run --script wiki_search.py</code>）は、W0_Wiki の複製（Markdown {cli["markdown_files"]} ファイル、小さい標本）で初回 {cli["runs"][0]["seconds"]:.0f} 秒（索引の作成を含む）、2 回目以降 {cli["warm_cli_median_seconds"]:.1f} 秒かかった。大半はプロセスの起動とモデルの読み込みである。MCP サーバーとして常駐すると、この費用は起動時の 1 回（R-130 ONNX で約 {runtimes[("R-130", "onnx-fp32")]["cold_total_seconds_median"]:.1f} 秒）になる。</p>
</section>

<section id="install">
<h2>11. 導入の重さ（副次）</h2>
<p>空の uv キャッシュから <code>uv run --script</code> で準備した時間と、キャッシュの容量である。PDF、OCR、MCP の依存（共通）は全構成に含む。時間はネットワークに左右される。</p>
<div class="wrap"><table class="data"><thead><tr><th>構成</th><th class="num">準備の時間</th><th class="num">容量</th></tr></thead><tbody>{"".join(install_rows)}</tbody></table></div>
<p>torch をやめて ONNX Runtime（fastembed の依存に含まれる）に移すと、容量は約 7.7 GB から 0.8 GB に減る。usearch と Tantivy が足すのは合わせて数十 MiB である。</p>
</section>

<section id="paths">
<h2>12. 統一の 3 つの形と移行の費用</h2>
<table class="data"><thead><tr><th>形</th><th>中身</th><th>判定</th><th>移行の費用</th></tr></thead><tbody>
<tr><td>(a) rag を wiki に合わせる</td><td>e5-small + sqlite-vec</td><td>採らない。精度が閾値を下回り（PDF 0.700）、総当たりが全量で {ms(wiki_now["speed_ms"])}</td><td>—</td></tr>
<tr><td>(b) wiki を rag に合わせる</td><td>R-130 + LanceDB（torch）</td><td>採らない。精度と容量が 7 点未満で、wiki に torch（約 7 GB）が入る</td><td>—</td></tr>
<tr><td>(c) 両方を第三の組に移す</td><td>R-130（ONNX）+ usearch + Tantivy</td><td><strong>採る</strong></td><td>
<ul class="tight">
<li>rag: モデルは同じで再埋め込みは不要（ONNX と torch の上位 30 件の一致 1.0）。既存のベクトルから usearch と Tantivy の索引を作り直す（全量で約 {rec["build_seconds"] / 60:.0f} 分）。<code>fingerprint</code> に実行系と索引の種類を入れる</li>
<li>wiki: モデルが変わるので再埋め込みが要る（数千セクションなら CPU で数分〜十数分）。<code>semantic_meta</code> を作り直す。語彙検索を純 Python の BM25 から Sudachi + Tantivy に移すと、<code>sudachipy</code> と <code>sudachidict-core</code> が加わる</li>
<li>依存: torch と lancedb を外し、onnxruntime（fastembed）、usearch、tantivy にする</li>
<li>モデルのキャッシュを 1 か所にまとめる（wiki の <code>~/.cache/info-hive/fastembed</code> と rag の <code>data_dir/models</code>）</li>
</ul></td></tr>
</tbody></table>
</section>

<section id="mcp">
<h2>13. wiki の MCP 化の設計（実装は次の作業）</h2>
<h3>トランスポート</h3>
<p>stdio の MCP サーバーは、ホストのセッションごとに起動される。エージェントが 3 つあればモデルが 3 回読み込まれ（R-130 ONNX で約 {runtimes[("R-130", "onnx-fp32")]["trials"][0]["rss_bytes"] / MIB:,.0f} MiB ずつ）、索引の書き手も 3 つになる。そこで、<strong>127.0.0.1 の streamable HTTP の MCP サーバーを必要なときに起動し、使われない状態が続いたら止める</strong>形を第一候補にする。ADR-0002（<code>/wiki:browse</code>）と同じ形で、実行方式の比較の案 9「MCP とデーモン」にあたる。stdio しか話せないホストのために、HTTP サーバーへ中継する小さな stdio の入口も置く。</p>
<svg viewBox="0 0 760 300" class="diagram" role="img" aria-label="wiki MCP サーバーの構成">
<rect x="10" y="20" width="170" height="44" class="box"/><text x="95" y="47" text-anchor="middle" class="t">Claude Code（wiki）</text>
<rect x="10" y="80" width="170" height="44" class="box"/><text x="95" y="107" text-anchor="middle" class="t">Claude Code（rag）</text>
<rect x="10" y="140" width="170" height="44" class="box"/><text x="95" y="167" text-anchor="middle" class="t">Codex など</text>
<rect x="10" y="200" width="170" height="44" class="box"/><text x="95" y="227" text-anchor="middle" class="t">CLI（診断と再実行）</text>
<rect x="250" y="60" width="250" height="150" class="box acc"/>
<text x="375" y="84" text-anchor="middle" class="t">wiki MCP サーバー（127.0.0.1）</text>
<text x="375" y="106" text-anchor="middle" class="ts">起動ごとのトークン、Host ヘッダーの確認</text>
<text x="375" y="132" text-anchor="middle" class="t">埋め込み: R-130 ONNX（1 つ）</text>
<text x="375" y="156" text-anchor="middle" class="t">索引の唯一の書き手</text>
<text x="375" y="180" text-anchor="middle" class="ts">使われなければ止まる。次の呼び出しで起動</text>
<rect x="570" y="40" width="180" height="56" class="box good"/><text x="660" y="64" text-anchor="middle" class="t">usearch HNSW f16</text><text x="660" y="82" text-anchor="middle" class="ts">wiki ごとに 1 つ</text>
<rect x="570" y="112" width="180" height="56" class="box good"/><text x="660" y="136" text-anchor="middle" class="t">Tantivy（BM25）</text><text x="660" y="154" text-anchor="middle" class="ts">Sudachi の語</text>
<rect x="570" y="184" width="180" height="56" class="box good"/><text x="660" y="208" text-anchor="middle" class="t">SQLite（台帳、世代）</text><text x="660" y="226" text-anchor="middle" class="ts">WAL</text>
<path d="M180 42 H215 V110 H248" class="arrow"/><path d="M180 102 H248" class="arrow"/><path d="M180 162 H215 V130 H248" class="arrow"/><path d="M180 222 H230 V190 H248" class="arrow"/>
<path d="M500 110 H535 V68 H568" class="arrow"/><path d="M500 140 H568" class="arrow"/><path d="M500 170 H535 V212 H568" class="arrow"/>
<text x="375" y="270" text-anchor="middle" class="ts">rag の子ワーカー（PDF の抽出と OCR）は、チャンクをサーバーに渡して索引に加えてもらう</text>
</svg>
<h3>ツール</h3>
<table class="data"><thead><tr><th>ツール</th><th>中身</th><th>元にする CLI</th></tr></thead><tbody>
<tr><td><code>query</code></td><td>ハイブリッド検索。<code>--json</code> と同じ出力</td><td><code>wiki_search.py</code></td></tr>
<tr><td><code>get_page</code></td><td>ページの本文と frontmatter（日本語の別名キーをそろえたもの）</td><td><code>wiki_text.py</code> の <code>canonical_meta()</code></td></tr>
<tr><td><code>list_index</code></td><td><code>index.md</code> と <code>indexes/</code> の一覧</td><td>—</td></tr>
<tr><td><code>lint</code></td><td>リンク切れ、frontmatter の検査</td><td><code>wiki_lint.py</code></td></tr>
<tr><td><code>stats</code></td><td>ページ数、索引の状態、モデルと索引の版</td><td><code>wiki_stats.py</code></td></tr>
<tr><td><code>graph</code></td><td>グラフの問い合わせ</td><td><code>wiki_graph_query.py</code></td></tr>
<tr><td><code>ingest_source</code></td><td>ソースの登録だけ。本文の執筆はエージェントが行う</td><td>—</td></tr>
<tr><td><code>index_chunks</code></td><td>rag からチャンクとベクトル（または本文）を受け取り、索引に加える。世代を指定して古い世代を消す</td><td>rag の <code>Engine</code></td></tr>
</tbody></table>
<p><code>/wiki:query</code> などのコマンドは、MCP のツールを呼ぶように移す。MCP が使えないときは今の CLI に戻る。</p>
<h3>モデルと DB の共有の形</h3>
<table class="data"><thead><tr><th>形</th><th>モデルの読み込み</th><th>判断</th></tr></thead><tbody>
<tr><td>1. 共通コアを両プラグインに複製する</td><td>プロセスの数だけ</td><td>索引の書き手が 2 つになり、usearch の Windows のロックと衝突する</td></tr>
<tr class="best"><td>2. wiki の MCP サーバーがモデルと DB を持ち、rag はそこに頼む（推奨）</td><td>1 回</td><td>依存の向き（rag → wiki）と合う。rag は wiki のサーバーに MCP で頼むので、別プラグインの内部パスを組み立てない（<code>ingest.md</code> の制約）。wiki が無効なら rag は検索できないと報告する</td></tr>
<tr><td>3. 共通パッケージ <code>info-hive-core</code> を作る</td><td>プロセスの数だけ</td><td><code>uv run --script</code> と配布の形の確認が要り、1 と同じく書き手が増える</td></tr>
<tr><td>4. wiki と rag を 1 つのサーバーにまとめる</td><td>1 回</td><td>プラグインの境界と <code>CLAUDE_PLUGIN_ROOT</code> の扱いがあいまいになる</td></tr>
</tbody></table>
<h3>置き場所、Claude Code 以外からの起動、同時アクセス</h3>
<ul>
<li>索引は wiki ごとに <code>%LOCALAPPDATA%/info-hive/index/&lt;wiki のハッシュ&gt;/</code>（macOS と Linux は XDG の data ディレクトリ）に置く。ユーザースコープとプロジェクトスコープの wiki はハッシュで分ける。wiki の中の <code>.wiki-cache/</code> には索引を置かない。</li>
<li>サーバーはポートとトークンを <code>%LOCALAPPDATA%/info-hive/server.json</code> に書く。Codex などの <code>CLAUDE_PLUGIN_ROOT</code> を持たないホストは、明示的なパスと wiki ルートの引数で stdio の入口を起動し、入口が HTTP サーバーを見つけるか起動する。</li>
<li>索引の書き手はサーバーだけにする。M5 では、SQLite と Qdrant 以外の DB はどれも、別プロセスで書いた行が開き直すまで見えなかった。usearch は書き込み自体が失敗した。書き手を 1 つにすれば、この問題は起きない。</li>
<li>世代の絞り込みは、取り込みのときに古い世代の行を消して（<code>remove</code>）避ける。検索のたびに <code>generation IN ...</code> を付ける方式は usearch と FAISS では測っていない。</li>
</ul>
</section>

<section id="lose">
<h2>14. 失うものと代替</h2>
<table class="data"><thead><tr><th>LanceDB で得ていたもの</th><th>代替</th></tr></thead><tbody>
<tr><td>全文検索（native FTS）</td><td>Tantivy。語彙側の精度と速度はどちらも上がる</td></tr>
<tr><td>世代の BITMAP 索引と絞り込み</td><td>取り込みのときに古い世代を消す。台帳（SQLite）が世代を持つ</td></tr>
<tr><td>行とベクトルを 1 か所に持つ表</td><td>SQLite の台帳 + usearch（ベクトル）+ Tantivy（語）。3 つの更新をそろえる処理を自前で持つ。中断したときは台帳から作り直せるようにする</td></tr>
<tr><td><code>optimize</code> による掃除</td><td>usearch の作り直し（全量で約 {rec["build_seconds"] / 60:.0f} 分）と Tantivy のマージ</td></tr>
<tr><td>別プロセスからの読み（<code>read_consistency_interval</code>）</td><td>書き手を MCP サーバーだけにする</td></tr>
</tbody></table>
</section>

<section id="adr">
<h2>15. ADR 案（確定は別の作業）</h2>
<h3>ADR 案 A: 埋め込みモデルとベクター DB を wiki と rag で統一する</h3>
<table class="data"><tbody>
<tr><th>決定</th><td>埋め込みは <code>cl-nagoya/ruri-v3-130m</code> を ONNX fp32（ONNX Runtime）で動かす。ベクトル索引は usearch HNSW f16、語彙検索は Sudachi + Tantivy（IDF を BM25 にそろえる）、融合は RRF（k = 60、候補 200 件）とする。wiki と rag は同じ実装を使う。</td></tr>
<tr><th>理由</th><td>全量で 3 つのスコアがすべて 7 点以上（{rec["score"]["speed"]:.1f} / {rec["score"]["size"]:.1f} / {rec["score"]["accuracy"]:.1f}）。現行の rag より検索が {cur["speed_ms"] / rec["speed_ms"]:.1f} 倍速く、容量は {cur["size_bytes"] / rec["size_bytes"]:.1f} 分の 1 で、精度は同等以上。torch が要らなくなる。</td></tr>
<tr><th>代替</th><td>FAISS IVF_SQ8 + Tantivy（同等の点）。Qdrant（速度は最良、容量とサーバー管理が重い）。</td></tr>
<tr><th>見直す条件</th><td>評価の質問を増やして精度の差が逆転する。usearch の Windows での保存が単一の書き手でも安定しない。wiki の規模で R-130 の再埋め込みの時間が受け入れられない。</td></tr>
</tbody></table>
<h3>ADR 案 B: wiki は MCP サーバーを持ち、モデルと索引を 1 つにする</h3>
<table class="data"><tbody>
<tr><th>決定</th><td>wiki は 127.0.0.1 の streamable HTTP の MCP サーバーを必要なときに起動する。サーバーはモデルと索引の唯一の持ち主で、rag は MCP でサーバーに検索と索引の更新を頼む。stdio の入口を併せて置く。</td></tr>
<tr><th>理由</th><td>他のエージェントから wiki を問い合わせ、操作できるようにする（必須の要件）。今の CLI の検索 1 回約 {cli["warm_cli_median_seconds"]:.1f} 秒が数十 ms になる。モデルの二重読み込みと索引の書き手の競合がなくなる。ADR-0007 で未決だった「モデルの保持と共有」を決める。</td></tr>
<tr><th>影響</th><td>rag の MCP サーバーは索引を持たず、PDF の抽出、OCR、チャンク化、ジョブの管理に絞る。ADR-0001 の 3 条件（127.0.0.1 への固定、トークン、書き込み API の制限）を守る。</td></tr>
</tbody></table>
</section>

<section id="repro">
<h2>16. 再現と出典</h2>
<p>計測のスクリプトは <code>poc/rag/unification/</code>、計測の記録と JSON は <code>docs/research/embedding-backend-unification-2026-11-05/</code> にある。手順、計画との違い、計測の条件は同じフォルダーの <code>README.md</code> に書いた。この HTML は <code>build_report.py</code> が JSON から作る。</p>
<ul class="tight">
<li>計画: 埋め込みモデル・ベクター DB の統一の比較（2026-11-05、承認済み）</li>
<li>JSON: <code>candidates.json</code>、<code>model-accuracy.json</code>、<code>runtime-parity.json</code>、<code>onnx-feasibility.json</code>、<code>lexical-bench-subset.json</code>、<code>lexical-bench-full.json</code>、<code>db-bench-subset.json</code>、<code>db-bench-full.json</code>、<code>scores.json</code>、<code>wiki-scale.json</code>、<code>install-results.json</code></li>
<li>既存の調査: <code>docs/research/japanese-pdf-local-rag-options.md</code>、<code>docs/research/rag-execution-architecture/brainstorm-diverge-converge.md</code>、<code>docs/research/rag-validation-remaining-2026-11-04/</code></li>
<li>ADR: <code>docs/adr/0001</code>、<code>0002</code>、<code>0007</code></li>
<li>コード: <code>info-hive-wiki/skills/info-hive/scripts/wiki_search.py</code>、<code>info-hive-rag/scripts/rag_index.py</code>、<code>rag_server.py</code>、<code>info-hive-wiki/commands/ingest.md</code></li>
<li>データ: <code>.rag-poc-data/full-20261104/</code>（761,915 チャンク、60 問）、<code>.rag-poc-data/natural-20261104/</code>（8,275 チャンク、119 問）</li>
</ul>
</section>
<footer>最終更新: {today}。数値は <code>scores.json</code> ほかの JSON から生成。</footer>
</main>
</div>
</body>
</html>
"""
    REPORT.write_text(body, encoding="utf-8")
    print(REPORT)


if __name__ == "__main__":
    main()
