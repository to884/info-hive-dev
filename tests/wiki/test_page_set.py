"""wiki のページの集合とリンクの規則（wiki_pages.py、wiki 0.9.0）の試験。

設計は `docs/plans/wiki-page-set-and-links-2026-11-09.md`、決定は ADR-0010 の決定の 1 と 3 にある。
lint、検索、統計、グラフが同じページの集合を使い、コードの中の `[[...]]` を数えないことを確かめる。
グラフの試験は PyYAML がなければ飛ばす。

実行（標準ライブラリだけで動く。グラフも確かめるときは PyYAML を入れる）:
    python -X utf8 -m unittest tests/wiki/test_page_set.py -v
    uv run --python 3.12 --with pyyaml==6.0.3 python -X utf8 -m unittest tests/wiki/test_page_set.py -v
"""
from __future__ import annotations

import contextlib
import importlib
import io
import json
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
SCRIPTS = ROOT / "info-hive-wiki/skills/info-hive/scripts"
sys.path.insert(0, str(SCRIPTS))

import wiki_lint  # noqa: E402
import wiki_pages  # noqa: E402
import wiki_search  # noqa: E402
import wiki_stats  # noqa: E402

try:
    import yaml  # noqa: F401
    import wiki_graph_extract  # noqa: E402
except (ImportError, SystemExit):
    wiki_graph_extract = None


def page(title: str, body: str = "") -> str:
    return "\n".join([
        "---", 'type: "concept"', f'title: "{title}"', 'tags: ["知識表現"]',
        "created: 2026-11-09", "updated: 2026-11-09", "---", "", body or f"# {title}", "",
    ])


# ページとして数えるもの
PAGES = [
    "concepts/a.md",
    "concepts/b.md",
    "entities/c.md",
    "top.md",
    "notes/README.md",       # 最上位でない README.md はページ
    "notes/assets/d.md",     # 最上位でない assets/ はページ
    "concepts/.NET/interop.md",  # 利用者が名付けた . で始まるディレクトリはページ（名前で除くものだけ除く）
    ".archive/old.md",
]
# ページとして数えないもの
NOT_PAGES = [
    "SCHEMA.md", "index.md", "log.md", "README.md",
    "indexes/concepts.md", "graph/README.md", "raw/x.md", "assets/x.md",
    ".evolution/x.md", ".wiki-cache/x.md", "concepts/.hidden.md",
]


