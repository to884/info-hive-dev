"""一方向 PoC の段階1・2を別ディレクトリで試す。"""

from __future__ import annotations

import argparse
import json
from pathlib import Path
import sqlite3
import sys
from tempfile import TemporaryDirectory

import export_wiki_graph as legacy
from demo_scenario import run_demo
from import_legacy import import_wiki, verify_import
from semantic_export import write_release


def run(output: Path, *, wiki=None, wiki_id=None, checkout=None) -> dict:
    output = output.resolve()
    if wiki:
        wiki = wiki.resolve(strict=True)
        if output.is_relative_to(wiki) or output.is_relative_to(wiki.parent / "raw"):
            raise ValueError("入力 wiki と原本の外に出力先を指定してください")
        if not wiki_id:
            raise ValueError("入力 wiki を識別する --wiki-id が必要です")
    if output.exists():
        raise FileExistsError(f"新しい出力先を指定してください: {output}")
    output.parent.mkdir(parents=True, exist_ok=True)
    with TemporaryDirectory(prefix=".ossie-trial-", dir=output.parent) as scratch:
        work = Path(scratch)
        bundle = work / "bundle"
        bundle.mkdir()
        if wiki:
            legacy_dir = bundle / "legacy"
            previous = legacy.export(wiki, legacy_dir, checkout)
            trial, source, snapshot, evidence_ids = import_wiki(
                wiki, wiki_id, legacy_dir, work / "reextracted.sqlite",
            )
            release = write_release(bundle / "semantic", trial.freeze(), checkout)
            result = verify_import(source, snapshot, evidence_ids, bundle / "semantic" / legacy.DATA)
            if legacy.snapshot(wiki / "graph" / "graph.sqlite") != source:
                raise ValueError("処理中に入力グラフが変更されました")
            report = {"mode": "legacy_import", "legacy": previous, "semantic": release, **result}
        else:
            report = {"mode": "synthetic_migration", **run_demo(bundle, checkout)}
        legacy.save_json(bundle / legacy.REPORT, report)
        if output.exists():
            raise FileExistsError(f"出力先がすでにあります: {output}")
        bundle.rename(output)
    return report


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    source = parser.add_mutually_exclusive_group(required=True)
    source.add_argument("--wiki", type=Path, help="既存 wiki のルート")
    source.add_argument("--demo", action="store_true", help="合成 wiki で集計・移行を試す")
    parser.add_argument("--wiki-id", help="再試行でも共用する既存 wiki の識別子")
    parser.add_argument("--output", type=Path, required=True, help="新しい出力ディレクトリ")
    parser.add_argument("--ossie-checkout", type=Path, help="公式検証器を実行する Ossie チェックアウト")
    args = parser.parse_args()
    if args.demo and args.wiki_id is not None:
        parser.error("--wiki-id は --wiki と組み合わせてください")
    try:
        report = run(args.output, wiki=args.wiki, wiki_id=args.wiki_id, checkout=args.ossie_checkout)
    except (OSError, ValueError, sqlite3.Error, ImportError, KeyError) as error:
        print(f"試行を完了できません: {error}", file=sys.stderr)
        return 1
    print(json.dumps(report, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    sys.exit(main())
