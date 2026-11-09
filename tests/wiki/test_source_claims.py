"""ソースの要約ページの `## 主張と行き先`（wiki 0.8.0、ADR-0015 の段階 2）の規定の試験。

段階 2 は記録だけで、スクリプトは変えず、取り込みの手順書とひな形だけを改める。
この試験は、手順書、ページの規約、`SCHEMA.md` のひな形、ページのひな形の 4 つが同じ形を示していること、
作例の表が規定どおりの形で lint を通ること、`init_wiki.py --upgrade` が新しいセクションを案内することを確かめる。
段階 3 の規定（`kind: "claim"`、行き先どおりにページを更新させる規定）が混ざっていないことも確かめる。

実行（標準ライブラリだけで動く）:
    python -X utf8 -m unittest tests/wiki/test_source_claims.py -v
"""
from __future__ import annotations

import re
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
SKILL = ROOT / "info-hive-wiki/skills/info-hive"
sys.path.insert(0, str(SKILL / "scripts"))

import init_wiki  # noqa: E402
import wiki_lint  # noqa: E402

INGEST = SKILL / "references/ingest-workflow.md"
CONVENTIONS = SKILL / "references/page-conventions.md"
SCHEMA = SKILL / "assets/SCHEMA.md.template"
PAGE = SKILL / "assets/page.md.template"
DOCS = (INGEST, CONVENTIONS, SCHEMA, PAGE)

HEADING = "## 主張と行き先"
HEADER = "| 候補 | 主張と成り立つ条件 | 根拠の位置 | 行き先 | 理由 |"
DESTINATIONS = ("create", "update", "source_only")
WIKILINK = re.compile(r"\[\[([^\]]+)\]\]")


def read(path: Path) -> str:
    return path.read_text(encoding="utf-8")


def cells(line: str) -> list[str]:
    """表の 1 行をセルに分ける。wikilink の別名の `|` も区切りとして数える（Markdown の表と同じ）。"""
    return [c.strip() for c in line.strip().strip("|").split("|")]


def tables(text: str) -> list[list[list[str]]]:
    """HEADER で始まる表を、本文の行（区切りの行を除く）のセルの並びとして返す。"""
    found = []
    lines = text.splitlines()
    for i, line in enumerate(lines):
        if line.strip() != HEADER:
            continue
        rows = []
        for row in lines[i + 2:]:
            if not row.strip().startswith("|"):
                break
            rows.append(cells(row))
        found.append(rows)
    return found


def example_section(text: str) -> str:
    """手順書の作例（```markdown のコードブロックの中の `## 主張と行き先` の節）を取り出す。"""
    match = re.search(r"```markdown\n(## 主張と行き先\n.*?)```", text, re.S)
    assert match, "手順書に作例のコードブロックがない"
    return match.group(1)


class DocumentsAgreeTests(unittest.TestCase):
    def test_heading_header_and_values_in_every_document(self):
        for path in DOCS:
            text = read(path)
            with self.subTest(path=path.name):
                self.assertIn(HEADING, text)
                self.assertIn(HEADER, text)
                for value in DESTINATIONS:
                    self.assertIn(f"`{value}`", text)

    def test_section_comes_right_before_related_pages(self):
        # 規約は `## 関係するページ` を最後のセクションにしている。その直前に置く。
        headings = [line for line in read(PAGE).splitlines() if line.startswith("## ")]
        self.assertEqual(headings[-2:], [HEADING, "## 関係するページ"])

    def test_ingest_step_7b_sits_between_steps_7_and_8(self):
        steps = [line for line in read(INGEST).splitlines() if line.startswith("## 手順")]
        names = [s.split(":")[0] for s in steps]
        i = names.index("## 手順 7b")
        self.assertEqual(names[i - 1:i + 2], ["## 手順 7", "## 手順 7b", "## 手順 8"])

    def test_records_only(self):
        # 段階 2 は記録だけ。表のためにページを作ったり更新したりしないと、4 つとも書いている。
        for path in (INGEST, CONVENTIONS, SCHEMA):
            with self.subTest(path=path.name):
                self.assertIn("表のためにページを作ったり更新したりしない", read(path))

    def test_no_stage_3_rules(self):
        # 段階 3 の `kind: "claim"` と claim の `status` は、PoC に合格するまで入れない。
        pattern = re.compile(r"kind:\s*\"?claim|`claim`")
        for path in [*DOCS, ROOT / "info-hive-wiki/commands/ingest.md", SKILL / "SKILL.md"]:
            with self.subTest(path=path.name):
                self.assertIsNone(pattern.search(read(path)))


