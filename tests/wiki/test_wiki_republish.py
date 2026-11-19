"""切り戻し後のライブ世代と、再公開中に固定した読み取りを隔離 wiki で確かめる。"""

from hashlib import sha256
import json
import os
from pathlib import Path
import sqlite3
import subprocess
import sys
from tempfile import TemporaryDirectory
from time import monotonic
import unittest
from urllib.request import urlopen

from tests.wiki import test_wiki_live_return as fixture
from tests.wiki import test_wiki_publication_acceptance as reading

import wiki_apply as publish
from wiki_fsguard import WriteGuard

SCRIPTS = fixture.SCRIPTS
WORKER = """
import json, os, sys
from pathlib import Path
from time import monotonic, sleep
sys.path.insert(0, sys.argv[1])
from wiki_apply import Conflict, apply_plan
def checkpoint(point):
    if point != sys.argv[6]:
        return
    if not sys.argv[7]:
        os._exit(71)
    ready = Path(sys.argv[7])
    ready.touch()
    gate = ready.with_suffix(".gate")
    deadline = monotonic() + 150
    while not gate.is_file() and monotonic() < deadline:
        sleep(.03)
    if not gate.is_file():
        raise TimeoutError("再公開の再開合図を待ちきれません")
plan = json.loads(Path(sys.argv[3]).read_bytes())["plan"]
try:
    print(json.dumps(apply_plan(sys.argv[2], sys.argv[4], plan, sys.argv[5], checkpoint=checkpoint), ensure_ascii=False))
except Conflict as error:
    print(error, file=sys.stderr)
    sys.exit(4)
"""


