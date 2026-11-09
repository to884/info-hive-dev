"""実際の wiki と原本のフォルダーのハッシュを取り、snapshots/real-wiki-hashes.json に追記する。

実行の前と後に取り、PoC が実際の wiki を書き換えていないことを確かめる。

使い方:
    python hash_real_wikis.py --label before
"""
from __future__ import annotations

import argparse
import hashlib
import json
from datetime import datetime
from pathlib import Path

HERE = Path(__file__).resolve().parent
OUT = HERE.parent / "snapshots" / "real-wiki-hashes.json"
TARGETS = {
    "W0_Wiki": Path.home() / "info-hive" / "W0_Wiki",
    "W1_Raw": Path.home() / "info-hive" / "W1_Raw",
    "semasynth-wiki": Path("C:/works/semasynth-dev/wiki"),
    "semasynth-raw": Path("C:/works/semasynth-dev/raw"),
}


def tree_hash(root: Path) -> tuple[str, int]:
    h = hashlib.sha256()
    n = 0
    for p in sorted(root.rglob("*"), key=lambda x: x.relative_to(root).as_posix()):
        if p.is_file():
            h.update(p.relative_to(root).as_posix().encode("utf-8") + b"\0")
            h.update(hashlib.sha256(p.read_bytes()).digest())
            n += 1
    return h.hexdigest(), n


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--label", required=True)
    args = ap.parse_args()
    data = json.loads(OUT.read_text(encoding="utf-8")) if OUT.exists() else []
    entry = {"label": args.label, "at": datetime.now().astimezone().isoformat(timespec="seconds"), "trees": {}}
    for name, root in TARGETS.items():
        digest, n = tree_hash(root)
        entry["trees"][name] = {"sha256": digest, "files": n}
        print(f"{args.label} {name}: {digest[:16]} files={n}")
    data.append(entry)
    OUT.write_text(json.dumps(data, ensure_ascii=False, indent=2) + "\n", encoding="utf-8", newline="\n")


if __name__ == "__main__":
    main()
