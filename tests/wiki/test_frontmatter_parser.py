"""frontmatter のパーサー（`wiki_text.parse_frontmatter_text`）が読む YAML の書き方の試験（wiki 0.9.7）。

0.9.5 までのパーサーは、YAML としては正しいのに読まない書き方があった。字下げが 2 つでないブロックの配列、
複数行にまたがる `[...]`、引用符つきのキーとコロンの前の空白、二重引用符の中の `\\"` と `\\\\` のほかの
エスケープ、`|` と `>` のブロックのスカラーである。lint、検索、統計、取得、MCP、グラフの最上位の欄が、この
パーサーを共有する。

確かめること（設計は docs/plans/wiki-frontmatter-parser-2026-11-11.md）:
- 5 つの書き方の値が、PyYAML の BaseLoader（型に直さない）の値と等しい。
- YAML と違ってよいと決めた箇所と、読まないまま残す書き方の値が、今までと同じ。
- 規約どおりのページと、読み方を変えない書き方では、値が 0.9.5 のパーサーと等しい。
- 自分の書き手（`format_frontmatter`）が書いた値を読み戻せる。
- `unquoted_string_keys()` と `top_level_keys()` が、値の辞書と同じ行を見る。
- lint、検索、統計が、読めるようになった欄を読む。検索の古いパースキャッシュを使い続けない。

グラフの診断 `unread_field` が出なくなることは、test_graph_frontmatter_values.py で確かめる。

実行（PyYAML 6.0.3 が要る）:
    uv run --python 3.12 --with pyyaml==6.0.3 python -X utf8 -m unittest tests/wiki/test_frontmatter_parser.py -v
"""
from __future__ import annotations

import hashlib
import json
import random
import sys
import tempfile
import unittest
from argparse import Namespace
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
SCRIPTS = ROOT / "info-hive-wiki/skills/info-hive/scripts"
# 0.9.5（info-hive-wiki 426d6bf）の wiki_text.py が UNCHANGED_CASES から返した値。作り方はファイルの note にある。
GOLDEN = Path(__file__).with_name("frontmatter_parser_golden.json")
sys.path.insert(0, str(SCRIPTS))

try:
    import yaml
    HAS_YAML = True
except ImportError:
    HAS_YAML = False

import wiki_lint  # noqa: E402
import wiki_search  # noqa: E402
import wiki_stats  # noqa: E402
import wiki_text  # noqa: E402

parse = wiki_text.parse_frontmatter_text


def base(text: str):
    """PyYAML が、型に直さずに読んだ値。frontmatter の最後の行にも改行があるものとして読む。"""
    return yaml.load(text + "\n", Loader=yaml.BaseLoader)


def as_parser(text: str) -> dict:
    """BaseLoader の値を、このパーサーの決まりの形にして返す。値のないキー（`sources:`）は、空の配列になる。

    引用符で書いた空の文字列（`title: ""`）と、中身のないブロックのスカラーは、空の文字列のままである。
    値のないキーは、YAML のノードが、引用符のない空のスカラーであることで見分ける。
    """
    loader = yaml.BaseLoader(text + "\n")
    try:
        root = loader.get_single_node()
        meta = loader.construct_document(root)
    finally:
        loader.dispose()
    if isinstance(meta, dict):
        # 同じキーを 2 度書いていれば、YAML は後の値にする。後のノードで見分ける。
        last = {key_node.value: value_node for key_node, value_node in root.value}
        for key, value_node in last.items():
            if isinstance(value_node, yaml.ScalarNode) and value_node.value == "" and value_node.style is None:
                meta[key] = []
    return meta


