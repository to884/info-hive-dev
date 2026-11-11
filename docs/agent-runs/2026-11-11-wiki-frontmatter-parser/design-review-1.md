## 判定

**却下。確信度：高。** 「不正な YAML は従来どおり読む」「対象の正しい YAML は `BaseLoader` と同じ値になる」という契約を破る反例がある。さらに、今回読むようになる制御文字によって、グラフの既定の出力に不正な GraphML が混入する。

## 致命的・重大な欠陥

### 1. 【致命】不正な複数行配列が、従来読めていた後続の欄を飲み込む

反例：

```yaml
tags: [a,
type: source
title: X]
```

実行結果：

```python
# 0.9.5
{'tags': '[a,', 'type': 'source', 'title': 'X]'}

# 試作
{'tags': ['a', 'type: source title: X']}

# BaseLoader
ParserError
```

`type` と `title` が消える。設計3の変更表にない後退であり、設計2.1の「YAML として誤りの書き方は、今までの読み方を変えない」に反する。

試作は括弧と引用符の状態だけで取り込み範囲を決め、範囲内が正しい YAML かを判定しない。「後ろに閉じ括弧が見つかる」ことから「取り込んでも互換性を壊さない」ことは導けない。

エスケープにも同じ契約違反がある：

```yaml
title: "\d+\n"
```

これは `BaseLoader` が拒否する入力だが、旧版は `\d+\n` を書かれた文字のまま返し、試作は末尾の `\n` だけを改行へ変える。不正なエスケープ自体を残しても、不正な値全体の互換性は維持できていない。

根拠：[設計2.1](C:/Works/info-hive-dev/.claude/worktrees/frontmatter-parser/docs/plans/wiki-frontmatter-parser-2026-11-11.md:30)、[複数行配列の取り込み](C:/Works/info-hive-dev/.claude/worktrees/frontmatter-parser/info-hive-wiki/skills/info-hive/scripts/wiki_text.py:356)、[エスケープ処理](C:/Works/info-hive-dev/.claude/worktrees/frontmatter-parser/info-hive-wiki/skills/info-hive/scripts/wiki_text.py:221)。

### 2. 【重大】正しい複数行配列で、コメントが値に混ざる。`unread_field` も出ない

反例：

```yaml
sources: [a,# comment
 b]
```

実行結果：

```python
# BaseLoader
{'sources': ['a', 'b']}

# 試作
{'sources': ['a', '# comment b']}
```

次も食い違う：

```yaml
sources: [# comment
 a]
```

`BaseLoader` は `['a']`、試作は `['# comment a']` を返す。

フロー構文では `[` や `,` の直後にもコメントを置ける。試作の「直前が空白、または行頭の `#`」という条件では足りない。この書き方は設計2.7の除外対象にない。

さらに、両例とも `wiki_graph_extract.read_frontmatter()` の診断は空だった。`_unread_fields()` は配列の要素数を見るため、**数が合ったまま別の参照になった失敗**を検出しない。設計2.8の判定を据え置くだけでは、正しく読めたという保証にならない。

根拠：[設計2.3](C:/Works/info-hive-dev/.claude/worktrees/frontmatter-parser/docs/plans/wiki-frontmatter-parser-2026-11-11.md:63)、[コメント判定](C:/Works/info-hive-dev/.claude/worktrees/frontmatter-parser/info-hive-wiki/skills/info-hive/scripts/wiki_text.py:323)、[診断の判定](C:/Works/info-hive-dev/.claude/worktrees/frontmatter-parser/info-hive-wiki/skills/info-hive/scripts/wiki_graph_extract.py:233)。

### 3. 【重大】NUL のデコードによって、書き出しに成功した GraphML が読めなくなる

反例：

```yaml
type: "source"
title: "a\0b"
```

試作は題名を `'a\x00b'` にする。その値をノードへ渡して `write_graphml_file()` を実行すると、NUL をそのまま含む XML が生成される。書き出しは成功するが、生成物を `xml.etree.ElementTree.fromstring()` で読むと、次の例外になる。

```text
ParseError: not well-formed (invalid token)
```

