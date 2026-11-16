# 全回の要約に、回答を読んで付けた判定を合わせ、runs-summary.json に書き出す
#
# 判定の欄
# - got: 回答の終わりの決まった 1 行の確からしさ。決まった 1 行がなければ、その旨を書く
# - path: 根拠のページをどう見つけたか（index: インデックスから開いた、search: wiki の検索、grep: Grep）
# - reason_ok: 理由が規則どおりか（はい、部分、いいえ）
# - raise_fit: 上げる方法が要因に合っていたか（はい、部分、いいえ。「高」と「なし」では null）
# - inline: 複数の結論の問いで、結論のそばに「（確からしさ: X）」を書いたか
# - kind: 期待との関係（match: 一致、alt: 事前に書いた別の読みに当たる、violation: 規則の外れ）
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from summarize import summarize, short  # noqa: E402
from paths import QUESTIONS, SUMMARY as OUT, require_runs  # noqa: E402

RUNS = require_runs()
GF = "作業前の git fetch に触れた（利用者のグローバルの指示が子にも読み込まれた）"

J = {
 ("R01", "0"): {"got": "高", "path": "index", "reason_ok": "はい", "kind": "match", "note": "試しの回。理由の wikilink を「管理者グイド」と書き損じた"},
 ("R01", "1"): {"got": "高", "path": "index", "reason_ok": "はい", "kind": "match"},
 ("R01", "2"): {"got": "高", "path": "index", "reason_ok": "はい", "kind": "match"},
 ("R01", "3"): {"got": "高", "path": "index", "reason_ok": "はい", "kind": "match"},
 ("R02", "1"): {"got": "なし", "path": "index", "reason_ok": "はい", "kind": "match"},
 ("R02", "2"): {"got": "なし", "path": "index", "reason_ok": "はい", "kind": "match"},
 ("R02", "3"): {"got": "なし", "path": "index", "reason_ok": "はい", "kind": "match"},
 ("R03", "1"): {"got": "低", "path": "index", "reason_ok": "はい", "raise_fit": "はい", "kind": "match"},
 ("R03", "2"): {"got": "低", "path": "index", "reason_ok": "はい", "raise_fit": "はい", "kind": "match"},
 ("R03", "3"): {"got": "低", "path": "index", "reason_ok": "はい", "raise_fit": "はい", "kind": "match"},
 ("R04", "1"): {"got": "低", "path": "index", "reason_ok": "はい", "raise_fit": "はい", "kind": "match"},
 ("R04", "2"): {"got": "低", "path": "index", "reason_ok": "はい", "raise_fit": "部分", "kind": "match", "note": "/wiki:lint で古い主張を確かめる提案がない"},
 ("R04", "3"): {"got": "低", "path": "index", "reason_ok": "はい", "raise_fit": "部分", "kind": "match", "note": "/wiki:lint の提案がない。決まった 1 行を回答の頭に置いた"},
 ("R05", "1"): {"got": "高", "path": "index", "reason_ok": "はい", "kind": "match"},
 ("R05", "2"): {"got": "高", "path": "index", "reason_ok": "はい", "kind": "match", "note": GF},
 ("R05", "3"): {"got": "高", "path": "index", "reason_ok": "はい", "kind": "match"},
 ("R06", "1"): {"got": "中", "path": "index", "reason_ok": "はい", "raise_fit": "部分", "kind": "match", "note": "古いページを直すことと /wiki:lint の提案がない"},
 ("R06", "2"): {"got": "中", "path": "index", "reason_ok": "はい", "raise_fit": "部分", "kind": "match", "note": "同上"},
 ("R06", "3"): {"got": "中", "path": "index", "reason_ok": "はい", "raise_fit": "部分", "kind": "match", "note": "同上"},
 ("R07", "1"): {"got": "低", "path": "index", "graph": "frontmatter", "reason_ok": "はい", "raise_fit": "部分", "kind": "match", "note": "グラフに問い合わせず、エッジは佐伯のページの frontmatter で読んだ。/wiki:graph lint の提案がない"},
 ("R07", "2"): {"got": "低", "path": "index", "graph": "frontmatter", "reason_ok": "はい", "raise_fit": "はい", "kind": "match", "note": "グラフに問い合わせず、エッジは frontmatter で読んだ"},
 ("R07", "3"): {"got": "低", "path": "search", "graph": "なし", "reason_ok": "いいえ", "raise_fit": "部分", "kind": "match", "note": "エッジの行は当てはまらないと書き、表にない「前提の性質」で低にした。ラベルだけが合った"},
 ("R08", "1"): {"got": "高", "path": "index", "graph": "frontmatter", "reason_ok": "部分", "kind": "alt", "note": "エッジの medium を見たうえで「根拠はエッジではなくソースの要約ページ」として上限に数えなかった"},
 ("R08", "2"): {"got": "高", "path": "index", "graph": "frontmatter", "reason_ok": "部分", "kind": "alt", "note": "エッジの存在に触れたが confidence に触れず、上限に数えなかった"},
 ("R08", "3"): {"got": "中", "path": "index", "graph": "frontmatter", "reason_ok": "はい", "raise_fit": "部分", "kind": "match", "note": "エッジの書き直しは提案したが、/wiki:graph lint がない"},
 ("R09", "1"): {"got": "中", "path": "search", "reason_ok": "はい", "raise_fit": "はい", "kind": "match", "note": GF},
 ("R09", "2"): {"got": "中", "path": "search", "reason_ok": "はい", "raise_fit": "はい", "kind": "match"},
 ("R09", "3"): {"got": "中", "path": "search", "reason_ok": "はい", "raise_fit": "はい", "kind": "match", "note": GF},
 ("R10", "1"): {"got": "中", "path": "search", "reason_ok": "はい", "raise_fit": "はい", "kind": "match"},
 ("R10", "2"): {"got": "中", "path": "search", "reason_ok": "はい", "raise_fit": "はい", "kind": "match", "note": GF},
 ("R10", "3"): {"got": "中", "path": "search", "reason_ok": "はい", "raise_fit": "はい", "kind": "match"},
 ("R11", "0"): {"got": "中", "path": "search", "reason_ok": "はい", "raise_fit": "はい", "kind": "match", "note": "試しの回"},
 ("R11", "1"): {"got": "中", "path": "search", "reason_ok": "はい", "raise_fit": "はい", "kind": "match"},
 ("R11", "2"): {"got": "高", "path": "grep", "reason_ok": "部分", "kind": "alt", "note": "Grep で見つけたのに「索引から候補を直接見つけた」と書いた。Grep の扱いは規則にない"},
 ("R11", "3"): {"got": "中", "path": "search", "reason_ok": "はい", "raise_fit": "はい", "kind": "match", "note": "理由に、理由 3（モデルを使えない）と理由 4（埋め込みの途中）の言い方が混ざった。上げる方法は理由 3 のもの"},
 ("R12", "0"): {"got": "高", "path": "search", "reason_ok": "いいえ", "kind": "violation", "note": "試しの回。MCP の縮退した検索で見つけたのに「ページ本体を読んだので下げない」とした"},
 ("R12", "1"): {"got": "中", "path": "search", "reason_ok": "はい", "raise_fit": "はい", "kind": "match"},
 ("R12", "2"): {"got": "高", "path": "grep", "reason_ok": "部分", "kind": "alt", "note": "Grep で見つけたのに「インデックスから直接候補を見つけた」と書いた。" + GF},
 ("R12", "3"): {"got": "中", "path": "search", "reason_ok": "はい", "raise_fit": "はい", "kind": "match"},
 ("R13", "1"): {"got": "高", "path": "index", "reason_ok": "はい", "kind": "match"},
 ("R13", "2"): {"got": "高", "path": "index", "reason_ok": "はい", "kind": "match"},
 ("R13", "3"): {"got": "高", "path": "index", "reason_ok": "はい", "kind": "match", "note": "縮退した MCP の検索も使ったが、インデックスから見つけたので上限に数えないと明記した"},
 ("R14", "1"): {"got": "中", "path": "index", "reason_ok": "はい", "raise_fit": "はい", "inline": "理由の中だけ", "kind": "match"},
 ("R14", "2"): {"got": "中", "path": "index", "reason_ok": "はい", "raise_fit": "はい", "inline": "理由の中だけ", "kind": "match"},
 ("R14", "3"): {"got": "中", "path": "index", "reason_ok": "はい", "raise_fit": "はい", "inline": "結論のそば", "kind": "match"},
 ("R15", "1"): {"got": "決まった行なし", "path": "index", "reason_ok": "はい", "raise_fit": "部分", "inline": "理由の中だけ", "kind": "violation", "note": "決まった 1 行を「設定ファイルの場所は高。上限は低」と崩し、回答全体の確からしさを書かなかった。/wiki:lint の提案がない"},
 ("R15", "2"): {"got": "低", "path": "index", "reason_ok": "はい", "raise_fit": "はい", "inline": "理由の中だけ", "kind": "match"},
 ("R15", "3"): {"got": "低", "path": "index", "reason_ok": "はい", "raise_fit": "はい", "inline": "理由の中だけ", "kind": "match"},
}

