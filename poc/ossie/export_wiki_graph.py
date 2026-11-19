"""wiki のグラフ SQLite を、Apache Ossie の文書とデータに書き出す。"""

from __future__ import annotations

import argparse
from collections import Counter, defaultdict
from collections.abc import Iterator
from contextlib import closing, suppress
import json
import os
from pathlib import Path
import sqlite3
import subprocess
import sys
import unicodedata


VERSION = "0.3.0.dev0"
OSSIE_COMMIT = "0f458dee0718b701930bf4597e1d84e427f0c8fc"
ONTOLOGY = "wiki.ontology.json"
MODEL = "wiki.semantic_model.json"
MAPPING = "wiki.mapping.json"
DATA = "wiki-data.sqlite"
REPORT = "verification.json"

SOURCE_COLUMNS = {
    "nodes": ("id", "slug", "title", "page_type", "node_type", "kind", "path",
              "created", "updated", "metadata_json"),
    "edges": ("id", "subject", "predicate", "object", "source", "evidence", "confidence",
              "status", "extraction_method", "page", "metadata_json"),
    "aliases": ("alias", "node_id"),
}
HISTORY_FIELDS = ("valid_from", "valid_to", "notes", "raw_ref", "contradicts", "supersedes")
REFERENCE_FIELDS = ("source", "contradicts", "supersedes")
EDGE_FIELDS = ("object_kind", "subject_node_id", "object_node_id", "source_node_id",
               *HISTORY_FIELDS, "contradicts_edge_id", "contradicts_node_id",
               "supersedes_edge_id", "supersedes_node_id",
               *(f"{field}_resolution" for field in REFERENCE_FIELDS))
EXPORT_COLUMNS = {**SOURCE_COLUMNS, "edges": (*SOURCE_COLUMNS["edges"], *EDGE_FIELDS)}
KEYS = {"nodes": ("id",), "edges": ("id",), "aliases": ("alias", "node_id")}
NAMES = {"nodes": "wiki_nodes", "edges": "wiki_edges", "aliases": "wiki_aliases"}
TYPED_LINKS = {
    "subject_node_id": "WikiNode",
    "object_node_id": "WikiNode",
    "source_node_id": "WikiNode",
    "contradicts_edge_id": "WikiEdge",
    "contradicts_node_id": "WikiNode",
    "supersedes_edge_id": "WikiEdge",
    "supersedes_node_id": "WikiNode",
}


def ident(name: str) -> str:
    return '"' + name.replace('"', '""') + '"'


def readonly(path: Path) -> sqlite3.Connection:
    return sqlite3.connect(path.resolve(strict=True).as_uri() + "?mode=ro", uri=True)


def read_rows(db: sqlite3.Connection, name: str, columns: tuple[str, ...],
              keys: tuple[str, ...]) -> list[dict]:
    actual = {row[1] for row in db.execute(f"PRAGMA table_info({ident(name)})")}
    if actual != set(columns):
        raise ValueError(f"{name} の列が想定と異なります: {sorted(actual ^ set(columns))}")
    selection = ", ".join(map(ident, columns))
    order = ", ".join(map(ident, keys))
    return [
        dict(zip(columns, row))
        for row in db.execute(f"SELECT {selection} FROM {ident(name)} ORDER BY {order}")
    ]


def snapshot(db_path: Path) -> dict[str, list[dict]]:
    with closing(readonly(db_path)) as db:
        db.execute("BEGIN")
        return {
            name: read_rows(db, name, columns, KEYS[name])
            for name, columns in SOURCE_COLUMNS.items()
        }


def metadata(text: str) -> dict:
    value = json.loads(text)
    if not isinstance(value, dict):
        raise ValueError("metadata_json の最上位がオブジェクトではありません")
    return value


