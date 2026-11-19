"""段階1・2の出力を DuckDB で消費し、SQLite の期待値と照合する。"""

from __future__ import annotations

import argparse
from contextlib import closing
from hashlib import sha256
import json
from pathlib import Path
import shutil
import sqlite3
import subprocess
import sys
from tempfile import TemporaryDirectory

import duckdb

import export_wiki_graph as legacy
from ossie_adapter import ConstraintError, Issue, OssieAdapter, read_json
from ossie_customers import evaluate_customer, metrics_document, set_views
from semantic_export import customer_counts
from semantic_records import TABLES


FILES = (legacy.ONTOLOGY, legacy.MODEL, legacy.MAPPING, legacy.DATA)
METRICS = "customers.semantic_model.json"
RELEASES = ("v1", "v1-renamed", "v2", "v3", "other")
CASES = (
    ("v1", "製品A", "2025-06-01", "product_a"),
    ("v1", "製品A", "2025-01-01", None),
    ("v1", "製品A", "2024-12-31", None),
    ("v1", "製品A", "2025-07-01", "product_a_after_period"),
    ("v1", "製品B", "2025-06-01", "product_b"),
    ("v1", "製品C", "2025-06-01", "product_c"),
    ("v1-renamed", "製品A", "2025-06-01", "product_a_after_rename"),
    ("v2", "製品B", "2025-06-01", "product_b_v2"),
    ("v3", "製品A", "2025-06-01", "product_a_v3"),
    ("v3", "製品B", "2025-06-01", "product_b_v3"),
    ("other", "製品A", "2025-06-01", "other_product_a"),
)


def compare(actual, expected, label):
    if actual != expected:
        raise ValueError(f"{label} の実行値が SQLite の期待値と異なります")


def sqlite_typed_links(path, semantic):
    """Mapping は使わず、SQLite の元列と外部キーから期待する関係を読む。"""
    with closing(legacy.readonly(path)) as db:
        if semantic:
            concepts = {f"sem_{table}": concept for table, (concept, _) in TABLES.items()}
            columns = [
                (table, concept, fk[3], concepts[fk[2]])
                for table, concept in concepts.items()
                for fk in db.execute(f"PRAGMA foreign_key_list({legacy.ident(table)})")
            ]
        else:
            columns = [("wiki_edges", "WikiEdge", field, target) for field, target in legacy.TYPED_LINKS.items()]
        return {
            (concept, id, field, target, value)
            for table, concept, field, target in columns
            for id, value in db.execute(
                f"SELECT id, {legacy.ident(field)} FROM {legacy.ident(table)} WHERE {legacy.ident(field)} IS NOT NULL"
            )
        }


def check_bundle(folder, *, semantic, label=None, metrics_path=None, previous=None):
    with OssieAdapter() as adapter:
        adapter.load(folder)
        links = set(adapter.db.execute("SELECT * FROM links WHERE target_kind <> 'String'").fetchall())
        expected = sqlite_typed_links(folder / legacy.DATA, semantic)
        compare(links, expected, f"{label or folder.name} の型付きリンク")
        counts = {"typed_links": len(links), "mapped_facts": adapter.db.execute("SELECT count(*) FROM links").fetchone()[0]}
        if label in RELEASES:
            set_views(adapter)
            counts["customers"] = check_customers(adapter, folder, label, metrics_path, previous)
        return counts


def check_customers(adapter, folder, label, metrics_path, previous):
    release = read_json(folder / "release.json")
    wiki = release["wiki_id"]
    definition = release["definition_id"]
    db_path = folder / legacy.DATA
    result = {}
    for case, product, day, historical in CASES:
        if case != label:
            continue
        with closing(legacy.readonly(db_path)) as db:
            (product_id,) = db.execute("""
                SELECT id FROM sem_entities WHERE wiki_id = ? AND name = ? AND entity_type = 'product'
            """, (wiki, product)).fetchone()
        expected = customer_counts(db_path, definition, wiki, product_id, day)
        if historical:
            compare(expected, previous["counts"][historical], "段階1・2で固定した SQLite の集計")
        else:
            compare(expected["customers"], int(day == "2025-01-01"), "有効期間の開始境界")
        actual, joined = evaluate_customer(adapter, metrics_path, wiki, definition, product_id, day)
        compare(actual, expected, f"{label} の {product}（{day}）")
        if historical == "product_a":
            # 1 件の主張に根拠を2行結合したこと自体も確かめる。
            compare(joined, 2, "根拠を結合した行数")
            compare([actual[k] for k in ("customers", "claims", "evidence")], [1, 1, 2], "結合後の各指標")
        result[f"{product}/{day}"] = {"sqlite": expected, "duckdb": actual, "joined_rows": joined}
    return result


