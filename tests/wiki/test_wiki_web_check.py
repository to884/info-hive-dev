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
        """fetch.json を一時の名前から正式な名前に変える前に失敗すると、raw は書かず、写しは「そろっていない」になる。"""
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


if __name__ == "__main__":
    unittest.main()
