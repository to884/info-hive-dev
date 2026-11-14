"""URL の取り込みの検査（wiki_rawcheck.py）と、wiki_fetch.py の雑音の規則・--html-file・作業用の写しの試験。

設計: docs/plans/wiki-web-ingest-check-2026-11-13.md

取得（`fetch`）を差し替えるので、ネットにはつながない。

実行（標準ライブラリだけで動く）:
    python -X utf8 -m unittest tests/wiki/test_wiki_web_check.py -v
"""
from __future__ import annotations

import argparse
import contextlib
import io
import json
import os
import struct
import sys
import tempfile
import unittest
import zlib
from pathlib import Path
from unittest import mock

ROOT = Path(__file__).resolve().parents[2]
SCRIPTS = ROOT / "info-hive-wiki/skills/info-hive/scripts"
sys.path.insert(0, str(SCRIPTS))

import wiki_fetch  # noqa: E402
import wiki_rawcheck  # noqa: E402

PAGE_URL = "https://site.example/request/start"
LONG = "This is the body text of the article and it is long enough to count as the first paragraph. " * 2


def png(width: int = 200, height: int = 120) -> bytes:
    ihdr = struct.pack(">II", width, height) + b"\x08\x06\x00\x00\x00"
    chunk = b"IHDR" + ihdr
    return (b"\x89PNG\r\n\x1a\n" + struct.pack(">I", len(ihdr)) + chunk
            + struct.pack(">I", zlib.crc32(chunk) & 0xFFFFFFFF))


class FetchStub:
    def __init__(self, html: bytes):
        self.html = html
        self.requested: list[str] = []

    def __call__(self, url, timeout, max_bytes, accept="", block_private=False):
        self.requested.append(url)
        if url == PAGE_URL:
            return self.html, url, "text/html; charset=utf-8"
        return png(), url, "image/png"


def html_page(article: str, *, head: str = "", body_before: str = "") -> bytes:
    return ("<!doctype html><html lang=\"en\"><head><title>Article</title>" + head + "</head><body>"
            + body_before + "<article><h1>Article</h1>" + article + "</article></body></html>").encode("utf-8")


class FetchCase(unittest.TestCase):
    def setUp(self):
        tmp = tempfile.TemporaryDirectory()
        self.addCleanup(tmp.cleanup)
        self.base = Path(tmp.name)
        self.wiki = self.base / "wiki"
        self.raw = self.base / "raw"
        self.wiki.mkdir()
        self.raw.mkdir()
        (self.wiki / "SCHEMA.md").write_text("# s\n", encoding="utf-8")

    def args(self, **kw) -> argparse.Namespace:
        values = dict(url=PAGE_URL, wiki=self.wiki, raw_root=self.raw, slug="page", json=True, no_images=False,
                      timeout=5, max_bytes=wiki_fetch.DEFAULT_MAX_BYTES, max_images=50, force=False,
                      keep_noise=False, html_file=None, page_url=None)
        values.update(kw)
        return argparse.Namespace(**values)

    def build(self, html: bytes, **kw) -> tuple[dict, str, FetchStub]:
        stub = FetchStub(html)
        with mock.patch.object(wiki_fetch, "fetch", stub), \
                mock.patch.object(wiki_fetch, "is_private_host", lambda host: False):
            code, result = wiki_fetch.build(self.args(**kw))
        self.assertEqual(code, 0, result)
        text = (self.raw / "page.md").read_text(encoding="utf-8")
        return result, text, stub


class NoiseRuleTest(FetchCase):
    def test_header_rules_drop_tags_and_phrases(self):
        article = ('<p><a href="https://site.example/tag/ai">AI</a></p>'
                   '<p>Member-only story</p><p>Article</p>'
                   '<p>Read this story for free: <a href="https://site.example/x?source=friends_link&amp;sk=1">link</a></p>'
                   f"<p>{LONG}</p><p>Press enter or click to view image in full size</p><p>{LONG}</p>")
        result, text, _ = self.build(html_page(article))
        rules = sorted(r["rule"] for r in result["removed_by_rule"])
        self.assertEqual(rules, ["duplicate_title", "medium_friend_link", "medium_member_only",
                                 "medium_view_image", "tag_links"])
        self.assertNotIn("Member-only", text)
        self.assertNotIn("/tag/ai", text)
        self.assertIn(LONG.strip(), text)

    def test_same_strings_in_body_are_kept(self):
        """本文の前の部分の規則は、本文の中では当てない（対照）。"""
        article = (f"<p>{LONG}</p><p><a href=\"https://docs.example/tag/release-1\">Tag specification</a></p>"
                   "<p>Top highlight</p><p>Article</p>")
        result, text, _ = self.build(html_page(article))
        self.assertEqual(result["removed_by_rule"], [])
        self.assertIn("[Tag specification](https://docs.example/tag/release-1)", text)
        self.assertIn("Top highlight", text)

    def test_emphasis_marks_do_not_count_as_text(self):
        """79 文字の段落を強調で囲んでも、本文の前の部分の判定は変わらない。"""
        short = "x" * 79
        for body in (f"<p>{short}</p>", f"<p><strong>{short}</strong></p>"):
            with self.subTest(body=body):
                result, text, _ = self.build(html_page(body + "<p>Top highlight</p>" + f"<p>{LONG}</p>"), force=True)
                self.assertIn("medium_top_highlight", [r["rule"] for r in result["removed_by_rule"]])

    def test_keep_noise_disables_rules(self):
        article = '<p><a href="https://site.example/tag/ai">AI</a></p>' + f"<p>{LONG}</p>"
        result, text, _ = self.build(html_page(article), keep_noise=True)
        self.assertEqual(result["removed_by_rule"], [])
        self.assertIn("/tag/ai", text)

    def test_mediawiki_parts_only_on_mediawiki(self):
        article = ('<a class="mw-jump-link" href="#c">スキップ</a><div id="siteSub">出典: 百科事典</div>'
                   '<table><tr><td class="metadata">i</td><td>曖昧さ回避の注記</td></tr></table>'
                   f"<p>{LONG}</p>")
        mw = '<meta name="generator" content="MediaWiki 1.48.0">'
        result, text, _ = self.build(html_page(article, head=mw))
        self.assertEqual(sorted(r["rule"] for r in result["removed_by_rule"]),
                         ["mediawiki_metadata_table", "mediawiki_site_sub", "mediawiki_skip_link"])
        self.assertNotIn("曖昧さ回避", text)
        # MediaWiki でないページの metadata の表は、本文のデータ表であり得るので残す（対照）。
        result, text, _ = self.build(html_page(article), force=True)
        self.assertEqual(result["removed_by_rule"], [])
        self.assertIn("曖昧さ回避", text)

    def test_mediawiki_rule_works_when_html_class_hits_noise_words(self):
        """<html> の class が NOISE_WORDS に当たる Wikipedia でも、部品を落とせること。"""
        page = ('<!doctype html><html class="client-nojs vector-toc-available"><head><title>T</title>'
                '<meta name="generator" content="MediaWiki 1.48"></head><body>'
                '<a class="mw-jump-link" href="#c">スキップ</a>'
                f"<main><h1>T</h1><p>{LONG}</p></main></body></html>").encode("utf-8")
        result, text, _ = self.build(page)
        self.assertEqual([r["rule"] for r in result["removed_by_rule"]], ["mediawiki_skip_link"])


class HtmlFileTest(FetchCase):
    def test_page_url_is_the_base(self):
        html = html_page(f'<p>{LONG}</p><img src="img.png" width="300" height="200"><p><a href="next.html">n</a></p>')
        path = self.base / "page.html"
        path.write_bytes(html)
        stub = FetchStub(b"")
        with mock.patch.object(wiki_fetch, "fetch", stub), \
                mock.patch.object(wiki_fetch, "is_private_host", lambda host: False):
            code, result = wiki_fetch.build(self.args(html_file=path, page_url="https://site.example/actual/article/"))
        self.assertEqual(code, 0)
        text = (self.raw / "page.md").read_text(encoding="utf-8")
        self.assertIn("https://site.example/actual/article/img.png", stub.requested)
        self.assertNotIn(PAGE_URL, stub.requested)
        self.assertIn("(https://site.example/actual/article/next.html)", text)
        self.assertIn('source_sha256_of: "dom"', text)
        self.assertIn('final_url: "https://site.example/actual/article/"', text)

    def test_non_utf8_file_is_rejected(self):
        path = self.base / "page.html"
        path.write_bytes(html_page(f"<p>{LONG}</p>").replace(b"body text", "café".encode("cp1252")))
        with self.assertRaises(ValueError):
            wiki_fetch.build(self.args(html_file=path, page_url=PAGE_URL))
        self.assertFalse((self.raw / "page.md").exists())


class WorkDirTest(FetchCase):
    def test_snapshot_matches_raw_and_records_language(self):
        result, text, _ = self.build(html_page(f"<p>{LONG}</p>"))
        wd = wiki_rawcheck.work_dir(self.wiki, "page")
        self.assertEqual((wd / "fetched.md").read_text(encoding="utf-8"), text)
        fetch = json.loads((wd / "fetch.json").read_text(encoding="utf-8"))
        self.assertTrue(fetch["needs_translation"])
        self.assertTrue(result["work_dir"])

    def test_unchanged_reports_missing_work_dir(self):
        self.build(html_page(f"<p>{LONG}</p>"))
        wiki_rawcheck.remove_work_dir(self.wiki, "page")
        stub = FetchStub(html_page(f"<p>{LONG}</p>"))
        with mock.patch.object(wiki_fetch, "fetch", stub), \
                mock.patch.object(wiki_fetch, "is_private_host", lambda host: False):
            code, result = wiki_fetch.build(self.args())
        self.assertTrue(result["unchanged"])
        self.assertFalse(result["work_dir"])

    def test_raw_is_not_written_when_snapshot_fails(self):
        """名前の変更（raw の一時のファイルから正式な名前へ）に失敗すると、raw は書かれず、写しの印（fetch.json）も
        置かれないので、写しは「そろっていない」になる。"""
        stub = FetchStub(html_page(f"<p>{LONG}</p>"))
        with mock.patch.object(wiki_fetch, "fetch", stub), \
                mock.patch.object(wiki_fetch, "is_private_host", lambda host: False), \
                mock.patch.object(wiki_fetch.os, "replace", side_effect=OSError("書けない")):
            with self.assertRaises(OSError):
                wiki_fetch.build(self.args())
        self.assertFalse((self.raw / "page.md").exists())
        self.assertTrue((wiki_rawcheck.work_dir(self.wiki, "page") / "fetched.md").is_file())
        self.assertFalse(wiki_rawcheck.work_dir_complete(self.wiki, "page"))

    def test_japanese_slug_round_trip(self):
        """日本語のスラッグの画像を、取得から freeze と check まで通す。"""
        html = html_page(f'<p>{LONG}</p><img src="i.png" width="300" height="200"><p>{LONG}</p>')
        result, text, _ = self.build(html, slug="日本語")
        rel = result["images"][0]["path"]
        self.assertTrue(rel.startswith("assets/日本語/"))
        self.assertEqual(wiki_rawcheck.freeze(self.wiki, self.raw, "日本語")[0], 0)
        raw = self.raw / "日本語.md"
        out = text.replace('translated_by: ""', 'translated_by: "Claude Sonnet 5.5"')
        out = out.replace(LONG.strip(), "本文の訳である。")
        line = next(x for x in out.split("\n") if x.startswith("!["))
        out = out.replace(line + "\n", line + "\n\n> Claude Sonnet 5.5 補足: 図の説明である。\n", 1)
        raw.write_text(out, encoding="utf-8", newline="\n")
        code, check = wiki_rawcheck.check(self.wiki, self.raw, "日本語", None, None)
        self.assertEqual(code, 0, check["errors"])

    def build(self, html: bytes, **kw):  # スラッグを変えられるように上書きする
        stub = FetchStub(html)
        with mock.patch.object(wiki_fetch, "fetch", stub), \
                mock.patch.object(wiki_fetch, "is_private_host", lambda host: False):
            code, result = wiki_fetch.build(self.args(**kw))
        self.assertEqual(code, 0, result)
        text = (self.raw / f"{kw.get('slug', 'page')}.md").read_text(encoding="utf-8")
        return result, text, stub


class LanguageAndSlugTest(unittest.TestCase):
    def test_needs_translation(self):
        self.assertTrue(wiki_fetch.needs_translation("en", 0.0))
        self.assertFalse(wiki_fetch.needs_translation("ja", 0.8))
        self.assertFalse(wiki_fetch.needs_translation("", 0.7))
        self.assertTrue(wiki_fetch.needs_translation("", 0.1))
        # lang="ja" なのに本文が英語なら、割合で決める（取り込みの手順と同じ）。
        self.assertTrue(wiki_fetch.needs_translation("ja", 0.05))
        self.assertFalse(wiki_fetch.needs_translation("en", 0.9))

    def test_slug_rejects_aliases_and_reserved_names(self):
        for bad in ("x.", "CON", "nul", "com1.txt", "LPT¹"):
            with self.subTest(bad=bad), self.assertRaises(ValueError):
                wiki_fetch.check_slug(bad)
        for ok in ("x.v2", "x.lock", "console", "COM10x"):
            with self.subTest(ok=ok):
                wiki_fetch.check_slug(ok)


