"""PoC と検証用スクリプトが使う作業データの置き場所を決める。

作業データ（索引、モデルのキャッシュ、計測の出力）はリポジトリの外に置く。
リポジトリの中に大量のファイルがあると、worktree の作成や git の走査が遅くなるためである。

置き場所は次の順に決める。

1. 環境変数 INFO_HIVE_POC_DATA があれば、その値を使う。
2. なければ、メインのチェックアウトの隣にある info-hive-dev-data/rag-poc-data を使う。
   worktree から呼ばれても、メインのチェックアウトを基準にするので同じ場所を指す。
"""
from __future__ import annotations

import os
from pathlib import Path

ENV_NAME = "INFO_HIVE_POC_DATA"
ROOT = Path(__file__).resolve().parents[1]


def main_checkout(root: Path = ROOT) -> Path:
    """root が worktree なら、メインのチェックアウトのパスを返す。そうでなければ root を返す。"""
    dot_git = root / ".git"
    if not dot_git.is_file():
        return root
    text = dot_git.read_text(encoding="utf-8").strip()
    if not text.startswith("gitdir:"):
        return root
    gitdir = Path(text[len("gitdir:"):].strip())
    if not gitdir.is_absolute():
        gitdir = (root / gitdir).resolve()
    commondir = gitdir / "commondir"
    if not commondir.is_file():
        return root
    common = Path(commondir.read_text(encoding="utf-8").strip())
    if not common.is_absolute():
        common = (gitdir / common).resolve()
    return common.parent


def poc_data_dir() -> Path:
    value = os.environ.get(ENV_NAME)
    if value:
        return Path(value)
    return main_checkout().parent / "info-hive-dev-data" / "rag-poc-data"


POC_DATA = poc_data_dir()
