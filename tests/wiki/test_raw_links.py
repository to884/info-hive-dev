"""ADR-0029 段階2。raw の解決、読まずに拒否する順番、lint と字幕検査の共通の境界。"""
from __future__ import annotations

import contextlib
import hashlib
import io
import json
import os
from pathlib import Path
import subprocess
import sys
from unittest import mock
import unittest

from tests.wiki.test_wiki_links import Base, junction, symlink, SCRIPTS
import init_wiki
import wiki_captions
import wiki_lint
import wiki_pages
import wiki_raw
import wiki_raw_ingest
import wiki_raw_roots
from wiki_fsguard import WriteGuard
from wiki_raw_roots import record_raw_root


class RawTests(Base):
    def setUp(self):
        super().setUp()
        self.raw = self.tmp / "raw"
        self.raw.mkdir()
        self.source = self.write("sources/s.md", "")

    def resolve(self, ref, **meta):
        return wiki_pages.resolve_raw({"type": "source", "raw": ref, **meta}, self.source, self.wiki,
                                      raw_roots=[self.raw])

    def source_page(self, raw, **meta):
        text = "---\n" + "\n".join(k + ": " + json.dumps(v, ensure_ascii=False)
                                  for k, v in {"type": "source", "title": "s", "raw": raw, **meta}.items()) + "\n---\n# s\n"
        self.source.write_text(text, encoding="utf-8", newline="\n")

    def lint(self, root=True):
        return wiki_lint.lint(wiki_lint.collect_pages(self.wiki), 100, 200, [], False, 5,
                              wiki_root=self.wiki, raw_root=self.raw if root else None)

    def test_relative_bases_and_missing(self):
        target = self.write("a.txt", "内容", self.raw)
        for ref in ("raw/a.txt", "../raw/a.txt", str(target)):
            with self.subTest(ref=ref):
                result = self.resolve(ref)[0]
                self.assertEqual(result.state, "resolved")
                self.assertEqual(result.path, target)
                self.assertTrue(result.version_unverified)
        self.assertEqual(self.resolve("raw/absent")[0].state, "missing")

    def test_non_source_and_urls(self):
        self.assertEqual(wiki_pages.resolve_raw({"type": "concept", "raw": "x"}, self.source, self.wiki), [])
        for ref in ("https://example.com/x", "file:///tmp/x"):
            self.assertEqual(self.resolve(ref)[0].state, "outside")

    def test_unrelated_recorded_root_does_not_hide_unverified_rag_scope(self):
        record_raw_root(self.wiki, self.raw, writer="wiki_session")
        target = self.write("document.pdf", "原本", self.ext)
        self.source_page(target.as_posix(), rag_job_id="job")
        found = self.lint(root=False)
        warning, = found["raw_paths_unchecked"]
        self.assertTrue(warning["scope_unverified"])
        self.assertEqual(Path(warning["candidate"]), target)

    def test_ambiguity_and_hash_selects_version(self):
        a = self.write("dup.txt", "A", self.wiki)
        b = self.write("dup.txt", "B", self.tmp)
        self.assertEqual(self.resolve("dup.txt")[0].state, "ambiguous")
        result = self.resolve("dup.txt", raw_sha256=hashlib.sha256(b.read_bytes()).hexdigest())[0]
        self.assertEqual((result.state, result.path), ("resolved", b))
        self.assertFalse(result.version_unverified)
        self.assertEqual(self.resolve("dup.txt", raw_sha256="0" * 64)[0].state, "missing")
        a.write_bytes(b"B")
        self.assertEqual(self.resolve("dup.txt", raw_sha256=hashlib.sha256(b"B").hexdigest())[0].state, "ambiguous")

    def test_same_file_through_root_alias_is_one_candidate(self):
        target = self.write("a.txt", "A", self.raw)
        alias = self.tmp / "view"
        if not junction(alias, self.wiki):
            self.skipTest("根のリンクを作れない")
        result = wiki_pages.resolve_raw({"type": "source", "raw": "../raw/a.txt"}, alias / "sources/s.md",
                                         self.wiki, alias, raw_roots=[self.raw])[0]
        self.assertEqual((result.state, result.path), ("resolved", target))

    def test_session_only_uses_wiki_parent_and_identity(self):
        self.write("archive/raw/a.md", '---\nsession_id: "wrong"\n---\n', self.wiki)
        target = self.write("archive/raw/a.md", '---\nsession_id: "right"\n---\n', self.tmp)
        r = self.resolve("archive/raw/a.md", session_id="right")[0]
        self.assertEqual((r.state, r.path, r.version_unverified), ("resolved", target, True))
        self.assertEqual(self.resolve("archive/raw/a.md", session_id="other")[0].state, "missing")
        self.assertEqual(self.resolve("archive/raw/a.md", session_id="right", raw_sha256="0" * 64)[0].state, "missing")

    def test_url_identity_and_final_url(self):
        target = self.write("a.md", '---\nurl: "https://old"\nfinal_url: "https://new"\n---\n', self.raw)
        for url in ("https://old", "https://new"):
            self.assertEqual(self.resolve(str(target), url=url)[0].state, "resolved")
        self.assertEqual(self.resolve(str(target), url="https://other")[0].state, "missing")
        self.assertEqual(self.resolve(str(target), url=["https://new"])[0].state, "resolved")
        self.assertEqual(self.resolve(str(target), url=["https://new", "https://old"])[0].state, "unknown")
        verified = self.resolve(str(target), url=["https://new", "https://old"],
                                raw_sha256=hashlib.sha256(target.read_bytes()).hexdigest())[0]
        self.assertEqual(verified.state, "resolved")
        self.assertFalse(verified.version_unverified)

    def test_mismatch_is_distinguished_from_absence(self):
        target = self.write("a", "A", self.raw)
        self.source_page(str(target), raw_sha256="0" * 64)
        found = self.lint()
        self.assertEqual(found["missing_raw"][0]["mismatches"][0]["kind"], "version")
        self.assertIn("raw_sha256 と一致しない", wiki_lint.render_text(found))
        self.source_page(str(self.raw / "absent"))
        self.assertNotIn("mismatches", self.lint()["missing_raw"][0])

    def test_sole_file_does_not_require_identity(self):
        target = self.write("a", "A", self.raw)
        with mock.patch.object(wiki_raw, "file_identity", side_effect=OSError("FileIdInfo がない")):
            self.assertEqual(self.resolve(str(target))[0].state, "resolved")

    def test_unknown_external_scope_is_reported_without_raw_root(self):
        target = self.write("book.pdf", "PDF", self.raw)
        os.link(target, self.raw / "copy.pdf")
        self.source_page(str(target), rag_job_id="j")
        found = self.lint(root=False)
        self.assertEqual(found["summary"]["links_raw"], 0)
        self.assertTrue(found["raw_paths_unchecked"][0]["scope_unverified"])
        self.assertEqual(self.lint()["summary"]["links_raw"], 1)

    def test_rootless_raw_link_counts_and_wiki_unchecked_are_separate(self):
        target = self.write("a", "A", self.raw)
        os.link(target, self.raw / "copy")
        self.source_page(str(target))
        found = wiki_lint.lint(wiki_lint.collect_pages(self.wiki), 100, 200, [], False, 5)
        self.assertEqual(found["summary"]["links"], len(found["links"]))
        self.assertIsNone(found["summary"]["links_wiki"])
        self.assertIsNone(found["summary"]["links_unchecked_wiki"])
        self.assertEqual(found["summary"]["links_unchecked_raw"], 0)

    def test_identity_absent_is_unverified_not_missing(self):
        for data in (b"plain text", b"\xff\x00", b"---\njust a horizontal line\n"):
            target = self.raw / "saved.md"
            target.write_bytes(data)
            for identity in ({"url": "https://release"}, {"session_id": "id"}):
                with self.subTest(data=data, identity=identity):
                    r = self.resolve(str(target), **identity)[0]
                    self.assertEqual((r.state, r.version_unverified), ("resolved", True))

    def test_rootless_lint_keeps_collected_raw_context(self):
        self.source_page("raw/missing.md")
        found = wiki_lint.lint(wiki_lint.collect_pages(self.wiki), 100, 200, [], False, 5)
        self.assertEqual(len(found["missing_raw"]), 1)
        self.assertIsNotNone(found["summary"]["raw_unknown"])
        unchecked = wiki_lint.lint([], 100, 200, [], False, 5)
        self.assertIsNone(unchecked["summary"]["raw_unknown"])

    def test_hidden_raw_is_reported_as_outside_even_when_absent(self):
        self.source_page(str(self.raw / ".old/a.md"))
        found = self.lint()
        self.assertEqual(len(found["raw_outside"]), 1)
        self.assertEqual(found["missing_raw"], [])

    def test_outside_does_not_hide_other_candidates_version_mismatch(self):
        self.write(".x/e.md", "A", self.tmp)
        self.source_page(".x/e.md", raw_sha256="0" * 64)
        found = self.lint()
        self.assertEqual(found["raw_outside"][0]["mismatches"][0]["kind"], "version")
        self.assertIn("raw_sha256 と一致しない", wiki_lint.render_text(found))

    def test_external_original_does_not_require_file_id(self):
        target = self.write("book.pdf", "PDF", self.ext)
        with mock.patch.object(wiki_raw, "file_identity", side_effect=OSError("FileIdInfo がない")):
            self.assertEqual(self.resolve(str(target), rag_job_id="job")[0].state, "resolved")

    def test_hash_arrays_and_bad_alignment(self):
        a = self.write("a", "A", self.raw)
        b = self.write("b", "B", self.raw)
        refs = [str(a), str(b)]
        hashes = [hashlib.sha256(p.read_bytes()).hexdigest() for p in (a, b)]
        self.assertTrue(all(r.state == "resolved" and not r.version_unverified
                            for r in self.resolve(refs, raw_sha256=hashes)))
        for wrong in ([hashes[0]], [hashes[0], "bad"], "bad"):
            self.assertTrue(all(r.state == "resolved" and r.version_unverified
                                for r in self.resolve(refs, raw_sha256=wrong)))

    def test_inside_parent_ref_is_unknown_before_any_io(self):
        with mock.patch.object(wiki_raw, "_inspect", side_effect=AssertionError("検査してはならない")):
            for ref in ("raw/jump/../a.txt", str(self.raw / "jump/../a.txt")):
                self.assertEqual(self.resolve(ref)[0].state, "unknown")

    def test_unknown_candidate_wins_even_if_another_exists(self):
        self.write("a", "A", self.wiki)
        original = wiki_pages._stat_entry
        def stat_entry(path):
            if Path(path) == self.tmp / "a":
                raise PermissionError("調べられない")
            return original(path)
        with mock.patch.object(wiki_pages, "_stat_entry", side_effect=stat_entry):
            self.assertEqual(self.resolve("a")[0].state, "unknown")

    def test_symlink_is_not_read_even_if_hash_matches(self):
        target = self.write("secret", "外の中身", self.ext)
        link = self.raw / "a.md"
        if not symlink(link, target):
            self.skipTest("ファイルの symlink を作れない")
        with mock.patch.object(wiki_raw, "_digest", side_effect=AssertionError("ハッシュを読んだ")), \
             mock.patch.object(wiki_raw, "_raw_meta", side_effect=AssertionError("本文を読んだ")):
            r = self.resolve(str(link), raw_sha256=hashlib.sha256(target.read_bytes()).hexdigest())[0]
        self.assertEqual(r.state, "link")
        self.assertEqual(r.links[0]["kind"], "symlink")

    def test_hardlink_and_unreferenced_files(self):
        target = self.write("secret", "秘密", self.ext)
        link = self.raw / "a"
        os.link(target, link)
        self.source_page(str(link), raw_sha256="0" * 64)
        before = target.read_bytes()
        found = self.lint()
        self.assertEqual(found["summary"]["links_raw"], 1)
        self.assertEqual(found["links"][-1]["kind"], "hardlink")
        self.assertEqual(found["missing_raw"], [])
        self.assertEqual(target.read_bytes(), before)
        self.source_page("raw/missing")
        self.assertEqual(self.lint()["summary"]["links_raw"], 0)

    def test_directory_link_on_way_is_not_followed(self):
        target = self.write("secret.md", "秘密", self.ext)
        link = self.raw / "jump"
        if not junction(link, self.ext):
            self.skipTest("ディレクトリのリンクを作れない")
        with mock.patch.object(wiki_raw, "_digest", side_effect=AssertionError("読んだ")):
            result = self.resolve(str(link / target.name), raw_sha256="0" * 64)[0]
        self.assertEqual(result.state, "link")
        self.assertEqual(Path(result.links[0]["path"]), link)

    def test_raw_root_itself_may_be_link_but_child_is_checked(self):
        link = self.tmp / "archive"
        if not junction(link, self.raw):
            self.skipTest("根のリンクを作れない")
        target = self.write("a.txt", "A", self.raw)
        for ref in (str(link), str(link / target.name)):
            r = wiki_pages.resolve_raw({"type": "source", "raw": ref}, self.source, self.wiki, raw_roots=[link])[0]
            self.assertEqual(r.state, "resolved")
        os.link(target, self.raw / "b.txt")
        r = wiki_pages.resolve_raw({"type": "source", "raw": str(link)}, self.source, self.wiki, raw_roots=[link])[0]
        self.assertEqual(r.state, "link")

    def test_nested_raw_origin_does_not_exempt_wiki_walk(self):
        link = self.wiki / "topics"
        if not junction(link, self.ext):
            self.skipTest("ディレクトリのリンクを作れない")
        target = self.write("raw/a.md", "A", self.ext)
        nested = link / "raw"
        r = wiki_pages.resolve_raw({"type": "source", "raw": str(nested / target.name)}, self.source,
                                    self.wiki, raw_roots=[nested])[0]
        self.assertEqual(r.state, "resolved")
        self.assertTrue(wiki_pages.walk_pages(self.wiki).links)

    def test_directory_links_and_hidden_files(self):
        directory = self.raw / "bundle"
        directory.mkdir()
        target = self.write("a.txt", "A", directory)
        os.link(target, directory / ".hidden")
        self.assertEqual(self.resolve(str(directory))[0].state, "link")  # a 自体の nlink が2
        (directory / ".hidden").unlink()
        secret = self.write("secret", "S", self.ext)
        os.link(secret, directory / ".hidden")
        self.assertEqual(self.resolve(str(directory))[0].state, "resolved")
        os.link(secret, directory / "part.txt")
        r = self.resolve(str(directory))[0]
        self.assertEqual(r.state, "link")
        self.assertEqual(len(r.links), 1)

    def test_directory_hash_is_sorted_and_escaped(self):
        directory = self.raw / "bundle"
        a = self.write("b.txt", "B", directory)
        b = self.write("a.txt", "A", directory)
        rows = [json.dumps([p.name, hashlib.sha256(p.read_bytes()).hexdigest()], ensure_ascii=False) for p in (b, a)]
        expected = hashlib.sha256("\n".join(rows).encode("utf-8")).hexdigest()
        self.assertEqual(wiki_raw.raw_digest(directory, self.raw), expected)
        self.assertEqual(self.resolve(str(directory), raw_sha256=expected)[0].state, "resolved")
        original = wiki_pages._list_dir
        with mock.patch.object(wiki_pages, "_list_dir", side_effect=lambda p: list(reversed(original(p)))):
            self.assertEqual(wiki_raw.raw_digest(directory, self.raw), expected)

    @unittest.skipIf(os.name == "nt", "Windows では制御文字を含む名前を作れない")
    def test_directory_hash_with_unicode_collision_and_newlines(self):
        directory = self.raw / "bundle"
        self.write("が.txt", "A", directory)
        b = self.write("か\u3099.txt", "B", directory)
        if len(list(directory.iterdir())) != 2:
            self.skipTest("正規化で同じになる名前を別ファイルにできない")
        h = wiki_raw.raw_digest(directory, self.raw)
        original = wiki_pages._list_dir
        with mock.patch.object(wiki_pages, "_list_dir", side_effect=lambda p: list(reversed(original(p)))):
            self.assertEqual(wiki_raw.raw_digest(directory, self.raw), h)
        self.write("tab\tname\nfile", "C", directory)
        self.assertNotEqual(wiki_raw.raw_digest(directory, self.raw), h)

    def test_unlistable_directory_is_unknown(self):
        directory = self.raw / "bundle"
        directory.mkdir()
        with mock.patch.object(wiki_pages, "_list_dir", side_effect=PermissionError("不可")):
            r = self.resolve(str(directory))[0]
        self.assertEqual(r.state, "unknown")
        self.assertTrue(r.unchecked)

    def test_unreadable_hash_is_unknown(self):
        target = self.write("a", "A", self.raw)
        with mock.patch.object(wiki_raw, "_digest", side_effect=OSError("読めない")):
            self.assertEqual(self.resolve(str(target), raw_sha256="0" * 64)[0].state, "unknown")

    def test_disappeared_directory_member_is_unknown(self):
        directory = self.raw / "bundle"
        target = self.write("a", "A", directory)
        original = wiki_pages._stat_entry
        with mock.patch.object(wiki_pages, "_stat_entry", side_effect=lambda p:
                               ("absent", None) if Path(p) == target else original(p)):
            self.assertEqual(self.resolve(str(directory))[0].state, "unknown")

    def test_file_cannot_be_used_as_raw_root_to_exempt_its_link(self):
        target = self.write("a", "A", self.raw)
        os.link(target, self.raw / "b")
        r = wiki_pages.resolve_raw({"type": "source", "raw": str(target)}, self.source, self.wiki,
                                    raw_roots=[target])[0]
        self.assertEqual(r.state, "unknown")

    def test_link_in_another_candidate_wins_before_hash(self):
        target = self.write("a", "A", self.wiki)
        os.link(target, self.tmp / "a")
        with mock.patch.object(wiki_raw, "_digest", side_effect=AssertionError("版を先に読んだ")):
            self.assertEqual(self.resolve("a", raw_sha256="0" * 64)[0].state, "link")

    def test_several_raw_roots_check_old_root_ancestors(self):
        old = self.tmp / "archive"
        old.mkdir()
        link = old / "jump"
        self.write("a", "A", self.ext)
        if not junction(link, self.ext):
            self.skipTest("ディレクトリのリンクを作れない")
        r = wiki_pages.resolve_raw({"type": "source", "raw": str(link / "a")}, self.source, self.wiki,
                                    raw_roots=[self.raw, old])[0]
        self.assertEqual(r.state, "link")
        self.assertEqual(Path(r.links[0]["root"]), old)

    def test_alias_root_parents_split_and_hash_prevents_wrong_version(self):
        real = self.tmp / "store/wiki"
        real.mkdir(parents=True)
        view = self.tmp / "view/wiki"
        view.parent.mkdir()
        if not junction(view, real):
            self.skipTest("根のリンクを作れない")
        first = self.write("raw/a.md", '---\nsession_id: "id"\n---\nA', view.parent)
        self.write("raw/a.md", '---\nsession_id: "id"\n---\nB', real.parent)
        m = {"type": "source", "raw": "raw/a.md", "session_id": "id"}
        def run(meta):
            return wiki_pages.resolve_raw(meta, real / "sources/a.md", real, view)[0]
        self.assertEqual(run(m).state, "ambiguous")
        r = run({**m, "raw_sha256": hashlib.sha256(first.read_bytes()).hexdigest()})
        self.assertEqual((r.state, r.path), ("resolved", first))

    def test_external_rag_original_link_is_exempt_but_inside_is_not(self):
        target = self.write("book.pdf", "PDF", self.ext)
        link = self.ext / "alias.pdf"
        os.link(target, link)
        with mock.patch.object(wiki_raw, "_digest", side_effect=AssertionError("外の原本を読んだ")):
            r = self.resolve(str(link), rag_job_id="job", raw_sha256="0" * 64)[0]
        self.assertEqual((r.state, r.external, r.links), ("resolved", True, []))
        inside = self.raw / "book.pdf"
        os.link(target, inside)
        self.assertEqual(self.resolve(str(inside), rag_job_id="job")[0].state, "link")
        self.assertEqual(self.resolve(str(link))[0].state, "link")

    def test_allowed_roots_checked_before_reads_even_for_rag(self):
        target = self.write("a", "A", self.ext)
        with mock.patch.object(wiki_raw, "_inspect", side_effect=AssertionError("外を調べた")):
            r = wiki_pages.resolve_raw({"type": "source", "raw": str(target), "rag_job_id": "j"}, self.source,
                                        self.wiki, allowed_roots=[self.raw])[0]
        self.assertEqual(r.state, "outside")

    def test_no_raw_root_reports_unchecked_parents_and_checks_target(self):
        target = self.write("a", "A", self.raw)
        self.source_page(str(target))
        found = self.lint(root=False)
        self.assertEqual(found["summary"]["links_raw"], 0)
        self.assertTrue(found["summary"]["raw_paths_unchecked"])
        self.assertIn("途中の道", wiki_lint.render_text(found))
        self.assertEqual(self.lint()["raw_paths_unchecked"], [])

    def test_raw_links_do_not_suppress_missing_wikilinks(self):
        self.assertIsNone(wiki_pages.refused_link("missing", [{"path": "sources/missing.md", "kind": "hardlink", "scope": "raw"}]))

    def test_lint_reports_ambiguity_and_unknown_without_rewriting(self):
        self.write("a", "A", self.wiki)
        self.write("a", "B", self.tmp)
        self.source_page("a")
        before = self.source.read_bytes()
        found = self.lint()
        self.assertEqual(len(found["raw_ambiguous"]), 1)
        self.assertEqual(found["missing_raw"], [])
        self.assertEqual(self.source.read_bytes(), before)
        self.source_page("jump/../a")
        self.assertEqual(len(self.lint()["raw_unknown"]), 1)

    def test_cli_root_argument_and_read_only(self):
        target = self.write("a", "A", self.raw)
        os.link(target, self.raw / "b")
        self.source_page(str(target))
        out = subprocess.run([sys.executable, "-X", "utf8", str(SCRIPTS / "wiki_lint.py"), str(self.wiki),
                              "--raw-root", str(self.raw), "--json"], capture_output=True, timeout=60)
        self.assertEqual(out.returncode, 0, out.stderr.decode("utf-8"))
        found = json.loads(out.stdout)
        self.assertEqual(found["summary"]["links_raw"], 1)
        self.assertEqual(found["missing_raw"], [])
        self.assertEqual(target.read_bytes(), b"A")

    def test_caption_checker_does_not_read_refused_raw(self):
        target = self.write("a.md", "秘密", self.raw)
        os.link(target, self.raw / "b.md")
        self.source_page(str(target))
        with mock.patch.object(wiki_raw, "_raw_meta", side_effect=AssertionError("読んだ")):
            result = wiki_captions.check_wiki(self.wiki, raw_roots=[self.raw])
        self.assertFalse(any(f.code == "unreadable_raw" for f in result.findings))
        self.assertTrue(any(w["state"] == "link" for w in result.raw_warnings))
        self.source_page(str(target), caption_kind="asr")
        result = wiki_captions.check_wiki(self.wiki, raw_roots=[self.raw])
        self.assertTrue(any(f.code == "unreadable_raw" for f in result.findings))
        self.assertIsNone(wiki_captions.resolve_raw_path(str(target), self.source, self.wiki))

    def test_unrelated_ambiguous_raw_does_not_block_caption_check(self):
        self.write("a.md", "A", self.wiki)
        self.write("a.md", "B", self.tmp)
        self.source_page("a.md")
        result = wiki_captions.check_wiki(self.wiki)
        self.assertFalse(any(f.code == "unreadable_raw" for f in result.findings))
        self.assertTrue(any(w["state"] == "ambiguous" for w in result.raw_warnings))

    def test_caption_checker_reports_unchecked_parents(self):
        target = self.write("a.md", "A", self.raw)
        self.source_page(str(target))
        result = wiki_captions.check_wiki(self.wiki)
        self.assertTrue(any(w["state"] == "parents_unchecked" for w in result.raw_warnings))
        checked = wiki_captions.check_wiki(self.wiki, raw_roots=[self.raw])
        self.assertFalse(any(w["state"] == "parents_unchecked" for w in checked.raw_warnings))

    def test_caption_checker_reports_raw_version_and_identity_mismatches(self):
        target = self.write("a.md", '---\nurl: "https://actual"\n---\n内容', self.raw)
        for meta, kind in (({"raw_sha256": "0" * 64}, "version"), ({"url": "https://other"}, "identity")):
            for related in ("unrelated", "video", "selected"):
                with self.subTest(kind=kind, related=related):
                    self.source_page(str(target), **meta, **({"caption_kind": "asr"} if related == "video" else {}))
                    result = wiki_captions.check_wiki(self.wiki, raw_roots=[self.raw],
                                                     only_raw=str(target) if related == "selected" else None)
                    warnings = [w for w in result.raw_warnings if w["state"] == "missing"]
                    self.assertEqual(len(warnings), 1)
                    self.assertEqual(warnings[0]["mismatches"][0]["kind"], kind)
                    errors = [f for f in result.findings if f.code == "unreadable_raw"]
                    self.assertEqual(len(errors), 0 if related == "unrelated" else 1)

    def test_queued_directory_replaced_by_link_is_not_read(self):
        queued = self.raw / "a"
        queued.mkdir()
        trigger = self.write("z.txt", "後の項目", self.raw)
        self.write("secret.txt", "外の原本", self.ext)
        original_stat = wiki_pages._stat_entry
        original_list = wiki_pages._list_dir
        changed = []

        def replace_queued(path):
            if Path(path) == trigger and not changed:
                queued.rmdir()
                if not junction(queued, self.ext):
                    self.skipTest("ディレクトリのリンクを作れない")
                changed.append(True)
            return original_stat(path)

        with mock.patch.object(wiki_pages, "_stat_entry", side_effect=replace_queued), \
             mock.patch.object(wiki_pages, "_list_dir", side_effect=lambda p: sorted(original_list(p), key=lambda e: e.name)), \
             mock.patch.object(wiki_raw, "_digest", side_effect=AssertionError("リンクを検出せず本文を読んだ")):
            result = self.resolve(str(self.raw), raw_sha256="0" * 64)[0]
        self.assertTrue(changed)
        self.assertEqual(result.state, "link")
        self.assertEqual(Path(result.links[0]["path"]), queued)