# ---------------------------------------------------------------- wiki_rawcheck

FM = '---\nurl: "https://site.example/a"\ntitle: "A"\nsource_sha256: "x"\ntranslated_by: ""\n---\n'


class RawCheckCase(unittest.TestCase):
    def setUp(self):
        tmp = tempfile.TemporaryDirectory()
        self.addCleanup(tmp.cleanup)
        self.base = Path(tmp.name)
        self.wiki = self.base / "wiki"
        self.raw = self.base / "raw"
        self.wd = wiki_rawcheck.work_dir(self.wiki, "a")
        self.wd.mkdir(parents=True)
        self.raw.mkdir()
        (self.wiki / "SCHEMA.md").write_text("# s\n", encoding="utf-8")

    def setup_fetch(self, body: str, *, images: list[str] = (), needs_translation: bool = True, fm: str = FM):
        text = fm + "\n" + body
        (self.wd / "fetched.md").write_text(text, encoding="utf-8", newline="\n")
        (self.raw / "a.md").write_text(text, encoding="utf-8", newline="\n")
        for rel in images:
            p = self.raw / rel
            p.parent.mkdir(parents=True, exist_ok=True)
            p.write_bytes(png())
        fetch = {"needs_translation": needs_translation, "images": [{"path": r} for r in images],
                 "removed_by_rule": []}
        (self.wd / "fetch.json").write_text(json.dumps(fetch), encoding="utf-8")

    def write_raw(self, body: str, fm: str = FM):
        (self.raw / "a.md").write_text(fm + "\n" + body, encoding="utf-8", newline="\n")

    def freeze(self) -> dict:
        code, result = wiki_rawcheck.freeze(self.wiki, self.raw, "a")
        self.assertEqual(code, 0 if result["ok"] else 1)
        return result

    def check(self, override=None) -> dict:
        code, result = wiki_rawcheck.check(self.wiki, self.raw, "a", override, "試験" if override else None)
        self.assertEqual(code, 0 if result["ok"] else 1)
        return result

    def kinds(self, result: dict) -> list[str]:
        return sorted({e["kind"] for e in result["errors"]})


SRC = """# A

Tag line

Alpha Share beta Tweet gamma with `code(1)` and [link](https://x.example/l).

## About the author

Writer bio.

```
SELECT 1; -- rationale
```

![](assets/a/a-01.png "https://x.example/1.png")

![](assets/a/a-01.png "https://x.example/1.png")
"""


class FreezeTest(RawCheckCase):
    def setUp(self):
        super().setUp()
        self.setup_fetch(SRC, images=["assets/a/a-01.png"])

    def test_deletions_pass_and_are_recorded(self):
        out = SRC.replace("Tag line\n\n", "").replace(" Share", "").replace(" Tweet", "")
        out = out.replace("## About the author\n\nWriter bio.\n\n", "")
        # 共有のファイルを使う 2 つの画像の行の片方だけを消す。ファイルは残す。
        out = out.replace('![](assets/a/a-01.png "https://x.example/1.png")\n\n', "", 1)
        self.write_raw(out)
        result = self.freeze()
        self.assertTrue(result["ok"], result["errors"])
        self.assertIn("Tag line", result["removed_lines"])
        self.assertIn("## About the author", result["removed_lines"])
        self.assertIn("Alpha beta gamma with `code(1)` and [link](https://x.example/l).",
                      [c["raw"] for c in result["shortened_lines"]])
        self.assertTrue((self.wd / "cleaned.md").is_file())

    def test_rejected_edits(self):
        cases = {
            "added": SRC.replace("Tag line", "Tag line\n\nNew line"),
            "rewrite": SRC.replace("Writer bio.", "Writer biography."),
            "reorder": SRC.replace("Tag line\n\n", "").replace("Writer bio.\n", "Writer bio.\n\nTag line\n"),
            "title": SRC.replace("# A\n\n", ""),
            "code": SRC.replace("SELECT 1; -- rationale", "SELECT 1;"),
            "code_span": SRC.replace("`code(1)`", "`code`"),
            "link": SRC.replace("[link](https://x.example/l)", "[link]"),
        }
        for name, body in cases.items():
            with self.subTest(name=name):
                self.write_raw(body)
                result = self.freeze()
                self.assertFalse(result["ok"], name)
                self.assertFalse((self.wd / "cleaned.md").exists())

    def test_frontmatter_must_not_change(self):
        self.write_raw(SRC, fm=FM.replace('title: "A"', 'title: "B"'))
        self.assertIn("frontmatter", self.kinds(self.freeze()))

    def test_image_files(self):
        # 両方の行を消したのに、ファイルが残っている。
        self.write_raw(SRC.replace('![](assets/a/a-01.png "https://x.example/1.png")\n', ""))
        self.assertIn("image_file", self.kinds(self.freeze()))
        # 行は残したのに、ファイルを消した。
        self.write_raw(SRC)
        (self.raw / "assets/a/a-01.png").unlink()
        self.assertIn("image_file", self.kinds(self.freeze()))


CLEAN = """# Title

The model uses `run(x)` and see [docs](https://x.example/d). The city of Greenwich is a place.

- item one
- item two ![i](assets/a/a-01.png "https://x.example/1.png")

> Quote text.
>
> ![q](assets/a/a-02.png "https://x.example/2.png")

| a | b |
|---|---|
| 1 | 2 |

```
print("hi")
```

![missing](https://x.example/3.png "https://x.example/3.png")（未取得）
"""

GOOD = """# 題名

モデルは `run(x)` を使い、[文書](https://x.example/d)を参照する。Greenwich の町は地名である。

- 項目 1
- 項目 2 ![i](assets/a/a-01.png "https://x.example/1.png")

  > Claude Sonnet 5.5 補足: 項目の中の図の説明である。

> 引用の文である。
>
> ![q](assets/a/a-02.png "https://x.example/2.png")
>
> > Claude Sonnet 5.5 補足: 引用の中の図の説明である。

| a | b |
|---|---|
| 1 | 2 |

```
print("hi")
```

![missing](https://x.example/3.png "https://x.example/3.png")（未取得）
"""

FM_T = FM.replace('translated_by: ""', 'translated_by: "Claude Sonnet 5.5"')


class CheckTest(RawCheckCase):
    def setUp(self):
        super().setUp()
        self.setup_fetch(CLEAN, images=["assets/a/a-01.png", "assets/a/a-02.png"])
        self.assertTrue(self.freeze()["ok"])

    def test_good_translation_passes(self):
        self.write_raw(GOOD, fm=FM_T)
        result = self.check()
        self.assertTrue(result["ok"], result["errors"])
        self.assertEqual(result["warnings"], [])

    def test_errors(self):
        # （名前、raw、frontmatter、出るはずの誤りの種類）
        cases = [
            ("translated_by", GOOD, FM, "translated_by"),
            ("caption", GOOD.replace("  > Claude Sonnet 5.5 補足: 項目の中の図の説明である。\n\n", ""), FM_T, "caption"),
            ("caption_name", GOOD.replace("> > Claude Sonnet 5.5", "> > Claude Haiku 5.5"), FM_T, "caption"),
            # 取得できなかった画像の補足は、原文の引用と見分けられないので、ブロックの数の違いとして止まる。
            ("caption_unavailable", GOOD + "\n> Claude Sonnet 5.5 補足: 見ていない図。\n", FM_T, "blocks"),
            ("links", GOOD.replace("[文書](https://x.example/d)", "文書"), FM_T, "links"),
            ("code_span", GOOD.replace("`run(x)`", "`run(y)`"), FM_T, "code_span"),
            ("code", GOOD.replace('print("hi")', 'print("やあ")'), FM_T, "code"),
            ("image", GOOD.replace("![q]", "![引用の図]"), FM_T, "image"),
            ("table", GOOD.replace("| 1 | 2 |", "| 1 | 2 |\n| 3 | 4 |"), FM_T, "blocks"),
            ("list", GOOD.replace("- 項目 1\n", ""), FM_T, "blocks"),
            ("quote_split", GOOD.replace("> 引用の文である。\n>\n", "> 引用の文である。\n\n"), FM_T, "blocks"),
        ]
        for name, body, fm, kind in cases:
            with self.subTest(name=name):
                self.write_raw(body, fm=fm)
                result = self.check()
                self.assertIn(kind, self.kinds(result), result["errors"])

    def test_warnings_and_controls(self):
        body = GOOD.replace("Greenwich の町は地名である。", "グリニッジの町は地名である。<> を使う。")
        self.write_raw(body, fm=FM_T)
        result = self.check()
        self.assertTrue(result["ok"], result["errors"])
        kinds = sorted({w["kind"] for w in result["warnings"]})
        self.assertEqual(kinds, ["missing_names", "new_tokens"])
        # 名前を文の先頭に移しただけなら、警告しない（対照）。
        self.write_raw(GOOD.replace("モデルは `run(x)` を使い、[文書](https://x.example/d)を参照する。Greenwich の町は地名である。",
                                    "Greenwich は地名である。モデルは `run(x)` を使い、[文書](https://x.example/d)を参照する。"),
                       fm=FM_T)
        self.assertEqual(self.check()["warnings"], [])

    def test_style_mix_warns(self):
        body = GOOD.replace("Greenwich の町は地名である。", "Greenwich の町は地名です。これは例です。")
        body = body.replace("引用の文である。", "引用の文である。次の文である。")
        self.write_raw(body, fm=FM_T)
        self.assertIn("style", {w["kind"] for w in self.check()["warnings"]})


class ReviewCounterexampleTest(RawCheckCase):
    """実装の 1 回目のレビュー（impl-review-1.md）の反例。どれも取得器が実際に出す形である。"""

    def freeze_with(self, src: str, out: str, images=()) -> dict:
        self.setup_fetch(src, images=images)
        self.write_raw(out)
        return self.freeze()

    def check_with(self, src: str, out: str, images=(), fm=FM_T) -> dict:
        self.setup_fetch(src, images=images)
        self.assertTrue(self.freeze()["ok"])
        self.write_raw(out, fm=fm)
        return self.check()

    def test_code_in_list_item_is_protected(self):
        src = "# A\n\n- item\n  ```\n  SELECT 1; -- rationale\n  ```\n"
        self.assertFalse(self.freeze_with(src, src.replace(" -- rationale", ""))["ok"])
        result = self.check_with(src, src.replace("item", "項目").replace(" -- rationale", ""))
        self.assertIn("code", self.kinds(result))

    def test_code_content_that_looks_like_a_prefix(self):
        src = "# A\n\n```\n- 1\n> - dangerous\n```\n"
        result = self.check_with(src, src.replace("- 1", "1"))
        self.assertIn("code", self.kinds(result))

    def test_link_with_escaped_bracket(self):
        src = "# A\n\nRead [a\\]b](https://x.example/safe).\n"
        self.assertFalse(self.freeze_with(src, src.replace("/safe", "/"))["ok"])

    def test_valid_deletions_are_not_mistaken_for_reordering(self):
        src = "# A\n\na\n\nb\n\nShare a\n"
        result = self.freeze_with(src, "# A\n\nb\n\na\n")
        self.assertTrue(result["ok"], result["errors"])

    def test_caption_on_list_continuation_image(self):
        src = "# A\n\n- item\n  ![x](assets/a/1.png)\n"
        out = "# A\n\n- 項目\n  ![x](assets/a/1.png)\n\n  > Claude Sonnet 5.5 補足: 図の説明である。\n"
        result = self.check_with(src, out, images=["assets/a/1.png"])
        self.assertTrue(result["ok"], result["errors"])

    def test_image_with_escaped_bracket_in_alt(self):
        src = "# A\n\n![a\\]b](assets/a/1.png)\n"
        self.assertTrue(self.freeze_with(src, src, images=["assets/a/1.png"])["ok"])
        out = src + "\n> Claude Sonnet 5.5 補足: 図の説明である。\n"
        self.write_raw(out, fm=FM_T)
        result = self.check()
        self.assertTrue(result["ok"], result["errors"])

    def test_nested_structure_changes(self):
        cases = [
            ("# A\n\n- Parent\n  - Child\n", "# A\n\n- 親\n- 子\n"),
            ("# A\n\n| a | b |\n|---|---|\n| 1 | 2 |\n", "# A\n\n| a | b |\n| あ | い |\n| 1 | 2 |\n"),
        ]
        for src, out in cases:
            with self.subTest(src=src):
                result = self.check_with(src, out)
                self.assertFalse(result["ok"])

    def test_two_captions_in_one_quote(self):
        src = "# A\n\n![x](assets/a/1.png)\n"
        out = src + "\n> Claude Sonnet 5.5 補足: 説明 1。\n> Other 補足: 説明 2。\n"
        result = self.check_with(src, out, images=["assets/a/1.png"])
        self.assertIn("caption", self.kinds(result))

    def test_image_syntax_inside_code_needs_no_caption(self):
        src = "# A\n\n```\n![x](assets/a/1.png)\n```\n\n![x](assets/a/1.png)\n"
        out = src + "\n> Claude Sonnet 5.5 補足: 図の説明である。\n"
        result = self.check_with(src, out, images=["assets/a/1.png"])
        self.assertTrue(result["ok"], result["errors"])

    def test_fetched_image_deleted_after_freeze(self):
        src = "# A\n\n![x](assets/a/1.png)\n"
        self.setup_fetch(src, images=["assets/a/1.png"])
        self.assertTrue(self.freeze()["ok"])
        (self.raw / "assets/a/1.png").unlink()
        self.write_raw(src, fm=FM_T)
        result = self.check()
        self.assertIn("image_file", self.kinds(result))
        self.assertIn("caption", self.kinds(result))

    def test_incomplete_work_dir_is_reported(self):
        self.setup_fetch("# A\n\nText.\n")
        (self.wd / "fetch.json").unlink()
        self.assertFalse(wiki_rawcheck.work_dir_complete(self.wiki, "a"))
        with self.assertRaises(FileNotFoundError):
            wiki_rawcheck.freeze(self.wiki, self.raw, "a")