`io.BytesIO` を使い、実際の書き出し関数で再現した。旧版の値は文字としての `\0` なので、この入力から NUL は出力されない。

JSON と SQLite では同じ値を保持できた。したがって、全形式が一緒に失敗するのではなく、**GraphML だけが不正な成果物として成功扱いになる**。設計5の試験には、デコードした制御文字をグラフの出力へ通し、再読込する確認がない。

根拠：[設計2.5](C:/Works/info-hive-dev/.claude/worktrees/frontmatter-parser/docs/plans/wiki-frontmatter-parser-2026-11-11.md:90)、[ノードの題名](C:/Works/info-hive-dev/.claude/worktrees/frontmatter-parser/info-hive-wiki/skills/info-hive/scripts/wiki_graph_extract.py:561)、[GraphML の文字列設定と書き出し](C:/Works/info-hive-dev/.claude/worktrees/frontmatter-parser/info-hive-wiki/skills/info-hive/scripts/wiki_graph_extract.py:1032)。

### 4. 【重大】空白と改行の扱いに、明示されていない `BaseLoader` との差がある

今回読むようになる字下げ4つの配列でも、次が食い違う。以下の `\u00a0` は、入力中の実文字 U+00A0 を表す。

```python
入力 = 'sources:\n    - \u00a0a\u00a0'

# BaseLoader
{'sources': ['\u00a0a\u00a0']}

# 試作
{'sources': ['a']}
```

YAML では文字列の一部になる空白を、Python の `.strip()` が削除している。引用符つきのキーでも同じ問題がある：

```python
入力 = '"type": \u00a0source'

# BaseLoader
{'type': '\u00a0source'}

# 試作
{'type': 'source'}
```

ブロックスカラーには別の反例がある。`\x85` は実文字 U+0085：

```python
入力 = 'title: |\n  x\x85  y'

# BaseLoader
{'title': 'x\ny\n'}

# 試作
{'title': 'x\x85  y\n'}
```

試作は LF でしか行を分割しないため、比較相手が改行として読む U+0085 を内容として残す。いずれも正しい YAML で、設計に列挙された例外ではない。

根拠：[キーの正規表現](C:/Works/info-hive-dev/.claude/worktrees/frontmatter-parser/info-hive-wiki/skills/info-hive/scripts/wiki_text.py:196)、[行分割と要素の空白除去](C:/Works/info-hive-dev/.claude/worktrees/frontmatter-parser/info-hive-wiki/skills/info-hive/scripts/wiki_text.py:446)、[ブロックスカラー](C:/Works/info-hive-dev/.claude/worktrees/frontmatter-parser/info-hive-wiki/skills/info-hive/scripts/wiki_text.py:384)。

## 崩れる前提

- **閉じ括弧までを読めば、不正な入力の従来値を保てる。** 欄の区切りとしては読めていた行が、不正なフロー配列へ取り込まれると崩れる。欠陥1で再現した。
- **行を空白でつなぎ、既存の要素分割を使えば YAML と一致する。** コメントの開始条件や、YAML と Python の空白の定義が違う入力で崩れる。
- **UTF-8 に書ける文字なら下流へ渡せる。** NUL は UTF-8 へエンコードできても XML に置けない。
- **要素数とキーの出現回数が合えば、読めたと判定できる。** 同数の誤った参照へ変わると崩れる。欠陥2では診断が出なかった。
- **手元の54ページで差がなければ、互換性の根拠になる。** この54ページの比較結果は再確認できたが、新しい構文を含まない標本では、不正入力との境界や新構文の値を検証できない。

## 見落としと軽微な問題

