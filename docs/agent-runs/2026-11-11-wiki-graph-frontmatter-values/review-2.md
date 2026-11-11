## 判定

**条件付きで採用可。確信度：高。** 前回の重大1〜3は再現せず、golden が旧スクリプトの出力と一致することも確認した。ただし、未読欄の診断漏れ・誤検出と、出力不変の条件に反例が残る。

## 致命的・重大な欠陥

なし。今回の修正に起因する新たな処理停止や、通常のマージ・タグ付きキーによる参照の誤置換は再現できなかった。

## 崩れる前提

- **「読めたキーの回数と、値のある宣言の回数を比較すれば、未読宣言を検出できる」**  
  値なしの宣言も読めた回数に入るため、後続の未読宣言を隠す。
- **「書かれた配列の要素数の合計は、最終的な値にも残る」**  
  後続のスカラーによる上書きや、英語キーと日本語別名の優先処理で崩れる。
- **「`raw` の配列を除外すれば、記載された条件で出力不変を保証できる」**  
  引用符付きのスカラータグと、前後に空白のあるスカラー `raw` で崩れる。

## 見落としと軽微な問題

### 1. 【軽微】値なしの宣言が、後続の読めないキーを隠す

```yaml
type: "concept"
sources:
"sources": "s"
```

`source` ページの `s.md` がある状態で実行した結果：

- 0.9.3：`sourced_from → source:s` ができる。
- HEAD：`sources: []` になり、エッジはできない。
- HEAD の診断：空。グラフ lint の全検出項目も0件。

`written_times` は値なしを除くので1回、`top_level_keys()` は値なしも数えるので1回となり、引用符付きキーの読み落としが隠れる。配列要素数による検査にも掛からない。`type:\n"type": "source"`、`type: null\n"type": "source"` でも診断漏れを確認した。

前回の重複キーの反例そのものは直っているが、**同じ目的の診断漏れが残っている**。

根拠：[wiki_graph_extract.py:251](/C:/Works/info-hive-dev/.claude/worktrees/graph-frontmatter-values/info-hive-wiki/skills/info-hive/scripts/wiki_graph_extract.py:251)、[wiki_graph_extract.py:254](/C:/Works/info-hive-dev/.claude/worktrees/graph-frontmatter-values/info-hive-wiki/skills/info-hive/scripts/wiki_graph_extract.py:254)、[wiki_text.py:283](/C:/Works/info-hive-dev/.claude/worktrees/graph-frontmatter-values/info-hive-wiki/skills/info-hive/scripts/wiki_text.py:283)。

### 2. 【軽微】読めている欄を `unread_field` と誤検出する

```yaml
sources: ["a"]
sources: "b"
```

YAML の有効値も lint の値も文字列 `"b"` だが、`unread_field: sources` が出る。

配列の要素数1を加算した後、スカラーによる上書きを反映しないため、最終値が配列でないことを「読めなかった」と判定している。

次の入力でも誤検出した。

```yaml
sources: ["a"]
出典: ["b"]
```

両キーともパーサーは読めている。英語キーを優先して最終値を `["a"]` にする `canonical_meta()` の処理を、配列要素の欠落と取り違えている。

根拠：[wiki_graph_extract.py:249](/C:/Works/info-hive-dev/.claude/worktrees/graph-frontmatter-values/info-hive-wiki/skills/info-hive/scripts/wiki_graph_extract.py:249)、[wiki_graph_extract.py:266](/C:/Works/info-hive-dev/.claude/worktrees/graph-frontmatter-values/info-hive-wiki/skills/info-hive/scripts/wiki_graph_extract.py:266)、[wiki_text.py:118](/C:/Works/info-hive-dev/.claude/worktrees/graph-frontmatter-values/info-hive-wiki/skills/info-hive/scripts/wiki_text.py:118)。

### 3. 【軽微】出力不変の条件は、`raw` 配列の除外後も成立しない

次のページは、設計3の3条件を満たす。

```yaml
type: "concept"
tags: "ml"
```

旧スクリプトのノードのタグは `["m", "l"]`、HEAD は `["ml"]` だった。この変更自体は修正の意図どおりだが、**出力不変の条件からスカラータグが除かれていない**。

また、次のページも条件を満たす。

```yaml
type: "source"
raw: " raw/a.md "
```

`a.md` として構築した結果：

| | 目的語 | エッジ ID |
|---|---|---|
| 0.9.3 | `raw: raw/a.md ` | `d5210eddf7979d6c26efe6a7` |
| HEAD | `raw:raw/a.md` | `9ac047e08a657de27c5694e1` |

`ref_values()` による空白除去で、スカラー `raw` でも目的語と ID が変わる。したがって、前回の重大4は、**試験方法と配列タグの扱いは対応済みだが、互換性の記述は未解決**である。

根拠：[CHANGELOG.md:34](/C:/Works/info-hive-dev/.claude/worktrees/graph-frontmatter-values/info-hive-wiki/CHANGELOG.md:34)、[設計書:112](/C:/Works/info-hive-dev/.claude/worktrees/graph-frontmatter-values/docs/plans/wiki-graph-frontmatter-values-2026-11-11.md:112)、[wiki_graph_extract.py:482](/C:/Works/info-hive-dev/.claude/worktrees/graph-frontmatter-values/info-hive-wiki/skills/info-hive/scripts/wiki_graph_extract.py:482)。

## 検証した事実

対象 HEAD は **`c71d468`**。実行環境は **Python 3.14.6／PyYAML 6.0.3**。ファイルは変更していない。Python 3.12および申告された試験一式は再実行していない。

| 確認対象 | 結果 |
|---|---|
| 前回重大1：NUL・DEL・U+0080 | `graph` の有無を含む6入力で停止せず、診断も指定どおり |
| 前回重大2：マージ由来の `maps_from.kind` | `"2024"` になり、ページの ID は `cohort:a` |
| 前回重大3：再帰アンカー | `node_id`、関係の参照欄とも文字列化された |
| 前回の配列タグの変更 | 空白・空要素を含めて旧出力と一致 |
| 新しい golden | c50854a の抽出・lint スクリプトをメモリー上で実行し、全項目で一致 |
| HEAD と golden | ノード・エッジ・別名・診断・追加キーを除いた lint 結果が一致 |
| 最上位 meta | 試験表27入力で、`graph` 除去・参照の NFC 正規化後に lint と一致 |
| オントロジーの受理範囲 | 空・null・非マッピング・再帰アンカー・マージ・複数文書など13入力で `safe_load` 基準と一致 |
| 前回の軽微3件の元の反例 | マージの誤検出、重複キーの見逃し、独立した `graph` の喪失はいずれも再現せず |

## 崩せなかった点

- `_child()` は、検証したマージ配列の優先順位と明示値の上書きを、構築された辞書と同じに選んだ。
- `!!str`・`!!value` のキーは参照欄として取得され、`!!binary` のキーは文字列キーと混同されなかった。
- `!!binary MDA3` の参照値は、書かれた文字の `"MDA3"` になった。
- 通常の共有アンカーでは、参照欄の変換が対象外の `notes` に伝播しなかった。
- `get_single_node()` と `construct_document()` への変更による、追加のオントロジー受理・拒否の差は、検証した入力では見つからなかった。

使用した MCP サーバー: なし  
使用した Agent Skills: なし
