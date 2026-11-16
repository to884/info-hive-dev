# 1 問を 1 回だけ claude -p で流し、stream-json と wiki の変更の有無を残す
# 前回の測定（wiki-query-confidence-sonnet-2026-11-16/scripts/run_one.py）を写し、次を変えた
# - 作業ディレクトリを試験用の wiki の置き場所（QC_WIKI_BASE）にした
# - 問いの条件（ready、broken、preparing）ごとに、MCP のデータの置き場所を分けた
# - wiki の変更の有無を、git status ではなく実行の前後のハッシュで見る
import json
import subprocess
import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from paths import QUESTIONS, RUNS as OUT, child_env, plugin_dir, wiki_base, wiki_digest  # noqa: E402

ALLOWED = [
    "Read", "Glob", "Grep", "Skill",
    "mcp__plugin_wiki_wiki__query", "mcp__plugin_wiki_wiki__get_page",
    "mcp__plugin_wiki_wiki__list_index", "mcp__plugin_wiki_wiki__graph",
    "mcp__plugin_wiki_wiki__stats", "mcp__plugin_wiki_wiki__lint",
    "mcp__plugin_wiki_wiki__index_chunks",
    "Bash(python *)", "Bash(uv run *)",
]


def main() -> int:
    qid, rep = sys.argv[1], sys.argv[2]
    qs = {q["id"]: q for q in json.loads(QUESTIONS.read_text(encoding="utf-8"))}
    q = qs[qid]
    plugin = plugin_dir()
    condition = q.get("condition", "ready")
    OUT.mkdir(parents=True, exist_ok=True)
    log = OUT / f"{qid}-r{rep}.jsonl"
    cmd = [
        "claude", "-p", f"/wiki:query {q['q']}",
        "--model", "claude-sonnet-5-5",
        "--output-format", "stream-json", "--verbose",
        "--plugin-dir", str(plugin),
        "--permission-mode", "default",
        "--allowedTools", *ALLOWED,
        "--disallowedTools", "Edit", "Write", "NotebookEdit",
        "--max-budget-usd", "0.8",
    ]
    before = wiki_digest()
    t0 = time.time()
    with log.open("wb") as f:
        p = subprocess.run(cmd, cwd=wiki_base(), stdout=f, stderr=subprocess.PIPE,
                           stdin=subprocess.DEVNULL, env=child_env(condition), timeout=1200)
    dt = time.time() - t0
    after = wiki_digest()
    meta = {"qid": qid, "rep": rep, "condition": condition, "rc": p.returncode, "seconds": round(dt, 1),
            "stderr": p.stderr.decode("utf-8", "replace")[-2000:],
            "wiki_changed": before != after, "digest_before": before, "digest_after": after}
    (OUT / f"{qid}-r{rep}.meta.json").write_bytes(
        json.dumps(meta, ensure_ascii=False, indent=1).encode("utf-8"))
    print(json.dumps({k: meta[k] for k in ("qid", "rep", "condition", "rc", "seconds", "wiki_changed")},
                     ensure_ascii=False), flush=True)
    if before != after:
        print("wiki が変わった。次の回の前に build_fixture.py --force で作り直す", flush=True)
        return 3
    return 0


if __name__ == "__main__":
    sys.exit(main())
