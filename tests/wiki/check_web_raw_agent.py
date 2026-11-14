"""URL の取り込みで、raw の段をエージェント wiki:web-raw（Sonnet）が行い、後段をメインのモデルが行ったかを、
Claude Code のセッションの記録から確かめる。

設計: docs/plans/wiki-web-raw-agent-2026-11-14.md

    # 一時の wiki で /wiki:ingest を動かして確かめる（claude -p を 1 回動かすので、モデルの呼び出しの費用がかかる）
    python -X utf8 tests/wiki/check_web_raw_agent.py run <URL> --work <空のフォルダー> [--model opus] [--out <結果の JSON>]

    # 動かし終えたセッションを確かめ直す
    python -X utf8 tests/wiki/check_web_raw_agent.py analyze --session <セッションの ID> --project <取り込みを動かしたフォルダー>

確かめること（どれも記録の上の事実で、モデルの自己申告は使わない）:
- 誰が動いたか: エージェントの記録の応答のモデルが Sonnet で、メインの記録の応答のモデルが指定のモデルであること。
- メインが Agent ツールで wiki:web-raw を呼び、model の引数を渡していないこと。
- 誰が何をしたか: wiki_fetch.py の実行と、raw と画像への書き込みと、freeze が、エージェントの記録にだけあること。
  エージェントの記録に、wiki のページ、index.md、log.md への書き込みがないこと。メインの記録に、要約ページ、index.md、
  log.md への書き込みがあり、raw への書き込みがないこと。
- 文章の受け渡し: エージェントの応答（文と道具の入力）に、要約ページの本文の 40 文字以上の並びがないこと。エージェントを
  呼び終えるまでのメインの出力に、raw の本文の 40 文字以上の並びがないこと（プロンプトや報告で、文章を受け渡していない）。
  これは受け渡しの一部を見つけるだけで、どのモデルが文を考えたかを証明するものではない。
- 結果: raw の translated_by と補足の表示名、log の「raw:」のサブ行、作業用の写しが消えていること、要約ページがあること。
"""
from __future__ import annotations

import argparse
import glob
import json
import os
import re
import shutil
import subprocess
import sys
import time
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
PLUGIN = ROOT / "info-hive-wiki"
WINDOW = 40


def read_jsonl(path: Path) -> list[dict]:
    out = []
    for line in path.read_bytes().decode("utf-8").splitlines():
        line = line.strip()
        if line:
            try:
                out.append(json.loads(line))
            except json.JSONDecodeError:
                pass
    return out


def find_transcripts(session: str) -> tuple[Path, list[Path]]:
    """セッションの記録（メイン）と、エージェントの記録の一覧。"""
    base = Path(os.path.expanduser("~/.claude/projects"))
    mains = [Path(p) for p in glob.glob(str(base / "*" / f"{session}.jsonl"))]
    if not mains:
        raise FileNotFoundError(f"セッションの記録が見つからない: {session}")
    main = mains[0]
    subs = sorted(Path(p) for p in glob.glob(str(main.with_suffix("") / "subagents" / "*.jsonl")))
    return main, subs


def assistant_parts(records: list[dict]):
    """応答の部品（モデル、種類、中身）を順に返す。"""
    for rec in records:
        msg = rec.get("message") or {}
        if msg.get("role") != "assistant":
            continue
        for part in msg.get("content") or []:
            if isinstance(part, dict):
                yield msg.get("model", ""), part


def summarize(records: list[dict]) -> dict:
    models, tools, texts = set(), [], []
    for model, part in assistant_parts(records):
        if model and not model.startswith("<"):
            models.add(model)
        if part.get("type") == "text":
            texts.append(part.get("text", ""))
        elif part.get("type") == "tool_use":
            inp = part.get("input") or {}
            tools.append({"name": part.get("name"), "input": inp, "id": part.get("id")})
            texts.append(json.dumps(inp, ensure_ascii=False))
    return {"models": sorted(models), "tools": tools, "texts": texts}


def tool_paths(tools: list[dict]) -> list[str]:
    """書き込みの道具（Edit、Write、NotebookEdit）が書いたファイル。"""
    return [str(t["input"].get("file_path", "")).replace("\\", "/")
            for t in tools if t["name"] in ("Edit", "Write", "NotebookEdit", "MultiEdit")]


def bash_commands(tools: list[dict]) -> list[str]:
    return [str(t["input"].get("command", "")) for t in tools if t["name"] in ("Bash", "PowerShell")]


def under(path: str, root: Path) -> bool:
    p = path.replace("\\", "/").lower()
    r = str(root).replace("\\", "/").lower().rstrip("/") + "/"
    return p.startswith(r)


