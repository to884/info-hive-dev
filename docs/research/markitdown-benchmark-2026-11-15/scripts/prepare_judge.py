"""Sol の判定のために、方式の名前を伏せた出力を judge/<試料>/<記号>.md に写す。

使い方: python prepare_judge.py <対応表の書き出し先> [--discard-judgement]

- 対応表（記号と方式の対応）は、判定が終わるまで judge/ の外に置く。判定のあとで judge/mapping.json に写す。
- judge/manifest.json に、写したファイルごとの SHA-256、対応表の SHA-256、それらをまとめたダイジェスト
  （digest）を書く。Sol には、判定の JSON の judge_digest に、読んだ manifest.json の digest を書かせる。
- 前の判定（judge/sol-result.md）か対応表が残っているときは、何もせずに止まる。--discard-judgement を
  付けると、それらを消してから写す。

aggregate.py は、(1) 判定の judge_digest と manifest.json の digest が同じこと、(2) manifest.json に書いた
SHA-256 と、judge/ の写し、outputs/ の出力、judge/mapping.json が同じことを確かめてから集計する。
写し直したあとに、前の写しを読んだ判定が書かれても、ダイジェストが違うので集計は止まる。
"""

from __future__ import annotations

import hashlib
import json
import random
import shutil
import sys
from pathlib import Path

BENCH = Path(__file__).resolve().parent.parent


def sha256(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def digest_of(files: dict[str, str], mapping_sha256: str) -> str:
    """写しと対応表の SHA-256 をまとめたダイジェスト。aggregate.py も同じ関数で計算し直す。"""
    canonical = json.dumps({"files": dict(sorted(files.items())), "mapping_sha256": mapping_sha256},
                           ensure_ascii=False, sort_keys=True)
    return sha256(canonical.encode("utf-8"))


def main() -> None:
    results = json.loads((BENCH / "results.json").read_text(encoding="utf-8"))["results"]
    judge = BENCH / "judge"
    old = sorted(judge.glob("sol-result.md*")) + sorted(judge.glob("mapping.json"))
    if old:
        if "--discard-judgement" not in sys.argv[2:]:
            sys.exit("前の判定が残っている: " + ", ".join(p.name for p in old)
                     + "。判定をやり直すときは --discard-judgement を付ける")
        for path in old:
            path.unlink()
    if judge.exists():
        for child in judge.iterdir():
            if child.is_dir():
                shutil.rmtree(child)
    judge.mkdir(exist_ok=True)
    rng = random.Random(20261115)
    mapping: dict[str, dict[str, str]] = {}
    files: dict[str, str] = {}
    by_file: dict[str, list[dict]] = {}
    for record in results:
        if "output" in record:
            by_file.setdefault(record["file"], []).append(record)
    for name, records in by_file.items():
        rng.shuffle(records)
        folder = judge / name.replace(".", "_")
        folder.mkdir()
        mapping[name] = {}
        for letter, record in zip("ABCD", records):
            data = (BENCH / record["output"]).read_bytes()
            (folder / f"{letter}.md").write_bytes(data)
            mapping[name][letter] = record["method"]
            files[f"{folder.name}/{letter}.md"] = sha256(data)
    mapping_bytes = json.dumps(mapping, ensure_ascii=False, indent=2).encode("utf-8")
    Path(sys.argv[1]).write_bytes(mapping_bytes)
    manifest = {"digest": digest_of(files, sha256(mapping_bytes)), "mapping_sha256": sha256(mapping_bytes),
                "files": files}
    (judge / "manifest.json").write_bytes(json.dumps(manifest, ensure_ascii=False, indent=2).encode("utf-8"))
    print(f"digest {manifest['digest']}")


if __name__ == "__main__":
    main()
