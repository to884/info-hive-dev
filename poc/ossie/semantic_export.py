"""検証済み意味スナップショットの SQLite・Ossie 書き出しと照会。"""

from contextlib import closing
from datetime import date
import json
from pathlib import Path
import sqlite3

import export_wiki_graph as legacy
from semantic_records import TABLES


def table_name(table):
    return f"sem_{table}"


def fields_for(table):
    return {"id": "String", "wiki_id": "String", **TABLES[table][1]}


def documents():
    ontology, core, mapping = legacy.documents()
    ontology.update(name="Info Hive Wiki Semantics", ontology=[],
                    description="実体、主張の版、根拠、履歴、旧 ID との対応。")
    core.update(name="Info Hive Wiki Semantic Data", datasets=[], relationships=[])
    mapping.update(name="Info Hive Wiki Semantic Mapping", concept_mappings=[])
    mapping["ontology_ref"]["name"] = ontology["name"]
    mapping["semantic_model_ref"]["name"] = core["name"]
    locations = {concept: table_name(table) for table, (concept, _) in TABLES.items()}
    for table, (concept, _) in TABLES.items():
        name = table_name(table)
        fields = fields_for(table)
        core["datasets"].append({
            "name": name, "source": name, "primary_key": ["id"],
            "fields": [{"name": field, "datatype": "String",
                        "expression": {"sql": f"source.{legacy.ident(field)}"}} for field in fields],
        })
        for field, target in fields.items():
            if target != "String":
                core["relationships"].append({
                    "name": f"{name}_{field}", "from": name, "to": locations[target],
                    "from_columns": [field], "to_columns": ["id"],
                })
        ontology["ontology"].append({
            "concept": concept, "type": "EntityType", "identify_by": ["id"],
            "relationships": [legacy.relation(field, target) for field, target in fields.items()],
        })
        identity = legacy.identity(name, "id")
        mapping["concept_mappings"].append({
            "concept": concept, "object_mappings": [identity],
            "link_mappings": [{"object_mapping": identity, "children": [
                legacy.attribute(name, field, target) for field, target in fields.items() if field != "id"
            ]}],
        })
    return ontology, core, mapping


def save_data(path, rows):
    with closing(sqlite3.connect(path)) as db, db:
        db.execute("PRAGMA foreign_keys = ON")
        destinations = {concept: table_name(table) for table, (concept, _) in TABLES.items()}
        for table in TABLES:
            columns = []
            for field, target in fields_for(table).items():
                definition = f"{legacy.ident(field)} TEXT"
                if field == "id":
                    definition += " NOT NULL PRIMARY KEY"
                elif field == "wiki_id":
                    definition += " NOT NULL"
                elif target != "String":
                    definition += f" REFERENCES {destinations[target]}(id) DEFERRABLE INITIALLY DEFERRED"
                columns.append(definition)
            db.execute(f"CREATE TABLE {table_name(table)} ({', '.join(columns)})")
        for table in TABLES:
            fields = fields_for(table)
            placeholders = ", ".join("?" for _ in fields)
            db.executemany(f"INSERT INTO {table_name(table)} VALUES ({placeholders})",
                           (tuple(row[field] for field in fields) for row in rows[table]))


def write_release(output, bundle, checkout=None):
    manifest, rows = bundle
    output.mkdir()
    ontology, core, mapping = documents()
    for name, value in zip((legacy.ONTOLOGY, legacy.MODEL, legacy.MAPPING), (ontology, core, mapping)):
        legacy.save_json(output / name, value)
    with (output / "records.jsonl").open("w", encoding="utf-8", newline="\n") as stream:
        for table, values in rows.items():
            for row in values:
                stream.write(json.dumps({"table": table, **row}, ensure_ascii=False, sort_keys=True) + "\n")
    db_path = output / legacy.DATA
    save_data(db_path, rows)
    expected = set()
    with closing(legacy.readonly(db_path)) as db:
        for table, (concept, _) in TABLES.items():
            columns = fields_for(table)
            if legacy.read_rows(db, table_name(table), tuple(columns), ("id",)) != rows[table]:
                raise ValueError(f"{table} の書き出し行が入力と一致しません")
            for row in rows[table]:
                expected.update((concept, row["id"], field, target, row[field])
                                for field, target in columns.items() if row[field] is not None)
        core = json.loads((output / legacy.MODEL).read_text(encoding="utf-8"))
        mapping = json.loads((output / legacy.MAPPING).read_text(encoding="utf-8"))
        if legacy.mapped_facts(db, core, mapping) != expected:
            raise ValueError("意味モデルの列参照が期待する値と一致しません")
    report = {**manifest, "rows": {table: len(values) for table, values in rows.items()},
              "local_mapped_facts": len(expected),
              "official_validation": legacy.validate_official(output, checkout) if checkout else {"state": "not_run"}}
    legacy.save_json(output / "release.json", report)
    return report


def contains_day(intervals, day):
    return any(start <= day and (end is None or day < end) for start, end in intervals)


def customer_rule_compatible(old, new):
    def rule(value):
        predicates = value.get("predicates", {})
        if isinstance(predicates, list):
            predicates = dict.fromkeys(predicates)
        return "customer_of" in predicates, predicates.get("customer_of")

    extras = lambda value: {name: item for name, item in value.items() if name != "predicates"}
    return rule(old)[0] and rule(old) == rule(new) and extras(old) == extras(new)