def project_edges(rows: dict[str, list[dict]]) -> list[dict]:
    nodes = {row["id"] for row in rows["nodes"]}
    edges = {row["id"] for row in rows["edges"]}
    source_nodes = {row["id"] for row in rows["nodes"] if row["page_type"] == "source"}
    sources = defaultdict(set)
    for node in rows["nodes"]:
        if node["id"] in source_nodes:
            sources[unicodedata.normalize("NFC", node["slug"])].add(node["id"])

    projected = []
    for edge in rows["edges"]:
        extras = metadata(edge["metadata_json"])
        using_raw = edge["predicate"] == "summarizes_raw"
        has_object = not using_raw and edge["object"] in nodes
        record = {
            **edge,
            "object_kind": "raw" if using_raw else ("node" if has_object else "unresolved"),
            "subject_node_id": edge["subject"] if edge["subject"] in nodes else None,
            "object_node_id": edge["object"] if has_object else None,
        }
        for field in HISTORY_FIELDS:
            value = extras.get(field)
            record[field] = value if isinstance(value, str) else None
        for field in REFERENCE_FIELDS:
            value = edge["source"] if field == "source" else extras.get(field)
            has_edge = False
            candidates = set()
            if isinstance(value, str) and value:
                candidates = sources.get(unicodedata.normalize("NFC", value), set()).copy()
                if field != "source":
                    candidates.update({value} & nodes)
                    has_edge = value in edges
                elif edge["extraction_method"] == "frontmatter_sources":
                    # 抽出時にパスや wikilink を解決した結果が、すでに目的語に入っている。
                    candidates = {edge["object"]} & source_nodes
            count = len(candidates) + has_edge
            record[f"{field}_node_id"] = next(iter(candidates)) if count == 1 and candidates else None
            if field != "source":
                record[f"{field}_edge_id"] = value if count == 1 and has_edge else None
            if value is None:
                resolution = None
            elif not isinstance(value, str):
                resolution = "non_string"
            elif count > 1:
                resolution = "ambiguous"
            elif count == 1:
                resolution = "edge" if has_edge else "node"
            else:
                resolution = "unresolved"
            record[f"{field}_resolution"] = resolution
        projected.append(record)
    return projected


def field_ref(dataset: str, column: str) -> str:
    return f"{dataset}.{column}"


def identity(dataset: str, column: str) -> dict:
    return {"referent_mappings": [{"relationship": "id", "expression": field_ref(dataset, column)}]}


def attribute(dataset: str, name: str, target: str = "String") -> dict:
    if target == "String":
        mapping = {"concept": "String", "expression": field_ref(dataset, name)}
    else:
        mapping = {"concept": target, **identity(dataset, name)}
    return {"relationship": name, "object_mapping": mapping}


def relation(name: str, target: str, *, single: bool = True) -> dict:
    value = {"name": name, "roles": [{"concept": target}], "verbalizes": []}
    if single:
        value["multiplicity"] = "ManyToOne"
    return value


def documents() -> tuple[dict, dict, dict]:
    ontology = {
        "version": VERSION,
        "name": "Info Hive Wiki Graph",
        "description": "wiki グラフのノードと、個別の根拠や履歴を持つ関係を写したもの。",
        "ontology": [],
    }
    core = {"version": VERSION, "name": "Info Hive Wiki Graph Data",
            "datasets": [], "relationships": []}
    mapping = {
        "version": VERSION,
        "name": "Info Hive Wiki Graph Mapping",
        "ontology_ref": {"name": ontology["name"], "iri": f"./{ONTOLOGY}"},
        "semantic_model_ref": {"name": core["name"], "iri": f"./{MODEL}"},
        "concept_mappings": [],
    }

    for table, name in NAMES.items():
        core["datasets"].append({
            "name": name, "source": name, "primary_key": list(KEYS[table]),
            "fields": [
                {"name": field, "datatype": "String",
                 "expression": {"sql": f"source.{ident(field)}"}}
                for field in EXPORT_COLUMNS[table]
            ],
        })
    for name, target in TYPED_LINKS.items():
        core["relationships"].append({
            "name": f"edge_{name}", "from": NAMES["edges"],
            "to": NAMES["nodes" if target == "WikiNode" else "edges"],
            "from_columns": [name], "to_columns": ["id"],
        })
    core["relationships"].append({
        "name": "alias_node", "from": NAMES["aliases"], "to": NAMES["nodes"],
        "from_columns": ["node_id"], "to_columns": ["id"],
    })
    for table, concept in (("nodes", "WikiNode"), ("edges", "WikiEdge")):
        table_name = NAMES[table]
        fields = {column: TYPED_LINKS.get(column, "String") for column in EXPORT_COLUMNS[table]}
        definition = {
            "concept": concept, "type": "EntityType", "identify_by": ["id"],
            "relationships": [relation(name, target) for name, target in fields.items()],
        }
        row_identity = identity(table_name, "id")
        rule = {
            "concept": concept, "object_mappings": [row_identity],
            "link_mappings": [{"object_mapping": row_identity, "children": [
                attribute(table_name, field, target) for field, target in fields.items()
                if field != "id"
            ]}],
        }
        if table == "nodes":
            definition["relationships"].append(relation("alias", "String", single=False))
            rule["link_mappings"].append({
                "object_mapping": identity(NAMES["aliases"], "node_id"),
                "children": [attribute(NAMES["aliases"], "alias")],
            })
        ontology["ontology"].append(definition)
        mapping["concept_mappings"].append(rule)
    return ontology, core, mapping