# 読めるようになった書き方。値は BaseLoader と等しい。(frontmatter, 期待する値)
YAML_CASES = {
    "字下げのない配列": ('sources:\n- paper\n- "b, c"\ntags: ["x"]', {"sources": ["paper", "b, c"], "tags": ["x"]}),
    "字下げ 1 つの配列": ("sources:\n - a\n - b", {"sources": ["a", "b"]}),
    "字下げ 4 つの配列": ('sources:\n    - paper\n    - "b"\ntype: x', {"sources": ["paper", "b"], "type": "x"}),
    "字下げ 6 つの配列": ("sources:\n      - a", {"sources": ["a"]}),
    "配列の間の空行とコメント": ("sources: # 出典\n\n- a # 1 つ目\n# コメント\n\n- 'b''c'\nnext: 1",
                      {"sources": ["a", "b'c"], "next": "1"}),
    "配列のあとに別のキーの配列": ("sources:\n- a\ntags:\n    - b\nraw:\n  - c",
                       {"sources": ["a"], "tags": ["b"], "raw": ["c"]}),
    "日本語の別名のキーの配列": ("出典:\n- 論文\nタグ:\n    - 税制", {"出典": ["論文"], "タグ": ["税制"]}),
    "複数行の配列": ('sources: [a,\n  "b, c",  # コメント\n  d]\ntags: [x]', {"sources": ["a", "b, c", "d"], "tags": ["x"]}),
    "字下げのない閉じ括弧": ("sources: [\na,\nb\n]\ntags: [x]", {"sources": ["a", "b"], "tags": ["x"]}),
    "複数行の配列の引用符の中の記号": ('tags: ["a]",\n  "b # c", \'d,e\',\n\n  f]  # 終わり\nnext: 1',
                         {"tags": ["a]", "b # c", "d,e", "f"], "next": "1"}),
    "複数行の配列の最後のカンマ": ("tags: [a,\n  b,\n]", {"tags": ["a", "b"]}),
    # フローの中では、`,`・`[`・`]` と閉じた引用符の直後の # もコメントになる。`a#b` の # は値の一部である。
    "複数行の配列の空白のないコメント": ('a: [x,# c\n y]\nb: [# c\n x]\nc: ["x"# c\n ,y]\nd: [x# c,\n y]\ne: [x,\n y]# c',
                          {"a": ["x", "y"], "b": ["x"], "c": ["x", "y"], "d": ["x# c", "y"], "e": ["x", "y"]}),
    # コメントの中の括弧と引用符は、配列の形に関わらない。
    "コメントの中の括弧と引用符": ("a: [x, # [y]\n z]\nb: [x,  # ]\n]\nc: [x,# メモ ] \"\n y, # it's\n]",
                       {"a": ["x", "z"], "b": ["x"], "c": ["x", "y"]}),
    "引用符の空の文字列": ('title: ""\ntags: ["", \'\']\nsources:\n- ""', {"title": "", "tags": ["", ""], "sources": [""]}),
    "複数行の配列の字下げのない要素": ("urls: [\na,\n'b: c',\n]", {"urls": ["a", "b: c"]}),
    "引用符つきのキー": ('"type": x\n\'kind\': "y"\n"種類": z', {"type": "x", "kind": "y", "種類": "z"}),
    "コロンの前の空白": ('type : x\nkind  : "y"\n"title" : z\nsources :\n- a',
                  {"type": "x", "kind": "y", "title": "z", "sources": ["a"]}),
    "引用符つきのキーが後の値で置き換える": ('type: "a"\n"type": "b"', {"type": "b"}),
    "エスケープ 1 文字": ('title: "a\\tb\\nc\\rd\\0e\\af\\bg\\vh\\fi\\ej\\ k\\/l\\"m\\\\n"',
                  {"title": "a\tb\nc\rd\0e\af\bg\vh\fi\x1bj k/l\"m\\n"}),
    "エスケープ 記号": ('title: "\\N\\_\\L\\P\\\t"', {"title": "\x85\xa0\u2028\u2029\t"}),
    "エスケープ 16 進": ('title: "caf\\u00e9 \\xE9 \\U0001F600 \\u6D88\\u8CBB\\u7A0E"', {"title": "café é \U0001F600 消費税"}),
    "配列の要素のエスケープ": ('sources: ["\\u8AD6\\u6587", "a\\tb"]\ntags:\n- "\\u7A0E"',
                     {"sources": ["論文", "a\tb"], "tags": ["税"]}),
    "ブロックのスカラー literal": ("raw: |\n  a\n  b\ntitle: x", {"raw": "a\nb\n", "title": "x"}),
    "ブロックのスカラー folded": ("title: >\n  長い\n  題名\n\n  次の段落\ntype: x", {"title": "長い 題名\n次の段落\n", "type": "x"}),
    "ブロックのスカラー 末尾を除く": ("title: >-\n  a\n  b\ntype: x", {"title": "a b", "type": "x"}),
    "ブロックのスカラー 末尾を残す": ("title: |+\n  a\n\n\ntype: x", {"title": "a\n\n\n", "type": "x"}),
    "ブロックのスカラー 最後の欄": ("title: |\n  a", {"title": "a\n"}),
    "ブロックのスカラー 字下げの指定": ("title: |2\n    a\n   b\ntype: x", {"title": "  a\n b\n", "type": "x"}),
    "ブロックのスカラー 指定の順": ("a: >1-\n  x\n  y\nb: |+2\n   z\n", {"a": " x\n y", "b": " z\n\n"}),
    "ブロックのスカラー 見出しのコメント": ("title: > # コメント\n  a\ntype: x", {"title": "a\n", "type": "x"}),
    "ブロックのスカラー 深い行は折りたたまない": ("d: >\n  a\n    b\n  c\n  d", {"d": "a\n  b\nc d\n"}),
    "ブロックのスカラー 記号を含む行": ('note: |\n  - x\n  # コメントではない\n  key: "v"\n  [a,\ntype: x',
                         {"note": '- x\n# コメントではない\nkey: "v"\n[a,\n', "type": "x"}),
    "ブロックのスカラー 引用符つきのキー": ('"raw" : >-\n    raw/a.md', {"raw": "raw/a.md"}),
}

