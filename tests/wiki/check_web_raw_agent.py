"""URL の取り込みで、raw の段をエージェント wiki:web-raw（Sonnet）が行い、後段をメインのモデルが行ったかを、
Claude Code のセッションの記録から確かめる。

設計: docs/plans/wiki-web-raw-agent-2026-11-14.md

    # 一時の wiki で /wiki:ingest を動かして確かめる（claude -p を 1 回動かすので、モデルの呼び出しの費用がかかる）
    python -X utf8 tests/wiki/check_web_raw_agent.py run <URL> --work <空のフォルダー> [--model opus] [--out <結果の JSON>]

    # 動かし終えたセッションを確かめ直す
    python -X utf8 tests/wiki/check_web_raw_agent.py analyze --session <セッションの ID> --project <取り込みを動かしたフォルダー>

調べるのは、記録に残った事実である（モデルの自己申告は使わない）。合否を決めるのは、確かに読み取れるものだけにする。

- 誰が動いたか: エージェントの記録の横にある、Claude Code が書いたメタデータ（`agent-*.meta.json` の `agentType` と
  `launchedWithDefaults`、`agent-*.prefix.json` のモデル）と、記録のすべての応答のモデル（欠けていれば不合格）。
- メインが Agent ツールで wiki:web-raw を呼び、model の引数を渡していないこと（入力とメタデータの両方）。
- 構造のある道具の書き込み: Edit、Write、NotebookEdit の対象のファイル（`..` とリンクを解いて比べる）。raw に書こうと
  したのは wiki:web-raw だけで、wiki:web-raw は wiki のページ、index.md、log.md に書こうとしていないこと（ほかの
  サブエージェントも含めて調べる。禁止は、失敗した呼び出しも数える）。メインが書いたことは、成功した呼び出し
  （結果が誤りでない）だけで数える。
- スクリプトの実行: wiki_fetch.py と freeze の出力を受け取ったのは wiki:web-raw だけで、W8 の check --finish が通って
  作業用の写しを消したこと。どれも、コマンドの文字列ではなく、呼び出しの id で対応させた道具の結果で決める。
- 文章の受け渡し: raw の文がメインに初めて届く（道具の結果か通知に現れる）までのメインの出力（文と道具の入力）と、
  すべての wiki:web-raw の依頼に、raw の本文の 40 文字以上の並びがないこと。エージェントの出力に、要約ページの文の並び
  （raw にもある並びは除く）がないこと。これは受け渡しの一部を見つけるだけで、どのモデルが文を考えたかの証明ではない。
- 結果: raw の translated_by と補足の表示名、log の「raw:」のサブ行、作業用の写しが消えていること、要約ページがあること。

Bash のコマンドの中の書き込みは、合否を決めない。シェルの文から書き込みを推し量ることは、完全にはできない
（mv の移動元、cd のあとの相対パス、コードの中で組み立てたパスなど）。担当ごとに、raw か wiki のページに触れうる
Bash のコマンド（raw や wiki のページのパス、cd、書き込みの呼び出しを含むもの）を一覧に出すので、人が読んで確かめる。
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
                    out.append({"kind": "in", "text": text, "tool_use_id": part.get("tool_use_id"),
                                "is_error": bool(part.get("is_error"))})
                else:
                    text = part.get("text", "") if isinstance(part.get("text"), str) else ""
                    out.append({"kind": "in", "text": text, "tool_use_id": None, "is_error": False})
    return out


def results_of(evs: list[dict]) -> dict[str, dict]:
    """道具の呼び出しの id ごとの結果。"""
    return {e["tool_use_id"]: e for e in evs if e["kind"] == "in" and e.get("tool_use_id")}


def succeeded(tool: dict, results: dict[str, dict]) -> bool:
    """呼び出しに結果があり、誤りでない（書けなかった Write などを、書いたと数えない）。"""
    r = results.get(tool.get("id"))
    return r is not None and not r["is_error"]


def tools_of(evs: list[dict]) -> list[dict]:
    return [e for e in evs if e["kind"] == "tool_use"]


def models_of(evs: list[dict]) -> list[str]:
    return sorted({e["model"] for e in evs if e.get("model") and not e["model"].startswith("<")})


WRITE_TOOLS = ("Edit", "Write", "NotebookEdit", "MultiEdit")


def norm(path: str, base: Path) -> str:
    """比べるためのパス。相対パスは base から読み、`..` とシンボリックリンクを解く（記録の別名を同じファイルにする）。"""
    p = Path(str(path).replace("\\", "/"))
    if not p.is_absolute():
        p = base / p
    return p.resolve().as_posix()


def tool_paths(tools: list[dict], base: Path, results: dict[str, dict] | None = None) -> list[str]:
    """書き込みの道具（Edit、Write、NotebookEdit）の対象のファイル。results を渡すと、成功した呼び出しだけにする。"""
    return [norm(t["input"].get("file_path", ""), base) for t in tools
            if t["name"] in WRITE_TOOLS and t["input"].get("file_path")
            and (results is None or succeeded(t, results))]


def bash_commands(tools: list[dict]) -> list[str]:
    return [str(t["input"].get("command", "")) for t in tools if t["name"] in ("Bash", "PowerShell")]


REDIRECT_RE = re.compile(r"(?<![0-9&])>>?\s*[\"']?([^\s;|&\"'<>]+)")
WIKI_PAGE_RE = re.compile(r"(?:^|/)(?:index\.md|log\.md|SCHEMA\.md)$|(?:^|/)(?:sources|entities|concepts|synthesis)/[^/]+\.md$")
RAW_PATH_RE = re.compile(r"(?:^|[\s\"'=(/\\])raw[/\\][^\s\"';|&)]*")
WIKI_PAGE_IN_TEXT_RE = re.compile(r"(?:index|log|SCHEMA)\.md|(?:sources|entities|concepts|synthesis)[/\\][^\s\"']+\.md")


def bash_write_targets(commands: list[str]) -> list[str]:
    """Bash のリダイレクト（`>`、`>>`）の書き込み先。`2>` や `&>` の行き先は数えない。"""
    return [m.group(1).replace("\\", "/") for c in commands for m in REDIRECT_RE.finditer(c)
            if m.group(1) not in ("/dev/null", "nul", "NUL")]


def under(path: str, root: Path) -> bool:
    """path（norm を通したもの）が root（resolve したもの）の下か。Windows の大文字小文字の違いは同じとみなす。"""
    p = path.replace("\\", "/").lower()
    r = root.as_posix().lower().rstrip("/") + "/"
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


def _out_text(e: dict) -> str:
    return e["text"] if e["kind"] == "out_text" else json.dumps(e["input"], ensure_ascii=False)


def touches(command: str, patterns: list[re.Pattern]) -> bool:
    return any(p.search(command) for p in patterns)


CD_RE = re.compile(r"(?:^|[;&|\n]\s*)(?:cd|pushd|Set-Location)\s")


# 誰がスクリプトを実行したかは、コマンドの文字列ではなく、その人に届いた道具の結果（スクリプトの出力の形）で決める。
# コマンドの文字列からは、引用符、変数、別の呼び出しで組み立てたパスなどを完全には読めず、echo などの表示を実行と
# 取り違える。スクリプトの名前を含むコマンドは、合否を決めない一覧（bash_to_review）に出す。
# 作業用の写しの fetch.json は取得の出力と同じ形なので、それを cat で読んだ結果も、取得の実行に数える（厳しい側に倒す）。
# --json の出力は、"final_url" のすぐあとに "source_sha256" が来る（wiki_fetch.build の結果の並び。0.14.1 までの版も同じ）。
FETCH_OUT = re.compile(r'"final_url": "[^"]*",\s*"source_sha256": "|^保存した: |ページを取得せずに続ける|'
                       r"内容は前回と同じなので、書き込まなかった|同じスラッグのファイルがあり、内容が違う", re.M)
FREEZE_OUT = re.compile(r'^freeze: (?:通った|規則に反している)|"stage": "freeze"', re.M)
SCRIPT_NAME = re.compile(r"wiki_fetch\.py|wiki_rawcheck\.py")


def check_finished(text: str) -> bool:
    """check の出力で、検査が通り、作業用の写しを消したもの（--finish を付けて通ったときだけ消す）。"""
    as_json = '"stage": "check"' in text and '"work_dir_removed": true' in text and '"ok": true' in text
    as_text = re.search(r"^check: 通った", text, re.M) is not None and "作業用の写しを消した" in text
    return as_json or as_text


def ran(tools: list[dict], results: dict[str, dict], out_re: re.Pattern) -> list[str]:
    """結果がスクリプトの出力の形をしている Bash と PowerShell の呼び出しのコマンド。"""
    return [str(t["input"].get("command", "")) for t in tools if t["name"] in ("Bash", "PowerShell")
            and t.get("id") in results and out_re.search(results[t["id"]]["text"])]


def analyze_paths(main_path: Path, sub_paths: list[Path], project: Path, main_model: str) -> dict:
    # 記録の書き込み先は絶対パスなので、相対パスで渡されたプロジェクトも絶対パスにしてから比べる
    project = Path(project).resolve()
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
    others = [s for s in subs if s["type"] != AGENT_TYPE]
    wiki, raw = project / "wiki", project / "raw"
    checks: list[dict] = []

    def check(name: str, ok, detail=None):
        checks.append({"check": name, "ok": bool(ok), "detail": detail})

    agent_calls = [t for t in main_tools if t["name"] in ("Agent", "Task")]
    web_raw_calls = [t for t in agent_calls if t["input"].get("subagent_type") == AGENT_TYPE]
    check("メインが wiki:web-raw を呼んだ", web_raw_calls and raw_agents,
          {"calls": [t["input"].get("subagent_type") for t in agent_calls], "agents": [s["type"] for s in subs]})
    check("メインが Agent に model を渡していない（入力と、Claude Code のメタデータの launchedWithDefaults）",
          all("model" not in t["input"] for t in web_raw_calls) and raw_agents
          and all(s["defaults"] is True for s in raw_agents),
          {"model": [t["input"].get("model") for t in web_raw_calls], "launchedWithDefaults": [s["defaults"] for s in raw_agents]})

    def response_models(evs: list[dict]) -> list[str]:
        return [e.get("model") or "" for e in evs if e["kind"] in ("out_text", "tool_use")]

    main_models = response_models(main_events)
    check(f"メインのすべての応答のモデルが {main_model}", main_models and all(main_model in m for m in main_models),
          sorted(set(main_models)))
    agent_models = [m for s in raw_agents for m in response_models(s["events"])]
    prefix_models = [s["prefix_model"] for s in raw_agents]
    check("wiki:web-raw のすべての応答のモデルと、prefix.json のモデルが Sonnet",
          agent_models and all("sonnet" in m for m in agent_models)
          and prefix_models and all(m and "sonnet" in m for m in prefix_models),
          {"responses": sorted(set(agent_models)), "prefix": prefix_models})

    # 担当ごとの出来事（道具の呼び出しと、その結果）。結果は呼び出しの id で引く。
    actor_events = {"main": main_events, AGENT_TYPE: [e for s in raw_agents for e in s["events"]]}
    for s in others:
        actor_events.setdefault(f"other:{s['type']}", []).extend(s["events"])
    actors = {name: tools_of(evs) for name, evs in actor_events.items()}
    results = {name: results_of(evs) for name, evs in actor_events.items()}
    bash = {name: bash_commands(tools) for name, tools in actors.items()}
    # 禁止を調べるときは、書こうとした呼び出しをすべて数える（失敗しても、書こうとしたことは違反である）。
    writes = {name: tool_paths(tools, project) for name, tools in actors.items()}
    # 書いたことを求めるときは、成功した呼び出しだけを数える。
    written = {name: tool_paths(tools, project, results[name]) for name, tools in actors.items()}

    fetch_runs = {name: ran(tools, results[name], FETCH_OUT) for name, tools in actors.items()}
    freeze_runs = {name: ran(tools, results[name], FREEZE_OUT) for name, tools in actors.items()}
    check("wiki_fetch.py と freeze を実行したのは wiki:web-raw だけ（道具の結果の形）",
          fetch_runs[AGENT_TYPE] and freeze_runs[AGENT_TYPE]
          and not any(fetch_runs[n] or freeze_runs[n] for n in actors if n != AGENT_TYPE),
          {n: [c[:160] for c in fetch_runs[n] + freeze_runs[n]] for n in actors
           if n != AGENT_TYPE and (fetch_runs[n] or freeze_runs[n])})
    finished = {n: [t for t in tools if t["name"] in ("Bash", "PowerShell") and succeeded(t, results[n])
                    and check_finished(results[n][t["id"]]["text"])] for n, tools in actors.items()}
    check("W8 の check --finish が通り、作業用の写しを消した（道具の結果）", any(finished.values()),
          {n: len(c) for n, c in finished.items() if c})

    raw_writers = {name: [p for p in paths if under(p, raw)] for name, paths in writes.items()}
    check("raw に書いた（Edit、Write）のは wiki:web-raw だけ",
          not any(paths for name, paths in raw_writers.items() if name != AGENT_TYPE),
          {name: paths for name, paths in raw_writers.items() if name != AGENT_TYPE and paths})
    agent_wiki = [p for p in writes[AGENT_TYPE] if under(p, wiki) and "/.wiki-cache/" not in p]
    check("wiki:web-raw は wiki のページ、index.md、log.md に書いていない（Edit、Write）", not agent_wiki, agent_wiki)
    ok_bash = [str(t["input"].get("command", "")) for t in actors["main"]
               if t["name"] in ("Bash", "PowerShell") and succeeded(t, results["main"])]
    main_targets = written["main"] + bash_write_targets(ok_bash)
    # Write の入力だけでは、書けたかは分からない（権限の誤りなど）。成功した書き込みで、ファイルがあることを求める
    # （前の取り込みの要約ページが残っていても、今回の書き込みが失敗していれば通さない）。
    main_sources = [p for p in written["main"] if under(p, wiki / "sources")]
    check("メインが要約ページ、index.md、log.md を書いた（要約ページはファイルがある）",
          any(Path(p).is_file() for p in main_sources)
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
    # 要約ページがないと、下の受け渡しの確かめは空の文と比べて通ってしまうので、あることを先に確かめる
    check("要約ページがある", sources, [str(s) for s in sources])
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

    # 合否を決めない一覧: raw か wiki のページに触れうる Bash のコマンド（人が読んで確かめる）。
    raw_like = [RAW_PATH_RE, re.compile(re.escape(str(raw).replace("\\", "/")), re.I)]
    wiki_like = [WIKI_PAGE_IN_TEXT_RE]
    review = {}
    for name, cmds in bash.items():
        if name == AGENT_TYPE:
            picked = [c for c in cmds if touches(c, wiki_like)]
        elif name == "main":
            picked = [c for c in cmds if touches(c, raw_like + [SCRIPT_NAME]) or (CD_RE.search(c) and "raw" in c)]
        else:
            picked = [c for c in cmds if touches(c, raw_like + wiki_like + [SCRIPT_NAME])]
        if picked:
            review[name] = [c[:300] for c in picked]
    return {"project": str(project), "checks": checks, "ok": all(c["ok"] for c in checks),
            "bash_to_review": review,
            "translated_by": translated_by.group(1) if translated_by else None, "caption_names": captions,
            "main_models": sorted(set(main_models)), "agent_models": sorted(set(agent_models)),
            "other_subagents": [{"path": s["path"], "type": s["type"], "models": models_of(s["events"])} for s in others],
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