class ReviewCounterexample2Test(RawCheckCase):
    """実装の 2 回目のレビュー（impl-review-2.md）の反例。"""

    def check_with(self, src: str, out: str, images=(), fm=FM_T, needs_translation=True) -> dict:
        self.setup_fetch(src, images=images, needs_translation=needs_translation)
        self.assertTrue(self.freeze()["ok"])
        self.write_raw(out, fm=fm)
        return self.check()

    def test_japanese_image_path(self):
        rel = "assets/日本語/日本語-01.png"
        src = f"# A\n\n![x]({rel} \"https://x.example/i.png\")\n"
        self.setup_fetch(src, images=[rel])
        self.assertTrue(self.freeze()["ok"], self.freeze()["errors"])
        out = src + "\n> Claude Sonnet 5.5 補足: 図の説明である。\n"
        self.write_raw(out, fm=FM_T)
        self.assertTrue(self.check()["ok"])
        # ファイルを消すと、補足を書いても誤りになる。
        (self.raw / rel).unlink()
        self.assertIn("image_file", self.kinds(self.check()))

    def test_caption_after_list_paragraph_with_tail(self):
        src = "# A\n\n- item\n  ![x](assets/a/1.png \"https://x.example/i.png\")\n  tail\n"
        out = ("# A\n\n- 項目\n  ![x](assets/a/1.png \"https://x.example/i.png\")\n  続き\n\n"
               "  > Claude Sonnet 5.5 補足: 図の説明である。\n")
        result = self.check_with(src, out, images=["assets/a/1.png"])
        self.assertTrue(result["ok"], result["errors"])

    def test_nested_second_caption_is_rejected(self):
        src = "# A\n\n![x](assets/a/1.png)\n"
        for extra in ("> Claude Sonnet 5.5 補足: 説明 1。\n>\n> > Other 補足: 説明 2。\n",
                      "> Claude Sonnet 5.5 補足: 説明 1。\n>\n> - Other 補足: 説明 2。\n"):
            with self.subTest(extra=extra):
                result = self.check_with(src, src + "\n" + extra, images=["assets/a/1.png"])
                self.assertIn("caption", self.kinds(result))

    def test_original_caption_like_quote_is_kept(self):
        src = "# A\n\n![x](assets/a/1.png)\n\n> Alice 補足: 図の前提。\n"
        out = "# A\n\n![x](assets/a/1.png)\n\n> Claude Sonnet 5.5 補足: 図の説明である。\n\n> Alice 補足: 図の前提。\n"
        result = self.check_with(src, out, images=["assets/a/1.png"], fm=FM, needs_translation=False)
        self.assertTrue(result["ok"], result["errors"])

    def test_link_inside_strong_can_be_removed(self):
        src = "# A\n\n**Body text. [Share](https://x.example/share)**\n"
        self.setup_fetch(src)
        self.write_raw("# A\n\n**Body text.**\n")
        result = self.freeze()
        self.assertTrue(result["ok"], result["errors"])

    def test_untranslated_markup_and_reference_changes(self):
        src = "# A\n\n**hello** world.\n"
        result = self.check_with(src, "# A\n\n__hello__ world.\n", fm=FM, needs_translation=False)
        self.assertIn("text", self.kinds(result))
        self.setup_fetch(src)
        self.write_raw(src + "\n[x]: https://evil.example/\n")
        self.assertFalse(self.freeze()["ok"])

    def test_bad_slug_is_refused_before_removing(self):
        with self.assertRaises(ValueError):
            wiki_rawcheck.remove_work_dir(self.wiki, "../..")
        argv = ["--wiki", str(self.wiki), "--raw-root", str(self.raw), "--slug", "../..", "--finish"]
        with contextlib.redirect_stderr(io.StringIO()), contextlib.redirect_stdout(io.StringIO()):
            self.assertEqual(wiki_rawcheck.main(["check", *argv]), 1)
        self.assertTrue(self.wiki.is_dir())

    def test_corrupt_fetch_json_is_incomplete(self):
        self.setup_fetch("# A\n\nText.\n")
        (self.wd / "fetch.json").write_bytes(b"{")
        self.assertFalse(wiki_rawcheck.work_dir_complete(self.wiki, "a"))


class ReviewCounterexample3Test(RawCheckCase):
    """実装の 3 回目のレビュー（impl-review-3.md）の反例。"""

    def check_with(self, src: str, out: str, images=(), fm=FM, needs_translation=False) -> dict:
        self.setup_fetch(src, images=images, needs_translation=needs_translation)
        result = self.freeze()
        self.assertTrue(result["ok"], result["errors"])
        self.write_raw(out, fm=fm)
        return self.check()

    def test_percent_in_image_path(self):
        rel = "assets/a%20b/a%20b-01.png"
        src = f"# A\n\n![x]({rel} \"https://x.example/i.png\")\n"
        out = src + "\n> Claude Sonnet 5.5 補足: 図の説明である。\n"
        self.assertTrue(self.check_with(src, out, images=[rel])["ok"])
        (self.raw / rel).unlink()
        self.write_raw(src)
        self.assertIn("image_file", self.kinds(self.freeze()))

    def test_untranslated_caption_inside_quote_and_list(self):
        cases = [
            ("# A\n\n> 前書きである。\n>\n> ![](assets/a/a-01.png \"https://x.example/i.png\")\n>\n> 後書きである。\n",
             "# A\n\n> 前書きである。\n>\n> ![](assets/a/a-01.png \"https://x.example/i.png\")\n>\n"
             "> > Claude Sonnet 5.5 補足: 図である。\n>\n> 後書きである。\n"),
            ("# A\n\n- 項目 1 ![](assets/a/a-01.png \"https://x.example/i.png\")\n- 項目 2\n",
             "# A\n\n- 項目 1 ![](assets/a/a-01.png \"https://x.example/i.png\")\n\n"
             "  > Claude Sonnet 5.5 補足: 図である。\n- 項目 2\n"),
        ]
        for src, out in cases:
            with self.subTest(src=src):
                result = self.check_with(src, out, images=["assets/a/a-01.png"])
                self.assertTrue(result["ok"], result["errors"])

    def test_reference_definitions_ignore_line_numbers(self):
        src = "# A\n\nnoise\n\n[x]: https://x.example/path\n\nBody [x].\n"
        self.setup_fetch(src)
        self.write_raw(src.replace("noise\n\n", ""))
        self.assertTrue(self.freeze()["ok"])
        src2 = "# A\n\n![x](assets/a/a-01.png)\n\n[r]: https://x.example/r\n\nSee [r].\n"
        out2 = src2.replace("![x](assets/a/a-01.png)\n", "![x](assets/a/a-01.png)\n\n> Claude Sonnet 5.5 補足: 図である。\n")
        self.assertTrue(self.check_with(src2, out2, images=["assets/a/a-01.png"])["ok"])

    def test_duplicate_reference_definition_is_rejected(self):
        src = "# A\n\nSee [x].\n\n[x]: https://x.example/path\n"
        self.setup_fetch(src)
        self.write_raw(src + "\n[x]: https://evil.example/path\n")
        self.assertFalse(self.freeze()["ok"])
        result = self.check_with(src, src + "\n[x]: https://evil.example/path\n")
        self.assertIn("references", self.kinds(result))

    def test_markup_rewrites_are_rejected_in_freeze(self):
        src = "# A\n\n## Section\n\nText.\n\n```\ncode\n```\n"
        for out in (src.replace("## Section", "Section\n-------"), src.replace("```", "~~~")):
            with self.subTest(out=out):
                self.setup_fetch(src)
                self.write_raw(out)
                self.assertFalse(self.freeze()["ok"])


class ReviewCounterexample4Test(RawCheckCase):
    """実装の 4 回目のレビュー（impl-review-4.md）の反例。"""

    TABLE = "# A\n\n| A | B |\n|---|---|\n| 1 | 2 |\n"

    def test_extra_table_cell_is_rejected(self):
        self.setup_fetch(self.TABLE)
        self.write_raw(self.TABLE.replace("| 1 | 2 |", "| 1 | 2 | NEW RAW PAYLOAD |"))
        self.assertFalse(self.freeze()["ok"])
        self.setup_fetch(self.TABLE)
        self.assertTrue(self.freeze()["ok"])
        self.write_raw(self.TABLE.replace("| 1 | 2 |", "| 1 | 2 | NEW RAW PAYLOAD |"), fm=FM_T)
        self.assertIn("table", self.kinds(self.check()))

    def test_paragraph_line_that_looks_like_a_reference(self):
        src = "# A\n\nReferences:  \n[x]: active\n"
        self.setup_fetch(src)
        self.assertTrue(self.freeze()["ok"])
        self.write_raw("# A\n\n参照:  \n[x]: 有効\n", fm=FM_T)
        result = self.check()
        self.assertTrue(result["ok"], result["errors"])

    def test_first_ordered_item_can_be_removed(self):
        src = "# A\n\n1. Share\n2. Body text.\n"
        self.setup_fetch(src)
        self.write_raw("# A\n\n2. Body text.\n")
        result = self.freeze()
        self.assertTrue(result["ok"], result["errors"])

    def test_duplicate_translated_by_is_rejected(self):
        self.setup_fetch("# A\n\nText.\n")
        self.assertTrue(self.freeze()["ok"])
        fm = FM.replace('translated_by: ""', 'translated_by: "Model"\ntranslated_by: ""')
        self.write_raw("# A\n\n文。\n", fm=fm)
        self.assertIn("translated_by", self.kinds(self.check()))


class ReviewCounterexample5Test(RawCheckCase):
    """実装の 5 回目のレビュー（impl-review-5.md）の反例。"""

    def test_image_inside_caption_is_rejected(self):
        src = ('# A\n\n![](assets/a/a-01.png "https://x.example/i.png")\n\n'
               '![](assets/a/a-02.png "https://x.example/j.png")\n')
        self.setup_fetch(src, images=["assets/a/a-01.png", "assets/a/a-02.png"])
        out = src.split("\n\n![](assets/a/a-02.png")[0] + "\n"
        (self.raw / "assets/a/a-02.png").unlink()
        self.write_raw(out)
        self.assertTrue(self.freeze()["ok"])
        self.write_raw(out + '\n> Claude Sonnet 5.5 補足: 説明 ![](assets/a/a-02.png "https://x.example/j.png")\n', fm=FM_T)
        self.assertIn("caption", self.kinds(self.check()))

    def test_deep_quotes_are_fast(self):
        """入れ子の深い引用でも、照らし直しで呼び出しが指数的に増えない。"""
        depth = 20
        noise = "> " * depth + "noise\n"
        body = "> " * depth + "Body.\n"
        src = "# A\n\n" + noise + "\n" + body
        self.setup_fetch(src)
        self.write_raw("# A\n\n" + body)
        calls = []
        original = wiki_rawcheck.derivable

        def counting(*a, **k):
            calls.append(1)
            return original(*a, **k)

        with mock.patch.object(wiki_rawcheck, "derivable", counting):
            result = self.freeze()
        self.assertTrue(result["ok"], result["errors"])
        self.assertLess(len(calls), 2000)

    def test_code_only_caption_is_not_empty(self):
        src = "# A\n\n![x](assets/a/1.png)\n"
        self.setup_fetch(src, images=["assets/a/1.png"])
        self.assertTrue(self.freeze()["ok"])
        self.write_raw(src + "\n> Claude Sonnet 5.5 補足: `foo()`\n", fm=FM_T)
        result = self.check()
        self.assertTrue(result["ok"], result["errors"])

    def test_link_title_must_not_be_added(self):
        src = "# A\n\nSee [docs](https://x.example/).\n"
        self.setup_fetch(src)
        self.assertTrue(self.freeze()["ok"])
        self.write_raw("# A\n\n[文書](https://x.example/ \"NEW RAW PAYLOAD\")を見る。\n", fm=FM_T)
        self.assertIn("links", self.kinds(self.check()))