# YAML と違ってよいと決めた箇所と、読まないまま残す書き方。(frontmatter, このパーサーの値)
KEPT_CASES = {
    "同じキーの配列はつなぐ": ("sources: [a]\nsources:\n- b\n'sources': [c]", {"sources": ["a", "b", "c"]}),
    "値のないキーは空の配列": ("sources:\ntype:", {"sources": [], "type": []}),
    "入れ子は読まない": ('graph:\n  node_id: "x"\n  relationships:\n    - predicate: "p"\ntitle: "t"',
                 {"graph": [], "title": "t"}),
    "入れ子の中の同じ字下げの配列は親の要素にしない": ('graph:\n  aliases:\n  - "a"\ntitle: x', {"graph": [], "title": "x"}),
    "要素の中の入れ子は書かれた文字": ("sources:\n- [[s/p]]\n- a: 1\n  b: 2\n- c", {"sources": ["[[s/p]]", "a: 1", "c"]}),
    "空の要素": ("sources:\n  - a\n  -\n  - b", {"sources": ["a", "", "b"]}),
    "コロンのあとに空白なし": ('type:x\n"kind":y', {"type": "x", "kind": "y"}),
    "次の行に書いた値": ('title:\n  "x"\nsources:\n  [a, b]\ntype: y', {"title": [], "sources": [], "type": "y"}),
    "複数行のスカラーは 1 行目だけ": ('title: a very long\n  title\nnote: "b\n  c"', {"title": "a very long", "note": '"b'}),
    "閉じない括弧は 1 行目だけの文字列": ('tags: [a, b\ntitle: "x"\nsources: ["c"]',
                           {"tags": "[a, b", "title": "x", "sources": ["c"]}),
    "1 行目で閉じて文字が続く": ("title: [下書き] 題名\ntype: x", {"title": "[下書き] 題名", "type": "x"}),
    "閉じたあとに文字が続く": ("tags: [a,\n  b] c\ntype: x", {"tags": "[a,", "type": "x"}),
    "YAML にないエスケープは書かれた文字": ('raw: "C:\\Users\\me"\ntitle: "\\d+\\.\\d+ \\u12 \\xZZ \\U0001F60"',
                              {"raw": "C:\\Users\\me", "title": "\\d+\\.\\d+ \\u12 \\xZZ \\U0001F60"}),
    "サロゲートの対は 1 文字": ('title: "\\uD83D\\uDE00"', {"title": "\U0001F600"}),
    "対にならないサロゲートは書かれた文字": ('a: "\\uD83D"\nb: "\\uDE00\\uD83D"\nc: "\\U0000D83D\\U0000DE00"',
                             {"a": "\\uD83D", "b": "\\uDE00\\uD83D", "c": "\\U0000D83D\\U0000DE00"}),
    "U+10FFFF を超える値は書かれた文字": ('a: "\\U00110000"\nb: "\\U0010FFFF"', {"a": "\\U00110000", "b": "\U0010FFFF"}),
    # 戻せないエスケープが 1 つでもある値は、YAML としては誤りである。全体を 0.9.5 までと同じに読む。
    "戻せないエスケープがあれば値の全体を今までどおり読む": (
        'pattern: "\\d+\\n"\nraw: "C:\\Users\\new\\temp.pdf"\nlatex: "$\\theta$ と $\\sigma$"\n'
        'mixed: "a\\"b\\\\c\\q\\t"\nsurrogate: "\\uD83D\\t"\ntail: ["x\\ty", "x\\ty\\q"]',
        {"pattern": "\\d+\\n", "raw": "C:\\Users\\new\\temp.pdf", "latex": "$\\theta$ と $\\sigma$",
         "mixed": 'a"b\\c\\q\\t', "surrogate": "\\uD83D\\t", "tail": ["x\ty", "x\\ty\\q"]}),
    # ] を書き忘れたあとに、対にならない ] があっても、字下げのないキーの行は配列に取り込まない。
    "閉じない括弧のあとのキーの行は取り込まない": ("tags: [a,\ntype: source\ntitle: X]",
                               {"tags": "[a,", "type": "source", "title": "X]"}),
    # ] で終わる行は、0.9.5 までと同じに 1 行の配列として読む。行末の ] が、空白のないコメントの中、引用符の中、
    # 入れ子の括弧にあるとき、YAML は後ろの行まで続く配列として読む。
    "] で終わる行は 1 行の配列": ("a: [x,# メモ ]\n y]\nb: [# ]\n x]\nc: [x, \"y]\n z\"]\nd: [x, [y]\n ]",
                        {"a": ["x", "# メモ"], "b": ["#"], "c": ["x", '"y'], "d": ["x", "[y"]}),
    # 括弧が閉じているかは、YAML と同じく、引用符のない値の途中の ' を文字として見る。要素に分けるときは、
    # 1 行の配列と同じく、' を引用符の始まりとして読む（`[x y's, z]` と同じ値になる。YAML は 2 つの要素）。
    "引用符のない値の途中の引用符": ("a: [x y's,\n z]\nb: [x y's, z]", {"a": ["x y's, z"], "b": ["x y's, z"]}),
    "1 行の配列のあとのコメントの行は取り込まない": ("sources: [it's]\n# don't ]\ntags: [a\"b]\n# x\"]",
                                {"sources": ["it's"], "tags": ['a"b']}),
    "続きの行が字下げのないキーの形の配列は読まない": ('sources: [a,\nb: c]\ntags: [d,\n"e": f\n]\nurls: [g,\nhttps://x/y]',
                                 {"sources": "[a,", "b": "c]", "tags": "[d,", "e": "f", "urls": "[g,", "https": "//x/y]"}),
    "値の前後の Unicode の空白は除く": ("sources:\n    - \N{NO-BREAK SPACE}a\N{IDEOGRAPHIC SPACE}\n\"type\": \N{IDEOGRAPHIC SPACE}source",
                             {"sources": ["a"], "type": "source"}),
    # 全角の空白などの Unicode の空白のあとの # も、コメントにする（0.9.5 までの 1 行の値と同じ読み方）。
    # YAML は、空白とタブのあとの # だけをコメントにするので、b と #c の間が U+00A0 なら、#c は値の一部である。
    "Unicode の空白のあとの # はコメント": (
        "title: 消費税\N{IDEOGRAPHIC SPACE}# メモ\ntags: [a,\n b\N{NO-BREAK SPACE}#c\n]\nsources:\n    - b\N{NO-BREAK SPACE}#c\n"
        "aliases: [a,\n b\N{IDEOGRAPHIC SPACE}#c]",
        {"title": "消費税", "tags": ["a", "b"], "sources": ["b"], "aliases": "[a,"}),
    "行は LF だけで分ける": ("title: |\n  x\N{NEXT LINE}  y\N{LINE SEPARATOR}z", {"title": "x\N{NEXT LINE}  y\N{LINE SEPARATOR}z\n"}),
    "複数行の配列の要素の途中の空行は空白": ("k: [a,\n\n b c\n\n d]", {"k": ["a", "b c d"]}),
    "要素の続きの行は読まない": ("k:\n- a\n  b\n-\n  c\n- d", {"k": ["a", "", "d"]}),
    "一重引用符はエスケープを読まない": ("title: 'a\\tb'", {"title": "a\\tb"}),
    "引用符のない値はエスケープを読まない": ("title: a\\tb", {"title": "a\\tb"}),
    "コロンの前のタブは読まない": ("kind\t: y\ntype: x", {"type": "x"}),
    "ハイフンのあとに空白のない行は要素ではない": ("sources:\n-a\n- b", {"sources": []}),
    # 配列は、字下げのない行で、その配列の要素でないものが来たら終わる。0.9.5 までは、読まないキーの行
    # （source-url:）を挟んでも続け、別のキーの要素を取り込んでいた。YAML では、b は source-url の要素である。
    "読まないキーの行のあとの要素は取り込まない": ('sources:\n  - "a"\nsource-url:\n  - "b"\ntags:\n  - "c"\n???\n  - "d"',
                              {"sources": ["a"], "tags": ["c"]}),
    "次の行が要素でなければ、あとの要素の行も読まない": ("sources:\n  -x\n  - y\ntags:\n  junk\n  - z", {"sources": [], "tags": []}),
    "見出しでない記号は文字列": ("a: > x\nb: |x\nc: >>\nd: |0", {"a": "> x", "b": "|x", "c": ">>", "d": "|0"}),
    "要素に書いたブロックのスカラーは読まない": ("sources:\n- |\n  a\n- b", {"sources": ["|", "b"]}),
    "アンカーとタグ": ("sources: &s [a]\nraw: !!str true\nother: *s", {"sources": "&s [a]", "raw": "!!str true", "other": "*s"}),
    "単語でないキー": ('source-url: x\n"a b": y\n? c\n: d\ntype: z', {"type": "z"}),
}

