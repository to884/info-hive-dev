"""rag が返す PDF の絶対パスと SHA-256 を、ソースの要約ページの frontmatter に書いて読み戻す試験（ADR-0013）。

ingest の手順は、`raw:` と `raw_sha256:` を二重引用符で囲み、`\\` を `\\\\`、`"` を `\\"` と書くと決めている。
wiki の手書きのパーサー（`wiki_text.parse_frontmatter_text`）と PyYAML が、同じ値として読むことを確かめる。
wiki 0.9.5 から、グラフのスクリプトも `raw:` などの最上位の欄は手書きのパーサーで読む（PyYAML で読むのは
`graph:` の欄だけ）。PyYAML と同じ値になることは、frontmatter を YAML として読むほかの道具のために確かめる。
"""
from __future__ import annotations

import hashlib
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "info-hive-wiki/skills/info-hive/scripts"))

import yaml  # noqa: E402
import wiki_text  # noqa: E402


def escape(value: str) -> str:
    """ingest の手順に書いた書き方。"""
    return '"' + value.replace("\\", "\\\\").replace('"', '\\"') + '"'


class RawFrontmatterTests(unittest.TestCase):
    VALUES = [
        "C:/Books/日本語の資料.pdf",                # rag が Windows で返す / 区切りの絶対パス
        "D:/Users/someone/OneDrive - 会社/本 #1.pdf",  # 空白、#、日本語
        "/home/someone/My Books/a,b.pdf",           # POSIX のパスとカンマ
        '/srv/books/題名 "引用" と \\ 記号.pdf',      # POSIX ではファイル名に " と \ を使える
    ]

    def test_documented_escape_matches_the_formatter(self):
        for value in self.VALUES:
            with self.subTest(value=value):
                self.assertEqual(escape(value), wiki_text.format_fm_value(value))

    def test_both_parsers_read_the_same_raw_and_sha256(self):
        for value in self.VALUES:
            sha256 = hashlib.sha256(value.encode("utf-8")).hexdigest()
            text = f"type: \"source\"\nraw: {escape(value)}\nraw_sha256: {escape(sha256)}\nrag_job_id: \"0123abcd\""
            with self.subTest(value=value):
                light = wiki_text.parse_frontmatter_text(text)
                full = yaml.safe_load(text)
                self.assertEqual(light["raw"], value)
                self.assertEqual(full["raw"], value)
                self.assertEqual(light["raw_sha256"], sha256)
                self.assertEqual(full["raw_sha256"], sha256)
                self.assertEqual(wiki_text.unquoted_string_keys(text), [])

    def test_windows_backslash_path_would_break_without_escape(self):
        # rag は / 区切りで返すので起きないが、手で \ のまま書いたときにどう読むかを残しておく。
        # wiki 0.9.6 から、手書きのパーサーも YAML のエスケープを YAML の意味で読む。\b と \n は YAML が決めている
        # エスケープなので、どちらのパーサーも、後退と改行の入った同じ（壊れた）値に読む。0.9.5 までの手書きの
        # パーサーは、書かれた文字のまま読んでいた。
        text = 'raw: "C:\\books\\new.pdf"'
        self.assertEqual(yaml.safe_load(text)["raw"], "C:\x08ooks\new.pdf")
        self.assertEqual(wiki_text.parse_frontmatter_text(text)["raw"], "C:\x08ooks\new.pdf")
        # YAML にないエスケープ（\U のあとが 16 進 8 桁でない）が 1 つでもある値は、YAML としては誤りである。
        # PyYAML は frontmatter を読めず、手書きのパーサーは、値の全体を書かれた文字のまま読む（\n も改行にしない）。
        text = 'raw: "C:\\Users\\new.pdf"'
        with self.assertRaises(yaml.YAMLError):
            yaml.safe_load(text)
        self.assertEqual(wiki_text.parse_frontmatter_text(text)["raw"], "C:\\Users\\new.pdf")


if __name__ == "__main__":
    unittest.main(verbosity=2)
