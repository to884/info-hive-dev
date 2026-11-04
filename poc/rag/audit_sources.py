"""抽出時と終了後の原資料ハッシュを比較する。原本は読み取り専用で開く。"""
import hashlib
import json
import os
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
OUT = ROOT / "docs/research/rag-poc-2026-11-04"
WORK = (Path(os.environ["LOCALAPPDATA"]) / "info-hive/rag-poc/2026-11-04").resolve()
manifest = json.loads((WORK / "sample-manifest.json").read_text(encoding="utf-8"))
extracted = json.loads((OUT / "extraction-results.json").read_text(encoding="utf-8"))["files"]
rows = []
for entry, before in zip(manifest["files"], extracted, strict=True):
    source = Path(manifest["root"]) / entry["relative_path"]
    with source.open("rb") as stream:
        digest = hashlib.file_digest(stream, "sha256").hexdigest()
    rows.append({"sample": before["sample"], "bytes": source.stat().st_size,
                 "sha256": digest, "unchanged": digest == before["sha256"]})
result = {"files": rows, "all_unchanged": all(row["unchanged"] for row in rows)}
(OUT / "source-integrity.json").write_text(json.dumps(result, ensure_ascii=False, indent=2), encoding="utf-8")
print(json.dumps(result, ensure_ascii=False))
if not result["all_unchanged"]:
    raise RuntimeError("原資料に抽出時と異なるハッシュがあります。")
