"""統一の決定のための追加測定（E1〜E11）の JSON から、HTML のレポートを作る。数値はすべて JSON から読む。

出力: docs/research/embedding-backend-decision-2026-11-06.html
CSS は統一の測定のレポート（../unification/build_report.py）の <style> をそのまま取り出して使う。
"""
from __future__ import annotations

import re
from pathlib import Path

from decision_common import OUT_D, load
from build_report import e, mib, ms

REPORT = OUT_D.parent / "embedding-backend-decision-2026-11-06.html"
UNIFICATION_REPORT = "embedding-backend-unification-2026-11-05.html"
GIB = 2 ** 30
EXTRA_STYLE = """
.verdict .card.bad { border-color: var(--bad); background: var(--bad-bg); }
.verdict .card.ok { border-color: var(--good); background: var(--good-bg); }
td.ok { color: var(--good); font-weight: 700; }
td.ng { color: var(--bad); font-weight: 700; }
.opt { border: 1px solid var(--line); border-radius: 6px; padding: 10px 14px; margin: 10px 0; }
.opt h3 { margin-top: 0; }
"""


def style():
    source = (Path(__file__).resolve().parent.parent / "unification/build_report.py").read_text(encoding="utf-8")
    css = re.search(r"<style>\n(.*?)</style>", source, re.S).group(1)
    return css.replace("{{", "{").replace("}}", "}") + EXTRA_STYLE


def ok_cell(value, yes="合格", no="不合格"):
    return f'<td class="{"ok" if value else "ng"}">{yes if value else no}</td>'


def gib(value):
    return f"{value / GIB:.2f} GiB"


def minutes(seconds):
    return f"{seconds / 60:.0f} 分" if seconds >= 120 else f"{seconds:.0f} 秒"


def table(head, rows, caption=None, num=()):
    out = ['<div class="wrap"><table class="data">' + (f"<caption>{e(caption)}</caption>" if caption else "") + "<thead><tr>"]
    out += [f'<th class="{"num" if i in num else ""}">{e(h)}</th>' for i, h in enumerate(head)]
    out.append("</tr></thead><tbody>")
    for row in rows:
        cells = []
        for i, cell in enumerate(row):
            cells.append(cell if isinstance(cell, str) and cell.startswith("<td") else f'<td class="{"num" if i in num else ""}">{cell}</td>')
        out.append("<tr>" + "".join(cells) + "</tr>")
    out.append("</tbody></table></div>")
    return "\n".join(out)