class RepublishTests(fixture.LiveReturnFixture, unittest.TestCase):
    def cutback(self):
        path, doc = self.return_plan()
        self.assertEqual(self.return_cli(path, doc)["state"], "returned_live")
        self.assertIsNone(self.view()["release_id"])
        return path, doc

    def republish_plan(self, name, *include, exclude=()):
        candidate = self.base / f"{name}-candidate"
        args = [value for name in include for value in ("--include", name)]
        args.extend(value for name in exclude for value in ("--exclude", name))
        document = self.cli("plan-republish-live", "--wiki", self.wiki, "--raw-root", self.raw,
                            "--out", candidate, *args)
        path = self.base / f"{name}.json"
        path.write_bytes(publish.encoded(document))
        return path, candidate, document

    def republish_cli(self, plan, *, expected=0):
        path, candidate, doc = plan
        return self.cli("republish-live", "--wiki", self.wiki, "--source", candidate, "--plan", path,
                        "--expect-sha256", doc["plan_sha256"], expected=expected)

    def publisher(self, plan, point, marker=""):
        path, candidate, doc = plan
        return self.child((WORKER, SCRIPTS, self.wiki, path, candidate, doc["plan_sha256"], point, marker))

    def save_live(self, plan, key):
        child = subprocess.Popen([sys.executable, "-B", str(SCRIPTS / "wiki_apply.py"), "apply",
                                  "--apply-dir", plan["apply_dir"], "--expect-sha256", key],
                                 env=self.env, encoding="utf-8", stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        self.addCleanup(fixture.public_save.PublicSaveTests.close_worker, child)
        return child

    def source_rows(self, root):
        path = root / "ontology/ossie/records.jsonl"
        rows = (json.loads(line) for line in path.read_bytes().splitlines())
        return {(row["table"], row["id"]): row for row in rows}

    def test_scaled_writers_recovery_and_pinned_reads(self):
        start = monotonic()
        self.seed(scaled=True)
        initial = len([name for name in self.first_plan["files"] if fixture.is_page(name)])
        self.assertEqual((initial, sum(fixture.is_page(name) for name in self.before)), (195, 192))
        originals = {p.relative_to(self.raw).as_posix(): sha256(p.read_bytes()).hexdigest()
                     for p in self.raw.rglob("*") if p.is_file()}
        self.assertEqual(len(originals), 160)
        prior, approved, _ = self.draft("saved-during-publication", release=self.first)
        previous = self.stage(prior, "apply", "--expect-sha256", approved)["release_id"]
        last_archive = Path(self.view(previous)["read_root"])
        prior_rows = self.source_rows(last_archive)
        self.cutback()
        self.assertTrue(self.private.is_file())
        stale = self.republish_plan("stale")
        wanted = (("republished-ingest", "ingest"), ("republished-query", "query"),
                  ("republished-learn", "learn"), ("republished-extra", "query"))
        drafts = [self.draft(slug, operation) for slug, operation in wanted]
        marker = self.base / "republish-precheck"
        would_publish = self.publisher(stale, "after_initial_check", marker)
        self.wait_ready([marker], [would_publish])
        writers = [self.save_live(plan, key) for plan, key, _ in drafts]
        for child in writers:
            out, err = child.communicate(timeout=160)
            self.assertEqual(child.returncode, 0, out + err)
            self.assertEqual(json.loads(out)["state"], "applied")
        marker.with_suffix(".gate").touch()
        out, err = would_publish.communicate(timeout=120)
        self.assertEqual(would_publish.returncode, 4, out + err)
        self.assertIn("ライブ wiki が変わりました", err)
        self.assertIsNone(self.view()["release_id"])

        held, held_key, held_dir = self.draft("republished-pending")
        guard = WriteGuard(self.wiki)
        with guard.hold_lock(self.wiki / publish.AREA / "apply.lock"):
            delayed = self.stage(held, "apply", "--expect-sha256", held_key, "--wait", 0, expected=4)
        self.assertIn("保留しました", delayed)
        blocked = self.republish_plan("blocked")
        self.assertIn("保留されたライブ", self.republish_cli(blocked, expected=4))
        self.stage(held, "apply", "--expect-sha256", held_key)
        (self.wiki / "assets/republished-attachment.txt").write_bytes(b"approved stand-alone fixture")
        final = self.republish_plan("complete", "assets/republished-attachment.txt")
        path, candidate, doc = final
        self.assertNotIn("concepts/live-exclusive.md", doc["plan"]["files"])
        journaled = self.base / "republish-pointer"
        publisher = self.publisher(final, "pointer_written", journaled)
        self.wait_ready([journaled], [publisher])
        self.assertIsNone(self.view()["release_id"])
        self.assertEqual(self.view(previous)["release_id"], previous)
        pinned = self.cli("KabutoMarker", "--wiki", self.wiki, "--release-id", previous,
                          "--no-embed", "--json", script="wiki_search.py")
        self.assertEqual(pinned["release_id"], previous)
        late = self.cli("begin", "--wiki", self.wiki, "--raw-root", self.raw, "--name", "future", expected=4)
        self.assertIn("再公開が中断", late)
        publisher.kill()
        publisher.communicate(timeout=25)
        candidate.rename(self.base / "retired-candidate")
        ack = self.cli("recover", "--wiki", self.wiki)
        newest = ack["release_id"]
        self.assertEqual(self.republish_cli(final), ack)
        for plan, key, _ in [*drafts, (held, held_key, held_dir)]:
            verified = self.stage(plan, "apply", "--expect-sha256", key)
            self.assertEqual(verified["state"], "already_applied")
        self.assertEqual(self.view()["release_id"], newest)
        self.assertEqual(self.view(self.first)["release_id"], self.first)
        self.assertEqual(self.view(previous)["release_id"], previous)
        archive = Path(self.view(newest)["read_root"])
        self.assertEqual(publish.source_files(archive), doc["plan"]["files"])
        sealed = publish.manifest(guard, self.wiki / publish.AREA, newest)
        self.assertEqual(sealed["parent"], previous)
        self.assertFalse((archive / "concepts/live-exclusive.md").exists())
        index = (archive / "index.md").read_text(encoding="utf-8")
        log = (archive / "log.md").read_text(encoding="utf-8")
        rows = self.source_rows(archive)
        self.assertEqual({key: rows[key] for key in prior_rows}, prior_rows)
        wanted_pages = [(slug, directory) for (slug, _), (_, _, directory) in zip(wanted, drafts)]
        wanted_pages.append(("republished-pending", held_dir))
        with sqlite3.connect((archive / "ontology/ossie/wiki-data.sqlite").as_uri() + "?mode=ro", uri=True) as db:
            for slug, directory in wanted_pages:
                relative = f"{directory}/{slug}.md"
                self.assertEqual((archive / relative).read_bytes(), (self.wiki / relative).read_bytes())
                self.assertEqual(index.count(f"[[{directory}/{slug}]]"), 1, slug)
                self.assertEqual(sum(line.endswith(f" | {slug}") for line in log.splitlines()), 1, slug)
                self.assertEqual(db.execute("select count(*) from sem_articles where page = ?", (relative,)).fetchone(), (1,))
        db.close()
        self.assertEqual(len(rows) - len(prior_rows), len(wanted_pages))
        self.assertEqual(originals, {p.relative_to(self.raw).as_posix(): sha256(p.read_bytes()).hexdigest()
                                     for p in self.raw.rglob("*") if p.is_file()})
        report = os.environ.get("INFO_HIVE_REPUBLISH_REPORT")
        if report:
            Path(report).write_bytes(publish.encoded({
                "public_articles": initial, "public_files": len(self.first_plan["files"]),
                "initial_live_articles": sum(fixture.is_page(name) for name in self.before),
                "raw_files": len(originals), "live_concurrent_saves": len(writers),
                "live_saves_once_in_markdown_index_log_sqlite": len(wanted_pages),
                "ossie_rows_preserved": len(prior_rows), "new_ossie_rows": len(rows) - len(prior_rows),
                "old_candidate_stopped": True, "pending_blocks_transition": True,
                "after_pointer_recovered_without_source": True, "pinned_reads_survived": True,
                "private_page_excluded": True, "raw_files_unchanged": True, "seconds": round(monotonic() - start, 2),
            }))

    def test_recovery_boundaries(self):
        points = ("receipt_prepared", "pointer_written", "head_prepared", "return_archive_prepared",
                  "return_archived", "republish_marker_prepared", "republish_switched")
        original = self.base, self.wiki, self.raw, self.candidate, self.env
        for stop in points:
            with self.subTest(stop=stop), TemporaryDirectory(dir=self.base) as directory:
                self.base = Path(directory)
                self.wiki, self.raw, self.candidate = (self.base / name for name in ("wiki", "raw", "candidate"))
                self.env = fixture.env_for(self.base)
                try:
                    self.seed()
                    path, document = self.cutback()
                    new = self.republish_plan("attempt")
                    worker = self.publisher(new, stop)
                    output = worker.communicate(timeout=95)
                    self.assertEqual(worker.returncode, 71, output)
                    self.assertEqual(self.view(self.first)["release_id"], self.first)
                    if stop != "republish_switched":
                        self.assertIsNone(self.view()["release_id"])
                    if stop == "return_archived":
                        self.assertEqual(self.return_cli(path, document)["state"], "already_returned")
                    if stop == "pointer_written":
                        journal = self.wiki / publish.AREA / publish.JOURNAL
                        backup = journal.with_suffix(".bak")
                        journal.rename(backup)
                        self.assertIn("一致しません", self.cli("view", "--wiki", self.wiki, expected=1))
                        backup.rename(journal)
                    ack = self.cli("recover", "--wiki", self.wiki)
                    self.assertEqual(self.republish_cli(new), ack)
                    self.assertEqual(self.view()["release_id"], ack["release_id"])
                    self.assertEqual(self.return_cli(path, document)["state"], "already_returned")
                    if stop == "republish_switched":
                        self.cutback()
                        second = self.republish_plan("second")
                        later = self.republish_cli(second)
                        guard = WriteGuard(self.wiki)
                        entry = publish.manifest(guard, self.wiki / publish.AREA, later["release_id"])
                        self.assertEqual(entry["parent"], ack["release_id"])
                finally:
                    self.base, self.wiki, self.raw, self.candidate, self.env = original

    def test_private_edits_and_discarded_live_approval(self):
        self.seed()
        self.cutback()
        private_path = "concepts/live-exclusive.md"
        begun = self.cli("begin", "--wiki", self.wiki, "--raw-root", self.raw, "--name", "private-update")
        edit = Path(self.stage(begun, "edit", "--path", private_path)["path"])
        edit.write_bytes(edit.read_bytes() + "\nライブ専用の追記。\n".encode("utf-8"))
        finger = self.stage(begun, "diff", "--json")["plan_sha256"]
        self.stage(begun, "apply", "--expect-sha256", finger)
        path = self.wiki / "assets/badge.svg"
        path.write_bytes(path.read_bytes() + b"\n")
        log = self.wiki / "log.md"
        log.write_bytes(log.read_bytes() + "\n手作業で足したログ行。\n".encode("utf-8"))
        appended = self.cli("begin", "--wiki", self.wiki, "--raw-root", self.raw, "--name", "log-after-manual")
        self.stage(appended, "log-entry", "--op", "learn", "--title", "log-after-manual")
        self.stage(appended, "apply", "--expect-sha256", self.stage(appended, "diff", "--json")["plan_sha256"])
        self.assertIn("完了記録にない", self.cli("plan-republish-live", "--wiki", self.wiki, "--raw-root", self.raw,
                                             "--out", self.base / "unapproved", expected=4))
        self.assertIn("log.md", self.cli("plan-republish-live", "--wiki", self.wiki, "--raw-root", self.raw,
                                               "--out", self.base / "without-log", "--include", "assets/badge.svg", expected=4))
        outside = "concepts/untracked-new.md"
        (self.wiki / outside).write_text(fixture.frontmatter({"type": "concept", "title": "直書き"}, "直接追加。"),
                                         encoding="utf-8")
        draft = self.cli("begin", "--wiki", self.wiki, "--raw-root", self.raw, "--name", "untracked-update")
        work = Path(self.stage(draft, "edit", "--path", outside)["path"])
        work.write_bytes(work.read_bytes() + "\n通常保存による追記。\n".encode("utf-8"))
        self.stage(draft, "apply", "--expect-sha256", self.stage(draft, "diff", "--json")["plan_sha256"])
        self.assertIn(outside, self.cli("plan-republish-live", "--wiki", self.wiki, "--raw-root", self.raw,
                                         "--out", self.base / "without-exclude", "--include", "assets/badge.svg",
                                         "--include", "log.md", expected=4))
        ready = self.republish_plan("private-is-excluded", "assets/badge.svg", "log.md", exclude=[outside])
        self.assertNotIn(private_path, ready[2]["plan"]["files"])
        self.assertNotIn("ライブ専用の追記", ready[2]["markdown_diff"])
        self.assertIn("assets/badge.svg", ready[2]["modified"])
        plan, key, _ = self.draft("cancel-before-switch")
        guard = WriteGuard(self.wiki)
        with guard.hold_lock(self.wiki / publish.AREA / "apply.lock"):
            self.assertIn("保留しました", self.stage(plan, "apply", "--expect-sha256", key, "--wait", 0, expected=4))
        self.assertIn("保留されたライブ", self.republish_cli(ready, expected=4))
        cancelled = self.cli("discard-live-pending", "--wiki", self.wiki, "--plan-id", plan["plan_id"],
                             "--expect-sha256", key)
        self.assertEqual(cancelled["state"], "discarded")
        self.assertIn("取り消されています", self.stage(plan, "apply", "--expect-sha256", key, expected=4))
        ack = self.republish_cli(ready)
        snapshot = Path(self.view(ack["release_id"])["read_root"])
        self.assertFalse((snapshot / private_path).exists())
        self.assertFalse((snapshot / outside).exists())
        self.assertIn("ライブ専用の追記", self.private.read_text(encoding="utf-8"))

    @unittest.skipUnless(reading.HAS_MCP, "MCP と browse の結合試験に必要な依存がない")
    def test_mcp_and_running_browse_remain_pinned(self):
        self.seed()
        release = publish.resolve_publication(self.wiki)
        opts = {"wiki": str(self.wiki)}
        with reading.mcp_client() as tool, reading.browse_server(release) as browse:
            results = tool("query", {**opts, "query": "KabutoMarker"})
            old = results["release_id"]
            page = results["results"][0]["rel_path"]
            core, _ = browse.state.get(wait=3)
            html = browse.url(core.out_name[core.resolve(page, articles=True)["id"]])
            image = browse.url(core.asset_out["assets/badge.svg"])
            with urlopen(image, timeout=10) as response:
                previous_asset = response.read()
            self.cutback()
            begun = self.cli("begin", "--wiki", self.wiki, "--raw-root", self.raw, "--name", "republished-quote")
            draft = Path(self.stage(begun, "edit", "--path", page)["path"])
            draft.write_bytes(draft.read_bytes() + "\n再公開後の引用。\n".encode("utf-8"))
            key = self.stage(begun, "diff", "--json")["plan_sha256"]
            self.stage(begun, "apply", "--expect-sha256", key)
            receipt = self.republish_cli(self.republish_plan("changed"))
            self.assertEqual(tool("get_page", {**opts, "page": page})["release_id"], receipt["release_id"])
            self.assertIn("再公開後の引用", tool("get_page", {**opts, "page": page})["body"])
            self.assertNotIn("再公開後の引用", tool("get_page", {**opts, "page": page, "release_id": old})["body"])
            with urlopen(html, timeout=10) as response:
                self.assertNotIn("再公開後の引用", response.read().decode("utf-8"))
            with urlopen(image, timeout=10) as response:
                self.assertEqual(response.read(), previous_asset)


if __name__ == "__main__":
    unittest.main()
