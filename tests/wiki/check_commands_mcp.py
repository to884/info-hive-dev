"""コマンド（/wiki:stats、/wiki:query、/wiki:lint）が、まず wiki の MCP サーバーのツールを使うかを確かめる（ADR-0012 の段階 5）。

`claude -p --plugin-dir <info-hive-wiki>` でプラグインを読み込み、評価用の日本語の wiki をコピーした一時ディレクトリで
コマンドを実行する。stream-json の出力から、呼んだツールの名前と Bash のコマンドを取り出す。

1. プラグインのまま実行する: `mcp__plugin_wiki_wiki__*` を呼び、wiki の CLI（`wiki_stats.py` など）を呼ばないこと。
2. `.mcp.json` を除いたプラグインの写しで実行する: ツールがないので、CLI に戻って答えること。

`claude -p` をコマンドの数だけ実行するので、モデルの呼び出しがその回数分かかる。埋め込みはテスト用のもの
（INFO_HIVE_TEST_EMBEDDER=hash）にし、データの置き場所は一時ディレクトリにする。

    uv run --python 3.12 --with psutil==7.2.2 python -X utf8 tests/wiki/check_commands_mcp.py
"""
from __future__ import annotations

import json
import os
import platform
import re
import shlex
import shutil
import subprocess
import sys
import tempfile
import time
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
PLUGIN = ROOT / "info-hive-wiki"
CORPUS = PLUGIN / "eval/retrieval/ja/corpus/wiki"
OUT = ROOT / "docs/research/wiki-mcp-server-2026-11-06/commands-mcp.json"
TOOL_PREFIX = "mcp__plugin_wiki_wiki__"
CLI_NAMES = ("wiki_search.py", "wiki_lint.py", "wiki_stats.py", "wiki_graph_query.py", "wiki_graph_lint.py")
# wiki のパスは必ず明示する。コマンドは「明示したパス → プロジェクトの指示 → グローバルの指示 → ./wiki」の順に
# wiki を選ぶので、省くと、実行した人のグローバルの指示にある wiki が対象になる。{wiki} は実行時に埋める。
COMMANDS = [
    ("stats", "/wiki:stats {wiki}"),
    # ファイル名やページを開くだけでは答えがたどれない問い（評価セットの j05。答えは entities/yamanote-line.md）。
    ("query", "/wiki:query {wiki} の wiki で答えて。高輪ゲートウェイ駅は何線の駅？"),
    ("lint", "/wiki:lint {wiki}"),
]
ALLOWED = ",".join([f"{TOOL_PREFIX}{name}" for name in ("query", "get_page", "list_index", "lint", "stats", "graph")]
                   + ["Read", "Glob", "Grep", "Bash"])


def find_claude() -> str:
    claude = shutil.which("claude")
    if not claude:
        raise SystemExit("claude（Claude Code の CLI）が PATH にない")
    return claude


# wiki のパスを最初の位置引数で受け取る CLI。wiki_search.py は --wiki で受け取る。どれも省くと ./wiki を使う。
WIKI_POSITIONAL = {"wiki_lint.py", "wiki_stats.py", "wiki_graph_query.py", "wiki_graph_lint.py"}


def same_path(value: str, base: Path, wiki: Path) -> bool:
    """value（相対なら base から見たもの）が wiki と同じ場所を指すか。"""
    path = Path(value or ".")
    if not path.is_absolute():
        path = base / path
    try:
        return os.path.normcase(str(path.resolve())) == os.path.normcase(str(wiki.resolve()))
    except OSError:
        return False


def cli_targets(command: str, cwd: Path) -> list[tuple[Path, str]]:
    """Bash のコマンドから、wiki の CLI に渡した wiki のパスを、そのときの作業ディレクトリと組にして返す。"""
    base, found = cwd, []
    for part in re.split(r"&&|\|\||;", command):
        try:
            tokens = shlex.split(part.replace("\\", "/"))
        except ValueError:
            continue
        if not tokens:
            continue
        if tokens[0] == "cd" and len(tokens) > 1:
            target = Path(tokens[1])
            base = target if target.is_absolute() else base / target
            continue
        for i, token in enumerate(tokens):
            name = Path(token).name
            if name not in CLI_NAMES:
                continue
            rest = tokens[i + 1:]
            if "--wiki" in rest and rest.index("--wiki") + 1 < len(rest):
                found.append((base, rest[rest.index("--wiki") + 1]))
            elif name in WIKI_POSITIONAL and rest and not rest[0].startswith("-"):
                found.append((base, rest[0]))
            else:
                found.append((base, "wiki"))
    return found