- **【軽微】閉じない `[` の探索が二乗時間になる。** `k0: [`、`k1: [`……を並べた入力で、250行＝約0.033秒、500行＝約0.137秒、1,000行＝約0.563秒、2,000行＝約2.76秒だった。旧版の2,000行は約0.004秒。各キーから残り全行を探索し直す。[該当処理](C:/Works/info-hive-dev/.claude/worktrees/frontmatter-parser/info-hive-wiki/skills/info-hive/scripts/wiki_text.py:368)。大きさの lint 検査より前にパースするため、ページの行数上限では探索を防げない。
- **【軽微】サロゲート対の説明より実装の対象が狭い。** `"\uD83D\uDE00"` はまとめるが、`"\U0000D83D\U0000DE00"` と混在表記は文字のまま残す。「上位と下位を続けて書いたもの」という設計2.5の説明には、この区別がない。[判定は小文字の `u` に限定されている](C:/Works/info-hive-dev/.claude/worktrees/frontmatter-parser/info-hive-wiki/skills/info-hive/scripts/wiki_text.py:250)。
- **【軽微】索引のハッシュについての説明が事実と違う。** 設計2.9は「frontmatter の値を含まない」とするが、`searchable_text` は `title` を含み、`section_hash()` はその全体をハッシュする。題名の変更でハッシュが変わることも実行確認した。fingerprint 据え置きによる古い題名の残存は、この経路では崩せなかった。[検索対象文字列](C:/Works/info-hive-dev/.claude/worktrees/frontmatter-parser/info-hive-wiki/skills/info-hive/scripts/wiki_search.py:373)、[ハッシュ](C:/Works/info-hive-dev/.claude/worktrees/frontmatter-parser/info-hive-wiki/skills/info-hive/scripts/wiki_index.py:810)。
- **【軽微】改行付きの識別値が下流で持つ意味を試験していない。** `type: >` の本文を `source` にすると値は `'source\n'` になり、`missing_raw()` の `type == "source"` に当たらない。存在しない `raw` があっても、この検査は空を返す。YAML の値としては一致するが、「読めた欄には検査が掛かる」という説明には留保が必要。[検査の入口](C:/Works/info-hive-dev/.claude/worktrees/frontmatter-parser/info-hive-wiki/skills/info-hive/scripts/wiki_lint.py:209)。
- **【軽微】0.9.6 の根拠は、互換性の検証になっていない。** 別ブランチが0.10.0を予定していることから、今回の変更の互換性は判断できない。番号自体が不適切とまでは断定しないが、現状は設計3にない値の消失がある。

## 検証した事実

Python 3.14.6 と、ローカルにある PyYAML 6.0.3 を使用した。旧版は指定された `426d6bf` のソースを取得し、メモリ上で実行した。リポジトリのファイルは変更していない。

| 確認項目 | 結果 |
|---|---|
| 不正な複数行配列・不正エスケープの新旧互換性 | 食い違い。欠陥1 |
| フロー配列のコメントと `BaseLoader` の一致 | 食い違い。欠陥2 |
| U+00A0・U+0085 を含む対象構文 | 食い違い。欠陥4 |
| ASCII の行・字下げ・空行・タブを組み合わせたブロックスカラー | YAML として読めた8,788件で一致 |
| リポジトリの wiki 6件、ユーザースコープの wiki 48件 | 辞書・キー一覧・引用符検査の新旧差なし |
| 既存 `eval/scripts/test_frontmatter.py` | 12件成功 |
| 制御文字、改行、引用符、バックスラッシュ、絵文字の書式化との往復 | 試した値では一致 |
| NUL を含む `raw` の `missing_raw()` | 例外にならず、欠落を報告 |
| NUL を含む値の JSON・SQLite | 保持できた |
| NUL を含む題名の GraphML | 書き出し成功、再読込失敗 |
| Tantivy・MCP の実際の索引更新 | 確かめられず。利用可能な依存環境の Python 実行がアクセス拒否された |

## 崩せなかった点

- 通常のブロックスカラーについて、折りたたみ、字下げ、末尾改行の処理は上記8,788件で崩せなかった。
- `fm_text + "\n"` を比較相手とする契約の範囲では、最後の欄や `|+` の末尾改行は一致した。
- `\uD83D\uDE00` の結合、単独サロゲートと範囲外コードポイントを文字のまま残す処理は、試した範囲で説明どおりだった。
- 調べた索引更新経路では、パースキャッシュを無効化した後も古い題名が永続索引に残る反例は得られなかった。

使用した MCP サーバー: なし  
使用した Agent Skills: なし
