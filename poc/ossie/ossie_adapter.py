"""この PoC の Ossie 宣言を DuckDB の一時データへ写すローカルアダプター。"""

from __future__ import annotations

from collections import defaultdict
from contextlib import closing
import json
from pathlib import Path
import re
from typing import NamedTuple

import duckdb

from export_wiki_graph import DATA, MAPPING, VERSION, ident, readonly


NAME = r"[A-Za-z_][A-Za-z_0-9]*"
FIELD = re.compile(rf"({NAME})\.({NAME})")
PHYSICAL = re.compile(rf'source\.(?:"({NAME})"|({NAME}))')
COUNT = re.compile(rf"COUNT\((DISTINCT )?({NAME})\.({NAME})\)", re.IGNORECASE)


def read_json(path):
    return json.loads(path.read_text(encoding="utf-8"))


def checked_name(name):
    if not isinstance(name, str) or not re.fullmatch(NAME, name):
        raise ValueError(f"識別子の対応範囲外です: {name!r}")
    return name


def only(value, keys):
    extra = set(value) - set(keys.split())
    if extra:
        raise ValueError(f"宣言の対応範囲外です: {sorted(extra)}")


def indexed(values, key):
    result = {}
    for value in values:
        name = checked_name(value[key])
        if name.casefold() in {item.casefold() for item in result}:
            raise ValueError(f"識別子が重複しています: {name}")
        result[name] = value
    return result


class Issue(NamedTuple):
    code: str
    concept: str
    relation: str
    object_id: str


class ConstraintError(ValueError):
    def __init__(self, issues):
        self.issues = sorted(set(issues))
        super().__init__(f"データの制約違反: {self.issues!r}")