def run_command(claude: str, plugin: Path, project: Path, prompt: str, env: dict, wiki: Path) -> dict:
    started = time.perf_counter()
    out = subprocess.run([claude, "-p", prompt, "--plugin-dir", str(plugin), "--allowedTools", ALLOWED,
                          "--output-format", "stream-json", "--verbose"],
                         cwd=project, capture_output=True, timeout=1800, env={**os.environ, "PYTHONUTF8": "1", **env})
    tools, bash, wiki_args, final, mcp_servers, result_ok = [], [], [], None, None, False
    for line in out.stdout.decode("utf-8", "replace").splitlines():
        try:
            event = json.loads(line)
        except ValueError:
            continue
        if event.get("type") == "system" and event.get("subtype") == "init":
            mcp_servers = event.get("mcp_servers")
        if event.get("type") == "assistant":
            for block in event.get("message", {}).get("content", []):
                if block.get("type") == "tool_use":
                    tools.append(block["name"])
                    arguments = block.get("input", {})
                    if block["name"] == "Bash":
                        bash.append(arguments.get("command", ""))
                    elif block["name"].startswith(TOOL_PREFIX):
                        wiki_args.append(arguments.get("wiki"))
        if event.get("type") == "result":
            final = event.get("result")
            result_ok = event.get("subtype") == "success" and not event.get("is_error")
    cli_commands = [c for c in bash if any(name in c for name in CLI_NAMES)]
    targets = [t for c in cli_commands for t in cli_targets(c, project)]
    return {"prompt": prompt, "returncode": out.returncode, "seconds": round(time.perf_counter() - started, 1),
            "mcp_servers": mcp_servers, "tools": tools, "bash": bash, "wiki_args": wiki_args,
            # claude -p が正常に終わり、最終の回答を返したか。
            "succeeded": out.returncode == 0 and result_ok and bool((final or "").strip()),
            "used_mcp": any(t.startswith(TOOL_PREFIX) for t in tools),
            "used_cli": bool(cli_commands),
            # 一時ディレクトリの wiki でない場所を、ツールか CLI に渡したか。相対パスは実行時の作業ディレクトリから解決する。
            "used_other_wiki": any(not same_path(str(w or ""), project, wiki) for w in wiki_args) or any(
                not same_path(value, base, wiki) for base, value in targets),
            "answer_head": (final or "")[:400],
            "stderr_tail": out.stderr.decode("utf-8", "replace")[-400:]}


def main() -> None:
    claude = find_claude()
    only = set(sys.argv[1:])  # 例: query。省くとすべてのコマンドと、MCP なしの確認を行う。
    report = {"purpose": "コマンドがまず wiki の MCP のツールを使い、ツールがないときは CLI に戻るか",
              "platform": platform.platform(),
              "claude_version": subprocess.run([claude, "--version"], capture_output=True, text=True,
                                               encoding="utf-8").stdout.strip(),
              "plugin_commit": subprocess.run(["git", "-C", str(PLUGIN), "describe", "--always", "--dirty"],
                                              capture_output=True, text=True).stdout.strip(),
              "with_mcp": [], "without_mcp": []}
    with tempfile.TemporaryDirectory(ignore_cleanup_errors=True) as temp:
        temp = Path(temp)
        project = temp / "project"
        shutil.copytree(CORPUS, project / "wiki")
        wiki = (project / "wiki").resolve()
        env = {"INFO_HIVE_DATA_DIR": str(temp / "data"), "INFO_HIVE_TEST_EMBEDDER": "hash",
               "INFO_HIVE_MCP_IDLE_SECONDS": "60"}
        for name, prompt in COMMANDS:
            if only and name not in only:
                continue
            result = run_command(claude, PLUGIN, project, prompt.format(wiki=wiki.as_posix()), env, wiki)
            report["with_mcp"].append({"command": name, **result})
            print(f"MCP あり {name}: tools={result['tools']} used_mcp={result['used_mcp']} "
                  f"used_cli={result['used_cli']}", flush=True)
        # .mcp.json を除いた写し。ツールがないので CLI に戻るはず。
        if only and "without_mcp" not in only:
            return finish(report, out=OUT.with_name(OUT.stem + "-" + "-".join(sorted(only)) + ".json"))
        bare = temp / "plugin-without-mcp"
        shutil.copytree(PLUGIN, bare, ignore=shutil.ignore_patterns(".git", ".mcp.json", "eval", "__pycache__"))
        result = run_command(claude, bare, project, COMMANDS[0][1].format(wiki=wiki.as_posix()), env, wiki)
        report["without_mcp"].append({"command": "stats", **result})
        print(f"MCP なし stats: tools={result['tools']} used_mcp={result['used_mcp']} used_cli={result['used_cli']}",
              flush=True)
    finish(report, OUT)


def finish(report: dict, out: Path) -> None:
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8", newline="\n")
    runs = report["with_mcp"] + report["without_mcp"]
    ok = all(r["used_mcp"] and not r["used_cli"] for r in report["with_mcp"]) and all(
        r["used_cli"] and not r["used_mcp"] for r in report["without_mcp"]) and all(
        r["succeeded"] and not r["used_other_wiki"] for r in runs)
    print("合格" if ok else "不合格", f"→ {out}")
    sys.exit(0 if ok else 1)


if __name__ == "__main__":
    main()
