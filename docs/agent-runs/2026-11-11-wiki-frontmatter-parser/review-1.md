## 判定

**却下。確信度：高。** 前回の主要な反例は修正されているが、設計2.1の決まり1・3を破る入力が残る。また、GraphML の文字置換によって、異なるノードが同じ ID になり、関係が変質する。

## 致命的・重大な欠陥

### 1. 【重大】新しい構文を使わないページでも、変更表にない配列要素の消失が起きる

反例：

```yaml
sources:
  - "a"
source-url:
  - "b"
```

実行結果：

```python
# 0.9.5
{'sources': ['a', 'b']}

# 26d8c8e
{'sources': ['a']}
```

旧版は、読めない `source-url:` を挟んでも `sources` の配列を継続する。新版は、字下げのない行で配列を終了する。

実装は設計2.2の終了規則には従うが、**「変更は設計3の表だけ」という決まり3には反する**。表にある「値のないキーの次の行が `- ` でない場合」でもない。最初の要素は通常の字下げ2つである。

`type: "concept"` を加え、`a`・`b` をソースページとしてグラフへ通した結果も確認した。

```text
0.9.5:     sourced_from → source:a、source:b
26d8c8e:   sourced_from → source:a
診断:      どちらも空
```

不正な入力でも同様になる：

```yaml
sources:
  - "a"
???
  - "b"
```

これも `['a', 'b']` から `['a']` へ変わる。CHANGELOG の Changed に、この終了条件による既存値の変化は記載されていない。

根拠：[配列の終了処理](C:/Works/info-hive-dev/.claude/worktrees/frontmatter-parser/info-hive-wiki/skills/info-hive/scripts/wiki_text.py:493)、[設計の変更表](C:/Works/info-hive-dev/.claude/worktrees/frontmatter-parser/docs/plans/wiki-frontmatter-parser-2026-11-11.md:226)。

### 2. 【重大】コメント中の `]` で、正しい複数行配列を一行の配列と誤判定する

反例：

```yaml
sources: [a,# comment ]
 b]
```

実行結果：

```python
# BaseLoader
{'sources': ['a', 'b']}

# 26d8c8e
{'sources': ['a', '# comment']}
```

次も食い違う：

```yaml
sources: [# ]
 a]
```

`BaseLoader` は `['a']`、実装は `['#']` を返す。いずれも正しい YAML で、実際の配列は複数行にまたがっている。

原因は、フロー構文用のコメント処理を呼ぶ前に、既存の `_fm_strip_comment()` と `value.endswith("]")` で一行の配列を確定すること。空白のないコメント開始を前者が認識せず、コメント内の括弧を閉じ括弧にしてしまう。追加された `_fm_flow_line()` の修正には到達しない。

`read_frontmatter()` の診断は両例とも空だった。誤った値でも要素数が合うため、`unread_field` が補足することもない。

設計2.3の対象となる複数行配列について、決まり1を満たさない。CHANGELOG の「行ごとのコメントを除く」という説明とも食い違う。無作為試験のコメントは固定の `# c` で、コメント内に括弧を生成しない。

根拠：[一行判定が先行する箇所](C:/Works/info-hive-dev/.claude/worktrees/frontmatter-parser/info-hive-wiki/skills/info-hive/scripts/wiki_text.py:511)、[到達しないフロー用コメント処理](C:/Works/info-hive-dev/.claude/worktrees/frontmatter-parser/info-hive-wiki/skills/info-hive/scripts/wiki_text.py:347)、[試験の生成範囲](C:/Works/info-hive-dev/.claude/worktrees/frontmatter-parser/tests/wiki/test_frontmatter_parser.py:346)。

### 3. 【重大】GraphML の ID 置換が、別ノードを同一ノードへ潰す

2ページの `graph.node_id` を、それぞれ次の値にする：

```yaml
# a.md
graph:
  node_id: "person:x\0y"
```

```yaml
# b.md
graph:
  node_id: "person:x\uFFFDy"
```

元の ID は異なるため、ノード構築時の重複診断は出ない。しかし GraphML では、両方が同じ値になる：

```xml
<node id="person:x�y">...</node>
<node id="person:x�y">...</node>
```

`a.md` から `b.md` へのリンクも加え、`read_frontmatter()` → `build_nodes()` → `build_edges()` → `write_graphml_file()` を実行した。結果は次のとおりだった。

```text
元のノード数:             2
抽出時の診断:             空
GraphML を NetworkX で読んだノード数: 1
元の2ノード間のエッジ:     自己ループになる
```

XML として読めることだけでは、グラフを保持できたことにならない。置換前の ID で重複を検査し、置換後の ID で出力するため、既存の重複診断でも捕捉されない。JSONL・SQLite と GraphML で、ノード数と関係が違う成果物になる。

