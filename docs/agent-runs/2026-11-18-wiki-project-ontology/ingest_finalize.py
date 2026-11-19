"""保存済み設計書を原本として登録し、索引と既存記事を部分更新する。"""
from pathlib import Path
import hashlib
import json

root = Path(__file__).resolve().parents[3]
run = Path(__file__).resolve().parent
slug = "プロジェクト用オントロジーの設計-2026-11-18"
source = root / "docs/plans/wiki-project-ontology-2026-11-18.md"
raw = root / f"raw/{slug}.md"
if raw.exists():
    assert raw.read_bytes() == source.read_bytes()
else:
    raw.write_bytes(source.read_bytes())
for name in ("オントロジーの記述例", "オントロジーと知識グラフの役割"):
    path = root / f"wiki/concepts/{name}.md"
    contents = path.read_text(encoding="utf-8")
    line = next(line for line in contents.splitlines() if line.startswith("sources: "))
    if slug not in line:
        updated = line[:-1] + f', "{slug}"]'
        path.write_text(contents.replace(line, updated, 1), encoding="utf-8", newline="")
index = root / "wiki/index.md"
contents = index.read_text(encoding="utf-8")
entries = [
    ("## ソース", f"- [[{slug}]]: 開発知識の種類・関係・版・評価を定めた設計第2版と、検証・レビューの記録。未適用の提案\n"),
    ("## コンセプト", "- [[プロジェクト用オントロジーの設計案]]: 構成要素・版・変更・問題・評価・管理対象物を追加し、根拠付きで追跡する未適用の設計案\n"),
]
for heading, entry in entries:
    if entry.strip() not in contents:
        assert heading + "\n" in contents, heading
        contents = contents.replace(heading + "\n", heading + "\n\n" + entry, 1)
index.write_text(contents, encoding="utf-8", newline="")
log = root / "wiki/log.md"
entry = f"\n## [2026-11-18] ingest | info-hive のプロジェクト用オントロジー設計\n   原本は設計第2版の Markdown。[[{slug}]] と [[プロジェクト用オントロジーの設計案]] を作成し、一般例と役割の2ページを部分更新した。本番の ontology と試料の型付き関係は適用していない。\n"
contents = log.read_text(encoding="utf-8")
if entry.strip() not in contents:
    log.write_text(contents + entry, encoding="utf-8", newline="")
(run / "ingest-record.json").write_text(json.dumps({"source": str(source), "raw": str(raw),
    "sha256": hashlib.sha256(raw.read_bytes()).hexdigest(), "raw_matches_design": True,
    "ontology_sha256": hashlib.sha256((root / "wiki/graph/ontology.yaml").read_bytes()).hexdigest()}, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
print("原本・既存ページの出典・索引・ログを更新した")
