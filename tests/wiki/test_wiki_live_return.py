"""公開後の通常保存からライブへ戻す境界を、隔離 wiki で確かめる。"""

from hashlib import sha256
import json
import os
from pathlib import Path
import shutil
import sqlite3
import subprocess
import sys
from tempfile import TemporaryDirectory
from time import monotonic, sleep
import unittest
from urllib.request import urlopen

from tests.wiki import test_wiki_public_save as public_save
from tests.wiki import test_wiki_publication_acceptance as reading

from rollout_trial import create_public_candidate, env_for, prepare_live, publish_existing
from publication_trial import frontmatter
import wiki_apply as publish
import wiki_live_apply as live
import wiki_live_return as cutback
from wiki_fsguard import WriteGuard

SCRIPTS = public_save.SCRIPTS
RETURN_WORKER = """
import json, os, sys
from pathlib import Path
from time import monotonic, sleep
sys.path.insert(0, sys.argv[1])
from wiki_live_return import apply
def checkpoint(point):
    if point != sys.argv[5]:
        return
    if not sys.argv[6]:
        os._exit(71)
    Path(sys.argv[6]).touch()
    deadline = monotonic() + 150
    while monotonic() < deadline:
        sleep(.05)
    raise TimeoutError("強制終了の合図を待ちきれません")
plan = json.loads(Path(sys.argv[3]).read_bytes())["plan"]
print(json.dumps(apply(sys.argv[2], plan, sys.argv[4], checkpoint=checkpoint), ensure_ascii=False))
"""


