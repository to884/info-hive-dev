"""ADR-0029 段階2。raw の解決、読まずに拒否する順番、lint と字幕検査の共通の境界。"""
from __future__ import annotations

import hashlib
import json
import os
from pathlib import Path
import subprocess
import sys
from unittest import mock
import unittest

from tests.wiki.test_wiki_links import Base, junction, symlink, SCRIPTS
import wiki_captions
import wiki_lint
import wiki_pages
import wiki_raw


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
        with mock.patch.object(wiki_raw, "_identity", side_effect=OSError("FileIdInfo がない")):
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
        with mock.patch.object(wiki_raw, "_identity", side_effect=OSError("FileIdInfo がない")):
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


if __name__ == "__main__":
    unittest.main()
