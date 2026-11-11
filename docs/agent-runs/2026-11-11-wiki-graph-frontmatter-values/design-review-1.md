## 判定

**条件付きで採用可。確信度：高。** 診断されずに `graph` を失う入力と、想定範囲外で既存 ID が変わる入力がある。また、試験の比較条件には、そのままでは成立しないものが含まれる。

実装は未了のため、現行関数の実行結果と、設計に明記された変更から導ける結果を区別して記す。

## 致命的・重大な欠陥

### 1. 【重大】オントロジーを据え置く判断は、規約に従ったページと、そのページへの参照を壊す

次の拡張オントロジーとページを使う。

```yaml
# ontology.yaml
node_types:
  cohort:
    maps_from: {type: entity, kind: 2024}
```

```yaml
# a.md の frontmatter
type: "entity"
kind: 2024
```

現行では両側の `kind` が整数なので、ノード ID は `cohort:a` になる。設計どおり最上位を文字列で読むと照合が外れ、型別の対応がほかなければ `concept:a` になる。別ページの、引用符で囲んだ `object: "cohort:a"` まで壊れる。

現行の関数に新旧の meta を渡して確認した結果は以下だった。

- 旧：`cohort:a`。参照元の `broken_object_refs` は空。
- 新：`concept:a`。参照元に `broken_object_refs` が発生。

ページ規約は**数値を引用符で囲まない**と定めている。「数値の kind はまず使わない」という見込みでは、この有効な拡張を互換性保証から除外できない。設計2.4は変更自体を認識しているが、3節の「規約どおりなら ID は変わらない」と両立しない。

根拠：[設計2.4](/C:/Works/info-hive-dev/.claude/worktrees/graph-frontmatter-values/docs/plans/wiki-graph-frontmatter-values-2026-11-11.md:75)、[互換性の主張](/C:/Works/info-hive-dev/.claude/worktrees/graph-frontmatter-values/docs/plans/wiki-graph-frontmatter-values-2026-11-11.md:83)、[型の照合と既定ID](/C:/Works/info-hive-dev/.claude/worktrees/graph-frontmatter-values/info-hive-wiki/skills/info-hive/scripts/wiki_graph_extract.py:229)、[ページ規約](/C:/Works/info-hive-dev/.claude/worktrees/graph-frontmatter-values/info-hive-wiki/skills/info-hive/references/page-conventions.md:25)。

### 2. 【重大】`unreadable_graph` の条件は、実際に受け付ける `graph` の書き方を網羅していない

反例：

```yaml
type: "concept"
title: a: b
"graph":
  node_id: "concept:a"
```

この入力では、

1. lint のパーサーは引用符付きキーを読まないため、meta に `graph` がない。
2. PyYAML は `title: a: b` で失敗する。
3. 設計2.1に従って `graph` が除かれる。
4. 設計2.3の「lint の形に `graph` のキーがある」を満たさず、診断されない。

`title` を正常にすると、現行のグラフ処理は同じ `"graph":` を正常に読むことも確認した。設計2.1でも、PyYAML のマッピングから取得するので受け付ける書き方である。**正常時には読む宣言を、異常時の存在判定だけが見落とす。**

根拠：[graphの取得条件](/C:/Works/info-hive-dev/.claude/worktrees/graph-frontmatter-values/docs/plans/wiki-graph-frontmatter-values-2026-11-11.md:26)、[診断条件](/C:/Works/info-hive-dev/.claude/worktrees/graph-frontmatter-values/docs/plans/wiki-graph-frontmatter-values-2026-11-11.md:64)、[lint側の読み込み](/C:/Works/info-hive-dev/.claude/worktrees/graph-frontmatter-values/info-hive-wiki/skills/info-hive/scripts/wiki_lint.py:300)。

### 3. 【重大・実装依存】PyYAML の構築時例外が、失敗経路と試験から抜けている

反例：

```yaml
type: "concept"
created: 2026-13-01
graph:
  node_id: 007
```

PyYAML 6.0.3 の `safe_load()` は、これを `yaml.YAMLError` ではなく **`ValueError`** で停止させる。同様に次の入力も `ValueError` になる。

```yaml
graph: {node_id: !!float nope}
```

現行の `parse_frontmatter()` が捕捉するのは `yaml.YAMLError` だけであり、実際にこの例外は捕捉されない。lint の文字列パーサーと BaseLoader は、どちらの入力も読めた。

設計は「PyYAML が読めなければ最上位は保持し、診断する」としているが、構築時例外の扱いを明記していない。**現行の捕捉範囲を引き継ぐ実装では、ページ単位の診断になる前に処理全体が止まる。** 新実装でも残るかは未確認だが、現行での再現と試験項目の欠落は確認済み。

根拠：[失敗時の設計](/C:/Works/info-hive-dev/.claude/worktrees/graph-frontmatter-values/docs/plans/wiki-graph-frontmatter-values-2026-11-11.md:62)、[試験4.5](/C:/Works/info-hive-dev/.claude/worktrees/graph-frontmatter-values/docs/plans/wiki-graph-frontmatter-values-2026-11-11.md:114)、[現行の例外捕捉](/C:/Works/info-hive-dev/.claude/worktrees/graph-frontmatter-values/info-hive-wiki/skills/info-hive/scripts/wiki_graph_extract.py:152)。

## 崩れる前提

