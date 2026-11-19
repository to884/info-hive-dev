"""公開版の通常保存を、隔離した wiki と実際の CLI で確かめる。"""

from hashlib import sha256
import json
import os
from pathlib import Path
import sqlite3
import subprocess
import sys
from tempfile import TemporaryDirectory
from time import monotonic, sleep
import unittest
from unittest.mock import patch


ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "poc" / "ossie"))
from rollout_trial import publish, create_public_candidate, env_for, prepare_live, publish_existing
from publication_trial import frontmatter
from wiki_browse_fs import X
from wiki_fsguard import WriteGuard
from wiki_public_save import queue_save
from wiki_raw_roots import read_raw_roots

SCRIPTS = ROOT / "info-hive-wiki" / "skills" / "info-hive" / "scripts"
SEARCH_MARKER = "KabutoMarker"
EVIDENCE = "公開保存された合成製品は基盤に依存する。"
WORKER = """
import json, os, sys
from pathlib import Path
from time import monotonic, sleep
sys.path.insert(0, sys.argv[1])
from wiki_public_save import queue_save
import wiki_fsguard
if sys.argv[4] in {"save_before_link", "save_between_link_and_unlink"}:
    ordinary_publish = wiki_fsguard.publish_exclusive
    def stop_after_link(tmp, target):
        if target.parent.name == "saves" and target.suffix == ".json":
            if sys.argv[4] == "save_between_link_and_unlink":
                os.link(tmp, target)
            os._exit(71)
        ordinary_publish(tmp, target)
    wiki_fsguard.publish_exclusive = stop_after_link
def checkpoint(point):
    if point == sys.argv[4]:
        os._exit(71)
    if point == "save_prepared" and sys.argv[5]:
        marker, gate = map(Path, sys.argv[5:7])
        if not marker.exists():
            marker.touch()
            deadline = monotonic() + 100
            while not gate.exists():
                if monotonic() >= deadline:
                    raise TimeoutError("並行試行の開始を待ちきれません")
                sleep(.02)
print(json.dumps(queue_save(sys.argv[2], sys.argv[3], checkpoint=checkpoint), ensure_ascii=False))
"""