class ReviewCounterexample6Test(RawCheckCase):
    """実装の 6 回目のレビュー（impl-review-6.md）の反例。"""

    def test_hidden_cells_after_removing_a_header_column(self):
        src = "# A\n\n| A | B |\n|---|---|\n| 1 | `SELECT 1;` [safe](https://safe.example/) |\n"
        self.setup_fetch(src)
        self.write_raw("# A\n\n| A |\n|---|\n| 1 | `SELECT 1;` [safe](https://safe.example/) |\n")
        self.assertIn("table", self.kinds(self.freeze()))
        # 列は、見出しとすべての行から消しても止まる（7 回目のレビューで、列を消せないことにした）。
        self.write_raw("# A\n\n| A |\n|---|\n| 1 |\n")
        self.assertIn("table", self.kinds(self.freeze()))
        # 行を丸ごと消すのは通る（対照）。
        src2 = "# A\n\n| A | B |\n|---|---|\n| 1 | 2 |\n| Share | Tweet |\n"
        self.setup_fetch(src2)
        self.write_raw("# A\n\n| A | B |\n|---|---|\n| 1 | 2 |\n")
        result = self.freeze()
        self.assertTrue(result["ok"], result["errors"])

    def test_second_caption_with_code_name(self):
        src = "# A\n\n![x](assets/a/1.png)\n"
        self.setup_fetch(src, images=["assets/a/1.png"])
        self.assertTrue(self.freeze()["ok"])
        self.write_raw(src + "\n> Claude Sonnet 5.5 補足: 一つ目の説明。\n>\n> `Other` 補足: 二つ目の説明。\n", fm=FM_T)
        self.assertIn("caption", self.kinds(self.check()))


class ReviewCounterexample7Test(RawCheckCase):
    """実装の 7 回目のレビュー（impl-review-7.md）の反例。"""

    def test_table_inside_list_cannot_hide_cells(self):
        src = "# A\n\n- | A | B |\n  |---|---|\n  | 1 | `SELECT 1;` [safe](https://safe.example/) |\n"
        self.setup_fetch(src)
        self.write_raw("# A\n\n- | A |\n  |---|\n  | 1 | `SELECT 1;` [safe](https://safe.example/) |\n")
        self.assertIn("table", self.kinds(self.freeze()))
        # 訳と補足の段で、表のセルの区切りを書き足しても止まる。
        self.setup_fetch(src)
        self.assertTrue(self.freeze()["ok"])
        self.write_raw("# A\n\n- | A | B |\n  |---|---|\n  | 1 | `SELECT 1;` [safe](https://safe.example/) | 足した |\n",
                       fm=FM_T)
        self.assertIn("table", self.kinds(self.check()))

    def test_entity_in_image_path(self):
        rel = "assets/a&amp;b/a&amp;b-01.png"
        src = f"# A\n\nBody.\n\n![]({rel} \"https://site.example/i.png\")\n"
        self.setup_fetch(src, images=[rel])
        result = self.freeze()
        self.assertTrue(result["ok"], result["errors"])
        self.write_raw(src.replace("Body.", "本文。"), fm=FM_T)
        self.assertIn("caption", self.kinds(self.check()))
        (self.raw / rel).unlink()
        self.write_raw(src)
        self.assertIn("image_file", self.kinds(self.freeze()))

    def test_failed_freeze_leaves_no_cleaned(self):
        src = "# A\n\nOpening paragraph.\n\n```\nSELECT 1;\n```\n"
        self.setup_fetch(src)
        real_replace = os.replace

        def failing(a, b):
            if str(b).endswith("cleaned.md"):
                raise OSError("書けない")
            return real_replace(a, b)

        with mock.patch.object(wiki_rawcheck.os, "replace", failing):
            with self.assertRaises(OSError):
                wiki_rawcheck.freeze(self.wiki, self.raw, "a")
        self.assertFalse((self.wd / "cleaned.md").exists())


def rendered_text(body: str) -> str:
    """lint と閲覧のパーサー（wiki_pages.new_parser()）が読む文字（インラインの文字とコード、リンク先、
    コードブロックの中身）。画面に出る範囲である。検査の木（表の規則を差し替えたもの）とは別に作る。"""
    import wiki_pages
    parts = []
    for tok in wiki_pages.new_parser().parse(body):
        if tok.type in ("fence", "code_block"):
            parts.append(tok.content)
        for child in tok.children or []:
            if child.type in ("text", "code_inline"):
                parts.append(child.content)
            elif child.type == "link_open":
                parts.append(child.attrGet("href") or "")
    return "\n".join(parts)


class ReviewCounterexample8Test(RawCheckCase):
    """実装の 8 回目のレビュー（impl-review-8.md）の反例。"""

    TABLE = "# A\n\n| A | B |\n|---|---|\n| 1 | `SELECT 1;` [safe](https://safe.example/) |\n"

    def test_surplus_cell_without_leading_pipe_is_rejected_in_check(self):
        self.setup_fetch(self.TABLE)
        self.assertTrue(self.freeze()["ok"])
        row = "| 1 | `SELECT 1;` [safe](https://safe.example/) |"
        evil = "1 | `SELECT 1;` [safe](https://safe.example/) | `DROP TABLE users;` [evil](https://evil.example/) |"
        self.write_raw(self.TABLE.replace(row, evil), fm=FM_T)
        self.assertIn("table", self.kinds(self.check()))

    def test_column_count_is_checked_on_the_same_table(self):
        src = "# A\n\n| Noise |\n|---|\n| noise |\n\n" + self.TABLE.removeprefix("# A\n\n")
        self.setup_fetch(src)
        self.write_raw("# A\n\n| A |\n|---|\n| 1 | `SELECT 1;` [safe](https://safe.example/) |\n")
        self.assertIn("table", self.kinds(self.freeze()))
        # 1 つ目の表を丸ごと消すのは通る（対照）。
        self.write_raw(self.TABLE)
        result = self.freeze()
        self.assertTrue(result["ok"], result["errors"])

    def test_table_rows_have_their_real_cells(self):
        """検査の木の表の行は、本文の行に実際にあるセルだけを持つ（補った空のセルを除き、捨てたセルを足す）。
        どの行も見出しと同じセルの数なら、トークンの並びは lint のパーサーと同じ。"""
        import wiki_pages
        plain = wiki_pages.new_parser()
        for body in (self.TABLE, "- | A | B |\n  |---|---|\n  | 1 | 2 |\n", "Para\n| A |\n|---|\n| 1 |\n"):
            with self.subTest(body=body):
                self.assertEqual([(t.type, t.content, t.map, t.level) for t in wiki_rawcheck._PARSER.parse(body)],
                                 [(t.type, t.content, t.map, t.level) for t in plain.parse(body)])
        bodies = {
            "- | A | B |\n  |---|---|\n  | 1 | 2 | `x` [l](https://l.example/) |\n": [["A", "B"], ["1", "2", "x l"]],
            "> | A |\n> |---|\n> | 1 \\| 2 |\n> | 1 | 2 |\n": [["A"], ["1 | 2"], ["1", "2"]],
            "| A | B | C |\n|---|---|---|\n1 | 2\n| |\n|\n": [["A", "B", "C"], ["1", "2"], [""], []],
        }
        for body, rows in bodies.items():
            with self.subTest(body=body):
                tree = wiki_rawcheck.parse_tree(body)
                got = [[wiki_rawcheck.inline_text(c.inline, code=True) for c in tr.children]
                       for tr in wiki_rawcheck.walk(tree) if tr.type == "tr"]
                self.assertEqual(got, rows)
        # 足したセルのリンクも、インラインの解析を通っている。
        tree = wiki_rawcheck.parse_tree("| A |\n|---|\n| 1 | [l](https://l.example/) |\n")
        links = [link for n in wiki_rawcheck.walk(tree) for link in wiki_rawcheck.links_of(n.inline)]
        self.assertEqual(links, [("https://l.example/", "")])

    def test_short_row_is_rejected_in_check(self):
        src = "# A\n\n| A | B | C |\n|---|---|---|\n| 1 | 2 | 3 |\n"
        self.setup_fetch(src)
        self.assertTrue(self.freeze()["ok"])
        self.write_raw(src.replace("| 1 | 2 | 3 |", "| 2 | 3 |"), fm=FM_T)
        self.assertIn("table", self.kinds(self.check()))
        self.write_raw(src.replace("| 1 | 2 | 3 |", "| 2 | 3 |"))
        self.assertIn("table", self.kinds(self.freeze()))

    def test_cells_cannot_shift_to_another_column(self):
        self.setup_fetch("# A\n\n| A | B |\n|---|---|\n| 1 | `x()` |\n")
        self.write_raw("# A\n\n| A | B |\n|---|---|\n| `x()` |\n")
        self.assertIn("table", self.kinds(self.freeze()))

    def test_noise_between_lists_can_be_removed(self):
        for src, out, translated in (
                ("# A\n\n- Body one.\n\nShare\n\n- Body two.\n", "# A\n\n- Body one.\n\n- Body two.\n",
                 "# A\n\n- 本文一。\n\n- 本文二。\n"),
                ("# A\n\n1. One.\n\n## Related\n\n1. Two.\n", "# A\n\n1. One.\n\n1. Two.\n",
                 "# A\n\n1. 一。\n\n1. 二。\n")):
            with self.subTest(src=src):
                self.setup_fetch(src)
                self.write_raw(out)
                result = self.freeze()
                self.assertTrue(result["ok"], result["errors"])
                self.write_raw(translated, fm=FM_T)
                result = self.check()
                self.assertTrue(result["ok"], result["errors"])

    def test_list_items_keep_their_structure(self):
        # 記号の違うリストは、間を消してもつながらない（2 つのリストのまま）。通る（対照）。
        self.setup_fetch("# A\n\n- a\n\nShare\n\n* b\n")
        self.write_raw("# A\n\n- a\n\n* b\n")
        result = self.freeze()
        self.assertTrue(result["ok"], result["errors"])
        # 項目の中の段落を、字下げを消してリストの外に出すのは、入れ子の変更なので止める。
        self.setup_fetch("# A\n\n- a\n\n  more\n")
        self.write_raw("# A\n\n- a\n\nmore\n")
        self.assertIn("edit", self.kinds(self.freeze()))
        # 空の行を消して段落をつなげるのは止め、空の行を残すように伝える。
        self.setup_fetch("# A\n\nOne.\n\nTwo.\n")
        self.write_raw("# A\n\nOne.\nTwo.\n")
        result = self.freeze()
        self.assertIn("空の行", next(e["message"] for e in result["errors"] if e["kind"] == "edit"))

    def run_main(self, *args) -> tuple[int, dict]:
        argv = ["--wiki", str(self.wiki), "--raw-root", str(self.raw), "--slug", "a", "--json"]
        out = io.StringIO()
        with contextlib.redirect_stdout(out), contextlib.redirect_stderr(io.StringIO()):
            code = wiki_rawcheck.main([args[0], *argv, *args[1:]])
        return code, (json.loads(out.getvalue()) if out.getvalue() else {})

    def test_finish_keeps_work_dir_while_warnings_remain(self):
        src = "# A\n\nThe town of Greenwich is old.\n"
        self.setup_fetch(src)
        self.assertEqual(self.run_main("freeze")[0], 0)
        self.write_raw("# A\n\nグリニッジの町は古い。\n", fm=FM_T)
        code, result = self.run_main("check", "--finish")
        self.assertEqual(code, 0)
        self.assertEqual(result["work_dir_kept"], "warnings")
        self.assertTrue((self.wd / "cleaned.md").is_file())
        # 警告を直して再検査できる。警告がなくなれば消す。
        self.write_raw("# A\n\nGreenwich の町は古い。\n", fm=FM_T)
        code, result = self.run_main("check", "--finish")
        self.assertEqual(code, 0)
        self.assertTrue(result["work_dir_removed"])
        self.assertFalse(self.wd.exists())

    def test_accept_warnings_removes_work_dir(self):
        self.setup_fetch("# A\n\nThe town of Greenwich is old.\n")
        self.assertEqual(self.run_main("freeze")[0], 0)
        self.write_raw("# A\n\nグリニッジの町は古い。\n", fm=FM_T)
        self.assertEqual(self.run_main("check", "--accept-warnings")[0], 1)  # --finish なしでは付けられない
        code, result = self.run_main("check", "--finish", "--accept-warnings")
        self.assertEqual(code, 0)
        self.assertTrue(result["warnings"])
        self.assertFalse(self.wd.exists())

    def test_error_lines_are_file_lines(self):
        """誤りと警告の行番号は、raw のファイルの行番号（frontmatter を含めて数える）。"""
        self.setup_fetch("# A\n\nAlpha.\n\nThe town of Greenwich.\n")
        self.write_raw("# A\n\nAlpha.\n\nThe city of Greenwich.\n")  # 書き換え
        error = self.freeze()["errors"][0]
        lines = (self.raw / "a.md").read_text(encoding="utf-8").split("\n")
        self.assertEqual(lines[error["line"] - 1], "The city of Greenwich.")
        self.setup_fetch("# A\n\nAlpha.\n\nThe town of Greenwich.\n")
        self.assertTrue(self.freeze()["ok"])
        self.write_raw("# A\n\nアルファ。\n\nグリニッジの町。\n", fm=FM_T)
        warning = next(w for w in self.check()["warnings"] if w["kind"] == "missing_names")
        lines = (self.raw / "a.md").read_text(encoding="utf-8").split("\n")
        self.assertEqual(lines[warning["line"] - 1], "グリニッジの町。")

    def test_freeze_lists_only_remaining_images(self):
        src = ('# A\n\nIntro.\n\n![](assets/a/a-01.png "https://x.example/1.png")\n\n'
               '![](assets/a/a-02.png "https://x.example/2.png")\n')
        self.setup_fetch(src, images=["assets/a/a-01.png", "assets/a/a-02.png"])
        (self.raw / "assets/a/a-01.png").unlink()
        self.write_raw('# A\n\nIntro.\n\n![](assets/a/a-02.png "https://x.example/2.png")\n')
        result = self.freeze()
        self.assertTrue(result["ok"], result["errors"])
        self.assertEqual([img["path"] for img in result["images"]], ["assets/a/a-02.png"])
        lines = (self.raw / "a.md").read_text(encoding="utf-8").split("\n")
        self.assertTrue(lines[result["images"][0]["line"] - 1].startswith("![](assets/a/a-02.png"))


