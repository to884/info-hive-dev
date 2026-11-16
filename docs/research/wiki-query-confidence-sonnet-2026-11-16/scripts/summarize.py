# stream-json の記録を要約する（モデル、MCP、道具の呼び出し、最終の回答、費用）
import json
import re
import sys
from pathlib import Path


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
    out = {"file": path.name, "tools": [], "results": [], "denials": []}
    tool_ids = {}
    for r in rows:
        t = r.get("type")
        if t == "system" and r.get("subtype") == "init":
            out["model"] = r.get("model")
            out["mcp"] = r.get("mcp_servers")
            out["plugins"] = r.get("plugins")
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
                            out["tools"][idx]["result_head"] = short(body or "", 300)
        elif t == "result":
            out["result"] = r.get("result")
            out["cost"] = r.get("total_cost_usd")
            out["turns"] = r.get("num_turns")
            out["duration_ms"] = r.get("duration_ms")
            out["denials"] = r.get("permission_denials")
            out["subtype"] = r.get("subtype")
    text = out.get("result") or ""
    # 回答の名前が「確からしさ」から「確信度」に変わったので、両方の字句を読む
    m = re.findall(r"(?:確信度|確からしさ)[^\n]{0,20}?[:：]\s*\**\s*(高|中|低)", text)
    out["confidence_marks"] = m
    out["opened_workflow"] = any(
        "query-workflow.md" in json.dumps(x.get("input"), ensure_ascii=False) for x in out["tools"])
    return out


if __name__ == "__main__":
    for p in sys.argv[1:]:
        s = summarize(Path(p))
        print("=" * 80)
        print(s["file"], "model=", s.get("model"), "cost=", s.get("cost"), "turns=", s.get("turns"),
              "subtype=", s.get("subtype"))
        print("mcp=", s.get("mcp"))
        print("plugins=", short(s.get("plugins"), 400))
        for x in s["tools"]:
            print(" -", x["name"], short(x["input"], 200), "ERR" if x.get("is_error") else "", "->", short(x.get("result_head", ""), 200))
        print("denials=", short(s.get("denials"), 400))
        print("marks=", s["confidence_marks"], "workflow=", s["opened_workflow"])
        print("--- result ---")
        print(s.get("result"))