# 0.9.5 のパーサーと同じ値になる書き方。規約どおりのページと、読み方を変えない書き方である。
UNCHANGED_CASES = {
    "規約どおりのページ": (
        'type: "concept"\ntitle: "消費税"\ntags: ["税制", "間接税"]\nsources: ["paper", "sources/b"]\n'
        'aliases: ["VAT", "付加価値税"]\ncreated: 2026-11-01\nupdated: 2026-11-09\ncount: 3'),
    "規約どおりのソース": (
        'type: "source"\ntitle: "題名 \\"引用\\" と \\\\ 記号"\nraw: "C:/Books/日本語の資料.pdf"\n'
        'raw_sha256: "0123abcd"\nfetched_at: "2026-11-01T10:00:00+09:00"\nauthors: ["Kingma, D.", "Ba, J."]'),
    "字下げ 2 つの配列": 'sources:\n  - "a"\n  - "b"\ntags:\n  - 税制 # コメント\n  - "c # d"\nraw:\n  - raw/a.md',
    "配列の間の空行とコメント": 'sources:\n\n  # コメント\n  - a\n\n  - b\ntype: x',
    "配列の間の読まない行": "sources:\n  - a\n  junk\n    more\n  - b\ntype: x",
    "行末に空白のある空の要素": "sources:\n  - a\n  - \n  - b",
    "引用符のない値": "type: source\ntags: [a, b]\ncreated: 2026-11-03\nflag: true\nnone: null\nnum: 007\nwhen: 2026-11-01 10:00:00",
    "コメント": 'type: source # 種類\nurl: "https://example.com/a?b=1#x" # 該当する場合\ntitle: "C# の #1"\nempty: # 値なし',
    "日本語の別名": "種類: 概念\nタイトル: 消費税\nタグ: [税制、間接税]\n出典: [a]\n作成日: 2026-11-01",
    "別名と英語のキーの両方": 'type: "concept"\n種類: 資料\nsources: ["a"]\n出典: ["b"]',
    "入れ子の graph": ('type: "entity"\ngraph:\n  node_id: "person:x"\n  aliases: ["X"]\n  relationships:\n'
                   '    - predicate: "works_at"\n      object: "company:y"\n      source: "paper"\ntitle: "x"'),
    "同じキーを 2 度": 'sources: ["a"]\nsources: ["b"]\ntitle: "x"\ntitle: "y"\ntags: [a]\ntags: b',
    "コロンのあとに空白なし": "type:source\nsources:[a]\ntitle:\t\"x\"",
    "1 行目で閉じて文字が続く": "title: [下書き] 題名\ntags: [a] # コメント\nnote: [a], [b]",
    "閉じない括弧": 'tags: [a, b\ntitle: "x"\nsources: ["c"]\nlast: [d',
    "閉じない括弧のあとの対にならない括弧": "tags: [a,\ntype: source\ntitle: X]\nurls: [g,\nhttps://x/y]",
    "YAML にないエスケープと YAML のエスケープが混ざる値": 'pattern: "\\d+\\n"\nraw: "C:\\Users\\new\\temp.pdf"\nlatex: "$\\theta$ と $\\sigma$"',
    "Unicode の空白のあとの #": "title: 消費税\N{IDEOGRAPHIC SPACE}# メモ\ntags: [a, b\N{NO-BREAK SPACE}#c]\nsources:\n  - b\N{EM SPACE}#c",
    "値の前後の Unicode の空白": "title: \N{IDEOGRAPHIC SPACE}消費税\N{NO-BREAK SPACE}\nsources:\n  - \N{NO-BREAK SPACE}a\N{IDEOGRAPHIC SPACE}\ntags: [\N{IDEOGRAPHIC SPACE}b]",
    "引用符が閉じない配列": 'tags: [a, "b]\ntitle: "x"',
    "1 行の配列のあとのコメントの行": "sources: [it's]\n# don't ]\ntags: [a\"b]\n# x\"]\nk: [- it's #w]\n  f, g]",
    "] で終わる行のあとの字下げした行": "a: [x,# メモ ]\n y]\nb: [x, \"y]\n z\"]\nc: [x, [y]\n ]",
    "入れ子の wikilink": "sources: [[sources/paper]]\nrelated: [[[a]], [[b|c]]]",
    "YAML にないエスケープ": 'raw: "C:\\Users\\me\\docs"\npattern: "\\d+\\.\\d+"\nlatex: "\\sigma \\pi \\omega"',
    "引用符": "a: 'it''s'\nb: \"x\" y\nc: 'p' q\nd: \"\"\ne: ''\nf: \"",
    "次の行に書いた値": 'title:\n  "x"\nsources:\n  [a, b]\ntype: y',
    "複数行のスカラー": 'title: a very long\n  title\nnote: "b\n  c"\ntype: y',
    "アンカー、タグ、マージキー": "base: &b {type: source}\n<<: *b\nsources: &s [a]\nraw: !!str true\nother: *s",
    "単語でないキー": "source-url: x\n? c\n: d\n- e\ntype: z",
    "全角のコロン": "タイトル：消費税\ntype: x",
    "CRLF": 'type: "concept"\r\nsources:\r\n  - "a"\r\ntags: ["x"]\r',
    "値のないキー": "type:\nkind:\nsources:\nraw:\ntitle:\ntags: []",
    "タブで字下げした要素": "sources:\n\t- a\ntype: x",
    "見出しでない記号": "a: > x\nb: |x\nc: >>\nd: -\ne: |0",
    "読めない YAML": "title: a: b\ntype: source\nsources: [true]",
    "空の frontmatter": "",
}