class FetchCounterexample8Test(FetchCase):
    """実装の 8 回目のレビューの反例のうち、取得器が書いた raw から始めるもの。"""

    TABLE = ('<table><tr><th>A</th><th>B</th></tr><tr><td>1</td><td>Prefix | <code>SELECT 1;</code>\n'
             '<a href="https://safe.example/">safe</a></td></tr></table>')
    ESCAPED = "Prefix \\| `SELECT 1;`"

    def fetch_table(self) -> str:
        _, text, _ = self.build(html_page(f"<p>{LONG}</p>" + self.TABLE))
        self.assertIn(self.ESCAPED, text)
        return text

    def write_raw(self, text: str):
        (self.raw / "page.md").write_text(text, encoding="utf-8", newline="\n")

    def test_deleting_escape_backslash_in_a_cell_is_rejected(self):
        text = self.fetch_table()
        self.write_raw(text.replace(self.ESCAPED, "Prefix | `SELECT 1;`"))
        code, result = wiki_rawcheck.freeze(self.wiki, self.raw, "page")
        self.assertEqual(code, 1)
        self.assertIn("table", {e["kind"] for e in result["errors"]})
        # 訳の段で \ を消し、見えなくなったセルを書き換えても止まる。
        self.write_raw(text)
        self.assertEqual(wiki_rawcheck.freeze(self.wiki, self.raw, "page")[0], 0)
        out = text.replace('translated_by: ""', 'translated_by: "Claude Sonnet 5.5"').replace(LONG.strip(), "本文の訳。")
        out = out.replace(self.ESCAPED + " [safe](https://safe.example/)",
                          "Prefix | `DROP TABLE users;` [safe](https://evil.example/)")
        self.write_raw(out)
        code, result = wiki_rawcheck.check(self.wiki, self.raw, "page", None, None)
        self.assertEqual(code, 1)
        self.assertIn("table", {e["kind"] for e in result["errors"]})

    def test_single_character_edits_never_hide_content(self):
        """表の 1 文字を消すか | を 1 つ足した raw が検査を通るなら、表のどの行も見出しと同じセルの数で、
        コードとリンク先は画面に出る（lint と閲覧のパーサーで読む）。データの行のセルの区切りを消せば止まる。"""
        text = self.fetch_table()
        start = text.index("| A | B |")
        targets = ("SELECT 1;", "https://safe.example/")
        translated = text.replace('translated_by: ""', 'translated_by: "Claude Sonnet 5.5"') \
            .replace(LONG.strip(), "本文の訳。")
        t_start = translated.index("| A | B |")
        row_start = translated.index("| 1 | Prefix")
        row_end = translated.index("\n", row_start)
        separators = {k for k in range(row_start + 1, row_end - 1)
                      if translated[k] == "|" and translated[k - 1] != "\\"}
        self.assertEqual(len(separators), 1)
        table_rule = wiki_rawcheck._TABLE_RULE

        def cell_counts(body: str) -> list[int]:
            """lint のパーサーが表と読んだ行の、セルの数（見出しと各データ行。区切りの行は除く）。"""
            import wiki_pages
            table = next(t for t in wiki_pages.new_parser().parse(body) if t.type == "table_open")
            lines = body.split("\n")[table.map[0]:table.map[1]]
            counts = []
            for line in lines[:1] + lines[2:]:
                cells = table_rule.escapedSplit(line.strip())
                if cells and cells[0] == "":
                    cells.pop(0)
                if cells and cells[-1] == "":
                    cells.pop()
                counts.append(len(cells))
            return counts

        edits = [("freeze", None, text[:i] + text[i + 1:]) for i in range(start, len(text))]
        edits += [("check", i, translated[:i] + translated[i + 1:]) for i in range(t_start, len(translated))]
        edits += [("check", None, translated[:i] + "|" + translated[i:]) for i in range(t_start, len(translated))]
        passed = 0
        # 取り直さずに raw だけを書き換える（freeze はいつも取得の写しの fetched.md と照らす）。取り直しは raw を
        # 名前の変更で置き換えるので、何百回もくり返すと、Windows でほかのプロセスがファイルを開いていて失敗しうる。
        baseline_frozen = False
        for stage, deleted, out in edits:
            if stage == "freeze":
                self.write_raw(out)
                code, _ = wiki_rawcheck.freeze(self.wiki, self.raw, "page")
            else:
                if not baseline_frozen:
                    # 訳の段の基準は、手を入れていない取得の内容（通った削除の内容ではない）。
                    self.write_raw(text)
                    self.assertEqual(wiki_rawcheck.freeze(self.wiki, self.raw, "page")[0], 0)
                    baseline_frozen = True
                self.write_raw(out)
                code, _ = wiki_rawcheck.check(self.wiki, self.raw, "page", None, None)
            if deleted in separators:
                self.assertEqual(code, 1, f"セルの区切りを消した raw が通った: {out[start - 10:]}")
            if code != 0:
                continue
            passed += 1
            body = wiki_rawcheck.split_frontmatter(out)[1]
            self.assertEqual(set(cell_counts(body)), {2}, f"{stage}: {out[start - 10:]}")
            seen = rendered_text(body)
            for target in targets:
                if target in body:
                    self.assertIn(target, seen, f"{stage}: {out[start - 10:]}")
        self.assertGreater(passed, 0)  # 通る編集（セルの中の文字の削除など）も照らしている

    def test_table_from_lines_of_a_paragraph(self):
        """<br> で区切った段落の行が表に読めるとき（取得器は文の中の Markdown の記法を外さない）、見出しより多い
        セルも検査の木にあり、手を入れていない raw は通り、訳の段でそのセルを変えれば止まる。"""
        html = html_page(f"<p>{LONG}</p><p>a | b<br>--- | ---<br>1 | 2 | <code>SELECT 1;</code></p>")
        _, text, _ = self.build(html)
        self.assertIn("1 | 2 | `SELECT 1;`", text)
        code, result = wiki_rawcheck.freeze(self.wiki, self.raw, "page")
        self.assertEqual(code, 0, result["errors"])
        base = text.replace('translated_by: ""', 'translated_by: "Claude Sonnet 5.5"').replace(LONG.strip(), "本文の訳。")
        for changed, kind in (("1 | 2 | `DROP TABLE users;`", "code_span"), ("1 | 2", "table")):
            with self.subTest(changed=changed):
                self.write_raw(base.replace("1 | 2 | `SELECT 1;`", changed))
                code, result = wiki_rawcheck.check(self.wiki, self.raw, "page", None, None)
                self.assertEqual(code, 1)
                self.assertIn(kind, {e["kind"] for e in result["errors"]})
        self.write_raw(base)
        code, result = wiki_rawcheck.check(self.wiki, self.raw, "page", None, None)
        self.assertEqual(code, 0, result["errors"])

    def test_noise_between_lists_from_the_fetcher(self):
        _, text, _ = self.build(html_page(f"<p>{LONG}</p>"
                                          "<ul><li>Body one.</li></ul><p>Share</p><ul><li>Body two.</li></ul>"))
        self.assertIn("- Body one.\n\nShare\n\n- Body two.", text)
        self.write_raw(text.replace("Share\n\n", ""))
        code, result = wiki_rawcheck.freeze(self.wiki, self.raw, "page")
        self.assertEqual(code, 0, result["errors"])

    def test_work_dir_of_another_fetch_is_not_resumed(self):
        """--force で写しを書いたあとに raw を書けずに止まると、前の raw が残る。写しがそろった印は raw のあとに
        置くので、写しはそろわず、途中から続けられない（9 回目のレビューで、印を置く順に改めた）。"""
        page_a = html_page(f"<p>{LONG}</p>")
        page_b = html_page(f"<p>{LONG} Changed.</p>")
        self.build(page_a)
        stub = FetchStub(page_b)
        with mock.patch.object(wiki_fetch, "fetch", stub), \
                mock.patch.object(wiki_fetch, "is_private_host", lambda host: False), \
                mock.patch.object(wiki_fetch, "write_outputs", side_effect=OSError("書けない")):
            with self.assertRaises(OSError):
                wiki_fetch.build(self.args(force=True))
        self.assertFalse(wiki_rawcheck.work_dir_complete(self.wiki, "page"))
        stub = FetchStub(page_a)
        with mock.patch.object(wiki_fetch, "fetch", stub), \
                mock.patch.object(wiki_fetch, "is_private_host", lambda host: False):
            code, result = wiki_fetch.build(self.args())
        self.assertTrue(result["unchanged"])
        self.assertFalse(result["work_dir"])

    def test_unchanged_after_freeze_returns_remaining_images(self):
        html = html_page(f'<p>{LONG}</p><img src="i.png" width="300" height="200">'
                         f'<p>{LONG}</p><img src="j.png" width="300" height="200">')
        result, text, _ = self.build(html)
        first, second = (img["path"] for img in result["images"])
        line = next(x for x in text.split("\n") if first in x)
        self.write_raw(text.replace(line + "\n\n", ""))
        (self.raw / first).unlink()
        code, frozen = wiki_rawcheck.freeze(self.wiki, self.raw, "page")
        self.assertEqual(code, 0, frozen["errors"])
        self.assertEqual([img["path"] for img in frozen["images"]], [second])
        stub = FetchStub(html)
        with mock.patch.object(wiki_fetch, "fetch", stub), \
                mock.patch.object(wiki_fetch, "is_private_host", lambda host: False):
            code, again = wiki_fetch.build(self.args())
        self.assertEqual(again["work_stage"], "frozen")
        self.assertEqual([img["path"] for img in again["images"]], [second])


class ReviewCounterexample9Test(RawCheckCase):
    """実装の 9 回目のレビュー（impl-review-9.md）の指摘。"""

    def test_error_in_table_cell_has_line_and_code(self):
        src = "# A\n\n| A | B |\n|---|---|\n| 1 | `SELECT 1;` [safe](https://safe.example/) |\n"
        self.setup_fetch(src)
        self.assertTrue(self.freeze()["ok"])
        self.write_raw(src.replace("SELECT 1;", "DROP TABLE users;"), fm=FM_T)
        error = next(e for e in self.check()["errors"] if e["kind"] == "code_span")
        lines = (self.raw / "a.md").read_text(encoding="utf-8").split("\n")
        self.assertTrue(lines[error["line"] - 1].startswith("| 1 |"))
        self.assertIn("SELECT 1;", error["source"])
        self.assertIn("DROP TABLE users;", error["raw"])

    def test_ordered_item_number_is_checked(self):
        src = "# A\n\n1. One.\n2. Two.\n"
        self.setup_fetch(src)
        self.assertTrue(self.freeze()["ok"])
        self.write_raw("# A\n\n1. 一。\n999. 二。\n", fm=FM_T)
        self.assertIn("structure", self.kinds(self.check()))
        self.write_raw("# A\n\n1. 一。\n2. 二。\n", fm=FM_T)
        result = self.check()
        self.assertTrue(result["ok"], result["errors"])


