"""現行記事との互換性と、実記事に基づく提案の形式をローカルで検査する。"""
from copy import deepcopy
from pathlib import Path
from collections import Counter
import hashlib
import json
import re
import sys

ROOT = Path(__file__).resolve().parents[3]
OUT = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT / "info-hive-wiki/skills/info-hive/scripts"))
import wiki_graph_extract as extract
import wiki_graph_lint as lint
import wiki_graph_query as query

LIVE = ROOT / "wiki"
PILOT = OUT / "pilot-v2/wiki"
CANDIDATE = ROOT / "docs/plans/wiki-project-ontology-2026-11-18.yaml"
before = hashlib.sha256((LIVE / "graph/ontology.yaml").read_bytes()).hexdigest()
base = extract.read_ontology(LIVE / "graph/ontology.yaml")
candidate = extract.read_ontology(CANDIDATE)
pages = extract.collect_pages(LIVE)

def compile_pages(pages, ontology):
    diagnostics = []
    nodes, ids, aliases = extract.build_nodes(pages, ontology, diagnostics)
    edges = extract.build_edges(pages, ids, diagnostics)
    return nodes, aliases, edges, diagnostics

bn, ba, be, bd = compile_pages(pages, base)
cn, ca, ce, cd = compile_pages(pages, candidate)
assert (bn, ba, be, bd) == (cn, ca, ce, cd), "候補 YAML だけで現行記事の解釈が変わった"
baseline_lint = lint.lint(pages, base)
candidate_live_lint = lint.lint(pages, candidate)
assert baseline_lint == candidate_live_lint
assert all(not values for values in candidate_live_lint.values() if isinstance(values, list))

for typ, definition in base["node_types"].items():
    assert candidate["node_types"][typ] == definition
for pred, definition in base["predicates"].items():
    if pred == "depends_on":
        for side in ("subject_types", "object_types"):
            assert candidate["predicates"][pred][side] == definition[side] + ["component", "release"]
    else:
        assert candidate["predicates"][pred] == definition

pilot_pages = extract.collect_pages(PILOT)
pilot_lint = lint.lint(pilot_pages, candidate)
assert all(not values for values in pilot_lint.values() if isinstance(values, list)), pilot_lint["summary"]
pn, pa, pe, pd = compile_pages(pilot_pages, candidate)
assert not pd, pd
extract.write_sqlite(PILOT / "graph", pn, pa, pe)

registry = json.loads((OUT / "evidence_and_pilot.json").read_text(encoding="utf-8"))
for e in registry["evidence"]:
    p = ROOT / e["path"]
    assert hashlib.sha256(p.read_bytes()).hexdigest() == e["sha256"]
    assert e["quote"] in p.read_text(encoding="utf-8")
source_text = {p["slug"]: p["body"] for p in pilot_pages if p["meta"].get("type") == "source"}
typed = [e for e in pe if e["extraction_method"] == "explicit_graph_frontmatter"]
assert len(typed) == 38, Counter(e["extraction_method"] for e in pe)
for e in typed:
    assert e["source"] in source_text and e["evidence"] in source_text[e["source"]]
    assert e["confidence"] and e["status"] and e["extras"].get("notes")

# 受け入れるべきでない型・参照・根拠の欠落を、既存 lint が検出するかを確認する。
negative = []
def mutate(name, node_id, index, field, value, bucket):
    altered = deepcopy(pilot_pages)
    p = next(p for p in altered if p["meta"].get("graph", {}).get("node_id") == node_id)
    p["meta"]["graph"]["relationships"][index][field] = value
    result = lint.lint(altered, candidate)
    assert result[bucket], (name, result["summary"])
    negative.append({"case": name, "detected_by": bucket, "findings": result[bucket]})

mutate("評価を修正の主語にできない", "evaluation:rag-051-pdf-direct", 0, "predicate", "fixes", "subject_type_mismatch")
mutate("出荷の目的語は変更に限る", "release:rag-0.5.1", 1, "object", "component:rag-pdf-reader", "object_type_mismatch")
mutate("存在しない対象を指さない", "change:rag-pdf-prefix-1024", 1, "object", "issue:missing", "broken_object_refs")
mutate("出典のない型付き関係を採らない", "change:rag-pdf-prefix-1024", 1, "source", "", "missing_source_field")
mutate("引用のない型付き関係を採らない", "change:rag-pdf-prefix-1024", 1, "evidence", "", "missing_evidence")

# これは未実装の意味の検査の確認。通常 lint が真実性を保証しないことを明示する。
semantic_counterexample = deepcopy(pilot_pages)
p = next(p for p in semantic_counterexample if p["meta"].get("graph", {}).get("node_id") == "change:rag-pdf-prefix-1024")
p["meta"]["graph"]["relationships"][1]["evidence"] = "この記事に存在しない、しかし空ではない引用"
unchecked = lint.lint(semantic_counterexample, candidate)
assert not unchecked["missing_evidence"]

results = {}
def check_query(key, subject, predicate, expected):
    result = query.run_query(PILOT, "edges", subject=subject, predicate=predicate)
    actual = sorted(e["object"] for e in result["edges"])
    assert actual == sorted(expected), (key, result)
    results[key] = result

