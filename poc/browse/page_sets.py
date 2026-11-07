"""未決 1（ページの集合）の材料。lint と search の collect_pages が返す集合を比べる。

wiki 0.6.0（36a4089）の scripts を out/wiki-src/ に取り出して使う（README を参照）。
使い方: python -X utf8 page_sets.py <wiki のルート> [...]
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE / "out" / "wiki-src" / "skills" / "info-hive" / "scripts"))

import wiki_lint  # noqa: E402
import wiki_search  # noqa: E402


def compare(root: Path) -> dict:
    lint = {p["rel_path"] for p in wiki_lint.collect_pages(root)}
    search = {p["rel_path"] for p in wiki_search.collect_pages(root)}
    every = {wiki_search.posix_rel(p.relative_to(root).as_posix()) for p in root.rglob("*.md")}
    return {
        "wiki": root.as_posix(),
        "all_md": len(every),
        "lint": len(lint),
        "search": len(search),
        "lint_only": sorted(lint - search),
        "search_only": sorted(search - lint),
        "neither": sorted(every - lint - search),
    }


def main(argv: list[str]) -> int:
    results = [compare(Path(a).resolve()) for a in argv]
    print(json.dumps(results, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