class FetchCounterexample9Test(FetchCase):
    """実装の 9 回目のレビューの指摘のうち、取得器が書いた raw から始めるもの。"""

    def write_raw(self, text: str):
        (self.raw / "page.md").write_text(text, encoding="utf-8", newline="\n")

    def test_raw_with_other_frontmatter_is_not_resumed(self):
        """写しがそろっていても、raw の frontmatter が写しと違えば（書き換えた、別の版に戻した）、途中から続けない。"""
        html = html_page(f"<p>{LONG}</p>")
        _, text, _ = self.build(html)
        self.assertTrue(wiki_rawcheck.work_dir_complete(self.wiki, "page"))
        self.write_raw(text.replace("fetched_at: ", "fetched_at: 2000-01-01T00:00:00+09:00\nold_fetched_at: ", 1))
        stub = FetchStub(html)
        with mock.patch.object(wiki_fetch, "fetch", stub), \
                mock.patch.object(wiki_fetch, "is_private_host", lambda host: False):
            code, result = wiki_fetch.build(self.args())
        self.assertTrue(result["unchanged"])
        self.assertFalse(result["work_dir"])

    def test_remaining_images_keep_their_own_alt(self):
        html = html_page(f'<p>{LONG}</p><img src="i.png" alt="Before treatment" width="300" height="200">'
                         f'<p>Middle.</p><img src="i.png" alt="After treatment" width="300" height="200">')
        result, text, _ = self.build(html)
        self.assertEqual([img["alt"] for img in result["images"]], ["Before treatment", "After treatment"])
        code, frozen = wiki_rawcheck.freeze(self.wiki, self.raw, "page")
        self.assertEqual(code, 0, frozen["errors"])
        self.assertEqual([img["alt"] for img in frozen["images"]], ["Before treatment", "After treatment"])
        # 後ろの画像の行だけを消すと、残った前の画像だけが、前の画像の alt で並ぶ。
        line = next(x for x in text.split("\n") if x.startswith("![After treatment]"))
        self.write_raw(text.replace("\n\n" + line, ""))
        code, frozen = wiki_rawcheck.freeze(self.wiki, self.raw, "page")
        self.assertEqual(code, 0, frozen["errors"])
        self.assertEqual([(img["alt"], img["url"]) for img in frozen["images"]],
                         [("Before treatment", "https://site.example/request/i.png")])

    def test_failed_refetch_in_the_same_second_is_not_resumed(self):
        """同じ秒に、画像を取らずに --force で取り直し、raw を書けずに止まると、写しはそろわない（frontmatter が
        前の raw と同じでも、途中から続けられない）。"""
        import datetime as dt

        class FixedNow(dt.datetime):
            @classmethod
            def now(cls, tz=None):
                return dt.datetime(2026, 11, 14, 8, 0, 0)

        html = html_page(f'<p>{LONG}</p><img src="i.png" width="300" height="200">')
        with mock.patch.object(wiki_fetch, "datetime", FixedNow):
            self.build(html)
            stub = FetchStub(html)
            with mock.patch.object(wiki_fetch, "fetch", stub), \
                    mock.patch.object(wiki_fetch, "is_private_host", lambda host: False), \
                    mock.patch.object(wiki_fetch, "write_outputs", side_effect=OSError("書けない")):
                with self.assertRaises(OSError):
                    wiki_fetch.build(self.args(force=True, no_images=True))
            self.assertFalse(wiki_rawcheck.work_dir_complete(self.wiki, "page"))
            stub = FetchStub(html)
            with mock.patch.object(wiki_fetch, "fetch", stub), \
                    mock.patch.object(wiki_fetch, "is_private_host", lambda host: False):
                code, result = wiki_fetch.build(self.args())
        self.assertTrue(result["unchanged"])
        self.assertFalse(result["work_dir"])


class PullRequestReviewTest(RawCheckCase):
    """プラグインの PR（to884/info-hive-wiki#53）の Codex のレビューの指摘。"""

    def test_polite_endings_are_not_counted_as_plain(self):
        # ください、ました、でしょう の末尾（い、た、う）は、である調の語尾にも当たる。文ごとに 1 回だけ分ける。
        styles = wiki_rawcheck.sentence_styles("設定を確認してください。結果を保存しました。次に進むでしょう。これは本です。")
        self.assertEqual(styles, {"desu": 4})
        styles = wiki_rawcheck.sentence_styles("これは本である。結果を保存した。次に移る。先に確かめてください。")
        self.assertEqual(styles, {"dearu": 3, "desu": 1})
        self.setup_fetch("# A\n\nCheck the settings. We saved the result. It will continue. This is a book.\n")
        self.assertTrue(self.freeze()["ok"])
        self.write_raw("# A\n\n設定を確認してください。結果を保存しました。次に進むでしょう。これは本です。\n", fm=FM_T)
        self.assertNotIn("style", {w["kind"] for w in self.check()["warnings"]})


class SonnetTrialTest(RawCheckCase):
    """Sonnet 5.5 で試したときの改善点（sonnet-trial.md）。"""

    def test_link_error_names_the_missing_url(self):
        src = "# A\n\nSee [a](https://x.example/a) and [b](https://x.example/b).\n"
        self.setup_fetch(src)
        self.assertTrue(self.freeze()["ok"])
        self.write_raw("# A\n\n[a](https://x.example/a) を見る。\n", fm=FM_T)
        message = next(e["message"] for e in self.check()["errors"] if e["kind"] == "links")
        self.assertIn("足りないリンク: https://x.example/b", message)
        self.assertIn("取得 2、raw 1", message)

    def test_months_and_credit_words_are_not_names(self):
        names = wiki_rawcheck.names_of("The fight was in November 2024 (Created by Fareed Khan). "
                                       "It ran on a Monday.")
        self.assertNotIn("November", names)
        self.assertNotIn("Created", names)
        self.assertNotIn("Monday", names)
        self.assertIn("Fareed", names)

    def test_word_after_term_dash_is_a_sentence_start(self):
        names = wiki_rawcheck.names_of("**NOCASE** - Similar to binary, except it folds case.")
        self.assertNotIn("Similar", names)
        self.assertIn("NOCASE", names)


class SonnetTrial2Test(RawCheckCase):
    """Sonnet 5.5 で 2 回目に試したときの改善点（sonnet-trial-2.md）。"""

    def test_japanese_abbreviations_are_not_new_tokens(self):
        self.setup_fetch("# A\n\nIt runs on a laptop.\n")
        self.assertTrue(self.freeze()["ok"])
        self.write_raw("# A\n\nノート PC で動く。\n", fm=FM_T)
        result = self.check()
        self.assertEqual([w for w in result["warnings"] if w["kind"] == "new_tokens"], [])
        # 略語の一覧にない英字は、今までどおり警告する（対照）。
        self.write_raw("# A\n\nノート PC と Kubernetes で動く。\n", fm=FM_T)
        warning = next(w for w in self.check()["warnings"] if w["kind"] == "new_tokens")
        self.assertIn("Kubernetes", warning["message"])
        self.assertNotIn("'PC'", warning["message"])

    def test_original_word_in_parentheses_clears_the_name_warning(self):
        self.setup_fetch("# A\n\nIt follows the Domain Model pattern.\n")
        self.assertTrue(self.freeze()["ok"])
        self.write_raw("# A\n\nドメインモデルのパターンに従う。\n", fm=FM_T)
        warning = next(w for w in self.check()["warnings"] if w["kind"] == "missing_names")
        self.assertIn("原語を括弧で添える", warning["message"])
        self.write_raw("# A\n\nドメインモデル（Domain Model）のパターンに従う。\n", fm=FM_T)
        self.assertEqual(self.check()["warnings"], [])

    def test_caption_may_have_several_paragraphs(self):
        src = "# A\n\n![x](assets/a/1.png)\n"
        self.setup_fetch(src, images=["assets/a/1.png"])
        self.assertTrue(self.freeze()["ok"])
        self.write_raw(src + "\n> Claude Sonnet 5.5 補足: 4 つのパネルを並べた図。\n>\n"
                       "> 左上は遅延、右上は誤り率を示す。\n", fm=FM_T)
        result = self.check()
        self.assertTrue(result["ok"], result["errors"])


class ResumeTest(FetchCase):
    def test_resume_after_translation(self):
        """訳したあとに止まった取り込みを取り直すと frozen になり、訳した raw が check を通る。"""
        html = html_page(f"<p>{LONG}</p>")
        _, text, _ = self.build(html)
        self.assertEqual(wiki_rawcheck.freeze(self.wiki, self.raw, "page")[0], 0)
        out = text.replace('translated_by: ""', 'translated_by: "Claude Sonnet 5.5"').replace(LONG.strip(), "本文の訳である。")
        (self.raw / "page.md").write_text(out, encoding="utf-8", newline="\n")
        stub = FetchStub(html)
        with mock.patch.object(wiki_fetch, "fetch", stub), \
                mock.patch.object(wiki_fetch, "is_private_host", lambda host: False):
            code, result = wiki_fetch.build(self.args())
        # 原文の HTML が同じなので unchanged。raw は訳したあとのものだが、比べるのは原文のハッシュである。
        self.assertTrue(result["unchanged"])
        self.assertEqual(result["work_stage"], "frozen")
        self.assertEqual(wiki_rawcheck.check(self.wiki, self.raw, "page", None, None)[0], 0)

    def test_unchanged_reports_stage_and_values(self):
        """削除を固定したあとに止まった取り込みを取り直すと、その段まで進んだことと、手順の値を返す。"""
        html = html_page(f"<p>{LONG}</p>")
        self.build(html)
        self.assertEqual(wiki_rawcheck.freeze(self.wiki, self.raw, "page")[0], 0)
        stub = FetchStub(html)
        with mock.patch.object(wiki_fetch, "fetch", stub), \
                mock.patch.object(wiki_fetch, "is_private_host", lambda host: False):
            code, result = wiki_fetch.build(self.args())
        self.assertTrue(result["unchanged"])
        self.assertTrue(result["work_dir"])
        self.assertEqual(result["work_stage"], "frozen")
        self.assertTrue(result["needs_translation"])
        self.assertIn("images", result)


class FetchCounterexample3Test(FetchCase):
    def test_visible_text_is_counted_by_the_parser(self):
        """コードの中の * と、# で始まる段落の文字も数える（4 回目のレビュー）。"""
        for first in ("<p><code>" + "x*" * 40 + "</code></p>", "<p>#hashtag " + "y" * 80 + "</p>"):
            with self.subTest(first=first):
                result, text, _ = self.build(html_page(first + "<p>Top highlight</p>" + f"<p>{LONG}</p>"), force=True)
                self.assertIn("Top highlight", text)

    def test_underscores_count_as_text(self):
        body = "<p>" + "x_" * 40 + "</p><p>Top highlight</p>" + f"<p>{LONG}</p>"
        result, text, _ = self.build(html_page(body))
        self.assertIn("Top highlight", text)

    def test_tag_link_with_escaped_bracket(self):
        body = '<p><a href="https://site.example/tag/a">a]b</a></p>' + f"<p>{LONG}</p>"
        result, text, _ = self.build(html_page(body))
        self.assertEqual([r["rule"] for r in result["removed_by_rule"]], ["tag_links"])


class UntranslatedTest(RawCheckCase):
    BODY = "# 題名\n\n本文である。\n\n![図](assets/a/a-01.png \"https://x.example/1.png\")\n"

    def setUp(self):
        super().setUp()
        self.setup_fetch(self.BODY, images=["assets/a/a-01.png"], needs_translation=False)
        self.assertTrue(self.freeze()["ok"])

    def test_only_captions_may_be_added(self):
        self.write_raw(self.BODY + "\n> Claude Sonnet 5.5 補足: 図の説明である。\n")
        self.assertTrue(self.check()["ok"])
        self.write_raw(self.BODY.replace("本文である。", "本文です。") + "\n> Claude Sonnet 5.5 補足: 図の説明。\n")
        self.assertIn("text", self.kinds(self.check()))

    def test_language_override(self):
        self.write_raw(self.BODY + "\n> Claude Sonnet 5.5 補足: 図の説明である。\n",
                       fm=FM.replace('translated_by: ""', 'translated_by: "Claude Sonnet 5.5"'))
        self.assertIn("translated_by", self.kinds(self.check()))
        result = self.check(override="translate")
        self.assertTrue(result["ok"], result["errors"])
        self.assertEqual(result["language_override"]["value"], "translate")


class MainAndWorkDirTest(RawCheckCase):
    def test_check_requires_freeze(self):
        self.setup_fetch("# A\n\nText.\n")
        with self.assertRaises(FileNotFoundError):
            wiki_rawcheck.check(self.wiki, self.raw, "a", None, None)

    def test_finish_removes_work_dir_only_on_success(self):
        self.setup_fetch("# A\n\nText.\n", needs_translation=False)
        argv = ["--wiki", str(self.wiki), "--raw-root", str(self.raw), "--slug", "a", "--json"]

        def run(*a):
            with contextlib.redirect_stdout(io.StringIO()):
                return wiki_rawcheck.main(list(a))

        self.assertEqual(run("freeze", *argv), 0)
        self.write_raw("# A\n\nChanged.\n")
        self.assertEqual(run("check", *argv, "--finish"), 1)
        self.assertTrue(self.wd.is_dir())
        self.write_raw("# A\n\nText.\n")
        self.assertEqual(run("check", *argv, "--finish"), 0)
        self.assertFalse(self.wd.exists())

    def test_uninitialized_wiki_is_refused(self):
        """SCHEMA.md のない wiki では、何も読み書きせずに終了コード 1 で止まる（ADR-0019）。"""
        self.setup_fetch("# A\n\nText.\n")
        (self.wiki / "SCHEMA.md").unlink()
        argv = ["--wiki", str(self.wiki), "--raw-root", str(self.raw), "--slug", "a"]
        err = io.StringIO()
        with contextlib.redirect_stderr(err), contextlib.redirect_stdout(io.StringIO()):
            self.assertEqual(wiki_rawcheck.main(["freeze", *argv]), 1)
            self.assertEqual(wiki_rawcheck.main(["check", *argv, "--finish"]), 1)
        self.assertIn("/wiki:init", err.getvalue())
        self.assertFalse((self.wd / "cleaned.md").exists())
        self.assertTrue(self.wd.is_dir())

    @unittest.skipUnless(os.name == "nt", "ジャンクションは Windows だけ")
    def test_remove_refuses_junction(self):
        import _winapi
        outside = self.base / "outside"
        target = outside / "ingest" / "a"
        target.mkdir(parents=True)
        (target / "keep.txt").write_text("消してはならない", encoding="utf-8")
        wiki = self.base / "wiki2"
        wiki.mkdir()
        _winapi.CreateJunction(str(outside), str(wiki / ".wiki-cache"))
        with self.assertRaises(ValueError):
            wiki_rawcheck.remove_work_dir(wiki, "a")
        self.assertTrue((target / "keep.txt").is_file())


