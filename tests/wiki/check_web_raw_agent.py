"""URL の取り込みで、raw の段をエージェント wiki:web-raw（Sonnet）が行い、後段をメインのモデルが行ったかを、
Claude Code のセッションの記録から確かめる。

設計: docs/plans/wiki-web-raw-agent-2026-11-14.md

    # 一時の wiki で /wiki:ingest を動かして確かめる（claude -p を 1 回動かすので、モデルの呼び出しの費用がかかる）
    python -X utf8 tests/wiki/check_web_raw_agent.py run <URL> --work <空のフォルダー> [--model opus] [--out <結果の JSON>]

    # 動かし終えたセッションを確かめ直す
    python -X utf8 tests/wiki/check_web_raw_agent.py analyze --session <セッションの ID> --project <取り込みを動かしたフォルダー>

調べるのは、記録に残った事実である（モデルの自己申告は使わない）。

- 誰が動いたか: エージェントの記録の横にある、Claude Code が書いたメタデータ（`agent-*.meta.json` の `agentType`、
  `launchedWithDefaults`、`agent-*.prefix.json` のモデル）と、記録の応答のモデル。`wiki:web-raw` 以外のサブエージェント
  （メインが後段の調べものに使ったものなど）は、判定から外して一覧に出すだけにする。
- メインが Agent ツールで wiki:web-raw を呼び、model の引数を渡していないこと。
- 誰が何を書いたか: 道具の入力に現れる書き込みだけを調べる。Edit と Write の対象のファイル、Bash のリダイレクトの行き先、
  ファイルを書き換えるコマンド（sed -i、cp と mv の行き先、rm など）の引数、Bash の中の Python の書き込み
  （write_text、open(..., "w") など）と同じコマンドに現れる raw や wiki のページのパス。コードの中で組み立てたパスや、
  ファイルに書いたスクリプトの中の書き込みは見つけられない。
- 文章の受け渡し: raw の文がメインに初めて届く（道具の結果か通知に現れる）までのメインの出力（文と道具の入力）と、
  すべての wiki:web-raw の依頼に、raw の本文の 40 文字以上の並びがないこと。エージェントの出力に、要約ページの文の並び
  （raw にもある並びは除く）がないこと。これは受け渡しの一部を見つけるだけで、どのモデルが文を考えたかの証明ではない。
- 結果: raw の translated_by と補足の表示名、log の「raw:」のサブ行、作業用の写しが消えていること、要約ページがあること。
"""
from __future__ import annotations

import argparse
import glob
import json
import os
import re
import shlex
import shutil
import subprocess
import sys
import time
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
PLUGIN = ROOT / "info-hive-wiki"
WINDOW = 40
AGENT_TYPE = "wiki:web-raw"


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


def read_json(path: Path) -> dict:
    try:
        return json.loads(path.read_bytes().decode("utf-8"))
    except (OSError, json.JSONDecodeError):
        return {}


def find_transcripts(session: str) -> tuple[Path, list[Path]]:
    """セッションの記録（メイン）と、サブエージェントの記録の一覧。"""
    base = Path(os.path.expanduser("~/.claude/projects"))
    mains = [Path(p) for p in glob.glob(str(base / "*" / f"{session}.jsonl"))]
    if not mains:
        raise FileNotFoundError(f"セッションの記録が見つからない: {session}")
    main = mains[0]
    subs = sorted(Path(p) for p in glob.glob(str(main.with_suffix("") / "subagents" / "agent-*.jsonl")))
    return main, subs


