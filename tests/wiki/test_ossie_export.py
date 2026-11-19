"""既存の抽出器で作ったグラフから、Ossie 出力に履歴と根拠が残ることを確かめる。"""

from contextlib import closing
from pathlib import Path
import json
import sys
import tempfile
from textwrap import dedent
import unittest
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[2]
PLUGIN = ROOT / "info-hive-wiki" / "skills" / "info-hive"
sys.path.insert(0, str(ROOT / "poc" / "ossie"))
sys.path.insert(0, str(PLUGIN / "scripts"))

import export_wiki_graph as ossie

try:
    import yaml
except ModuleNotFoundError:
    yaml = None

if yaml is not None:
    import wiki_graph_extract as extract


@unittest.skipIf(yaml is None, "既存の抽出器を動かすには PyYAML が必要です")
class OssieExportTest(unittest.TestCase):
    def setUp(self):
        folder = tempfile.TemporaryDirectory(prefix="wiki-ossie-test-")
        self.addCleanup(folder.cleanup)
        self.wiki = Path(folder.name) / "wiki"
        self.output = Path(folder.name) / "ossie"
        self.db_path = self.wiki / "graph" / "graph.sqlite"
        self.db_path.parent.mkdir(parents=True)
        self.write("SCHEMA.md", "# スキーマ\n")
        self.write("entities/製品A.md", """
            ---
            type: entity
            graph:
              node_id: product:製品A
              node_type: product
              aliases: [製品エー, 製品Ａ]
            ---
            # 製品A
        """)
        self.write("entities/製品B.md", """
            ---
            type: entity
            graph:
              node_id: product:製品B
              node_type: product
            ---
            # 製品B
        """)
        for source in ("旧資料", "現行資料"):
            self.write(f"sources/{source}.md", f"""
                ---
                type: source
                raw: raw/{source}.md
                ---
                # {source}
            """)
        self.ontology = extract.read_ontology(PLUGIN / "assets" / "ontology.yaml.template")

    def write(self, path, content):
        path = self.wiki / path
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(dedent(content).lstrip(), encoding="utf-8")

    def build(self):
        pages = extract.collect_pages(self.wiki)
        nodes, page_node_ids, aliases = extract.build_nodes(pages, self.ontology)
        edges = extract.build_edges(pages, page_node_ids)
        return nodes, aliases, edges

    def build_sqlite(self, nodes, aliases, edges):
        self.db_path.touch(exist_ok=False)
        extract.build_sqlite(self.db_path, nodes, aliases, edges)

    def test_preserves_individual_claims_dates_and_references(self):
        path = "entities/製品A.md"
        previous = (self.wiki / path).read_text(encoding="utf-8")
        header, body = previous.rsplit("---\n", 1)
        history = dedent("""
            relationships:
              - predicate: depends_on
                object: product:製品B
                source: 旧資料
                evidence: 以前の根拠
                confidence: medium
                status: superseded
                valid_from: 2024-01-01
                valid_to: 2024-12-31
                raw_ref: raw/旧資料.md#L2
                notes: 旧版
              - predicate: depends_on
                object: product:製品B
                source: 現行資料
                evidence: 現在の根拠
                confidence: high
                status: current
                valid_from: 2025-01-01
              - predicate: depends_on
                object: product:製品B
                source: 旧資料
                evidence: 反対の根拠
                confidence: low
                status: disputed
                supersedes: 旧資料
        """).strip().splitlines()
        with_claims = header + "".join(f"  {line}\n" for line in history) + "---\n" + body
        self.write(path, with_claims)
        _, _, first_edges = self.build()
        ids = {row["status"]: row["id"] for row in first_edges if row["predicate"] == "depends_on"}
        self.write(path, with_claims.replace(
            "      valid_from: 2025-01-01\n",
            f'      valid_from: 2025-01-01\n      supersedes: "{ids["superseded"]}"\n',
        ).replace(
            "      supersedes: 旧資料\n",
            f'      supersedes: 旧資料\n      contradicts: "{ids["current"]}"\n',
        ))
        nodes, aliases, edges = self.build()
        self.assertEqual(
            {row["status"]: row["id"] for row in edges if row["predicate"] == "depends_on"}, ids,
        )
        self.build_sqlite(nodes, aliases, edges)
        before = self.db_path.read_bytes()
        report = ossie.export(self.wiki, self.output)
        self.assertEqual(self.db_path.read_bytes(), before)
        self.assertTrue(report["exact_snapshot_match"])
        self.assertEqual(report["predicates"], {"depends_on": 3, "summarizes_raw": 2})
        self.assertEqual(report["repeated_subject_predicate_object"], 1)
        self.assertEqual(report["edges_with_evidence"], 3)
        self.assertEqual(report["object_kinds"], {"node": 3, "raw": 2})
        self.assertEqual(report["history_fields_present"], {
            "valid_from": 2, "valid_to": 1, "notes": 1, "raw_ref": 1,
            "contradicts": 1, "supersedes": 2,
        })

        core = json.loads((self.output / ossie.MODEL).read_text(encoding="utf-8"))
        mapping = json.loads((self.output / ossie.MAPPING).read_text(encoding="utf-8"))
        with closing(ossie.readonly(self.output / ossie.DATA)) as db:
            facts = ossie.mapped_facts(db, core, mapping)
            raw_targets = db.execute(
                "SELECT object, object_node_id, evidence FROM wiki_edges "
                "WHERE object_kind = 'raw' ORDER BY object"
            ).fetchall()
        self.assertEqual(raw_targets, [("raw:raw/旧資料.md", None, None), ("raw:raw/現行資料.md", None, None)])
        expected = {
            ("WikiEdge", ids["superseded"], "evidence", "String", "以前の根拠"),
            ("WikiEdge", ids["current"], "evidence", "String", "現在の根拠"),
            ("WikiEdge", ids["disputed"], "evidence", "String", "反対の根拠"),
            ("WikiEdge", ids["superseded"], "valid_to", "String", "2024-12-31"),
            ("WikiEdge", ids["superseded"], "notes", "String", "旧版"),
            ("WikiEdge", ids["superseded"], "raw_ref", "String", "raw/旧資料.md#L2"),
            ("WikiEdge", ids["superseded"], "source_node_id", "WikiNode", "source:旧資料"),
            ("WikiEdge", ids["current"], "supersedes_edge_id", "WikiEdge", ids["superseded"]),
            ("WikiEdge", ids["disputed"], "contradicts_edge_id", "WikiEdge", ids["current"]),
            ("WikiEdge", ids["disputed"], "supersedes_node_id", "WikiNode", "source:旧資料"),
            ("WikiNode", "product:製品A", "alias", "String", "製品エー"),
            ("WikiNode", "product:製品A", "alias", "String", "製品Ａ"),
        }
        self.assertFalse(expected - facts, expected - facts)

    def test_reports_reference_to_changed_edge_id(self):
        self.write("concepts/旧版.md", """
            ---
            type: concept
            graph:
              relationships:
                - predicate: depends_on
                  object: product:製品B
                  status: current
            ---
        """)
        _, _, edges = self.build()
        old_id = next(row["id"] for row in edges if row["predicate"] == "depends_on")
        path = self.wiki / "concepts/旧版.md"
        path.write_text(
            path.read_text(encoding="utf-8").replace("status: current", "status: superseded"),
            encoding="utf-8",
        )
        self.write("concepts/新版.md", f"""
            ---
            type: concept
            sources: ['[[sources/現行資料]]']
            graph:
              relationships:
                - predicate: depends_on
                  object: product:製品B
                  supersedes: "{old_id}"
            ---
        """)
        nodes, aliases, edges = self.build()
        self.assertNotIn(old_id, {row["id"] for row in edges})
        self.build_sqlite(nodes, aliases, edges)
        report = ossie.export(self.wiki, self.output)
        self.assertEqual(report["official_validation"], {"state": "not_run"})
        self.assertEqual(report["reference_resolution"], {
            "source": {"node": 1}, "contradicts": {}, "supersedes": {"unresolved": 1},
        })
        with closing(ossie.readonly(self.output / ossie.DATA)) as db:
            result = db.execute(
                "SELECT supersedes, supersedes_edge_id, supersedes_node_id "
                "FROM wiki_edges WHERE supersedes_resolution = 'unresolved'"
            ).fetchall()
        self.assertEqual(result, [(old_id, None, None)])

    def test_reports_invalid_reference_without_discarding_metadata(self):
        rows = {
            "nodes": [
                {"id": "source:資料", "slug": "資料", "page_type": "source"},
                {"id": "source:別の資料", "slug": "資料", "page_type": "source"},
            ],
            "edges": [{
                "id": "relation",
                "subject": "source:資料",
                "predicate": "mentions",
                "object": "source:別の資料",
                "source": None,
                "extraction_method": "explicit_graph_frontmatter",
                "metadata_json": '{"contradicts": ["a", "b"], "supersedes": "資料"}',
            }],
        }
        record, = ossie.project_edges(rows)
        self.assertEqual(record["contradicts_resolution"], "non_string")
        self.assertEqual(record["supersedes_resolution"], "ambiguous")
        self.assertIsNone(record["supersedes_node_id"])
        self.assertEqual(record["metadata_json"], rows["edges"][0]["metadata_json"])

    def test_rejects_destination_inside_wiki_or_existing(self):
        with self.assertRaisesRegex(ValueError, "wiki の外"):
            ossie.export(self.wiki, self.wiki / "new-export")
        self.output.mkdir()
        marker = self.output / "keep.txt"
        marker.write_text("保存済み", encoding="utf-8")
        with self.assertRaises(FileExistsError):
            ossie.export(self.wiki, self.output)
        self.assertEqual(list(self.output.iterdir()), [marker])
        self.assertEqual(marker.read_text(encoding="utf-8"), "保存済み")

    def test_preserves_original_error_and_unowned_file(self):
        self.build_sqlite(*self.build())

        def fail(output, *_):
            (output / "other.txt").write_text("別のファイル", encoding="utf-8")
            raise ValueError("試験用の照合失敗")

        with patch.object(ossie, "verify", side_effect=fail):
            with self.assertRaisesRegex(ValueError, "試験用の照合失敗"):
                ossie.export(self.wiki, self.output)
        self.assertEqual([item.name for item in self.output.iterdir()], ["other.txt"])


if __name__ == "__main__":
    unittest.main()
