"""隔離した合成 wiki で公開の共通処理と実際の読み口を確かめる。"""

from contextlib import closing, contextmanager
import importlib.util
import json
import os
from pathlib import Path
from queue import Queue
import shutil
import sqlite3
import subprocess
import sys
from tempfile import TemporaryDirectory
import threading
import time
import unittest
from urllib.error import HTTPError
from urllib.request import urlopen

ROOT = Path(__file__).resolve().parents[2]
POC = ROOT / "poc" / "ossie"
SCRIPTS = ROOT / "info-hive-wiki" / "skills" / "info-hive" / "scripts"
LEGACY_OUTPUT = Path(__file__).with_name("fixtures") / "ossie-publication-legacy.json"
sys.path[:0] = [str(POC), str(SCRIPTS)]

HAS_YAML = importlib.util.find_spec("yaml") is not None
HAS_MCP = all(importlib.util.find_spec(name) is not None for name in ("mcp", "tantivy", "numpy", "usearch"))
if HAS_YAML:
    import publication_trial as fixture
    import wiki_apply as publish
    import wiki_browse
    import wiki_graph_query

PRODUCT_ID = "product:"
TASKS = (
    ("neighbors", {"node": "concept:platform"}),
    ("edges", {}),
    ("facts", {}),
    ("path", {"goal": "concept:platform"}),
)


@contextmanager
def browse_server(release, live_root=None):
    wiki_browse._load()
    core = wiki_browse.core
    app = wiki_browse.App(release.root if release else live_root, 30,
                          assets=core.load_assets(), frame_assets=core.load_frame_assets(),
                          publication=release)
    server = wiki_browse._Server(("127.0.0.1", 0), wiki_browse.Handler)
    server.app = app
    app.httpd = server
    app.port = server.server_address[1]
    worker = threading.Thread(target=server.serve_forever, daemon=True)
    worker.start()
    try:
        yield app
    finally:
        server.shutdown()
        worker.join(10)
        server.server_close()


@contextmanager
def mcp_client():
    from starlette.testclient import TestClient
    from wiki_mcp_server import Activity, build_app

    class NoLegacyIndex:
        activity = Activity()

        def query_wiki(self, *_):
            raise AssertionError("公開版の検索は従来の索引を使わない")

        def wiki(self, *_):
            raise AssertionError("公開版の取得は従来の索引を使わない")

    port = 18041
    token = "local-test-token"
    headers = {"Authorization": f"Bearer {token}", "Accept": "application/json, text/event-stream"}
    with TestClient(build_app(NoLegacyIndex(), token, port), base_url=f"http://127.0.0.1:{port}",
                    headers=headers) as client:
        req_id = 0

        def send(method, params, notice=False):
            nonlocal req_id
            req_id += 1
            request = {"jsonrpc": "2.0", "method": method, "params": params}
            if not notice:
                request["id"] = req_id
            return client.post("/mcp", json=request)

        response = send("initialize", {"protocolVersion": "2025-06-18", "capabilities": {},
                                      "clientInfo": {"name": "isolated-test", "version": "1"}})
        response.raise_for_status()
        client.headers["Mcp-Session-Id"] = response.headers["Mcp-Session-Id"]
        client.headers["MCP-Protocol-Version"] = response.json()["result"]["protocolVersion"]
        send("notifications/initialized", {}, notice=True).raise_for_status()

        def tool(name, arguments, *, error=False):
            response = send("tools/call", {"name": name, "arguments": arguments})
            response.raise_for_status()
            result = response.json()["result"]
            if error:
                return result.get("isError", False), result["content"][0]["text"]
            if result.get("isError"):
                raise AssertionError(result)
            return result.get("structuredContent") or json.loads(result["content"][0]["text"])

        yield tool