class OssieAdapter:
    """この PoC が出す Core・Ontology・独立 Mapping の部分集合を評価する。"""

    def __init__(self):
        self.db = duckdb.connect(":memory:", config={"enable_external_access": "false", "threads": "2"})
        self.release = None
        self.datasets = {}
        self.relations = {}
        self.requires = {}

    def __enter__(self):
        return self

    def __exit__(self, *_):
        self.db.close()

    def load(self, folder: Path):
        mapping = read_json(folder / MAPPING)
        manifest = folder / "release.json"
        if manifest.is_file():
            self.release = read_json(manifest)

        def referenced(name):
            ref = mapping[name]
            only(ref, "name iri")
            path = (folder / ref["iri"]).resolve(strict=True)
            if not path.is_relative_to(folder.resolve()) or path.suffix != ".json":
                raise ValueError("ローカルの同一バンドル内にある JSON 文書を指定してください")
            value = read_json(path)
            if value["name"] != ref["name"]:
                raise ValueError(f"{name} の文書名が一致しません")
            return value

        ontology = referenced("ontology_ref")
        core = referenced("semantic_model_ref")
        if any(value["version"] != VERSION for value in (ontology, core, mapping)):
            raise ValueError("文書版がこのアダプターの対応範囲外です")
        only(core, "version name description datasets relationships")
        only(ontology, "version name description ontology")
        only(mapping, "version name description ontology_ref semantic_model_ref concept_mappings")
        with closing(readonly(folder / DATA)) as file:
            file.execute("BEGIN")
            self.load_sources(core, file)
        self.declarations(ontology)
        self.materialize(mapping)
        issues = self.check_links() + self.check_core(core)
        if issues:
            raise ConstraintError(issues)

    def load_sources(self, core, source):
        for index, (name, definition) in enumerate(indexed(core["datasets"], "name").items()):
            only(definition, "name source fields primary_key")
            table = checked_name(definition["source"])
            fields = indexed(definition["fields"], "name")
            physical = []
            for field in fields.values():
                only(field, "name datatype expression")
                only(field["expression"], "sql")
                match = PHYSICAL.fullmatch(field["expression"]["sql"])
                if field["datatype"] != "String" or not match:
                    raise ValueError("Core の列は String 型の source 列参照に限ります")
                physical.append(match[1] or match[2])
            keys = definition["primary_key"]
            if not fields or not keys or len(set(keys)) != len(keys) or set(keys) - fields.keys():
                raise ValueError(f"Core 主キーを解決できません: {name}")
            view = f"core_{index}"
            self.datasets[name] = (view, fields, keys)
            physical_columns = {row[1] for row in source.execute(f"PRAGMA table_info({ident(table)})")}
            if set(physical) - physical_columns:
                raise ValueError(f"SQLite の参照先の列がありません: {name}")
            rows = source.execute(
                f"SELECT {', '.join(map(ident, physical))} FROM {ident(table)}"
            ).fetchall()
            if any(value is not None and not isinstance(value, str) for row in rows for value in row):
                raise ValueError(f"Core の String 型と元の値が一致しません: {name}")
            self.db.execute(f"CREATE TABLE {view} ({', '.join(ident(field) + ' VARCHAR' for field in fields)})")
            if rows:
                self.db.executemany(f"INSERT INTO {view} VALUES ({','.join('?' for _ in fields)})", rows)
            key_names = ", ".join(map(ident, keys))
            null = " OR ".join(f"{ident(key)} IS NULL" for key in keys)
            if self.db.execute(f"SELECT 1 FROM {view} WHERE {null} LIMIT 1").fetchone() or self.db.execute(
                f"SELECT 1 FROM {view} GROUP BY {key_names} HAVING COUNT(*) > 1 LIMIT 1"
            ).fetchone():
                raise ConstraintError([Issue("primary_key", name, ",".join(keys), "")])

    def declarations(self, ontology):
        concepts = indexed(ontology["ontology"], "concept")
        if "String" in concepts:
            raise ValueError("組み込み型 String は再定義できません")
        for name, definition in concepts.items():
            only(definition, "concept type description identify_by relationships requires")
            properties = indexed(definition["relationships"], "name")
            if definition["type"] != "EntityType" or definition["identify_by"] != ["id"]:
                raise ValueError("単一の id で識別する EntityType のみ扱います")
            self.relations[name] = {}
            for relation, entry in properties.items():
                only(entry, "name description roles multiplicity verbalizes")
                roles = entry["roles"]
                mult = entry.get("multiplicity")
                if len(roles) != 1 or mult not in (None, "ManyToOne", "OneToOne"):
                    raise ValueError("2項関係の多重度のみ扱います")
                only(roles[0], "concept name")
                target = roles[0]["concept"]
                if target != "String" and target not in concepts:
                    raise ValueError(f"関係の型を解決できません: {name}.{relation}")
                self.relations[name][relation] = (target, mult)
            if self.relations[name].get("id") not in (("String", "ManyToOne"), ("String", "OneToOne")):
                raise ValueError(f"単一の文字列 id が必要です: {name}")
            for expr in definition.get("requires", []):
                match = FIELD.fullmatch(expr)
                if not match or match[1] != name or match[2] not in properties:
                    raise ValueError(f"requires の対応範囲外です: {expr}")
                self.requires.setdefault(name, set()).add(match[2])

    def field(self, expression):
        match = FIELD.fullmatch(expression)
        if not match or match[1] not in self.datasets or match[2] not in self.datasets[match[1]][1]:
            raise ValueError(f"Mapping/Core の列を解決できません: {expression}")
        return match[1], ident(match[2])

    def identity(self, mapping, expected):
        only(mapping, "concept referent_mappings")
        if mapping.get("concept", expected) != expected:
            raise ValueError("Mapping の識別対象が宣言の型と一致しません")
        refs = mapping["referent_mappings"]
        if len(refs) != 1 or refs[0]["relationship"] != "id":
            raise ValueError("Mapping は単一の id 参照に限ります")
        only(refs[0], "relationship expression")
        return self.field(refs[0]["expression"])

    def materialize(self, mapping):
        self.db.execute("CREATE TABLE staged_objects (kind VARCHAR, id VARCHAR)")
        self.db.execute("CREATE TABLE staged_links (kind VARCHAR, id VARCHAR, rel VARCHAR, target_kind VARCHAR, val VARCHAR)")
        for kind, rule in indexed(mapping["concept_mappings"], "concept").items():
            only(rule, "concept object_mappings link_mappings")
            if kind not in self.relations:
                raise ValueError(f"Mapping の型が未宣言です: {kind}")
            for obj in rule.get("object_mappings", []):
                name, column = self.identity(obj, kind)
                view = self.datasets[name][0]
                if self.db.execute(f"SELECT 1 FROM {view} WHERE {column} IS NULL LIMIT 1").fetchone():
                    raise ConstraintError([Issue("identity_null", kind, "id", "")])
                self.db.execute(f"INSERT INTO staged_objects SELECT ?, {column} FROM {view}", (kind,))
            for link in rule.get("link_mappings", []):
                only(link, "object_mapping children")
                name, subject = self.identity(link["object_mapping"], kind)
                view = self.datasets[name][0]
                for child in link["children"]:
                    only(child, "relationship object_mapping")
                    relation = child["relationship"]
                    if relation == "id" or relation not in self.relations[kind]:
                        raise ValueError(f"Mapping の関係が未対応です: {kind}.{relation}")
                    target = self.relations[kind][relation][0]
                    obj = child["object_mapping"]
                    if obj["concept"] != target:
                        raise ValueError(f"Mapping の役割型が一致しません: {kind}.{relation}")
                    if target == "String":
                        only(obj, "concept expression")
                        other, value = self.field(obj["expression"])
                    else:
                        other, value = self.identity(obj, target)
                    if name != other:
                        raise ValueError("1つのリンク Mapping では同じデータセットを使ってください")
                    self.db.execute(f"""
                        INSERT INTO staged_links
                        SELECT ?, {subject}, ?, ?, {value} FROM {view}
                        WHERE {subject} IS NOT NULL AND {value} IS NOT NULL
                    """, (kind, relation, target))
        self.db.execute("CREATE TABLE objects AS SELECT DISTINCT * FROM staged_objects")
        self.db.execute("INSERT INTO staged_links SELECT kind, id, 'id', 'String', id FROM objects")
        self.db.execute("CREATE TABLE links AS SELECT DISTINCT * FROM staged_links")

    def check_links(self):
        results = [Issue(code, kind, relationship, id) for code, kind, relationship, id in self.db.execute("""
            SELECT 'missing_subject', l.kind, l.rel, l.id
            FROM links l ANTI JOIN objects s ON (l.kind, l.id) = (s.kind, s.id)
            UNION ALL
            SELECT 'missing_target', l.kind, l.rel, l.id
            FROM (SELECT * FROM links WHERE target_kind <> 'String') l
            ANTI JOIN objects t ON (l.target_kind, l.val) = (t.kind, t.id)
        """).fetchall()]
        for kind, declarations in self.relations.items():
            for relation, (_, mult) in declarations.items():
                if mult:
                    rows = self.db.execute("""
                        SELECT id FROM links WHERE kind = ? AND rel = ? GROUP BY id HAVING count(*) > 1
                    """, (kind, relation)).fetchall()
                    results.extend(Issue("many_to_one", kind, relation, id) for (id,) in rows)
                if mult == "OneToOne":
                    rows = self.db.execute("""
                        SELECT a.id FROM links a JOIN links b ON (a.kind, a.rel, a.val) = (b.kind, b.rel, b.val)
                        WHERE a.kind = ? AND a.rel = ? AND a.id <> b.id
                    """, (kind, relation)).fetchall()
                    results.extend(Issue("one_to_one", kind, relation, id) for (id,) in rows)
            for relation in self.requires.get(kind, []):
                rows = self.db.execute("""
                    SELECT o.id FROM objects o WHERE o.kind = ?
                      AND NOT EXISTS (SELECT 1 FROM links l WHERE l.kind = o.kind AND l.id = o.id AND l.rel = ?)
                """, (kind, relation)).fetchall()
                results.extend(Issue("requires", kind, relation, id) for (id,) in rows)
        return results

    def check_core(self, core):
        issues = []
        for relationship, entry in indexed(core.get("relationships", []), "name").items():
            only(entry, "name from to from_columns to_columns")
            start, start_fields, keys = self.datasets[entry["from"]]
            end, end_fields, end_keys = self.datasets[entry["to"]]
            a, b = entry["from_columns"], entry["to_columns"]
            if len(a) != len(b) or set(a) - start_fields.keys() or set(b) - end_fields.keys() or b != end_keys:
                raise ValueError(f"Core の結合先を主キーで識別できません: {relationship}")
            join = " AND ".join(f"a.{ident(x)} = b.{ident(y)}" for x, y in zip(a, b))
            present = " AND ".join(f"a.{ident(x)} IS NOT NULL" for x in a)
            id_columns = ", ".join(f"a.{ident(key)}" for key in keys)
            rows = self.db.execute(f"""
                SELECT {id_columns} FROM {start} a ANTI JOIN {end} b ON {join} WHERE {present}
            """).fetchall()
            issues.extend(Issue("core_reference", entry["from"], relationship, "|".join(key)) for key in rows)
        return issues

    def concept_view(self, name, kind, fields):
        """語彙の1対1/多対1の関係を列へ戻したビューを、実行結果から作る。"""
        predicates = self.relations[kind]
        if any(field == "id" or field not in predicates or not predicates[field][1] for field in fields):
            raise ValueError("列にできる関係は、単一値のプロパティに限ります")
        # kind・field は読み込み時に検査済みの識別子だけを使う。
        columns = "".join(f", MAX(l.val) FILTER (WHERE l.rel = '{field}') AS {ident(field)}" for field in fields)
        self.db.execute(f"""
            CREATE VIEW {ident(name)} AS
            SELECT o.id {columns}
            FROM objects o LEFT JOIN links l ON (l.kind, l.id) = (o.kind, o.id)
            WHERE o.kind = '{kind}' GROUP BY o.id
        """)


