#!/usr/bin/env python3
"""プロンプトのフック（ADR-0032）の段階 0 の測定。起動行の時間と終了コード、ページ数への伸びを測る。

使い方:
    python tests/wiki/bench_prompt_hook.py launch [--runs 30] [--out <json>]
    python tests/wiki/bench_prompt_hook.py scale [--runs 10] [--out <json>]

launch は、フックの起動行を 3 つの形（exec、Git Bash、PowerShell）で動かし、何もしない入口の時間と、
失敗の場面（uv がない、スクリプトがない、Python がない）の終了コードを記録する。
scale は、合成の wiki（80、150、300、1000 ページ）で、検索の各段の時間を測る。

結果は JSON で標準出力に書く（--out を付ければファイルにも書く）。手元の測定の道具なので CI では動かさない。
"""
from __future__ import annotations

import argparse
import json
import os
import shutil
import statistics
import subprocess
import sys
import tempfile
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
SCRIPTS = ROOT / "info-hive-wiki" / "skills" / "info-hive" / "scripts"

# 何もしない入口の代わり。依存を持たず、標準入力を読んで何も出さずに終わる。
STUB = """#!/usr/bin/env python3
# /// script
# requires-python = ">=3.12,<3.15"
# dependencies = []
# ///
import sys
sys.stdin.buffer.read()
"""

HOOK_INPUT = {
    "session_id": "bench-session",
    "transcript_path": "",
    "cwd": str(ROOT),
    "permission_mode": "default",
    "hook_event_name": "UserPromptSubmit",
    "prompt": "uv の UV_SYSTEM_CERTS の直しはどうなった？",
}

UV_FLAGS = ["--no-project", "--no-config", "--quiet", "--quiet", "--offline", "--no-python-downloads",
            "--python", ">=3.12,<3.15", "python", "-I", "-S"]


def percentile(values: list[float], q: float) -> float:
    ordered = sorted(values)
    if not ordered:
        return float("nan")
    k = (len(ordered) - 1) * q
    lo = int(k)
    hi = min(lo + 1, len(ordered) - 1)
    return ordered[lo] + (ordered[hi] - ordered[lo]) * (k - lo)


def summary(values: list[float]) -> dict:
    return {
        "n": len(values),
        "p50_ms": round(statistics.median(values) * 1000, 1) if values else None,
        "p95_ms": round(percentile(values, 0.95) * 1000, 1) if values else None,
        "max_ms": round(max(values) * 1000, 1) if values else None,
    }


def valid_candidate_output(stdout: bytes) -> bool:
    """合成 wiki の候補2件と、フックの出力の契約を確かめる。"""
    try:
        output = json.loads(stdout)["hookSpecificOutput"]
        text = output["additionalContext"]
        if output["hookEventName"] != "UserPromptSubmit" or not isinstance(text, str) or len(text) > 2000:
            return False
        identities = [json.loads(rest) for line in text.splitlines()
                      for number, separator, rest in [line.partition(". ")]
                      if separator and number.isdecimal()]
        return all({"slug": f"page-{i:04d}", "path": f"concepts/page-{i:04d}.md"}
                   in identities for i in (0, 1))
    except (ValueError, KeyError, TypeError):
        return False


def bash_path() -> str | None:
    found = shutil.which("bash")
    if os.name == "nt":
        git_bash = Path(r"C:\Program Files\Git\bin\bash.exe")
        if git_bash.is_file():
            return str(git_bash)
    return found


def pwsh_path() -> str | None:
    return shutil.which("pwsh") or shutil.which("powershell")


def shell_line(script: Path, uv: str = "uv") -> str:
    # hooks.json の command と同じ形。パスは Claude Code の置換と同じくスラッシュにする。
    command = json.loads((ROOT / "info-hive-wiki/hooks/hooks.json").read_text(encoding="utf-8"))["hooks"]["UserPromptSubmit"][0]["hooks"][0]["command"]
    return command.replace("uv ", uv + " ", 1).replace("${CLAUDE_PLUGIN_ROOT}/skills/info-hive/scripts/wiki_prompt_hook.py", script.as_posix())