def golden_entry(module, text: str) -> dict:
    return {"meta": module.parse_frontmatter_text(text), "unquoted": module.unquoted_string_keys(text),
            "keys": module.top_level_keys(text)}


@unittest.skipUnless(HAS_YAML, "PyYAML が要る")
class YamlValuesTest(unittest.TestCase):
    """読めるようになった書き方の値は、決めた値で、PyYAML の BaseLoader とも等しい。"""

    def test_values(self):
        for name, (text, expected) in YAML_CASES.items():
            with self.subTest(name):
                self.assertEqual(parse(text), expected)
                self.assertEqual(as_parser(text), expected)

    def test_crlf(self):
        # 行末が CRLF でも、同じ値になる。ブロックのスカラーの値に CR を残さない。
        for name, (text, expected) in YAML_CASES.items():
            if "\\\t" in text:
                continue
            with self.subTest(name):
                self.assertEqual(parse(text.replace("\n", "\r\n")), expected)

    def test_comparison_helper_tells_missing_values_from_empty_strings(self):
        # as_parser() は、値のないキーだけを空の配列にする。引用符の空の文字列と、後から書いた値は変えない。
        self.assertEqual(as_parser('a:\nb: ""\nc:\nc: x\nd:\nd: ""\ne: x\ne:'),
                         {"a": [], "b": "", "c": "x", "d": "", "e": []})
        for text in ('k:\nk: x', 'k:\nk: ""', 'k: ""', "k:"):
            with self.subTest(text):
                self.assertEqual(parse(text), as_parser(text))

    def test_empty_block_scalar_is_an_empty_string(self):
        # 値のないキーは空の配列だが、中身のないブロックのスカラーは空の文字列である（YAML と同じ）。
        text = "a: |\nb: >-\nc: |+\n\n\nd: x"
        self.assertEqual(parse(text), {"a": "", "b": "", "c": "\n\n", "d": "x"})
        self.assertEqual(base(text), parse(text))

    def test_block_scalar_value_does_not_depend_on_position(self):
        # PyYAML に frontmatter の本文だけを渡すと、最後の欄のブロックのスカラーにだけ末尾の改行が付かない。
        # このパーサーは、最後の行にも改行があるものとして読むので、欄の位置で値が変わらない。
        self.assertEqual(parse("title: |\n  a"), {"title": "a\n"})
        self.assertEqual(parse("title: |\n  a\ntype: x")["title"], "a\n")
        self.assertEqual(yaml.load("title: |\n  a", Loader=yaml.BaseLoader), {"title": "a"})

    def test_surrogate_pairs_differ_from_pyyaml_on_purpose(self):
        # PyYAML は、\uD83D\uDE00 を対にならないサロゲート 2 つにする。UTF-8 で書き出せない。
        text = 'title: "\\uD83D\\uDE00"'
        with self.assertRaises(UnicodeEncodeError):
            base(text)["title"].encode("utf-8")
        self.assertEqual(parse(text)["title"].encode("utf-8"), "\U0001F600".encode("utf-8"))


class KeptValuesTest(unittest.TestCase):
    """YAML と違ってよいと決めた箇所と、読まないまま残す書き方（PyYAML は要らない）。"""

    def test_values(self):
        for name, (text, expected) in {**{k: v for k, v in YAML_CASES.items()}, **KEPT_CASES}.items():
            with self.subTest(name):
                self.assertEqual(parse(text), expected)

    def test_multiline_flow_equals_the_one_line_spelling(self):
        # 複数行の [...] の値は、行をつないで 1 行に書いたときの値と同じ。
        cases = ['[a,\n  "b, c",\n  d]', "[\na,\nb\n]", '[[[x]],\n [[y|z]]]', "[it's,\n fine']", '["a\n  b", c]']
        for value in cases:
            with self.subTest(value):
                joined = " ".join(line.strip() for line in value.split("\n"))
                self.assertEqual(parse("k: " + value), parse("k: " + joined))
                self.assertIsInstance(parse("k: " + value)["k"], list)

    def test_unclosed_bracket_does_not_swallow_the_following_fields(self):
        meta = parse('tags: [a, "b\ntitle: "x"\ntype: "concept"\nsources:\n- "s"')
        self.assertEqual(meta["tags"], '[a, "b')
        self.assertEqual((meta["title"], meta["type"], meta["sources"]), ("x", "concept", ["s"]))

    def test_many_unclosed_brackets_stay_fast(self):
        # 閉じない [ のたびに frontmatter の終わりまで探すと、行の数の 2 乗の時間がかかる。次のキーの行で止める。
        import time
        text = "\n".join(f"k{n}: [" for n in range(20000)) + "\n" + "\n".join(f"q{n}:[" for n in range(20000))
        start = time.perf_counter()
        meta = parse(text)
        self.assertLess(time.perf_counter() - start, 5.0)
        self.assertEqual((len(meta), meta["k0"], meta["q19999"]), (40000, "[", "["))

    def test_values_never_hold_unencodable_text(self):
        for text in ('t: "\\uD800"', 't: "\\uDFFF\\uD800"', 't: "\\U0010FFFF\\U00110000"', 't: "\\uD83D\\uDE00\\uD83D"'):
            with self.subTest(text):
                parse(text)["t"].encode("utf-8")