def offline(url, timeout, max_bytes, accept="", block_private=False):
    raise wiki_fetch.FetchError("ネットにつながらない")


# 途中から続けるときに返す、前の取得の出力の値。実装の定数（wiki_rawcheck.RESUME_KEYS）に頼らずに書き並べる。
RESUMED_KEYS = ("source_sha256_of", "title", "source_lang", "encoding", "content_root", "ja_ratio",
                "needs_translation", "chars", "images", "dropped_images", "removed_by_rule", "warnings")


def fixed_now(hour: int):
    """wiki_fetch.datetime の代わり。取得の時刻（fetched_at）を決める。"""
    import datetime as dt

    class FixedNow(dt.datetime):
        @classmethod
        def now(cls, tz=None):
            return dt.datetime(2026, 11, 14, hour, 0, 0)

    return mock.patch.object(wiki_fetch, "datetime", FixedNow)


class ResumeBeforeFetchTest(FetchCase):
    """途中の取り込みは、取得の前に再開する（docs/plans/wiki-fetch-resume-before-fetch-2026-11-14.md）。

    DOM（--html-file）で取ったページは、URL で取り直した HTML とバイト列が違う。再開の判定を取得の前に置かないと、
    写しがそろっていても、比べた時点で終了コード 3（existing_differs）になり、ネットにつながらなければ取得の失敗になる。
    """

    ARTICLE = f'<p>{LONG}</p><img src="i.png" width="300" height="200"><p>{LONG}</p>'
    DOM = html_page(ARTICLE, head='<meta name="saved-by" content="browser">')
    HTML = html_page(ARTICLE)

    def take_dom(self, content: bytes = DOM, **kw) -> dict:
        path = self.base / "saved.html"
        path.write_bytes(content)
        result, text, _ = self.build(b"", html_file=path, page_url=PAGE_URL, **kw)
        self.assertIn('source_sha256_of: "dom"', text)
        return result

    def refetch(self, stub=None, **kw) -> tuple[int, dict, FetchStub]:
        stub = stub or FetchStub(self.HTML)
        with mock.patch.object(wiki_fetch, "fetch", stub), \
                mock.patch.object(wiki_fetch, "is_private_host", lambda host: False):
            code, result = wiki_fetch.build(self.args(**kw))
        return code, result, stub

    def run_main(self, *extra: str) -> tuple[int, str]:
        out = io.StringIO()
        argv = [PAGE_URL, "--wiki", str(self.wiki), "--raw-root", str(self.raw), "--slug", "page", *extra]
        with mock.patch.object(wiki_fetch, "fetch", offline), contextlib.redirect_stdout(out), \
                contextlib.redirect_stderr(io.StringIO()):
            code = wiki_fetch.main(argv)
        return code, out.getvalue()

    def test_dom_take_resumes_without_fetch(self):
        """再現: DOM で取ったあと、URL だけで呼ぶ。直す前は、取得して比べ、終了コード 3 になった。"""
        first = self.take_dom()
        raw_before = (self.raw / "page.md").read_bytes()
        code, result, stub = self.refetch()
        self.assertEqual(code, 0, result)
        self.assertNotIn("error", result)
        self.assertEqual(stub.requested, [])
        self.assertTrue(result["unchanged"])
        self.assertTrue(result["fetch_skipped"])
        self.assertTrue(result["work_dir"])
        self.assertEqual(result["work_stage"], "fetched")
        self.assertEqual(result["source_sha256_of"], "dom")
        self.assertEqual(result["source_sha256"], first["source_sha256"])
        self.assertEqual(result["final_url"], first["final_url"])
        for key in RESUMED_KEYS:
            self.assertEqual(result[key], first[key], key)
        self.assertEqual((self.raw / "page.md").read_bytes(), raw_before)

    def test_offline_resume_after_freeze(self):
        """ネットにつながらなくても、削除を固定したあとの段から続けられる。補足を書く画像は、残ったものだけ。"""
        first = self.take_dom()
        text = (self.raw / "page.md").read_text(encoding="utf-8")
        line = next(x for x in text.split("\n") if x.startswith("!["))
        (self.raw / "page.md").write_text(text.replace(line + "\n\n", ""), encoding="utf-8", newline="\n")
        (self.raw / first["images"][0]["path"]).unlink()
        self.assertEqual(wiki_rawcheck.freeze(self.wiki, self.raw, "page")[0], 0)
        code, result, _ = self.refetch(stub=offline)
        self.assertEqual(code, 0, result)
        self.assertEqual(result["work_stage"], "frozen")
        self.assertEqual(result["images"], [])
        code, out = self.run_main("--json")
        self.assertEqual(code, 0)
        self.assertTrue(json.loads(out)["fetch_skipped"])

    def test_text_output_does_not_claim_same_content(self):
        """取得していないので、「前回と同じ」とは書かない。取り直す方法（--force）を示す。"""
        self.take_dom()
        code, out = self.run_main()
        self.assertEqual(code, 0)
        self.assertNotIn("前回と同じ", out)
        self.assertIn("取得せず", out)
        self.assertIn("--force", out)

    def test_url_take_resumes_even_if_page_changed(self):
        """URL で取ったページも、途中の取り込みがあれば取得しない。ページの更新は、取り込みを終えるまで見ない（意図した変更）。"""
        self.build(self.HTML)
        code, result, stub = self.refetch(stub=FetchStub(html_page(f"<p>{LONG} Updated.</p>")))
        self.assertEqual(code, 0, result)
        self.assertEqual(stub.requested, [])
        self.assertTrue(result["fetch_skipped"])

    # ---- 対照: 今の動き（取得して比べる）を変えない

    def test_force_refetches(self):
        self.take_dom()
        code, result, stub = self.refetch(force=True)
        self.assertEqual(code, 0, result)
        self.assertEqual(stub.requested[0], PAGE_URL)
        self.assertNotIn("fetch_skipped", result)
        self.assertIn('source_sha256_of: "html"', (self.raw / "page.md").read_text(encoding="utf-8"))

    def test_html_file_is_read_and_compared(self):
        """--html-file は、渡した内容で取るという入力なので、再開に吸い込まず、読んで比べる。"""
        self.take_dom()
        again = self.base / "again.html"
        again.write_bytes(self.DOM)
        code, result, stub = self.refetch(html_file=again, page_url=PAGE_URL)
        self.assertEqual(code, 0, result)
        self.assertTrue(result["unchanged"])
        self.assertTrue(result["work_dir"])
        self.assertNotIn("fetch_skipped", result)
        again.write_bytes(html_page(self.ARTICLE, head='<meta name="saved-by" content="browser-2">'))
        code, result, stub = self.refetch(html_file=again, page_url=PAGE_URL)
        self.assertEqual(code, 3, result)
        self.assertEqual(result["error"], "existing_differs")
        self.assertEqual(stub.requested, [])

    def test_other_url_is_fetched(self):
        self.take_dom()
        other = "https://site.example/other"
        requested: list[str] = []

        def stub(url, timeout, max_bytes, accept="", block_private=False):
            requested.append(url)
            return self.HTML, url, "text/html; charset=utf-8"

        code, result, _ = self.refetch(stub=stub, url=other)
        self.assertEqual(code, 3, result)
        self.assertEqual(requested, [other])

    def test_edited_frontmatter_is_fetched(self):
        """raw の frontmatter が写しと違えば（別の版に戻した、など）、写しで続けない。"""
        self.take_dom()
        raw = self.raw / "page.md"
        raw.write_text(raw.read_text(encoding="utf-8").replace("fetched_at: ", "fetched_at: 2000-01-01T00:00:00+09:00\nold: ", 1),
                       encoding="utf-8", newline="\n")
        code, result, stub = self.refetch()
        self.assertEqual(code, 3, result)
        self.assertEqual(stub.requested, [PAGE_URL])

    def test_removed_work_dir_is_fetched(self):
        """写しがなければ（取り込みを終えた、写しを失った）、今までどおり取得して比べる（設計書の限界）。"""
        self.take_dom()
        wiki_rawcheck.remove_work_dir(self.wiki, "page")
        code, result, stub = self.refetch()
        self.assertEqual(code, 3, result)
        self.assertEqual(stub.requested, [PAGE_URL])

    def test_resume_returns_the_first_warnings(self):
        """設計のレビュー 1 の重大 1: 本文が短いという警告を、続けるときも返す。返さないと、ブラウザで本文を取り直す
        段（W3）を飛ばして、取れなかった本文のまま続けてしまう。"""
        short = html_page("<p>記事を読み込んでいます</p>")
        first, _, _ = self.build(short)
        self.assertTrue(any("本文が短い" in w for w in first["warnings"]))
        code, result, stub = self.refetch(stub=FetchStub(self.HTML))
        self.assertEqual(code, 0, result)
        self.assertTrue(result["fetch_skipped"])
        self.assertEqual(stub.requested, [])
        for key in RESUMED_KEYS:
            self.assertEqual(result[key], first[key], key)
        code, out = self.run_main()
        self.assertIn("注意: 本文が短い", out)
        # 取得して比べる枝（--html-file に同じ内容）も、前の取得の警告を返し、文字の出力にも並べる。
        path = self.base / "short.html"
        path.write_bytes(short)
        self.build(b"", html_file=path, page_url=PAGE_URL, force=True)
        code, result, _ = self.refetch(html_file=path, page_url=PAGE_URL)
        self.assertTrue(result["work_dir"])
        self.assertTrue(any("本文が短い" in w for w in result["warnings"]))
        code, out = self.run_main("--html-file", str(path), "--page-url", PAGE_URL)
        self.assertEqual(code, 0)
        self.assertIn("前回と同じ", out)
        self.assertIn("注意: 本文が短い", out)

    def test_another_take_of_the_same_page_is_not_resumed(self):
        """実装のレビュー 1 の重大 1: 同じ URL の同じ原文を、別の設定（--keep-noise）で取った fetch.json は、取得元と
        ハッシュが同じでも、写しの fetched.md と内容で結ばれていないので、その記録で続けない。"""
        page = html_page('<p><a href="https://site.example/tag/ai">AI</a></p>' + f"<p>{LONG}</p>")
        first, _, _ = self.build(page)
        self.assertEqual([r["rule"] for r in first["removed_by_rule"]], ["tag_links"])
        wd = wiki_rawcheck.work_dir(self.wiki, "page")
        raw_a, fetched_a = (self.raw / "page.md").read_bytes(), (wd / "fetched.md").read_bytes()
        second, _, _ = self.build(page, keep_noise=True, force=True)
        self.assertEqual((second["url"], second["final_url"], second["source_sha256"]),
                         (first["url"], first["final_url"], first["source_sha256"]))
        # 取得 A の raw と fetched.md を戻し、fetch.json だけを取得 B のものにする（一部だけを戻したバックアップ）。
        (self.raw / "page.md").write_bytes(raw_a)
        (wd / "fetched.md").write_bytes(fetched_a)
        code, result, stub = self.refetch(stub=FetchStub(page))
        self.assertEqual(stub.requested, [PAGE_URL])
        self.assertNotIn("fetch_skipped", result)
        self.assertTrue(result["unchanged"])
        self.assertFalse(result["work_dir"])

    def make_legacy(self):
        """写しの fetch.json を、0.14.1 までの版が書いた形にする（fetched_sha256 と source_sha256_of がない）。"""
        path = wiki_rawcheck.work_dir(self.wiki, "page") / "fetch.json"
        saved = json.loads(path.read_text(encoding="utf-8"))
        del saved["fetched_sha256"], saved["source_sha256_of"]
        path.write_bytes(json.dumps(saved, ensure_ascii=False).encode("utf-8"))

    def test_record_of_old_versions_is_not_resumed(self):
        """実装のレビュー 3 の重大 1・2: 0.14.1 までの版が書いた写しは、fetch.json と fetched.md を結べず（別の設定で取った
        記録を見分けられない）、どの取得かも分からない（source_sha256_of がない）ので、どちらの枝でも続けない。"""
        self.build(self.HTML)
        self.make_legacy()
        code, result, stub = self.refetch()
        self.assertEqual(code, 0, result)
        self.assertEqual(stub.requested, [PAGE_URL])
        self.assertTrue(result["unchanged"])
        self.assertFalse(result["work_dir"])
        # 削除を固定したあとの写しも続けない。
        self.assertEqual(wiki_rawcheck.freeze(self.wiki, self.raw, "page")[0], 0)
        code, result, stub = self.refetch()
        self.assertFalse(result["work_dir"])
        out = wiki_fetch.render_text(code, result)
        self.assertIn("0.14.1 までの版", out)
        self.assertIn("--force", out)
        # DOM で取った写しに同じ HTML のファイルを渡しても（取得して比べる枝）、続けない。
        self.take_dom(force=True)
        path = self.base / "saved.html"
        self.make_legacy()
        code, result, _ = self.refetch(html_file=path, page_url=PAGE_URL)
        self.assertEqual(code, 0, result)
        self.assertFalse(result["work_dir"])
        self.assertEqual(result["source_sha256_of"], "dom")

    def test_restored_old_record_of_another_setting_is_not_resumed(self):
        """実装のレビュー 3 の重大 1: 同じ原文を別の設定（--keep-noise）で取った 0.14.1 までの版の fetch.json を丸ごと戻しても、
        取得して原文が同じだからといって、その記録で続けない（本文が空という今の取得の警告を消さない）。"""
        page = html_page('<p><a href="https://site.example/tag/ai">AI</a></p>' + f"<p>{LONG}</p>")
        self.build(page, keep_noise=True)
        self.make_legacy()
        wd = wiki_rawcheck.work_dir(self.wiki, "page")
        legacy = (wd / "fetch.json").read_bytes()
        self.build(page, force=True)
        (wd / "fetch.json").write_bytes(legacy)
        code, result, stub = self.refetch(stub=FetchStub(page))
        self.assertEqual(stub.requested, [PAGE_URL])
        self.assertFalse(result["work_dir"])
        self.assertNotIn("work_stage", result)

    def swap_cleaned(self, take_a: dict, take_b: dict) -> tuple[Path, bytes]:
        """取得 A のあとに freeze し、取得 B で取り直してから、A の cleaned.md だけを写しに戻す。"""
        with fixed_now(take_a.pop("hour")):
            self.build(**take_a)
        self.assertEqual(wiki_rawcheck.freeze(self.wiki, self.raw, "page")[0], 0)
        wd = wiki_rawcheck.work_dir(self.wiki, "page")
        cleaned_a = (wd / "cleaned.md").read_bytes()
        with fixed_now(take_b.pop("hour")):
            self.build(**take_b, force=True)
        self.assertFalse((wd / "cleaned.md").exists())
        (wd / "cleaned.md").write_bytes(cleaned_a)
        return wd, cleaned_a

    def test_cleaned_of_another_take_is_not_resumed(self):
        """実装のレビュー 2 の重大 1: 別の取得の cleaned.md だけを戻した写しは、1 つの取得と、その取得のあとの freeze
        が残しうる組ではないので、どちらの枝でも続けない。"""
        page = html_page('<p><a href="https://site.example/tag/ai">AI</a></p>' + f"<p>{LONG}</p>")
        path = self.base / "b.html"
        path.write_bytes(page)
        cases = {
            # 時刻と原文が違う（frontmatter が違う）。
            "other_hour": (dict(hour=8, html=html_page(f"<p>{LONG} Earlier.</p>")),
                           dict(hour=9, html=b"", html_file=path, page_url=PAGE_URL)),
            # 同じ秒の同じ原文（frontmatter が同じ）。A は規則を止めてタグのリンクを残し、B は消した。A の cleaned.md は、
            # B の fetched.md から消すことだけでは作れない（本文で見分ける）。
            "same_frontmatter": (dict(hour=8, html=b"", html_file=path, page_url=PAGE_URL, keep_noise=True),
                                 dict(hour=8, html=b"", html_file=path, page_url=PAGE_URL)),
        }
        for name, (take_a, take_b) in cases.items():
            with self.subTest(name):
                wd, _ = self.swap_cleaned(take_a, take_b)
                # 取得の前の再開（URL だけ）は続けず、取得して比べる。原文は同じなので、取得して比べる枝で続けないと示す。
                code, result, stub = self.refetch(stub=FetchStub(page))
                self.assertEqual(stub.requested, [PAGE_URL])
                self.assertNotIn("fetch_skipped", result)
                self.assertFalse(result["work_dir"])
                # 取得して比べる枝（同じ HTML のファイル）も続けない。
                code, result, _ = self.refetch(html_file=path, page_url=PAGE_URL)
                self.assertEqual(code, 0, result)
                self.assertFalse(result["work_dir"])
                # 対照: 取得 B のあとの freeze が書いた cleaned.md なら、続ける。
                (wd / "cleaned.md").unlink()
                self.assertEqual(wiki_rawcheck.freeze(self.wiki, self.raw, "page")[0], 0)
                code, result, stub = self.refetch(stub=offline)
                self.assertEqual(code, 0, result)
                self.assertEqual(result["work_stage"], "frozen")

    def test_cleaned_that_the_take_could_have_frozen_is_resumed(self):
        """整合の定義の対照: 別の取得の cleaned.md でも、今の取得のあとの freeze が残しうるもの（frontmatter が同じで、
        今の fetched.md から消すことだけで作れる）なら、ファイルからは見分けられず、続けてよい組である。"""
        path = self.base / "b.html"
        path.write_bytes(html_page('<p><a href="https://site.example/tag/ai">AI</a></p>' + f"<p>{LONG}</p>"))
        # A は規則でタグのリンクを消し、B は規則を止めて残した。A の cleaned.md は、B のあとに W4 でタグのリンクを
        # 消して freeze したものと同じである。
        self.swap_cleaned(dict(hour=8, html=b"", html_file=path, page_url=PAGE_URL),
                          dict(hour=8, html=b"", html_file=path, page_url=PAGE_URL, keep_noise=True))
        code, result, stub = self.refetch(stub=offline)
        self.assertEqual(code, 0, result)
        self.assertEqual(result["work_stage"], "frozen")
        self.assertEqual(result["freeze"]["removed_lines"], ["[AI](https://site.example/tag/ai)"])

    def test_interrupted_second_freeze_resumes_with_the_first(self):
        """2 回目の freeze が、removed.json を置いたあと、cleaned.md を置く前に止まっても、1 回目の cleaned.md は
        freeze が通す内容なので、それで続ける（報告も 1 回目のもの）。"""
        tail = "This closing paragraph is long enough that removing it trips the twenty percent warning. " * 3
        self.build(html_page(f"<p>{LONG * 3}</p><p>{tail}</p>"))
        self.assertEqual(wiki_rawcheck.freeze(self.wiki, self.raw, "page")[0], 0)
        raw = self.raw / "page.md"
        raw.write_text(raw.read_text(encoding="utf-8").replace("\n\n" + tail.strip(), ""), encoding="utf-8", newline="\n")
        real = wiki_rawcheck.write_atomic

        def stop_before_cleaned(path, text):
            if path.name == "cleaned.md":
                raise OSError("止まった")
            real(path, text)

        with mock.patch.object(wiki_rawcheck, "write_atomic", stop_before_cleaned):
            with self.assertRaises(OSError):
                wiki_rawcheck.freeze(self.wiki, self.raw, "page")
        code, result, _ = self.refetch(stub=offline)
        self.assertEqual(code, 0, result)
        self.assertEqual(result["work_stage"], "frozen")
        self.assertEqual(result["freeze"]["removed_lines"], [])
        self.assertEqual(result["freeze"]["warnings"], [])

    def test_frozen_resume_returns_freeze_report(self):
        """実装のレビュー 1 の重大 2: freeze の出力を読む前に止まっても、続けるときに freeze の報告（消した行と警告）を
        返す。止まる前に読むはずだった報告を読み直して、本文を消していないかを確かめられる。"""
        tail = "This closing paragraph is long enough that removing it trips the twenty percent warning. " * 3
        first, _, _ = self.build(html_page(f"<p>{LONG * 3}</p><p>{tail}</p>"))
        self.assertEqual(first["warnings"], [])
        raw = self.raw / "page.md"
        text = raw.read_text(encoding="utf-8")
        raw.write_text(text.replace("\n\n" + tail.strip(), ""), encoding="utf-8", newline="\n")
        code, frozen = wiki_rawcheck.freeze(self.wiki, self.raw, "page")
        self.assertEqual(code, 0, frozen["errors"])
        self.assertEqual([w["kind"] for w in frozen["warnings"]], ["removed_much"])
        code, result, _ = self.refetch(stub=offline)
        self.assertEqual(code, 0, result)
        self.assertEqual(result["work_stage"], "frozen")
        self.assertEqual(result["freeze"], {"removed_lines": frozen["removed_lines"],
                                            "shortened_lines": frozen["shortened_lines"],
                                            "warnings": frozen["warnings"]})
        self.assertEqual(result["images"], frozen["images"])
        self.assertEqual(result["warnings"], [])  # 取得の警告と、freeze の警告を混ぜない
        code, out = self.run_main()
        self.assertIn("警告: 消した文字が本文の 2 割を超える", out)
        self.assertIn("消した行: " + tail.strip()[:40], out)

    def test_frontmatter_final_url_of_another_type_is_not_resumed(self):
        """frontmatter の final_url が文字列でなければ（[] など）、ないものとして url で代えずに、続けない。"""
        self.build(self.HTML)
        wd = wiki_rawcheck.work_dir(self.wiki, "page")
        for path in (self.raw / "page.md", wd / "fetched.md"):
            path.write_bytes(path.read_bytes().replace(b"\nsource_lang:", b"\nfinal_url: []\nsource_lang:", 1))
        record = wd / "fetch.json"
        saved = json.loads(record.read_text(encoding="utf-8"))
        saved["fetched_sha256"] = wiki_rawcheck.snapshot_sha256((wd / "fetched.md").read_bytes())
        record.write_bytes(json.dumps(saved, ensure_ascii=False).encode("utf-8"))
        self.assertTrue(wiki_rawcheck.work_dir_matches_raw(self.wiki, "page", self.raw / "page.md"))
        code, result, stub = self.refetch()
        self.assertEqual(stub.requested, [PAGE_URL])
        self.assertFalse(result["work_dir"])

    def test_fetch_json_of_another_fetch_is_not_resumed(self):
        """設計のレビュー 1 の重大 2: fetch.json の取得元とハッシュが、写しの fetched.md（と raw）の frontmatter と
        違えば（一部だけを戻したバックアップなど）、その記録で続けない。"""
        other = "https://site.example/other"
        for change in ({"url": other}, {"source_sha256": "b" * 64}, {"final_url": other}):
            with self.subTest(change=change):
                self.build(self.HTML, force=True)
                path = wiki_rawcheck.work_dir(self.wiki, "page") / "fetch.json"
                saved = json.loads(path.read_text(encoding="utf-8"))
                saved.update(change)
                path.write_bytes(json.dumps(saved).encode("utf-8"))
                requested: list[str] = []

                def stub(url, timeout, max_bytes, accept="", block_private=False):
                    requested.append(url)
                    return self.HTML, url, "text/html; charset=utf-8"

                url = change.get("url", PAGE_URL)
                code, result, _ = self.refetch(stub=stub, url=url)
                self.assertEqual(requested, [url])
                self.assertNotIn("fetch_skipped", result)
                self.assertFalse(result["work_dir"])

    def test_malformed_fetch_json_is_not_resumed(self):
        """fetch.json が JSON として読めても、取得器の書いた形（続けるときに使うキーがその型）でなければ、続けずに
        取得に進む。例外では止まらない（設計のレビュー 1 の軽微: images が null のまま frozen で選び直すと落ちた）。"""
        self.build(self.HTML)
        path = wiki_rawcheck.work_dir(self.wiki, "page") / "fetch.json"
        good = json.loads(path.read_text(encoding="utf-8"))
        broken = ["[]", '{"source_sha256": "x"}', '{"url": 1, "source_sha256": "x"}']
        for key, value in (("images", None), ("images", [1]), ("images", [{"path": None}]),
                           ("removed_by_rule", [{"rule": "x"}]), ("warnings", [1]), ("needs_translation", "yes"),
                           ("final_url", None)):
            broken.append(json.dumps({**good, key: value}))
        for content in broken:
            with self.subTest(content=content[:80]):
                self.build(self.HTML, force=True)
                (wiki_rawcheck.work_dir(self.wiki, "page") / "cleaned.md").write_bytes(
                    (self.raw / "page.md").read_bytes())
                path.write_bytes(content.encode("utf-8"))
                code, result, stub = self.refetch()
                self.assertEqual(code, 0, result)
                self.assertEqual(stub.requested, [PAGE_URL])
                self.assertTrue(result["unchanged"])
                self.assertFalse(result["work_dir"])


if __name__ == "__main__":
    unittest.main()
