## 判定

**却下。確信度：高。** ページ1件で処理全体が停止する回帰と、マージキー・再帰アンカーによって参照が壊れる入力を再現した。また、条件を満たすページでも出力が変わり、現在の互換性試験では検出できない。

## 致命的・重大な欠陥

### 1. 【重大】`SafeLoader` の初期化例外が漏れ、ページ収集全体が停止する

次の文字列を `read_frontmatter()` に渡す。`\x00` は、バックスラッシュ表記ではなく実際の NUL 文字である。

```python
text = '---\ntype: "concept"\ntitle: "a\x00b"\ngraph: {}\n---\n本文\n'
```

結果は `yaml.reader.ReaderError`。`unreadable_graph` を返す前に停止する。U+007F、U+0080でも再現し、`graph` のないページでも発生した。

原因は、`yaml.SafeLoader(fm_text)` が例外処理の外にあること。`collect_pages()` の直接呼び出しでも例外が漏れた。旧コミットの `parse_frontmatter()` は同じ入力を捕捉し、空の meta を返したため、**今回導入された停止の回帰**である。

グラフの lint も同じ収集関数を使う。MCP の `lint_graph()` にもこの例外の捕捉がなく、ページ単位の診断にならない。

根拠：[wiki_graph_extract.py:264](/C:/Works/info-hive-dev/.claude/worktrees/graph-frontmatter-values/info-hive-wiki/skills/info-hive/scripts/wiki_graph_extract.py:264)、[wiki_mcp_server.py:118](/C:/Works/info-hive-dev/.claude/worktrees/graph-frontmatter-values/info-hive-wiki/skills/info-hive/scripts/wiki_mcp_server.py:118)。

### 2. 【重大】マージで継承した `maps_from` は文字列化されず、既存のノード ID と参照が壊れる

オントロジー：

```yaml
base: &b {type: entity, kind: 2024}
node_types:
  cohort:
    maps_from: {<<: *b}
predicates: {}
```

ページ `a.md`：

```yaml
type: "entity"
kind: 2024
```

実測結果：

| | 読み込んだ `maps_from.kind` | ノード ID |
|---|---|---|
| 旧コミット | 整数 `2024` | `cohort:a` |
| 新実装 | 整数 `2024` | `concept:a` |

ページ側だけが文字列 `"2024"` になる。別ページからの `object: "cohort:a"` は、旧版では正常、新版では `broken_object_refs` になった。

`BaseLoader` は `<<` を展開しないため、`written_maps` に `kind` が存在せず、置換が実行されない。型定義全体をマージで継承した場合も同じ経路に入る。これは CHANGELOG とワークフローの「`maps_from` も書かれた文字で比べる」という説明に対する反例である。

根拠：[wiki_graph_extract.py:402](/C:/Works/info-hive-dev/.claude/worktrees/graph-frontmatter-values/info-hive-wiki/skills/info-hive/scripts/wiki_graph_extract.py:402)、[graph-workflow.md:82](/C:/Works/info-hive-dev/.claude/worktrees/graph-frontmatter-values/info-hive-wiki/skills/info-hive/references/graph-workflow.md:82)。

### 3. 【重大】無関係な再帰アンカーで、参照欄すべての文字列化が無診断で失敗する

```yaml
type: "concept"
graph: &g
  node_id: 007
  unused: *g
```

`read_frontmatter()` は正常終了するが、`graph.node_id` は文字列 `"007"` ではなく整数 `7`。診断は空だった。

別ページに次の関係を書くと、

```yaml
graph:
  relationships:
    - predicate: depends_on
      object: 007
      source: s
      evidence: "x"
      confidence: high
      status: current
```

参照元の `object` は `"007"` に変換される一方、参照先の ID は `"7"` になる。実際に `broken_object_refs` が発生し、`unreadable_graph` は空だった。

SafeLoader は再帰するマッピングを構築できるが、同じ木を組み立てる `BaseConstructor` は失敗する。その例外を捕捉した後、**全参照欄を元の型のまま返している**。再帰部分を出力に使わなくても発生する。

根拠：[wiki_graph_extract.py:199](/C:/Works/info-hive-dev/.claude/worktrees/graph-frontmatter-values/info-hive-wiki/skills/info-hive/scripts/wiki_graph_extract.py:199)。

### 4. 【重大】出力不変の保証が成立せず、互換性試験もその差を見逃す

次のページは設計3の両条件を満たす。

```yaml
type: "source"
raw: ["raw/a.md", "raw/b.md"]
```

旧コミットの構築関数と現行関数を実行して比較した結果：

- 旧版：目的語が `raw:['raw/a.md', 'raw/b.md']` のエッジ1本。
- 新版：目的語が `raw:raw/a.md`、`raw:raw/b.md` のエッジ2本。IDも変わる。

この変更自体は修正意図5どおりだが、**意図6および CHANGELOG の出力不変保証とは両立しない**。

さらに、次の入力では meta 自体が新旧で等しいのに、ノードのタグが変わる。

```yaml
type: "concept"
tags: [" a ", "", "x"]
```

