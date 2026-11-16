# 条件ごとに wiki の MCP を直接呼び、検索の mode、warning、index.state を確かめる（モデルを使わないので費用はない）
# 使い方: uv run --with mcp==1.30.0 python probe_mcp.py <条件> <検索語> [回数]
import asyncio
import json
import sys
from pathlib import Path

from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client

sys.path.insert(0, str(Path(__file__).resolve().parent))
from paths import child_env, plugin_dir, wiki_root  # noqa: E402


async def main(condition: str, query: str, times: int) -> None:
    launch = plugin_dir() / "skills" / "info-hive" / "scripts" / "wiki_mcp_launch.py"
    params = StdioServerParameters(command="uv", args=["run", "--quiet", "--script", str(launch)],
                                   env=child_env(condition))
    async with stdio_client(params) as (r, w):
        async with ClientSession(r, w) as s:
            await s.initialize()
            for i in range(times):
                res = await s.call_tool("query", {"wiki": str(wiki_root()), "query": query, "top": 3})
                body = json.loads(res.content[0].text)
                hits = [(h.get("path") or h.get("rel_path"), h.get("heading")) for h in body.get("results", [])][:3]
                print(json.dumps({"condition": condition, "try": i + 1, "mode": body.get("mode"),
                                  "warning": body.get("warning"), "index": body.get("index"), "hits": hits},
                                 ensure_ascii=False))
                await asyncio.sleep(3)


if __name__ == "__main__":
    asyncio.run(main(sys.argv[1], sys.argv[2], int(sys.argv[3]) if len(sys.argv) > 3 else 1))
