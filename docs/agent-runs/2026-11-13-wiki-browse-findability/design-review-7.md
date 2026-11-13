## 判定

**条件付きで採用可。分類 A の反例は得られませんでした。確信度：中。** 試作に分類 B の重大な欠陥が2件残っています。実ブラウザでの検証は未実行です。

## 致命的・重大な欠陥

### 【B・重大】未知のグループ ID で全ページが隠れ、解除用の印も出ない

**設計本文は正しいものの、試作が従っていません。**

グループ `_g1` に属するページが1件ある状態で、索引を次の URL で開きます。

```text
index.html#group=_g999
```

設計4.3は「知らない ID なら、絞り込みをせず、印も出さない」と定めています。しかし、試作の `fromHash()` は存在確認をせず `_g999` を採用します。`apply()` は全行を隠し、存在しないグループの解除ボタンも隠します。

該当関数を抽出し、メモリ上の DOM 代替で**実行済み**です。

```text
state.group = "_g999"
件数 = "1 件中 0 件"
ページの hidden = true
グループの解除ボタンの hidden = true
```

また、`#group=_g1garbage` は、存在しない ID として扱われず、部分一致した `_g1` の絞り込みになります。ブラウザでの操作は未実行です。

根拠：[設計4.3](C:/Works/info-hive-dev/.claude/worktrees/wiki-browse-findability/docs/plans/wiki-browse-findability-2026-11-13.md:289)、[fromHash()](C:/Works/info-hive-dev/.claude/worktrees/wiki-browse-findability/poc/browse-findability/assets/proto.js:364)、[行の絞り込み](C:/Works/info-hive-dev/.claude/worktrees/wiki-browse-findability/poc/browse-findability/assets/proto.js:339)、[解除ボタンの表示](C:/Works/info-hive-dev/.claude/worktrees/wiki-browse-findability/poc/browse-findability/assets/proto.js:354)。

### 【B・重大】題名と異なる h1 にしかない語を、試作では引き続き検索できない

次のページを使います。索引は不要です。

```markdown
---
type: concept
title: Operations
---

# StartupFailure

Lead.
```

現行 `Core` は見出しを次のように保持します。

```text
[("startupfailure", "startupfailure", "StartupFailure")]
```

しかし、試作の `load_pages()` は `<h2>`〜`<h6>` だけを抽出するため、検索用の見出しは空になります。

```text
title = "Operations"
headings = []
lead = "Lead."
```

`StartupFailure` は検索対象のどの欄にも残らず、検索結果が0件になります。第1回レビューで設計について指摘された反例が、試作には残っています。

**メモリ上の `Snapshot` → 現行 `Core` の HTML 描画 → 試作の `load_pages()` を実行して確認しました。** ブラウザでの入力操作は未実行です。

設計5.1は h1〜h6をすべて含めると明記しているため、分類 B です。

根拠：[設計5.1](C:/Works/info-hive-dev/.claude/worktrees/wiki-browse-findability/docs/plans/wiki-browse-findability-2026-11-13.md:311)、[試作の見出し抽出](C:/Works/info-hive-dev/.claude/worktrees/wiki-browse-findability/poc/browse-findability/proto.py:82)、[検索用データの生成](C:/Works/info-hive-dev/.claude/worktrees/wiki-browse-findability/poc/browse-findability/proto.py:386)。

## 崩れる前提

- **【B】ハッシュから取り出せたグループ ID は、木にも存在する。** `_g999` のような未知の ID で崩れます。現在の正規表現は、ID 全体の一致も保証していません。
- **【B】h1を検索から除いても、題名から同じ語を探せる。** 題名とh1が異なるページで崩れます。設計本文はこの前提を撤回していますが、試作の抽出処理は残っています。
- **【C】試作で検索できれば、設計した検索の読み込みまで確かめられる。** 試作は `data/search.js` を最初から読みます。フォーカスを契機とする遅延読み込みについて、試作の成功は証拠になりません。根拠：[試作の tail()](C:/Works/info-hive-dev/.claude/worktrees/wiki-browse-findability/poc/browse-findability/proto.py:254)、[設計5.4](C:/Works/info-hive-dev/.claude/worktrees/wiki-browse-findability/docs/plans/wiki-browse-findability-2026-11-13.md:362)。

## 見落としと軽微な問題

### 【C・軽微】「参照実装の出力をそのまま写した表」に1ケース足りない

参照実装の `CASES` は19件ですが、設計2.1の表は18件です。今回追加したハッシュ衝突のケースが表にありません。第9節の「2.1の表の19の索引」とも一致しません。

これは表の掲載漏れであり、分類 A には数えません。

根拠：[表についての説明](C:/Works/info-hive-dev/.claude/worktrees/wiki-browse-findability/docs/plans/wiki-browse-findability-2026-11-13.md:117)、[追加したケース](C:/Works/info-hive-dev/.claude/worktrees/wiki-browse-findability/docs/agent-runs/2026-11-13-wiki-browse-findability/nav_model.py:291)、[試験の説明](C:/Works/info-hive-dev/.claude/worktrees/wiki-browse-findability/docs/plans/wiki-browse-findability-2026-11-13.md:423)。

### 【C・軽微】参照実装の `check()` は5番目の性質を検査しない

`check()` は、グループ項目の `label` と行き先の名前が等しいことを検査していません。今回の追加検証では別途照合し、不一致はありませんでした。検査の網羅についての指摘です。

根拠：[check()](C:/Works/info-hive-dev/.claude/worktrees/wiki-browse-findability/docs/agent-runs/2026-11-13-wiki-browse-findability/nav_model.py:204)、[5番目の性質](C:/Works/info-hive-dev/.claude/worktrees/wiki-browse-findability/docs/plans/wiki-browse-findability-2026-11-13.md:148)。

## 検証した事実

| 確かめた主張 | 結果 |
| --- | --- |
| 参照実装の19ケースを組み立てられる | **一致**。メモリ上の `Snapshot` で全件成功 |
| 設計2.1に掲載された18例と参照実装の出力 | **一致** |
| 第6回のハッシュ衝突への対応 | **解消を確認**。2ファイルのグループが別IDで残る |
| N2〜N8と木の5つの性質 | **追加生成した750ケースで成立**。`label` の一致も別途検査 |
| 第6回の試作のグループリンク形式 | **修正を確認**。`itemLink()` は `#group=` を生成 |
| 要約・検索データが機械の絶対パスやトークンを追加しない | **設計上の食い違いは発見せず**。構造変更後の実装は未検証 |
| 遅延読み込み、CSP、`file://`、サーバーのトークン付きURL、起動時間 | **確かめられず**。実ブラウザ試験は未実行 |

ファイルは変更していません。反例の実行はメモリ上に限定しました。

## 崩せなかった点

- ファイルグループの番号と、見出し等の通し番号が衝突する入力。
- N3の1回の圧縮とN6の除去により、索引に載ったページが失われる入力。
- 中継・相互参照・自己参照によって、木から消したグループへのリンクが残る入力。
- NFCで同じになるファイル名や空白を含む種類によって、グループIDを識別できなくなる入力。
- 4.2・5.1の規則に従うことで、P7に反して生成器が機械の情報を追加する経路。

使用した MCP サーバー: なし  
使用した Agent Skills: なし
