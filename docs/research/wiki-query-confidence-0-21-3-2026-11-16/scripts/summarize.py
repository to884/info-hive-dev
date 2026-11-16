# stream-json の記録を要約する（モデル、道具の呼び出し、最終の回答、費用、確からしさの印）
# 前回の測定の summarize.py を写し、次を足した
# - 回答の終わりの決まった 1 行（**確からしさ（confidence）: X**）と、結論のそばの「（確からしさ: X）」を分けて数える
# - 回答の名前が「確からしさ」から「確信度」に変わったので、両方の字句を読む
# - query-confidence.md を開いたか、グラフに問い合わせたか、検索の mode・warning・index.state、CLI の検索の引数
import json
import re
import sys
from pathlib import Path

FINAL = re.compile(r"\*\*(?:確信度|確からしさ)（confidence）: (高|中|低)\*\*")
INLINE = re.compile(r"（(?:確信度|確からしさ)[:：]\s*(高|中|低)）")
ANY = re.compile(r"(?:確信度|確からしさ)[^\n]{0,20}?[:：]\s*\**\s*(高|中|低)")


def load(path: Path):
    rows = []
    for line in path.read_bytes().decode("utf-8", "replace").splitlines():
        line = line.strip()
        if line.startswith("{"):
            try:
                rows.append(json.loads(line))
            except json.JSONDecodeError:
                pass
    return rows


def short(v, n=160):
    s = json.dumps(v, ensure_ascii=False) if not isinstance(v, str) else v
    return s if len(s) <= n else s[:n] + "…"


def summarize(path: Path) -> dict:
    rows = load(path)
    out = {"file": path.name, "tools": [], "denials": []}
    tool_ids = {}
    for r in rows:
        t = r.get("type")
        if t == "system" and r.get("subtype") == "init":
            out["model"] = r.get("model")
            out["mcp"] = r.get("mcp_servers")
        elif t == "assistant":
            for c in r.get("message", {}).get("content", []):
                if c.get("type") == "tool_use":
                    tool_ids[c["id"]] = len(out["tools"])
                    out["tools"].append({"name": c["name"], "input": c.get("input")})
        elif t == "user":
            content = r.get("message", {}).get("content", [])
            if isinstance(content, list):
                for c in content:
                    if c.get("type") == "tool_result":
                        idx = tool_ids.get(c.get("tool_use_id"))
                        body = c.get("content")
                        if isinstance(body, list):
                            body = " ".join(x.get("text", "") for x in body if isinstance(x, dict))
                        if idx is not None:
                            out["tools"][idx]["is_error"] = bool(c.get("is_error"))
                            out["tools"][idx]["result"] = body or ""
        elif t == "result":
            out["result"] = r.get("result")
            out["cost"] = r.get("total_cost_usd")
            out["turns"] = r.get("num_turns")
            out["denials"] = r.get("permission_denials")
            out["subtype"] = r.get("subtype")
    text = out.get("result") or ""
    out["final_marks"] = FINAL.findall(text)
    out["inline_marks"] = INLINE.findall(text)
    out["any_marks"] = ANY.findall(text)
    dumps = [json.dumps(x.get("input"), ensure_ascii=False) for x in out["tools"]]
    out["opened_confidence"] = any("query-confidence.md" in d for d in dumps)
    out["opened_workflow"] = any("query-workflow.md" in d for d in dumps)
    searches = []
    for x in out["tools"]:
        name, inp, res = x["name"], x.get("input") or {}, x.get("result", "")
        if name.endswith("__query"):
            mo = re.search(r'"mode":\s*"(\w+)"', res)
            w = re.search(r'"warning":\s*(null|"[^"]*")', res)
            s = re.search(r'"state":\s*"(\w+)"', res)
            searches.append({"via": "mcp", "query": inp.get("query"), "mode": mo and mo.group(1),
                             "warning": w and w.group(1)[:40], "state": s and s.group(1)})
        elif name == "Bash" and "wiki_search.py" in str(inp.get("command", "")):
            cmd = str(inp.get("command", ""))
            mo = re.search(r'"mode":\s*"(\w+)"', res)
            searches.append({"via": "cli", "uv": cmd.lstrip().startswith("uv "),
                             "no_embed": "--no-embed" in cmd, "page": "--granularity page" in cmd,
                             "mode": mo and mo.group(1), "stderr_warn": "ローカルの埋め込み検索を使えない" in res})
    out["searches"] = searches
    out["graph_calls"] = [x.get("input") for x in out["tools"]
                          if x["name"].endswith("__graph") or "wiki_graph_query.py" in json.dumps(x.get("input"), ensure_ascii=False)]
    return out