追加試験は題名の文字置換と XML の再読込を確認するだけで、ID の一意性や関係の保持を検査していない。

根拠：[置換関数](C:/Works/info-hive-dev/.claude/worktrees/frontmatter-parser/info-hive-wiki/skills/info-hive/scripts/wiki_graph_extract.py:1010)、[ID・端点への適用](C:/Works/info-hive-dev/.claude/worktrees/frontmatter-parser/info-hive-wiki/skills/info-hive/scripts/wiki_graph_extract.py:1047)、[GraphML の試験](C:/Works/info-hive-dev/.claude/worktrees/frontmatter-parser/tests/wiki/test_frontmatter_parser.py:518)。

## 崩れる前提

- **旧版のキー行を残せば、既存の欄の互換性を守れる。** キー行を残しても、配列の終了条件が変わると、同じ欄の要素と既存エッジが消える。
- **文字列末尾の `]` で一行の配列を確定できる。** その文字がコメント内にあると崩れる。
- **同じ文字置換を ID と参照に適用すれば、関係を保てる。** 置換が一対一でないため、異なる ID が衝突すると崩れる。
- **XML の再読込成功が、GraphML の正しさを示す。** 重複 ID や、ノードの統合による自己ループは、XML の構文検査では分からない。

## 見落としと軽微な問題

- **【軽微】CR は GraphML の再読込で LF に変わる。** `title: "a\rb"` をパースし、実際の書き出し関数と `ElementTree.fromstring()` に通すと、`'a\rb'` が `'a\nb'` になる。`_xml_text()` は CR を保持するが、出力されたテキスト中の CR が読込時に変わる。試験は `_xml_text()` 単体で CR の保持を検査しており、ファイル相当の往復には CR を含めていない。根拠：[テキストの出力](C:/Works/info-hive-dev/.claude/worktrees/frontmatter-parser/info-hive-wiki/skills/info-hive/scripts/wiki_graph_extract.py:1055)、[単体の期待値](C:/Works/info-hive-dev/.claude/worktrees/frontmatter-parser/tests/wiki/test_frontmatter_parser.py:546)。
- **【軽微】比較用の `as_parser()` が、空文字列を値なしと混同する。** `base('title: ""')` は `{'title': ''}` だが、`as_parser()` を通すと `{'title': []}` になる。設計の例外は値のないキーであり、引用符で明示した空文字列ではない。現在の実装はこの入力を正しく空文字列として読むが、この比較補助関数はその値の判定に使えない。根拠：[比較値の変換](C:/Works/info-hive-dev/.claude/worktrees/frontmatter-parser/tests/wiki/test_frontmatter_parser.py:57)。

## 検証した事実

Python 3.14.6、PyYAML 6.0.3 を使用した。対象スクリプトの作業ツリーに `26d8c8e` からの差がないことを確認し、旧版は `426d6bf` のソースをメモリ上で実行した。ファイルは変更していない。

| 確認項目 | 結果 |
|---|---|
| 前回の後続 `type`・`title` 飲み込み | 再現しない |
| 前回の `"\d+\n"` の部分デコード | 再現しない。全体が旧版と同じ |
| 前回の `[,#`・`[#` 相当のコメント反例 | 通常のコメント本文では一致 |
| コメント本文に `]` を追加 | 食い違い。欠陥2 |
| 前回の NUL による XML 構文エラー | 再現しない |
| Unicode 全コードポイントを題名に入れて GraphML 出力・再読込 | XML として読めた |
| 置換後のノード ID の一意性 | 崩れる。欠陥3 |
| 新試験の、ファイル書込を伴わない19件 | 全件成功 |
| golden 33件と実際の `426d6bf` の出力 | 全件一致 |
| 行を組み合わせた12,000入力で旧版のキー行の回数を比較 | 欠落なし |

`ToolsTest` とファイル書込を伴う `GraphmlTest` は実行していない。GraphML の反例は `io.BytesIO` で実際の書き出し関数を実行した。

## 崩せなかった点

- 決まり2の「旧版が読んだキー行を失わない」は、今回の入力群では崩せなかった。
- `top_level_keys()` と `unquoted_string_keys()` が、辞書のパースと異なる行を読む反例は得られなかった。
- `_fm_unescape()` の全体フォールバックと、明示されたサロゲートの扱いに、新たな反例は得られなかった。
- 明示された例外を除く通常のブロックスカラーでは、新たな `BaseLoader` との差を見つけられなかった。
- `_xml_text()` 適用後に、文字そのものが原因で XML の構文エラーになる反例は得られなかった。

使用した MCP サーバー: なし  
使用した Agent Skills: なし