def events(records: list[dict]) -> list[dict]:
    """記録を、順に並んだ出来事にする。応答の部品（text、tool_use）と、届いた内容（tool_result、利用者の文）。

    同じ部品が 2 度記録されることがあるので、部品の id（なければ中身）で重ねない。
    """
    out, seen = [], set()
    for rec in records:
        msg = rec.get("message") or {}
        role = msg.get("role")
        content = msg.get("content")
        parts = content if isinstance(content, list) else ([{"type": "text", "text": content}] if content else [])
        for part in parts:
            if not isinstance(part, dict):
                continue
            key = part.get("id") or part.get("tool_use_id") or json.dumps(part, ensure_ascii=False, sort_keys=True)
            key = (role, part.get("type"), key)
            if key in seen:
                continue
            seen.add(key)
            if role == "assistant" and part.get("type") == "text":
                out.append({"kind": "out_text", "model": msg.get("model", ""), "text": part.get("text", "")})
            elif role == "assistant" and part.get("type") == "tool_use":
                out.append({"kind": "tool_use", "model": msg.get("model", ""), "name": part.get("name"),
                            "id": part.get("id"), "input": part.get("input") or {}})
            elif role == "user":
                if part.get("type") == "tool_result":
                    c = part.get("content")
                    text = c if isinstance(c, str) else " ".join(
                        x.get("text", "") for x in (c or []) if isinstance(x, dict))
                else:
                    text = part.get("text", "") if isinstance(part.get("text"), str) else ""
                out.append({"kind": "in", "text": text})
    return out


def tools_of(evs: list[dict]) -> list[dict]:
    return [e for e in evs if e["kind"] == "tool_use"]


def models_of(evs: list[dict]) -> list[str]:
    return sorted({e["model"] for e in evs if e.get("model") and not e["model"].startswith("<")})


def tool_paths(tools: list[dict]) -> list[str]:
    """書き込みの道具（Edit、Write、NotebookEdit）が書いたファイル。"""
    return [str(t["input"].get("file_path", "")).replace("\\", "/")
            for t in tools if t["name"] in ("Edit", "Write", "NotebookEdit", "MultiEdit")]


def bash_commands(tools: list[dict]) -> list[str]:
    return [str(t["input"].get("command", "")) for t in tools if t["name"] in ("Bash", "PowerShell")]


REDIRECT_RE = re.compile(r"(?<![0-9&])>>?\s*[\"']?([^\s;|&\"'<>]+)")
WIKI_PAGE_RE = re.compile(r"(?:^|/)(?:index\.md|log\.md|SCHEMA\.md)$|(?:^|/)(?:sources|entities|concepts|synthesis)/[^/]+\.md$")
RAW_PATH_RE = re.compile(r"(?:^|[\s\"'=(/\\])raw[/\\][^\s\"';|&)]*")
PY_WRITE_RE = re.compile(r"\.write_(?:text|bytes)\(|\bopen\([^)]*[\"'][wax]\+?b?[\"']|shutil\.(?:copy\w*|move)\(|os\.replace\(")
WIKI_PAGE_IN_TEXT_RE = re.compile(r"(?:index|log|SCHEMA)\.md|(?:sources|entities|concepts|synthesis)[/\\][^\s\"']+\.md")
SEGMENT_RE = re.compile(r"&&|\|\||;|\|")


def bash_write_targets(commands: list[str]) -> list[str]:
    """Bash のリダイレクト（`>`、`>>`）の書き込み先。`2>` や `&>` の行き先は数えない。"""
    return [m.group(1).replace("\\", "/") for c in commands for m in REDIRECT_RE.finditer(c)
            if m.group(1) not in ("/dev/null", "nul", "NUL")]


def _words(segment: str) -> list[str]:
    try:
        return shlex.split(segment, posix=True)
    except ValueError:
        return segment.split()


def command_write_targets(commands: list[str]) -> list[str]:
    """ファイルを書き換えるコマンドの、書き換える先の引数（cp と mv は行き先、sed -i と rm は対象）。"""
    out = []
    for command in commands:
        for line in command.split("\n"):
            for segment in SEGMENT_RE.split(line):
                # Windows のパスの \ を、shlex がエスケープとして読まないように / にそろえる。
                words = _words(segment.strip().replace("\\", "/"))
                if not words:
                    continue
                name = words[0].lower()
                args = [w for w in words[1:] if not w.startswith("-")]
                if name in ("cp", "mv", "copy-item", "move-item") and args:
                    out.append(args[-1])
                elif name == "sed" and any(w.startswith("-i") for w in words[1:]):
                    out.extend(args[1:])
                elif name in ("rm", "remove-item", "set-content", "out-file", "add-content", "tee"):
                    out.extend(args)
    return [t.replace("\\", "/") for t in out]