def metric_results(db, core_path, dataset):
    """単一データセットの COUNT と COUNT(DISTINCT ...) を宣言から実行する。"""
    core = read_json(core_path)
    if core["version"] != VERSION:
        raise ValueError("Core 指標の版が対応範囲外です")
    only(core, "version name description datasets metrics")
    definitions = indexed(core["datasets"], "name")
    if set(definitions) != {dataset}:
        raise ValueError("Core 指標のデータセットが一致しません")
    definition = definitions[dataset]
    only(definition, "name source fields")
    fields = indexed(definition["fields"], "name")
    for name, entry in fields.items():
        if entry != {"name": name, "datatype": "String", "expression": {"sql": f"source.{ident(name)}"}}:
            raise ValueError("Core 指標の入力列が対応範囲外です")
    expressions = {}
    for name, metric in indexed(core["metrics"], "name").items():
        only(metric, "name expression description")
        only(metric["expression"], "sql")
        match = COUNT.fullmatch(metric["expression"]["sql"])
        if not match or match[2] != dataset or match[3] not in fields:
            raise ValueError(f"Core 指標式が対応範囲外です: {name}")
        distinct = "DISTINCT " if match[1] else ""
        expressions[name] = f"COUNT({distinct}{ident(match[3])})"
    values = db.execute(f"SELECT {', '.join(expressions.values())} FROM {ident(checked_name(definition['source']))}").fetchone()
    return dict(zip(expressions, values))
