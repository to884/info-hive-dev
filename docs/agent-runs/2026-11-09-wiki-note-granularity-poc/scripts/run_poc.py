"""wiki の記事の単位の PoC を走らせる。3 資料 × 2 方式 × 2 モデル × 3 回 = 36 件。

各実行は、固定のスナップショットを作業ディレクトリにし、読むだけの権限で「配置の計画」を JSON で出させる。
結果は runs/<run_id>.json に 1 件ずつ書く。結果がある実行は飛ばすので、途中から再開できる。

CLI の呼び出し（child_env、_run、call_claude、call_codex など）は、
~/.claude/skills/multi-agent-dispatch/scripts/dispatch.py（sha256 94de5b80…）から写して手直しした。
手直しは、Claude の権限を読むだけにしたこと（dontAsk、MCP なし、書き込みのツールを禁止）と、
Codex に --skip-git-repo-check を足したこと、ツール呼び出しを監査のために集めることである。

使い方:
    python run_poc.py --snapshot-root <dir> [--only R-hybrid-opus-1,...] [--parallel 3] [--dry-run]
"""
from __future__ import annotations

import argparse
import hashlib
import json
import os
import re
import shutil
import subprocess
import threading
import time
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime
from pathlib import Path

HERE = Path(__file__).resolve().parent
RUN_DIR = HERE.parent
MANIFEST = RUN_DIR / "snapshots" / "manifest.json"
# 生の記録（原本の引用と CLI の出力を含む）は、公開リポジトリの外に置く。
PRIVATE = Path(os.environ.get("POC_PRIVATE_DIR") or Path.home() / "info-hive-dev-private" / RUN_DIR.name)

MODELS = {
    "opus": {"vendor": "claude", "model": "claude-opus-5-5", "label": "Claude Opus 5.5"},
    "sol": {"vendor": "codex", "model": "gpt-6.1-sol", "label": "GPT-6.1 Sol"},
}
METHODS = ("current", "hybrid")
SOURCES = ("O", "R", "V")
REPS = (1, 2, 3)
EFFORT = "high"
TIMEOUT_S = 2400

# ツールは使わせない。wiki のファイルと原本は依頼文に埋め込む（README の「設計の変更」）。
CLAUDE_DISALLOWED = ["Read", "Glob", "Grep", "Write", "Edit", "MultiEdit", "NotebookEdit", "Bash", "PowerShell",
                     "WebFetch", "WebSearch", "Skill", "Agent", "Task"]

METHOD_CURRENT = """\
現行の取り込みの手順に従う。`_rules/ingest-workflow.md` の手順 4〜7 と `_rules/page-conventions.md` を、書かれているとおりに適用する。手順 5〜7 でページを書く代わりに、どの知見をどのページに書くかを計画として出す。

- 手順 5 の source の要約にだけ書く知見は `source_only` とする。
- 手順 6 で既存のページに書き加える知見は `update` とし、書き加えるページを示す。
- 手順 7 で新しいエンティティやコンセプトのページを作るなら `create` とし、作るページを示す。独立したページにする価値があるかは、手順 7 の目安で判断する。
"""


def method_hybrid() -> str:
    proc = (RUN_DIR / "procedure-hybrid.md").read_text(encoding="utf-8")
    # 手順書の見出しを 1 段下げ、依頼文の「## 配置の方式」の下に収める
    proc = re.sub(r"^(#+) ", lambda m: "#" * (len(m.group(1)) + 1) + " ", proc, flags=re.M)
    head = ("併用案の手順に従う。`_rules/ingest-workflow.md` の手順 4〜7 のうち、知見をどのページに置くかの判断は、"
            "下の手順書で置き換える。手順書が `_rules/ingest-workflow.md` と食い違うときは、手順書を優先する。"
            "`page_kind` は、昇格させた主張のページなら `\"claim\"` にする。用語ページの `###` の節に置く知見は、"
            "`page_slug` を用語ページのスラッグ、`section` を `### <節の見出し>` にする。\n\n")
    # 手順書の冒頭（題名と出典の説明）は依頼文には要らないので、最初の「### 1.」から使う
    idx = proc.find("### 1.")
    return head + (proc[idx:] if idx >= 0 else proc)