def customer_counts(path: Path, definition_id: str, wiki_id: str, product_id: str, day: str) -> dict:
    """公開版の試験用照会。主張数・根拠数・実体数を独立に数える。"""
    if date.fromisoformat(day).isoformat() != day:
        raise ValueError("集計日は YYYY-MM-DD で指定してください")
    release = json.loads(path.with_name("release.json").read_text(encoding="utf-8"))
    if (release["wiki_id"], release["definition_id"]) != (wiki_id, definition_id):
        raise ValueError("wiki または定義の版がスナップショットと一致しません")
    with closing(legacy.readonly(path)) as db:
        entity = db.execute(
            "SELECT 1 FROM sem_entities WHERE id = ? AND wiki_id = ? AND entity_type = 'product'",
            (product_id, wiki_id),
        ).fetchone()
        definition = db.execute(
            "SELECT rules_json FROM sem_definitions WHERE id = ? AND wiki_id = ?", (definition_id, wiki_id),
        ).fetchone()
        if not entity or not definition:
            raise ValueError("指定した wiki の製品または定義がありません")
        rules = json.loads(definition[0])
        customers = db.execute("""
            SELECT c.id, r.id, c.subject_entity_id, c.polarity, r.state, r.intervals_json, d.rules_json, c.qualifier
            FROM sem_claims c JOIN sem_heads h ON h.claim_id = c.id
            JOIN sem_revisions r ON r.id = h.revision_id JOIN sem_definitions d ON d.id = r.definition_id
            WHERE c.wiki_id = ? AND c.object_entity_id = ? AND c.predicate = 'customer_of'
        """, (wiki_id, product_id)).fetchall()

        contrary = list(db.execute("""
            SELECT CASE WHEN ref.from_id = r.id THEN ref.to_id ELSE ref.from_id END, r.state, r.intervals_json
            FROM sem_references ref JOIN sem_heads h ON h.revision_id = ref.from_id
            JOIN sem_heads j ON j.revision_id = ref.to_id
            JOIN sem_revisions r ON r.id IN (ref.from_id, ref.to_id)
            JOIN sem_claims c ON c.id = r.claim_id
            WHERE ref.wiki_id = ? AND ref.kind = 'contradicts' AND c.polarity = 'negative'
              AND c.object_entity_id = ? AND r.state IN ('accepted', 'candidate', 'disputed')
        """, (wiki_id, product_id)))
        holds = db.execute("""
            SELECT h.kind, h.candidates_json FROM sem_holds h
            WHERE h.wiki_id = ? AND (h.product_id IS NULL OR h.product_id = ?)
              AND NOT EXISTS (SELECT 1 FROM sem_decisions d WHERE d.hold_id = h.id AND d.state = 'resolved')
        """, (wiki_id, product_id)).fetchall()
        reasons = {kind for kind, _ in holds}
        pending = {revision for kind, candidates in holds if kind == "reference_pending"
                   for revision in json.loads(candidates)}
        negative = {}
        for _, _, subject, polarity, state, interval_json, old_rules, qualifier in customers:
            if polarity == "negative" and customer_rule_compatible(json.loads(old_rules), rules):
                negative.setdefault((subject, qualifier), []).append((state, interval_json))
        linked = {}
        for target, state, interval_json in contrary:
            linked.setdefault(target, []).append((state, interval_json))
        entities, claims, evidence = set(), set(), set()
        for claim_id, revision_id, subject, polarity, state, interval_json, old_rules, qualifier in customers:
            if polarity != "positive" or state in {"withdrawn", "superseded"}:
                continue
            intervals = json.loads(interval_json)
            if intervals and not contains_day(intervals, day):
                continue
            opposition = linked.get(revision_id, []) + negative.get((subject, qualifier), [])
            doubt = set()
            for opposing_state, opposing_json in opposition:
                opposing_intervals = json.loads(opposing_json)
                if opposing_state in {"candidate", "disputed", "accepted"} and (
                    not opposing_intervals or contains_day(opposing_intervals, day)
                ):
                    if opposing_state == "candidate" or not opposing_intervals:
                        doubt.add("reference_pending")
                    else:
                        doubt.add("disputed")
            if not customer_rule_compatible(json.loads(old_rules), rules):
                reasons.add("migration_pending")
            elif state == "candidate":
                reasons.add("claim_candidate")
            elif state == "disputed":
                reasons.add("disputed")
            elif doubt or revision_id in pending:
                reasons.update(doubt | ({"reference_pending"} if revision_id in pending else set()))
            elif not intervals:
                reasons.add("unknown_valid_time")
            elif state == "accepted":
                entities.add(subject)
                claims.add(claim_id)
                evidence.update(row[0] for row in db.execute("""
                    SELECT evidence_id FROM sem_supports WHERE revision_id = ? AND kind = 'supports'
                """, (revision_id,)))
    return {"customers": len(entities), "claims": len(claims), "evidence": len(evidence),
            "customer_ids": sorted(entities), "limitations": sorted(reasons)}
