# 測定のスクリプトが共有するパス。実行と集計で同じ記録の場所を使う
#
# - REPO: このファイルの場所から決める（docs/research/<名前>/scripts/ の 4 つ上）
# - 記録の場所: 環境変数 QC_RUNS_DIR。なければ <名前>/runs/（.gitignore で無視する）
# - プラグイン: 環境変数 QC_PLUGIN_DIR（測る版の info-hive-wiki を取り出したディレクトリ）
import os
import sys
from pathlib import Path

SCRIPTS = Path(__file__).resolve().parent
RESEARCH = SCRIPTS.parent
REPO = SCRIPTS.parents[3]
QUESTIONS = RESEARCH / "questions.json"
SUMMARY = RESEARCH / "runs-summary.json"
RUNS = Path(os.environ.get("QC_RUNS_DIR") or RESEARCH / "runs").resolve()


def plugin_dir() -> Path:
    """測る版のプラグインのディレクトリを返す。なければ理由を書いて止まる"""
    value = os.environ.get("QC_PLUGIN_DIR")
    if not value:
        sys.exit("QC_PLUGIN_DIR に、測る版の info-hive-wiki のディレクトリを指定してください")
    path = Path(value).resolve()
    if not (path / ".claude-plugin" / "plugin.json").is_file():
        sys.exit(f"プラグインではない: {path}（.claude-plugin/plugin.json がない）")
    return path


def require_runs() -> Path:
    """集計の前に記録の場所があるかを確かめる"""
    if not RUNS.is_dir():
        sys.exit(f"記録の場所がない: {RUNS}（QC_RUNS_DIR を確かめてください）")
    return RUNS
