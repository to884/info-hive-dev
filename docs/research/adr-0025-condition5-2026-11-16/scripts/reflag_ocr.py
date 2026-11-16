"""保存した OCR の結果の行の印を、今の製品の決まり（rag_ocr_flags.static_flags）で付け直す。

使い方（rag の依存の環境で動かす）: python -X utf8 scripts/reflag_ocr.py <置き場所の名前（例: ocr3）>

8 回目のレビューで、4 つ目の印の比べ方を直した（flags-v2 → flags-v3）。印は、行の本文、確信度、ぼかした読み、
別の解像度の読み、別の認識器の読みだけから決まるので、OCR をやり直さずに付け直せる。読みのない結果は付け直さない。
付け直した結果には、もとの版を reflagged_from に残す。
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

BENCH = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(BENCH.parents[2] / "info-hive-rag" / "scripts"))

from rag_ocr_flags import OCR_FLAG_REVISION, static_flags  # noqa: E402


def main() -> None:
    folder = BENCH / "corpus" / sys.argv[1]
    changed = skipped = 0
    for path in sorted(folder.glob("*.json")):
        result = json.loads(path.read_bytes().decode("utf-8"))
        lines = result.get("lines")
        # 行の記録がない（None）結果だけを飛ばす。行が 0 件（[]）は正常な結果なので、版を上げる（9 回目のレビュー）
        if lines is None or any(k not in x for x in lines for k in ("blur_text", "alt_text", "rapid_text")):
            skipped += 1
            continue
        if result.get("flag_revision") == OCR_FLAG_REVISION:
            continue
        for line in lines:
            line["flags"] = static_flags(line)
        result["reflagged_from"] = result.get("flag_revision")
        result["flag_revision"] = OCR_FLAG_REVISION
        path.write_bytes(json.dumps(result, ensure_ascii=False).encode("utf-8"))
        changed += 1
    print("付け直した", changed, "読みがなく飛ばした", skipped)


if __name__ == "__main__":
    main()
