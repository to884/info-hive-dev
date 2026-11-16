"""3 回目: 開発用の資料で、製品の OCR の結果（corpus/ocr3/）が、2 回目の読み（corpus/ocr2/）と試しの別の認識器の読み
（corpus/probe/rapid/）と同じで、印が今の製品の決まりどおりかを確かめる。

使い方（rag の依存の環境で動かす）: python -X utf8 scripts/compare_flags_v3.py
確かめる資料を数える前に通す（../../adr-0025-condition5-v3-2026-11-17.md の「印は製品のコードで付ける」）。
結果を results/compare-flags-v3.json に、照らした ocr3 の結果の SHA-256 と一緒に書く。違う行があれば失敗で終わる。
"""

from __future__ import annotations

import hashlib
import json
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
sys.path.insert(0, str(HERE.parents[3] / "info-hive-rag" / "scripts"))

from rag_ocr_flags import OCR_FLAG_REVISION, static_flags  # noqa: E402
from score import CORPUS, RESULTS, load_truths  # noqa: E402


def main() -> None:
    counts = {"pages": 0, "lines": 0, "same_reads": 0, "same_rapid": 0, "same_flags": 0}
    problems, inputs = [], {}
    for truth in load_truths():
        if truth["side"] not in ("tuning", "evaluation"):
            continue
        for page in truth["pages"]:
            key = f"{truth['name']}-p{page['page']:04d}"
            raw = (CORPUS / "ocr3" / f"{key}.json").read_bytes()
            inputs[key] = hashlib.sha256(raw).hexdigest()
            mine = json.loads(raw.decode("utf-8"))
            old = json.loads((CORPUS / "ocr2" / f"{key}.json").read_bytes().decode("utf-8"))["lines"]
            rapid = json.loads((CORPUS / "probe" / "rapid" / f"{key}.json").read_bytes().decode("utf-8"))["reads"]
            counts["pages"] += 1
            if mine.get("flag_revision") != OCR_FLAG_REVISION or len(mine["lines"]) != len(old) or len(old) != len(rapid):
                problems.append({"page": key, "flag_revision": mine.get("flag_revision"), "lines": (len(mine["lines"]), len(old), len(rapid))})
                continue
            for line, before, read in zip(mine["lines"], old, rapid):
                counts["lines"] += 1
                reads = all(line[k] == before[k] for k in ("text", "box", "confidence", "blur_text", "alt_text"))
                same_rapid = line.get("rapid_text") == (read["text"] if read else None)
                same_flags = line.get("flags") == static_flags(line)
                counts["same_reads"] += reads
                counts["same_rapid"] += same_rapid
                counts["same_flags"] += same_flags
                if not (reads and same_rapid and same_flags) and len(problems) < 20:
                    problems.append({"page": key, "reads": reads, "rapid": same_rapid, "flags": same_flags})
    all_equal = (counts["pages"] > 0 and not problems
                 and all(counts[k] == counts["lines"] for k in ("same_reads", "same_rapid", "same_flags")))
    print(json.dumps(counts, ensure_ascii=False))
    for problem in problems:
        print(json.dumps(problem, ensure_ascii=False))
    RESULTS.mkdir(exist_ok=True)
    (RESULTS / "compare-flags-v3.json").write_bytes(
        (json.dumps({**counts, "all_equal": all_equal, "flag_revision": OCR_FLAG_REVISION, "inputs": inputs},
                    ensure_ascii=False, indent=1) + "\n").encode("utf-8"))
    if not all_equal:
        raise SystemExit("製品の OCR の結果が、2 回目の読みか試しの読みと違う行がある")


if __name__ == "__main__":
    main()