qs = {q["id"]: q for q in json.loads(QUESTIONS.read_text(encoding="utf-8"))}
rows = []
for meta in sorted(RUNS.glob("R*-r[0-9].meta.json")):
    m = json.loads(meta.read_text(encoding="utf-8"))
    s = summarize(meta.with_name(meta.name.replace(".meta.json", ".jsonl")))
    j = J[(m["qid"], m["rep"])]
    rows.append({
        "qid": m["qid"], "rep": int(m["rep"]), "trial": m["rep"] == "0", "condition": m["condition"],
        "expect": qs[m["qid"]]["expect"], **j,
        "final_marks": s["final_marks"], "inline_marks": s["inline_marks"],
        "opened_query_confidence": s["opened_confidence"], "searches": s["searches"],
        "graph_calls": s["graph_calls"],
        "model": s.get("model"), "seconds": m["seconds"], "cost_usd": round(s.get("cost") or 0, 4),
        "turns": s.get("turns"),
        "tools": [{"name": t["name"], "input": short(t["input"], 220), "error": bool(t.get("is_error"))} for t in s["tools"]],
        "permission_denials": s.get("denials"), "wiki_changed": m["wiki_changed"],
        "answer": s.get("result"),
    })
OUT.write_bytes((json.dumps(rows, ensure_ascii=False, indent=1) + "\n").encode("utf-8"))
main = [r for r in rows if not r["trial"]]
print(len(rows), "rows", round(sum(r["cost_usd"] for r in rows), 2), "USD")
print("本番の一致", sum(r["got"] == r["expect"] for r in main), "/", len(main))
print("kind", {k: sum(r["kind"] == k for r in main) for k in ("match", "alt", "violation")})
print("query-confidence.md を開いた", sum(r["opened_query_confidence"] for r in rows), "/", len(rows))
print("グラフに問い合わせた", sum(bool(r["graph_calls"]) for r in rows), "/", len(rows))
print("wiki が変わった", sum(r["wiki_changed"] for r in rows))