class LocalRawTests(Base):
    def setUp(self):
        super().setUp()
        self.raw = self.tmp / "raw"
        self.raw.mkdir()

    def command(self, action, source, *extra):
        return subprocess.run(
            [sys.executable, "-X", "utf8", "-B", str(SCRIPTS / "wiki_raw_ingest.py"), action,
             "--wiki", str(self.wiki), "--raw-root", str(self.raw), "--source", str(source), *extra],
            check=False, capture_output=True, encoding="utf-8", timeout=60,
        )

    def test_cli_saves_link_contents_and_lints_a_previous_raw_root(self):
        outside = self.write("clip.md", "取り込む内容", self.ext)
        asset = self.wiki / "assets" / "clip.md"
        asset.parent.mkdir()
        os.link(outside, asset)
        done = self.command("save", asset, "--name", "clip.md")
        self.assertEqual(done.returncode, 0, done.stderr)
        result = json.loads(done.stdout)
        self.assertEqual(result["raw_ref"], "raw/clip.md")
        stored = self.raw / "clip.md"
        self.assertEqual(stored.read_bytes(), outside.read_bytes())
        self.assertFalse(stored.samefile(asset))
        self.assertTrue(outside.samefile(asset))
        page = self.write("sources/clip.md", "---\ntype: source\ntitle: クリップ\n"
                          f"raw: {json.dumps(result['raw_ref'], ensure_ascii=False)}\n"
                          f"raw_sha256: {result['raw_sha256']}\n---\n")
        raw_now = self.tmp / "new-raw"
        raw_now.mkdir()
        found = wiki_lint.lint(wiki_lint.collect_pages(self.wiki), 100, 200, [], False, 5,
                               wiki_root=self.wiki, raw_root=raw_now)
        self.assertFalse(found["raw_paths_unchecked"])
        self.assertFalse(found["missing_raw"])
        self.assertFalse(found["raw_version_unverified"])
        self.assertTrue(page.exists())

    def test_wiki_article_and_raw_in_place_links_are_refused(self):
        article = self.write("sources/linked.md", "記事")
        os.link(article, self.ext / "article.md")
        raw = self.raw / "linked.md"
        os.link(article, raw)
        for source in (article, raw):
            with self.subTest(source=source):
                with self.assertRaisesRegex((ValueError, OSError), "hardlink"):
                    wiki_raw_ingest.save(self.wiki, self.raw, source, None)
        self.assertEqual(list(self.raw.iterdir()), [raw])

    def test_copies_directory_links_and_reuses_saved_tree(self):
        source = self.ext / "bundle"
        source.mkdir()
        data = self.write("data.txt", "同じ中身", self.ext / "material")
        for name in ("a", "b"):
            if not junction(source / name, data.parent):
                self.skipTest("ディレクトリのリンクを作れない")
        self.write(".note", "隠し項目", source)
        result = wiki_raw_ingest.save(self.wiki, self.raw, source, None)
        stored = self.raw / "bundle"
        for name in ("a", "b"):
            self.assertEqual((stored / name / "data.txt").read_bytes(), data.read_bytes())
            self.assertFalse((stored / name).samefile(data.parent))
        self.assertTrue((stored / ".note").is_file())
        self.assertEqual(result["raw_sha256"], wiki_raw.raw_digest(stored, self.raw))
        again = wiki_raw_ingest.save(self.wiki, self.raw, stored, None)
        self.assertEqual((again["status"], again["raw_sha256"]), ("existing", result["raw_sha256"]))

    def test_refuses_existing_empty_directory_and_cyclic_copy(self):
        empty = self.ext / "empty"
        empty.mkdir()
        target = self.raw / "empty"
        target.mkdir()
        with self.assertRaises(FileExistsError):
            wiki_raw_ingest.save(self.wiki, self.raw, empty, None)
        self.assertEqual(list(target.iterdir()), [])
        source = self.ext / "cyclic"
        source.mkdir()
        if not junction(source / "back", source):
            self.skipTest("ディレクトリのリンクを作れない")
        with self.assertRaisesRegex(ValueError, "循環"):
            wiki_raw_ingest.save(self.wiki, self.raw, source, None)
        self.assertFalse((self.raw / "cyclic").exists())
        self.assertEqual(list(self.raw.glob(".wiki-raw-ingest-*.tmp")), [])

    def test_directory_copy_checks_a_recorded_root_inside_the_input(self):
        source = self.ext / "collection"
        old_raw = source / "raw"
        old_raw.mkdir(parents=True)
        outside = self.write("book.txt", "出典", self.ext)
        os.link(outside, old_raw / "book.txt")
        record_raw_root(self.wiki, old_raw, writer="test")
        with self.assertRaisesRegex(OSError, "hardlink"):
            wiki_raw_ingest.save(self.wiki, self.raw, source, None)
        self.assertFalse((self.raw / source.name).exists())
        self.assertEqual(list(self.raw.glob(".wiki-raw-ingest-*.tmp")), [])

    def test_directory_save_uses_the_same_lock_for_the_raw_root(self):
        source = self.ext / "bundle"
        source.mkdir()
        with WriteGuard(self.raw).hold_lock(self.raw / ".wiki-raw-ingest.lock"):
            blocked = self.command("save", source)
            self.assertEqual(blocked.returncode, 1)
            self.assertIn("同じ対象の処理が動いている", blocked.stderr)
            self.assertFalse((self.raw / source.name).exists())
        done = self.command("save", source)
        self.assertEqual(done.returncode, 0, done.stderr)
        self.assertTrue((self.raw / source.name).is_dir())

    def test_copy_rejects_a_branch_that_contains_the_destination(self):
        source = self.ext / "bundle"
        source.mkdir()
        if not junction(source / "destination", self.raw):
            self.skipTest("ディレクトリのリンクを作れない")
        with self.assertRaisesRegex(ValueError, "一時ディレクトリと取り込み元が重なる"):
            wiki_raw_ingest.save(self.wiki, self.raw, source, None)
        self.assertFalse((self.raw / source.name).exists())
        self.assertFalse(list(self.raw.glob(".wiki-raw-ingest-*.tmp")))

    def test_unknown_recorded_scope_stops_external_copy_and_pdf_registration(self):
        self.write(".wiki-cache/raw-roots.d/broken.json", "{")
        source = self.write("book.pdf", "%PDF-1.7", self.ext)
        for action in ("save", "pdf"):
            with self.subTest(action=action):
                done = self.command(action, source)
                self.assertEqual(done.returncode, 1)
                self.assertIn("過去の raw の根を確認できない", done.stderr)
        self.assertFalse(list(self.raw.iterdir()))

    def test_failed_root_record_leaves_no_copy_or_derivative(self):
        source = self.ext / "encoded.txt"
        source.write_bytes("文字コードを確認する。\r\n".encode("cp932"))
        fault = OSError("根を記録できない")
        with mock.patch.object(wiki_raw_ingest, "record_raw_root", side_effect=fault):
            with self.assertRaisesRegex(OSError, "根を記録できない"):
                wiki_raw_ingest.save(self.wiki, self.raw, source, None)
        self.assertEqual(list(self.raw.iterdir()), [])
        first = wiki_raw_ingest.save(self.wiki, self.raw, source, None)
        stored = self.raw / source.name
        args = (self.wiki, self.raw, stored, first["raw_sha256"], "encoded.utf8.txt")
        with mock.patch.object(wiki_raw_ingest, "record_raw_root", side_effect=fault):
            with self.assertRaisesRegex(OSError, "根を記録できない"):
                wiki_raw_ingest.encoding(*args)
        self.assertEqual(list(self.raw.iterdir()), [stored])
        for status in ("created", "existing"):
            second = wiki_raw_ingest.encoding(*args)
            data = (self.raw / "encoded.utf8.txt").read_bytes()
            self.assertEqual(data.decode("utf-8"), "文字コードを確認する。\r\n")
            self.assertEqual(second["raw_sha256"], hashlib.sha256(data).hexdigest())
            self.assertEqual(second["status"], status)
        self.assertEqual(stored.read_bytes(), source.read_bytes())
        page = self.wiki / "sources" / "encoded.md"
        evidence = [first, second]
        refs = wiki_raw.resolve_raw(
            {"type": "source", "raw": [item["raw_ref"] for item in evidence],
             "raw_sha256": [item["raw_sha256"] for item in evidence]},
            page, self.wiki, raw_roots=[self.raw],
        )
        self.assertEqual([ref.state for ref in refs], ["resolved", "resolved"])
        self.assertFalse(any(ref.version_unverified for ref in refs))

    def test_pdf_preflight_preserves_external_path_and_checks_historical_root(self):
        sample = self.write("book.pdf", "%PDF-1.7", self.ext)
        outside = self.ext / "alias.pdf"
        os.link(sample, outside)
        done = self.command("pdf", outside)
        self.assertEqual(done.returncode, 0, done.stderr)
        self.assertEqual(Path(json.loads(done.stdout)["source"]), outside)
        self.assertFalse((self.wiki / ".wiki-cache").exists())
        old = self.tmp / "old"
        old.mkdir()
        record_raw_root(self.wiki, old, writer="test")
        os.link(sample, old / "book.pdf")
        hidden = self.write(".folder/book.pdf", "%PDF-1.7", old)
        for source in (old / "book.pdf", hidden, self.ext / "unused" / ".." / "book.pdf"):
            with self.subTest(source=source):
                self.assertEqual(self.command("pdf", source).returncode, 1)

        external_hidden = self.write(".book.pdf", "%PDF-1.7", self.ext)
        self.assertEqual(self.command("pdf", external_hidden).returncode, 0)
        result = wiki_raw.resolve_raw({"type": "source", "raw": str(external_hidden), "rag_job_id": "example"},
                                      self.wiki / "sources/book.md", self.wiki, raw_roots=[self.raw])
        self.assertEqual(result[0].state, "resolved")