class LiveReturnFixture:
    def setUp(self):
        temporary = TemporaryDirectory(prefix="ih-live-return-")
        self.addCleanup(temporary.cleanup)
        self.base = Path(temporary.name)
        self.env = env_for(self.base)
        self.wiki = self.base / "wiki"
        self.raw = self.base / "raw"
        self.candidate = self.base / "candidate"

    def cli(self, *arguments, script="wiki_apply.py", expected=0):
        result = subprocess.run([sys.executable, "-B", str(SCRIPTS / script), *map(str, arguments)],
                                env=self.env, encoding="utf-8", capture_output=True, timeout=180)
        self.assertEqual(result.returncode, expected, result.stdout + result.stderr)
        if not result.stdout.strip():
            return result.stderr
        return json.loads(result.stdout)

    def seed(self, *, scaled=False):
        _, originals = prepare_live(self.base / "originals", 2, 160 if scaled else 2)
        originals.rename(self.raw)
        create_public_candidate(self.candidate, 96 if scaled else 2)
        with (self.candidate / "index.md").open("a", encoding="utf-8") as stream:
            stream.write("\n## シンセシス\n")
        if not scaled:
            (self.candidate / "assets/remove-after-publication.txt").write_text("廃止する添付", encoding="utf-8")
        shutil.copytree(self.candidate, self.wiki)
        # 最初から公開対象外の原本と記事を保持する。公開版にだけある記事も切り戻しで引き継ぐ。
        for path in sorted((self.wiki / "sources").glob("release-seed-*.md"))[:4]:
            path.unlink()
        self.private = self.wiki / "concepts/live-exclusive.md"
        self.private.write_text(frontmatter({"type": "concept", "title": "ライブ専用の知識"}, "ライブ専用の内容。"),
                                encoding="utf-8")
        self.live_graph_path = "graph/nodes.jsonl"
        graph = self.wiki / self.live_graph_path
        self.initial_live_graph = graph.read_bytes() + b"\n"
        graph.write_bytes(self.initial_live_graph)
        old = self.cli("begin", "--wiki", self.wiki, "--raw-root", self.raw, "--name", "before-cutover")
        self.stage(old, "log-entry", "--op", "learn", "--title", "before-cutover")
        old_approval = self.stage(old, "diff", "--json")["plan_sha256"]
        self.stage(old, "apply", "--expect-sha256", old_approval)
        shutil.copyfile(self.wiki / "log.md", self.candidate / "log.md")
        self.old_live = old, old_approval
        self.first_plan, self.first_receipt = publish_existing(self.wiki, self.candidate)
        self.first = self.first_receipt["release_id"]
        self.before = publish.live_files(WriteGuard(self.wiki))

    def stage(self, plan, command, *args, expected=0):
        return self.cli(command, "--apply-dir", plan["apply_dir"], *args, expected=expected)

    def draft(self, slug, operation="query", *, release=None):
        pinned = ["--release-id", release] if release else []
        plan = self.cli("begin", "--wiki", self.wiki, "--raw-root", self.raw, "--name", slug, *pinned)
        directory = "sources" if operation in ("ingest", "learn") else "synthesis"
        kind, heading = ("source", "ソース") if directory == "sources" else ("synthesis", "シンセシス")
        registered = self.stage(plan, "new", "--path", f"{directory}/{slug}.md")
        Path(registered["path"]).write_text(frontmatter({"type": kind, "title": slug, "sources": ["seed"]},
                                                        f"{slug} の根拠は [[sources/seed]]。"), encoding="utf-8")
        self.stage(plan, "index-add", "--file", "index.md", "--section", f"## {heading}", "--line",
                   f"- [[{directory}/{slug}]]: 切り戻し試験")
        self.stage(plan, "log-entry", "--op", operation, "--title", slug)
        return plan, self.stage(plan, "diff", "--json")["plan_sha256"], directory

    def return_plan(self, name="return-plan.json"):
        document = self.cli("plan-return-live", "--wiki", self.wiki, "--raw-root", self.raw)
        path = self.base / name
        path.write_bytes(publish.encoded(document))
        return path, document

    def return_cli(self, path, doc, *, expected=0):
        return self.cli("return-live", "--wiki", self.wiki, "--plan", path,
                        "--expect-sha256", doc["plan_sha256"], expected=expected)

    def child(self, args):
        child = subprocess.Popen([sys.executable, "-B", "-c", *map(str, args)], env=self.env, encoding="utf-8",
                                 stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        self.addCleanup(public_save.PublicSaveTests.close_worker, child)
        return child

    def start_return(self, path, doc, checkpoint, ready=""):
        return self.child((RETURN_WORKER, SCRIPTS, self.wiki, path, doc["plan_sha256"], checkpoint, ready))

    def wait_ready(self, markers, children):
        deadline = monotonic() + 140
        while not all(path.is_file() for path in markers):
            self.assertLess(monotonic(), deadline, "試行プロセスが検証位置まで進む")
            for child in children:
                if child.poll() is not None:
                    self.fail(child.communicate(timeout=5))
            sleep(.03)

    def view(self, identifier=None):
        args = ["--release-id", identifier] if identifier else []
        return self.cli("view", "--wiki", self.wiki, *args)

    def assert_once(self, slug, directory):
        self.assertTrue((self.wiki / directory / f"{slug}.md").is_file())
        index = (self.wiki / "index.md").read_text(encoding="utf-8")
        log = (self.wiki / "log.md").read_text(encoding="utf-8")
        self.assertEqual(index.count(f"[[{directory}/{slug}]]"), 1)
        self.assertEqual(sum(line.endswith(f" | {slug}") for line in log.splitlines()), 1)

class LiveReturnTests(LiveReturnFixture, unittest.TestCase):
    def test_scaled_concurrency_resume_and_pinned_reads(self):
        start = monotonic()
        self.seed(scaled=True)
        article_count = sum(is_page(name) for name in self.first_plan["files"])
        self.assertEqual(article_count, 195)
        self.assertEqual(sum(is_page(name) for name in self.before), 192)
        raw_before = {p.relative_to(self.raw).as_posix(): sha256(p.read_bytes()).hexdigest()
                      for p in self.raw.rglob("*") if p.is_file()}
        self.assertEqual(len(raw_before), 160)
        original, draft_return = self.return_plan("return-from-first.json")
        wanted = [("return-ingest", "ingest"), ("return-query", "query"),
                  ("return-learn", "learn"), ("return-other", "query")]
        plans = [self.draft(slug, operation, release=self.first) for slug, operation in wanted]
        gate = self.base / "publish-start"
        ready = [self.base / f"started-{i}" for i in range(len(plans))]
        workers = [self.child((public_save.WORKER, SCRIPTS, plan["apply_dir"], checksum, "", marker, gate))
                   for (plan, checksum, _), marker in zip(plans, ready)]
        self.wait_ready(ready, workers)
        self.assertIn("未適用の承認済み保存", self.return_cli(original, draft_return, expected=4))
        gate.touch()
        initial_states, observed = [], []
        for worker in workers:
            out, error = worker.communicate(timeout=180)
            self.assertEqual(worker.returncode, 0, out + error)
            result = json.loads(out)
            initial_states.append(result["state"])
            observed.append(result)
        results = []
        for (plan, checksum, _), outcome in zip(plans, observed):
            if outcome["state"] == "pending":
                outcome = self.cli("retry", "--wiki", self.wiki, "--plan-id", plan["plan_id"],
                                   "--expect-sha256", checksum)
            self.assertEqual(outcome["state"], "applied", outcome)
            results.append(outcome)
        self.assertIn("公開版が変わりました", self.return_cli(original, draft_return, expected=4))

        path, document = self.return_plan()
        latest = document["plan"]["release_id"]
        self.assertEqual(self.view()["release_id"], latest)
        archive = Path(self.view(latest)["read_root"])
        pinned_before = (archive / "sources/return-ingest.md").read_bytes()
        late, late_approval, _ = self.draft("return-unaccepted", release=latest)
        halfway = self.base / "copy-started"
        returning = self.start_return(path, document, "return_after_write:0", halfway)
        self.wait_ready([halfway], [returning])
        self.assertEqual(self.view()["release_id"], latest)
        self.assertIn("切り戻し中", self.stage(late, "apply", "--expect-sha256", late_approval, "--wait", 0, expected=4))
        late_record = self.wiki / publish.AREA / "saves" / f"{late['plan_id']}.json"
        self.assertFalse(late_record.exists())
        during = self.cli("return-query", "--wiki", self.wiki, "--no-embed", "--json", script="wiki_search.py")
        self.assertEqual(during["release_id"], latest)
        self.assertEqual(self.view(self.first)["release_id"], self.first)
        returning.kill()
        returning.communicate(timeout=30)
        restored = self.cli("recover", "--wiki", self.wiki)
        self.assertEqual(restored["release_id"], latest)
        self.assertEqual(restored["state"], "returned_live")
        self.assertEqual(publish.live_files(WriteGuard(self.wiki)), document["plan"]["after"])
        original_graph = self.wiki / publish.AREA / "return-preimages" / restored["plan_id"] / self.live_graph_path
        self.assertEqual(original_graph.read_bytes(), self.initial_live_graph)
        self.assertIsNone(self.view()["release_id"])
        self.assertTrue(self.private.is_file())
        self.assertFalse((self.wiki / "synthesis/return-unaccepted.md").exists())
        for (slug, _), (plan, checksum, directory), public_result in zip(wanted, plans, results):
            self.assert_once(slug, directory)
            repeated = self.cli("retry", "--wiki", self.wiki, "--plan-id", plan["plan_id"], "--expect-sha256", checksum)
            self.assertEqual(repeated["state"], "already_applied")
            self.assertEqual(repeated["release_id"], public_result["release_id"])
        with sqlite3.connect(self.wiki / "ontology/ossie/wiki-data.sqlite") as db:
            projected = db.execute("select count(*) from sem_articles where page like '%/return-%.md'").fetchone()[0]
        db.close()
        self.assertEqual(projected, 4)
        old, old_approval = self.old_live
        self.assertEqual(self.stage(old, "apply", "--expect-sha256", old_approval)["state"], "already_applied")

        new, checksum, directory = self.draft("saved-after-return")
        self.assertEqual(self.stage(new, "apply", "--expect-sha256", checksum)["state"], "applied")
        self.assert_once("saved-after-return", directory)
        self.assertEqual(self.return_cli(path, document)["state"], "already_returned")
        self.assert_once("saved-after-return", directory)
        first_pin = self.cli("saved-after-return", "--wiki", self.wiki, "--release-id", latest,
                             "--no-embed", "--json", script="wiki_search.py")
        default = self.cli("saved-after-return", "--wiki", self.wiki, "--no-embed", "--json", script="wiki_search.py")
        self.assertEqual(first_pin["release_id"], latest)
        self.assertNotIn("synthesis/saved-after-return.md", json.dumps(first_pin))
        self.assertIn("synthesis/saved-after-return.md", json.dumps(default))
        self.assertEqual((Path(self.view(latest)["read_root"]) / "sources/return-ingest.md").read_bytes(), pinned_before)
        self.assertEqual(raw_before, {p.relative_to(self.raw).as_posix(): sha256(p.read_bytes()).hexdigest()
                                     for p in self.raw.rglob("*") if p.is_file()})
        report = os.environ.get("INFO_HIVE_LIVE_RETURN_REPORT")
        if report:
            Path(report).write_bytes(publish.encoded({
                "public_articles": article_count, "baseline_public_files": len(self.first_plan["files"]),
                "baseline_live_articles": sum(is_page(name) for name in self.before), "raw_files": len(raw_before),
                "parallel_saves": len(plans), "parallel_first_pass": sorted(initial_states),
                "ossie_new_article_rows_retained": projected, "files_written_back": restored["written"],
                "already_applied_public_retries": len(plans), "accepted_pending_blocks_return": True,
                "stale_approval_blocks_return": True, "default_read_pinned_until_switch": True,
                "explicit_historical_read_after_return": True, "live_retry_after_further_write": True,
                "raw_bytes_unchanged": True, "initial_live_graph_preimage_verified": True,
                "seconds": round(monotonic() - start, 2),
            }))

    def test_recovers_at_each_boundary_and_refuses_corruption(self):
        for point in ("return_queued", "return_write_intent", "return_before_write:0", "return_write_live_receipt",
                      "return_write_receipt", "return_write_mode", "return_switched"):
            with self.subTest(point=point), TemporaryDirectory(dir=self.base) as directory:
                previous = self.base, self.wiki, self.raw, self.candidate, self.env
                self.base = Path(directory)
                self.wiki, self.raw, self.candidate = (self.base / name for name in ("wiki", "raw", "candidate"))
                self.env = env_for(self.base)
                try:
                    self.seed()
                    # 取り下げた添付をライブからも除く。公開後の追加・削除を同じ計画で戻す。
                    version = publish.resolve_publication(self.wiki)
                    revised = self.base / "revised"
                    shutil.copytree(version.root, revised)
                    (revised / "assets/remove-after-publication.txt").unlink()
                    (revised / "assets/new-after-publication.txt").write_text("新しい添付", encoding="utf-8")
                    _, child_release = publish_existing(self.wiki, revised, base=version)
                    path, doc = self.return_plan()
                    writer = self.start_return(path, doc, point)
                    output = writer.communicate(timeout=90)
                    self.assertEqual(writer.returncode, 71, output)
                    expected = None if point == "return_switched" else child_release["release_id"]
                    self.assertEqual(self.view()["release_id"], expected)
                    self.assertEqual(self.view(self.first)["release_id"], self.first)
                    if point == "return_before_write:0":
                        journal = self.wiki / publish.AREA / publish.RETURN_JOURNAL
                        held = journal.with_suffix(".bak")
                        journal.rename(held)
                        self.assertIn("日誌", self.cli("recover", "--wiki", self.wiki, expected=1))
                        held.rename(journal)
                    returned = self.return_cli(path, doc)
                    self.assertEqual(returned["state"], "returned_live")
                    self.assertEqual(returned["removed"], 1)
                    self.assertEqual(self.view()["release_id"], None)
                    self.assertFalse((self.wiki / "assets/remove-after-publication.txt").exists())
                    self.assertTrue((self.wiki / "assets/new-after-publication.txt").exists())
                    self.assertEqual(publish.live_files(WriteGuard(self.wiki)), doc["plan"]["after"])
                    self.assertEqual(self.return_cli(path, doc)["state"], "already_returned")
                finally:
                    self.base, self.wiki, self.raw, self.candidate, self.env = previous

    def test_live_drift_or_conflicting_initial_index_refuses(self):
        self.seed()
        self.assertIn("公開版を使う wiki", self.cli(self.wiki, "--formats", "sqlite",
                                                 script="wiki_graph_extract.py", expected=1))
        archive = self.view(self.first)["read_root"]
        self.assertIn("公開版を使う wiki", self.cli(archive, "--out", self.wiki / "graph", "--formats", "sqlite",
                                                 script="wiki_graph_extract.py", expected=1))
        path, doc = self.return_plan()
        self.private.write_text("公開中に外から編集されたライブ専用ページ。", encoding="utf-8")
        self.assertIn("ライブ wiki が変わりました", self.return_cli(path, doc, expected=4))
        self.assertEqual(self.view()["release_id"], self.first)
        self.assertEqual(self.private.read_text(encoding="utf-8"), "公開中に外から編集されたライブ専用ページ。")
        with self.assertRaisesRegex(publish.Conflict, "ライブ専用ファイル"):
            cutback.target_files({"index.md": "1"}, {}, {"index.md": "3"})

    @unittest.skipUnless(reading.HAS_MCP, "MCP と browse の結合試験に必要な依存がない")
    def test_pinned_mcp_citation_and_running_browse_keep_old_bytes(self):
        self.seed()
        release = publish.resolve_publication(self.wiki)
        options = {"wiki": str(self.wiki)}
        with reading.mcp_client() as tool, reading.browse_server(release) as browse:
            result = tool("query", {**options, "query": "KabutoMarker"})
            pin = result["release_id"]
            page = result["results"][0]["rel_path"]
            self.assertEqual((pin, page), (release.release_id, "sources/seed.md"))
            core, _ = browse.state.get(wait=3)
            name = core.out_name[core.resolve(page, articles=True)["id"]]
            with urlopen(browse.url(core.asset_out["assets/badge.svg"]), timeout=10) as response:
                asset_bytes = response.read()
            path, doc = self.return_plan()
            self.assertEqual(self.return_cli(path, doc)["state"], "returned_live")
            draft = self.cli("begin", "--wiki", self.wiki, "--raw-root", self.raw, "--name", "live-citation")
            copy = Path(self.stage(draft, "edit", "--path", page)["path"])
            copy.write_bytes(copy.read_bytes() + "\n切り戻し後の版。\n".encode("utf-8"))
            key = self.stage(draft, "diff", "--json")["plan_sha256"]
            self.stage(draft, "apply", "--expect-sha256", key)
            retained = tool("get_page", {**options, "page": page, "release_id": pin})
            self.assertEqual(retained["release_id"], pin)
            self.assertIn("旧版", retained["body"])
            self.assertNotIn("切り戻し後の版", retained["body"])
            with urlopen(browse.url(name), timeout=10) as response:
                self.assertNotIn("切り戻し後の版", response.read().decode("utf-8"))
            with urlopen(browse.url(core.asset_out["assets/badge.svg"]), timeout=10) as response:
                self.assertEqual(response.read(), asset_bytes)


def is_page(name):
    return live.is_page_path(name)


if __name__ == "__main__":
    unittest.main()
