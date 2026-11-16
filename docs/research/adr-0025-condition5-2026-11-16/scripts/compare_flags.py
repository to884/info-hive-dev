"""製品のコード（rag_pdf.ocr_page）が付けた行の印が、選ぶ資料で試した印（probe）と同じかを確かめる。

使い方（rag の依存の環境で動かす）: python -X utf8 scripts/compare_flags.py
corpus/ocr2/（RUN_OCR_OUT=ocr2 の run_ocr.py の結果）と、corpus/probe/ の読みを、選ぶ資料のページごとに比べる。
比べるのは、行の本文と箱、ぼかした読み（製品の blur_text と probe の blur100）、別の解像度の読み（製品の alt_text と
probe の 200 dpi の読みをつないだ本文）、印の理由（製品の flags と、probe で同じ決まりから求めた理由）である。
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
sys.path.insert(0, str(HERE.parents[3] / "info-hive-rag" / "scripts"))

import probe_analyze  # noqa: E402
from rag_ocr_flags import static_flags  # noqa: E402
from score import CORPUS, load_truths  # noqa: E402


def main() -> None:
    import hashlib

    counts = {"pages": 0, "lines": 0, "text": 0, "blur": 0, "alt": 0, "flags": 0}
    examples = []
    inputs = {}
    for truth in load_truths():
        if truth["side"] != "tuning":
            continue
        for page in truth["pages"]:
            key = f"{truth['name']}-p{page['page']:04d}"
            raw = (CORPUS / "ocr2" / f"{key}.json").read_bytes()
            inputs[key] = hashlib.sha256(raw).hexdigest()
            product = json.loads(raw.decode("utf-8"))
            if product["pdf_sha256"] != truth["pdf_sha256"]:
                raise SystemExit(f"製品の OCR の結果の PDF が正解と違う: {key}")
            probe = probe_analyze.load_reads("reads", key, truth["pdf_sha256"])
            boxed = [{**x, "box": [x["box"][0], x["box"][1], x["box"][0] + x["box"][2], x["box"][1] + x["box"][3]]}
                     for x in probe]
            probe_analyze.attach_other_dpi(boxed, key, truth["pdf_sha256"])
            counts["pages"] += 1
            for mine, theirs in zip(product["lines"], boxed):
                counts["lines"] += 1
                expected = static_flags({"text": theirs["text"], "confidence": theirs["confidence"],
                                         "blur_text": theirs["reads"]["blur100"]["text"], "alt_text": theirs["dpi_text"]})
                checks = {"text": (mine["text"], mine["box"], mine["confidence"]) == (theirs["text"], probe[boxed.index(theirs)]["box"], theirs["confidence"]),
                          "blur": mine.get("blur_text") == theirs["reads"]["blur100"]["text"],
                          "alt": mine.get("alt_text") == theirs["dpi_text"],
                          "flags": mine.get("flags") == expected}
                for name, ok in checks.items():
                    counts[name] += ok
                if not all(checks.values()) and len(examples) < 10:
                    examples.append({"page": key, "checks": checks, "product_flags": mine.get("flags"), "probe_flags": expected})
            if len(product["lines"]) != len(probe):
                examples.append({"page": key, "lines": (len(product["lines"]), len(probe))})
    all_equal = (counts["pages"] > 0 and not examples
                 and all(counts[k] == counts["lines"] for k in ("text", "blur", "alt", "flags")))
    print(json.dumps(counts, ensure_ascii=False))
    for example in examples:
        print(json.dumps(example, ensure_ascii=False))
    from score import RESULTS
    RESULTS.mkdir(exist_ok=True)
    (RESULTS / "compare-flags.json").write_bytes(
        (json.dumps({**counts, "all_equal": all_equal, "inputs": inputs}, ensure_ascii=False, indent=1) + "\n").encode("utf-8"))
    if not all_equal:
        raise SystemExit("製品の印と試した印が違う行がある")


if __name__ == "__main__":
    main()