check_query("rag-051-delivers", "release:rag-0.5.1", "delivers", ["change:rag-pdf-prefix-1024"])
check_query("pdf-fix", "change:rag-pdf-prefix-1024", "fixes", ["issue:rag-pdf-prefix-rejected"])
check_query("sonnet-choice", "decision:ingest-sonnet-20261113", "selects", ["release:claude-sonnet-5.5"])
check_query("sonnet-reason", "decision:ingest-sonnet-20261113", "motivated_by", ["evaluation:ingest-models-20261113"])
check_query("sonnet-split", "decision:web-raw-split-20261114", "selects", ["release:claude-sonnet-5.5"])
check_query("youtube-implementation", "change:wiki-youtube-v0230", "implements", ["decision:adr-0027-captions"])
check_query("youtube-tool-choice", "decision:adr-0027-captions", "selects", ["product:yt-dlp"])
check_query("pinned-dependency", "release:wiki-0.23.0", "depends_on", ["release:yt-dlp-2026.8.19"])
check_query("versioned-issue", "issue:rag-pdf-prefix-rejected", "affects", ["release:rag-0.5.0"])
check_query("document-change", "change:rag-header-wording-v052", "changes", ["artifact:" + key for key in ("rag-readme", "rag-changelog", "rag-index-comments", "rag-v051-release-notes", "dev-adr-0013")])
check_query("query-document-change", "change:wiki-youtube-confidence-v0230", "changes", ["artifact:wiki-query-confidence"])
check_query("lesson-scope", "concept:ingestに使うモデル", "applies_to", ["component:wiki-web-raw"])
family = query.run_query(PILOT, "facts", about="product:yt-dlp")
assert any(e["predicate"] == "release_of" and e["subject"] == "release:yt-dlp-2026.8.19" for e in family["inbound"])
results["yt-dlp-version-family"] = family
for n in pn:
    if n["node_type"] == "release":
        owners = [e["object"] for e in typed if e["subject"] == n["id"] and e["predicate"] == "release_of"]
        assert len(owners) == 1, (n["id"], owners)
assert before == hashlib.sha256((LIVE / "graph/ontology.yaml").read_bytes()).hexdigest()
existing_original = (LIVE / "concepts/ingestに使うモデル.md").read_text(encoding="utf-8")
existing_candidate = (PILOT / "concepts/ingestに使うモデル.md").read_text(encoding="utf-8")
assert existing_candidate.count("# /wiki:ingest に使うモデル") == 1
marker = existing_original.index("\n---", 4)
assert existing_candidate.startswith(existing_original[:marker])
assert existing_candidate.endswith(existing_original[marker:])
assert not any(n["id"] == "evaluation:youtube-impl-reviews-17" for n in pn)
document = (ROOT / "docs/plans/wiki-project-ontology-2026-11-18.md").read_text(encoding="utf-8")
example = re.search(r"```yaml\n(.*?)\n```", document, re.S)[1]
example_meta, _ = extract.parse_frontmatter(example + "\n\n")
sample_page = next(p for p in pilot_pages if p["meta"].get("graph", {}).get("node_id") == "change:rag-pdf-prefix-1024")
assert example_meta["graph"] == sample_page["meta"]["graph"]
inventory = json.loads((OUT / "corpus_inventory.json").read_text(encoding="utf-8"))
assert all(hashlib.sha256((ROOT / row["path"]).read_bytes()).hexdigest() == row["sha256"] for row in inventory["pages"])

record = {
    "date": "2026-11-18", "candidate": CANDIDATE.relative_to(ROOT).as_posix(),
    "live_ontology_sha256_before": before, "live_ontology_unchanged": True, "corpus_snapshot_still_matches": True,
    "current_corpus": {"pages": len(pages), "nodes": len(cn), "edges": len(ce),
        "predicates": dict(Counter(e["predicate"] for e in ce)),
        "typed_edges": len([e for e in ce if e["extraction_method"] == "explicit_graph_frontmatter"])},
    "compatibility": {"identical_compiled_graph": True, "identical_graph_lint": True,
        "preserved_node_types": len(base["node_types"]), "preserved_predicates": len(base["predicates"]),
        "depends_on_addition": "subject_types/object_types に component と release を追加。既存の組はすべて保つ。"},
    "pilot": {"pages": len(pilot_pages), "nodes": len(pn), "typed_edges": len(typed),
        "predicate_coverage": sorted({e["predicate"] for e in typed}), "graph_lint": pilot_lint["summary"],
        "all_quotes_present": True, "all_required_fields_present": True, "existing_concept_targeted_patch_only": True,
        "aggregate_reviews_not_promoted_to_final_release_evaluation": True,
        "every_release_has_exactly_one_product_in_pilot": True, "published_example_matches_pilot": True,
        "limits": "構造 lint/型付き抽出の試料。wiki 全体の構造 lint には索引/raw/全リンクの複製が必要。意味・最新版・成功は未証明。"},
    "negative_cases": negative, "queries": results,
    "known_unchecked": {"nonexistent_quote_accepted_by_ordinary_lint": True,
        "additional_policies": ["循環", "関係ごとの必須欄の欠落の一部", "同じ型の別の対象の誤参照", "適用範囲", "評価の成功", "ソースの新旧・節内の矛盾"]},
    "input_versions": [{"path": str(p.relative_to(ROOT)).replace("\\", "/"),
        "sha256": hashlib.sha256(p.read_bytes()).hexdigest()} for p in [CANDIDATE, *[ROOT / "info-hive-wiki/skills/info-hive/scripts" / name for name in ("wiki_graph_extract.py", "wiki_graph_lint.py", "wiki_graph_query.py")]]],
}
(OUT / "verification.json").write_text(json.dumps(record, ensure_ascii=False, indent=2, default=str) + "\n", encoding="utf-8")
print(json.dumps({k: record[k] for k in ("current_corpus", "compatibility", "pilot", "live_ontology_unchanged")}, ensure_ascii=False, indent=2))