def clone(source, target):
    target.mkdir()
    for name in FILES:
        shutil.copyfile(source / name, target / name)


def make_fixtures(source, output):
    valid = output / "constrained"
    invalid = output / "invalid-data"
    broken = output / "invalid-mapping"
    clone(source, valid)
    ontology_file = valid / legacy.ONTOLOGY
    ontology = read_json(ontology_file)
    concepts = {entry["concept"]: entry for entry in ontology["ontology"]}
    concepts["WikiEvidenceLink"]["requires"] = ["WikiEvidenceLink.evidence_id"]
    relation = next(item for item in concepts["WikiClaimHead"]["relationships"] if item["name"] == "revision_id")
    relation["multiplicity"] = "OneToOne"
    legacy.save_json(ontology_file, ontology)

    clone(valid, invalid)
    with closing(sqlite3.connect(invalid / legacy.DATA)) as db, db:
        rows = db.execute("SELECT id FROM sem_supports ORDER BY id LIMIT 2").fetchall()
        missing, wrong = (row[0] for row in rows)
        db.execute("UPDATE sem_supports SET evidence_id = NULL WHERE id = ?", (missing,))
        entity = db.execute("SELECT min(id) FROM sem_entities").fetchone()[0]
        db.execute("UPDATE sem_supports SET evidence_id = ? WHERE id = ?", (entity, wrong))
        db.execute("""
            INSERT INTO sem_heads (id, wiki_id, claim_id, revision_id)
            SELECT 'stage3_duplicate_head', wiki_id, claim_id, revision_id FROM sem_heads ORDER BY id LIMIT 1
        """)

    clone(valid, broken)
    mapping = read_json(broken / legacy.MAPPING)
    mapping["concept_mappings"][0]["object_mappings"][0]["referent_mappings"][0]["expression"] = (
        "sem_definitions.stage3_missing_field"
    )
    legacy.save_json(broken / legacy.MAPPING, mapping)
    return valid, invalid, broken


def sqlite_violations(path):
    with closing(legacy.readonly(path)) as db:
        missing = db.execute("SELECT id FROM sem_supports WHERE evidence_id IS NULL").fetchall()
        wrong = db.execute("""
            SELECT s.id FROM sem_supports s LEFT JOIN sem_evidence e ON e.id = s.evidence_id
            WHERE s.evidence_id IS NOT NULL AND e.id IS NULL
        """).fetchall()
        duplicates = db.execute("""
            SELECT id FROM sem_heads WHERE revision_id IN (
                SELECT revision_id FROM sem_heads GROUP BY revision_id HAVING count(*) > 1
            )
        """).fetchall()
    return sorted(
        [Issue("requires", "WikiEvidenceLink", "evidence_id", id) for (id,) in missing]
        + [Issue("missing_target", "WikiEvidenceLink", "evidence_id", id) for (id,) in wrong]
        + [Issue("core_reference", "sem_supports", "sem_supports_evidence_id", id) for (id,) in wrong]
        + [Issue("one_to_one", "WikiClaimHead", "revision_id", id) for (id,) in duplicates]
    )


def reject_broken(operation, message):
    try:
        operation()
    except ValueError as error:
        if message not in str(error):
            raise
        return "rejected"
    raise ValueError(f"壊れた Mapping を受理しました: {message}")


def verify_violations(valid, invalid, broken):
    with OssieAdapter() as adapter:
        adapter.load(valid)
    expected = sqlite_violations(invalid / legacy.DATA)
    compare(sorted(issue.code for issue in expected),
            ["core_reference", "missing_target", "one_to_one", "one_to_one", "requires"],
            "制約違反の試験データ")
    with OssieAdapter() as adapter:
        try:
            adapter.load(invalid)
        except ConstraintError as error:
            compare(error.issues, expected, "実データの制約違反")
        else:
            raise ValueError("制約違反があるデータを受理しました")
    with OssieAdapter() as adapter:
        broken_mapping = reject_broken(lambda: adapter.load(broken), "stage3_missing_field")
    return {"valid_data": "passed", "invalid_data": "rejected", "broken_mapping": broken_mapping,
            "matching_issues": [issue._asdict() for issue in expected]}


