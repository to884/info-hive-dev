"""通常のライブ wiki の書く段を、隔離した原本と記事で確かめる。"""

import hashlib
import json
import os
from pathlib import Path
import sqlite3
import subprocess
import sys
from tempfile import TemporaryDirectory
import time
import unittest

ROOT = Path(__file__).resolve().parents[2]
SKILL = ROOT / "info-hive-wiki" / "skills" / "info-hive"
SCRIPTS = SKILL / "scripts"


def article(kind, title, body, *, raw=None, source=None):
    fields = ["---", f"type: {kind}", f"title: {json.dumps(title, ensure_ascii=False)}",
              "tags: [ontology]", "created: 2026-11-19", "updated: 2026-11-19"]
    if raw:
        fields += [f"raw: {json.dumps(raw['raw_ref'], ensure_ascii=False)}",
                   f"raw_sha256: {raw['raw_sha256']}"]
    if source:
        fields += [f"sources: [{source}]"]
    return "\n".join([*fields, "---", "", f"# {title}", "", body, ""])


class LiveWrite(unittest.TestCase):
    def setUp(self):
        temp = TemporaryDirectory()
        self.addCleanup(temp.cleanup)
        self.base = Path(temp.name)
        self.wiki = self.base / "wiki"
        self.raw = self.base / "raw"
        self.wiki.mkdir()
        self.raw.mkdir()
        self.env = dict(os.environ, INFO_HIVE_DATA_DIR=str(self.base / "data"), PYTHONUTF8="1")
        for name in ("SCHEMA.md", "index.md", "log.md"):
            (self.wiki / name).write_bytes((SKILL / "assets" / (name + ".template")).read_bytes())

    def run_script(self, script, *args, status=0):
        result = subprocess.run([sys.executable, str(SCRIPTS / script), *map(str, args)], env=self.env,
                                capture_output=True, encoding="utf-8", timeout=30)
        self.assertEqual(result.returncode, status, result.stderr + result.stdout)
        return result

    def cli(self, command, *args, status=0):
        result = self.run_script("wiki_apply.py", command, *args, "--json", status=status)
        return json.loads(result.stdout) if status == 0 else result.stderr

    def begin(self, name):
        return self.cli("begin", "--wiki", self.wiki, "--raw-root", self.raw, "--name", name)["apply_dir"]

    def within(self, directory, command, *args, status=0):
        return self.cli(command, "--apply-dir", directory, *args, status=status)

    def draft(self, directory, name, body, command="new"):
        path = Path(self.within(directory, command, "--path", name)["path"])
        path.write_text(body, encoding="utf-8", newline="\n")
        return path

    def index(self, directory, section, page):
        self.within(directory, "index-add", "--file", "index.md", "--section", "## " + section,
                    "--line", f"- [[{page}]]: 合成資料の説明")

    def log(self, directory, operation, title, *lines):
        args = [arg for line in lines for arg in ("--line", line)]
        self.within(directory, "log-entry", "--date", "2026-11-19", "--op", operation, "--title", title, *args)

    def approve(self, directory):
        return self.within(directory, "diff")["plan_sha256"]

    def apply(self, directory, checksum=None, *, status=0):
        return self.within(directory, "apply", "--expect-sha256", checksum or self.approve(directory), status=status)

    def record(self, directory, key, operation="query", *, title=None):
        self.draft(directory, f"synthesis/{key}.md", article("synthesis", key, "合成の回答。", source="stub"))
        self.index(directory, "シンセシス", key)
        self.log(directory, operation, title or key, "保存した項目を確認")

    def interrupt(self, directory, at):
        code = ("import os,sys; sys.path.insert(0, sys.argv[1]); from wiki_live_apply import apply; "
                "apply(sys.argv[2],sys.argv[3],checkpoint=lambda point: os._exit(71) if point==sys.argv[4] else None)")
        checksum = self.approve(directory)
        result = subprocess.run([sys.executable, "-c", code, str(SCRIPTS), directory, checksum, at],
                                env=self.env, capture_output=True, timeout=30)
        self.assertEqual(result.returncode, 71, result.stderr.decode("utf-8"))
        return checksum

    def test_ingest_query_and_learn(self):
        ontology = self.wiki / "graph/ontology.yaml"
        ontology.parent.mkdir()
        ontology.write_bytes((SKILL / "assets/ontology.yaml.template").read_bytes())
        source_input = self.base / "メモ.txt"
        source_input.write_text("BerylliumLedger は合成の台帳の識別子。", encoding="utf-8")
        saved = json.loads(self.run_script("wiki_raw_ingest.py", "save", "--wiki", self.wiki, "--raw-root", self.raw,
                                          "--source", source_input, "--name", source_input.name).stdout)
        ingest = self.begin("ローカル資料の取り込み")
        self.draft(ingest, "sources/台帳.md", article("source", "台帳",
                   "BerylliumLedger は合成の識別子。[[台帳の規則]]", raw=saved))
        self.draft(ingest, "concepts/台帳の規則.md", article("concept", "台帳の規則", "[[台帳]] に根拠がある。", source="台帳"))
        self.index(ingest, "ソース", "台帳")
        self.index(ingest, "コンセプト", "台帳の規則")
        self.log(ingest, "ingest", "台帳", "原本の版を照合")
        result = self.apply(ingest)
        self.assertEqual(set(result["files"]), {"sources/台帳.md", "concepts/台帳の規則.md", "index.md", "log.md"})
        self.assertEqual(source_input.read_bytes(), Path(saved["raw_path"]).read_bytes())
        self.run_script("wiki_graph_extract.py", self.wiki, "--formats", "sqlite")
        with sqlite3.connect(self.wiki / "graph/graph.sqlite") as db:
            nodes = db.execute("select count(*) from nodes").fetchone()[0]
        db.close()
        self.assertGreaterEqual(nodes, 2)
        search = self.run_script("wiki_search.py", "BerylliumLedger", "--wiki", self.wiki, "--no-embed", "--json")
        self.assertIn("sources/台帳.md", search.stdout)
        query = self.begin("回答の保存")
        self.draft(query, "synthesis/台帳の回答.md", article("synthesis", "台帳の回答",
                   "BerylliumLedger の根拠は [[台帳]]。", source="台帳"))
        self.index(query, "シンセシス", "台帳の回答")
        self.log(query, "query", "台帳の識別子は何か")
        self.apply(query)
        search = self.run_script("wiki_search.py", "BerylliumLedger", "--wiki", self.wiki, "--no-embed", "--json")
        self.assertIn("synthesis/台帳の回答.md", search.stdout)
        experience = self.base / "experience.json"
        experience.write_text(json.dumps({"id": "check-ledger", "task": "台帳を検査する", "outcome": "success",
                                           "verification": "版を照合した", "model": "fixture", "tools": "sha256",
                                           "scope": "合成台帳", "actions": ["読んだ"]}), encoding="utf-8")
        captured = json.loads(self.run_script("wiki_evolve.py", "--wiki", self.wiki, "capture",
                                             "--raw", self.raw, "--record", experience).stdout)
        learn = self.begin("経験を反映する")
        self.draft(learn, "sources/check-ledger.md", article("source", "検査の経験", "[[台帳の規則]] の観測。", raw=captured))
        path = self.wiki / "concepts/台帳の規則.md"
        previous = path.read_text(encoding="utf-8")
        self.draft(learn, "concepts/台帳の規則.md", previous + "\n[[check-ledger]] の経験も根拠とする。\n", command="edit")
        self.index(learn, "ソース", "check-ledger")
        self.log(learn, "learn", "率直に検査結果を記録する")
        self.apply(learn)
        self.assertTrue(path.read_text(encoding="utf-8").startswith(previous))
        self.assertIn(captured["raw_sha256"], (self.wiki / "sources/check-ledger.md").read_text(encoding="utf-8"))
        self.assertEqual(len(list((self.wiki / "concepts").glob("*.md"))), 1)
        heading = result["log_entries"][0]
        graph_log = self.begin("グラフ更新の記録")
        note = f"グラフ: ノード +{nodes}、型付きエッジ +0"
        self.within(graph_log, "log-sub", "--entry", heading["heading"], "--nth", heading["nth"],
                    "--line", note)
        self.apply(graph_log)
        log = (self.wiki / "log.md").read_text(encoding="utf-8")
        self.assertIn("ingest | 台帳\n   原本の版を照合\n   " + note, log)
        self.assertIn("query | 台帳の識別子は何か", log)
        self.assertIn("learn | 率直に検査結果を記録する", log)
        findings = json.loads(self.run_script("wiki_lint.py", self.wiki, "--raw-root", self.raw, "--json").stdout)
        self.assertEqual(findings["missing_raw"], [])
        html = self.base / "browse"
        self.run_script("wiki_browse.py", "build", self.wiki, "--out", html, "--raw", "none")
        self.assertTrue(any("BerylliumLedger の根拠" in p.read_text(encoding="utf-8") for p in html.rglob("*.html")))

    def test_parallel_writers_keep_every_index_and_log_item(self):
        plans = []
        for key, operation in (("one", "ingest"), ("two", "query"), ("three", "learn")):
            plan = self.begin(key)
            self.record(plan, key, operation)
            plans.append((plan, self.approve(plan)))
        children = [subprocess.Popen([sys.executable, str(SCRIPTS / "wiki_apply.py"), "apply", "--apply-dir",
                                      plan, "--expect-sha256", sha], env=self.env, encoding="utf-8",
                                     stdout=subprocess.PIPE, stderr=subprocess.PIPE) for plan, sha in plans]
        results = [child.communicate(timeout=30) for child in children]
        for child, (out, err) in zip(children, results):
            self.assertEqual(child.returncode, 0, err + out)
        log = (self.wiki / "log.md").read_text(encoding="utf-8")
        index = (self.wiki / "index.md").read_text(encoding="utf-8")
        for key in ("one", "two", "three"):
            self.assertEqual(index.count(f"[[{key}]]"), 1)
            self.assertEqual(log.count(f" | {key}\n"), 1)
            self.assertTrue((self.wiki / f"synthesis/{key}.md").is_file())

    def test_process_death_then_unlock_and_resume_at_each_boundary(self):
        for i, point in enumerate(("after_journal", "after_write:0", "before_write:0", "after_receipt")):
            with self.subTest(point=point):
                key = f"stopped-{i}"
                plan = self.begin(key)
                self.record(plan, key)
                sha = self.interrupt(plan, point)
                self.assertIn("unlock", self.cli("recover", "--live", "--wiki", self.wiki, status=4))
                self.assertEqual(self.cli("unlock", "--wiki", self.wiki)["state"], "unlocked")
                if i == 1:
                    succeeding = self.begin("次の計画")
                    self.record(succeeding, "succeeding")
                    self.apply(succeeding)
                else:
                    self.assertEqual(self.cli("recover", "--live", "--wiki", self.wiki)["state"], "applied")
                self.assertFalse(list(self.wiki.rglob(".wiki-live-*.tmp")))
                self.assertEqual(self.apply(plan, sha)["state"], "already_applied")
                self.assertIn("適用済み", self.within(plan, "diff", status=4))
                log = (self.wiki / "log.md").read_text(encoding="utf-8")
                self.assertEqual(log.count(f" | {key}\n"), 1)
                self.assertEqual((self.wiki / "index.md").read_text(encoding="utf-8").count(f"[[{key}]]"), 1)
        self.assertIn(" | succeeding\n", (self.wiki / "log.md").read_text(encoding="utf-8"))

    def test_outside_write_stops_recovery_and_keeps_third_party_bytes(self):
        plan = self.begin("中断")
        self.record(plan, "stuck")
        self.interrupt(plan, "after_write:0")
        self.assertTrue((self.wiki / "synthesis/stuck.md").exists())
        index = self.wiki / "index.md"
        external = index.read_bytes() + b"\n# Outside\n"
        index.write_bytes(external)
        self.cli("unlock", "--wiki", self.wiki)
        self.assertIn("日誌を保留", self.cli("recover", "--live", "--wiki", self.wiki, status=5))
        self.assertEqual(index.read_bytes(), external)
        self.assertFalse((self.wiki / "synthesis/stuck.md").exists())
        self.assertNotIn(" | stuck", (self.wiki / "log.md").read_text(encoding="utf-8"))
        view = self.cli("recover", "--live", "--wiki", self.wiki, "--show")
        self.assertEqual(view["state"], "rollback")
        discarded = self.cli("recover", "--live", "--wiki", self.wiki, "--discard", view["plan_id"])
        self.assertEqual(discarded["state"], "discarded")
        archive = Path(discarded["journal"])
        archived = archive.read_bytes()
        self.interrupt(plan, "after_write:0")
        index.write_bytes(external + b"\n# Outside again\n")
        self.cli("unlock", "--wiki", self.wiki)
        self.cli("recover", "--live", "--wiki", self.wiki, status=5)
        next_archive = self.cli("recover", "--live", "--wiki", self.wiki, "--discard", view["plan_id"])
        self.assertNotEqual(next_archive["journal"], str(archive))
        self.assertEqual(archive.read_bytes(), archived)
        succeeding = self.begin("止まった日誌の確認後")
        self.record(succeeding, "unblocked")
        self.apply(succeeding)
        self.assertIn("# Outside", index.read_text(encoding="utf-8"))

    def test_recovery_can_be_inspected_while_raw_root_is_missing(self):
        plan = self.begin("原本の根を一時的に外す")
        self.record(plan, "missing-root")
        checksum = self.interrupt(plan, "after_journal")
        moved = self.base / "moved"
        self.raw.rename(moved)
        shown = self.cli("recover", "--wiki", self.wiki, "--live", "--show")
        self.assertEqual(shown["state"], "prepared")
        self.assertEqual(shown["raw_root"], str(self.raw))
        self.assertEqual(shown["owner"]["plan_id"], shown["plan_id"])
        self.assertIn("元の場所", self.cli("unlock", "--wiki", self.wiki, status=5))
        self.assertIn("元の場所", self.cli("recover", "--wiki", self.wiki, "--live", status=5))
        moved.rename(self.raw)
        self.cli("unlock", "--wiki", self.wiki)
        self.assertEqual(self.cli("recover", "--wiki", self.wiki, "--live")["state"], "applied")
        self.assertEqual(self.apply(plan, checksum)["state"], "already_applied")

    def test_missing_latest_completion_is_detected_even_without_journal(self):
        plan = self.begin("最後の完了記録")
        self.record(plan, "missing-receipt")
        approved = self.approve(plan)
        result = self.apply(plan, approved)
        area = self.wiki / ".wiki-cache/apply"
        receipt = area / "live-receipts" / f"{result['plan_id']}.json"
        hidden = area / "missing-receipt"
        receipt.rename(hidden)
        self.assertFalse((area / "live-journal.json").exists())
        self.assertIn("先頭記録と完了記録", self.cli("recover", "--live", "--wiki", self.wiki, status=5))
        self.assertIn("先頭記録と完了記録", self.apply(plan, approved, status=5))
        hidden.rename(receipt)
        self.assertEqual(self.apply(plan, approved)["state"], "already_applied")

    def test_recovery_reclaims_temporary_name_of_exclusive_publish(self):
        plan = self.begin("新しいファイルに名前が二つ残る")
        self.record(plan, "linked-topic")
        checksum = self.approve(plan)
        code = """import os, sys
sys.path.insert(0, sys.argv[1])
import wiki_fsguard
from wiki_live_apply import apply
original = wiki_fsguard.publish_exclusive
def staged_publish(tmp, target):
    if target.name == 'linked-topic.md':
        os.link(tmp, target)
        os._exit(72)
    original(tmp, target)
wiki_fsguard.publish_exclusive = staged_publish
apply(sys.argv[2], sys.argv[3])
"""
        child = subprocess.run([sys.executable, "-c", code, str(SCRIPTS), plan, checksum],
                               env=self.env, capture_output=True, timeout=30)
        self.assertEqual(child.returncode, 72, child.stderr.decode("utf-8"))
        target = self.wiki / "synthesis/linked-topic.md"
        self.assertEqual(target.stat().st_nlink, 2)
        self.cli("unlock", "--wiki", self.wiki)
        self.assertEqual(self.cli("recover", "--live", "--wiki", self.wiki)["state"], "applied")
        self.assertEqual(self.apply(plan, checksum)["state"], "already_applied")
        self.assertEqual(target.stat().st_nlink, 1)
        self.assertFalse(list(self.wiki.rglob(".wiki-live-*.tmp")))

    def test_live_owner_prevents_unlock_and_contended_plan_can_be_retried(self):
        first, second = self.begin("待たせる計画"), self.begin("待つ計画")
        self.record(first, "first", operation="ingest")
        self.record(second, "second", operation="query")
        first_sha, second_sha = self.approve(first), self.approve(second)
        paused, release = self.base / "paused", self.base / "release"
        code = """import sys, time
from pathlib import Path
sys.path.insert(0, sys.argv[1])
from wiki_live_apply import apply
def wait(point):
    if point == 'after_journal':
        Path(sys.argv[4]).touch()
        deadline = time.monotonic() + 15
        while not Path(sys.argv[5]).exists():
            if time.monotonic() >= deadline:
                raise TimeoutError('試験の完了待ち')
            time.sleep(0.02)
apply(sys.argv[2], sys.argv[3], checkpoint=wait)
"""
        child = subprocess.Popen([sys.executable, "-c", code, str(SCRIPTS), first, first_sha, str(paused), str(release)],
                                 env=self.env, encoding="utf-8", stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        try:
            deadline = time.monotonic() + 8
            while not paused.exists() and child.poll() is None and time.monotonic() < deadline:
                time.sleep(0.02)
            self.assertTrue(paused.exists())
            self.assertIn("実行中", self.cli("unlock", "--wiki", self.wiki, status=4))
            self.assertIn("保留しました", self.within(second, "apply", "--expect-sha256", second_sha, "--wait", 0, status=4))
            records = self.cli("pending", "--wiki", self.wiki)["pending"]
            self.assertEqual(len(records), 1)
            self.assertEqual(records[0]["plan_sha256"], second_sha)
            self.assertIn("+合成の回答。", records[0]["diff"])
            self.assertFalse((self.wiki / "synthesis/second.md").exists())
        finally:
            release.touch()
            _, err = child.communicate(timeout=20)
        self.assertEqual(child.returncode, 0, err)
        self.apply(second, second_sha)
        self.assertEqual(self.cli("pending", "--wiki", self.wiki)["pending"], [])

    def test_stale_page_and_changed_draft_require_new_approval(self):
        target = self.wiki / "shared.md"
        target.write_text("# 共有\n", encoding="utf-8", newline="\n")
        first, second = self.begin("最初"), self.begin("次")
        self.draft(first, "shared.md", "# 共有\n\n先の編集\n", command="edit")
        proposal = self.draft(second, "shared.md", "# 共有\n\n後の編集\n", command="edit")
        self.log(second, "learn", "後の編集")
        approved = self.approve(second)
        proposal.write_text("# 共有\n\n承認後の変更\n", encoding="utf-8")
        self.assertIn("指紋", self.apply(second, approved, status=4))
        latest = self.approve(second)
        self.apply(first)
        self.assertIn("基準版", self.apply(second, latest, status=4))
        self.assertNotIn(" | 後の編集", (self.wiki / "log.md").read_text(encoding="utf-8"))
        rebased = self.within(second, "rebase", "--path", "shared.md")
        self.assertIn("先の編集", Path(rebased["path"]).read_text(encoding="utf-8"))
        self.assertIn("承認後の変更", Path(rebased["previous"]).read_text(encoding="utf-8"))
        with Path(rebased["path"]).open("a", encoding="utf-8") as draft:
            draft.write("\n後の編集\n")
        self.apply(second)
        self.assertIn("先の編集", target.read_text(encoding="utf-8"))
        self.assertIn("後の編集", target.read_text(encoding="utf-8"))

    def test_index_keeps_frontmatter_bom_crlf_and_fenced_heading(self):
        index = self.wiki / "indexes/pages.md"
        index.parent.mkdir()
        original = "\ufeff---\r\ntitle: Pages\r\n---\r\n\r\n```text\r\n## 項目\r\n```\r\n\r\n## 項目\r\n\r\n- [[existing]]: 項目\r\n"
        index.write_bytes(original.encode("utf-8"))
        plan = self.begin("分割した索引")
        self.within(plan, "index-add", "--file", "indexes/pages.md", "--section", "## 項目",
                    "--line", "- [[new]]: 次の項目")
        self.apply(plan)
        self.assertEqual(index.read_bytes().decode("utf-8"), original + "- [[new]]: 次の項目\r\n")
        repeated = self.begin("二重登録")
        self.within(repeated, "index-add", "--file", "indexes/pages.md", "--section", "## 項目",
                    "--line", "- [[NEW.md#見出し|別名]]: 重複")
        self.assertIn("同じページ", self.within(repeated, "diff", status=4))
        heading = "# （ソースを取り込むと追加される）\n"
        secondary = self.wiki / "indexes/heading.md"
        secondary.write_bytes(heading.encode("utf-8"))
        append = self.begin("見出しを保持した追記")
        self.within(append, "index-add", "--file", "indexes/heading.md", "--line", "- [[valid]]: 項目")
        self.apply(append)
        self.assertEqual(secondary.read_bytes().decode("utf-8"), heading + "\n- [[valid]]: 項目\n")

    def test_raw_and_published_mode_are_protected(self):
        plan = self.begin("無効な書く先")
        self.assertIn("使えない", self.within(plan, "new", "--path", "raw/sample.md", status=1))
        self.assertIn("正規の相対パス", self.within(plan, "new", "--path", "sources/example~1.md", status=1))
        child = self.wiki / "child"
        child.mkdir()
        (child / "SCHEMA.md").touch()
        self.assertIn("別の wiki", self.within(plan, "new", "--path", "child/new.md", status=4))
        self.assertFalse((child / "new.md").exists())
        own_raw = self.wiki / "original.md"
        own_raw.write_text("原本", encoding="utf-8")
        self.draft(plan, "sources/invalid.md", article("source", "原本参照", "本文",
                                                       raw={"raw_ref": own_raw.as_posix(), "raw_sha256": "0" * 64}))
        self.assertIn("原本として", self.within(plan, "diff", status=1))
        area = self.wiki / ".wiki-cache/apply"
        area.mkdir(parents=True)
        (area / "current").write_text("0" * 64, encoding="ascii")
        self.assertIn("公開版を確認できません", self.cli(
            "begin", "--wiki", self.wiki, "--raw-root", self.raw, "--name", "拒否", status=1))

    def test_external_pdf_next_to_wiki_remains_read_only(self):
        paper = self.base / "paper.pdf"
        original = b"%PDF-1.4\n% fixture\n"
        paper.write_bytes(original)
        metadata = {"raw_ref": paper.as_posix(), "raw_sha256": hashlib.sha256(original).hexdigest()}
        plan = self.begin("PDF 原本への参照")
        self.draft(plan, "sources/paper.md", article("source", "PDF", "資料を参照する。", raw=metadata))
        self.index(plan, "ソース", "paper")
        self.log(plan, "ingest", "PDF")
        self.apply(plan)
        next_plan = self.begin("PDF の要約だけ直す")
        self.draft(next_plan, "sources/paper.md", article("source", "PDF", "要約を更新した。", raw=metadata), command="edit")
        self.apply(next_plan)
        self.assertEqual(original, paper.read_bytes())
        records = list((self.wiki / ".wiki-cache/raw-roots.d").glob("*.json"))
        self.assertEqual(len(records), 1)

    def test_live_save_preserves_raw_inside_the_wiki(self):
        self.raw = self.wiki / "raw"
        self.raw.mkdir()
        original = b"# Original\n\nRaw bytes.\n"
        source = self.base / "original.md"
        source.write_bytes(original)
        saved = json.loads(self.run_script("wiki_raw_ingest.py", "save", "--wiki", self.wiki,
                                          "--raw-root", self.raw, "--source", source).stdout)
        plan = self.begin("wiki 内の原本を参照する")
        self.assertIn("使えない", self.within(plan, "new", "--path", "raw/original.md", status=1))
        self.draft(plan, "sources/original.md", article("source", "原本", "要約を保存する。", raw=saved))
        self.index(plan, "ソース", "original")
        self.log(plan, "ingest", "原本")
        checksum = self.approve(plan)
        self.apply(plan, checksum)
        self.assertEqual(self.apply(plan, checksum)["state"], "already_applied")
        self.assertEqual((self.raw / "original.md").read_bytes(), original)
        self.assertIn(saved["raw_sha256"], (self.wiki / "sources/original.md").read_text(encoding="utf-8"))


if __name__ == "__main__":
    unittest.main()
