# stream-json の記録を要約する（モデル、道具の呼び出し、最終の回答、費用、確からしさの印）
# 前回の測定の summarize.py を写し、次を足した
# - 回答の終わりの決まった 1 行（**確からしさ（confidence）: X**）と、結論のそばの「（確からしさ: X）」を分けて数える
# - 回答の名前が「確からしさ」から「確信度」に変わった。決まった 1 行と結論の文末の印は、両方の名前を読む。
#   新しい名前はエッジの confidence にも使うので、字句だけでは回答の印と見分けられない。
#   そのため広い抽出（ANY）は前の名前だけを読み、新しい名前の崩れた書き方は回答を読んで判断する
# - query-confidence.md を開いたか、グラフに問い合わせたか、検索の mode・warning・index.state、CLI の検索の引数
import json
import re
import sys
from pathlib import Path

FINAL = re.compile(r"\*\*(?:確信度|確からしさ)（confidence）: (高|中|低)\*\*")
INLINE = re.compile(r"（(?:確信度|確からしさ)[:：]\s*(高|中|低)）")
ANY = re.compile(r"確からしさ[^\n]{0,20}?[:：]\s*\**\s*(高|中|低)")


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