# ---------------------------------------------------------------------------
# CLI の呼び出し（dispatch.py から写した）
# ---------------------------------------------------------------------------

class CallResult:
    def __init__(self) -> None:
        self.ok = False
        self.text = ""
        self.session_id: str | None = None
        self.error = ""
        self.stdout = ""
        self.stderr = ""
        self.usage: dict = {}
        self.returncode: int | None = None
        self.tool_calls: list[dict] = []


def child_env() -> dict:
    env = dict(os.environ)
    keep = {"CLAUDE_CODE_GIT_BASH_PATH", "CLAUDE_CONFIG_DIR"}
    for k in list(env):
        if k.startswith("CLAUDE") and k not in keep:
            env.pop(k)
    env.setdefault("PYTHONIOENCODING", "utf-8")
    return env


def find_exe(name: str, env_key: str) -> str:
    p = os.environ.get(env_key) or shutil.which(name)
    if p:
        return p
    if name == "claude":
        for cand in (Path.home() / ".local" / "bin" / "claude.exe", Path.home() / ".local" / "bin" / "claude"):
            if cand.exists():
                return str(cand)
    raise SystemExit(f"{name} の CLI が見つかりません。環境変数 {env_key} で指定してください。")


def _kill_tree(pid: int) -> None:
    if os.name == "nt":
        subprocess.run(["taskkill", "/PID", str(pid), "/T", "/F"], capture_output=True)
    else:
        subprocess.run(["kill", "-9", str(pid)], capture_output=True)


def _reap_children(pid: int) -> None:
    if os.name != "nt":
        return
    query = (f"Get-CimInstance Win32_Process -Filter 'ParentProcessId={pid}' | "
             "ForEach-Object { Stop-Process -Id $_.ProcessId -Force -ErrorAction SilentlyContinue }")
    subprocess.run(["powershell", "-NoProfile", "-Command", query], capture_output=True)


def _run(cmd: list[str], prompt: str, cwd: Path, timeout: int) -> tuple[int | None, str, str]:
    proc = subprocess.Popen(cmd, stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.PIPE,
                            text=True, encoding="utf-8", errors="replace", cwd=str(cwd), env=child_env())
    out_lines: list[str] = []
    err_lines: list[str] = []

    def pump(stream, sink):
        for line in iter(stream.readline, ""):
            sink.append(line)

    readers = [threading.Thread(target=pump, args=(proc.stdout, out_lines), daemon=True),
               threading.Thread(target=pump, args=(proc.stderr, err_lines), daemon=True)]
    for t in readers:
        t.start()
    try:
        proc.stdin.write(prompt)
        proc.stdin.close()
    except (BrokenPipeError, OSError):
        pass
    try:
        rc: int | None = proc.wait(timeout=timeout)
    except subprocess.TimeoutExpired:
        _kill_tree(proc.pid)
        rc = None
    _reap_children(proc.pid)
    for t in readers:
        t.join(timeout=10)
    return rc, "".join(out_lines), "".join(err_lines)


def call_claude(model: str, prompt: str, cwd: Path) -> CallResult:
    r = CallResult()
    cmd = [find_exe("claude", "DISPATCH_CLAUDE"), "-p", "--output-format", "stream-json", "--verbose",
           "--model", model, "--effort", EFFORT, "--permission-mode", "dontAsk",
           "--strict-mcp-config", "--disallowedTools", *CLAUDE_DISALLOWED]
    r.returncode, r.stdout, r.stderr = _run(cmd, prompt, cwd, TIMEOUT_S)
    if r.returncode is None:
        r.error = "timeout"
        return r
    final = None
    texts: list[str] = []
    for line in r.stdout.splitlines():
        line = line.strip()
        if not line.startswith("{"):
            continue
        try:
            ev = json.loads(line)
        except json.JSONDecodeError:
            continue
        if ev.get("type") == "assistant":
            for block in ev.get("message", {}).get("content") or []:
                if block.get("type") == "tool_use":
                    r.tool_calls.append({"tool": block.get("name"), "input": block.get("input")})
                    texts.clear()
                elif block.get("type") == "text" and block.get("text"):
                    texts.append(block["text"])
        elif ev.get("type") == "result":
            final = ev
    if final is None:
        r.error = f"JSON を読めません（returncode={r.returncode}）: {r.stderr[:200]}"
        return r
    r.session_id = final.get("session_id")
    r.usage = {"total_cost_usd": final.get("total_cost_usd"), "usage": final.get("usage"),
               "num_turns": final.get("num_turns"), "duration_ms": final.get("duration_ms")}
    joined = "".join(texts).strip()
    fallback = (final.get("result") or "").strip()
    r.text = joined if len(joined) >= len(fallback) else fallback
    if final.get("is_error") or not r.text:
        r.error = f"claude が失敗しました: {r.text[:300]}"
        return r
    r.ok = True
    return r


