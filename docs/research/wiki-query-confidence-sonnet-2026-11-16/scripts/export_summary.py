# 全回の要約に手で付けた判定を合わせ、docs/research に書き出す
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from summarize import summarize, short  # noqa: E402

SCRATCH = Path(__file__).resolve().parent
OUT = Path(r"C:\Works\info-hive-dev\.claude\worktrees\infallible-elbakyan-e57994\docs\research\wiki-query-confidence-sonnet-2026-11-16\runs-summary.json")

# 回答を読んで付けた判定（got: 回答全体の確からしさ。部分の問いは答えた部分の判定）
J = {
 ("Q01","0"): {"got":"高","note":"試しの回。高のときも原本を開く提案を添えた"},
 ("Q01","1"): {"got":"高"}, ("Q01","2"): {"got":"高"}, ("Q01","3"): {"got":"高"},
 ("Q02","1"): {"got":"中","note":"raw の研究レポートを承認なしに grep して一致を確かめたうえで、規則にない上限（実行が 1 回だけ）で中にした"},
 ("Q02","2"): {"got":"高"},
 ("Q02","3"): {"got":"中","note":"規則にない上限（raw で確かめていない）で中にした"},
 ("Q03","1"): {"got":"中","external":"AGENTS.md の CSP の記述を「補足（wiki の外）」として添えた"},
 ("Q03","2"): {"got":"中"},
 ("Q03","3"): {"got":"中","external":"AGENTS.md の CSP の記述を添えた"},
 ("Q04","1"): {"got":"中","note":"メインのチェックアウトの docs/plans を grep し、その記述も理由に使った","raise_fit":"部分"},
 ("Q04","2"): {"got":"中","note":"グローバルの指示の git fetch を試み、権限で拒まれた"},
 ("Q04","3"): {"got":"中"},
 ("Q05","1"): {"got":"低","note":"仮説の上限に加え、規則にない上限（成功が 1 回だけ）で低にした"},
 ("Q05","2"): {"got":"中"},
 ("Q05","3"): {"got":"低","note":"仮説の上限に加え、規則にない上限（再現がない）で低にした"},
 ("Q06","1"): {"got":"中","reason_ok":"部分","note":"「一般化には上限」と書いたが、評価の言葉への当てはめとは書いていない","raise_fit":"いいえ"},
 ("Q06","2"): {"got":"中","reason_ok":"いいえ","note":"理由は実行の回数とページの数","raise_fit":"いいえ"},
 ("Q06","3"): {"got":"中","reason_ok":"いいえ","note":"「決まった手順で導いた」と書き、規則にない上限 3 つで中にした","raise_fit":"いいえ"},
 ("Q07","1"): {"got":"高"}, ("Q07","2"): {"got":"高"}, ("Q07","3"): {"got":"高"},
 ("Q08","1"): {"got":"中","note":"log.md の日付を git の履歴で確かめていないことを上限にした"},
 ("Q08","2"): {"got":"高"},
 ("Q08","3"): {"got":"中","note":"wiki 自身の事柄を、ソースの要約ページや raw で確かめていないとして中にした"},
 ("Q09","1"): {"got":"なし"}, ("Q09","2"): {"got":"なし"},
 ("Q09","3"): {"got":"なし","note":"取り込む候補として外部の記事の名前を挙げた（答えは添えていない）"},
 ("Q10","1"): {"got":"中","reason_ok":"いいえ","note":"理由は raw 未確認と、1 つの PDF と 1 つの版。原因がソースの要約ページにないことは挙げていない","raise_fit":"はい"},
 ("Q10","2"): {"got":"中","reason_ok":"いいえ","note":"同上","raise_fit":"はい"},
 ("Q10","3"): {"got":"中","reason_ok":"いいえ","note":"原因の根拠をソースの要約ページと誤って書いた","raise_fit":"いいえ"},
 ("Q11","1"): {"got":"中","note":"規則にない上限（原本未確認）で中にした","external":"検索語に Rust を使ったと書いた"},
 ("Q11","2"): {"got":"中","note":"同上","external":"検索語に Rust を使ったと書いた"},
 ("Q11","3"): {"got":"中","note":"同上","external":"検索語に Rust を使ったと書き、取り込む候補に astral-sh/uv を挙げた"},
}

qs = {q["id"]: q for q in json.loads((OUT.parent / "questions.json").read_text(encoding="utf-8"))}
rows = []
for meta in sorted((SCRATCH / "runs").glob("Q*.meta.json")):
    m = json.loads(meta.read_text(encoding="utf-8"))
    s = summarize(meta.with_name(meta.name.replace(".meta.json", ".jsonl")))
    j = J[(m["qid"], m["rep"])]
    rows.append({
        "qid": m["qid"], "rep": int(m["rep"]), "trial": m["rep"] == "0",
        "expect": qs[m["qid"]]["expect"], **j,
        "model": s.get("model"), "seconds": m["seconds"], "cost_usd": round(s.get("cost") or 0, 4),
        "turns": s.get("turns"), "opened_step_5b": s["opened_workflow"],
        "tools": [{"name": t["name"], "input": short(t["input"], 220), "error": bool(t.get("is_error"))} for t in s["tools"]],
        "permission_denials": s.get("denials"), "wiki_changed": bool(m["wiki_status"]),
        "answer": s.get("result"),
    })
OUT.write_bytes((json.dumps(rows, ensure_ascii=False, indent=1) + "\n").encode("utf-8"))
print(len(rows), "rows", sum(r["cost_usd"] for r in rows))