@unittest.skipUnless(HAS_YAML, "PyYAML が要る")
class RandomizedTest(unittest.TestCase):
    """種を固定した無作為の入力で、BaseLoader と等しい。"""

    COUNT = 600

    def compare(self, generate, minimum=200):
        rng = random.Random(20261111)
        compared = 0
        for _ in range(self.COUNT):
            text = generate(rng)
            try:
                expected = as_parser(text)
            except yaml.YAMLError:
                continue  # YAML として読めない入力は比べない
            if not isinstance(expected, dict):
                continue
            compared += 1
            self.assertEqual(parse(text), expected, text)
        self.assertGreaterEqual(compared, minimum)

    def test_block_scalars(self):
        def generate(rng):
            style, chomp = rng.choice("|>"), rng.choice(["", "", "-", "+"])
            explicit = rng.choice(["", "", "", "1", "2", "3"])
            header = style + (chomp + explicit if rng.random() < 0.5 else explicit + chomp)
            header += rng.choice(["", "", "", " # c", "  #c", " "])
            lines = []
            for _ in range(rng.randint(0, 7)):
                kind, indent = rng.random(), rng.choice([1, 2, 2, 2, 3, 4, 5])
                if kind < 0.2:
                    lines.append(" " * rng.choice([0, 0, 1, 2, 3, 6]))
                elif kind < 0.3:
                    lines.append(" " * indent + rng.choice(["- x", "# not comment", "k: v", "\tt", "a  ", "[a,"]))
                else:
                    lines.append(" " * indent + rng.choice(["a", "b c", "長い", "x", "  deep", "d\te"]))
            tail = rng.choice(["", "", "next: 1", "next: 1\nlast: |\n  z"])
            return "key: " + header + "\n" + "\n".join(lines) + ("\n" + tail if tail else "")

        self.compare(generate)

    def test_escapes(self):
        parts = ["\\t", "\\n", "\\\\", '\\"', "\\/", "\\ ", "\\_", "\\N", "\\L", "\\P", "\\0", "\\a", "\\b", "\\e",
                 "\\f", "\\r", "\\v", "\\x41", "\\xe9", "\\u00e9", "\\u3042", "\\U0001F600", "\\U00000041", "a", "あ",
                 " ", "b#c", "x, y", "'", "\\\t"]

        def generate(rng):
            return 'key: "' + "".join(rng.choice(parts) for _ in range(rng.randint(0, 6))) + '"'

        self.compare(generate)

    def test_block_sequences(self):
        def generate(rng):
            indent = " " * rng.choice([0, 0, 1, 2, 3, 4, 6])
            lines = ["key:" + rng.choice(["", " # c", "  "])]
            for _ in range(rng.randint(1, 4)):
                if rng.random() < 0.15:
                    lines.append("")
                if rng.random() < 0.15:
                    lines.append(indent + "# コメント")
                lines.append(indent + "- " + rng.choice(
                    ["a", '"b, c"', "'d''e'", "007", "true", "x # c", '"q#q"', "あ", '"\\u3042"', ""]).rstrip())
            lines.append(rng.choice(["next: 1", "next:\n  - z", "'q': [a]", "sp : v"]))
            return "\n".join(lines)

        self.compare(generate)

    def test_multiline_flow_sequences(self):
        def generate(rng):
            items = [rng.choice(["a", '"b, c"', "'d''e'", "007", "true", '"q#q"', "あ", '"]"', '"\\u3042"', "x y"])
                     for _ in range(rng.randint(1, 5))]
            out = "key: ["
            for n, item in enumerate(items):
                out += item + ("," if n < len(items) - 1 else "")
                # コメントの中の括弧、カンマ、引用符は、配列の形に関わらない。
                comment = rng.choice(["# c", "# ]", "# [x, y]", '# "q', "#]", "# a, 'b"])
                if rng.random() < 0.15:
                    # 空白のない #。`,` と閉じた引用符の直後ならコメントで、引用符のない値の直後なら値の一部である。
                    # 値の一部になるときに、引用符のない値の中の引用符（YAML と違ってよい箇所）を作らない。
                    # ] で終わるコメントは作らない（] で終わる 1 行目は、1 行の配列として読む。YAML と違ってよい箇所）。
                    out += rng.choice(["# c", "# ] c", "# [x, y] c", "#] c"]) + "\n"
                r = rng.random()
                if r < 0.5:
                    out += "\n" + " " * rng.choice([0, 1, 2, 4])
                elif r < 0.6:
                    out += "  " + comment + "\n" + " " * rng.choice([0, 2])
                elif r < 0.7:
                    out += "\n\n  "
                else:
                    out += " "
            return out + "]" + rng.choice(["", " # c", "  "]) + "\n" + rng.choice(["next: 1", '"q": [a]'])

        self.compare(generate)

    def test_keys(self):
        def generate(rng):
            lines = []
            for key in rng.sample(["type", "kind", "種類", "t1"], rng.randint(1, 4)):
                form = rng.choice(["{k}: {v}", '"{k}": {v}', "'{k}': {v}", "{k} : {v}", '"{k}"  : {v}', "{k}:   {v}"])
                lines.append(form.format(k=key, v=rng.choice(["x", '"y"', "[a, b]", "", "'z'"])).rstrip())
            return "\n".join(lines)

        self.compare(generate)


class UnchangedTest(unittest.TestCase):
    """規約どおりのページと、読み方を変えない書き方は、0.9.5 のパーサーと同じ値になる。"""

    def test_equal_to_the_0_9_5_parser(self):
        golden = json.loads(GOLDEN.read_text(encoding="utf-8"))["cases"]
        self.assertEqual(sorted(golden), sorted(UNCHANGED_CASES))
        for name, text in UNCHANGED_CASES.items():
            with self.subTest(name):
                self.assertEqual(golden_entry(wiki_text, text), golden[name])


class WriterRoundTripTest(unittest.TestCase):
    def test_reads_back_what_the_writer_wrote(self):
        meta = {
            "title": 'タブ\tと改行\nと "引用" と \\ と制御 \x07\x1f\x7f と絵文字 \U0001F600',
            "tags": ["a, b", "c\td", "\u2028", "\x00"],
            "raw": "C:\\books\\new.pdf",
            "created": "2026-11-03",
        }
        text = wiki_text.format_frontmatter(meta)
        inner = text.split("---\n")[1]
        self.assertEqual(parse(inner), meta)
        self.assertEqual(wiki_text.unquoted_string_keys(inner), [])