- **「ID が変わるのは `graph` の参照欄を直す関係だけ」**  
  最上位の参照先が変わるだけでも崩れる。`sources: [1.10]` と `1.1.md`・`1.10.md` を用意すると、旧処理は `source:1.1`、新しい読み方は `source:1.10` を指す。実行した例ではエッジ ID も `d43808a16a628c03782fa65a` から `0df45802e139856c08913102` に変わった。`graph` は不要である。[設計の限定](/C:/Works/info-hive-dev/.claude/worktrees/graph-frontmatter-values/docs/plans/wiki-graph-frontmatter-values-2026-11-11.md:104)とは食い違う。

- **「同じパーサーを使えば、最終的な最上位 meta も同じ」**  
  グラフ側だけが後段で `normalize_refs()` を通る。`sources: ["カ\u3099"]` を実際の分解文字で書くと、lint は分解形、グラフは NFC の `"ガ"` になる。参照解決上の同一性と、辞書の完全一致は別である。

- **「少数の既存 wiki に例がなければ、後退の影響は限定できる」**  
  調査対象外の利用者や、規約を拡張した wiki では成立しない。配列の後退を受け入れる判断自体は明示されているが、ローカルの不在確認は利用者全体の互換性の根拠にならない。

## 見落としと軽微な問題

### 【軽微】試験4.2の比較式は、通常の `graph:` があるだけで不一致になる

記述どおりグラフ側だけから `graph` を除くと、lint 側には `graph: []` が残る。

```text
グラフ側：{"type": "concept"}
lint側 ：{"type": "concept", "graph": []}
```

この不一致を実測した。さらに前述の NFC 差もあるため、指定された試験は、正常な実装でもそのままでは通らない。

根拠：[試験4.2](/C:/Works/info-hive-dev/.claude/worktrees/graph-frontmatter-values/docs/plans/wiki-graph-frontmatter-values-2026-11-11.md:111)。

### 【軽微】試験4.3の「ノードが等しい」は、規約の日付で成立しない

`created: 2026-04-15` は、現行ノードでは `datetime.date`、新しい読み方では文字列になる。ノード辞書の比較は不一致になる。

一方、現行の JSON 正規化後は両方とも `"2026-04-15"` になった。**内部辞書の一致と、生成物の一致が区別されていない。**

根拠：[試験4.3](/C:/Works/info-hive-dev/.claude/worktrees/graph-frontmatter-values/docs/plans/wiki-graph-frontmatter-values-2026-11-11.md:112)、[ノードの日付欄](/C:/Works/info-hive-dev/.claude/worktrees/graph-frontmatter-values/info-hive-wiki/skills/info-hive/scripts/wiki_graph_extract.py:318)。

### 【軽微・推測】アンカーが共有する可変オブジェクトの扱いが未定義

```yaml
graph:
  aliases: &a [007]
  relationships:
    - predicate: "depends_on"
      object: "concept:x"
      notes: *a
```

SafeLoader では `aliases` と `notes` が同じリストになる。`aliases[0]` をその場で `"007"` に置き換えると、対象外とした `notes` まで整数から文字列へ変わる。共有される事実と変更の伝播は実測した。

実装がコピーを作れば発生しないため、欠陥の発生は推測。ただし設計は共有オブジェクトの扱いを定めておらず、試験もこの副作用を確かめない。

根拠：[位置による置換](/C:/Works/info-hive-dev/.claude/worktrees/graph-frontmatter-values/docs/plans/wiki-graph-frontmatter-values-2026-11-11.md:53)、[対象外の欄](/C:/Works/info-hive-dev/.claude/worktrees/graph-frontmatter-values/docs/plans/wiki-graph-frontmatter-values-2026-11-11.md:58)。

### 【軽微】0.9.5 の判断理由は、変更の範囲を過小評価している

診断キーの追加だけでなく、規約に沿う数値の型対応、既存ノード ID、その ID を指す別ページにも影響する。0.9.2に類例があることだけでは、今回の互換性の根拠にならない。

ただし、**このリポジトリの運用から、0.9.5という番号自体を禁止する根拠は確認できなかった。** 問題は番号そのものより、設計が掲げる影響範囲との食い違いである。

## 検証した事実

実行環境は **Python 3.14.6／PyYAML 6.0.3**。Python 3.12では未検証。ファイルは変更していない。

| 確認対象 | 結果 |
|---|---|
| lint とグラフの frontmatter 切り出し正規表現 | 一致 |
| 型変換による `007`・`1.10`・`yes` の差 | 設計の説明と一致 |
| NFC適用後の最上位metaの完全一致 | 分解文字で不一致 |
| 数値kindと据え置きオントロジー | ノードID変更と別ページの参照切れを確認 |
| 無効な日付・明示タグの失敗 | `YAMLError` 以外の `ValueError` を確認 |
| マージで継承した参照欄 | SafeLoaderには欄があり、BaseLoaderの同じ位置にはない |
| 同じ参照キーの重複 | 通常の例では両ローダーとも後の値を採用 |
| 複雑な配列キー | 両ローダーとも `ConstructorError` |
| ローカルの配列不在調査 | この作業ツリーの `wiki/` と指定fixtureでは一致。ユーザースコープ全体は未確認 |
| PR #38の現在の状態・0.9.4の予約 | 未確認 |

## 崩せなかった点

- 通常のアンカー参照と同じキーの重複では、対応する位置から別の値を誤取得する例は作れなかった。
- マージ由来の欄が BaseLoader 側にない場合に、元の値を残すという分岐自体は崩せなかった。
- `None` を保持しても、`"null"`・`"~"` と引用すれば文字列の参照を表せる。値なしとの区別を維持する判断に、重大な反例は見つからなかった。
- BaseLoader が任意の Python オブジェクトを構築するという根拠は見つからなかった。アンカー共有の副作用とは別の問題である。

使用した MCP サーバー: なし  
使用した Agent Skills: なし