def python_writes(commands: list[str], target: re.Pattern) -> list[str]:
    """Bash の中の Python で、書き込みの呼び出しと同じコマンドに target のパスが現れるもの（コマンドの頭）。"""
    return [c[:200] for c in commands if PY_WRITE_RE.search(c) and target.search(c)]


def under(path: str, root: Path) -> bool:
    p = path.replace("\\", "/").lower()
    r = str(root).replace("\\", "/").lower().rstrip("/") + "/"
    return p.startswith(r)


def is_raw_target(path: str, raw: Path) -> bool:
    p = path.replace("\\", "/")
    return under(p, raw) or bool(re.match(r"^(?:\./)?raw/", p))


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


def _out_text(e: dict) -> str:
    return e["text"] if e["kind"] == "out_text" else json.dumps(e["input"], ensure_ascii=False)


def analyze_paths(main_path: Path, sub_paths: list[Path], project: Path, main_model: str) -> dict:
    main_events = events(read_jsonl(main_path))
    main_tools = tools_of(main_events)
    subs = []
    for path in sub_paths:
        meta = read_json(path.with_suffix(".meta.json"))
        prefix = read_json(path.with_suffix(".prefix.json"))
        evs = events(read_jsonl(path))
        subs.append({"path": str(path), "type": meta.get("agentType"), "defaults": meta.get("launchedWithDefaults"),
                     "prefix_model": (prefix.get("state") or {}).get("model"), "events": evs})
    raw_agents = [s for s in subs if s["type"] == AGENT_TYPE]
    others = [{"path": s["path"], "type": s["type"], "models": models_of(s["events"])}
              for s in subs if s["type"] != AGENT_TYPE]
    wiki, raw = project / "wiki", project / "raw"
    checks: list[dict] = []

    def check(name: str, ok, detail=None):
        checks.append({"check": name, "ok": bool(ok), "detail": detail})

    agent_calls = [t for t in main_tools if t["name"] in ("Agent", "Task")]
    web_raw_calls = [t for t in agent_calls if t["input"].get("subagent_type") == AGENT_TYPE]
    check("メインが wiki:web-raw を呼んだ", web_raw_calls and raw_agents,
          {"calls": [t["input"].get("subagent_type") for t in agent_calls], "agents": [s["type"] for s in subs]})
    check("メインが Agent に model を渡していない（記録の入力と、Claude Code のメタデータ）",
          all("model" not in t["input"] for t in web_raw_calls) and all(s["defaults"] is not False for s in raw_agents),
          {"model": [t["input"].get("model") for t in web_raw_calls], "launchedWithDefaults": [s["defaults"] for s in raw_agents]})
    main_models = models_of(main_events)
    check(f"メインの応答のモデルが {main_model}", main_models and all(main_model in m for m in main_models), main_models)
    agent_models = sorted({m for s in raw_agents for m in models_of(s["events"])}
                          | {s["prefix_model"] for s in raw_agents if s["prefix_model"]})
    check("wiki:web-raw の応答のモデルが Sonnet（記録と prefix.json）",
          agent_models and all("sonnet" in m for m in agent_models), agent_models)

    agent_tools = [t for s in raw_agents for t in tools_of(s["events"])]
    agent_bash, main_bash = bash_commands(agent_tools), bash_commands(main_tools)
    agent_writes, main_writes = tool_paths(agent_tools), tool_paths(main_tools)
    check("wiki_fetch.py は wiki:web-raw だけが実行した",
          any("wiki_fetch.py" in c for c in agent_bash) and not any("wiki_fetch.py" in c for c in main_bash),
          {"main": [c[:200] for c in main_bash if "wiki_fetch.py" in c]})
    check("freeze は wiki:web-raw だけが実行した",
          any("wiki_rawcheck.py" in c and " freeze" in c for c in agent_bash)
          and not any("wiki_rawcheck.py" in c and " freeze" in c for c in main_bash))
    main_raw = [p for p in main_writes + bash_write_targets(main_bash) + command_write_targets(main_bash)
                if is_raw_target(p, raw)] + python_writes(main_bash, RAW_PATH_RE)
    check("メインは raw と画像に書いていない（道具の入力に現れる書き込み）", not main_raw, main_raw)
    agent_wiki = [p for p in agent_writes if under(p, wiki) and "/.wiki-cache/" not in p]
    agent_wiki += [p for p in bash_write_targets(agent_bash) + command_write_targets(agent_bash)
                   if WIKI_PAGE_RE.search(p) and "/.wiki-cache/" not in p]
    agent_wiki += python_writes(agent_bash, WIKI_PAGE_IN_TEXT_RE)
    check("wiki:web-raw は wiki のページ、index.md、log.md に書いていない（道具の入力に現れる書き込み）",
          not agent_wiki, agent_wiki)
    main_targets = main_writes + bash_write_targets(main_bash) + command_write_targets(main_bash)
    check("メインが要約ページ、index.md、log.md を書いた",
          any(under(p, wiki / "sources") for p in main_writes)
          and any(p.lower().endswith("index.md") for p in main_targets)
          and any(p.lower().endswith("log.md") for p in main_targets),
          sorted(set(main_targets)))

    # 文章の受け渡し
    raws = sorted(raw.glob("*.md"))
    raw_text = "\n".join(body_of(p.read_bytes().decode("utf-8")) for p in raws)
    raw_windows = windows(raw_text)
    cut = next((i for i, e in enumerate(main_events)
                if e["kind"] == "in" and any(w in re.sub(r"\s+", " ", e["text"]) for w in raw_windows)),
               len(main_events))
    before = [_out_text(e) for e in main_events[:cut] if e["kind"] in ("out_text", "tool_use")]
    prompts = [str(t["input"].get("prompt", "")) for t in web_raw_calls]
    check("raw の文が届くまでのメインの出力と、wiki:web-raw へのすべての依頼に、raw の文がない",
          not shares_text(raw_text, before) and not shares_text(raw_text, prompts),
          {"before": shares_text(raw_text, before), "prompts": shares_text(raw_text, prompts)})
    sources = sorted((wiki / "sources").glob("*.md"))
    summary = "\n".join(body_of(p.read_bytes().decode("utf-8")) for p in sources)
    agent_texts = [_out_text(e) for s in raw_agents for e in s["events"] if e["kind"] in ("out_text", "tool_use")]
    # 要約ページは raw から引用するので、raw にもある並びは受け渡しに数えない。
    check("wiki:web-raw の出力に、要約ページの文がない", not shares_text(summary, agent_texts, raw_text),
          shares_text(summary, agent_texts, raw_text))

    # 結果
    fm = raws[0].read_bytes().decode("utf-8") if raws else ""
    translated_by = re.search(r'^translated_by: "(.*)"$', fm, re.M)
    captions = sorted(set(re.findall(r"^> ?(?:> )*(.{1,60}?) 補足: ", body_of(fm), re.M)))
    check("raw がある", raws, [str(p) for p in raws])
    log = (wiki / "log.md").read_bytes().decode("utf-8") if (wiki / "log.md").exists() else ""
    check("log に raw の段の分担のサブ行がある", re.search(r"raw:.*web-raw", log) is not None)
    ingest = wiki / ".wiki-cache" / "ingest"
    check("作業用の写しが消えた", not (ingest.exists() and any(ingest.iterdir())))
    return {"project": str(project), "checks": checks, "ok": all(c["ok"] for c in checks),
            "translated_by": translated_by.group(1) if translated_by else None, "caption_names": captions,
            "main_models": main_models, "agent_models": agent_models, "other_subagents": others,
            "agent_transcripts": [s["path"] for s in raw_agents]}


def analyze(session: str, project: Path, main_model: str) -> dict:
    main_path, sub_paths = find_transcripts(session)
    report = analyze_paths(main_path, sub_paths, project, main_model)
    report["session"] = session
    return report


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
