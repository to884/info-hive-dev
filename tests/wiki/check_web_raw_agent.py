"""URL の取り込みで、raw の段をエージェント wiki:web-raw（Sonnet）が行い、後段をメインのモデルが行ったかを、
Claude Code のセッションの記録から確かめる。

設計: docs/plans/wiki-web-raw-agent-2026-11-14.md

    # 一時の wiki で /wiki:ingest を動かして確かめる（claude -p を 1 回動かすので、モデルの呼び出しの費用がかかる）
    python -X utf8 tests/wiki/check_web_raw_agent.py run <URL> --work <空のフォルダー> [--model opus] [--out <結果の JSON>]

    # 動かし終えたセッションを確かめ直す
    python -X utf8 tests/wiki/check_web_raw_agent.py analyze --session <セッションの ID> --project <取り込みを動かしたフォルダー>

調べるのは、記録に残った事実である（モデルの自己申告は使わない）。合否を決めるのは、確かに読み取れるものだけにする。

前提（この外のことは、見つけることを主張しない）:

- 記録は、手順に従って動いたセッションのものとする（わざと隠した書き込みや実行、スクリプトの名前と
  サブコマンドを名前に含むファイルを cat で表示する、などの見せかけは見つけない）。
- analyze に渡すプロジェクトは、空のフォルダーから始めた取り込みとする（run はそうする）。前の取り込みのページが
  残っているプロジェクトでは、ファイルの中身は今回書いたことの証拠にならない。
- 1 回の確かめでは、1 つの URL を取り込む（run はそうする）。いくつもの URL を同時に取り込んだ記録では、表示名は
  最後に終えた W8 の分だけを見る。

合否を決めるもの（あったことを示す証拠）:

- 誰が動いたか: エージェントの記録の横にある、Claude Code が書いたメタデータ（`agent-*.meta.json` の `agentType` と
  `launchedWithDefaults`、`agent-*.prefix.json` のモデル）と、記録のすべての応答のモデル（欠けていれば不合格）。
- メインが Agent ツールで wiki:web-raw を呼び、model の引数を渡していないこと（入力とメタデータの両方）。
- 構造のある道具の書き込み: Edit、Write、NotebookEdit の対象のファイル（`..`、Windows の拡張パスの接頭辞、リンクを解いて比べる）。
  raw に Edit や Write で書こうとしたのは wiki:web-raw だけで、wiki:web-raw は wiki のページ、index.md、log.md に
  Edit や Write で書こうとしていないこと（禁止は、失敗した呼び出しも数える）。メインが書いたことは、成功した呼び出し
  （結果が誤りでない）だけで数える。
- スクリプトの実行: wiki:web-raw が wiki_fetch.py と freeze の出力を受け取ったこと（呼び出しの id で対応させた道具の
  結果の形で決める）。W8 は、wiki:web-raw の呼び出しのコマンドに `wiki_rawcheck`、`check`、`--finish` が書かれ、その
  結果に、検査が通って作業用の写しを消した check の出力があること（シェルの区切りや引用符は読まない）。結果が
  誤り（あとのコマンドが失敗して、呼び出し全体が誤りになる）でも、その中の出力は読む。1 つの結果の中の check の
  出力は、出た順の 1 回ずつに分ける。JSON の回（行の頭の `{` から始まるもの）と、文字の出力の回である。文字の
  出力の回は、wiki_rawcheck.render が書く行の形（render から作る）に合う行だけで、freeze の出力などのほかの行が
  来たら終わる。W8 の終わりは、写しを消した回のうち、時刻と記録の順で最後の回で、JSON の回でなければならない
  （W8 は `--json` で動かす。0.18.1 の手順）。警告が残ったまま写しを消した回は、check に
  `--accept-warnings` を付けたときだけ出る。wiki:web-raw のその回は、JSON でも文字の出力でも、どの回でも不合格
  （あとで取り直して正しく終えても消えない。エージェントは警告を受け入れない）。最後の回を、警告を受け入れる
  流れでメインがその形で終えたときは通し、どちらが終えたかを `w8_finished_by` に書く。
- 結果の形で読めること: raw のファイルに、確かめが読むスクリプトの出力の形の文字列（check と freeze の見出しと
  最後の行、`"stage": "check"`、wiki_fetch.py の出力の文言など）がないこと。あれば、本文を表示した結果の中で
  本物の出力と見分けられないので、判定できないとして不合格にする。
- 文章の受け渡し: raw の文がメインに初めて届く（道具の結果か通知に現れる）までのメインの出力（文と道具の入力）と、
  すべての wiki:web-raw の依頼に、raw の本文の 40 文字以上の並びがないこと。エージェントの出力に、要約ページの文の並び
  （raw にもある並びは除く）がないこと。これは受け渡しの一部を見つけるだけで、どのモデルが文を考えたかの証明ではない。
- 結果（ファイルの中身と、プラグインの出力）: 要約ページを、メインが成功した Edit か Write で書いたこと。index.md に、
  その要約ページのすべてへのリンクがあること（プラグインの wiki_pages.extract_wikilinks と resolve_link で読む。コードの
  中のリンクは数えないので、初期の index.md の説明文の記入例は数えない。`[[sources/スラッグ]]` の形も読む）。log.md の
  取り込みの項目（`## [日付] ingest |` の見出しの項目）の中に「raw:」のサブ行があること。索引とログは Bash で書くことも
  あるので、コマンドからは決めない。訳と補足の表示名は、W8 の最後の回（`check --json` の出力）の値
  （wiki_rawcheck.py が画像と Markdown の木から補足を見分けた名前）から取る（W8 が通らなければ判定せず、
  `display_names_verified` を false にする）。作業用の写しが消えていること。

合否を決めないもの（なかったことは、記録からは示せない）:

- ほかの担当（メインとほかのサブエージェント）が、wiki_fetch.py や freeze を動かさなかったこと、Bash で raw や
  wiki のページに書かなかったこと。出力を捨てる、変数に入れたパスで呼ぶ、コードの中でパスを組み立てる、などは
  文字列からも結果からも読み切れない。そこで、メインとほかのサブエージェントの Bash と PowerShell のコマンドを
  すべて `bash_to_review` に出し（wiki:web-raw のものは、wiki のページに触れうるものだけ）、人が読んで確かめる。
  結果の形からほかの担当の実行が見えたときは、`other_script_runs` に出す（これも合否を決めない）。
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
sys.path.insert(0, str(PLUGIN / "skills" / "info-hive" / "scripts"))
import wiki_pages  # noqa: E402  プラグインの wikilink の読み方（コードの中のリンクを除き、パス付きの形も読む）
import wiki_rawcheck  # noqa: E402  check の文字の出力の形（render）
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

    同じ応答が 2 度記録されることがあるので、重ねない。重ねるのは、同じ部品と分かるときだけにする。道具の部品は
    その id で、文の部品は、応答の id（なければ記録の uuid）とモデルと中身がすべて同じときである。別の応答が同じ文を
    返しても（モデルが違っても、モデルが欠けていても）、別の出来事として残す（モデルの確かめで落とさないため）。
    """
    out, seen = [], set()
    for n, rec in enumerate(records):
        # 会話の記録（type が assistant と user）だけを読む。api-request-blob などは、要求に入れた前の応答の写しで、
        # 応答そのものではない（モデルを持たないので、数えるとモデルの確かめを誤る）。
        if rec.get("type") not in (None, "assistant", "user"):
            continue
        msg = rec.get("message") or {}
        role = msg.get("role")
        content = msg.get("content")
        parts = content if isinstance(content, list) else ([{"type": "text", "text": content}] if content else [])
        origin = msg.get("id") or rec.get("uuid") or f"record-{n}"
        for part in parts:
            if not isinstance(part, dict):
                continue
            key = part.get("id") or part.get("tool_use_id") or (
                origin, msg.get("model"), json.dumps(part, ensure_ascii=False, sort_keys=True))
            key = (role, part.get("type"), key)
            if key in seen:
                continue
            seen.add(key)
            if role == "assistant" and part.get("type") == "text":
                out.append({"kind": "out_text", "model": msg.get("model", ""), "text": part.get("text", "")})
            elif role == "assistant" and part.get("type") == "tool_use":
                out.append({"kind": "tool_use", "model": msg.get("model", ""), "name": part.get("name"),
                            "ts": rec.get("timestamp") or "",
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


EXTENDED_PREFIX_RE = re.compile(r"^(?:\\\\|//)[?.][\\/](?:UNC[\\/])?", re.I)


def norm(path, base: Path) -> str:
    r"""比べるためのパス。相対パスは base から読み、`..` とシンボリックリンクを解く（記録の別名を同じファイルにする）。

    Windows の拡張パスの接頭辞（`\\?\C:\...`、`\\.\C:\...`、`\\?\UNC\host\share\...`）は外してから解く。
    `resolve()` は接頭辞を残すことがあり、残ると、同じファイルでも比べる文字列が変わる。
    """
    text = str(path)
    m = EXTENDED_PREFIX_RE.match(text)
    if m:
        unc = m.group(0).upper().rstrip("\\/").endswith("UNC")
        text = ("//" if unc else "") + text[m.end():]
    p = Path(text.replace("\\", "/"))
    if not p.is_absolute():
        p = base / p
    resolved = p.resolve().as_posix()
    m = EXTENDED_PREFIX_RE.match(resolved)
    if m:
        unc = m.group(0).upper().rstrip("\\/").endswith("UNC")
        resolved = ("//" if unc else "") + resolved[m.end():]
    return resolved


def tool_paths(tools: list[dict], base: Path, results: dict[str, dict] | None = None) -> list[str]:
    """書き込みの道具（Edit、Write、NotebookEdit）の対象のファイル。results を渡すと、成功した呼び出しだけにする。"""
    return [norm(t["input"].get("file_path", ""), base) for t in tools
            if t["name"] in WRITE_TOOLS and t["input"].get("file_path")
            and (results is None or succeeded(t, results))]


def bash_commands(tools: list[dict]) -> list[str]:
    return [str(t["input"].get("command", "")) for t in tools if t["name"] in ("Bash", "PowerShell")]


WIKI_PAGE_IN_TEXT_RE = re.compile(r"(?:index|log|SCHEMA)\.md|(?:sources|entities|concepts|synthesis)[/\\][^\s\"']+\.md")


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


# wiki:web-raw がスクリプトの出力を受け取ったことは、その呼び出しの結果の形で決める（あったことの証拠）。
# ほかの担当が動かさなかったことは、記録からは示せない（出力を捨てる、変数に入れたパスで呼ぶ、など）ので、合否を
# 決めず、結果の形から見えたものを other_script_runs に、コマンドをすべて bash_to_review に出す。
# --json の出力は、"final_url" のすぐあとに "source_sha256" が来る（wiki_fetch.build の結果の並び。0.14.1 までの版も同じ）。
FETCH_OUT = re.compile(r'"final_url": "[^"]*",\s*"source_sha256": "|^保存した: |ページを取得せずに続ける|'
                       r"内容は前回と同じなので、書き込まなかった|同じスラッグのファイルがあり、内容が違う", re.M)
FREEZE_OUT = re.compile(r'^freeze: (?:通った|規則に反している)|"stage": "freeze"', re.M)
def names_finish(command: str) -> bool:
    """コマンドが wiki_rawcheck.py の check を --finish で動かしたものに見えるか。

    シェルの区切りや引用符は読まない（引用符の中の `;` や、行の継続の場所で取り違えるため）。前の出力を cat で表示した
    だけの呼び出しを W8 の証拠にしないために、スクリプトの名前とサブコマンドとオプションが書かれていることだけを見る。
    """
    return "wiki_rawcheck" in command and re.search(r"(?<![\w-])check(?![\w-])", command) is not None \
        and "--finish" in command


def check_json_spans(text: str) -> list[tuple[int, int, dict]]:
    """結果の文の中の、wiki_rawcheck.py check --json の出力の JSON を、(始まり, 終わり, 値) で出た順にすべて返す。

    --json の出力は、行の頭の `{` から始まる（json.dumps の indent=2 を print したもの。`"stage"` が最初のキー）。
    行の途中から始まる JSON は数えない。文字の出力の誤りの詳細（`    取得: {…}`）に、ページの中の 1 行の JSON が
    出ることがあるからである。
    """
    out, pos = [], 0
    decoder = json.JSONDecoder()
    while True:
        at = text.find('"stage": "check"', pos)
        if at < 0:
            return out
        start = text.rfind("{", 0, at)
        pos = at + 1
        if start < 0 or (start > 0 and text[start - 1] != "\n"):
            continue
        try:
            value, end = decoder.raw_decode(text[start:])
        except json.JSONDecodeError:
            continue
        if isinstance(value, dict) and value.get("stage") == "check":
            out.append((start, start + end, value))
            pos = start + end


def check_jsons(text: str) -> list[dict]:
    """結果の文の中の check の JSON を、出た順にすべて返す。"""
    return [value for _, _, value in check_json_spans(text)]


def check_text_forms() -> dict:
    """wiki_rawcheck.render が check の文字の出力に書く行の形。render そのものから作る（文言が変わってもずれない）。

    1 回の出力は、見出しの行（通ったか）、誤りと警告の行（誤りには、取得と raw の行が続く）、最後の 1 行（写しを
    消した、警告や誤りで残した。--finish のないときはない）の順に並ぶ。render は 1 回の print で書く。項目の値の中の
    改行のあとの行は、0.18.1 から字下げされる（wiki_rawcheck.CONTINUATION）ので、ページの本文が見出しや最後の行の
    形で出ることはない。
    """
    base = {"stage": "check", "ok": True, "errors": [], "warnings": []}

    def lines(**changes) -> list[str]:
        return wiki_rawcheck.render({**base, **changes}).split("\n")

    passed, removed = lines(work_dir_removed=True)
    failed = lines(ok=False, errors=[{"message": "\0", "source": "\0", "raw": "\0"}], work_dir_kept="errors")
    warned = lines(warnings=[{"message": "\0"}], work_dir_kept="warnings")
    continued = lines(warnings=[{"message": "\0\n\0"}])[2].split("\0")[0]
    warning = warned[1].split("\0")[0]
    return {"passed": passed, "heads": {passed, failed[0]}, "removed": removed,
            "endings": {removed, failed[-1], warned[-1]}, "warning": warning,
            "items": tuple(line.split("\0")[0] for line in failed[1:-1]) + (warning, continued)}


CHECK_TEXT = check_text_forms()


def output_shapes(text: str) -> list[str]:
    """ページの本文の中の、確かめが読むスクリプトの出力の形の文字列。

    確かめは、道具の結果の文から、wiki_fetch.py、freeze、check の出力を形で読む。ページの本文に同じ形の文字列が
    あると、本文を表示した結果（0.18.0 までの check の誤りの詳細、cat など）の中で、本物の出力と見分けられない。
    行の頭かどうか、字下げや引用の記号の有無は問わずに、文字列として探す（本文の表示のされ方で、行の頭が変わる）。
    """
    freeze = {wiki_rawcheck.render({"stage": "freeze", "ok": ok, "errors": [], "warnings": []}) for ok in (True, False)}
    shapes = sorted(CHECK_TEXT["heads"] | CHECK_TEXT["endings"] | freeze) + [
        '"stage": "check"', '"stage": "freeze"', '"final_url": ', "保存した: ", "ページを取得せずに続ける",
        "内容は前回と同じなので、書き込まなかった", "同じスラッグのファイルがあり、内容が違う"]
    return [s for s in shapes if s in text]


def check_runs(text: str) -> list[dict]:
    """1 つの結果の中の check の出力を、出た順の 1 回ずつに分ける。

    1 つの呼び出しで、check を何度か動かすことがある（検査、直す、再検査。取り直してもう一度）。回ごとに、
    写しを消したか（removed）、警告が残ったまま消したか（accepted。--accept-warnings を付けたときだけ起きる。
    wiki_rawcheck.main）、JSON（文字の出力なら None）を返す。JSON の回は、その JSON の値で決める。文字の出力の回は、
    見出しの行から、render が書く形（check_text_forms）の行だけを読む。最後の行で終わり、形に合わない行（freeze の
    出力、ほかのコマンドの出力、JSON）が来たら、そこで終わる。ほかの段の警告を、check の回に数えないためである。
    """
    spans = check_json_spans(text)
    runs = [{"pos": start, "json": value, "removed": value.get("ok") is True and value.get("work_dir_removed") is True,
             "warnings": bool(value.get("warnings"))} for start, _, value in spans]
    inside = lambda i: any(s <= i < e for s, e, _ in spans)  # noqa: E731
    lines, offsets, at = [], [], 0
    for line in text.split("\n"):
        lines.append(line.rstrip("\r"))  # Windows の print は CRLF で書く
        offsets.append(at)
        at += len(line) + 1
    for i, head in enumerate(lines):
        if head not in CHECK_TEXT["heads"] or inside(offsets[i]):
            continue
        warnings = removed = False
        for line in lines[i + 1:]:
            if line in CHECK_TEXT["endings"]:
                removed = line == CHECK_TEXT["removed"]
                break
            if not line.startswith(CHECK_TEXT["items"]):
                break
            warnings = warnings or line.startswith(CHECK_TEXT["warning"])
        runs.append({"pos": offsets[i], "json": None, "removed": head == CHECK_TEXT["passed"] and removed,
                     "warnings": warnings})
    for run in runs:
        run["accepted"] = run["removed"] and run["warnings"]
    return sorted(runs, key=lambda r: r["pos"])


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
        records = read_jsonl(path)
        first = next((r.get("timestamp") for r in records if r.get("timestamp")), "")
        subs.append({"path": str(path), "type": meta.get("agentType"), "defaults": meta.get("launchedWithDefaults"),
                     "prefix_model": (prefix.get("state") or {}).get("model"), "events": evs, "first": first})
    subs.sort(key=lambda s: (s["first"], s["path"]))
    raw_agents = [s for s in subs if s["type"] == AGENT_TYPE]
    others = [s for s in subs if s["type"] != AGENT_TYPE]
    # wiki と raw そのものがリンクのこともあるので、書き込み先と同じく解いてから比べる
    wiki, raw = Path(norm(project / "wiki", project)), Path(norm(project / "raw", project))
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

    # あったことの証拠: wiki:web-raw が取得と freeze の出力を受け取った（結果の形）。
    fetch_runs = {name: ran(tools, results[name], FETCH_OUT) for name, tools in actors.items()}
    freeze_runs = {name: ran(tools, results[name], FREEZE_OUT) for name, tools in actors.items()}
    check("wiki:web-raw が wiki_fetch.py と freeze の出力を受け取った（道具の結果の形）",
          fetch_runs[AGENT_TYPE] and freeze_runs[AGENT_TYPE],
          {"fetch": len(fetch_runs[AGENT_TYPE]), "freeze": len(freeze_runs[AGENT_TYPE])})
    # ほかの担当の実行は、記録からは「なかった」と示せないので、見えたものを出すだけにする（合否を決めない）。
    other_runs = {n: fetch_runs[n] + freeze_runs[n] for n in actors
                  if n != AGENT_TYPE and (fetch_runs[n] or freeze_runs[n])}

    # check --finish の回を、担当ごとに、時刻と記録の順で並べる。1 つの呼び出しの中の何回もの check は、出た順に分ける。
    # 結果が誤りでも読む。呼び出しの誤りは、その中の最後のコマンドの終了コードで決まり、先に終えた check の出力は
    # 残るからである（finish のあとの確かめのコマンドが失敗したときなど）。回が通ったかは、回の出力で決める。
    # 並べる鍵は（時刻、担当、担当の中の呼び出しの順、結果の中の位置）。担当をまたぐ前後は時刻でしか決まらないので、
    # 時刻が同じか欠けたときは、エージェントの回をあとにする。
    def finish_runs(name: str, order: int) -> list[dict]:
        out = []
        for n, t in enumerate(actors[name]):
            if t["name"] in ("Bash", "PowerShell") and names_finish(str(t["input"].get("command", ""))) \
                    and t.get("id") in results[name]:
                for run in check_runs(results[name][t["id"]]["text"]):
                    out.append({**run, "actor": name, "command": str(t["input"].get("command", "")),
                                "key": (t.get("ts") or "", order, n, run["pos"])})
        return out

    agent_runs = finish_runs(AGENT_TYPE, 1)
    main_runs = finish_runs("main", 0)
    # 警告が残ったまま写しを消せるのは、check に --accept-warnings を付けたときだけである（wiki_rawcheck.main）。
    # エージェントは付けない（agents/web-raw.md）。どの回でも、その出力があれば違反とする（あとで取り直して正しく
    # 終えても、違反は消えない）。コマンドの文字列ではなく、出力で決める。
    agent_accepted = [r["command"] for r in agent_runs if r["accepted"]]
    check("wiki:web-raw は警告を受け入れて終えていない（check --finish の出力。どの回も）", not agent_accepted, agent_accepted)
    # W8 の終わりは、写しを消した回のうち、時刻と記録の順で最後のもので決める。エージェントが警告なしで終えたか、
    # 警告を受け入れる流れ（references/web-raw.md の warnings）でメインが警告の残ったまま終えたなら通す。W8 は
    # --json で動かす（0.18.1 の手順）ので、最後の回は JSON でなければならない。文字の出力の回は、上の違反を
    # 見つけるためだけに読む。
    final = max([r for r in agent_runs + main_runs if r["removed"]], key=lambda r: r["key"], default=None)
    w8_by = []
    if final is not None and final["json"] is not None:
        if final["actor"] == AGENT_TYPE and not final["warnings"]:
            w8_by = [AGENT_TYPE]
        elif final["actor"] == "main" and final["warnings"]:
            w8_by = ["main"]
    check("W8 の check --finish --json を wiki:web-raw が自分で動かして通った（警告を受け入れる流れでは、メインが"
          "警告の残ったまま終える）", w8_by,
          {"finished_by": w8_by, "final_actor": final["actor"] if final else None,
           "final_is_json": final["json"] is not None if final else None})

    raw_writers = {name: [p for p in paths if under(p, raw)] for name, paths in writes.items()}
    check("raw に書いた（Edit、Write）のは wiki:web-raw だけ",
          not any(paths for name, paths in raw_writers.items() if name != AGENT_TYPE),
          {name: paths for name, paths in raw_writers.items() if name != AGENT_TYPE and paths})
    agent_wiki = [p for p in writes[AGENT_TYPE] if under(p, wiki) and "/.wiki-cache/" not in p]
    check("wiki:web-raw は wiki のページ、index.md、log.md に書いていない（Edit、Write）", not agent_wiki, agent_wiki)
    # Write の入力だけでは、書けたかは分からない（権限の誤りなど）。成功した書き込みで、ファイルがあることを求める
    # （前の取り込みの要約ページが残っていても、今回の書き込みが失敗していれば通さない）。
    main_sources = [p for p in written["main"] if under(p, wiki / "sources") and Path(p).is_file()]
    check("メインが要約ページを Edit か Write で書いた（成功した呼び出しで、ファイルがある）", main_sources, main_sources)
    # 索引とログは、Bash で書くこともあり、コマンドから書き込み先は読み切れないので、ファイルの中身で決める。
    # プロジェクトは空のフォルダーから始めた取り込みなので（前提）、中身は今回の取り込みが書いたものである。
    index = (wiki / "index.md").read_bytes().decode("utf-8") if (wiki / "index.md").exists() else ""
    # プラグインの読み方（wiki_pages.extract_wikilinks。コードの中のリンクは数えない。初期の index.md の説明文の
    # 記入例はインラインのコードなので数えない）で、リンクを sources/<スラッグ> のページに解く（パス付きの形も読む）。
    stems = sorted({Path(p).stem for p in main_sources})
    by_path = {f"sources/{s}": s for s in stems}
    resolved = {wiki_pages.resolve_link(link, by_path, set(stems)) for link in wiki_pages.extract_wikilinks(index)}
    linked = [s for s in stems if s in resolved]
    check("index.md に、メインが書いた要約ページのすべてへのリンクがある（ファイルの中身）",
          stems and linked == stems, {"pages": stems, "linked": linked})

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
    check("raw がある", raws, [str(p) for p in raws])
    # スクリプトの実行は結果の文の形で読むので、ページの本文に同じ形の文字列があれば、記録から判定できない
    # （判定できないことを、通したことにしない）。
    raw_full = "\n".join(p.read_bytes().decode("utf-8") for p in raws)
    shapes = output_shapes(raw_full)
    check("raw に、確かめが読むスクリプトの出力の形の文字列がない（あれば、記録の中で本物の出力と見分けられず、"
          "判定できない）", not shapes, shapes)
    # 表示名は、W8 の check --json の結果から取る（wiki_rawcheck.py が、画像と Markdown の木から補足を見分けた名前）。
    # 自前で raw を読み直すと、リストの中の補足を見落とし、原文の引用を補足と取り違える。W8 が通ったなら、最後の
    # 回は JSON なので、いつも判定する。訳したなら Sonnet の名前であること
    # （訳さないページの空の translated_by と、画像がないときの補足のなさはよい。references/web-raw.md の呼び出す側の
    # 手順 6）。
    display = final["json"] if final is not None and w8_by else None
    if display is not None:
        names = ([display.get("translated_by")] if display.get("translated_by") else []) + list(display.get("caption_names") or [])
        check("W8 の check の結果の、訳と補足の表示名が Sonnet（空はよい）",
              all(isinstance(n, str) and "sonnet" in n.lower() for n in names),
              {"translated_by": display.get("translated_by"), "caption_names": display.get("caption_names")})
    log = (wiki / "log.md").read_bytes().decode("utf-8") if (wiki / "log.md").exists() else ""
    entries = re.split(r"(?m)^(?=## \[)", log)
    ingested = [e for e in entries if re.match(r"## \[\d{4}-\d{2}-\d{2}\] ingest \|", e)
                and re.search(r"(?m)^\s+raw:.*web-raw", e)]
    check("log の取り込みの項目に、raw の段の分担のサブ行がある（ファイルの中身）", ingested,
          [e.splitlines()[0] for e in ingested])
    ingest = wiki / ".wiki-cache" / "ingest"
    check("作業用の写しが消えた", not (ingest.exists() and any(ingest.iterdir())))

    # 合否を決めない一覧（人が読んで確かめる）。メインとほかのサブエージェントは、絞り込むと見落とすので、Bash と
    # PowerShell のコマンドをすべて出す。wiki:web-raw は数が多いので、wiki のページに触れうるものだけを出す。
    review = {}
    for name, cmds in bash.items():
        picked = [c for c in cmds if touches(c, [WIKI_PAGE_IN_TEXT_RE])] if name == AGENT_TYPE else list(cmds)
        if picked:
            # 人が読む証拠なので、切り詰めない（長いコマンドの後半に書き込みがあることがある）
            review[name] = picked
    return {"project": str(project), "checks": checks, "ok": all(c["ok"] for c in checks),
            "bash_to_review": review, "other_script_runs": other_runs, "w8_finished_by": w8_by,
            "display_names_verified": display is not None,
            "translated_by": display.get("translated_by") if display else None,
            "caption_names": display.get("caption_names") if display else None,
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
