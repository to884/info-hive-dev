"""PoC 用の wiki の固定スナップショットを作り、ハッシュを記録する。

実際の wiki は読むだけで、書かない。スナップショットは --out の下に作る（リポジトリの外を想定）。
資料ごとに、取り込む資料の source ページ、索引の行、ログを抜いた「取り込む前の状態」を作る。

使い方:
    python build_snapshots.py --out <スナップショットの置き場所> --manifest ../snapshots/manifest.json
"""
from __future__ import annotations

import argparse
import hashlib
import json
import re
import shutil
from pathlib import Path

HOME = Path.home()
HERE = Path(__file__).resolve().parent
REPO = HERE.parents[3]  # docs/agent-runs/<run>/scripts → リポジトリのルート
RULES_SRC = REPO / "info-hive-wiki" / "skills" / "info-hive" / "references"

# 取り込む資料。id は実行の記録とファイル名に使う。
SOURCES = {
    "O": {
        "snapshot": "w0",
        "slug": "part-1-what-is-an-ontology-classes-properties-and-axioms",
        "raw_rel": "W1_Raw/part-1-what-is-an-ontology-classes-properties-and-axioms.md",
        "title": "Part 1: What Is an Ontology? Classes, Properties, and Axioms",
    },
    "R": {
        "snapshot": "semasynth",
        "slug": "semasynth再現性の検証-2026-11-06",
        "raw_rel": "raw/semasynth再現性の検証-2026-11-06.md",
        "title": "SemaSynth 再現性の検証",
    },
    "V": {
        "snapshot": "semasynth",
        "slug": "semasynth-mvp設計の敵対的レビュー-2026-11-06",
        "raw_rel": "raw/semasynth-mvp設計の敵対的レビュー-2026-11-06.md",
        "title": "SemaSynth MVP 設計の敵対的レビュー",
    },
}

SNAPSHOTS = {
    "w0": {
        "wiki_src": HOME / "info-hive" / "W0_Wiki",
        "wiki_dst": "W0_Wiki",
        "raw_src": HOME / "info-hive" / "W1_Raw",
        # 取り込む資料のほかに、この PoC の題材そのものを論じたシンセシス 2 本も抜く。
        # 現行の手順の対照が、併用案の結論を読んで影響を受けないようにするためである。
        "drop_pages": [
            "sources/part-1-what-is-an-ontology-classes-properties-and-axioms.md",
            "synthesis/wikiの記事の単位とatomic-notesとevergreen-notes.md",
            "synthesis/wikiの記事作成の方法論の提案の導入判断.md",
        ],
    },
    "semasynth": {
        "wiki_src": Path("C:/works/semasynth-dev/wiki"),
        "wiki_dst": "wiki",
        "raw_src": Path("C:/works/semasynth-dev/raw"),
        "drop_pages": [
            "sources/semasynth再現性の検証-2026-11-06.md",
            "sources/semasynth-mvp設計の敵対的レビュー-2026-11-06.md",
        ],
    },
}

# 配置の計画には使わない派生データ。グラフと検索のキャッシュ、評価ループの作業領域。
SKIP_DIRS = {"graph", ".wiki-cache", ".evolution"}


def sha256_file(p: Path) -> str:
    return hashlib.sha256(p.read_bytes()).hexdigest()


def tree_hash(root: Path) -> tuple[str, list[dict]]:
    files = []
    h = hashlib.sha256()
    for p in sorted(root.rglob("*"), key=lambda x: x.relative_to(root).as_posix()):
        if p.is_file():
            rel = p.relative_to(root).as_posix()
            digest = sha256_file(p)
            files.append({"path": rel, "sha256": digest, "bytes": p.stat().st_size})
            h.update(f"{rel}\0{digest}\n".encode("utf-8"))
    return h.hexdigest(), files