旧版は `[" a ", "", "x"]`、新版は `["a", "x"]`。`ref_values()` が空白除去と空要素の除外まで行うためである。

互換性試験の `compare()` は、新旧両方の meta を**現行の** `build_nodes()`・`build_edges()` に渡す。上記2例をこの比較関数に渡すと、どちらも通った。旧版の構築処理との差は検証されていない。

根拠：[wiki_graph_extract.py:519](/C:/Works/info-hive-dev/.claude/worktrees/graph-frontmatter-values/info-hive-wiki/skills/info-hive/scripts/wiki_graph_extract.py:519)、[wiki_graph_extract.py:751](/C:/Works/info-hive-dev/.claude/worktrees/graph-frontmatter-values/info-hive-wiki/skills/info-hive/scripts/wiki_graph_extract.py:751)、[test_graph_frontmatter_values.py:441](/C:/Works/info-hive-dev/.claude/worktrees/graph-frontmatter-values/tests/wiki/test_graph_frontmatter_values.py:441)、[CHANGELOG.md:34](/C:/Works/info-hive-dev/.claude/worktrees/graph-frontmatter-values/info-hive-wiki/CHANGELOG.md:34)。

## 崩れる前提

- **「YAML の読めない入力は、既存の例外処理で診断になる」**  
  ローダー生成時に失敗する文字で崩れる。
- **「SafeLoader が構築できた木は、BaseConstructor でも構築できる」**  
  再帰アンカーで崩れる。失敗は参照欄の変換全体に波及する。
- **「2つのローダーで同じキーを引けば、同じ有効値を取得できる」**  
  オントロジーのマージキーで崩れる。
- **「旧 meta と比較すれば、旧版の出力との互換性を確かめられる」**  
  構築関数自体を変更した場合に崩れる。

## 見落としと軽微な問題

### 【軽微】`unread_field` がマージで上書きされた値まで数え、誤検出する

```yaml
base: &b {sources: ["a"]}
<<: *b
sources: ["b"]
```

YAML の有効値も lint の値も `["b"]` なのに、`unread_field: sources` が出た。展開後の既定値と明示値を両方加算するためである。

根拠：[wiki_graph_extract.py:239](/C:/Works/info-hive-dev/.claude/worktrees/graph-frontmatter-values/info-hive-wiki/skills/info-hive/scripts/wiki_graph_extract.py:239)。

### 【軽微】重複したスカラー欄では、読めなかったキーを見逃す

```yaml
type: "concept"
"type": "source"
```

結果は `type: concept`、診断なし。YAML の有効値は `source` である。

同様に、

```yaml
sources: ["a"]
"sources": "b"
```

も結果は `["a"]`、診断なし。「キーが既にある」「配列の要素数が足りる」だけでは、後続の読めなかった宣言を検出できない。

根拠：[wiki_graph_extract.py:248](/C:/Works/info-hive-dev/.claude/worktrees/graph-frontmatter-values/info-hive-wiki/skills/info-hive/scripts/wiki_graph_extract.py:248)。

### 【軽微】外側の値が影響しないという説明は、実装より広い

```yaml
type: concept
<<: 3
graph: {node_id: x}
```

構文木の取得後、最上位の `flatten_mapping()` が失敗し、独立した `graph` も失われる。`unreadable_graph: yaml_error` は出るが、ワークフローの「構文が読めれば、外側の値はどう書いてあっても影響しない」には反する。

根拠：[wiki_graph_extract.py:269](/C:/Works/info-hive-dev/.claude/worktrees/graph-frontmatter-values/info-hive-wiki/skills/info-hive/scripts/wiki_graph_extract.py:269)、[graph-workflow.md:69](/C:/Works/info-hive-dev/.claude/worktrees/graph-frontmatter-values/info-hive-wiki/skills/info-hive/references/graph-workflow.md:69)。

## 検証した事実

実行環境は **Python 3.14.6／PyYAML 6.0.3**。Python 3.12と、申告された試験一式の通過は再確認していない。ファイルは変更していない。

- 対象コミットの HEAD は `a38c537` と一致。親コミットのコードをメモリー上で実行し、新旧の実装を比較した。
- 試験表の27入力について、両 `collect_pages()` の meta は、双方の `graph` 除去と参照の NFC 正規化後にすべて一致した。
- fixture の4ページは、現行グラフ lint の全検出項目が0件だった。
- `fm_problems` のない手製ページは、`build_nodes()` とグラフ lint の両方で処理できた。
- 上記4件の重大な指摘と、診断の誤検出・見逃しは関数呼び出しで再現した。

## 崩せなかった点

- 通常のグラフ内マージでは、継承した `object: 007`・`source: no` が正しく文字列になった。
- 通常の重複した `node_id` は、後の値を正しく採用した。
- `aliases` と `notes` が共有する通常のアンカーでは、置換後も `notes` の整数は保持された。
- グラフ内の `null`・`~` は値なしのまま保持された。
- 通常入力では、同じ構文木を2種類の constructor に渡すことによる追加の誤置換は確認できなかった。

使用した MCP サーバー: なし  
使用した Agent Skills: なし
