# 回答に wiki の外の語が出たかを数える
#
# 使い方: python check_search_terms.py <要約の JSON か、記録のディレクトリ> [...]
#   要約の JSON は runs-summary*.json（回答は result か answer の欄）。
#   記録のディレクトリは run_one.py が書いた Q*-r*.jsonl を読む（QC_RUNS_DIR の場所）。
#
# 判定は 2 段である。
# 1. 主の判定（漏れ）: questions.json の問いごとの leak（出てはならない外の語の正規表現）が、
#    回答のどこかに出たか。回答の文の形に頼らないので、引用符の有無や言い回しで数え漏れない。
#    leak のない問いは数えない。
# 2. 補助の走査（候補）: 検索や照合を述べた文と、その直後の箇条書きで引用された語のうち、
#    質問文にないもの。思わぬ漏れ（leak に書いていない語）を見つけるためのもので、
#    検索の縮退の理由（warning）の引用なども拾うので、人が読んで判断する。合否には使わない。
import io
import json
import re
import sys
import unicodedata
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from paths import QUESTIONS  # noqa: E402
from summarize import summarize  # noqa: E402

SEARCH_WORDS = re.compile(r"検索|探し|探す|探った|調べ|照合|全文|grep|ヒット|引いた|反応|一致")
QUOTED = re.compile(r"「([^」]+)」|『([^』]+)』|“([^”]+)”|\"([^\"]+)\"|`([^`]+)`")
# バッククォートで書かれることの多い、検索の語ではない名前
TOOL_NAMES = {"query", "get_page", "list_index", "graph", "lint", "stats", "index_chunks",
              "grep", "glob", "read", "bash", "mcp", "warning", "mode", "hybrid", "lexical"}
PATH_LIKE = re.compile(r"[/\\]|\.(md|py|json|jsonl|sqlite)\b|^--|^\$")
LIST_ITEM = re.compile(r"^\s*([-*・]|\d+[.)])\s")
SENTENCE = re.compile(r"[^。]+")


def norm(text: str) -> str:
    return unicodedata.normalize("NFKC", text).casefold()


def leaks(patterns: list[str], answer: str) -> list[str]:
    """主の判定。出てはならない語のうち、回答に出たものを返す"""
    text = unicodedata.normalize("NFKC", answer)
    found = []
    for p in patterns:
        m = re.search(p, text, re.IGNORECASE)
        if m:
            found.append(m.group(0))
    return found


def search_spans(answer: str) -> list[str]:
    """検索や照合を述べた文と、行の最後のその文に続く箇条書きの行を返す"""
    spans = []
    lines = answer.split("\n")
    for i, line in enumerate(lines):
        sents = SENTENCE.findall(line)
        for k, sent in enumerate(sents):
            if not SEARCH_WORDS.search(sent):
                continue
            spans.append(sent)
            # 「検索語は次のとおり」のあとの箇条書きも、検索の説明として読む
            if k == len(sents) - 1:
                j = i + 1
                while j < len(lines) and LIST_ITEM.match(lines[j]):
                    spans.append(lines[j])
                    j += 1
    return spans


def candidates(question: str, answer: str) -> list[str]:
    """補助の走査。検索の説明で引用された語のうち、質問文にないものを返す"""
    q = norm(question)
    found = []
    for span in search_spans(answer):
        for groups in QUOTED.findall(span):
            term = next(g for g in groups if g)
            if groups[-1] and (norm(term) in TOOL_NAMES or PATH_LIKE.search(term)):
                continue
            if norm(term) not in q and term not in found:
                found.append(term)
    return found


def load_runs(arg: str) -> list[dict]:
    path = Path(arg)
    if path.is_dir():
        rows = []
        for log in sorted(path.glob("Q*-r*.jsonl")):
            qid, rep = log.stem.split("-r")
            rows.append({"qid": qid, "rep": rep, "answer": summarize(log).get("result") or ""})
        return rows
    data = json.loads(path.read_text(encoding="utf-8"))
    return [{"qid": r["qid"], "rep": str(r["rep"]), "answer": r.get("result") or r.get("answer") or ""}
            for r in data]


def main() -> int:
    questions = {q["id"]: q for q in json.loads(QUESTIONS.read_text(encoding="utf-8"))}
    # Windows の端末は cp932 なので、標準出力を UTF-8 にする
    out = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")
    for arg in sys.argv[1:]:
        runs = load_runs(arg)
        judged = leaked = 0
        out.write(f"# {arg}\n")
        for r in runs:
            q = questions[r["qid"]]
            if q.get("leak"):
                judged += 1
                hit = leaks(q["leak"], r["answer"])
                if hit:
                    leaked += 1
                    out.write(f"漏れ {r['qid']}-{r['rep']}: {' / '.join(hit)}\n")
            cand = candidates(q["q"], r["answer"])
            if cand:
                out.write(f"候補 {r['qid']}-{r['rep']}: {' / '.join(cand)}\n")
        out.write(f"漏れた回: {leaked}/{judged}（leak のある問いの回）\n\n")
    out.flush()
    return 0


if __name__ == "__main__":
    sys.exit(main())