def call_codex(model: str, prompt: str, cwd: Path) -> CallResult:
    r = CallResult()
    cmd = [find_exe("codex", "DISPATCH_CODEX"), "exec", "-c", f'model_reasoning_effort="{EFFORT}"',
           "-c", 'approval_policy="never"', "--json", "--skip-git-repo-check",
           "-m", model, "-s", "read-only", "-C", str(cwd), "-"]
    r.returncode, r.stdout, r.stderr = _run(cmd, prompt, cwd, TIMEOUT_S)
    if r.returncode is None:
        r.error = "timeout"
        return r
    msgs: list[str] = []
    last_msg = ""
    errors: list[str] = []
    for line in r.stdout.splitlines():
        line = line.strip()
        if not line.startswith("{"):
            continue
        try:
            ev = json.loads(line)
        except json.JSONDecodeError:
            continue
        t = ev.get("type")
        if t == "thread.started":
            r.session_id = ev.get("thread_id")
        elif t == "item.completed":
            item = ev.get("item") or {}
            itype = item.get("type")
            if itype == "agent_message":
                if item.get("text"):
                    msgs.append(item["text"])
                    last_msg = item["text"]
            elif itype == "error":
                errors.append(item.get("message") or "")
                msgs.clear()
            elif itype != "reasoning":
                r.tool_calls.append({"tool": itype, "input": {k: v for k, v in item.items()
                                                              if k in ("command", "path", "changes", "query")}})
                msgs.clear()
        elif t == "turn.completed":
            r.usage = ev.get("usage") or {}
        elif t == "turn.failed":
            errors.append(json.dumps(ev.get("error"), ensure_ascii=False))
    joined = "".join(msgs).strip()
    r.text = joined if joined else last_msg
    if not last_msg.strip():
        r.error = "codex の最終メッセージが空です: " + (" / ".join(errors) or r.stderr[:200])[:300]
        return r
    r.ok = True
    return r


# ---------------------------------------------------------------------------
# 計画の読み取りと監査
# ---------------------------------------------------------------------------

def parse_plan(text: str) -> tuple[dict | None, str]:
    blocks = re.findall(r"```json\s*(.*?)```", text, flags=re.S)
    cands = blocks[::-1] if blocks else [text]
    last_err = "JSON のコードブロックがありません"
    for b in cands:
        try:
            return json.loads(b), ""
        except json.JSONDecodeError as e:
            last_err = f"JSON を読めません: {e}"
    return None, last_err


ABS_PATH = re.compile(r"(?:[A-Za-z]:[\\/]|/[a-z]/|~[\\/]|\$HOME|\$env:USERPROFILE|%USERPROFILE%)[^\s\"'`|;,)]*")


def audit_paths(tool_calls: list[dict], snapshot: Path) -> list[str]:
    """スナップショットの外を指すパスを集める。読んだかどうかまでは判定しない（人が確かめる）。"""
    snap = str(snapshot).replace("\\", "/").lower()
    alt = "/" + snap[0] + snap[2:] if re.match(r"[a-z]:", snap) else snap  # /d/Users/... の形
    hits = []
    for call in tool_calls:
        blob = json.dumps(call.get("input"), ensure_ascii=False).replace("\\\\", "/").replace("\\", "/")
        for m in ABS_PATH.findall(blob):
            p = m.lower()
            if p.startswith(snap) or p.startswith(alt):
                continue
            hits.append(f"{call.get('tool')}: {m}")
        if re.search(r"info-hive[/\\]W0_Wiki|semasynth-dev", blob, flags=re.I) and snap not in blob.lower():
            hits.append(f"{call.get('tool')}: 実際の wiki の名前を含む: {blob[:160]}")
    return sorted(set(hits))


