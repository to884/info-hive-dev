"""Web ページの取得（wiki_fetch.py）の試験。info-hive-wiki#42 の Medium の取りこぼしを確かめる。

- `<picture>` の `<source srcset>` にだけ URL がある図を保存すること（`<img>` に URL がない）。
- `<pre>` の中で `<br>` で区切った行を、改行のまま保つこと。

取得（`fetch`）を差し替えるので、ネットにはつながない。

実行（標準ライブラリだけで動く）:
    python -X utf8 -m unittest tests/wiki/test_wiki_fetch.py -v
"""
from __future__ import annotations

import argparse
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

PAGE_URL = "https://medium.example/@someone/article-1"
CDN = "https://miro.medium.example/v2"
FILLER = "<p>" + "本文の段落である。" * 80 + "</p>"


def png(width: int, height: int) -> bytes:
    ihdr = struct.pack(">II", width, height) + b"\x08\x06\x00\x00\x00"
    chunk = b"IHDR" + ihdr
    return (b"\x89PNG\r\n\x1a\n" + struct.pack(">I", len(ihdr)) + chunk
            + struct.pack(">I", zlib.crc32(chunk) & 0xFFFFFFFF))


def medium_figure(image_id: str, *, webp_only: bool = False, img_attrs: str = "") -> str:
    """Medium が返す図の形を縮めたもの。URL は <source> にだけあり、<img> にはない。"""
    webp = (f'<source srcSet="{CDN}/resize:fit:640/format:webp/{image_id}.png 640w, '
            f'{CDN}/resize:fit:1400/format:webp/{image_id}.png 1400w" '
            'sizes="(min-resolution: 4dppx) and (max-width: 700px) 50vw, 700px" type="image/webp"/>')
    plain = (f'<source data-testid="og" srcSet="{CDN}/resize:fit:640/{image_id}.png 640w, '
             f'{CDN}/resize:fit:1400/{image_id}.png 1400w, {CDN}/resize:fit:1000/{image_id}.png 1000w" '
             'sizes="(min-resolution: 4dppx) and (max-width: 700px) 50vw, 700px"/>')
    sources = webp if webp_only else webp + plain
    return (f'<figure><div><picture>{sources}'
            f'<img alt="" class="bh md" width="700" height="467" loading="eager" role="presentation" {img_attrs}/>'
            '</picture></div><figcaption>図の説明</figcaption></figure>')


def page(body: str) -> bytes:
    html = ('<!doctype html><html lang="en"><head><title>Article | Medium</title></head><body>'
            f'<article><h1>Article</h1>{FILLER}{body}{FILLER}</article></body></html>')
    return html.encode("utf-8")


class FetchStub:
    """ページの URL には HTML を、それ以外には PNG を返す。取りに来た URL を記録する。"""

    def __init__(self, html: bytes):
        self.html = html
        self.requested: list[str] = []

    def __call__(self, url, timeout, max_bytes, accept="", block_private=False):
        self.requested.append(url)
        if url == PAGE_URL:
            return self.html, url, "text/html; charset=utf-8"
        return png(200, 120), url, "image/png"


class FetchTestCase(unittest.TestCase):
    def run_build(self, body: str) -> tuple[dict, str, FetchStub]:
        stub = FetchStub(page(body))
        tmp = tempfile.TemporaryDirectory()
        self.addCleanup(tmp.cleanup)
        args = argparse.Namespace(
            url=PAGE_URL, raw_root=Path(tmp.name), slug="article-1", json=True, no_images=False,
            timeout=5, max_bytes=wiki_fetch.DEFAULT_MAX_BYTES, max_images=50, force=False)
        # 内部のアドレスかを調べるときの名前の解決（DNS）も止める。
        with mock.patch.object(wiki_fetch, "fetch", stub), \
                mock.patch.object(wiki_fetch, "is_private_host", lambda host: False):
            code, result = wiki_fetch.build(args)
        self.assertEqual(code, 0, result)
        text = (Path(tmp.name) / "article-1.md").read_text(encoding="utf-8")
        return result, text, stub