def fingerprint(bundles, synthetic):
    paths = [folder / name for folder in bundles.values() for name in FILES]
    paths += [bundles[label] / "release.json" for label in RELEASES]
    paths.append(synthetic / legacy.REPORT)
    return {path: sha256(path.read_bytes()).hexdigest() for path in paths}


def official(bundles, valid, invalid, broken, metrics_path, checkout):
    if checkout is None:
        return {"state": "not_run"}
    results = {label: legacy.validate_official(folder, checkout) for label, folder in bundles.items()}
    results["constrained"] = legacy.validate_official(valid, checkout)
    results["invalid_data_same_documents"] = legacy.validate_official(invalid, checkout)
    check = subprocess.run(
        ["uv", "run", "--no-project", str(checkout / "validation/validate.py"), "--schema",
         str(checkout / "core-spec/ossie-schema.json"), str(metrics_path)],
        capture_output=True, encoding="utf-8",
    )
    if check.returncode:
        raise ValueError(check.stdout + check.stderr)
    results["metrics"] = {"state": "passed", "documents": [METRICS]}
    return {"state": "passed", "positive": results, "broken_mapping": reject_broken(
        lambda: legacy.validate_official(broken, checkout), "stage3_missing_field",
    )}


def run(semasynth, synthetic, output, checkout=None):
    semasynth, synthetic = semasynth.resolve(strict=True), synthetic.resolve(strict=True)
    output = output.resolve()
    if output.exists():
        raise FileExistsError(f"新しい出力先を指定してください: {output}")
    if any(output.is_relative_to(root) for root in (semasynth, synthetic)):
        raise ValueError("入力の外に出力先を指定してください")
    if checkout is not None:
        checkout = checkout.resolve(strict=True)
    bundles = {"semasynth_legacy": semasynth / "legacy", "semasynth_semantic": semasynth / "semantic",
               **{name: synthetic / name for name in RELEASES}}
    before = fingerprint(bundles, synthetic)
    previous = read_json(synthetic / legacy.REPORT)
    output.parent.mkdir(parents=True, exist_ok=True)
    with TemporaryDirectory(prefix=".ossie-consume-", dir=output.parent) as directory:
        stage = Path(directory) / "result"
        stage.mkdir()
        metrics = stage / METRICS
        legacy.save_json(metrics, metrics_document())
        fixtures = make_fixtures(synthetic / "v1", stage)
        runtime = {label: check_bundle(folder, semantic=label != "semasynth_legacy", label=label,
                                      metrics_path=metrics, previous=previous) for label, folder in bundles.items()}
        constraints = verify_violations(*fixtures)
        report = {
            "engine": {"adapter": "info-hive local subset", "duckdb": duckdb.__version__,
                       "external_access": False},
            "official_validation": official(bundles, *fixtures, metrics, checkout),
            "execution": {"bundles": runtime, "constraints": constraints},
            "input_files_unchanged": fingerprint(bundles, synthetic) == before,
        }
        if not report["input_files_unchanged"]:
            raise ValueError("照合中に入力が変更されました")
        legacy.save_json(stage / legacy.REPORT, report)
        if output.exists():
            raise FileExistsError(f"出力先がすでにあります: {output}")
        stage.rename(output)
    return report


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--semasynth", type=Path, required=True, help="段階1・2の SemaSynth 出力")
    parser.add_argument("--synthetic", type=Path, required=True, help="段階1・2の合成 wiki 出力")
    parser.add_argument("--output", type=Path, required=True, help="入力外の新しい出力ディレクトリ")
    parser.add_argument("--ossie-checkout", type=Path, help="公式検証器を実行する固定改訂のチェックアウト")
    args = parser.parse_args()
    try:
        report = run(args.semasynth, args.synthetic, args.output, args.ossie_checkout)
    except (OSError, ValueError, KeyError, sqlite3.Error, duckdb.Error) as error:
        print(f"消費試験に失敗しました: {error}", file=sys.stderr)
        return 1
    print(json.dumps(report, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    sys.exit(main())