# ---------------------------------------------------------------------------
# 実行
# ---------------------------------------------------------------------------

def build_prompt(manifest: dict, source: str, method: str) -> str:
    tmpl = (RUN_DIR / "prompt-template.md").read_text(encoding="utf-8")
    src = manifest["sources"][source]
    wiki_dir = "W0_Wiki" if src["snapshot"] == "w0" else "wiki"
    vals = {
        "{WIKI_DIR}": wiki_dir, "{RAW_PATH}": src["raw_rel"], "{RAW_LINES}": str(src["raw_lines"]),
        "{SOURCE_TITLE}": src["title"], "{SOURCE_SLUG}": src["slug"], "{SOURCE_ID}": source,
        "{METHOD_SECTION}": METHOD_CURRENT if method == "current" else method_hybrid(),
    }
    for k, v in vals.items():
        tmpl = tmpl.replace(k, v)
    return tmpl


def embed_files(manifest: dict, snapshot_root: Path, source: str) -> str:
    """スナップショットの Markdown をすべて、パスの順に埋め込む。原本には行番号を付ける。"""
    src = manifest["sources"][source]
    root = snapshot_root / src["snapshot"]
    raw_rel = src["raw_rel"]
    parts = ["", "---", "", "## wiki のファイル", "",
             "以下は、この作業の wiki と規約の全文である。`=== FILE: <パス> ===` から `=== END FILE ===` までが"
             " 1 つのファイルである。", ""]
    files = sorted((p for p in root.rglob("*.md") if p.is_file()), key=lambda x: x.relative_to(root).as_posix())
    for f in files:
        rel = f.relative_to(root).as_posix()
        if rel == raw_rel:
            continue
        parts += [f"=== FILE: {rel} ===", f.read_text(encoding="utf-8").rstrip("\n"), "=== END FILE ===", ""]
    raw_lines = (root / raw_rel).read_text(encoding="utf-8").splitlines()
    parts += ["## 取り込む原本", "", f"`{raw_rel}` の全文。各行の先頭の `L<番号>| ` は行番号である。", "",
              f"=== RAW: {raw_rel} ==="]
    parts += [f"L{i}| {line}" for i, line in enumerate(raw_lines, 1)]
    parts += ["=== END RAW ===", ""]
    return "\n".join(parts)


def all_runs() -> list[dict]:
    runs = []
    for rep in REPS:
        for source in SOURCES:
            for method in METHODS:
                for mkey in MODELS:
                    runs.append({"run_id": f"{source}-{method}-{mkey}-{rep}", "source": source,
                                 "method": method, "model_key": mkey, "rep": rep})
    return runs


