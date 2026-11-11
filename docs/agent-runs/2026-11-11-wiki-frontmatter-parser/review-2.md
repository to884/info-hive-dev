## 判定

**却下。確信度：高。** 複数行の判定を先に試す変更により、旧版で読めていた一行の配列が、後続コメントを値へ取り込む。設計3にない値の変化であり、既存の `sourced_from` が消えることも再現した。

## 致命的・重大な欠陥

### 【重大】一行で完結した配列の値が、後続コメントによって変わる

正しい YAML の反例：

```yaml
sources: [it's]
# don't ]
```

実行結果：

```python
# 0.9.5 と BaseLoader
{'sources': ["it's"]}

# a27d311
{'sources': ["it's] # don't"]}
```

`[it's]` の `'` を `_fm_flow_line()` が引用符の開始として扱うため、一行目の `]` を認識しない。次のコメント内の `'` で引用符を閉じ、その後の `]` まで配列へ取り込む。

旧版も要素分割では `'` を引用符として扱っていたが、一行の配列として処理を終えていた。今回の判定順序の変更が、後続行への読み進めを新たに発生させている。

引用符なしの文字列中の引用符は、設計2.1で YAML との差を許した箇所である。しかし、それは**旧版から値を変えてよいという例外ではない**。この入力は一行の配列とコメントであり、設計3の「複数行にまたがる `[...]`」には当たらない。決まり3に反する。

`type: concept` を加え、ソースページ `it's.md` とともにグラフへ通した結果：

```text
0.9.5:
  sourced_from → source:it's
  診断なし

a27d311:
  エッジなし
  unresolved_source（source: "it's] # don't"）
```

`read_frontmatter()` の `unread_field` は出ない。キーと要素数が保たれたまま、参照の内容が変わる。

同じ原因で、次も旧版・`BaseLoader` と食い違う：

```yaml
tags: [a"b]
# x"]
```

根拠：[複数行判定を先行させた箇所](C:/Works/info-hive-dev/.claude/worktrees/frontmatter-parser/info-hive-wiki/skills/info-hive/scripts/wiki_text.py:517)、[引用符の開始判定](C:/Works/info-hive-dev/.claude/worktrees/frontmatter-parser/info-hive-wiki/skills/info-hive/scripts/wiki_text.py:369)、[後続行の取り込み](C:/Works/info-hive-dev/.claude/worktrees/frontmatter-parser/info-hive-wiki/skills/info-hive/scripts/wiki_text.py:401)、[設計3の変更表](C:/Works/info-hive-dev/.claude/worktrees/frontmatter-parser/docs/plans/wiki-frontmatter-parser-2026-11-11.md:231)。

## 崩れる前提

- **`_fm_flow_line()` で一行目の閉じ括弧を判定すれば、一行の配列の互換性を保てる。** YAML と異なる引用符の読み方を引き継いでいるため、完結した配列を未完結と誤判定する。
- **キーの行で止めれば、後続行の取り込みによる後退を防げる。** コメント行はキーの行ではないため、値へ取り込めてしまう。
- **YAML との比較試験から除外した構文は、既存値の互換性にも影響しない。** 引用符なしの文字列中の引用符は、今回、一行から複数行へ読む範囲を変える条件になった。

## 見落としと軽微な問題

### 【軽微】修正した `as_parser()` が、重複キーの後勝ちを壊す

入力：

```yaml
k:
k: x
```

実行結果：

```python
# BaseLoader と実装
{'k': 'x'}

# 試験の as_parser()
{'k': []}
```

`construct_document()` が後の値を採用した後、先に書かれた空のノードを走査して、その結果を `[]` で上書きしてしまう。次も同様である：

```yaml
k:
k: ""
```

実装は `''`、比較用関数は `[]` を返す。今回の引用符付き空文字列への対応は、重複キーがある場合には成立していない。無作為のキー生成は `rng.sample()` で重複を避けるため、この誤判定を通らない。

根拠：[比較用関数](C:/Works/info-hive-dev/.claude/worktrees/frontmatter-parser/tests/wiki/test_frontmatter_parser.py:63)、[重複しないキー生成](C:/Works/info-hive-dev/.claude/worktrees/frontmatter-parser/tests/wiki/test_frontmatter_parser.py:397)。

### 【軽微】CHANGELOG の ID の無変更条件が、実装と一致しない

CHANGELOG は「XML に書ける文字だけの ID は変わらない」とするが、XML に書ける U+FFFD は二重になる。

```python
_xml_id("person:x\uFFFDy")
# "person:x\uFFFD\uFFFDy"
```

依頼文にある「U+FFFD を含まない」という条件が、CHANGELOG、設計2.11、docstring の無変更条件にはない。

根拠：[CHANGELOG](C:/Works/info-hive-dev/.claude/worktrees/frontmatter-parser/info-hive-wiki/CHANGELOG.md:23)、[実際の無変更条件](C:/Works/info-hive-dev/.claude/worktrees/frontmatter-parser/info-hive-wiki/skills/info-hive/scripts/wiki_graph_extract.py:1028)。

## 検証した事実

Python 3.14.6、PyYAML 6.0.3 を使用した。対象スクリプトに `a27d311` からの作業ツリー差分がないことを確認した。ファイルは変更していない。

| 確認項目 | 結果 |
|---|---|
| 前回のコメント中の `]` の反例 | `BaseLoader` と一致するようになった |
| `source-url:` を挟んだ配列要素の減少 | 挙動は残るが、今回の設計3と CHANGELOG に記載された |
| 前回の NUL と U+FFFD の ID 衝突 | 再現しない。2ノードと、その間のエッジを保持 |
| `_xml_id()` の衝突探索 | NUL、U+0001、U+FFFD、括弧、数字など8文字から長さ0〜5の37,449文字列を生成し、衝突なし |
| Unicode 全コードポイントを含む ID・題名の GraphML 出力 | XML として再読込できた |
| ファイル書込を伴わない新試験19件 | 全件成功 |
| 一行配列と後続コメントの組み合わせ | 新しい後退を再現 |
| 引用符付き空文字列単独の比較 | 修正後は一致 |
| 空の宣言の後に同じキーを再宣言する比較 | `as_parser()` だけ食い違う |

GraphML は `io.BytesIO` で実際の書き出し関数を実行し、前回の ID 衝突は NetworkX の再読込でも確認した。ファイル書込を伴う試験群全体は実行していない。

## 崩せなかった点

- `_xml_id()` が異なる文字列を同じ ID にする反例は得られなかった。
- `_xml_id()` の出力が、文字そのものを原因として読めない XML になる反例は得られなかった。
- 前回の ID 衝突によるノード統合と自己ループは再現しなかった。
- 今回、決まり2の「旧版が読んだキー行を失わない」を破る入力は見つからなかった。
- `_fm_block_scalar()` と `_fm_unescape()` には、明示された例外以外の新しい反例を見つけられなかった。

使用した MCP サーバー: なし  
使用した Agent Skills: なし
