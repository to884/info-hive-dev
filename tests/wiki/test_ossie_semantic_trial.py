"""一方向 PoC の段階1・2の受け入れ試験。"""

from pathlib import Path
import sys
from tempfile import TemporaryDirectory
import unittest

ROOT = Path(__file__).resolve().parents[2]
PLUGIN = ROOT / "info-hive-wiki" / "skills" / "info-hive"
sys.path[:0] = [str(ROOT / "poc" / "ossie"), str(PLUGIN / "scripts")]

import semantic_trial
from semantic_records import Trial
from semantic_export import customer_counts, write_release


class SemanticTrialTest(unittest.TestCase):
    def test_synthetic_wiki_proves_counts_split_and_resolution(self):
        with TemporaryDirectory() as directory:
            output = Path(directory) / "export"
            report = semantic_trial.run(output)
            self.assertEqual(
                [report["counts"]["product_a"][name] for name in ("customers", "claims", "evidence")],
                [1, 1, 2],
            )
            self.assertEqual(report["counts"]["product_b"]["customers"], 0)
            self.assertEqual(report["migration_remaining"], {"v1": 1, "v2": 1, "v3": 0})
            self.assertEqual(report["resolved"]["confirmed"], 1)
            refs = report["references"]
            self.assertEqual(refs["active_target"], refs["contract"])
            self.assertNotEqual(refs["active_target"], refs["trial"])
            self.assertEqual(refs["undecided"], 1)
            self.assertTrue((output / "synthetic-wiki" / "sources" / "opposition.md").is_file())
            self.assertEqual(report["releases"]["v3"]["parent_release_id"],
                             report["releases"]["v2"]["release_id"])
            with self.assertRaisesRegex(ValueError, "スナップショットと一致しません"):
                customer_counts(output / "v3" / "wiki-data.sqlite", report["releases"]["v1"]["definition_id"],
                                "synthetic-project", "any", "2025-06-01")

    def test_rejects_different_roles_and_unrelated_evidence_in_migration(self):
        trial = Trial("wiki")
        trial.definition("v1", "初版", {})
        org = trial.entity("a", "A社", "organization")
        other = trial.entity("b", "B社", "organization")
        product = trial.entity("product", "製品", "product")
        approved = trial.add_evidence(None, "出典1", method="fixture", verification="matched")
        unrelated = trial.add_evidence(None, "出典2", method="fixture", verification="matched")
        original_claim = trial.claim("uses", org, product)
        original = trial.revise(original_claim, state="candidate")
        hold = trial.open_hold("migration_pending", original, "根拠不足", product_id=product)
        trial.definition("v2", "新定義", {})
        new = trial.revise(trial.claim("contract", org, product), state="accepted",
                           evidence=[(approved, "supports")])
        wrong = trial.revise(trial.claim("trial", other, product), state="accepted",
                             evidence=[(approved, "supports")])
        with self.assertRaisesRegex(ValueError, "同じ実体"):
            trial.split(original, [new, wrong], {})
        with self.assertRaisesRegex(ValueError, "確定済みの版と根拠"):
            trial.resolve_hold(hold, new, unrelated, "無関係")
        with self.assertRaisesRegex(ValueError, "確定済みの版と根拠"):
            trial.resolve_hold(hold, wrong, approved, "別の会社")
        self.assertEqual(trial.current(original_claim), original)
        self.assertEqual(len(trial.rows["decisions"]), 1)
        self.assertEqual(trial.freeze(), trial.freeze())

    def test_migrated_claim_with_an_opponent_requires_reference_review(self):
        trial = Trial("wiki")
        rules = {"predicates": ["customer_of"]}
        trial.definition("v1", "初版", rules)
        org = trial.entity("a", "A社", "organization")
        product = trial.entity("p", "製品", "product")
        proof = trial.add_evidence(None, "購入", method="fixture", verification="matched")
        counter = trial.add_evidence(None, "購入を否定", method="fixture", verification="matched")
        old = trial.revise(trial.claim("customer_of", org, product, qualifier="old"), state="candidate")
        negative = trial.revise(trial.claim("customer_of", org, product, polarity="negative"),
                                state="accepted", intervals=[("2025-01-01", None)],
                                evidence=[(counter, "supports")])
        trial.reference("contradicts", negative, old, evidence_id=counter, reason="旧記録に反証")
        pending = trial.open_hold("migration_pending", old, "旧版を確認", product_id=product)
        trial.definition("v2", "新版", rules)
        target = trial.revise(trial.claim("customer_of", org, product), state="accepted",
                              intervals=[("2025-01-01", None)], evidence=[(proof, "supports")])
        trial.resolve_hold(pending, target, proof, "購入を確認")
        ref = next(row["id"] for row in trial.rows["holds"].values() if row["kind"] == "reference_pending")
        with TemporaryDirectory() as folder:
            output = Path(folder)
            for name, reason in (("pending", "reference_pending"), ("relinked", "disputed")):
                path = output / name
                release = write_release(path, trial.freeze())
                result = customer_counts(path / "wiki-data.sqlite", release["definition_id"], "wiki",
                                         product, "2025-06-01")
                self.assertEqual(result["customers"], 0)
                self.assertIn(reason, result["limitations"])
                if name == "pending":
                    trial.resolve_reference(ref, target, counter, "新版の購入にも反証が成立")

    def test_counts_distinct_entities_and_shared_evidence_and_detects_opposition(self):
        trial = Trial("wiki")
        trial.definition("v1", "顧客", {"predicates": ["customer_of"]})
        org = trial.entity("a", "A社", "organization")
        product = trial.entity("p", "製品", "product")
        proof = trial.add_evidence(None, "契約2件", method="fixture", verification="matched")
        intervals = [("2025-01-01", None)]
        for qualifier in ("1", "2"):
            trial.revise(trial.claim("customer_of", org, product, qualifier=qualifier),
                         state="accepted", intervals=intervals, evidence=[(proof, "supports")])
        contrary = trial.add_evidence(None, "契約2を否定", method="fixture", verification="matched")
        neg = trial.claim("customer_of", org, product, qualifier="2", polarity="negative")
        with TemporaryDirectory() as folder:
            for label, limits, claims in (("both", [], 2), ("unknown", ["reference_pending"], 1),
                                          ("conflict", ["disputed"], 1)):
                path = Path(folder) / label
                release = write_release(path, trial.freeze())
                result = customer_counts(path / "wiki-data.sqlite", release["definition_id"], "wiki",
                                         product, "2025-06-01")
                self.assertEqual((result["customers"], result["claims"], result["evidence"], result["limitations"]),
                                 (1, claims, 1, limits))
                if label in {"both", "unknown"}:
                    trial.revise(neg, state="accepted", evidence=[(contrary, "supports")],
                                 intervals=[] if label == "both" else intervals)

    def test_legacy_import_is_repeatable_and_read_only(self):
        try:
            import yaml  # noqa: F401
        except ImportError:
            self.skipTest("既存 wiki の読み込みには PyYAML が必要です")
        import wiki_graph_extract as extract

        with TemporaryDirectory() as directory:
            root = Path(directory)
            wiki = root / "wiki"
            files = {
                "SCHEMA.md": "# 構成\n",
                "concepts/a.md": (
                    "---\ntype: concept\ntitle: A\ngraph:\n  relationships:\n"
                    "    - predicate: depends_on\n      object: concept:b\n      source: sample\n"
                    "      evidence: 引用\n      raw_ref: raw/sample.md#L2\n      supersedes: sample\n"
                    "---\n[[b]]\n"
                ),
                "concepts/b.md": "---\ntype: concept\ntitle: B\n---\n",
                "sources/sample.md": "---\ntype: source\ntitle: 例\n---\n引用\n",
                "raw/sample.md": "一行目\n引用\n",
                "graph/ontology.yaml": (PLUGIN / "assets" / "ontology.yaml.template").read_text(encoding="utf-8"),
            }
            for relative, text in files.items():
                path = wiki / relative
                path.parent.mkdir(parents=True, exist_ok=True)
                path.write_text(text, encoding="utf-8")
            ontology = extract.read_ontology(wiki / "graph" / "ontology.yaml")
            pages = extract.collect_pages(wiki)
            nodes, page_ids, aliases = extract.build_nodes(pages, ontology)
            old_id = next(edge["id"] for edge in extract.build_edges(pages, page_ids)
                          if edge["predicate"] == "depends_on")
            (wiki / "concepts/c.md").write_text(
                "---\ntype: concept\ngraph:\n  relationships:\n"
                "    - predicate: depends_on\n      object: concept:b\n"
                f'      contradicts: "{old_id}"\n      supersedes: missing\n---\n',
                encoding="utf-8",
            )
            pages = extract.collect_pages(wiki)
            nodes, page_ids, aliases = extract.build_nodes(pages, ontology)
            db_path = wiki / "graph" / "graph.sqlite"
            db_path.touch(exist_ok=False)
            extract.build_sqlite(db_path, nodes, aliases, extract.build_edges(pages, page_ids))
            before = {p.relative_to(wiki): p.read_bytes() for p in wiki.rglob("*") if p.is_file()}
            report = semantic_trial.run(root / "export-1", wiki=wiki, wiki_id="legacy")
            self.assertEqual(report, semantic_trial.run(root / "export-2", wiki=wiki, wiki_id="legacy"))
            self.assertEqual(report["legacy_history"], {"revision_links": 1, "record_links": 1, "unresolved": 1})
            self.assertEqual(report["evidence"], [{"legacy_id": old_id, "predicate": "depends_on", "linked": True,
                                                  "raw_verification": "matched", "source_page_version": True}])
            self.assertEqual(before, {p.relative_to(wiki): p.read_bytes()
                                      for p in wiki.rglob("*") if p.is_file()})
            with self.assertRaisesRegex(ValueError, "入力 wiki"):
                semantic_trial.run(wiki / "export", wiki=wiki, wiki_id="legacy")


if __name__ == "__main__":
    unittest.main()
