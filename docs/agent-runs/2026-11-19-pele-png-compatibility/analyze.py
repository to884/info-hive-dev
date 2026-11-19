"""保存したブラウザ比較と画像から集計を再生成する。"""

import hashlib
import json
import statistics
from pathlib import Path

directory = Path(__file__).resolve().parent
result = json.loads((directory / "results/results.json").read_text(encoding="utf-8"))
checks = json.loads((directory / "results/png-browser-checks.json").read_text(encoding="utf-8"))
summary = {"cases": len(result["prepared"]), "browser_cases": len(result["observations"])}
for browser in ("chromium", "webkit"):
    observations = [row for row in result["observations"] if row["browser"] == browser]
    images = [row for row in checks if row["browser"] == browser]
    assert len(observations) == len(images) == len(result["prepared"])
    summary[browser] = {
        "normalization_max": max(row["normalization"]["fractionOver16"] for row in observations),
        "png1x_median": statistics.median(row["png1x"]["fractionOver16"] for row in observations),
        "png1x_max": max(row["png1x"]["fractionOver16"] for row in observations),
        "png2x_median": statistics.median(row["png2xFractionOver16"] for row in images),
        "png2x_max": max(row["png2xFractionOver16"] for row in images),
        "outside_original": sum(label["outsideViewport"] for row in observations for label in row["labels"]),
        "outside_normalized": sum(label["outsideViewport"] for row in observations for label in row["normalizedLabels"]),
        "changed_texts": [row["id"] for row in observations if
                          [label["text"] for label in row["labels"]] !=
                          [label["text"] for label in row["normalizedLabels"]]],
        "normalization_nonzero": [row["id"] for row in observations if row["normalization"]["fractionOver16"] > 0],
    }
corpus = [row for row in result["prepared"] if not row["id"].startswith("control-")]
summary["bytes"] = {
    "original_svg": sum((directory / f"{row['id']}.svg").stat().st_size for row in corpus),
    "normalized_svg": sum((directory / "results" / f"{row['id']}-normalized.svg").stat().st_size for row in corpus),
}
for scale in (1, 2):
    summary["bytes"][f"png{scale}x"] = sum(image["bytes"] for row in corpus for image in row["images"] if image["scale"] == scale)
for row in result["prepared"]:
    for image in row["images"]:
        content = (directory / "results" / image["file"]).read_bytes()
        assert len(content) == image["bytes"]
        assert hashlib.sha256(content).hexdigest() == image["sha256"]
(directory / "summary.json").write_text(json.dumps(summary, ensure_ascii=False, indent=2), encoding="utf-8", newline="\n")
print(json.dumps(summary, ensure_ascii=False))
