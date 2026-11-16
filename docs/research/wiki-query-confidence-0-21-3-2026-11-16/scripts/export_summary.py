# 全回の要約に、回答を読んで付けた判定を合わせ、runs-summary.json に書き出す
#
# 判定の欄
# - got: 回答の終わりの決まった 1 行の確からしさ。決まった 1 行がなければ、その旨を書く
# - path: 根拠のページをどう見つけたか（index: インデックスから開いた、search: wiki の検索、grep: Grep、graph: グラフ）
# - reason_ok: 理由が規則どおりか（はい、部分、いいえ）
# - raise_fit: 上げる方法が要因に合っていたか（はい、部分、いいえ。「高」と「なし」では null）
# - inline: 複数の結論の問いで、結論のそばに「（確からしさ: X）」を書いたか
# - kind: 期待との関係（match: 一致、alt: 事前に書いた別の読みに当たる、unregistered: 事前に書いていない経路で外れた、
#   violation: 規則の外れ）
#
# 書き出す前に、セッションの一時の場所（利用者名とセッションの ID を含む）を <SCRATCH> に置き換える
#
# 手で付けた判定（J）は、判定したときのログにだけ当てはまる。ログの SHA-256 を judged-logs.json に残し、
# ハッシュの合わないログ（測り直したログなど）や、判定のないログがあれば、書き出さずに止まる。
# 判定を付け直したら、--bind でハッシュを記録し直す。
# 使い方: python export_summary.py [--bind]
import hashlib
import json
import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from summarize import found_by, summarize, short  # noqa: E402
from paths import QUESTIONS, SUMMARY as OUT, plugin_dir, require_runs, wiki_base  # noqa: E402

RUNS = require_runs()
GF = "作業前の git fetch に触れた（利用者のグローバルの指示が子にも読み込まれた）"

# 0.21.3 の測り直しの判定。回答を読んで付け、--bind でログのハッシュに結ぶ
J = {
}

# セッションの一時の場所（利用者名とセッションの ID を含む）を <SCRATCH> に置き換える
SCRATCH = re.compile(r"(?i)(?:[a-z]:|/[a-z])[\\/]+UserData[\\/]+[^\\/\s\"]+[\\/]+Temp[\\/]+claude[\\/]+[0-9a-f]+"
                     r"[\\/]+[0-9a-f-]+[\\/]+scratchpad")
LEFT = re.compile(r"(?i)(?:[a-z]:|/[a-z])?[\\/]*UserData[\\/]+[^\s\"]*")


def scrub(v):
    if isinstance(v, str):
        return LEFT.sub("<SCRATCH>…", SCRATCH.sub("<SCRATCH>", v))
    if isinstance(v, list):
        return [scrub(x) for x in v]
    if isinstance(v, dict):
        return {k: scrub(x) for k, x in v.items()}
    return v


JUDGED = OUT.with_name("judged-logs.json")


def log_hashes() -> dict:
    return {log.stem: hashlib.sha256(log.read_bytes()).hexdigest() for log in sorted(RUNS.glob("R*-r[0-9].jsonl"))}


current = log_hashes()
if "--bind" in sys.argv[1:]:
    missing = sorted(k for k in current if tuple(k.split("-r")) not in J)
    if missing:
        sys.exit(f"判定のないログがある: {', '.join(missing)}（J に判定を足してから --bind する）")
    JUDGED.write_bytes((json.dumps(current, ensure_ascii=False, indent=1) + "\n").encode("utf-8"))
    print(f"{len(current)} 件のログのハッシュを {JUDGED.name} に記録した")
judged = json.loads(JUDGED.read_text(encoding="utf-8")) if JUDGED.is_file() else {}
stale = sorted(k for k in current if judged.get(k) != current[k])
gone = sorted(k for k in judged if k not in current)
if stale or gone:
    sys.exit("判定を付けたときのログと合わない。回答を読んで J を付け直し、--bind で記録し直す\n"
             + (f"  ハッシュが違うか未判定: {', '.join(stale)}\n" if stale else "")
             + (f"  判定したのに見当たらない: {', '.join(gone)}\n" if gone else ""))

qs = {q["id"]: q for q in json.loads(QUESTIONS.read_text(encoding="utf-8"))}
rows = []
for meta in sorted(RUNS.glob("R*-r[0-9].meta.json")):
    m = json.loads(meta.read_text(encoding="utf-8"))
    s = summarize(meta.with_name(meta.name.replace(".meta.json", ".jsonl")))
    j = J[(m["qid"], m["rep"])]
    if j["got"] in ("高", "中", "低") and s["final_marks"] != [j["got"]]:
        sys.exit(f"{m['qid']} r{m['rep']}: 判定 {j['got']} が回答の決まった 1 行 {s['final_marks']} と合わない")
    rows.append({
        "qid": m["qid"], "rep": int(m["rep"]), "trial": m["rep"] == "0", "condition": m["condition"],
        "expect": qs[m["qid"]]["expect"], **j,
        "final_marks": s["final_marks"], "inline_marks": s["inline_marks"],
        "opened_query_confidence": s["opened_confidence"], "searches": s["searches"],
        "graph_calls": s["graph_calls"],
        "found_by": found_by(s, qs[m["qid"]].get("answer_pages", [])),
        "model": s.get("model"), "seconds": m["seconds"], "cost_usd": round(s.get("cost") or 0, 4),
        "turns": s.get("turns"),
        "tools": [{"name": t["name"], "input": short(scrub(t["input"]), 220), "error": bool(t.get("is_error"))}
                  for t in s["tools"]],
        "permission_denials": scrub(s.get("denials")), "wiki_changed": m["wiki_changed"],
        "answer": scrub(s.get("result")),
    })
rows = scrub(rows)
text = json.dumps(rows, ensure_ascii=False, indent=1) + "\n"
OUT.write_bytes(text.encode("utf-8"))
main = [r for r in rows if not r["trial"]]
print(len(rows), "rows", round(sum(r["cost_usd"] for r in rows), 2), "USD")
print("本番の一致", sum(r["got"] == r["expect"] for r in main), "/", len(main))
print("kind", {k: sum(r["kind"] == k for r in main) for k in ("match", "alt", "unregistered", "violation")})
print("残った UserData", text.count("UserData"))
print("query-confidence.md を開いた", sum(r["opened_query_confidence"] for r in rows), "/", len(rows))
print("グラフに問い合わせた", sum(bool(r["graph_calls"]) for r in rows), "/", len(rows))
print("wiki が変わった", sum(r["wiki_changed"] for r in rows))