class ExampleTableTests(unittest.TestCase):
    def rows(self, text: str) -> list[list[str]]:
        found = tables(text)
        self.assertEqual(len(found), 1)
        self.assertTrue(found[0])
        return found[0]

    def check_rows(self, rows: list[list[str]]):
        ids = []
        for row in rows:
            with self.subTest(row=row[0]):
                # 5 列。表の中で `[[a|b]]` を使うと 6 列以上になり、ここで見つかる。
                self.assertEqual(len(row), 5, row)
                candidate, claim, evidence, destination, reason = row
                ids.append(candidate)
                self.assertRegex(candidate, r"^c\d+$")
                self.assertTrue(claim and evidence and reason)
                self.assertIn(destination.strip("`"), DESTINATIONS)
                self.assertTrue(destination.startswith("`") and destination.endswith("`"))
                if destination.strip("`") in ("create", "update"):
                    self.assertRegex(reason, WIKILINK.pattern)
        self.assertEqual(len(ids), len(set(ids)))

    def test_ingest_example(self):
        rows = self.rows(example_section(read(INGEST)))
        self.check_rows(rows)
        # 作例は 3 つの値をすべて示す。
        self.assertEqual({r[3].strip("`") for r in rows}, set(DESTINATIONS))

    def test_page_template_example(self):
        self.check_rows(self.rows(read(PAGE)))

    def test_alias_wikilink_breaks_the_table(self):
        # 規約が表の中で別名を禁じている理由。`|` が列の区切りになる。
        row = cells("| c1 | 主張 | 冒頭 | `update` | [[消費税|税]] に足した |")
        self.assertEqual(len(row), 6)


class UpgradeMarkerTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory(ignore_cleanup_errors=True)
        self.addCleanup(self.temp.cleanup)

    def test_template_has_no_gaps(self):
        self.assertEqual(init_wiki.detect_schema_gaps(SCHEMA), [])

    def test_schema_without_section_is_reported(self):
        text = read(SCHEMA)
        start = text.index("## Claim destinations\n")
        end = text.index("\n## ", start + 1) + 1
        old = Path(self.temp.name) / "SCHEMA.md"
        old.write_text(text[:start] + text[end:], encoding="utf-8")
        gaps = init_wiki.detect_schema_gaps(old)
        self.assertEqual([(g["marker"], g["version"]) for g in gaps], [("## Claim destinations", "0.8.0")])
        self.assertIn(gaps[0]["anchor"], text)


class ExamplePassesLintTests(unittest.TestCase):
    """手順書の作例を source のページに入れ、lint が新しい指摘を出さないことを確かめる。"""

    def setUp(self):
        self.temp = tempfile.TemporaryDirectory(ignore_cleanup_errors=True)
        self.addCleanup(self.temp.cleanup)
        self.wiki = Path(self.temp.name) / "wiki"
        (Path(self.temp.name) / "raw").mkdir()
        (Path(self.temp.name) / "raw/消費税の説明会-2025.md").write_text("# 消費税の説明会\n", encoding="utf-8")
        for d in ("sources", "concepts", "entities", "synthesis"):
            (self.wiki / d).mkdir(parents=True)

    def write(self, rel: str, text: str):
        (self.wiki / rel).write_text(text, encoding="utf-8")

    def test_example_source_page(self):
        section = example_section(read(INGEST))
        targets = sorted({link for row in tables(section)[0] for link in WIKILINK.findall(row[4])})
        self.assertEqual(targets, ["インボイス制度", "消費税", "軽減税率"])
        fm = ['type: "{}"', 'title: "{}"', 'tags: ["税制"]', "created: 2026-11-09", "updated: 2026-11-09"]
        source = "\n".join([
            "---", fm[0].format("source"), fm[1].format("消費税の説明会 2025"), 'authors: ["税務署"]',
            'raw: "raw/消費税の説明会-2025.md"', "ingested: 2026-11-09", *fm[2:], "---", "",
            "# 消費税の説明会 2025", "", "## 主な主張", "", "軽減税率とインボイス制度の要点。", "",
            section.rstrip("\n"), "",
            "## 関係するページ", "", *[f"- [[{t}]]" for t in targets], "",
        ])
        self.write("sources/消費税の説明会-2025.md", source)
        for t in targets:
            self.write(f"concepts/{t}.md", "\n".join([
                "---", fm[0].format("concept"), fm[1].format(t), *fm[2:4],
                'sources: ["消費税の説明会-2025"]', fm[4], "---", "", f"# {t}", "",
                "出典は [[消費税の説明会-2025]]。", "",
            ]))
        pages = wiki_lint.collect_pages(self.wiki)
        findings = wiki_lint.lint(pages, 100, 200, list(wiki_lint.DEFAULT_REQUIRED_FM), False, 5,
                                  index_entries=wiki_lint.collect_index_entries(self.wiki), allowed_tags=["税制"])
        # 提案（suggested_pages）のほかに、指摘が 1 件もない。表の wikilink も解決し、大きさも上限の内である。
        checked = [k for k, v in findings.items() if isinstance(v, list) and k != "suggested_pages"]
        self.assertIn("broken_links", checked)
        self.assertIn("oversized_soft", checked)
        for key in checked:
            with self.subTest(key=key):
                self.assertEqual(findings[key], [], findings[key])
        source_page = next(p for p in pages if p["slug"] == "消費税の説明会-2025")
        self.assertEqual(sorted(set(source_page["links"])), targets)


if __name__ == "__main__":
    unittest.main(verbosity=2)