def run_once(argv: list[str], payload: bytes, env: dict) -> tuple[float, int, bytes, bytes]:
    start = time.perf_counter()
    proc = subprocess.run(argv, input=payload, capture_output=True, env=env, timeout=120)
    return time.perf_counter() - start, proc.returncode, proc.stdout, proc.stderr


def forms(script: Path) -> dict[str, list[str]]:
    result = {"exec": ["uv", "run", *UV_FLAGS, str(script)]}
    bash = bash_path()
    if bash:
        result["git_bash"] = [bash, "-c", shell_line(script)]
    pwsh = pwsh_path()
    if pwsh:
        result["powershell"] = [pwsh, "-NoProfile", "-NonInteractive", "-Command", shell_line(script)]
    return result


def cmd_launch(args) -> dict:
    payload = json.dumps(HOOK_INPUT, ensure_ascii=False).encode("utf-8")
    env = dict(os.environ)
    out: dict = {"uv": subprocess.run(["uv", "--version"], capture_output=True, text=True).stdout.strip(),
                 "platform": sys.platform, "timing": {}, "failures": {}}
    with tempfile.TemporaryDirectory() as tmp:
        stub = Path(tmp) / "stub_hook.py"
        stub.write_bytes(STUB.encode("utf-8"))
        # 最初の 1 回は uv が Python を探すので、時間に数えない。
        for name, argv in forms(stub).items():
            run_once(argv, payload, env)
            times = []
            codes = set()
            for _ in range(args.runs):
                elapsed, code, _stdout, _stderr = run_once(argv, payload, env)
                times.append(elapsed)
                codes.add(code)
            out["timing"][name] = {**summary(times), "exit_codes": sorted(codes)}

        # (a2) 標準入力のバイト列が、形ごとに変わらずに子へ届くか。届いたものを別のファイルに写して比べる。
        echo = Path(tmp) / "echo_hook.py"
        echo.write_bytes((STUB.replace("sys.stdin.buffer.read()", "")
                          + "import os\nopen(os.environ['BENCH_ECHO_OUT'], 'wb').write(sys.stdin.buffer.read())\n"
                          ).encode("utf-8"))
        out["stdin"] = {}
        for name, argv in forms(echo).items():
            sink = Path(tmp) / f"echo-{name}.bin"
            echo_env = dict(env, BENCH_ECHO_OUT=str(sink))
            _elapsed, code, _stdout, stderr = run_once(argv, payload, echo_env)
            received = sink.read_bytes() if sink.is_file() else None
            out["stdin"][name] = {"exit_code": code, "same_bytes": received == payload,
                                  "received_bytes": None if received is None else len(received),
                                  "stderr_head": stderr.decode("utf-8", "replace")[:160]}

        missing = Path(tmp) / "missing_hook.py"
        no_uv_env = dict(env)
        no_uv_env["PATH"] = os.pathsep.join(
            p for p in env.get("PATH", "").split(os.pathsep)
            if p and not (Path(p) / ("uv.exe" if os.name == "nt" else "uv")).is_file()
        )
        no_python_env = dict(env)
        no_python_env.pop("VIRTUAL_ENV", None)
        no_python_env["UV_MANAGED_PYTHON"] = "1"
        no_python_env["UV_PYTHON_INSTALL_DIR"] = str(Path(tmp) / "no-python")
        scenarios = {
            "script_missing": (missing, env),
            "python_missing": (stub, no_python_env),
            "uv_missing": (stub, no_uv_env),
        }
        for scenario, (script, scenario_env) in scenarios.items():
            row = {}
            for name, argv in forms(script).items():
                try:
                    _elapsed, code, stdout, stderr = run_once(argv, payload, scenario_env)
                    row[name] = {"exit_code": code, "stdout_bytes": len(stdout),
                                 "stderr_head": stderr.decode("utf-8", "replace")[:160]}
                except FileNotFoundError as exc:
                    row[name] = {"exit_code": None, "error": f"FileNotFoundError: {exc.filename}"}
                except subprocess.TimeoutExpired:
                    row[name] = {"exit_code": None, "error": "timeout"}
            out["failures"][scenario] = row
    return out