def execute(run: dict, manifest: dict, snapshot_root: Path, prompts: dict, lock: threading.Lock) -> None:
    out = PRIVATE / "runs" / f"{run['run_id']}.json"
    m = MODELS[run["model_key"]]
    src = manifest["sources"][run["source"]]
    cwd = snapshot_root / src["snapshot"]
    prompt = prompts[(run["source"], run["method"])]
    started = datetime.now().astimezone()
    t0 = time.monotonic()
    with lock:
        print(f"[{started:%H:%M:%S}] start {run['run_id']}", flush=True)
    res = call_claude(m["model"], prompt, cwd) if m["vendor"] == "claude" else call_codex(m["model"], prompt, cwd)
    elapsed = time.monotonic() - t0
    plan, perr = parse_plan(res.text) if res.ok else (None, res.error)
    logs = PRIVATE / "logs"
    logs.mkdir(parents=True, exist_ok=True)
    (logs / f"{run['run_id']}.stdout.jsonl").write_text(res.stdout, encoding="utf-8")
    (logs / f"{run['run_id']}.stderr.txt").write_text(res.stderr, encoding="utf-8")
    record = {
        **run, "vendor": m["vendor"], "model": m["model"], "label": m["label"], "effort": EFFORT,
        "snapshot": src["snapshot"], "snapshot_tree_sha256": manifest["snapshots"][src["snapshot"]]["tree_sha256"],
        "prompt_file": f"prompts/{run['source']}-{run['method']}.md",
        "prompt_sha256": hashlib.sha256(prompt.encode("utf-8")).hexdigest(),
        "started": started.isoformat(timespec="seconds"), "elapsed_s": round(elapsed, 1),
        "ok": res.ok and plan is not None and bool(plan.get("candidates")) and not plan.get("error"),
        "error": res.error or perr or (str(plan.get("error") or "") if plan else "") or ("" if (plan or {}).get("candidates") else "候補が 0 件"), "returncode": res.returncode,
        "session_id": res.session_id, "usage": res.usage,
        "n_tool_calls": len(res.tool_calls),
        "files_read": sorted({str((c.get("input") or {}).get("file_path", "")) for c in res.tool_calls
                              if c.get("tool") == "Read"} - {""}),
        "tool_calls": res.tool_calls,
        "outside_snapshot": audit_paths(res.tool_calls, cwd),
        "final_text": res.text, "plan": plan,
    }
    out.write_text(json.dumps(record, ensure_ascii=False, indent=2) + "\n", encoding="utf-8", newline="\n")
    with lock:
        n = len((plan or {}).get("candidates") or [])
        print(f"[{datetime.now():%H:%M:%S}] done  {run['run_id']} ok={record['ok']} cands={n} "
              f"{elapsed:.0f}s outside={len(record['outside_snapshot'])} {record['error'][:120]}", flush=True)


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--snapshot-root", required=True, type=Path)
    ap.add_argument("--only", default="", help="run_id をカンマ区切りで")
    ap.add_argument("--parallel", type=int, default=3, help="ベンダーごとの同時実行数")
    ap.add_argument("--dry-run", action="store_true", help="依頼文だけを書く")
    ap.add_argument("--rerun", action="store_true", help="結果がある実行もやり直す")
    args = ap.parse_args()

    manifest = json.loads(MANIFEST.read_text(encoding="utf-8"))
    prompts = {}
    (RUN_DIR / "prompts").mkdir(exist_ok=True)
    for s in SOURCES:
        for meth in METHODS:
            p = build_prompt(manifest, s, meth)
            full = p + embed_files(manifest, args.snapshot_root, s)
            prompts[(s, meth)] = full
            digest = hashlib.sha256(full.encode("utf-8")).hexdigest()
            # リポジトリには埋め込む前の依頼文だけを置く。全文は作者の wiki と原本を含むので外に置く。
            (RUN_DIR / "prompts" / f"{s}-{meth}.md").write_text(
                p + f"\n---\n\n（ここに wiki のファイルと原本を埋め込んだ。全文の sha256 は `{digest}`、"
                f"{len(full):,} 文字。全文はリポジトリの外の `prompts/{s}-{meth}.md` にある）\n",
                encoding="utf-8", newline="\n")
            (PRIVATE / "prompts").mkdir(parents=True, exist_ok=True)
            (PRIVATE / "prompts" / f"{s}-{meth}.md").write_text(full, encoding="utf-8", newline="\n")
    if args.dry_run:
        print("依頼文を prompts/ に書いた")
        return
    (PRIVATE / "runs").mkdir(parents=True, exist_ok=True)
    runs = all_runs()
    if args.only:
        want = set(args.only.split(","))
        runs = [r for r in runs if r["run_id"] in want]
    if not args.rerun:
        def done(r):
            p = PRIVATE / "runs" / f"{r['run_id']}.json"
            return p.exists() and json.loads(p.read_text(encoding="utf-8")).get("ok")
        runs = [r for r in runs if not done(r)]
    print(f"実行する件数: {len(runs)}", flush=True)
    lock = threading.Lock()
    pools = {v: ThreadPoolExecutor(max_workers=args.parallel) for v in ("claude", "codex")}
    futs = [pools[MODELS[r["model_key"]]["vendor"]].submit(execute, r, manifest, args.snapshot_root, prompts, lock)
            for r in runs]
    for f in futs:
        f.result()
    for p in pools.values():
        p.shutdown()


if __name__ == "__main__":
    main()