class SharedReaderTest(unittest.TestCase):
    """unquoted_string_keys() と top_level_keys() は、値の辞書と同じ行を見る。"""

    def test_top_level_keys(self):
        text = ('"type": x\nkind : y\nsources: [a,\n  title: b,\n"c"]\nnote: |\n  inner: 1\n  - z\ntags:\n- t\n'
                "'type': w\ngraph:\n  node_id: n\nsource-url: u")
        self.assertEqual(wiki_text.top_level_keys(text), ["type", "kind", "sources", "note", "tags", "type", "graph"])
        self.assertEqual(sorted(parse(text)), sorted(set(wiki_text.top_level_keys(text))))
        # 0.9.5 までキーの行として読んでいた行は、複数行の [...] の中にあっても、キーの行として読む。
        self.assertEqual(wiki_text.top_level_keys("sources: [a,\ntitle: b,\nc]"), ["sources", "title"])

    def test_unquoted_string_keys(self):
        cases = {
            'sources:\n- "a"\n- "b"': [],
            "sources:\n- a": ["sources"],
            'sources:\n    - "a"\n    - b': ["sources"],
            'tags: ["a",\n  "b"]': [],
            'tags: ["a",\n  b]': ["tags"],
            'counts: [1,\n  2026-11-01,\n  true]': [],
            '"type": "x"\nkind : "y"': [],
            '"type": x\nkind : y': ["type", "kind"],
            'title: "a\\tb\\u00e9"': [],
            "title: >-\n  題名\nraw: |\n  raw/a.md": ["title", "raw"],
            'graph:\n  aliases:\n  - a\ntitle: "x"': [],
        }
        for text, expected in cases.items():
            with self.subTest(text):
                self.assertEqual(wiki_text.unquoted_string_keys(text), expected)


NEW_SPELLINGS_PAGE = '''---
"type": "concept"
title : "A"
tags:
- "税制"
sources:
    - "paper"
aliases: ["VAT",
  "付加価値税"]
created: 2026-11-11
updated: 2026-11-11
---

# A
'''
SOURCE_PAGE = '---\ntype: "source"\ntitle: "論文"\ntags: ["税制"]\ncreated: 2026-11-11\nupdated: 2026-11-11\n---\n\n# 論文\n'


class ToolsTest(unittest.TestCase):
    """lint、検索、統計が、読めるようになった欄を読む。"""

    def setUp(self):
        self.temp = tempfile.TemporaryDirectory(ignore_cleanup_errors=True)
        self.addCleanup(self.temp.cleanup)
        self.wiki = Path(self.temp.name) / "wiki"
        self.write("sources/paper.md", SOURCE_PAGE)
        self.write("concepts/a.md", NEW_SPELLINGS_PAGE)

    def write(self, rel: str, text: str) -> None:
        path = self.wiki / rel
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(text, encoding="utf-8")

    def lint(self) -> dict:
        return wiki_lint.lint(wiki_lint.collect_pages(self.wiki), 100, 200, list(wiki_lint.DEFAULT_REQUIRED_FM), False, 5,
                              index_entries=wiki_lint.collect_index_entries(self.wiki))

    def test_lint(self):
        meta = {p["rel_path"]: p["meta"] for p in wiki_lint.collect_pages(self.wiki)}["concepts/a.md"]
        self.assertEqual((meta["type"], meta["title"], meta["tags"], meta["sources"], meta["aliases"]),
                         ("concept", "A", ["税制"], ["paper"], ["VAT", "付加価値税"]))
        findings = self.lint()
        for key in ("missing_frontmatter", "unresolved_sources", "unquoted_strings", "malformed_frontmatter"):
            self.assertEqual(findings[key], [], key)

    def test_lint_checks_apply_to_the_fields_it_now_reads(self):
        # 今までは空の配列に読んでいたので、字下げのない sources: は検査に掛からなかった。
        self.write("concepts/a.md", NEW_SPELLINGS_PAGE.replace('    - "paper"', "- nowhere"))
        findings = self.lint()
        self.assertEqual(findings["unresolved_sources"],
                         [{"path": "concepts/a.md", "source": "nowhere", "reason": "missing"}])
        self.assertEqual([f["path"] for f in findings["unquoted_strings"]], ["concepts/a.md"])

    def test_search(self):
        pages = {p["rel_path"]: p for p in wiki_search.collect_pages(self.wiki)}
        page = pages["concepts/a.md"]
        self.assertEqual((page["meta"]["type"], page["meta"]["title"]), ("concept", "A"))
        self.assertTrue(wiki_search.passes_filters(page, Namespace(type="概念", tag=["税制"], since="2026-11-01")))
        self.assertFalse(wiki_search.passes_filters(pages["sources/paper.md"], Namespace(type="concept", tag=[], since=None)))

    def test_stats(self):
        stats = wiki_stats.compute_stats(self.wiki)
        self.assertEqual(stats["pages_by_type"], {"concept": 1, "source": 1})

    def test_search_does_not_keep_an_old_parse_cache(self):
        # 形式 4（0.9.5 まで）のパースキャッシュは、同じ SHA-256 でも使わない。古いパーサーの値が残るためである。
        cache = Path(self.temp.name) / "parse-cache.json"
        files = {}
        for rel in ("concepts/a.md", "sources/paper.md"):
            digest = hashlib.sha256((self.wiki / rel).read_bytes()).hexdigest()
            files[rel] = {"sha256": digest, "meta": {"title": "古い値", "sources": []}, "links": [], "sections": []}
        cache.write_text(json.dumps({"schema": 4, "parser": wiki_search.PARSER_ID, "files": files}), encoding="utf-8")
        pages = {p["rel_path"]: p for p in wiki_search.collect_pages(self.wiki, cache)}
        self.assertEqual(pages["concepts/a.md"]["meta"]["sources"], ["paper"])
        self.assertEqual(pages["concepts/a.md"]["meta"]["title"], "A")
        self.assertGreater(wiki_search.PARSE_CACHE_SCHEMA, 4)
        # 書き直したキャッシュは、次に使う。
        self.assertEqual(json.loads(cache.read_text(encoding="utf-8"))["schema"], wiki_search.PARSE_CACHE_SCHEMA)
        again = {p["rel_path"]: p for p in wiki_search.collect_pages(self.wiki, cache)}
        self.assertEqual(again["concepts/a.md"]["meta"], pages["concepts/a.md"]["meta"])