def save_sqlite(path: Path, rows: dict[str, list[dict]]) -> None:
    with closing(sqlite3.connect(path)) as db, db:
        for table, columns in EXPORT_COLUMNS.items():
            name = ident(NAMES[table])
            primary = ", ".join(map(ident, KEYS[table]))
            definitions = ", ".join(
                f"{ident(column)} TEXT{' NOT NULL' if column in KEYS[table] else ''}"
                for column in columns
            )
            db.execute(f"CREATE TABLE {name} ({definitions}, PRIMARY KEY ({primary}))")
            placeholders = ", ".join("?" for _ in columns)
            db.executemany(
                f"INSERT INTO {name} VALUES ({placeholders})",
                (tuple(row[column] for column in columns) for row in rows[table]),
            )


def mapped_facts(db: sqlite3.Connection, core: dict, mapping: dict) -> set[tuple]:
    """PoC が出す単一データセットの列参照を SQLite で評価する。"""
    datasets = {dataset["name"]: dataset for dataset in core["datasets"]}

    def logical_field(expression: str) -> tuple[str, str]:
        table, _, field = expression.partition(".")
        dataset = datasets[table]
        sql = next(item["expression"]["sql"] for item in dataset["fields"]
                   if item["name"] == field)
        return dataset["source"], sql

    facts = set()
    for rule in mapping["concept_mappings"]:
        concept = rule["concept"]
        for object_mapping in rule["object_mappings"]:
            source, sql = logical_field(object_mapping["referent_mappings"][0]["expression"])
            for (key,) in db.execute(f"SELECT {sql} FROM {ident(source)} AS source"):
                facts.add((concept, key, "id", "String", key))
        for link in rule["link_mappings"]:
            source, subject = logical_field(link["object_mapping"]["referent_mappings"][0]["expression"])
            for child in link["children"]:
                obj = child["object_mapping"]
                expression = obj["expression"] if "expression" in obj else obj["referent_mappings"][0]["expression"]
                target_source, value = logical_field(expression)
                if source != target_source:
                    raise ValueError("PoC の試験は同じデータセットの列参照だけを扱います")
                for key, item in db.execute(f"SELECT {subject}, {value} FROM {ident(source)} AS source"):
                    if key is not None and item is not None:
                        facts.add((concept, key, child["relationship"], obj["concept"], item))
    return facts


def expected_facts(rows: dict[str, list[dict]]) -> Iterator[tuple]:
    for table, concept in (("nodes", "WikiNode"), ("edges", "WikiEdge")):
        for row in rows[table]:
            for column, value in row.items():
                if value is not None:
                    yield (concept, row["id"], column, TYPED_LINKS.get(column, "String"), value)
    for row in rows["aliases"]:
        yield ("WikiNode", row["node_id"], "alias", "String", row["alias"])