class UpgradeRawRootsTests(Base):
    def upgrade(self, *options, base=None):
        args = ["init_wiki.py", str(base or self.tmp), "--upgrade", *map(str, options)]
        with mock.patch.object(sys, "argv", args), mock.patch.object(init_wiki, "install_runtime") as install, \
             contextlib.redirect_stdout(io.StringIO()):
            init_wiki.main()
        install.assert_called_once()

    def lint(self, current):
        done = subprocess.run([sys.executable, "-X", "utf8", "-B", str(SCRIPTS / "wiki_lint.py"), str(self.wiki),
                               "--raw-root", str(current), "--json"], capture_output=True, encoding="utf-8", timeout=60)
        self.assertEqual(done.returncode, 0, done.stderr)
        return json.loads(done.stdout)

    def test_upgrade_feeds_lint_after_switching_roots_and_preserves_existing_pages(self):
        current = self.tmp / "raw"
        archive = self.ext / "old"
        targets = [self.write("folder/a.txt", "原本", root) for root in (current, archive)]
        for number, target in enumerate(targets):
            sha = hashlib.sha256(target.read_bytes()).hexdigest()
            ref = json.dumps(target.as_posix(), ensure_ascii=False)
            self.write(f"sources/s{number}.md", f"---\ntype: source\ntitle: 出典\nraw: {ref}\nraw_sha256: {sha}\n---\n")
        self.write("sources/legacy.md",
                   f"---\ntype: source\ntitle: 旧版\nraw: {json.dumps(targets[1].as_posix(), ensure_ascii=False)}\n---\n")
        before = {path: path.read_bytes() for path in (self.wiki / "sources").iterdir()}
        self.upgrade("--previous-raw-root", "ext/old")
        next_root = self.tmp / "new-raw"
        self.upgrade("--raw-dir", "new-raw")
        self.assertEqual(set(wiki_raw_roots.read_raw_roots(self.wiki)[0]), {current, archive, next_root})
        report = self.lint(next_root)
        self.assertFalse(report["raw_paths_unchecked"])
        self.assertFalse(report["missing_raw"])
        self.assertEqual(len(report["raw_version_unverified"]), 1)
        self.assertEqual({path: path.read_bytes() for path in before}, before)

        original = targets[1]
        external = self.write("destination/a.txt", "原本", self.ext)
        original.unlink()
        original.parent.rmdir()
        if not junction(original.parent, external.parent):
            self.skipTest("ディレクトリのリンクを作れない")
        report = self.lint(next_root)
        self.assertTrue(any(item["scope"] == "raw" and Path(item["path"]) == original.parent
                            for item in report["links"]), report["links"])
        self.assertFalse(report["raw_paths_unchecked"])

    def test_absolute_roots_outside_base_and_repeated_upgrade(self):
        current = self.ext / "raw"
        previous = self.ext / "old"
        previous.mkdir()
        base = self.tmp / "different-base"
        base.mkdir()
        args = ("--wiki-dir", self.wiki, "--raw-dir", current, "--previous-raw-root", previous,
                "--previous-raw-root", previous)
        self.upgrade(*args, base=base)
        records = self.wiki / wiki_raw_roots.RECORDS
        before = {path: path.read_bytes() for path in records.glob("*.json")}
        self.assertEqual(len(before), 2)
        self.assertTrue((current / "assets").is_dir())
        self.upgrade(*args, base=base)
        self.assertEqual({path: path.read_bytes() for path in records.glob("*.json")}, before)

    def test_preserves_given_spelling_through_a_base_alias(self):
        alias = self.tmp / "view"
        actual = self.ext / "project"
        (actual / "wiki").mkdir(parents=True)
        (actual / "wiki" / "SCHEMA.md").write_text("# 根の確認", encoding="utf-8")
        if not junction(alias, actual):
            self.skipTest("ベースディレクトリへのリンクを作れない")
        self.upgrade(base=alias)
        found = list((actual / "wiki" / wiki_raw_roots.RECORDS).glob("*.json"))
        self.assertEqual(len(found), 1)
        record = json.loads(found[0].read_text(encoding="utf-8"))
        self.assertEqual(Path(record["given"]), alias / "raw")
        self.assertEqual(Path(record["resolved"]), actual / "raw")

    def test_invalid_previous_root_is_rejected_before_creating_anything(self):
        before = set(self.tmp.rglob("*"))
        previous = (self.tmp / "missing", self.ext / "file", self.ext / "child" / "..")
        self.write("file", "ディレクトリ以外", self.ext)
        before.add(self.ext / "file")
        for root in previous:
            with self.subTest(path=root), mock.patch.object(init_wiki, "install_runtime") as install, \
                 contextlib.redirect_stdout(io.StringIO()), contextlib.redirect_stderr(io.StringIO()) as stderr:
                with self.assertRaises(SystemExit) as failure:
                    init_wiki.init_wiki(self.tmp, "wiki", "raw", upgrade=True, previous_raw_roots=(root,))
                self.assertEqual(failure.exception.code, 1)
                self.assertIn("raw の根を記録できない", stderr.getvalue())
                install.assert_not_called()
            self.assertEqual(set(self.tmp.rglob("*")), before)

    def test_guard_refusal_leaves_the_link_target_untouched(self):
        cache = self.wiki / ".wiki-cache"
        cache.mkdir()
        records = self.wiki / wiki_raw_roots.RECORDS
        if not junction(records, self.ext):
            self.skipTest("記録先へのリンクを作れない")
        with mock.patch.object(init_wiki, "install_runtime") as install, contextlib.redirect_stdout(io.StringIO()), \
             contextlib.redirect_stderr(io.StringIO()) as stderr, self.assertRaises(SystemExit):
            init_wiki.init_wiki(self.tmp, "wiki", "raw", upgrade=True)
        self.assertIn("raw の根を記録できない", stderr.getvalue())
        self.assertFalse((self.tmp / "raw").exists())
        self.assertFalse(list(self.ext.iterdir()))
        install.assert_not_called()

    def test_partial_registration_is_reused_and_tampered_record_is_preserved(self):
        old = self.ext / "old"
        old.mkdir()
        real_write = wiki_raw_roots._write_record

        def fail_old(guard, path, pair, writer):
            if pair[0] == old:
                raise PermissionError("過去の根を登録できない")
            real_write(guard, path, pair, writer)

        with mock.patch.object(wiki_raw_roots, "_write_record", side_effect=fail_old), \
             mock.patch.object(init_wiki, "install_runtime") as install, contextlib.redirect_stdout(io.StringIO()), \
             contextlib.redirect_stderr(io.StringIO()), self.assertRaises(SystemExit):
            init_wiki.init_wiki(self.tmp, "wiki", "raw", upgrade=True, previous_raw_roots=(old,))
        install.assert_not_called()
        folder = self.wiki / wiki_raw_roots.RECORDS
        first, = folder.glob("*.json")
        registered = first.read_bytes()
        self.upgrade("--previous-raw-root", old)
        self.assertEqual(first.read_bytes(), registered)
        self.assertEqual(len(list(folder.glob("*.json"))), 2)

        data = json.loads(registered)
        data["writer"] = "別の書き手"
        first.write_text(json.dumps(data, ensure_ascii=False), encoding="utf-8")
        tampered = first.read_bytes()
        with mock.patch.object(init_wiki, "install_runtime") as install, contextlib.redirect_stdout(io.StringIO()), \
             contextlib.redirect_stderr(io.StringIO()) as stderr, self.assertRaises(SystemExit):
            init_wiki.init_wiki(self.tmp, "wiki", "raw", upgrade=True)
        self.assertIn("書き手が一致しない", stderr.getvalue())
        self.assertEqual(first.read_bytes(), tampered)
        install.assert_not_called()

    def test_parallel_registrations_keep_distinct_roots_and_share_the_common_record(self):
        from concurrent.futures import ThreadPoolExecutor
        from threading import Barrier

        roots = [self.ext / name for name in ("current", "first", "second")]
        for root in roots:
            root.mkdir()
        current, first, second = [wiki_raw_roots.raw_root_pair(root) for root in roots]
        ready = Barrier(2)

        def register(previous):
            ready.wait(5)
            wiki_raw_roots.register_upgrade_roots(WriteGuard(self.wiki), [current, previous])

        with mock.patch.object(wiki_raw_roots, "_write_record", wraps=wiki_raw_roots._write_record) as write, \
             ThreadPoolExecutor(max_workers=2) as executor:
            list(executor.map(register, (first, second)))
        self.assertEqual(write.call_count, 3)
        self.assertEqual(len(list((self.wiki / wiki_raw_roots.RECORDS).glob("*.json"))), 3)
        paths, unchecked = wiki_raw_roots.read_raw_roots(self.wiki)
        self.assertEqual(set(paths), set(roots))
        self.assertEqual(unchecked, [])


if __name__ == "__main__":
    unittest.main()