def body_of(text: str) -> str:
    if text.startswith("---\n"):
        end = text.find("\n---\n", 4)
        if end >= 0:
            return text[end + 5:]
    return text


def windows(text: str, size: int = WINDOW) -> set[str]:
    """文章の並び（空白をつぶした size 文字の窓）。記法の多い行やコードは除く。"""
    lines = [ln for ln in text.split("\n")
             if ln.strip() and not ln.lstrip().startswith(("```", "|", "#", "![", "> ", "---"))]
    flat = re.sub(r"\s+", " ", " ".join(lines))
    return {flat[i:i + size] for i in range(0, max(len(flat) - size + 1, 0), size // 2)}


def shares_text(source: str, generated: list[str], common: str = "") -> list[str]:
    """source の文の並びのうち、generated に現れるもの。common にもある並び（原文の言葉、raw から引いた文）は除く。"""
    hay = re.sub(r"\s+", " ", " ".join(generated))
    shared = re.sub(r"\s+", " ", common)
    return sorted(w for w in windows(source) if w in hay and w not in shared)[:5]


# raw の下に書き込む Bash のコマンド（リダイレクトの行き先か、書き換えるコマンドの引数が raw の下にある）。
RAW_WRITE_RE = re.compile(
    r"(?:>>?|\btee\b)\s*[\"']?[^\s;|&\"']*\braw[/\\]"
    r"|\b(?:sed\s+-i|Set-Content|Out-File|Add-Content|cp|mv|rm|Remove-Item|Copy-Item|Move-Item)\b[^\n;|&]*\braw[/\\]")


def analyze(session: str, project: Path, main_model: str) -> dict:
    main_path, sub_paths = find_transcripts(session)
    main = summarize(read_jsonl(main_path))
    subs = [summarize(read_jsonl(p)) for p in sub_paths]
    wiki, raw = project / "wiki", project / "raw"
    checks: list[dict] = []

    def check(name: str, ok: bool, detail=None):
        checks.append({"check": name, "ok": bool(ok), "detail": detail})

    agent_calls = [t for t in main["tools"] if t["name"] in ("Agent", "Task")]
    web_raw_calls = [t for t in agent_calls if t["input"].get("subagent_type") == "wiki:web-raw"]
    check("メインが wiki:web-raw を呼んだ", web_raw_calls, [t["input"].get("subagent_type") for t in agent_calls])
    check("メインが Agent に model を渡していない", all("model" not in t["input"] for t in web_raw_calls),
          [t["input"].get("model") for t in web_raw_calls])
    check(f"メインの応答のモデルが {main_model}", main["models"] and all(main_model in m for m in main["models"]),
          main["models"])
    agent_models = sorted({m for s in subs for m in s["models"]})
    check("エージェントの応答のモデルが Sonnet", agent_models and all("sonnet" in m for m in agent_models), agent_models)

    agent_tools = [t for s in subs for t in s["tools"]]
    agent_bash, main_bash = bash_commands(agent_tools), bash_commands(main["tools"])
    agent_writes, main_writes = tool_paths(agent_tools), tool_paths(main["tools"])
    check("wiki_fetch.py はエージェントだけが実行した",
          any("wiki_fetch.py" in c for c in agent_bash) and not any("wiki_fetch.py" in c for c in main_bash),
          {"main": [c for c in main_bash if "wiki_fetch.py" in c]})
    check("freeze はエージェントだけが実行した",
          any("wiki_rawcheck.py" in c and " freeze" in c for c in agent_bash)
          and not any("wiki_rawcheck.py" in c and " freeze" in c for c in main_bash))
    main_raw_bash = [c[:200] for c in main_bash if RAW_WRITE_RE.search(c)]
    check("メインは raw と画像に書いていない", not any(under(p, raw) for p in main_writes) and not main_raw_bash,
          {"paths": [p for p in main_writes if under(p, raw)], "bash": main_raw_bash})
    agent_wiki_writes = [p for p in agent_writes if under(p, wiki) and "/.wiki-cache/" not in p]
    check("エージェントは wiki のページ、index.md、log.md に書いていない", not agent_wiki_writes, agent_wiki_writes)
    check("メインが要約ページ、index.md、log.md を書いた",
          any(under(p, wiki / "sources") for p in main_writes)
          and any(p.lower().endswith("wiki/index.md") for p in main_writes)
          and any(p.lower().endswith("wiki/log.md") for p in main_writes),
          sorted(set(main_writes)))

    # 文章の受け渡し
    sources = sorted((wiki / "sources").glob("*.md"))
    summary = "\n".join(body_of(p.read_bytes().decode("utf-8")) for p in sources)
    agent_texts = [t for s in subs for t in s["texts"]]
    raws = sorted(raw.glob("*.md"))
    raw_text = "\n".join(body_of(p.read_bytes().decode("utf-8")) for p in raws)
    # 要約ページは raw から引用するので、raw にもある並びは受け渡しに数えない。
    check("エージェントの出力に、要約ページの文がない", not shares_text(summary, agent_texts, raw_text),
          shares_text(summary, agent_texts, raw_text))
    before: list[str] = []
    for t in main["tools"]:
        before.append(json.dumps(t["input"], ensure_ascii=False))
        if t in web_raw_calls:
            break
    check("エージェントを呼ぶまでのメインの出力に、raw の文がない", not shares_text(raw_text, before),
          shares_text(raw_text, before))

    # 結果
    fm = raws[0].read_bytes().decode("utf-8") if raws else ""
    translated_by = re.search(r'^translated_by: "(.*)"$', fm, re.M)
    captions = sorted(set(re.findall(r"^> ?(?:> )*(.{1,60}?) 補足: ", body_of(fm), re.M)))
    check("raw がある", raws, [str(p) for p in raws])
    log = (wiki / "log.md").read_bytes().decode("utf-8") if (wiki / "log.md").exists() else ""
    check("log に raw の段の分担のサブ行がある", re.search(r"raw:.*web-raw", log) is not None)
    check("作業用の写しが消えた", not any((wiki / ".wiki-cache" / "ingest").glob("*")) if (wiki / ".wiki-cache" / "ingest").exists() else True)
    return {"session": session, "project": str(project), "checks": checks,
            "ok": all(c["ok"] for c in checks),
            "translated_by": translated_by.group(1) if translated_by else None,
            "caption_names": captions,
            "main_models": main["models"], "agent_models": agent_models,
            "agent_transcripts": [str(p) for p in sub_paths]}


def run(url: str, work: Path, model: str, timeout: int) -> tuple[str, dict]:
    if work.exists() and any(work.iterdir()):
        raise SystemExit(f"--work は空のフォルダーにする: {work}")
    work.mkdir(parents=True, exist_ok=True)
    init = PLUGIN / "skills/info-hive/scripts/init_wiki.py"
    subprocess.run([sys.executable, str(init), str(work)], check=True, capture_output=True)
    claude = shutil.which("claude")
    if not claude:
        raise SystemExit("claude が見つからない")
    prompt = f"/wiki:ingest {url} 人と話し合わないまとめての取り込みとして行う。グラフ層の手順は飛ばす。"
    started = time.time()
    proc = subprocess.run([claude, "-p", prompt, "--plugin-dir", str(PLUGIN), "--model", model,
                           "--allowedTools", "Bash Read Edit Write Glob Grep Agent", "--output-format", "json"],
                          cwd=work, capture_output=True, timeout=timeout)
    out = json.loads(proc.stdout.decode("utf-8"))
    out["_seconds"] = round(time.time() - started)
    return out["session_id"], out


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = parser.add_subparsers(dest="command", required=True)
    p_run = sub.add_parser("run")
    p_run.add_argument("url")
    p_run.add_argument("--work", type=Path, required=True)
    p_run.add_argument("--model", default="opus")
    p_run.add_argument("--timeout", type=int, default=1500)
    p_run.add_argument("--out", type=Path)
    p_an = sub.add_parser("analyze")
    p_an.add_argument("--session", required=True)
    p_an.add_argument("--project", type=Path, required=True)
    p_an.add_argument("--model", default="opus")
    p_an.add_argument("--result", type=Path, help="claude -p の --output-format json の出力（時間と費用を添える）")
    p_an.add_argument("--out", type=Path)
    args = parser.parse_args()
    if args.command == "run":
        session, result = run(args.url, args.work, args.model, args.timeout)
        report = analyze(session, args.work, args.model)
    else:
        result = json.loads(args.result.read_bytes().decode("utf-8")) if args.result else {}
        report = analyze(args.session, args.project, args.model)
    report["usage"] = {"seconds": result.get("_seconds"), "duration_ms": result.get("duration_ms"),
                       "total_cost_usd": result.get("total_cost_usd"), "modelUsage": result.get("modelUsage")}
    text = json.dumps(report, ensure_ascii=False, indent=2)
    if args.out:
        args.out.write_bytes((text + "\n").encode("utf-8"))
    print(text)
    return 0 if report["ok"] else 1


if __name__ == "__main__":
    for _stream in (sys.stdout, sys.stderr):
        if hasattr(_stream, "reconfigure"):
            _stream.reconfigure(encoding="utf-8")
    sys.exit(main())