def main():
    onnx = load("onnx-distribution.json")
    gate = load("wiki-gate.json")
    sweep = load("fusion-sweep.json")
    deep = load("fusion-deep.json")
    reembed = load("wiki-reembed.json")
    check = load("wiki-reembed-check.json")
    knobs = load("db-knobs-full.json")
    gen = load("generation-filter.json")
    write = load("write-safety.json")
    retry = load("tantivy-commit-retry.json")
    memory = load("server-memory.json")
    relay = load("mcp-relay.json")
    final = load("decision-scores.json")
    env = final["env"]
    gates = final["gates"]

    # ---- E7 の数値（区間ごとの推定を、無作為 1,000 行の実測の比で補正する） ----
    by_model = {(r["model"], r["runtime"]): r for r in reembed["results"] if r["status"] == "ok"}
    ratio = {(r["model"], r["runtime"]): r["ratio_measured_to_estimate"] for r in check["results"] if r["status"] == "ok"}
    rows_natural = reembed["distribution"]["natural_tokens"]["count"]
    rows_wiki = reembed["distribution"]["wiki_tokens"]["count"]
    r130 = by_model[("R-130", "onnx-fp32")]
    r130_ratio = ratio[("R-130", "onnx-fp32")]
    r130_natural = r130["estimate_natural_seconds"][str(r130["best_batch"])]
    r130_wiki_scaled = r130["estimate_wiki_sections_seconds"][str(r130["best_batch"])] / rows_wiki * rows_natural

    # ---- E10 の分解 ----
    parts = final["notes"]["E10"]["overhead_parts_ms"]
    decisions = final["decisions"]
    claude_job = load("claude-job-check.json")
    variants = final["notes"]["E10"]["variants"]
    best_variant = min((v for n, v in variants.items() if not n.endswith("noauth")), key=lambda v: v["overhead_relay_ms"])
    variant_label = {"mcp-relay": "ログあり、SSE", "mcp-relay-quiet": "ログなし、SSE", "mcp-relay-quiet-json": "ログなし、JSON の応答",
                     "mcp-relay-quiet-json-asgi": "ログなし、JSON、認証を ASGI で書く", "mcp-relay-quiet-json-noauth": "ログなし、JSON、認証なし（下限）"}
    noauth = variants["mcp-relay-quiet-json-noauth"]
    asgi = variants["mcp-relay-quiet-json-asgi"]
    variant_rows = [[e(variant_label[n]), ms(v["function_p95_ms"]), ms(v["direct_http_p95_ms"]), ms(v["relay_p95_ms"]),
                     ms(v["overhead_relay_ms"])] for n, v in variants.items()]

    # ---- E8 ----
    g = gate["gates"]
    chosen = gate["chosen"]
    ja_base, ja_sudachi = g["r130"]["ja"]["metrics"], g["r130-sudachi"]["ja"]["metrics"]
    kinds = gate["sudachi_by_kind"]["ja-section"]
    worse_kinds = [k for k, v in kinds.items() if v["sudachi_recall@10"] < v["bigram_recall@10"] - 1e-9]
    tantivy_same = all(abs(x["wiki_bm25"] - x["r130-tantivy"]) < 5e-4 for v in gate["r130-tantivy_vs_wiki_bm25"].values() for x in v.values())

    # ---- E1 ----
    sets = ["natural-pdf", "natural-wiki", "full-usearch", "full-sqlite-vec f32", "full-FAISS IVF_SQ8"]
    base_row, best_row, verdict = sweep["base_row"], sweep["best_row"], sweep["verdict"]
    fusion_rows = [[e(s), f'{base_row[s]["recall_at_30"]:.3f}', f'{best_row[s]["recall_at_30"]:.3f}',
                    f'{verdict[s]["delta_recall"]:+.3f}', f'{base_row[s]["ndcg_at_10"]:.3f}', f'{best_row[s]["ndcg_at_10"]:.3f}',
                    f'{verdict[s]["wins"]} / {verdict[s]["losses"]}'] for s in sets]
    c = sweep["chosen"]

    # ---- E2 ----
    pick = ("dense_only", "rrf_k60_w1", "rrf_e1", "minmax_a0.6")
    names = {"dense_only": "dense だけ", "rrf_k60_w1": "RRF k=60、重み 1（統一の測定）", "rrf_e1": f"RRF k={c['k']}、語彙の重み {c['lexical_weight']}（E1）",
             "minmax_a0.6": "スコアの min-max 正規化、α=0.6"}
    deep_rows = [[r["candidates"], e(names[r["fusion"]]), f'{r["recall_at_30"]:.3f}', f'{r["ndcg_at_10"]:.3f}', f'{r["wins"]} / {r["losses"]}', ms(r["db_p95_ms"])]
                 for r in deep["results"] if r["fusion"] in pick]
    e1_full = next(r for r in deep["results"] if r["candidates"] == 200 and r["fusion"] == "rrf_e1")
    mm = next(r for r in deep["results"] if r["candidates"] == 200 and r["fusion"] == "minmax_a0.6")

    # ---- E7 の表 ----
    reembed_rows = []
    for (model, runtime), r in by_model.items():
        b = str(r["best_batch"])
        k = ratio.get((model, runtime))
        natural = r["estimate_natural_seconds"][b]
        wiki_scaled = r["estimate_wiki_sections_seconds"][b] / rows_wiki * rows_natural
        reembed_rows.append([f"{model} {e(runtime)}", b, minutes(natural), f"{k:.2f}" if k else "未測定",
                             minutes(natural * k) if k else "—", minutes(wiki_scaled), f'{r["page_update"]["seconds"]:.2f} 秒'])

    # ---- E3 ----
    knob_rows = []
    for key, r in knobs["results"].items():
        p = r["operating_point"]
        knob_rows.append([e(key), e(p["knob"]), ms(p["dense_p95_ms"]), ms(p["db_p95_ms"]), f'{p["dense_recall_vs_exact_at_30"]:.3f}',
                          f'{p["recall_at_30"]:.3f}', mib(r["size"]["vector_bytes"]), minutes(r["build_seconds"])])
    repro = knobs["results"]["usearch M16 ea128 (既存)"]["reproduction"]

    # ---- E4 ----
    gen_rows = []
    for f in gen["filtering"]:
        u = f["usearch_smallest_ok"] or {}
        fs = f["faiss_selector"]
        gen_rows.append([f'{f["fraction_documents"] * 100:g}%', f'{f["invalid_rows"]:,}', f'{u.get("multiplier", "—")} 倍',
                         f'{u.get("p95_increase_ms", float("nan")):+.1f} ms', f'{u.get("recall_vs_exact_valid", float("nan")):.3f}',
                         f'{fs["p95_increase_ms"]:+.1f} ms', f'{fs["recall_vs_exact_valid"]:.3f}', fs["leaked_invalid"]])
    rm, frm, td = gen["usearch_remove"], gen["faiss_remove"], gen["tantivy_delete"]

    # ---- E5 ----
    a, bw, bf, cv = write["a_replace_while_mapped"], write["b_single_writer_wiki"], write["b_single_writer_full"], write["c_versioned_manifest"]
    d, d2 = write["d_tantivy"], write["d2_tantivy_same_process"]
    retry_rows = [[f'{r["interval_seconds"]:g} 秒', "rollback して入れ直す" if r["recover"] else "何もしない", f'{r["commits"]:,}', r["errors"],
                   f'{r["error_rate"] * 100:.1f}%', f'{r["docs_added"]:,}', f'{r["docs_in_index"]:,}',
                   f'<td class="num {"ok" if r["lost"] == 0 else "ng"}">{r["lost"]:,}</td>'] for r in retry["results"]]
    lost_plain = next(r for r in retry["results"] if not r["recover"])

    # ---- E6 ----
    mem_rows = []
    for r in memory["results"]:
        if r["status"] != "ok":
            continue
        s = r["stages"]
        mem_rows.append([("wiki 規模" if r["scale"] == "wiki" else "全量"), e(r["index"]), "あり" if r["model"] else "なし",
                         gib(s["start"]["private"]), gib(s["model_loaded"]["private"]) if "model_loaded" in s else "—",
                         gib(s["after_queries"]["private"]), gib(s["after_longest_passages"]["private"]) if "after_longest_passages" in s else "—",
                         gib(r["peak_wset_bytes"])])
    view_wiki = next(r for r in memory["results"] if r["scale"] == "wiki" and r["index"] == "usearch-view" and r["model"])
    view_wiki_none = next(r for r in memory["results"] if r["scale"] == "wiki" and r["index"] == "usearch-view" and not r["model"])
    view_full = next(r for r in memory["results"] if r["scale"] == "full" and r["index"] == "usearch-view" and r["model"])

    # ---- E11 ----
    score_rows = []
    for r in sorted(final["rows"], key=lambda r: (-r["score"]["minimum"], r["speed_ms"])):
        s = r["score"]
        score_rows.append([e(r["key"]), ms(r["speed_ms"]), mib(r["size_bytes"]), f'{r["accuracy"]:.3f}',
                           f'{s["speed"]:.1f}', f'{s["size"]:.1f}', f'{s["accuracy"]:.1f}', f'<td class="num"><strong>{s["minimum"]:.1f}</strong></td>'])
    best_u = next(r for r in final["rows"] if r["key"] == final["best_usearch"])
    best_f = next(r for r in final["rows"] if r["key"] == final["best_faiss"])

    gate_names = {
        "E8_wiki_gate_r130": ("E8", "R-130 で wiki の評価ゲートを通る"), "E8_calibration_separable": ("E8", "max_distance を偽陽性 0 で較正できる"),
        "E8_sudachi": ("E8", "Sudachi に替えても ja のゲートを通る"), "E8_tantivy_bigram": ("E8", "Tantivy に wiki の bigram を渡してもゲートを通る"), "E7_reembed": ("E7", "初回の再埋め込み ≤ 20 分、1 ページの更新 ≤ 5 秒"),
        "E1_fusion_keep": ("E1", "融合が dense だけに負けない"), "E3_faiss_not_better_by_0_5": ("E3", "FAISS の最小点が usearch を 0.5 以上上回らない"),
        "E5_write_safe": ("E5", "usearch を Windows で安全に書き換えられる"), "E5_tantivy_with_retry": ("E5", "Tantivy の commit の失敗から文書を失わずに回復できる"),
        "E4_filter_ok": ("E4", "世代の絞り込みの増分 ≤ 20 ms"), "E6_memory_not_favoring_faiss": ("E6", "メモリの結果で FAISS に替える理由がない"),
        "E10_relay": ("E10", "中継の上乗せ ≤ 15 ms（10 ms から緩めた）、重複起動 0、防御が効く"),
        "E10_claude_code_keeps_detached": ("E10", "Claude Code のセッションが終わっても、サーバーの起動した孫が残る"), "E9_onnx": ("E9", "公開版の ONNX で同じベクトルが出る"),
    }
    gate_rows = [[gate_names[k][0], e(gate_names[k][1]), ok_cell(v)] for k, v in gates.items()]

    pkgs = env["packages"]
    css = style()
    toc = [("tldr", "1. 要約"), ("decide", "2. 決めてほしいこと"), ("q", "3. 9 つの問いと測定"), ("cond", "4. 測定の条件"),
           ("e9", "5. ONNX の配布（E9）"), ("e8", "6. wiki の評価ゲート（E8）"), ("e1", "7. 融合（E1、E2）"), ("e7", "8. 再埋め込みの時間（E7）"),
           ("e3", "9. DB のつまみ（E3）"), ("e4", "10. 世代の絞り込み（E4）"), ("e5", "11. 書き込みの安全性（E5）"), ("e6", "12. 常駐メモリ（E6）"),
           ("e10", "13. MCP の中継（E10）"), ("e11", "14. 最終の採点（E11）"), ("ocr", "15. OCR と fingerprint"), ("adr", "16. ADR との整合"),
           ("repro", "17. 再現と出典")]
    nav = "".join(f'<a href="#{i}">{e(t)}</a>' for i, t in toc)

    body = f"""<!doctype html>
<html lang="ja">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>埋め込みと索引の統一の決定</title>
<style>
{css}
</style>
</head>
<body>
<div class="layout">
<nav class="toc" aria-label="目次">{nav}</nav>
<main>
<header>
<h1>埋め込みと索引の統一を決めるための追加測定</h1>
<p class="lede">統一の測定（<a href="{UNIFICATION_REPORT}">2026-11-05 のレポート</a>）が推した組（案 A）と wiki の MCP サーバー（案 B）について、決定に足りなかった 9 点を E1〜E11 の測定で確かめた。</p>
</header>

<section id="tldr" class="tldr">
<h2>1. 要約: 閾値を外れた 3 点を決め、ADR-0011 と ADR-0012 に残した</h2>
<p>モデル（ruri-v3-130m の ONNX fp32）とベクトル索引（usearch HNSW f16）は、測定の結果でも変わらない。融合も残す。変えるのはパラメーターだけで、RRF を k={c["k"]}、語彙の重み {c["lexical_weight"]} にする。最初の測定では次の 3 点が計画の閾値を外れたので、計画の停止の規則に従って ADR-0011 と ADR-0012 を書く前で止めた。その後 {e(decisions["date"])} に、測り直しを含めて 3 点を決めた。決定は <a href="../adr/0011-shared-embedding-and-index-stack.md">ADR-0011</a>（技術の組）と <a href="../adr/0012-wiki-owns-local-mcp-index-server.md">ADR-0012</a>（wiki の MCP サーバー）に書いた。</p>
<div class="verdict">
<div class="card ok"><div class="k">語彙検索（E8）</div><div class="v">Tantivy にそろえると決めた</div><div class="small">Sudachi はセクションの MRR {ja_base["section"]["mrr"]:.3f} → {ja_sudachi["section"]["mrr"]:.3f} で落ちた。Tantivy に wiki の bigram を渡すと、指標は wiki の BM25 と同じ</div></div>
<div class="card ok"><div class="k">wiki の初回の再埋め込み（E7）</div><div class="v">目安を緩めると決めた</div><div class="small">R-130、rag の長さのチャンク 8,275 件で約 {r130_natural * r130_ratio / 60:.0f} 分。目安は 20 分だった</div></div>
<div class="card ok"><div class="k">MCP の上乗せ（E10）</div><div class="v">目安を 15 ms に緩めると決めた</div><div class="small">最良の構成で {best_variant["overhead_relay_ms"]:.1f} ms、認証なしでも {noauth["overhead_relay_ms"]:.1f} ms。最初の目安は 10 ms</div></div>
<div class="card ok"><div class="k">変わらなかったもの</div><div class="v">モデル、索引、融合</div><div class="small">E9、E8（R-130）、E1、E3、E4、E5、E6</div></div>
</div>
<ul>
<li>R-130 は wiki の en と ja のゲートを通り、<code>max_distance</code> を {chosen["max_distance"]} にすれば偽陽性 0 にできる。ただし natural の負例 {chosen["natural_negatives_within"]} 問はすべてこの距離の内側に入る。これは e5 でも同じで、今の wiki の限界である。</li>
<li>usearch は全量で FAISS IVF_SQ8 より速い（DB の p95 {ms(best_u["db_p95_ms"])} 対 {ms(best_f["db_p95_ms"])}）。最小点では FAISS が {best_f["score"]["minimum"]:.1f} 点、usearch が {best_u["score"]["minimum"]:.1f} 点で、差の {best_f["score"]["minimum"] - best_u["score"]["minimum"]:.1f} 点は容量の点だけから来る。規則（0.5 点以上の差で FAISS に替える）には届かないが、余裕は小さい。</li>
<li>Windows では Tantivy の commit が約 {retry["results"][0]["error_rate"] * 100:.0f}% の割合で「アクセスが拒否されました」で失敗した。失敗した writer を使い続けると、その後の commit が成功を返しても文書が残らない（{lost_plain["docs_added"]:,} 件中 {lost_plain["docs_in_index"]:,} 件しか残らなかった）。rollback して入れ直せば失われなかったので、語彙エンジンは替えず、この規則を ADR に書く。</li>
<li>Claude Code（CLI {e(claude_job["claude_version"].split()[0])}）は stdio の MCP サーバーをジョブオブジェクトに入れず、サーバーが <code>DETACHED_PROCESS</code> で起動した孫プロセスはセッションの後も残った。セッションをまたいでサーバーを共有するのに WMI は要らない。試作の測定でサーバーが止まったのは、測定に使った Python の MCP の SDK がジョブを使うためだった。</li>
</ul>
</section>

<section id="decide">
<h2>2. 決めたこと</h2>
<div class="opt">
<h3>再埋め込み: 目安の 20 分を緩める（決定）</h3>
<p>{e(decisions["E7_reembed"])}。区間ごとの推定では、rag の長さのチャンク 8,275 件で {minutes(r130_natural)}、wiki の長さのセクションなら {minutes(r130_wiki_scaled)} だった。無作為の 1,000 行で測ると実測は推定の {r130_ratio:.2f} 倍だったので、rag の長さで約 {r130_natural * r130_ratio / 60:.0f} 分になる。wiki の長さの値にも同じ比を掛けると約 {r130_wiki_scaled * r130_ratio / 60:.0f} 分だが、この比は natural の行で測ったもので、wiki のセクションでは確かめていない。1 ページの更新は {r130["page_update"]["seconds"]:.2f} 秒で、目安の 5 秒に収まる。</p>
</div>
<div class="opt">
<h3>語彙検索: 案 2（Tantivy にそろえる）に決めた</h3>
<p>Sudachi（SplitMode C、normalized_form）に替えると、ja のセクションの MRR が {ja_base["section"]["mrr"]:.3f} から {ja_sudachi["section"]["mrr"]:.3f} に下がった。下がったのは {e("、".join(worse_kinds))} の種類である。そこで案 2 を測った。語彙のスコアを Tantivy の BM25 で出し、トークンは wiki の bigram のまま渡す構成である。en と ja のゲートをどちらも通り、ページ・セクション・ハイブリッドの recall@10、MRR、偽陽性の割合は、{"wiki の BM25 と小数第 3 位まで同じだった" if tantivy_same else "wiki の BM25 と一部で違った（§6）"}。個々のスコアは k1（wiki 1.5、Tantivy 1.2）の違いで変わり、下位の順位が入れ替わることはあった。</p>
<ul>
<li>決定（案 2）: 語彙のエンジンを Tantivy にそろえ、wiki の索引には bigram、rag の索引には Sudachi のトークンを入れる。エンジンと索引の扱い（書き込みの規則、世代の削除）は 1 つにまとまり、トークンの作り方だけが索引の集まりごとに違う。</li>
<li>採らなかった案 1: wiki は今の純 Python の BM25 のまま、rag だけ Sudachi + Tantivy にする。</li>
</ul>
</div>
<div class="opt">
<h3>MCP の上乗せ: 目安を 15 ms に緩める（決定）</h3>
<p>同じ日に 5 通りで測った。ログを止めても上乗せはほとんど変わらず、応答を SSE から JSON にすると下がった。認証を starlette の BaseHTTPMiddleware から ASGI のミドルウェアに書き直すと {asgi["overhead_relay_ms"]:.1f} ms、認証を外しても {noauth["overhead_relay_ms"]:.1f} ms だった。認証の書き方は上乗せの原因ではなく、残りの約 {noauth["direct_http_p95_ms"] - noauth["function_p95_ms"]:.0f} ms は Python の MCP の SDK が HTTP で 1 回の呼び出しを処理する費用である。中継の 1 段は {asgi["relay_p95_ms"] - asgi["direct_http_p95_ms"]:.1f} ms だった。</p>
{table(["構成", "関数 p95", "HTTP の MCP p95", "中継経由 p95", "上乗せ"], variant_rows, num=(1, 2, 3, 4))}
<p class="small">「ログなし、JSON の応答」は認証の比較のときにもう 1 度測り、その値で上書きしている。認証なしの行は下限を見るためだけのもので、トークンなしの要求も通る。</p>
<ul>
<li>決定: 目安を 15 ms に緩める。最良の構成（応答は JSON、認証は ASGI のミドルウェア）の {best_variant["overhead_relay_ms"]:.1f} ms で合格とする。</li>
<li>採らなかった案: 目安を「中継の 1 段 ≤ 10 ms」と読む。中継とサーバーのあいだを MCP ではなく軽い JSON の HTTP にする（未測定）。</li>
</ul>
</div>
<p class="small">E6 のメモリの提案値（wiki 規模 1.0 GiB、全量 2.5 GiB）は、モデルを読み込んだ構成ではどの索引でも超えた。FAISS も収まらないので索引の選択は変わらず、提案値のほうを見直す（§12）。</p>
</section>

<section id="q">
<h2>3. 9 つの問いと測定</h2>
{table(["決定に足りなかった点", "測定", "節"], [
    ["融合が dense だけを上回らない", "E1、E2", '<a href="#e1">§7</a>'],
    ["usearch の Windows での保存を実測していない", "E5", '<a href="#e5">§11</a>'],
    ["wiki での再埋め込みの時間が見積もりだけ", "E7", '<a href="#e7">§8</a>'],
    ["常駐メモリが 5.18 GB で、内訳がない", "E6", '<a href="#e6">§12</a>'],
    ["世代の絞り込みの費用を測っていない", "E4", '<a href="#e4">§10</a>'],
    ["ADR-0001 と ADR-0007 との整合", "E10", '<a href="#e10">§13</a>、<a href="#adr">§16</a>'],
    ["wiki の評価ゲートと max_distance の較正", "E8", '<a href="#e8">§6</a>'],
    ["ONNX の配布", "E9", '<a href="#e9">§5</a>'],
    ["OCR の結果を再利用できない設計", "設計", '<a href="#ocr">§15</a>'],
])}
<p>測定ごとの判定は次のとおり。DB のつまみ（E3）は、案 A の索引の選択を全量で確かめ直すために加えた。</p>
{table(["測定", "確かめたこと", "判定"], gate_rows)}
<p class="small">判定は <code>decision-scores.json</code> の <code>gates</code>。E6 は計画の停止の規則（usearch が上限を超え、かつ FAISS が収まるときだけ索引を替える）で判定した。</p>
</section>

<section id="cond">
<h2>4. 測定の条件</h2>
<ul class="tight">
<li>{e(env["platform"])}、Python {e(env["python"])}、論理 CPU {env["logical_cpus"]} のうち {env["cpu_threads_limit"]} スレッドに制限した。</li>
<li>usearch {e(pkgs["usearch"])}、faiss-cpu {e(pkgs["faiss-cpu"])}、tantivy {e(pkgs["tantivy"])}、onnxruntime {e(pkgs["onnxruntime"])}、fastembed {e(pkgs["fastembed"])}、sudachipy {e(pkgs["sudachipy"])}。E10 は mcp を入れた別の venv で測った。</li>
<li>データは全量 761,915 チャンク（60 問）、natural 8,275 行（PDF 60 問、wiki 47 問）、wiki の評価用コーパス（en と ja）。1 問は全量で {deep["one_question"]:.3f} にあたる。</li>
<li>info-hive-dev {e(env["dev_commit"])}、info-hive-wiki {e(env["wiki_commit"])}、info-hive-rag {e(env["rag_commit"])}。</li>
</ul>
</section>

<section id="e9">
<h2>5. ONNX の配布（E9）: 公開版でそのまま使える</h2>
<p>空のキャッシュから <code>onnx-community/ruri-v3-130m-ONNX</code> と <code>cl-nagoya/ruri-v3-130m</code> のトークナイザーを取得した。{len(onnx["files"])} ファイルの sha256 はすべて測定に使ったものと同じで、取得は {onnx["download_seconds"]:.0f} 秒、重みは {mib(onnx["weights_bytes"])} だった。ライセンスはどちらも {e(onnx["licenses"]["onnx-community/ruri-v3-130m-ONNX"])}。GPU の sentence-transformers と比べた cosine の最小は {onnx["parity"]["cosine_min"]:.4f}、上位 30 件の一致は {onnx["parity"]["top30_overlap_within_parity"]:.3f} である。</p>
</section>

<section id="e8">
<h2>6. wiki の評価ゲート（E8）: R-130 と Tantivy + bigram は通り、Sudachi は ja で落ちる</h2>
<p>r130-tantivy は、語彙のスコアを Tantivy の BM25 で出し、トークンは wiki の bigram のまま渡した構成（§2 の案 2）である。</p>
{table(["構成", "コーパス", "ページ MRR", "セクション MRR", "ハイブリッド MRR", "ハイブリッド recall@10", "判定"],
       [[e(v), cc, f'{g[v][cc]["metrics"]["page"]["mrr"]:.3f}', f'{g[v][cc]["metrics"]["section"]["mrr"]:.3f}', f'{g[v][cc]["metrics"]["hybrid"]["mrr"]:.3f}',
         f'{g[v][cc]["metrics"]["hybrid"]["recall@10"]:.3f}', ok_cell(g[v][cc]["exit_code"] == 0)] for v in ("e5", "r130", "r130-sudachi", "r130-tantivy") for cc in ("en", "ja")],
       num=(2, 3, 4, 5))}
<p>較正: 正例が必要とする距離の最大は {chosen["positive_needed_max"]:.4f}、負例の最も近い距離の最小は {chosen["negative_nearest_min"]:.4f} で、あいだに偽陽性 0 の範囲がある。中点の {chosen["max_distance"]} を選んだ。natural では正例 {chosen["natural_positives_within"]} / {chosen["natural_positives"]} 問と負例 {chosen["natural_negatives_within"]} / {chosen["natural_negatives"]} 問が内側に入った。</p>
{table(["種類（ja のセクション）", "bigram recall@10", "Sudachi recall@10"],
       [[e(k), f'{v["bigram_recall@10"]:.3f}', f'<td class="num {"ng" if k in worse_kinds else ""}">{v["sudachi_recall@10"]:.3f}</td>'] for k, v in kinds.items() if k != "negative"],
       num=(1, 2))}
</section>

<section id="e1">
<h2>7. 融合（E1、E2）: 残し、k と重みを変える</h2>
<p>保存済みの順位で、k（10〜200）× 語彙の重み（0〜2）× 候補数（30〜200）を掃引した。natural で最良だったのは k={c["k"]}、語彙の重み {c["lexical_weight"]}、候補数 {c["candidates"]} で、どのセットでも 1 問を超えて悪化しなかった。既存値（全量の融合 {base_row["full-usearch"]["recall_at_30"]:.3f}）も再現した。</p>
{table(["セット", "再現率@30（k=60）", f'再現率@30（k={c["k"]}）', "差", "nDCG@10（k=60）", f'nDCG@10（k={c["k"]}）', "上がった / 下がった問"], fusion_rows, num=(1, 2, 3, 4, 5, 6))}
<p>E2 では全量で候補数を 400、800 に増やし、スコアを正規化する融合も試した。E1 の設定は全量で {e1_full["recall_at_30"]:.3f} だった。min-max 正規化（α=0.6）は {mm["recall_at_30"]:.3f} で、下がった問が 0 だったが、差は 1 問未満で natural では選んでいない。候補として記録だけ残す。候補数を 800 にしても DB の p95 の増分は数 ms だった。</p>
{table(["候補数", "融合", "再現率@30", "nDCG@10", "上がった / 下がった問（k=60 比）", "DB p95"], deep_rows, num=(0, 2, 3, 4, 5))}
</section>

<section id="e7">
<h2>8. 再埋め込みの時間（E7）: R-130 の初回は目安を超える</h2>
<p>長さの区間（256〜4,096 トークン以上）ごとに 48 件を測り、natural 8,275 行の長さの分布で合計を推定した。wiki の長さの列は、wiki のコーパス {rows_wiki} セクションの推定を 8,275 セクションに伸ばした値である。補正の比は、natural から無作為に選んだ 1,000 行の実測と推定の比。</p>
{table(["モデル", "バッチ", "推定（rag の長さ）", "実測 / 推定", "補正後", "推定（wiki の長さ）", "1 ページの更新"], reembed_rows, num=(1, 2, 3, 4, 5, 6))}
</section>

<section id="e3">
<h2>9. DB のつまみ（E3）: usearch M16 / expansion_add 256 が最も速い</h2>
<p>動作点は、dense の厳密解に対する再現率@30 が 0.95 以上になる最も安い設定（usearch は ef、FAISS は nprobe）。既存の索引の再現では dense の p95 が {repro["dense_p95_ms"]:.1f} ms で、統一の測定の {repro["expected"]} ms から ±10% を外れた。統一の測定は GPU の仕事と並べて測っていたので、今回のほうが速く出たと考える。</p>
{table(["構成", "動作点", "dense p95", "DB p95", "dense の再現率", "再現率@30", "ベクトルの容量", "構築"], knob_rows, num=(1, 2, 3, 4, 5, 6, 7))}
</section>

<section id="e4">
<h2>10. 世代の絞り込み（E4）: 増分は誤差の範囲</h2>
<p>無効の世代の文書を 1〜20% にし、usearch は多めに取ってから後で除く方式、FAISS は IDSelector で除く方式を比べた。p95 の増分はどれも ±数 ms で、計画の目安（20 ms）に収まった。負の値は誤差である。</p>
{table(["無効の文書", "無効の行", "usearch の倍率", "usearch 増分", "usearch 再現率", "FAISS 増分", "FAISS 再現率", "FAISS の漏れ"], gen_rows, num=(1, 2, 3, 4, 5, 6, 7))}
<p>文書の 10%（{rm["rows"]:,} 行）を消す操作は、usearch の remove が {rm["remove_seconds"]:.3f} 秒（再現率の変化 {rm["recall_drop"]:+.3f}）、FAISS の remove_ids が {frm["remove_seconds"]:.3f} 秒、Tantivy の削除と commit が {td["delete_commit_seconds"]:.3f} 秒だった。FAISS は IndexIDMap2 で IVF を包むと remove_ids の後に id の対応が壊れたので、IVF に直接 id を付けて作った。</p>
</section>

<section id="e5">
<h2>11. 書き込みの安全性（E5）: 単一の書き手なら安全、Tantivy は入れ直しが要る</h2>
<ul>
<li>(a) 別のプロセスが view で開いている索引ファイルの置き換えは、{a["attempts"]} 回とも PermissionError で失敗した（成功 {a["succeeded"]} 回）。Windows では、メモリに写像されたファイルを置き換えられない。</li>
<li>(b) 1 つのプロセスが索引を読み込み、追記、一時ファイルへの保存、<code>os.replace</code> を繰り返した。wiki 規模 {bw["rounds"]} 回、全量 {bf["rounds"]} 回で、保存・置き換え・検索のエラーは 0、最終の件数も一致した。保存の最大は wiki 規模 {bw["save_seconds_max"]:.2f} 秒、全量 {bf["save_seconds_max"]:.1f} 秒。読み書きのロックは書き手を優先する形にした。読み手を優先する形では、検索が途切れないと書き手がロックを取れず、測定が 6 時間止まった。</li>
<li>(c) 版ごとのファイルと manifest の付け替えは、強制終了 {cv["kills"]} 回の後も壊れた版はなかったが、書き手が manifest.json の置き換えで PermissionError になった。読み手が manifest.json を開いている間は置き換えられないためと考える。この方式を Windows で使うなら、書き手と読み手の両方に入れ直しが要る。</li>
<li>(d) 別のプロセスの読み手が reload を続けると、Tantivy の commit {d["commits"]:,} 回のうち {len(d["writer_errors"]):,} 回が失敗した。同じプロセスの読み手（d2）でも {d2["commits"]:,} 回のうち {len(d2["writer_errors"]):,} 回が失敗し、最後に残った文書は {d2["num_docs_after"]:,} 件（追加したのは {d2["expected_docs"]:,} 件）だった。</li>
</ul>
<p>読み手がいなくても失敗するかを、書き手だけで確かめた。</p>
{table(["commit の間隔", "失敗したとき", "commit", "失敗", "失敗の割合", "追加した文書", "残った文書", "失われた文書"], retry_rows, num=(0, 2, 3, 4, 5, 6, 7))}
<p>失敗の原因（ウイルス対策の走査など）は切り分けていない。ADR には「索引の書き手はサーバーの 1 プロセスだけ」「usearch は一時ファイルに保存して置き換える」「Tantivy の commit が失敗したら rollback して同じ文書を入れ直す」を書く。</p>
</section>

<section id="e6">
<h2>12. 常駐メモリ（E6）: 大半はモデルと長い文書の埋め込み</h2>
<p>構成ごとに新しいプロセスで測った。private は Windows のコミット済みの専用メモリで、測定用のプロセスは何も読み込まない時点で {gib(view_wiki["stages"]["start"]["private"])} ある。モデルを読み込むと約 {gib(view_wiki["stages"]["model_loaded"]["private"] - view_wiki["stages"]["start"]["private"])} 増え、最長 20 件の文書を 1 回で埋め込むとさらに約 {gib(view_wiki["stages"]["after_longest_passages"]["private"] - view_wiki["stages"]["after_queries"]["private"])} 増えた。測定の最後まで減らなかったのは、onnxruntime が確保した領域を返さないためと考える。</p>
{table(["規模", "索引", "モデル", "開始時", "モデル読み込み後", "クエリの後", "最長の文書の後", "作業セットの最大"], mem_rows, num=(3, 4, 5, 6, 7))}
<p>usearch を view で開く構成は、どちらの規模でも 3 つの索引のうち最も小さい（モデルなしで wiki 規模 {gib(view_wiki_none["private_bytes"])}、モデルありの最後で全量 {gib(view_full["private_bytes"])}）。提案値（wiki 規模 {memory["limits_private_gib"]["wiki"]} GiB、全量 {memory["limits_private_gib"]["full"]} GiB）はどの索引でも超えたので、埋め込みのバッチの大きさと文書の長さの上限と合わせて、値を決め直す。</p>
</section>

<section id="e10">
<h2>13. MCP の中継（E10）: 形は成り立ち、上乗せは目安を超えた</h2>
{table(["項目", "結果"], [
    ["関数の直接呼び出し p95", ms(relay["function_p95_ms"])],
    ["HTTP のサーバーへ直接 MCP p95", ms(relay["direct_http"]["query_p95_ms"])],
    ["stdio の中継経由 p95（サーバー起動済み）", ms(relay["relay_warm"]["query_p95_ms"])],
    ["中継の起動から initialize まで（サーバーも起動）", f'{relay["relay_cold"]["initialize_seconds"]:.1f} 秒'],
    ["中継の起動から initialize まで（サーバー起動済み）", f'{relay["relay_warm"]["initialize_seconds"]:.1f} 秒'],
    ["index_chunks（1,000 チャンク）", f'{relay["relay_cold"]["index_chunks"]["payload_bytes"] / 2 ** 20:.1f} MiB を {ms(relay["relay_cold"]["index_chunks"]["ms"])}'],
    ["トークンなし / 違うトークン / Host の偽装", f'{relay["direct_http"]["security"]["no_token"]} / {relay["direct_http"]["security"]["wrong_token"]} / {relay["direct_http"]["security"]["spoofed_host"]}'],
    ["中継を 4 つ同時に起動", f'サーバーは {relay["concurrent_summary"]["distinct_server_pids"]} つ（同時に見えた最大 {relay["concurrent_summary"]["max_servers_seen"]}）'],
    ["中継の終了後もサーバーが残る", "残った" if relay["server_survived_relay_exit"] else "残らなかった"],
    [f'要求がなくなって {relay["idle_shutdown"]["idle_seconds"]} 秒後', ("止まった" if relay["idle_shutdown"]["servers_after_idle"] == 0 else f'{relay["idle_shutdown"]["servers_after_idle"]} つ残った')],
])}
<p>サーバーの起動のしかたで 2 つの問題が出た。1 つ目は、venv の <code>python.exe</code> が本体を子プロセスとして起動するので、<code>Popen</code> が返す pid と、サーバーが記録した pid が一致しないこと。起動の前にロックの中で <code>server.json</code> を消し、新しく現れた <code>server.json</code> を今起動したサーバーのものとみなすようにした。2 つ目は、MCP の SDK（mcp 1.30.0）の <code>stdio_client</code> が中継を KILL_ON_JOB_CLOSE のジョブに入れること。<code>DETACHED_PROCESS</code> も <code>CREATE_BREAKAWAY_FROM_JOB</code> も、エラーにはならなかったがサーバーはジョブに残り、中継の終了とともに止まった。WMI（<code>Win32_Process.Create</code>）に起動させるとジョブの外に出た。</p>
<p>このジョブは、測定に使った Python の MCP の SDK のものである。Claude Code（CLI {e(claude_job["claude_version"].split()[0])}）でも起きるかを、標準ライブラリだけで書いた最小の MCP サーバーを <code>claude -p</code> に登録して確かめた。サーバーはジョブに入って{"いた" if claude_job["claude"]["job"]["in_job"] else "いなかった"}。<code>DETACHED_PROCESS</code> で起動した孫は、claude が終わった後も{"残った" if claude_job["summary"]["detached_grandchild_survives_claude"] else "残らなかった"}（サーバー自身は claude とともに終わった）。Claude Code の下では、サーバーを <code>DETACHED_PROCESS</code> で起動すれば足りる。デスクトップアプリは測っていない。</p>
</section>

<section id="e11">
<h2>14. 最終の採点（E11）: usearch が速く、FAISS が小さい</h2>
<p>統一の測定と同じ式で採点した。速度はクエリの埋め込みの p95（ほかの仕事がない状態で測り直した {ms(final["query_embedding"]["p95_ms"])}）、DB の p95、世代の絞り込みの増分の和。精度は統一の測定と同じ RRF k=60 の再現率@30 で、E1 の融合の設定は、どの行にも同じものを使うので、この表には含めていない。LanceDB の行は統一の測定の値である。</p>
{table(["構成", "速度", "容量", "再現率@30", "速度点", "容量点", "精度点", "最小"], score_rows, num=(1, 2, 3, 4, 5, 6, 7))}
</section>

<section id="ocr">
<h2>15. OCR と fingerprint: 抽出用と索引用に分ける</h2>
<p>今の rag の fingerprint はモデルを含むので、モデルを替えると 22,335 ページの OCR からやり直すことになる。統一の測定のレポートの §12 はこの前提で移行の手間を見積もっていた。ADR-0011 では fingerprint を 2 つに分ける。抽出用は OCR の方式、dpi、revision から作り、抽出結果の再利用に使う。索引用はモデル、実行系、チャンクの切り方、索引の種類から作り、埋め込みと索引だけを作り直す判断に使う。この分け方は設計で、今回は測っていない。</p>
</section>

<section id="adr">
<h2>16. ADR との整合</h2>
<ul>
<li>ADR-0001: 127.0.0.1 だけで待ち受け、起動ごとのトークンと Host の確認を入れた試作で、トークンなしは 401、Host の偽装は 421 になった。wiki を書き換える API を持たない条件 3 に当たるので、案 B のツールから ingest_source を外す。</li>
<li>ADR-0007: サーバーは使われなければ止まり（idle で 0 になった）、OS のサービスとして登録しない。Claude Code の下では <code>DETACHED_PROCESS</code> で起動すれば足り、WMI のようにホストの外からプロセスを起動する方式は使わない。</li>
<li>ADR-0010: 未決 4（RAG の経路）に、wiki の MCP サーバーに検索と索引の更新を頼む案を加える。状態は変えない。</li>
</ul>
</section>

<section id="repro">
<h2>17. 再現と出典</h2>
<p>スクリプトは <code>poc/rag/decision/</code>、結果の JSON は <code>docs/research/embedding-backend-decision-2026-11-06/</code> にある。手順とファイルの一覧は同じフォルダーの README.md に書いた。</p>
<pre>set INFO_HIVE_POC_DATA=C:\\Works\\info-hive-dev-data\\rag-poc-data
cd poc\\rag\\decision
%INFO_HIVE_POC_DATA%\\unification-20261105\\venv\\Scripts\\python.exe -X utf8 decision_summary.py
%INFO_HIVE_POC_DATA%\\unification-20261105\\venv\\Scripts\\python.exe -X utf8 build_decision_report.py</pre>
</section>
<footer>数値はすべて JSON から生成した。生成: <code>poc/rag/decision/build_decision_report.py</code></footer>
</main>
</div>
</body>
</html>
"""
    REPORT.write_text(body, encoding="utf-8", newline="\n")
    print("書き出した", REPORT)


if __name__ == "__main__":
    main()