def save_json(path: Path, value: dict) -> None:
    path.write_text(json.dumps(value, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def verify(output: Path, original: dict, projected: dict) -> dict:
    core = json.loads((output / MODEL).read_text(encoding="utf-8"))
    mapping = json.loads((output / MAPPING).read_text(encoding="utf-8"))
    with closing(readonly(output / DATA)) as db:
        for table, columns in EXPORT_COLUMNS.items():
            actual = read_rows(db, NAMES[table], columns, KEYS[table])
            restored = [{key: row[key] for key in SOURCE_COLUMNS[table]} for row in actual]
            if restored != original[table] or actual != projected[table]:
                raise ValueError(f"{table} の値が入力と一致しません")
        actual = mapped_facts(db, core, mapping)
    expected = set(expected_facts(projected))
    if actual != expected:
        raise ValueError(f"マッピングで算出した関係が一致しません: 不足 {len(expected - actual)}、余分 {len(actual - expected)}")

    edges = projected["edges"]
    metadata_counts = {
        field: sum(metadata(row["metadata_json"]).get(field) is not None for row in edges)
        for field in HISTORY_FIELDS
    }
    groups = Counter((row["subject"], row["predicate"], row["object"]) for row in edges)
    resolutions = {
        field: dict(sorted(Counter(row[f"{field}_resolution"] for row in edges
                                   if row[f"{field}_resolution"] is not None).items()))
        for field in REFERENCE_FIELDS
    }
    for field, counts in resolutions.items():
        total = sum(row["source"] is not None for row in edges) if field == "source" else metadata_counts[field]
        if sum(counts.values()) != total:
            raise ValueError(f"{field} の参照解決結果の件数が一致しません")
    return {
        "ossie_version": VERSION,
        "ossie_commit": OSSIE_COMMIT,
        "exact_snapshot_match": True,
        "mapping_check": "local_column_references",
        "rows": {table: len(rows) for table, rows in original.items()},
        "mapped_facts": len(actual),
        "predicates": dict(sorted(Counter(row["predicate"] for row in edges).items())),
        "object_kinds": dict(sorted(Counter(row["object_kind"] for row in edges).items())),
        "typed_links": {column: sum(row[column] is not None for row in edges) for column in TYPED_LINKS},
        "reference_resolution": resolutions,
        "edges_with_source": sum(row["source"] is not None for row in edges),
        "edges_with_evidence": sum(row["evidence"] is not None for row in edges),
        "statuses": dict(sorted(Counter(row["status"] or "" for row in edges).items())),
        "history_fields_present": metadata_counts,
        "repeated_subject_predicate_object": sum(count > 1 for count in groups.values()),
    }


def validate_official(output: Path, checkout: Path) -> dict:
    checkout = checkout.resolve(strict=True)
    env = {**os.environ, "PYTHONIOENCODING": "utf-8"}

    def run(*args: str) -> str:
        result = subprocess.run(args, capture_output=True, encoding="utf-8", env=env)
        if result.returncode:
            raise ValueError((result.stdout + result.stderr).strip())
        return result.stdout.strip()

    if run("git", "-C", str(checkout), "rev-parse", "HEAD") != OSSIE_COMMIT:
        raise ValueError(f"公式検証には Ossie の {OSSIE_COMMIT} が必要です")
    for file, schema in ((ONTOLOGY, "ontology/ontology.json"), (MODEL, "core-spec/ossie-schema.json"),
                         (MAPPING, "ontology/mapping.json")):
        run("uv", "run", "--no-project", str(checkout / "validation/validate.py"),
            "--schema", str(checkout / schema), str(output / file))
    return {"state": "passed", "documents": [ONTOLOGY, MODEL, MAPPING]}


def export(wiki: Path, output: Path, ossie_checkout: Path | None = None) -> dict:
    wiki = wiki.resolve(strict=True)
    output = output.resolve()
    if not (wiki / "SCHEMA.md").is_file():
        raise ValueError(f"初期化された wiki ではありません: {wiki}")
    if output.is_relative_to(wiki):
        raise ValueError("出力先は wiki の外を指定してください")
    if output.exists():
        raise FileExistsError(f"新しい出力先を指定してください: {output}")

    original = snapshot(wiki / "graph" / "graph.sqlite")
    projected = {**original, "edges": project_edges(original)}
    ontology, core, mapping = documents()
    output.mkdir(parents=True)
    try:
        save_json(output / ONTOLOGY, ontology)
        save_json(output / MODEL, core)
        save_json(output / MAPPING, mapping)
        save_sqlite(output / DATA, projected)
        report = verify(output, original, projected)
        report["official_validation"] = (
            {"state": "not_run"} if ossie_checkout is None else validate_official(output, ossie_checkout)
        )
        save_json(output / REPORT, report)
        return report
    except BaseException:
        # 作成に失敗した自分のファイルだけを回収する。
        for name in (ONTOLOGY, MODEL, MAPPING, DATA, REPORT):
            with suppress(OSError):
                (output / name).unlink(missing_ok=True)
        with suppress(OSError):
            output.rmdir()
        raise


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--wiki", type=Path, required=True, help="入力 wiki のルート")
    parser.add_argument("--output", type=Path, required=True, help="wiki 外の新しい出力ディレクトリ")
    parser.add_argument("--ossie-checkout", type=Path, help="公式検証器を実行する Ossie チェックアウト")
    args = parser.parse_args()
    try:
        result = export(args.wiki, args.output, args.ossie_checkout)
    except (OSError, sqlite3.Error, ValueError) as error:
        print(f"書き出せません: {error}", file=sys.stderr)
        return 1
    print(json.dumps(result, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    sys.exit(main())
