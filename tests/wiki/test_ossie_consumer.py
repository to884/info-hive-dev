"""Ossie のローカル消費試験を、合成 wiki の出力から再現する。"""

import importlib.util
from pathlib import Path
import sys
from tempfile import TemporaryDirectory
import unittest

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "poc" / "ossie"))

import export_wiki_graph as legacy
import semantic_trial
from semantic_export import customer_counts, write_release
from semantic_records import Trial

HAS_DUCKDB = importlib.util.find_spec("duckdb") is not None
if HAS_DUCKDB:
    import consume_ossie as stage3
    from ossie_adapter import ConstraintError, OssieAdapter
    from ossie_customers import evaluate_customer, metrics_document, set_views


@unittest.skipUnless(HAS_DUCKDB, "段階3の消費試験には DuckDB が必要です")
class ConsumeOssieTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        tmp = TemporaryDirectory(prefix="ossie-consumer-test-")
        cls.addClassCleanup(tmp.cleanup)
        cls.root = Path(tmp.name)
        cls.bundles = cls.root / "generations"
        cls.report = semantic_trial.run(cls.bundles)
        cls.v1 = cls.bundles / "v1"

    def test_all_synthetic_releases_match_sqlite_and_fixed_expectations(self):
        path = self.root / "customer-metrics.json"
        legacy.save_json(path, metrics_document())
        for label in stage3.RELEASES:
            with self.subTest(label=label):
                result = stage3.check_bundle(self.bundles / label, semantic=True, label=label,
                                             metrics_path=path, previous=self.report)
                if label == "v1":
                    case = result["customers"]["製品A/2025-06-01"]
                    self.assertEqual(case["joined_rows"], 2)
                    self.assertEqual(case["duckdb"], case["sqlite"])
                    self.assertEqual(case["duckdb"]["customers"], 1)

    def test_executes_core_metric_expression_as_written(self):
        definition = stage3.read_json(self.v1 / "release.json")
        doc = metrics_document()
        doc["metrics"][0]["expression"]["sql"] = "COUNT(customer_evidence.customer_id)"
        path = self.root / "non_distinct.json"
        legacy.save_json(path, doc)
        with OssieAdapter() as adapter:
            adapter.load(self.v1)
            set_views(adapter)
            product_id = adapter.db.execute("SELECT id FROM entity WHERE name = '製品A'").fetchone()[0]
            result, raw = evaluate_customer(adapter, path, definition["wiki_id"], definition["definition_id"],
                                            product_id, "2025-06-01")
            self.assertEqual((result["customers"], raw), (2, 2))
            self.assertEqual(result["claims"], 1)
            with self.assertRaisesRegex(ValueError, "読み込んだバンドルと一致しません"):
                evaluate_customer(adapter, path, definition["wiki_id"], "old-definition",
                                  product_id, "2025-06-01")

    def test_valid_documents_invalid_data_and_broken_mapping(self):
        with TemporaryDirectory(dir=self.root) as target:
            fixtures = stage3.make_fixtures(self.v1, Path(target))
            report = stage3.verify_violations(*fixtures)
        self.assertEqual(report["valid_data"], "passed")
        self.assertEqual(report["invalid_data"], "rejected")
        self.assertEqual(report["broken_mapping"], "rejected")
        self.assertEqual({row["code"] for row in report["matching_issues"]},
                         {"requires", "missing_target", "core_reference", "one_to_one"})

    def test_customer_filters_on_nontrivial_competing_claims(self):
        trial = Trial("coverage-wiki")
        trial.definition("legacy", "顧客定義を持たない旧版", {"predicates": ["other"]})
        product = trial.entity("p", "製品", "product")
        a = trial.entity("a", "A社", "organization")
        b = trial.entity("b", "B社", "organization")
        evidence = trial.add_evidence(None, "顧客の根拠", method="fixture", verification="matched")
        context = trial.add_evidence(None, "背景を補足", method="fixture", verification="matched")
        inside = [("2025-01-01", "2026-01-01")]

        def record(subject, key, state="accepted", polarity="positive", predicate="customer_of", interval=inside):
            claim = trial.claim(predicate, subject, product, qualifier=key, polarity=polarity)
            return trial.revise(claim, state=state, intervals=interval,
                                evidence=[(evidence, "supports"), (context, "context")])

        record(a, "legacy-positive")
        record(a, "qualified", polarity="negative")
        trial.definition("current", "顧客を照会する版", {"predicates": {"customer_of": None, "other": None}})
        record(a, "qualified")
        record(a, "candidate-opposition")
        record(a, "candidate-opposition", state="candidate", polarity="negative")
        record(b, "qualified")
        record(b, "qualified", polarity="negative", interval=[("2024-01-01", "2025-01-01")])
        subject = record(b, "reversed-link")
        opponent = record(b, "extra-assertion", polarity="negative", predicate="other")
        trial.reference("contradicts", subject, opponent, reason="逆向きの反証")
        record(b, "candidate", state="candidate")
        with TemporaryDirectory(dir=self.root) as directory:
            root = Path(directory)
            bundle = root / "bundle"
            manifest = write_release(bundle, trial.freeze())
            path = root / "metrics.json"
            legacy.save_json(path, metrics_document())
            args = (manifest["definition_id"], manifest["wiki_id"], product, "2025-06-01")
            expected = {"customers": 2, "claims": 2, "evidence": 1, "customer_ids": sorted([a, b]),
                        "limitations": ["claim_candidate", "disputed", "migration_pending", "reference_pending"]}
            self.assertEqual(customer_counts(bundle / legacy.DATA, *args), expected)
            with OssieAdapter() as adapter:
                adapter.load(bundle)
                set_views(adapter)
                actual, joined = evaluate_customer(adapter, path, args[1], args[0], args[2], args[3])
            self.assertEqual((actual, joined), (expected, 2))

    def test_rejects_constraint_errors_and_role_mismatch(self):
        def objects(rule):
            return rule["object_mappings"][0]["referent_mappings"][0]

        def subject(rule):
            return rule["link_mappings"][0]["object_mapping"]["referent_mappings"][0]

        def duplicate_name(rule):
            first = rule["link_mappings"][0]
            first["children"].append({"relationship": "name", "object_mapping": {
                "concept": "String", "expression": "sem_entities.entity_type",
            }})

        changes = {
            "identity_null": ("WikiClaim", lambda rule: objects(rule).update(expression="sem_claims.subject_article_id")),
            "missing_subject": ("WikiEntity", lambda rule: subject(rule).update(expression="sem_entities.name")),
            "many_to_one": ("WikiEntity", duplicate_name),
        }
        with TemporaryDirectory(dir=self.root) as directory:
            for code, (concept, change) in changes.items():
                with self.subTest(code=code):
                    target = Path(directory) / code
                    stage3.clone(self.v1, target)
                    path = target / legacy.MAPPING
                    mapping = stage3.read_json(path)
                    change(next(item for item in mapping["concept_mappings"] if item["concept"] == concept))
                    legacy.save_json(path, mapping)
                    with OssieAdapter() as adapter, self.assertRaises(ConstraintError) as error:
                        adapter.load(target)
                    self.assertIn(code, {issue.code for issue in error.exception.issues})

            target = Path(directory) / "invalid-primary-key"
            stage3.clone(self.v1, target)
            core_path = target / legacy.MODEL
            core = stage3.read_json(core_path)
            next(d for d in core["datasets"] if d["name"] == "sem_supports")["primary_key"] = ["revision_id"]
            legacy.save_json(core_path, core)
            with OssieAdapter() as adapter, self.assertRaises(ConstraintError) as error:
                adapter.load(target)
            self.assertEqual([item.code for item in error.exception.issues], ["primary_key"])

    def test_mapping_drives_typed_target_even_when_sqlite_is_unchanged(self):
        with TemporaryDirectory(dir=self.root) as directory:
            target = Path(directory) / "changed"
            stage3.clone(self.v1, target)
            mapping = stage3.read_json(target / legacy.MAPPING)
            rule = next(row for row in mapping["concept_mappings"] if row["concept"] == "WikiEvidenceLink")
            child = next(row for row in rule["link_mappings"][0]["children"] if row["relationship"] == "evidence_id")
            child["object_mapping"]["referent_mappings"][0]["expression"] = "sem_supports.revision_id"
            legacy.save_json(target / legacy.MAPPING, mapping)
            with OssieAdapter() as adapter:
                with self.assertRaises(ConstraintError) as error:
                    adapter.load(target)
            self.assertIn("missing_target", {issue.code for issue in error.exception.issues})
            child["object_mapping"]["concept"] = "WikiEntity"
            legacy.save_json(target / legacy.MAPPING, mapping)
            with OssieAdapter() as adapter, self.assertRaisesRegex(ValueError, "役割型が一致しません"):
                adapter.load(target)


if __name__ == "__main__":
    unittest.main()
