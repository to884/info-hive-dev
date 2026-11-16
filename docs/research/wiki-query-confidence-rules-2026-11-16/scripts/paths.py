# 測定のスクリプトが共有するパスと条件。実行と集計で同じ記録の場所を使う
#
# - 記録の場所: 環境変数 QC_RUNS_DIR。なければ <名前>/runs/（.gitignore で無視する）
# - プラグイン: 環境変数 QC_PLUGIN_DIR（測る版の info-hive-wiki を取り出したディレクトリ）
# - 試験用の wiki: 環境変数 QC_WIKI_BASE。リポジトリの外に置く。<QC_WIKI_BASE>/wiki が wiki のルートで、
#   クエリはこのディレクトリを作業ディレクトリにして流す（リポジトリの AGENTS.md と wiki/ を読ませないため）
# - MCP サーバーのデータの置き場所: <QC_WIKI_BASE>/data/<条件>。条件ごとに別のサーバーが立つ
import hashlib
import os
import sys
from pathlib import Path

SCRIPTS = Path(__file__).resolve().parent
RESEARCH = SCRIPTS.parent
REPO = SCRIPTS.parents[3]
FIXTURE = RESEARCH / "fixture" / "wiki"
QUESTIONS = RESEARCH / "questions.json"
SUMMARY = RESEARCH / "runs-summary.json"
RUNS = Path(os.environ.get("QC_RUNS_DIR") or RESEARCH / "runs").resolve()

# 条件: MCP サーバーのデータの置き場所と、子に渡す環境変数
#   ready:     モデルを置いた置き場所。索引は前もって埋め込んでおく（index.state は ready）
#   broken:    verified.json はあるが、モデルのファイルが空。読み込みに失敗し「埋め込みモデルを使えない」になる
#   preparing: モデルがなく、取得もできない（HF_HUB_OFFLINE）。いつも「埋め込みモデルを用意している」になる
CONDITIONS = ("ready", "broken", "preparing")


def wiki_base() -> Path:
    value = os.environ.get("QC_WIKI_BASE")
    if not value:
        sys.exit("QC_WIKI_BASE に、試験用の wiki を置くリポジトリの外のディレクトリを指定してください")
    path = Path(value).resolve()
    try:
        path.relative_to(REPO)
    except ValueError:
        return path
    sys.exit(f"QC_WIKI_BASE がリポジトリの中にある: {path}（リポジトリの指示と wiki を読ませないため、外に置く）")


def wiki_root() -> Path:
    return wiki_base() / "wiki"


def data_dir(condition: str) -> Path:
    if condition not in CONDITIONS:
        sys.exit(f"知らない条件: {condition}")
    return wiki_base() / "data" / condition


def child_env(condition: str) -> dict:
    env = dict(os.environ)
    for k in list(env):
        if k.startswith("CLAUDECODE") or k == "CLAUDE_CODE_ENTRYPOINT":
            env.pop(k)
    env["INFO_HIVE_DATA_DIR"] = str(data_dir(condition))
    if condition != "ready":
        env["HF_HUB_OFFLINE"] = "1"
    return env


def plugin_dir() -> Path:
    """測る版のプラグインのディレクトリを返す。なければ理由を書いて止まる"""
    value = os.environ.get("QC_PLUGIN_DIR")
    if not value:
        sys.exit("QC_PLUGIN_DIR に、測る版の info-hive-wiki のディレクトリを指定してください")
    path = Path(value).resolve()
    if not (path / ".claude-plugin" / "plugin.json").is_file():
        sys.exit(f"プラグインではない: {path}（.claude-plugin/plugin.json がない）")
    return path


def wiki_digest() -> str:
    """wiki の中身のハッシュ。検索のキャッシュ（.wiki-cache）は除く。実行の前後で比べ、wiki が変わっていないかを見る"""
    root = wiki_root()
    h = hashlib.sha256()
    for p in sorted(root.rglob("*")):
        rel = p.relative_to(root).as_posix()
        if not p.is_file() or rel.startswith(".wiki-cache/"):
            continue
        h.update(rel.encode("utf-8") + b"\0" + hashlib.sha256(p.read_bytes()).digest())
    return h.hexdigest()


def require_runs() -> Path:
    """集計の前に記録の場所があるかを確かめる"""
    if not RUNS.is_dir():
        sys.exit(f"記録の場所がない: {RUNS}（QC_RUNS_DIR を確かめてください）")
    return RUNS
