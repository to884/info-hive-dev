"""wiki_lint.py の索引、出典、原本、タグの検査（wiki 0.7.0）の試験。

検査の仕様は `docs/research/wiki-article-methodology-adoption-2026-11-08.md` の第 3 節にある。
小さな wiki を一時ディレクトリに作り、`collect_pages`、`collect_index_entries`、`lint` を呼ぶ。
CLI の引数（`--allowed-tags`）は子プロセスで確かめる。

実行（標準ライブラリだけで動く）:
    python -X utf8 -m unittest tests/wiki/test_wiki_lint.py -v
"""
from __future__ import annotations

import json
import os
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
SCRIPTS = ROOT / "info-hive-wiki/skills/info-hive/scripts"
sys.path.insert(0, str(SCRIPTS))

import wiki_lint  # noqa: E402


def page(type_: str | None, title: str, *, tags=("知識表現",), sources=None, raw=None, body="") -> str:
    lines = ["---"]
    if type_ is not None:
        lines.append(f'type: "{type_}"')
    lines.append(f'title: "{title}"')
    lines.append("tags: [" + ", ".join(f'"{t}"' for t in tags) + "]")
    if sources is not None:
        if isinstance(sources, str):
            lines.append(f'sources: "{sources}"')
        else:
            lines.append("sources: [" + ", ".join(f'"{s}"' for s in sources) + "]")
    if raw is not None:
        lines.append("raw: " + json.dumps(raw, ensure_ascii=False))
    lines += ["created: 2026-11-09", "updated: 2026-11-09", "---", "", body or f"# {title}", ""]
    return "\n".join(lines)


def by_path(findings: list[dict]) -> list[dict]:
    """ページを集める順（rglob）は OS で違うので、ページのパスの順に並べてから比べる。"""
    return sorted(findings, key=lambda f: f["path"])