@unittest.skipUnless(HAS_YAML, "PyYAML が要る")
class GraphmlTest(unittest.TestCase):
    """エスケープを YAML の意味で読むと、値に制御文字が入りうる。GraphML は、読める XML のまま書き出す。"""

    def test_control_characters_do_not_break_graphml(self):
        import xml.etree.ElementTree as ET

        import wiki_graph_extract as extract

        temp = tempfile.TemporaryDirectory(ignore_cleanup_errors=True)
        self.addCleanup(temp.cleanup)
        wiki = Path(temp.name) / "wiki"
        wiki.mkdir()
        # エスケープで書いた NUL と BEL と、ファイルに直接書いた制御文字（U+0001）。タブと改行は XML に書ける。
        (wiki / "s.md").write_bytes('---\ntype: "source"\ntitle: "a\\0b\\ac\\td\\ne"\n---\n本文\n'.encode("utf-8"))
        (wiki / "t.md").write_bytes('---\ntype: "source"\ntitle: "x\x01y"\nsources: ["s"]\n---\n本文\n'.encode("utf-8"))
        ontology = extract.read_ontology(SCRIPTS.parent / "assets" / "ontology.yaml.template")
        pages = extract.collect_pages(wiki)
        diagnostics: list[dict] = []
        nodes, ids, _aliases = extract.build_nodes(pages, ontology, diagnostics)
        edges = extract.build_edges(pages, ids, diagnostics)
        self.assertEqual(sorted(n["title"] for n in nodes), ["a\0b\ac\td\ne", "x\x01y"])
        path = Path(temp.name) / "graph.graphml"
        extract.write_graphml_file(path, nodes, edges)
        root = ET.parse(path).getroot()   # 読めない XML なら、ここで ParseError になる
        titles = sorted(el.text for el in root.iter("{http://graphml.graphdrawing.org/xmlns}data")
                        if el.get("key") == "d_title")
        self.assertEqual(titles, ["a\N{REPLACEMENT CHARACTER}b\N{REPLACEMENT CHARACTER}c\td\ne",
                                  "x\N{REPLACEMENT CHARACTER}y"])
        # ID は、別の ID と同じ文字列にならないように書く。XML に書ける文字だけの ID は変えない。
        ids = ["person:x", "person:x\0y", "person:x\x01y", "person:x\N{REPLACEMENT CHARACTER}y",
               "person:x\N{REPLACEMENT CHARACTER}{0}y", "person:x\N{REPLACEMENT CHARACTER}\N{REPLACEMENT CHARACTER}y",
               "person:x{0}y", "person:x\ud800y", "a\tb\nc\rd"]
        written = [extract._xml_id(value) for value in ids]
        self.assertEqual(len(set(written)), len(ids))
        self.assertEqual((written[0], written[6], written[8]), (ids[0], ids[6], ids[8]))
        self.assertEqual(extract._xml_text("".join(written)), "".join(written))   # どれも XML に書ける
        self.assertEqual(extract._xml_text("ok\t\n\r 日本語 \U0001F600 \x00\x1f\x7f\ud800" + chr(0xFFFE) + chr(0xFFFF)),
                         "ok\t\n\r 日本語 \U0001F600 \N{REPLACEMENT CHARACTER}\N{REPLACEMENT CHARACTER}\x7f\N{REPLACEMENT CHARACTER}\N{REPLACEMENT CHARACTER}\N{REPLACEMENT CHARACTER}")


    def test_node_ids_stay_distinct_in_graphml(self):
        # 置き換えたあとの ID が重なると、GraphML の中で別のノードが 1 つになり、エッジが自分を指す。
        import xml.etree.ElementTree as ET

        import wiki_graph_extract as extract

        temp = tempfile.TemporaryDirectory(ignore_cleanup_errors=True)
        self.addCleanup(temp.cleanup)
        wiki = Path(temp.name) / "wiki"
        wiki.mkdir()
        pages = {
            "a.md": 'type: "entity"\nkind: "person"\ngraph:\n  node_id: "person:x\\0y"\n  relationships:\n'
                    '    - predicate: "knows"\n      object: "person:x\\uFFFDy"\n      source: "s"',
            "b.md": 'type: "entity"\nkind: "person"\ngraph:\n  node_id: "person:x\\uFFFDy"',
            "c.md": 'type: "entity"\nkind: "person"\ngraph:\n  node_id: "person:x\\x01y"',
            "s.md": 'type: "source"\ntitle: "s"',
        }
        for name, frontmatter in pages.items():
            (wiki / name).write_bytes(("---\n" + frontmatter + "\n---\n本文\n").encode("utf-8"))
        ontology = extract.read_ontology(SCRIPTS.parent / "assets" / "ontology.yaml.template")
        collected = extract.collect_pages(wiki)
        diagnostics: list[dict] = []
        nodes, ids, _aliases = extract.build_nodes(collected, ontology, diagnostics)
        edges = extract.build_edges(collected, ids, diagnostics)
        self.assertEqual(len({n["id"] for n in nodes}), 4)
        path = Path(temp.name) / "graph.graphml"
        extract.write_graphml_file(path, nodes, edges)
        ns = "{http://graphml.graphdrawing.org/xmlns}"
        root = ET.parse(path).getroot()
        node_ids = [el.get("id") for el in root.iter(ns + "node")]
        self.assertEqual(len(set(node_ids)), 4)
        knows = [(el.get("source"), el.get("target")) for el in root.iter(ns + "edge")
                 if any(d.get("key") == "d_predicate" and d.text == "knows" for d in el.iter(ns + "data"))]
        self.assertEqual(knows, [(extract._xml_id("person:x\0y"), extract._xml_id("person:x\N{REPLACEMENT CHARACTER}y"))])
        self.assertNotEqual(knows[0][0], knows[0][1])
        self.assertLessEqual(set(knows[0]), set(node_ids))


if __name__ == "__main__":
    unittest.main(verbosity=2)