class PublicSaveTests(unittest.TestCase):
    def setUp(self):
        temporary = TemporaryDirectory(prefix="ih-public-save-")
        self.addCleanup(temporary.cleanup)
        self.base = Path(temporary.name)
        self.env = env_for(self.base)

    def seed(self, *, scaled=False):
        self.wiki, self.raw = prepare_live(self.base, 192 if scaled else 4, 160 if scaled else 4)
        self.raw_count = sum(path.is_file() for path in self.raw.rglob("*"))
        self.raw_bytes = sum(path.stat().st_size for path in self.raw.rglob("*") if path.is_file())
        candidate = self.base / "candidate"
        create_public_candidate(candidate, 96 if scaled else 2)
        with (candidate / "index.md").open("a", encoding="utf-8") as stream:
            stream.write("\n## シンセシス\n")
        plan, _ = publish_existing(self.wiki, candidate)
        self.initial = self.view()
        self.initial_files = len(plan["files"])
        self.live_index = (self.wiki / "index.md").read_bytes()
        self.live_log = (self.wiki / "log.md").read_bytes()

    def cli(self, *arguments, script="wiki_apply.py", expected=0):
        cmd = [sys.executable, "-B", str(SCRIPTS / script), *map(str, arguments)]
        if script == "wiki_apply.py" and arguments[0] == "diff":
            cmd.append("--json")
        result = subprocess.run(cmd, env=self.env, encoding="utf-8", capture_output=True, timeout=180)
        self.assertEqual(result.returncode, expected, result.stderr + result.stdout)
        return json.loads(result.stdout) if result.stdout else None

    def view(self, release_id=None):
        return self.cli("view", "--wiki", self.wiki, *(["--release-id", release_id] if release_id else []))

    def begin(self, slug, view=None):
        view = view or self.view()
        return self.cli("begin", "--wiki", self.wiki, "--raw-root", self.raw, "--name", slug,
                        "--release-id", view["release_id"])

    def stage(self, plan, command, *arguments):
        return self.cli(command, "--apply-dir", plan["apply_dir"], *arguments)

    def article(self, plan, directory, slug, page_type, body, raw=None, **metadata):
        document = {"type": page_type, "title": slug, "tags": ["fixture"], "created": "2026-11-19",
                    "updated": "2026-11-19", **metadata}
        if raw:
            document.update(raw=raw["raw_ref"], raw_sha256=raw["raw_sha256"])
        draft = self.stage(plan, "new", "--path", f"{directory}/{slug}.md")
        Path(draft["path"]).write_text(frontmatter(document, body), encoding="utf-8")
        section = {"source": "ソース", "entity": "エンティティ", "synthesis": "シンセシス"}[page_type]
        self.stage(plan, "index-add", "--file", "index.md", "--section", f"## {section}", "--line",
                   f"- [[{directory}/{slug}]]: 隔離試験の記事")

    def approval(self, plan, operation, slug):
        self.stage(plan, "log-entry", "--op", operation, "--title", slug)
        return self.stage(plan, "diff")["plan_sha256"]

    def apply(self, plan, approval, *arguments, expected=0):
        return self.stage_with_exit("apply", plan, approval, arguments, expected)

    def stage_with_exit(self, command, plan, approval, arguments, expected):
        identity = ("--apply-dir", plan["apply_dir"]) if command == "apply" else (
            "--wiki", self.wiki, "--plan-id", plan["plan_id"])
        return self.cli(command, *identity, "--expect-sha256", approval, *arguments, expected=expected)

    def retry(self, plan, approval, expected=0):
        return self.stage_with_exit("retry", plan, approval, (), expected)

    def simple(self, slug, operation="query", view=None):
        plan = self.begin(slug, view)
        self.article(plan, "synthesis", slug, "synthesis", f"{slug} の根拠は [[sources/seed]]。", sources=["seed"])
        return plan, self.approval(plan, operation, slug)

    def worker(self, plan, approval, *, stop="", marker="", gate=""):
        child = subprocess.Popen([sys.executable, "-B", "-c", WORKER, str(SCRIPTS), plan["apply_dir"],
                                  approval, stop, str(marker), str(gate)], env=self.env, encoding="utf-8",
                                 stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        self.addCleanup(self.close_worker, child)
        return child

    @staticmethod
    def close_worker(child):
        if child.poll() is None:
            child.kill()
        child.communicate(timeout=15)

    def raw_inputs(self):
        source = self.base / "public-source.txt"
        source.write_text(EVIDENCE, encoding="utf-8")
        original = self.cli("save", "--wiki", self.wiki, "--raw-root", self.raw, "--source", source,
                            "--name", source.name, script="wiki_raw_ingest.py")
        experience = self.base / "experience.json"
        experience.write_text(json.dumps({"id": "public-lesson", "task": "基盤を検査する", "outcome": "success",
                                          "verification": "版を照合した", "model": "fixture", "tools": "sha256",
                                          "scope": "合成資料", "actions": ["読んだ"]}, ensure_ascii=False), encoding="utf-8")
        learned = self.cli("--wiki", self.wiki, "capture", "--raw", self.raw, "--record", experience,
                           script="wiki_evolve.py")
        return original, learned

    def assert_once(self, root, operation, slug, directory):
        self.assertTrue((root / directory / f"{slug}.md").is_file(), slug)
        index = (root / "index.md").read_text(encoding="utf-8")
        log = (root / "log.md").read_text(encoding="utf-8")
        self.assertEqual(index.count(f"[[{directory}/{slug}]]"), 1, slug)
        self.assertEqual(sum(line.endswith(f" {operation} | {slug}") for line in log.splitlines()), 1, slug)
        with sqlite3.connect(root / "ontology/ossie/wiki-data.sqlite") as db:
            pages = db.execute("select count(*) from sem_articles where page = ?", (f"{directory}/{slug}.md",)).fetchone()
        db.close()
        self.assertEqual(pages, (1,), slug)

    @unittest.skipUnless(os.name == "nt", "Windows の同期移動を検査する")
    def test_failing_durable_move_does_not_queue_save(self):
        self.seed()
        plan, approval = self.simple("durable-move-error")
        points = []
        with patch.dict(os.environ, {"INFO_HIVE_DATA_DIR": self.env["INFO_HIVE_DATA_DIR"]}), \
                patch.object(X, "move_write_through", side_effect=OSError("同期移動の失敗")):
            with self.assertRaisesRegex(OSError, "同期移動の失敗"):
                queue_save(plan["apply_dir"], approval, checkpoint=points.append)
        self.assertNotIn("save_queued", points)
        self.assertEqual(self.cli("pending", "--wiki", self.wiki)["pending"], [])
        self.assertEqual(self.view()["release_id"], self.initial["release_id"])
        self.assertEqual(self.apply(plan, approval)["state"], "applied")
        self.assert_once(Path(self.view()["read_root"]), "query", "durable-move-error", "synthesis")

    @unittest.skipUnless(os.name == "posix", "POSIX の排他的なリンクの中断を検査する")
    def test_interrupted_link_is_recovered(self):
        self.seed()
        for recovery in ("pending", "retry", "apply"):
            with self.subTest(recovery=recovery):
                slug = f"interrupted-link-{recovery}"
                plan, approval = self.simple(slug)
                point = "save_before_link" if recovery == "apply" else "save_between_link_and_unlink"
                child = self.worker(plan, approval, stop=point)
                out, error = child.communicate(timeout=60)
                self.assertEqual(child.returncode, 71, out + error)
                folder = self.wiki / publish.AREA / "saves"
                record = folder / f"{plan['plan_id']}.json"
                temporary = folder / f".wiki-save-{plan['plan_id']}.tmp"
                if recovery == "apply":
                    self.assertFalse(record.exists())
                    self.assertEqual(temporary.stat().st_nlink, 1)
                    first = self.apply(plan, approval)
                else:
                    self.assertTrue(record.samefile(temporary))
                    self.assertEqual(record.stat().st_nlink, 2)
                    if recovery == "pending":
                        [pending] = self.cli("pending", "--wiki", self.wiki)["pending"]
                        self.assertEqual((pending["plan_id"], pending["plan_sha256"]), (plan["plan_id"], approval))
                        self.assertFalse(temporary.exists())
                    first = self.retry(plan, approval)
                self.assertEqual(first["state"], "applied")
                self.assertFalse(temporary.exists())
                self.assertEqual(record.stat().st_nlink, 1)
                again = self.retry(plan, approval)
                self.assertEqual((again["state"], again["release_id"]), ("already_applied", first["release_id"]))
                self.assert_once(Path(self.view()["read_root"]), "query", slug, "synthesis")

    def test_conflicts_require_fresh_approval(self):
        self.seed()
        one, two = (self.begin(title, self.initial) for title in ("winning-edit", "stale-edit"))
        for plan, title in ((one, "winning-edit"), (two, "stale-edit")):
            draft = Path(self.stage(plan, "edit", "--path", "concepts/platform.md")["path"])
            draft.write_text(draft.read_text(encoding="utf-8") + f"\n{title} の追記。\n", encoding="utf-8")
        first = self.approval(one, "learn", "winning-edit")
        second = self.approval(two, "learn", "stale-edit")
        dependency = self.begin("stale-reference", self.initial)
        self.stage(dependency, "depends-on", "--path", "concepts/platform.md")
        basis = self.approval(dependency, "query", "stale-reference")
        implicit = self.begin("stale-link", self.initial)
        self.article(implicit, "synthesis", "stale-link", "synthesis", "根拠は [[concepts/platform]]。")
        implicit_approval = self.approval(implicit, "query", "stale-link")
        winning = self.apply(one, first)
        for plan, approval, reason in ((two, second, "ページの基準版"), (dependency, basis, "読んだページ"),
                                      (implicit, implicit_approval, "下書きから参照したページ")):
            self.assertIn(reason, self.apply(plan, approval, expected=4)["reason"])
            self.assertIn(reason, self.retry(plan, approval, expected=4)["reason"])
        self.assertEqual(self.view()["release_id"], winning["release_id"])
        root = Path(self.view()["read_root"])
        page = (root / "concepts/platform.md").read_text(encoding="utf-8")
        self.assertIn("winning-edit", page)
        self.assertNotIn("stale-edit", page)
        self.assertFalse((root / "synthesis/stale-link.md").exists())
        publish.retire(self.wiki, self.initial["release_id"])
        self.assertIn("取り下げられました", self.retry(two, second, expected=4)["reason"])
        dropped = self.cli("discard-save", "--wiki", self.wiki, "--plan-id", two["plan_id"], "--expect-sha256", second)
        self.assertEqual(dropped["state"], "discarded")
        self.assertNotIn(two["plan_id"], json.dumps(self.cli("pending", "--wiki", self.wiki)))

    def test_published_raw_roots_and_raw_drift(self):
        self.seed()
        original = self.raw / "standalone-proof.txt"
        original.write_bytes(b"isolated original")
        digest = sha256(original.read_bytes()).hexdigest()
        plan = self.begin("original-at-a")
        self.article(plan, "sources", "original-at-a", "source", "隔離した原本。", raw={
            "raw_ref": "raw/standalone-proof.txt", "raw_sha256": digest})
        approval = self.approval(plan, "ingest", "original-at-a")
        first = self.apply(plan, approval)
        roots, failures = read_raw_roots(self.wiki)
        self.assertFalse(failures)
        self.assertIn(self.raw, roots)

        other = self.base / "raw-b"
        other.mkdir()
        edit = self.cli("begin", "--wiki", self.wiki, "--raw-root", other, "--name", "edit-at-b",
                        "--release-id", first["release_id"])
        draft = Path(self.stage(edit, "edit", "--path", "sources/original-at-a.md")["path"])
        draft.write_text(draft.read_text(encoding="utf-8") + "\n別の根から点検した。\n", encoding="utf-8")
        approved = self.approval(edit, "learn", "edit-at-b")
        original.write_bytes(b"changed outside the wiki")
        drifted = self.apply(edit, approved, expected=4)
        self.assertIn("原本の版", drifted["reason"])
        self.assertEqual(self.view()["release_id"], first["release_id"])
        original.write_bytes(b"isolated original")
        resumed = self.retry(edit, approved)
        self.assertEqual(resumed["state"], "applied")
        self.assertEqual(self.retry(edit, approved)["release_id"], resumed["release_id"])
        self.assertIn(other, read_raw_roots(self.wiki)[0])

    def test_quarantined_candidate_and_simultaneous_retry(self):
        self.seed()
        plan, approval = self.simple("retry-same-approval")
        torn = self.worker(plan, approval, stop="after_journal")
        self.assertEqual(torn.communicate(timeout=180)[0], "")
        self.assertEqual(torn.returncode, 71)
        area = self.wiki / publish.AREA
        journal = json.loads((area / publish.JOURNAL).read_bytes())
        broken = area / "staging" / journal["stage"] / "wiki" / "synthesis/retry-same-approval.md"
        broken.write_text("故障注入で指紋を変えた。", encoding="utf-8")
        Path(plan["apply_dir"]).rename(self.base / "retired-broken-draft")
        args = [sys.executable, "-B", str(SCRIPTS / "wiki_apply.py"), "retry", "--wiki", str(self.wiki),
                "--plan-id", plan["plan_id"], "--expect-sha256", approval]
        children = [subprocess.Popen(args, env=self.env, encoding="utf-8", stdout=subprocess.PIPE,
                                     stderr=subprocess.PIPE) for _ in range(2)]
        for child in children:
            self.addCleanup(self.close_worker, child)
        results = []
        for child in children:
            out, error = child.communicate(timeout=180)
            self.assertEqual(child.returncode, 0, out + error)
            results.append(json.loads(out))
        self.assertEqual({result["state"] for result in results}, {"applied", "already_applied"})
        self.assertEqual(results[0]["release_id"], results[1]["release_id"])
        self.assertTrue((area / "rejected" / f"{journal['plan_id']}.json").is_file())
        self.assert_once(Path(self.view()["read_root"]), "query", "retry-same-approval", "synthesis")

    def test_scaled_parallel_and_crash(self):
        started = monotonic()
        self.seed(scaled=True)
        root = Path(self.initial["read_root"])
        page_count = sum(len(list((root / directory).glob("*.md"))) for directory in ("sources", "entities", "concepts"))
        self.assertEqual((page_count, self.raw_count), (195, 160))
        pinned_seed = (root / "sources/seed.md").read_bytes()
        wanted, plans = [], []

        original, learned = self.raw_inputs()
        ingest = self.begin("public-ingest", self.initial)
        self.article(ingest, "sources", "public-ingest", "source", EVIDENCE, raw=original)
        self.article(ingest, "entities", "public-product", "entity", "この製品は [[concepts/platform]] に依存する。",
                     kind="product", sources=["public-ingest"], graph={
                         "node_id": "product:public-product", "relationships": [{"predicate": "depends_on",
                         "object": "concept:platform", "source": "public-ingest", "evidence": EVIDENCE,
                         "confidence": "high", "status": "current"}]})
        plans.append((ingest, self.approval(ingest, "ingest", "public-ingest")))
        wanted.append(("ingest", "public-ingest", "sources"))

        search = self.cli(SEARCH_MARKER, "--wiki", self.wiki, "--release-id", self.initial["release_id"],
                          "--no-embed", "--json", script="wiki_search.py")
        self.assertIn("sources/seed.md", json.dumps(search))
        query = self.begin("public-query", self.initial)
        self.stage(query, "depends-on", "--path", "sources/seed.md")
        self.article(query, "synthesis", "public-query", "synthesis", f"{SEARCH_MARKER} の根拠は [[sources/seed]]。",
                     sources=["seed"])
        plans.append((query, self.approval(query, "query", "public-query")))
        wanted.append(("query", "public-query", "synthesis"))

        learn = self.begin("public-learn", self.initial)
        self.article(learn, "sources", "public-learn", "source", "基盤の検査経験。", raw=learned)
        draft = Path(self.stage(learn, "edit", "--path", "concepts/shared.md")["path"])
        draft.write_text(draft.read_text(encoding="utf-8") + "\n[[sources/public-learn]] の経験を参照。\n", encoding="utf-8")
        plans.append((learn, self.approval(learn, "learn", "public-learn")))
        wanted.append(("learn", "public-learn", "sources"))
        plans.append(self.simple("parallel-note", view=self.initial))
        wanted.append(("query", "parallel-note", "synthesis"))

        gate = self.base / "go"
        markers = [self.base / f"ready-{i}" for i in range(len(plans))]
        children = [self.worker(plan, approval, marker=marker, gate=gate)
                    for (plan, approval), marker in zip(plans, markers)]
        deadline = monotonic() + 100
        while not all(marker.exists() for marker in markers):
            self.assertLess(monotonic(), deadline, "4件すべてが同一の基準版で候補を作る")
            for child in children:
                if child.poll() is not None:
                    self.fail(child.communicate(timeout=5))
            sleep(.02)
        gate.touch()
        states = []
        for child, (plan, approval) in zip(children, plans):
            out, err = child.communicate(timeout=180)
            self.assertEqual(child.returncode, 0, out + err)
            result = json.loads(out)
            states.append(result["state"])
            if result["state"] == "pending":
                result = self.retry(plan, approval)
            self.assertEqual(result["state"], "applied", result)
            self.assertEqual(self.retry(plan, approval)["release_id"], result["release_id"])

        pending, approval = self.simple("waiting-note")
        guard = WriteGuard(self.wiki)
        with guard.hold_lock(self.wiki / publish.AREA / "apply.lock"):
            postponed = self.apply(pending, approval, "--wait", 0, expected=4)
        self.assertEqual(postponed["state"], "pending")
        self.assertIn(pending["plan_id"], json.dumps(self.cli("pending", "--wiki", self.wiki)))
        Path(pending["apply_dir"]).rename(self.base / "retired-pending-draft")
        self.assertEqual(self.retry(pending, approval)["state"], "applied")
        wanted.append(("query", "waiting-note", "synthesis"))

        crashes = ["save_queued", "after_journal", "pointer_written"]
        for point in crashes:
            slug = point.replace("_", "-")
            plan, approved = self.simple(slug)
            child = self.worker(plan, approved, stop=point)
            output = child.communicate(timeout=180)
            self.assertEqual(child.returncode, 71, output)
            Path(plan["apply_dir"]).rename(self.base / f"retired-{slug}")
            resumed = self.retry(plan, approved)
            self.assertIn(resumed["state"], ("applied", "already_applied"), resumed)
            self.assertEqual(self.retry(plan, approved)["release_id"], resumed["release_id"])
            wanted.append(("query", slug, "synthesis"))

        final = self.view()
        active = Path(final["read_root"])
        self.assertNotEqual(final["release_id"], self.initial["release_id"])
        for operation, slug, directory in wanted:
            self.assert_once(active, operation, slug, directory)
        self.assertIn("[[sources/public-learn]]", (active / "concepts/shared.md").read_text(encoding="utf-8"))
        for slug, original in (("public-ingest", original), ("public-learn", learned)):
            self.assertIn(original["raw_sha256"], (active / f"sources/{slug}.md").read_text(encoding="utf-8"))
            raw_file = self.base / original["raw_ref"]
            self.assertEqual(original["raw_sha256"], sha256(raw_file.read_bytes()).hexdigest())
        with sqlite3.connect(active / "graph/graph.sqlite") as db:
            edges = db.execute("select predicate, object, source, evidence from edges where subject = ? and predicate = ?",
                               ("product:public-product", "depends_on")).fetchall()
        db.close()
        self.assertEqual(edges, [("depends_on", "concept:platform", "public-ingest", EVIDENCE)])
        before, after = {}, {}
        for snapshot, data in ((root, before), (active, after)):
            for line in (snapshot / "ontology/ossie/records.jsonl").read_text(encoding="utf-8").splitlines():
                row = json.loads(line)
                data[(row["table"], row["id"])] = row
        self.assertTrue(before)
        self.assertEqual({key: after[key] for key in before}, before)
        article_changes = [row for key, row in after.items() if key not in before]
        self.assertTrue(all(row["table"] == "articles" for row in article_changes))
        self.assertEqual(len(article_changes), 10)
        self.assertEqual((Path(self.view(self.initial["release_id"])["read_root"]) / "sources/seed.md").read_bytes(), pinned_seed)
        self.assertEqual((self.wiki / "index.md").read_bytes(), self.live_index)
        self.assertEqual((self.wiki / "log.md").read_bytes(), self.live_log)
        self.assertIn("synthesis/public-query.md", json.dumps(self.cli(
            SEARCH_MARKER, "--wiki", self.wiki, "--no-embed", "--json", script="wiki_search.py")))
        report = os.environ.get("INFO_HIVE_PUBLIC_SAVE_REPORT")
        if report:
            Path(report).write_text(json.dumps({
                "baseline_articles": page_count, "baseline_public_files": self.initial_files,
                "baseline_raw_files": self.raw_count, "baseline_raw_bytes": self.raw_bytes,
                "parallel_first_pass": sorted(states), "crash_recovery": crashes,
                "exactly_once_in_article_index_log_sem_articles": len(wanted),
                "new_sem_article_versions": len(article_changes), "preserved_sem_rows": len(before),
                "typed_edge_with_evidence": len(edges), "pending_retry_without_drafts": True,
                "explicit_old_release_verified": True, "live_index_and_log_unchanged": True,
                "seconds": round(monotonic() - started, 2),
            }, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


if __name__ == "__main__":
    unittest.main()