def synthetic_wiki(root: Path, pages: int) -> None:
    """題、見出し、本文を持つ合成の wiki を作る。語彙は日本語と英数字を混ぜる。"""
    (root / "concepts").mkdir(parents=True)
    (root / "SCHEMA.md").write_bytes("# SCHEMA\n".encode("utf-8"))
    index_lines = ["# Wiki のインデックス", "", "## コンセプト", ""]
    words = ["検索", "索引", "埋め込み", "リリース", "フック", "設定", "試験", "文書", "移植", "版",
             "graph", "lint", "query", "ingest", "browse", "uv", "python", "windows"]
    for i in range(pages):
        a, b, c = words[i % len(words)], words[(i * 7) % len(words)], words[(i * 13) % len(words)]
        slug = f"page-{i:04d}"
        body = [
            "---", 'type: "concept"', f'title: "{a}と{b}の話 {i}"', "tags: []", "---", "",
            f"# {a}と{b}の話 {i}", "",
        ]
        for s in range(6):
            body.append(f"## {c}の節 {s}")
            body.append("")
            body.append(f"{a}を{b}で扱うときの決まり。{c} の手順は {i} 番目のページにある。" * 8)
            body.append("")
        (root / "concepts" / f"{slug}.md").write_bytes("\n".join(body).encode("utf-8"))
        index_lines.append(f"- [[{slug}]]: {a}と{b}の話 {i} の要約")
    (root / "index.md").write_bytes(("\n".join(index_lines) + "\n").encode("utf-8"))


def cmd_scale(args) -> dict:
    sys.path.insert(0, str(SCRIPTS))
    start = time.perf_counter()
    import wiki_search  # noqa: E402
    import_s = time.perf_counter() - start
    out = {"import_ms": round(import_s * 1000, 1), "sizes": {}}
    query = wiki_search.tokenize("フックの設定と索引の試験はどうなっている？")
    with tempfile.TemporaryDirectory() as tmp:
        for size in (80, 150, 300, 1000):
            root = Path(tmp) / f"wiki-{size}"
            synthetic_wiki(root, size)
            collect, build, rank = [], [], []
            for _ in range(args.runs):
                t0 = time.perf_counter()
                pages = wiki_search.collect_pages(root)
                t1 = time.perf_counter()
                rows = wiki_search.collect_sections(pages)
                idx = wiki_search.build_bm25(rows)
                t2 = time.perf_counter()
                wiki_search.lexical_ranking(query, idx)
                t3 = time.perf_counter()
                collect.append(t1 - t0)
                build.append(t2 - t1)
                rank.append(t3 - t2)
            total = [c + b + r for c, b, r in zip(collect, build, rank)]
            out["sizes"][str(size)] = {
                "collect_pages": summary(collect), "sections_bm25": summary(build),
                "ranking": summary(rank), "total": summary(total),
            }
    return out


def main() -> None:
    for stream in (sys.stdout, sys.stderr):
        stream.reconfigure(encoding="utf-8")
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    sub = parser.add_subparsers(dest="command", required=True)
    for name, runs in (("launch", 30), ("scale", 10)):
        p = sub.add_parser(name)
        p.add_argument("--runs", type=int, default=runs)
        p.add_argument("--out", type=Path)
    args = parser.parse_args()
    result = cmd_launch(args) if args.command == "launch" else cmd_scale(args)
    text = json.dumps(result, ensure_ascii=False, indent=2) + "\n"
    sys.stdout.write(text)
    if args.out:
        args.out.parent.mkdir(parents=True, exist_ok=True)
        args.out.write_bytes(text.encode("utf-8"))


if __name__ == "__main__":
    main()