def drop_index_lines(index: Path, slugs: list[str]) -> int:
    text = index.read_text(encoding="utf-8")
    lines = text.splitlines(keepends=True)
    keep, dropped = [], 0
    for line in lines:
        if any(line.lstrip().startswith(f"- [[{s}]]") for s in slugs):
            dropped += 1
            continue
        keep.append(line)
    index.write_text("".join(keep), encoding="utf-8", newline="")
    return dropped


def truncate_log(log: Path) -> None:
    """ログは前文だけを残す。過去の取り込みの記録が、資料の扱いを先回りして示すのを避ける。"""
    text = log.read_text(encoding="utf-8")
    m = re.search(r"^## \[", text, flags=re.M)
    if m:
        log.write_text(text[: m.start()].rstrip() + "\n", encoding="utf-8", newline="")


def build(out: Path) -> dict:
    manifest: dict = {"rules": {}, "snapshots": {}, "sources": {}}
    out.mkdir(parents=True, exist_ok=True)
    for sid, cfg in SNAPSHOTS.items():
        dst_root = out / sid
        if dst_root.exists():
            shutil.rmtree(dst_root)
        wiki_dst = dst_root / cfg["wiki_dst"]
        shutil.copytree(cfg["wiki_src"], wiki_dst,
                        ignore=lambda d, names: [n for n in names if n in SKIP_DIRS])
        dropped_slugs = []
        for rel in cfg["drop_pages"]:
            p = wiki_dst / rel
            if not p.exists():
                raise SystemExit(f"抜くページがありません: {p}")
            p.unlink()
            dropped_slugs.append(Path(rel).stem)
        n_index = drop_index_lines(wiki_dst / "index.md", dropped_slugs)
        truncate_log(wiki_dst / "log.md")
        # 取り込む原本だけを置く
        for src in SOURCES.values():
            if src["snapshot"] != sid:
                continue
            raw_src = cfg["raw_src"] / Path(src["raw_rel"]).name
            raw_dst = dst_root / src["raw_rel"]
            raw_dst.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(raw_src, raw_dst)
        # 現行の規約（両方式に共通）
        rules_dst = dst_root / "_rules"
        rules_dst.mkdir()
        for name in ("ingest-workflow.md", "page-conventions.md"):
            shutil.copy2(RULES_SRC / name, rules_dst / name)
        th, files = tree_hash(dst_root)
        manifest["snapshots"][sid] = {
            "wiki_src": str(cfg["wiki_src"]).replace("\\", "/"),
            "dropped_pages": cfg["drop_pages"],
            "dropped_index_lines": n_index,
            "log": "前文だけに切り詰めた",
            "skipped_dirs": sorted(SKIP_DIRS),
            "tree_sha256": th,
            "n_files": len(files),
            "files": files,
        }
    for name in ("ingest-workflow.md", "page-conventions.md"):
        manifest["rules"][name] = sha256_file(RULES_SRC / name)
    for key, src in SOURCES.items():
        raw = out / src["snapshot"] / src["raw_rel"]
        text = raw.read_text(encoding="utf-8")
        manifest["sources"][key] = {**src, "raw_sha256": sha256_file(raw),
                                    "raw_lines": len(text.splitlines()), "raw_chars": len(text)}
    return manifest


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--out", required=True, type=Path)
    ap.add_argument("--manifest", required=True, type=Path)
    args = ap.parse_args()
    manifest = build(args.out)
    manifest["snapshot_root"] = str(args.out).replace("\\", "/")
    args.manifest.parent.mkdir(parents=True, exist_ok=True)
    args.manifest.write_text(json.dumps(manifest, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    for sid, s in manifest["snapshots"].items():
        print(f"{sid}: files={s['n_files']} tree_sha256={s['tree_sha256'][:16]} index行の削除={s['dropped_index_lines']}")
    for k, s in manifest["sources"].items():
        print(f"{k}: lines={s['raw_lines']} chars={s['raw_chars']} sha256={s['raw_sha256'][:16]}")


if __name__ == "__main__":
    main()