@unittest.skipUnless(HAS_YAML, "公開版の試験には PyYAML が必要です")
class PublicationAcceptance(unittest.TestCase):
    def setUp(self):
        root = TemporaryDirectory(prefix="wiki-publish-test-")
        self.addCleanup(root.cleanup)
        self.root = Path(root.name)
        self.wiki = self.root / "wiki"
        base = self.root / "seed"
        base.mkdir()
        fixture.initial(self.wiki, base)
        self.base = publish.resolve_publication(self.wiki)
        self.legacy = self.root / "unpublished-baseline"
        shutil.copytree(self.base.root, self.legacy)

    def intent(self, slug, part="CONCURRENT"):
        return {"definition_id": self.base.definition_id,
                "intent": {"source": slug, "maker": "verified-maker", "part": part,
                           "quote": f"{slug} の出典は基盤への依存を確認した。"}}

    def test_live_browse_stops_after_cutover_and_after_missing_pointer(self):
        with browse_server(None, self.legacy) as app:
            url = f"http://127.0.0.1:{app.port}/{app.view_token}/w/{app.key}/index.html"
            with urlopen(url, timeout=10) as response:
                self.assertEqual(response.status, 200)
            baseline = publish.capture_live_base(self.legacy)
            plan = publish.build_plan(self.legacy, self.base.root, live_base=baseline)
            publish.apply_plan(self.legacy, self.base.root, plan, publish.digest(publish.encoded(plan)))
            with self.assertRaises(HTTPError) as stopped:
                urlopen(url, timeout=10)
            self.assertEqual(stopped.exception.code, 410)
            stopped.exception.close()
            pointer = self.legacy / publish.AREA / "current"
            pointer.rename(pointer.with_name("missing-for-test"))
            with self.assertRaises(HTTPError) as broken:
                urlopen(url, timeout=10)
            self.assertEqual(broken.exception.code, 410)
            broken.exception.close()

    def test_verified_legacy_release_can_be_read_and_upgraded(self):
        wiki = self.legacy
        files = publish.source_files(self.base.root)
        plan_id = "1" * 32
        definition_id = publish.definition_fingerprint(files)
        legacy_plan = {"format": 1, "plan_id": plan_id, "wiki": str(wiki), "base": None,
                       "base_definition": None, "definition_id": definition_id, "files": files}
        entry = publish.encoded({"parent": None, "definition_id": definition_id, "plan_id": plan_id, "files": files})
        release_id = publish.digest(entry)
        area = wiki / publish.AREA
        release = area / "releases" / release_id
        shutil.copytree(self.base.root, release / "wiki")
        (release / "manifest.json").write_bytes(entry)
        (area / "receipts").mkdir()
        (area / "current").write_bytes((release_id + "\n").encode("ascii"))
        record = area / "receipts" / f"{plan_id}.json"
        prepared = publish.encoded({"plan_id": plan_id, "plan_sha256": publish.digest(publish.encoded(legacy_plan)),
                                    "release_id": release_id})
        record.write_bytes(prepared)
        read = publish.resolve_publication(wiki)
        self.assertEqual(read.release_id, release_id)
        record.write_bytes(publish.encoded({**json.loads(prepared), "plan_sha256": "f" * 64}))
        with self.assertRaisesRegex(publish.PublicationError, "完了記録"):
            publish.resolve_publication(wiki)
        record.write_bytes(prepared)
        # 旧形式へ先頭記録だけが追加された中断点も、既存の公開版から検証できる。
        (area / publish.HEAD).write_bytes(prepared)
        self.assertEqual(publish.resolve_publication(wiki), read)
        self.assertIsNone(publish.recover(wiki))
        updated = publish.build_plan(wiki, self.base.root, base=read)
        applied = publish.apply_plan(wiki, self.base.root, updated, publish.digest(publish.encoded(updated)))
        self.assertEqual(publish.resolve_publication(wiki).release_id, applied["release_id"])
        self.assertEqual(publish.resolve_publication(wiki, release_id), read)
        self.assertTrue((wiki / publish.MARKER).is_file())

    def worker(self, value, plan_id, *options):
        path = self.root / f"{plan_id}.json"
        path.write_bytes(publish.encoded(value))
        env = {**os.environ, "TEMP": str(self.root), "TMP": str(self.root)}
        process = subprocess.Popen([sys.executable, "-B", "-X", "utf8", str(POC / "publication_trial.py"),
                                    str(self.wiki), str(path), "--plan-id", plan_id, *options],
                                   stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True, encoding="utf-8", env=env)
        self.addCleanup(self.close_worker, process)
        return process

    @staticmethod
    def close_worker(worker):
        if worker.poll() is None:
            worker.kill()
        worker.communicate(timeout=20)

    def finished(self, worker, code):
        out, err = worker.communicate(timeout=50)
        self.assertEqual(worker.returncode, code, err)
        return json.loads(out) if out.strip() else None

    def cli(self, program, *args):
        result = subprocess.run([sys.executable, "-B", "-X", "utf8", str(SCRIPTS / program), *map(str, args)],
                                capture_output=True, encoding="utf-8", timeout=50)
        self.assertEqual(result.returncode, 0, result.stderr)
        return result.stdout

    def reads(self, wiki, *, release_id=None, part="BASE"):
        product = PRODUCT_ID + fixture.product_slug("verified-maker", part)
        args = {"edges": {"subject": product}, "facts": {"about": product}, "path": {"start": product}}
        result = {op: wiki_graph_query.run_query(wiki, op, release_id=release_id, **params, **args.get(op, {}))
                  for op, params in TASKS}
        for row in result.values():
            row.pop("release_id", None)
        return result

    def test_processes_rebase_same_entity_and_claim_and_keep_unrelated_ingest(self):
        separate = [self.root / "ready-one", self.root / "ready-two"]
        go = self.root / "go"
        one = self.worker(self.intent("one"), "1"*32, "--ready", str(separate[0]), "--go", str(go))
        two = self.worker(self.intent("two"), "2"*32, "--ready", str(separate[1]), "--go", str(go))
        deadline = time.monotonic() + 25
        while not all(file.is_file() for file in separate):
            if time.monotonic() >= deadline or any(p.poll() is not None for p in (one, two)):
                self.fail("並行版の準備が終わらない")
            time.sleep(0.04)
        self.assertEqual([path.read_text(encoding="utf-8") for path in separate], [self.base.release_id]*2)
        fixture.ingest(self.wiki, self.intent("independent", "OTHER"), "3"*32)
        go.touch()
        results = [self.finished(worker, 0) for worker in (one, two)]
        self.assertTrue(all(result["attempts"] >= 2 for result in results))
        version = publish.resolve_publication(self.wiki)
        with closing(sqlite3.connect(version.root / "ontology" / "ossie" / "wiki-data.sqlite")) as db:
            group = db.execute("""
                SELECT count(DISTINCT e.id), count(DISTINCT c.id), count(DISTINCT x.article_id)
                FROM sem_entities e JOIN sem_claims c ON c.subject_entity_id = e.id
                JOIN sem_heads h ON h.claim_id = c.id JOIN sem_supports s ON s.revision_id = h.revision_id
                JOIN sem_evidence x ON x.id = s.evidence_id WHERE e.name = 'CONCURRENT'
            """).fetchone()
            self.assertEqual(group, (1, 1, 2))
            self.assertEqual(db.execute("SELECT count(*) FROM sem_entities WHERE name = 'OTHER'").fetchone()[0], 1)
        log = (version.root / "log.md").read_text(encoding="utf-8")
        self.assertEqual([log.count(f"[[sources/{slug}]]") for slug in ("one", "two", "independent")], [1, 1, 1])
        current = self.reads(self.wiki)
        before = self.reads(self.legacy)
        # nodes の隣接先に新しい製品が加わる。それ以外の固定製品の関係・引用は契約どおり。
        for name in ("edges", "facts", "path"):
            self.assertEqual(current[name], before[name])
        public_neighbors = current["neighbors"]["neighbors"]
        for neighbor in before["neighbors"]["neighbors"]:
            self.assertIn(neighbor, public_neighbors)
        self.assertEqual(self.reads(self.wiki, release_id=self.base.release_id), before)

    def test_recover_after_killing_writer_before_and_after_pointer(self):
        for index, checkpoint in enumerate(("before_pointer", "after_pointer"), start=5):
            with self.subTest(checkpoint=checkpoint):
                old = publish.resolve_publication(self.wiki)
                stamp = str(index)*32
                approved = self.intent(f"crash-{index}")
                self.finished(self.worker(approved, stamp, "--crash", checkpoint), 71)
                journal = fixture.read_json(self.wiki / publish.AREA / "publication.journal.json")
                live = publish.resolve_publication(self.wiki)
                after = checkpoint == "after_pointer"
                self.assertEqual(live.release_id, journal["release_id"] if after else old.release_id)
                self.assertEqual((live.root / "sources" / f"crash-{index}.md").exists(), after)
                if not after:
                    with self.assertRaisesRegex(publish.PublicationError, "公開済み"):
                        publish.resolve_publication(self.wiki, journal["release_id"])
                repaired = publish.recover(self.wiki)
                self.assertEqual(repaired["release_id"], journal["release_id"])
                self.assertIsNone(publish.recover(self.wiki))
                replay = fixture.ingest(self.wiki, approved, stamp)
                self.assertEqual(replay["release_id"], repaired["release_id"])
                version = publish.resolve_publication(self.wiki)
                log = (version.root / "log.md").read_text(encoding="utf-8")
                self.assertEqual(log.count(f"[[sources/crash-{index}]]"), 1)
                with closing(sqlite3.connect(version.root / "ontology" / "ossie" / "wiki-data.sqlite")) as db:
                    self.assertEqual(db.execute("SELECT count(*) FROM sem_evidence WHERE original_source = ?",
                                                (f"crash-{index}",)).fetchone()[0], 1)

    def test_stale_definition_and_approval_tamper_do_not_publish(self):
        state = fixture.state_of(self.base)
        state["definition"]["label"] = "改訂した定義"
        work = self.root / "new"
        work.mkdir()
        plan = fixture.prepare(self.wiki, work, self.base, state, "a"*32)
        checksum = publish.digest(publish.encoded(plan))
        invalid = {**plan, "definition_id": self.base.definition_id}
        with self.assertRaisesRegex(publish.PublicationError, "定義の指紋"):
            publish.apply_plan(self.wiki, work, invalid, publish.digest(publish.encoded(invalid)))
        (work / "index.md").write_text("# changed outside approval", encoding="utf-8")
        with self.assertRaisesRegex(publish.PublicationError, "成果物が変更"):
            publish.apply_plan(self.wiki, work, plan, checksum)
        self.assertEqual(publish.resolve_publication(self.wiki), self.base)
        (work / "index.md").write_bytes((self.base.root / "index.md").read_bytes())
        second = self.root / "approved"
        second.mkdir()
        result = fixture.publish_state(self.wiki, second, self.base, state, "b"*32)
        self.finished(self.worker(self.intent("stale"), "c"*32), 4)
        self.assertEqual(publish.resolve_publication(self.wiki).release_id, result["release_id"])

    def test_rejects_changed_staging_and_recovers_corrupted_candidate(self):
        state = fixture.state_of(self.base)
        fixture.insert(state, self.intent("pending")["intent"])
        work = self.root / "untrusted"
        work.mkdir()

        def corrupt_staging(checkpoint):
            if checkpoint == "before_journal":
                root = self.wiki / publish.AREA / "staging"
                candidate = next(root.glob("*/wiki/index.md"))
                candidate.write_bytes(b"damaged")

        with self.assertRaisesRegex(publish.PublicationError, "指紋が一致しません"):
            fixture.publish_state(self.wiki, work, self.base, state, "e"*32, checkpoint=corrupt_staging)
        journal_path = self.wiki / publish.AREA / "publication.journal.json"
        self.assertFalse(journal_path.exists())
        self.finished(self.worker(self.intent("corrupt"), "f"*32, "--crash", "before_pointer"), 71)
        journal = fixture.read_json(journal_path)
        candidate = self.wiki / publish.AREA / "releases" / journal["release_id"] / "wiki"
        (candidate / "index.md").write_bytes(b"damaged after interruption")
        recovered = publish.recover(self.wiki)
        self.assertEqual(recovered["state"], "aborted")
        self.assertEqual(recovered["release_id"], self.base.release_id)
        self.assertFalse(journal_path.exists())
        next_release = fixture.ingest(self.wiki, self.intent("normal"), "9"*32)
        self.assertEqual(publish.resolve_publication(self.wiki).release_id, next_release["release_id"])
        with self.assertRaisesRegex(publish.PublicationError, "公開済み"):
            publish.resolve_publication(self.wiki, journal["release_id"])

    def test_generic_writer_changes_are_not_dropped_by_fixture_ingest(self):
        work = self.root / "generic-plan"
        shutil.copytree(self.base.root, work)
        (work / "concepts" / "external.md").write_text("# 別の書き手のページ\n", encoding="utf-8")
        plan = publish.build_plan(self.wiki, work, base=self.base, plan_id="7"*32)
        written = publish.apply_plan(self.wiki, work, plan, publish.digest(publish.encoded(plan)))
        self.assertEqual(publish.resolve_publication(self.wiki).definition_id, self.base.definition_id)
        self.finished(self.worker(self.intent("would-replace"), "8"*32), 4)
        live = publish.resolve_publication(self.wiki)
        self.assertEqual(live.release_id, written["release_id"])
        self.assertTrue((live.root / "concepts" / "external.md").exists())

    def test_pinned_reads_preserve_legacy_outputs(self):
        expected = json.loads(LEGACY_OUTPUT.read_text(encoding="utf-8"))
        self.assertEqual(self.reads(self.wiki, release_id=self.base.release_id), expected["graph"])
        for program, legacy in expected["lint"].items():
            with self.subTest(program=program):
                pinned = json.loads(self.cli(program, self.wiki, "--release-id", self.base.release_id,
                                             "--json"))
                self.assertEqual(pinned.pop("release_id"), self.base.release_id)
                self.assertEqual(pinned, legacy)
        search = json.loads(self.cli("wiki_search.py", "KabutoMarker", "--wiki", self.wiki, "--json"))
        self.assertEqual(search["release_id"], self.base.release_id)
        self.assertEqual(search["results"][0]["rel_path"], "sources/seed.md")
        target = self.root / "html-pinned"
        self.cli("wiki_browse.py", "build", self.wiki, "--release-id", self.base.release_id,
                 "--out", target, "--raw", "none")
        renders = sorted(path.relative_to(target).as_posix() for path in target.rglob("*.html")
                         if "KabutoMarker" in path.read_text(encoding="utf-8"))
        self.assertEqual(renders, expected["rendered_seed"])

    def test_browse_serve_cli_starts_with_requested_release(self):
        work = self.root / "changed-for-serve"
        work.mkdir()
        state = fixture.state_of(self.base)
        state["citations"]["seed"]["quote"] = "KabutoMarker 新しい本文。"
        fixture.publish_state(self.wiki, work, self.base, state, "4"*32)
        env = {**os.environ, "INFO_HIVE_DATA_DIR": str(self.root / "browse-data")}
        common = [sys.executable, "-B", "-X", "utf8", str(SCRIPTS / "wiki_browse.py")]
        process = subprocess.Popen([*common, "serve", str(self.wiki), "--release-id", self.base.release_id,
                                    "--page", "sources/seed", "--no-open", "--idle-timeout", "40"],
                                   stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True, encoding="utf-8", env=env)
        self.addCleanup(self.close_worker, process)
        ready = Queue()
        listener = threading.Thread(target=lambda: ready.put(process.stdout.readline()), daemon=True)
        listener.start()
        text = ready.get(timeout=25)
        if not text:
            self.fail(process.communicate(timeout=10)[1])
        info = json.loads(text)
        with urlopen(info["url"], timeout=5) as response:
            self.assertIn("旧版", response.read().decode("utf-8"))
        stopped = subprocess.run([*common, "stop", str(self.wiki), "--release-id", self.base.release_id],
                                 env=env, capture_output=True, encoding="utf-8", timeout=20)
        self.assertEqual(stopped.returncode, 0, stopped.stderr)
        self.finished(process, 0)

    @unittest.skipUnless(HAS_MCP, "実際の MCP エンドポイントには索引の依存パッケージが必要です")
    def test_mcp_search_pins_citation_and_browse_pins_assets_until_retired(self):
        with mcp_client() as tool, browse_server(self.base) as old_browse:
            args = {"wiki": str(self.wiki)}
            query = tool("query", {**args, "query": "KabutoMarker"})
            choice = query["results"][0]["rel_path"]
            self.assertEqual(choice, "sources/seed.md")
            old = query["release_id"]
            self.assertEqual(old, self.base.release_id)

            core, _ = old_browse.state.get(wait=3)
            page = core.resolve("sources/seed.md", articles=True)
            old_name = core.out_name[page["id"]]
            old_html = urlopen(old_browse.url(old_name), timeout=5).read().decode()
            self.assertIn("旧版", old_html)
            asset = core.asset_out["assets/badge.svg"]
            with urlopen(old_browse.url(asset), timeout=5) as response:
                old_asset = response.read()
                self.assertEqual(response.headers["Cache-Control"], "no-store")

            state = fixture.state_of(self.base)
            state["citations"]["seed"]["quote"] = "KabutoMarker この出典の新版は基盤への依存を再確認した。"
            fixture.insert(state, self.intent("asset-revision", "OTHER")["intent"])
            work = self.root / "changed"
            work.mkdir()
            applied = fixture.publish_state(self.wiki, work, self.base, state, "d"*32)
            active = publish.resolve_publication(self.wiki)
            self.assertEqual(active.release_id, applied["release_id"])
            citation = tool("get_page", {**args, "page": choice, "release_id": old})
            self.assertEqual(citation["release_id"], old)
            self.assertIn("旧版", citation["body"])
            self.assertIn("新版", tool("get_page", {**args, "page": choice})["body"])
            error, message = tool("get_page", {**args, "page": "shared", "release_id": old}, error=True)
            self.assertTrue(error)
            self.assertIn("複数", message)
            self.assertIn("旧版", urlopen(old_browse.url(old_name), timeout=5).read().decode())
            self.assertEqual(urlopen(old_browse.url(asset), timeout=5).read(), old_asset)
            with browse_server(active) as new_browse:
                new_core, _ = new_browse.state.get(wait=3)
                new_name = new_core.out_name[new_core.resolve("sources/seed.md", articles=True)["id"]]
                self.assertIn("新版", urlopen(new_browse.url(new_name), timeout=5).read().decode())
                new_asset = new_core.asset_out["assets/badge.svg"]
                self.assertNotEqual(urlopen(new_browse.url(new_asset), timeout=5).read(), old_asset)

            first_lint = tool("lint", {**args, "release_id": old})
            original_lint = tool("lint", {"wiki": str(self.legacy)})
            self.assertEqual(first_lint.pop("release_id"), old)
            self.assertEqual(first_lint, original_lint)
            graph = tool("graph", {**args, "command": "facts", "about": "concept:platform", "release_id": old})
            self.assertEqual(graph["release_id"], old)
            publish.retire(self.wiki, old)
            denied, message = tool("get_page", {**args, "page": choice, "release_id": old}, error=True)
            self.assertTrue(denied)
            self.assertIn("取り下げ", message)
            denied, message = tool("get_page", {"wiki": str(self.base.root), "page": choice}, error=True)
            self.assertTrue(denied)
            self.assertIn("取り下げ", message)
            with self.assertRaises(wiki_graph_query.QueryError):
                wiki_graph_query.run_query(self.legacy, "facts", about="concept:platform",
                                           db=self.base.root / "graph" / "graph.sqlite")
            with self.assertRaises(publish.PublicationError):
                publish.recover(self.base.root)
            with self.assertRaises(HTTPError) as error:
                urlopen(old_browse.url(asset), timeout=5)
            self.assertEqual(error.exception.code, 410)