class LintCase(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory(ignore_cleanup_errors=True)
        self.addCleanup(self.temp.cleanup)
        self.base = Path(self.temp.name)
        self.wiki = self.base / "wiki"
        for d in ("sources", "concepts", "entities", "synthesis"):
            (self.wiki / d).mkdir(parents=True)

    def write(self, rel: str, text: str) -> Path:
        path = self.wiki / rel
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(text, encoding="utf-8")
        return path

    def run_lint(self, allowed_tags=None) -> dict:
        pages = wiki_lint.collect_pages(self.wiki)
        return wiki_lint.lint(pages, 100, 200, list(wiki_lint.DEFAULT_REQUIRED_FM), False, 5,
                              index_entries=wiki_lint.collect_index_entries(self.wiki), allowed_tags=allowed_tags)


class IndexTypeMismatchTests(LintCase):
    def setUp(self):
        super().setUp()
        self.write("sources/論文a.md", page("source", "論文 A"))
        self.write("sources/論文b.md", page("source", "論文 B"))
        self.write("concepts/消費税.md", page("concept", "消費税", sources=["論文a"]))
        self.write("synthesis/比較.md", page("synthesis", "比較", sources=["論文a"]))
        self.write("entities/山田.md", page("entity", "山田", sources=["論文a"]))
        self.write("concepts/型なし.md", page(None, "型なし"))

    def mismatches(self) -> list[tuple]:
        return [(f["index"], f["heading"], f["expected"], f["link"], f["type"])
                for f in self.run_lint()["index_type_mismatch"]]

    def test_source_listed_under_synthesis(self):
        # 作者の wiki で起きた誤り。シンセシスの欄に source のページが並んでいる。
        self.write("index.md", "\n".join([
            "# Wiki のインデックス", "",
            "各項目は wikilink と要約からなる（`- [[消費税]]: 概要`）。例: [[論文b]] も見る。", "",
            "## ソース", "", "- [[論文a]]: 論文 A。", "",
            "## コンセプト", "", "- [[消費税]]: 税の概要。[[論文b]] を参照。", "",
            "## シンセシス", "", "- [[比較]]: 比較。", "- [[論文b]]: 誤ってここにある。", "",
        ]))
        self.assertEqual(self.mismatches(), [("index.md", "シンセシス", "synthesis", "論文b", "source")])
        findings = self.run_lint()
        self.assertEqual(findings["summary"]["index_type_mismatch"], 1)
        self.assertEqual(findings["index_type_mismatch"][0]["path"], "sources/論文b.md")
        self.assertIn("synthesis の欄にあるが", wiki_lint.render_text(findings))

    def test_only_first_link_of_list_items_under_type_headings(self):
        self.write("index.md", "\n".join([
            "# Wiki のインデックス", "",
            "- [[論文a]]: 見出しの前の項目は数えない。", "",
            "## コンセプト", "",
            "冒頭の説明文の [[論文a]] は数えない。", "",
            "- [[消費税]]: 要約の中の [[論文a]] は数えない。",
            "- `[[論文b]]` はコードなので数えない。[[山田]] が最初のリンクになる。",
            "```", "- [[論文a]]: コードフェンスの中は数えない。", "```", "",
        ]))
        self.assertEqual(self.mismatches(), [("index.md", "コンセプト", "concept", "山田", "entity")])

    def test_nested_and_unknown_headings(self):
        self.write("index.md", "\n".join([
            "## エンティティ（2）", "",
            "### 人物", "", "- [[山田]]: 人物。", "- [[消費税]]: 深い見出しは種類を引き継ぐ。", "",
            "## 使い方", "", "- [[論文a]]: 種類でない見出しの下は数えない。", "",
            "## Sources", "", "- [[論文b]]", "- [[比較]]: 英語の見出しも読む。", "",
        ]))
        self.assertEqual(self.mismatches(), [
            ("index.md", "エンティティ（2）", "entity", "消費税", "concept"),
            ("index.md", "Sources", "source", "比較", "synthesis"),
        ])

    def test_split_indexes_use_file_name(self):
        self.write("index.md", "\n".join([
            "# インデックス", "", "## ソース", "", "- [[indexes/sources]]: ソースの一覧（2 件）", "",
        ]))
        self.write("indexes/sources.md", "# ソースのインデックス\n\n- [[論文a]]\n- [[消費税]]\n")
        self.write("indexes/entities-people.md", "# 人物\n\n- [[山田]]\n- [[論文b]]\n")
        self.write("indexes/howto.md", "# 手順\n\n- [[論文a]]\n")
        self.assertEqual(self.mismatches(), [
            ("indexes/entities-people.md", None, "entity", "論文b", "source"),
            ("indexes/sources.md", None, "source", "消費税", "concept"),
        ])

    def test_broken_and_typeless_entries_are_skipped(self):
        self.write("index.md", "## ソース\n\n- [[存在しない]]\n- [[型なし]]\n- [[sources/論文a|別名]]\n")
        self.assertEqual(self.mismatches(), [])

    def test_without_index(self):
        self.assertEqual(self.run_lint()["index_type_mismatch"], [])


class UnresolvedSourcesTests(LintCase):
    def test_missing_and_not_source(self):
        self.write("sources/論文a.md", page("source", "論文 A"))
        self.write("concepts/消費税.md", page("concept", "消費税", sources=["論文a"]))
        self.write("concepts/所得税.md", page("concept", "所得税", sources=["論文a", "消えた論文", "消費税"]))
        self.write("synthesis/比較.md", page("synthesis", "比較", sources="[[sources/論文a]]"))
        self.write("synthesis/比較2.md", page("synthesis", "比較 2", sources=["[[論文z]]"]))
        self.write("synthesis/比較3.md", page("synthesis", "比較 3", sources=[]))
        findings = self.run_lint()
        self.assertEqual(by_path(findings["unresolved_sources"]), [
            {"path": "concepts/所得税.md", "source": "消えた論文", "reason": "missing"},
            {"path": "concepts/所得税.md", "source": "消費税", "reason": "not_source", "type": "concept"},
            {"path": "synthesis/比較2.md", "source": "[[論文z]]", "reason": "missing"},
        ])
        self.assertEqual(findings["summary"]["unresolved_sources"], 3)
        text = wiki_lint.render_text(findings)
        self.assertIn("消えた論文: ページがない", text)
        self.assertIn("type が concept のページを指している", text)


class MissingRawTests(LintCase):
    def test_relative_bases(self):
        (self.base / "raw").mkdir()
        (self.base / "raw" / "a.md").write_text("原本", encoding="utf-8")
        (self.base / "raw" / "論文c").mkdir()
        (self.wiki / "sources" / "local.txt").write_text("原本", encoding="utf-8")
        self.write("sources/a.md", page("source", "A", raw="../raw/a.md"))      # wiki のルートから
        self.write("sources/b.md", page("source", "B", raw="raw/a.md"))         # wiki の親から（ひな形）
        self.write("sources/c.md", page("source", "C", raw="../raw/論文c"))     # ディレクトリ
        self.write("sources/d.md", page("source", "D", raw="local.txt"))        # ページのディレクトリから
        self.write("sources/e.md", page("source", "E", raw="../raw/ない.md"))
        self.write("sources/f.md", page("source", "F", raw=["../raw/a.md", "raw/ない.pdf"]))
        self.write("concepts/g.md", page("concept", "G", raw="../raw/ない.md"))  # source でなければ見ない
        findings = self.run_lint()
        self.assertEqual(by_path(findings["missing_raw"]), [
            {"path": "sources/e.md", "raw": "../raw/ない.md", "absolute": False},
            {"path": "sources/f.md", "raw": "raw/ない.pdf", "absolute": False},
        ])
        self.assertIn("raw: ../raw/ない.md", wiki_lint.render_text(findings))

    def test_absolute_paths_and_urls(self):
        pdf = self.base / "My Books" / "日本語の資料 #1.pdf"
        pdf.parent.mkdir()
        pdf.write_bytes(b"%PDF-1.7")
        gone = (self.base / "My Books" / "消えた.pdf").as_posix()   # rag が返す / 区切りの絶対パス
        self.write("sources/a.md", page("source", "A", raw=pdf.as_posix()))
        self.write("sources/b.md", page("source", "B", raw=gone))
        self.write("sources/c.md", page("source", "C", raw="https://example.com/a.pdf"))
        self.write("sources/d.md", page("source", "D", raw="file:///nowhere/a.pdf"))
        # Windows のドライブのパスは URL として読み飛ばさない。
        self.write("sources/e.md", page("source", "E", raw="Q:/存在しない/本.pdf"))
        findings = self.run_lint()
        self.assertEqual(by_path(findings["missing_raw"]), [
            {"path": "sources/b.md", "raw": gone, "absolute": True},
            {"path": "sources/e.md", "raw": "Q:/存在しない/本.pdf", "absolute": True},
        ])


class UnknownTagsTests(LintCase):
    def setUp(self):
        super().setUp()
        self.write("sources/a.md", page("source", "A", tags=["知識表現", "Windows", "MCP", "Windows"]))
        self.write("concepts/b.md", page("concept", "B", tags=["ＡＩ", "情報検索"], sources=["a"]))
        self.write("concepts/c.md", page("concept", "C", tags=[], sources=["a"]))

    def test_reports_tags_outside_the_taxonomy(self):
        findings = self.run_lint(allowed_tags=["知識表現", "AI", " 情報検索 "])
        # 全角の「ＡＩ」は NFKC で「AI」にそろう。同じタグは 1 回だけ挙げる。
        self.assertEqual(findings["unknown_tags"], [{"path": "sources/a.md", "tags": ["Windows", "MCP"]}])
        self.assertEqual(findings["summary"]["unknown_tags"], 1)

    def test_skipped_without_taxonomy(self):
        for allowed in (None, [], ["", " "]):
            with self.subTest(allowed=allowed):
                findings = self.run_lint(allowed_tags=allowed)
                self.assertEqual(findings["unknown_tags"], [])
                self.assertIsNone(findings["summary"]["unknown_tags"])
                text = wiki_lint.render_text(findings)
                self.assertIn("タグの検査はしていない", text)
        # 検査していない項目（None）は、問題があるものとして数えない。
        empty = wiki_lint.lint([], 100, 200, [], False, 5)
        self.assertIsNone(empty["summary"]["unknown_tags"])
        self.assertIn("問題は見つからなかった。", wiki_lint.render_text(empty))


class CliTests(LintCase):
    def cli(self, *args) -> dict:
        out = subprocess.run([sys.executable, "-X", "utf8", str(SCRIPTS / "wiki_lint.py"), str(self.wiki), "--json",
                              *args], capture_output=True, timeout=120, env={**os.environ, "PYTHONUTF8": "1"})
        self.assertEqual(out.returncode, 0, out.stderr.decode("utf-8", "replace"))
        return json.loads(out.stdout.decode("utf-8"))

    def test_allowed_tags_and_index(self):
        self.write("sources/a.md", page("source", "A", tags=["知識表現", "Claude Code"]))
        self.write("concepts/b.md", page("concept", "B", sources=["a"], body="[[a]]"))
        self.write("index.md", "## シンセシス\n\n- [[a]]\n- [[b]]\n")
        self.assertIsNone(self.cli()["summary"]["unknown_tags"])
        self.assertIsNone(self.cli("--allowed-tags", "")["summary"]["unknown_tags"])
        result = self.cli("--allowed-tags", "知識表現, AIエージェント")
        self.assertEqual(result["unknown_tags"], [{"path": "sources/a.md", "tags": ["Claude Code"]}])
        self.assertEqual([f["link"] for f in result["index_type_mismatch"]], ["a", "b"])
        # MCP のツールと同じく、関数を直接呼んだ結果と一致する。
        direct = json.loads(json.dumps(self.run_lint(allowed_tags=["知識表現", "AIエージェント"]),
                                       default=str, ensure_ascii=False))
        self.assertEqual(result, direct)


if __name__ == "__main__":
    unittest.main(verbosity=2)