class Wiki(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory(ignore_cleanup_errors=True)
        self.addCleanup(self.temp.cleanup)
        self.wiki = Path(self.temp.name) / "wiki"
        self.wiki.mkdir()

    def write(self, rel: str, text: str) -> Path:
        path = self.wiki / rel
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(text, encoding="utf-8", newline="\n")
        return path

    def quiet(self, fn, *args):
        with contextlib.redirect_stderr(io.StringIO()):
            return fn(*args)


class PageSetTests(Wiki):
    def setUp(self):
        super().setUp()
        for rel in PAGES + NOT_PAGES:
            self.write(rel, page(Path(rel).stem))

    def test_is_page_path(self):
        for rel in PAGES:
            self.assertTrue(wiki_pages.is_page_path(rel), rel)
        for rel in NOT_PAGES:
            self.assertFalse(wiki_pages.is_page_path(rel), rel)
        self.assertFalse(wiki_pages.is_page_path("concepts/a.txt"))
        # Windows の rglob("*.md") は Upper.MD も返す。0.8.0 までもページだったので、拡張子の大小は問わない。
        self.assertTrue(wiki_pages.is_page_path("concepts/Upper.MD"))
        self.assertTrue(wiki_pages.is_page_path("concepts\\a.md"))

    def test_iter_page_files(self):
        found = [p.relative_to(self.wiki).as_posix() for p in wiki_pages.iter_page_files(self.wiki)]
        self.assertEqual(found, sorted(PAGES))

    def test_index_signature_sees_upper_case_extension(self):
        """MCP の索引の変更の印も、拡張子が .MD のページを含める（Linux でも .MD の変更に気づく）。"""
        try:
            import wiki_index
        except ImportError:
            self.skipTest("wiki_index の依存（numpy など）がない")
        before = wiki_index.stat_signature(self.wiki)
        self.write("concepts/New.MD", page("New"))
        self.assertNotEqual(wiki_index.stat_signature(self.wiki), before)

    def test_upper_case_extension(self):
        """拡張子が .MD のページも、どの OS でも走査で拾う（Linux の rglob("*.md") は拾わない）。"""
        self.write("concepts/Upper.MD", page("Upper"))
        found = [p.relative_to(self.wiki).as_posix() for p in wiki_pages.iter_page_files(self.wiki)]
        self.assertIn("concepts/Upper.MD", found)
        self.assertEqual(wiki_stats.compute_stats(self.wiki)["pages"], len(PAGES) + 1)

    def test_lint_search_stats_graph_agree(self):
        expected = sorted(PAGES)
        lint_set = sorted(p["rel_path"] for p in wiki_lint.collect_pages(self.wiki))
        search_set = sorted(p["rel_path"] for p in self.quiet(wiki_search.collect_pages, self.wiki))
        self.assertEqual(lint_set, expected)
        self.assertEqual(search_set, expected)
        self.assertEqual(wiki_stats.compute_stats(self.wiki)["pages"], len(expected))
        findings = wiki_lint.lint(wiki_lint.collect_pages(self.wiki), 100, 200, [], False, 5)
        self.assertEqual(findings["summary"]["total_pages"], len(expected))
        if wiki_graph_extract is not None:
            graph_set = sorted(p["rel_path"] for p in wiki_graph_extract.collect_pages(self.wiki))
            self.assertEqual(graph_set, expected)


CODE_BODY = """# 例

本文の [[a]] は数える。

インラインのコード `[[code-span]]` と ``二重の `[[double]]` コード`` は数えない。
行をまたぐコード `[[multi
line]]` も数えない。
エスケープしたバッククォート \\`[[escaped]]\\` の中は、コードではないので数える。

```markdown
[[fence-backtick]]
```

~~~
[[fence-tilde]]
~~~

> 引用の中のフェンス
> ```
> [[fence-quote]]
> ```
> 引用のフェンスの外の [[b]] は数える。

- リストの中のフェンス
  ```
  [[fence-list]]
  ```

最後に [[c|別名]] も数える。
"""
CODE_LINKS = ["a", "escaped", "b", "c"]

# (本文, 拾うリンク)。閲覧の markdown-it（commonmark、html は無効、表は有効）と同じ結果になる。
# 前半は、設計の敵対的レビュー（docs/agent-runs/2026-11-09-wiki-page-set-review/design-review-1.md）の反例。
MARKDOWN_CASES = [
    ("`start\n[[hidden]]\nend`", []),                                   # 行をまたぐコードスパン
    ("    [[hidden]]", []),                                             # 字下げのコードブロック
    ("```\n[[hidden1]]\n> ```\n[[hidden2]]\n```\n[[visible]]", ["visible"]),  # フェンスの中の > ```
    ("- - ```\n    [[hidden]]\n    ```\n[[v]]", ["v"]),                 # 入れ子のリストの中のフェンス
    ("````\n```\n# heading\n[[entity]]\n````", []),                     # 4 連の中の 3 連
    ("\\`[[visible]]`", ["visible"]),                                   # escape したバッククォート
    ("text\n    [[lazy]]", ["lazy"]),                                   # 段落の続きの字下げはコードではない
    ("> ```\n> [[q]]\n[[after]]", ["after"]),                           # 引用が終わるとフェンスも閉じる
    ("> a\n[[lazy]]", ["lazy"]),                                        # 引用の段落の遅延継続
    ("- a\n\n      [[code-in-item]]\n- b [[b]]", ["b"]),                # 項目の中の字下げのコード
    ("1. x\n   ```\n   [[c]]\n   ```\n   [[d]]", ["d"]),
    ("| a | b |\n| - | - |\n| [[t]] | `[[u]]` |", ["t"]),               # 表
    ("~~~\n[[t1]]\n~~~~\n[[t2]]", ["t2"]),
    ("``a ` [[x]] ``", []),
    ("\t[[tab-code]]", []),
    ("> - ```\n>   [[nest]]\n> ```\n[[out]]", ["out"]),
    ("para\n```\n[[fence-after-para]]\n```", []),
    ("text\n2. [[not-item]]", ["not-item"]),                            # 1 以外の番号は段落を割り込めない
    ("1. \n\n\n    x [[a]]", []),                                       # 空の項目は空行で終わる
    ("``\n- \n[[a]]``", ["a"]),                                         # Setext の見出しの下線で段落が終わる
    ("\\[\\[esc]]", ["esc"]),                                           # escape した角括弧は外して読む
    ("[[a\\|b]] と \\\\[[c]]", ["a", "c"]),
    ("[[a]] `x` [[b]]", ["a", "b"]),                                    # コードスパンが文字のかたまりを分ける
    ("\\[\\[ ```[[a]] ``` x [[b]]", ["b"]),
    # 実装の敵対的レビュー（impl-review-1.md）の反例
    ("- - -\n    [[entity]]", []),                                      # 区切り線はリストより先に見る
    ("* * *\n    [[entity]]", []),
    ("| ` | [[a]] | ` |\n| --- | --- | --- |", ["a"]),                   # コードスパンは表のセルをまたがない
    ("| A | B |\n| --- | --- |\n| ` | [[a]] |\n| ` | [[b]] |", ["a", "b"]),
    ("説明\n　\n    [[visible]]", ["visible"]),                     # 全角空白の行は空行ではない
    ("説明\n \n    [[visible]]", ["visible"]),
    ('[ref]: https://example.com "[[hidden]]"\n\n[[visible]]', ["visible"]),  # 参照リンクの定義
    ('[ref]: https://example.com\n  "[[hidden]]"\n[[visible]]', ["visible"]),
    ("[[R&amp;D]]", ["R&D"]),                                           # 文字参照は元の文字に戻す
    ("&#91;&#91;a]]", ["a"]),
    ("[[a&notit;]]", ["a&notit;"]),                                     # 正式な名前でないものは戻さない
    ("\\&amp; [[x&#x26;y]]", ["x&y"]),
    ("intro\n| a | b |\n| - | - |\n| [[c]] | d | [[extra]] |", ["c"]),  # 列の数を超えるセルは描かれない
    ("a | b\n--- | ---\n`x` | [[y]]", ["y"]),
    # 実装の 2 回目の敵対的レビュー（impl-review-2.md）の反例と、行の種類を組み合わせた比べ方で見つかった形
    ("| A | B |\n| --- | --- |\n    [[entity]]", []),                    # 表は字下げのコードで終わる
    ('[ref]: https://example.com\n  "タイトル\n  [[hidden]]\n  続き"\n[[visible]]', ["visible"]),  # 複数行のタイトル
    ("2. y\n[[s]]`\n2. y\n| [[a]] | `x` |", ["s", "a"]),               # 外側の項目を終わらせる印に制限はない
    ("1. x\n- \n[ref]: u \"[[t]]\"", []),
    ("|---|\n|---|\n　\n    [[code]]", ["code"]),                  # 表は全角空白だけの行でも終わる
    ("x\n---\n[[a]]", ["a"]),
    ("[r]: https://example.com\n\n# H\n[[entity]][r]", []),             # 参照リンクの文字（impl-review-5.md）
    ("[a]: javascript:x\n[[v]]", ["v"]),                               # 行き先が許されない定義は段落になる
    # 実装の 3 回目の敵対的レビュー（impl-review-3.md）の反例と、そのあとの比べ方で見つかった形
    ("- 分類 | 説明\n--- | ---\n    [[entity]]", []),                   # 表は引用やリストより先に見る
    ("> 分類 | 説明\n--- | ---\n    [[entity]]", []),
    ('[ref]: <javascript&#58;x> "[[visible]]"', ["visible"]),           # 行き先は戻してから調べる
    ('[ref]: javascript\\:x "[[visible]]"', ["visible"]),
    ("- 分類 | 説明\n- a | b\n--- | ---\n    [[code]]\n  [[cont]]", ["code", "cont"]),  # 同じリストの次の項目
    ("説明 `\n#　コード中の行\n[[entity]]\n終了`", []),             # # のあとが全角空白の行は見出しではない
]


class LinkTests(Wiki):
    def test_extract_wikilinks(self):
        self.assertEqual(wiki_pages.extract_wikilinks(CODE_BODY), CODE_LINKS)

    def test_markdown_cases(self):
        for body, expected in MARKDOWN_CASES:
            with self.subTest(body=body):
                self.assertEqual(wiki_pages.extract_wikilinks(body), expected)

    def test_split_sections_ignores_headings_in_code(self):
        body = "前書き\n````\n```\n# 見出しではない\n[[entity]]\n````\n# 本当の見出し\n本文 [[x]]\n"
        sections = wiki_search.split_sections("T", body)
        self.assertEqual([s["heading_path"] for s in sections], [[], ["本当の見出し"]])
        # 矛盾の候補探し（wiki_decide）は、セクションの本文からリンクを拾う。
        self.assertEqual([wiki_pages.extract_wikilinks(s["text"]) for s in sections], [[], ["x"]])

    def test_section_text_same_as_080(self):
        """コードも見出しの変化もない本文では、セクションの文字列が 0.8.0（splitlines）と同じになる。
        変わると、変わっていないページまで検索の埋め込みを作り直すことになる。"""
        cases = {
            "# T\n\ntext\n": ["", "\ntext"],
            "a\n\n": ["a\n"],
            "x\r\n# H\r\ny\r\n": ["x", "y"],
            "# A\nb\n\n\n": ["", "b\n\n"],
        }
        for body, texts in cases.items():
            with self.subTest(body=body):
                self.assertEqual([s["text"] for s in wiki_search.split_sections("T", body)], texts)

    def test_contradiction_pairs_ignore_code(self):
        """コードの中でしかエンティティを指していない 2 ページは、矛盾の候補にならない。"""
        import wiki_decide
        entity = "\n".join(["---", 'type: "entity"', 'title: "E"', 'tags: ["知識表現"]',
                            "created: 2026-11-09", "updated: 2026-11-09", "---", "", "# E", ""])
        self.write("entities/entity.md", entity)
        code_only = "- - -\n    [[entity]]\n\n````\n```\n# 見出し\n[[entity]]\n````\n"
        self.write("concepts/a.md", page("a", code_only))
        self.write("concepts/b.md", page("b", code_only))
        self.assertEqual(self.quiet(wiki_decide.contradiction_pairs, self.wiki, 10), [])
        self.write("concepts/b.md", page("b", "本文で [[entity]] を指す。"))
        self.write("concepts/c.md", page("c", "こちらも [[entity]] を指す。"))
        pairs = self.quiet(wiki_decide.contradiction_pairs, self.wiki, 10)
        self.assertTrue(pairs)
        self.assertEqual({p[0] for p in pairs}, {"E"})   # 組の先頭はエンティティのタイトル

    def test_extract_normalizes(self):
        nfd = "ガ"  # 「ガ」の NFD
        self.assertEqual(wiki_pages.extract_wikilinks(f"[[ {nfd} ]]"), ["ガ"])

    def test_lint_search_stats_graph_use_same_links(self):
        self.write("concepts/a.md", page("a"))
        self.write("concepts/b.md", page("b"))
        self.write("concepts/c.md", page("c"))
        self.write("concepts/x.md", page("x", CODE_BODY))
        lint_pages = {p["slug"]: p for p in wiki_lint.collect_pages(self.wiki)}
        search_pages = {p["slug"]: p for p in self.quiet(wiki_search.collect_pages, self.wiki)}
        self.assertEqual(lint_pages["x"]["links"], CODE_LINKS)
        self.assertEqual(search_pages["x"]["links"], CODE_LINKS)
        self.assertEqual(wiki_stats.compute_stats(self.wiki)["links"], len(CODE_LINKS))
        if wiki_graph_extract is not None:
            graph_pages = {p["slug"]: p for p in wiki_graph_extract.collect_pages(self.wiki)}
            self.assertEqual(graph_pages["x"]["links"], CODE_LINKS)

    def test_code_links_are_not_broken_links(self):
        self.write("concepts/a.md", page("a"))
        self.write("concepts/b.md", page("b"))
        self.write("concepts/c.md", page("c"))
        self.write("concepts/x.md", page("x", CODE_BODY))
        findings = wiki_lint.lint(wiki_lint.collect_pages(self.wiki), 100, 200, [], False, 5)
        self.assertEqual(sorted(f["to"] for f in findings["broken_links"]), ["escaped"])

    def test_old_parse_cache_is_rebuilt(self):
        """links の中身が変わったので、古い形式のキャッシュは読み捨てて解析し直す。"""
        body = "`[[code-span]]` と [[a]]\n````\n```\n# 見出しではない\n````\n# 本当の見出し\n本文\n"
        self.write("concepts/x.md", page("x", body))
        cache = self.wiki / ".wiki-cache" / "search-index.json"
        fresh = self.quiet(wiki_search.collect_pages, self.wiki, cache)
        payload = json.loads(cache.read_text(encoding="utf-8"))
        self.assertEqual(payload["schema"], wiki_search.PARSE_CACHE_SCHEMA)
        # 古い形式のキャッシュに、0.8.0 の解析が作る links とセクション（コードの中の見出しで分けたもの）を書いておく。
        payload["schema"] = wiki_search.PARSE_CACHE_SCHEMA - 1
        entry = payload["files"]["concepts/x.md"]
        entry["links"] = ["code-span", "a"]
        entry["sections"] = [{"heading_path": [], "level": 0, "text": "古い"},
                             {"heading_path": ["見出しではない"], "level": 1, "text": "古い"}]
        cache.write_text(json.dumps(payload, ensure_ascii=False), encoding="utf-8")
        pages = self.quiet(wiki_search.collect_pages, self.wiki, cache)
        page_x = next(p for p in pages if p["slug"] == "x")
        fresh_x = next(p for p in fresh if p["slug"] == "x")
        self.assertEqual(page_x["links"], ["a"])
        headings = [s["heading_path"] for s in fresh_x["sections"]]
        self.assertEqual(headings, [[], ["本当の見出し"]])
        self.assertEqual([s["heading_path"] for s in page_x["sections"]], headings)
        self.assertEqual([s["text"] for s in page_x["sections"]], [s["text"] for s in fresh_x["sections"]])
        self.assertEqual([s["links"] for s in page_x["sections"]], [s["links"] for s in fresh_x["sections"]])

    def test_parse_cache_is_rebuilt_when_parser_changes(self):
        """同梱した解析器が変わると、キャッシュの links とセクションを作り直す。"""
        self.write("concepts/x.md", page("x", "`[[code]]` と [[a]]"))
        cache = self.wiki / ".wiki-cache" / "search-index.json"
        self.quiet(wiki_search.collect_pages, self.wiki, cache)
        payload = json.loads(cache.read_text(encoding="utf-8"))
        self.assertEqual(payload["parser"], wiki_pages.PARSER_ID)
        payload["parser"] = "markdown-it-py 0.0.0 / mdurl 0.0.0"
        payload["files"]["concepts/x.md"]["links"] = ["code", "a"]
        cache.write_text(json.dumps(payload, ensure_ascii=False), encoding="utf-8")
        pages = self.quiet(wiki_search.collect_pages, self.wiki, cache)
        self.assertEqual([p["links"] for p in pages if p["slug"] == "x"], [["a"]])


class VendoredParserTests(unittest.TestCase):
    """wiki_pages は、同梱した markdown-it-py（_vendor/）で本文を読む。閲覧の PoC と同じ版であること。"""

    def test_uses_vendored_markdown_it(self):
        vendor = SCRIPTS / "_vendor"
        self.assertEqual(wiki_pages.markdown_it.__version__, wiki_pages.MARKDOWN_IT_VERSION)
        self.assertEqual(Path(wiki_pages.markdown_it.__file__).resolve().parent.parent, vendor.resolve())
        for name in ("markdown-it-py.LICENSE", "markdown-it.LICENSE", "mdurl.LICENSE"):
            self.assertTrue((vendor / "licenses" / name).is_file(), name)

    def test_same_version_as_browse_poc(self):
        gen = (ROOT / "poc/browse/gen.py").read_text(encoding="utf-8")
        self.assertIn(f"markdown-it-py=={wiki_pages.MARKDOWN_IT_VERSION}", gen)

    def test_foreign_modules_are_replaced(self):
        """別の場所の markdown_it と mdurl が先に読み込まれていても、同梱したものに替える。"""
        import importlib
        import types
        names = ("markdown_it", "mdurl", "wiki_pages")
        saved = {k: v for k, v in sys.modules.items() if k.split(".")[0] in names}
        try:
            for k in saved:
                del sys.modules[k]
            fake = types.ModuleType("mdurl")
            # _vendor と同じ文字列で始まる別のディレクトリ（_vendor_old/）も、同梱ではない。
            fake.__file__ = str(SCRIPTS / "_vendor_old" / "mdurl" / "__init__.py")
            fake.__version__ = "9.9.9"
            sys.modules["mdurl"] = fake
            reloaded = importlib.import_module("wiki_pages")
            self.assertIn((SCRIPTS / "_vendor").resolve(), Path(sys.modules["mdurl"].__file__).resolve().parents)
            self.assertEqual(reloaded.extract_wikilinks("[[a]] `[[b]]`"), ["a"])
        finally:
            for k in [k for k in sys.modules if k.split(".")[0] in names]:
                del sys.modules[k]
            sys.modules.update(saved)

    def test_code_version_includes_vendor(self):
        """同梱したファイルだけを変えても、MCP サーバーの版が変わる（動いているサーバーが入れ替わる）。"""
        import importlib
        import shutil
        common = importlib.import_module("wiki_mcp_common")
        with tempfile.TemporaryDirectory(ignore_cleanup_errors=True) as temp:
            copy = Path(temp) / "scripts"
            shutil.copytree(SCRIPTS, copy, ignore=shutil.ignore_patterns("__pycache__"))
            original = common.SCRIPTS
            try:
                common.SCRIPTS = copy
                before = common.code_version()
                target = copy / "_vendor" / "mdurl" / "_url.py"
                target.write_text(target.read_text(encoding="utf-8") + "\n# changed\n", encoding="utf-8")
                self.assertNotEqual(common.code_version(), before)
            finally:
                common.SCRIPTS = original


class SectionTests(unittest.TestCase):
    """セクションの links（判定レイヤーの矛盾の候補探しが使う）を集めると、本文全体（分け目の見出しの中を除く）と
    同じリンクになること。セクションの境目が、見出しの判定（heading_line_mask）と一致すること。
    """

    TOKENS = ["[[a]]", "`", "``", "```", "~~~", "> ", "- ", "1. ", "    ", "  ", "\n", "\n\n", "x ", "[[b]]",
              "# ", "\\", "\t", "\\[", "|", "]", "-", "===", "　", "&amp;", "&#91;", "[r]: u \"", "\"",
              "| - |", "- - -", "* * *"]

    LINE_KINDS = [
        "| A | B |", "| --- | --- |", "|---|", "a | b", "--- | ---", "| [[a]] | `x` |", "| ` | [[b]] |",
        "    [[code]]", "\t[[tab]]", "[ref]: https://example.com", '[ref]: u "[[t]]"', '  "title', "  [[mid]]",
        '  end"', "> [[q]]", ">", "> ```", "- [[li]]", "  [[cont]]", "1. x", "2. y", "- ", "```", "~~~", "````",
        "", "", "text [[p]]", "`span", "[[s]]`", "# [[h]]", "---", "===", "- - -", "* * *",
        "　", "[[R&amp;D]]", "\\[\\[e]]", "  - nested [[n]]",
        "- 分類 | 説明", "> a | b", "#　見出しでない", "# 本当 [[hh]]", '[ref]: <javascript&#58;x> "[[v]]"',
        '[ref]: javascript\\:x "[[v]]"', "説明 `", "終了`", "- a | b", "> --- | ---",
        "説明 ` # 見出し [[u2028]] 終了`",
        "[r]: https://example.com", "[[entity]][r]",
        "#", "##", "  # 字下げした見出し [[ind]]", "# A",
    ]

    def check(self, bodies) -> list[str]:
        import collections
        broken = []
        for body in bodies:
            got = collections.Counter()
            for section in wiki_search.split_sections("T", body):
                got.update(section["links"])   # 判定レイヤー（wiki_decide）が使うリンク
            sections = wiki_search.split_sections("T", body)
            splits = sum(wiki_pages.heading_line_mask(wiki_pages.split_lines(body)))
            if (got != collections.Counter(wiki_pages.extract_wikilinks(body, headings=False))
                    or len(sections) != splits + 1):
                broken.append(body)
        return broken

    def test_fixed_cases(self):
        self.assertEqual(self.check([body for body, _ in MARKDOWN_CASES] + [CODE_BODY]), [])

    def test_line_structured_bodies(self):
        import random
        rng = random.Random(20261111)
        bodies = ["\n".join(rng.choice(self.LINE_KINDS) for _ in range(rng.randint(2, 9))) for _ in range(3000)]
        self.assertEqual(self.check(bodies), [])

    def test_random_bodies(self):
        import random
        rng = random.Random(20261109)
        bodies = ["".join(rng.choice(self.TOKENS) for _ in range(rng.randint(3, 14))) for _ in range(3000)]
        self.assertEqual(self.check(bodies), [])


class CaseOnlyTests(Wiki):
    def test_files_and_dirs(self):
        found = wiki_pages.case_only_duplicates([
            "concepts/Kalman.md", "concepts/kalman.md",
            "Entities/a.md", "entities/b.md",
            "sources/x.md",
        ])
        self.assertEqual(found, [
            {"kind": "file", "paths": ["concepts/Kalman.md", "concepts/kalman.md"]},
            {"kind": "dir", "paths": ["Entities", "entities"]},
        ])

    def test_file_and_dir_are_compared_separately(self):
        """Foo.md と foo.MD/ は、閲覧の書き出しで Foo.html と foo.MD/ になり、同じ場所を取らない。"""
        self.assertEqual(wiki_pages.case_only_duplicates(["Foo.md", "foo.MD/x.md"]), [])

    def test_case_key_normalizes_after_casefold(self):
        """NFC のあとに casefold すると、NFC でなくなる組がある（ΐ と Ϊ́）。前後で NFC にそろえる。"""
        found = wiki_pages.case_only_duplicates(["concepts/ΐ.md", "concepts/Ϊ́.md"])
        self.assertEqual(len(found), 1)

    def test_normalization_only_is_not_case_only(self):
        nfd = "concepts/ガ.md"
        nfc = "concepts/ガ.md"
        self.assertEqual(wiki_pages.case_only_duplicates([nfd, nfc]), [])

    def test_lint_reports(self):
        # 大文字と小文字を区別しない OS では同じフォルダーに置けないので、ディレクトリを分けて作る。
        self.write("Concepts/a.md", page("a"))
        self.write("concepts/b.md", page("b"))
        pages = wiki_lint.collect_pages(self.wiki)
        if len({p["rel_path"].split("/")[0] for p in pages}) < 2:
            self.skipTest("このファイルシステムは大文字と小文字を区別しない")
        findings = wiki_lint.lint(pages, 100, 200, [], False, 5)
        self.assertEqual(findings["case_only_duplicates"], [{"kind": "dir", "paths": ["Concepts", "concepts"]}])
        self.assertEqual(findings["summary"]["case_only_duplicates"], 1)

    def test_lint_summary_is_zero(self):
        self.write("concepts/a.md", page("a"))
        findings = wiki_lint.lint(wiki_lint.collect_pages(self.wiki), 100, 200, [], False, 5)
        self.assertEqual(findings["case_only_duplicates"], [])
        self.assertEqual(findings["summary"]["case_only_duplicates"], 0)
        self.assertNotIn("大文字と小文字だけが違う", wiki_lint.render_text(findings))


class ReexportTests(unittest.TestCase):
    """ほかのスクリプトと試験が使う古い名前が、wiki_pages と同じものを指すこと。"""

    def test_names(self):
        for module in (wiki_lint, wiki_search):
            self.assertIs(module.resolve_link, wiki_pages.resolve_link)
            self.assertIs(module.clean_link_target, wiki_pages.clean_link_target)
            self.assertIs(module.WIKILINK_RE, wiki_pages.WIKILINK_RE)
        self.assertIs(wiki_search.extract_wikilinks, wiki_pages.extract_wikilinks)
        self.assertIs(wiki_search.build_link_index, wiki_pages.build_link_index)
        if wiki_graph_extract is not None:
            self.assertIs(wiki_graph_extract.resolve_link_slug, wiki_pages.resolve_link)

    def test_mcp_server_version_includes_wiki_pages(self):
        common = importlib.import_module("wiki_mcp_common")
        self.assertIn("wiki_pages.py", common.SERVER_FILES)


if __name__ == "__main__":
    unittest.main()