class PictureSourceTest(FetchTestCase):
    def test_saves_image_from_picture_source(self):
        result, text, stub = self.run_build(medium_figure("1*abc"))
        self.assertEqual([d["reason"] for d in result["dropped_images"]], [])
        self.assertEqual(len(result["images"]), 1)
        image = result["images"][0]
        # WebP でない <source> を選び、その中で幅のいちばん大きい候補を取る。
        self.assertEqual(image["url"], f"{CDN}/resize:fit:1400/1*abc.png")
        self.assertEqual(image["path"], "assets/article-1/article-1-01.png")
        self.assertIn(f"{CDN}/resize:fit:1400/1*abc.png", stub.requested)
        self.assertIn("](assets/article-1/article-1-01.png ", text)

    def test_uses_webp_source_when_it_is_the_only_one(self):
        result, _, _ = self.run_build(medium_figure("1*def", webp_only=True))
        self.assertEqual(len(result["images"]), 1)
        self.assertEqual(result["images"][0]["url"], f"{CDN}/resize:fit:1400/format:webp/1*def.png")

    def test_placeholder_data_uri_falls_back_to_source(self):
        result, _, _ = self.run_build(medium_figure("1*ghi", img_attrs='src="data:image/gif;base64,R0lGOD"'))
        self.assertEqual(len(result["images"]), 1)
        self.assertEqual(result["images"][0]["url"], f"{CDN}/resize:fit:1400/1*ghi.png")

    def test_img_src_wins_over_picture_source(self):
        result, _, _ = self.run_build(medium_figure("1*jkl", img_attrs=f'src="{CDN}/own/1*jkl.png"'))
        self.assertEqual(result["images"][0]["url"], f"{CDN}/own/1*jkl.png")

    def test_several_figures_keep_order(self):
        result, text, _ = self.run_build(medium_figure("1*one") + "<p>間の段落。</p>" + medium_figure("1*two"))
        self.assertEqual([i["url"] for i in result["images"]],
                         [f"{CDN}/resize:fit:1400/1*one.png", f"{CDN}/resize:fit:1400/1*two.png"])
        self.assertLess(text.index("article-1-01.png"), text.index("article-1-02.png"))

    def test_source_with_media_is_tried_last(self):
        body = ('<figure><picture><source media="(max-width: 600px)" srcset="https://cdn.example/crop.png 600w"/>'
                '<source srcset="https://cdn.example/full.png 1400w"/>'
                '<img alt="" width="700" height="467"/></picture></figure>')
        result, _, _ = self.run_build(body)
        self.assertEqual(result["images"][0]["url"], "https://cdn.example/full.png")

    def test_comma_inside_source_url_is_kept(self):
        body = ('<figure><picture><source srcset="https://cdn.example/resize,w_640/a.png 640w, '
                'https://cdn.example/resize,w_1400/a.png 1400w"/><img alt="" width="700" height="467"/>'
                '</picture></figure>')
        result, _, _ = self.run_build(body)
        self.assertEqual(result["images"][0]["url"], "https://cdn.example/resize,w_1400/a.png")

    def test_data_uri_srcset_falls_back_to_data_srcset(self):
        body = ('<figure><picture><source srcset="data:image/gif;base64,AAAA" '
                'data-srcset="https://cdn.example/real.png 1400w"/><img alt="" width="700" height="467"/>'
                '</picture></figure>')
        result, _, _ = self.run_build(body)
        self.assertEqual(result["images"][0]["url"], "https://cdn.example/real.png")

    def test_plain_img_is_unchanged(self):
        result, _, _ = self.run_build(f'<figure><img src="{CDN}/plain.png" alt="図" width="600" height="400"/></figure>')
        self.assertEqual(result["images"][0]["url"], f"{CDN}/plain.png")
        self.assertEqual(result["images"][0]["alt"], "図")


class SrcsetTest(unittest.TestCase):
    def test_parse_keeps_commas_inside_urls(self):
        self.assertEqual(wiki_fetch.parse_srcset("a,b.png 1x, c,d.png 2x"),
                         [("a,b.png", "x", 1.0), ("c,d.png", "x", 2.0)])

    def test_trailing_comma_ends_candidate_without_descriptor(self):
        self.assertEqual(wiki_fetch.parse_srcset("a.png, b.png 2x"), [("a.png", "x", 1.0), ("b.png", "x", 2.0)])

    def test_largest_treats_missing_descriptor_as_1x(self):
        self.assertEqual(wiki_fetch._largest_candidate("full.png, half.png 0.5x"), "full.png")
        self.assertEqual(wiki_fetch._largest_candidate("a.png 1x, b.png 1.5x"), "b.png")

    def test_largest_skips_invalid_descriptors(self):
        self.assertEqual(wiki_fetch._largest_candidate("valid.png 100w, invalid.png 2x 1000w, bad.png abcw"),
                         "valid.png")

    def test_largest_skips_data_uri(self):
        self.assertEqual(wiki_fetch._largest_candidate("data:image/gif;base64,AAAA 2000w, real.png 100w"), "real.png")
        self.assertEqual(wiki_fetch._largest_candidate("data:image/gif;base64,AAAA"), "")


class PreLineBreakTest(FetchTestCase):
    YAML_LINES = [
        "dataProduct: Claim",
        "type: foundational",
        "",
        "attributes:",
        "  claimId: ClaimIdentifier",
        "  policyId: PolicyIdentifier",
    ]

    def code_block(self, text: str) -> str:
        start = text.index("```\n") + 4
        return text[start:text.index("\n```", start)]

    def test_br_inside_pre_becomes_newline(self):
        # Medium は <pre> の中の <span> で行を <br> で区切る。空行は <br><br> になる。
        inner = "<br>".join(self.YAML_LINES)
        _, text, _ = self.run_build(f'<pre class="lv"><span class="ox" data-code-block-mode="0">{inner}</span></pre>')
        self.assertEqual(self.code_block(text), "\n".join(self.YAML_LINES))

    def test_self_closing_br_inside_pre(self):
        inner = "<br/>".join(self.YAML_LINES)
        _, text, _ = self.run_build(f"<pre><code>{inner}</code></pre>")
        self.assertEqual(self.code_block(text), "\n".join(self.YAML_LINES))

    def test_newlines_in_pre_text_are_kept(self):
        _, text, _ = self.run_build("<pre><code>a = 1\n  b = 2\n</code></pre>")
        self.assertEqual(self.code_block(text), "a = 1\n  b = 2")

    def test_br_outside_pre_is_unchanged(self):
        _, text, _ = self.run_build("<p>一行目<br>二行目</p>")
        self.assertIn("一行目  \n二行目", text)


if __name__ == "__main__":
    unittest.main()