# 0.21.3 の見つけ方の決め方（query-confidence.md の縮退の理由の表のあとの 1〜4）を、記録から機械で当てる。
# 探す道具: MCP の query、CLI の wiki_search.py の検索（--backlinks を除く）、Grep、Glob。
# wiki のページでの一致がない呼び出し（0 件、SCHEMA.md・index.md・log.md だけ）は数えない
NOT_PAGES = ("SCHEMA.md", "index.md", "log.md")
EMPTY = ("No files found", "No matches found", "Found 0")


PAGE_DIRS = ("sources", "entities", "concepts", "synthesis")


def _page_hits(text: str) -> set:
    """結果の文字列から、インデックスに載るページ（sources、entities、concepts、synthesis の下）のスラッグを拾う。
    パスを出さない形の結果（MCP の検索の "path" など）も、ページの置き場所の名前で見分ける"""
    names = set(re.findall(r"(?:%s)[\\/]+([^\\/\s\"'`:|]+)\.md" % "|".join(PAGE_DIRS), text or ""))
    return {n for n in names if n + ".md" not in NOT_PAGES}


def _kind(x: dict):
    """探す道具なら (種類, 正常な hybrid か, 一致したページ) を返す。そうでなければ None"""
    name, inp, res = x["name"], x.get("input") or {}, x.get("result", "") or ""
    if name.endswith("__query"):
        mo = re.search(r'"mode":\s*"(\w+)"', res)
        w = re.search(r'"warning":\s*(null|"[^"]*")', res)
        s = re.search(r'"state":\s*"(\w+)"', res)
        normal = bool(mo and mo.group(1) == "hybrid" and (not w or w.group(1) == "null") and not (s and s.group(1) == "embedding"))
        return ("mcp", normal, _page_hits(res))
    if name == "Bash" and "wiki_search.py" in str(inp.get("command", "")) and "--backlinks" not in str(inp.get("command", "")):
        cmd = str(inp.get("command", ""))
        mo = re.search(r'"mode":\s*"(\w+)"', res)
        normal = bool(mo and mo.group(1) == "hybrid") and "--no-embed" not in cmd and "--granularity page" not in cmd
        return ("cli", normal, _page_hits(res))
    if name in ("Grep", "Glob"):
        empty = any(res.strip().startswith(e) for e in EMPTY)
        hits = set() if empty else _page_hits(res)
        target = str(inp.get("path", ""))
        if not empty and not hits and res.strip() and target.endswith(".md") and not any(target.endswith(n) for n in NOT_PAGES):
            # 1 つのページを対象にした Grep が、パスを出さずに本文の行を返した
            hits = {Path(target).stem}
        return (name.lower(), False, hits)
    return None


def _opens(x: dict, page: str) -> bool:
    name, inp = x["name"], json.dumps(x.get("input"), ensure_ascii=False)
    if name in ("Read",) or name.endswith("__get_page"):
        return page in inp
    if name == "Bash" and "wiki_search.py" not in inp and "wiki_graph_query.py" not in inp:
        return page in inp and re.search(r"\b(cat|head|sed|type|Get-Content)\b", inp) is not None
    return False


def found_by(out: dict, pages: list) -> dict:
    """答えのページごとに、見つけ方の決め方の 1〜4 のどれに当たったかを返す"""
    res = {}
    for page in pages:
        pre, first = [], None
        for i, x in enumerate(out["tools"]):
            if _opens(x, page):
                first = i
                break
            k = _kind(x)
            if k and k[2]:
                pre.append({"i": i, "kind": k[0], "normal": k[1], "lists": page in k[2]})
        if first is None:
            res[page] = {"rule": "未読", "pre": pre}
            continue
        if not pre:
            rule = "1-index"
        elif any(p["normal"] and p["lists"] for p in pre):
            rule = "2-hybrid"
        elif any(p["kind"] in ("grep", "glob") for p in pre):
            rule = "3-reason0"
        elif any(not p["normal"] for p in pre):
            rule = "3-degraded"
        else:
            rule = "4-hybrid-only"
        # 開いたあとの、正常な hybrid での検索し直し（その場での検索し直し）
        resea = any((k := _kind(x)) and k[1] and page in k[2] for x in out["tools"][first + 1:])
        res[page] = {"rule": rule, "first_open": first, "pre": pre, "re_searched_hybrid": resea}
    return res


if __name__ == "__main__":
    for p in sys.argv[1:]:
        s = summarize(Path(p))
        print("=" * 80)
        print(s["file"], "model=", s.get("model"), "cost=", s.get("cost"), "turns=", s.get("turns"),
              "subtype=", s.get("subtype"))
        for x in s["tools"]:
            print(" -", x["name"], short(x["input"], 200), "ERR" if x.get("is_error") else "", "->",
                  short(x.get("result", ""), 200))
        print("denials=", short(s.get("denials"), 400))
        print("final=", s["final_marks"], "inline=", s["inline_marks"], "confidence_md=", s["opened_confidence"])
        print("searches=", s["searches"])
        print("graph=", s["graph_calls"])
        print("--- result ---")
        print(s.get("result"))
