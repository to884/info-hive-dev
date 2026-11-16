# 1 問を 1 回だけ claude -p で流し、stream-json と wiki の変更の有無を残す
import json
import os
import subprocess
import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from paths import QUESTIONS, REPO, RUNS as OUT, plugin_dir  # noqa: E402

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
    env = dict(os.environ)
    for k in list(env):
        if k.startswith("CLAUDECODE") or k == "CLAUDE_CODE_ENTRYPOINT":
            env.pop(k)
    t0 = time.time()
    with log.open("wb") as f:
        p = subprocess.run(cmd, cwd=REPO, stdout=f, stderr=subprocess.PIPE,
                           stdin=subprocess.DEVNULL, env=env, timeout=1200)
    dt = time.time() - t0
    st = subprocess.run(["git", "status", "--porcelain", "wiki/"], cwd=REPO,
                        capture_output=True, encoding="utf-8").stdout
    meta = {"qid": qid, "rep": rep, "rc": p.returncode, "seconds": round(dt, 1),
            "stderr": p.stderr.decode("utf-8", "replace")[-2000:], "wiki_status": st}
    (OUT / f"{qid}-r{rep}.meta.json").write_bytes(
        json.dumps(meta, ensure_ascii=False, indent=1).encode("utf-8"))
    print(json.dumps(meta, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    sys.exit(main())
