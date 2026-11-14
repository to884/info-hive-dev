## 判定

**却下。分類 A が1件あります。確信度：高。** 読み書きの失敗も競合もない入力で、既存IDの維持とグループIDの一意性を同時に満たせません。以下の B・C は却下の理由に含めません。

## 致命的・重大な欠陥

### 【A・重大】別々の索引ファイルに同じIDが付き、設計の規則を同時に満たせない

次の2つの索引ファイルを置きます。`concepts/a.md`、`concepts/b.md` は、必須の frontmatter を持つ通常の別ページです。`index.md` は不要です。

```python
{
    "indexes/probe-910039.md": "# A\n- [[a]]\n",
    "indexes/probe-1542287.md": "# B\n- [[b]]\n",
}
```

現行の `short_hash()` を実行すると、両方のパスの SHA-256 の先頭10桁が **`81823b0577`** になります。したがって、N1 の `Core._nav()` は、別々の索引に同じ **`_g81823b0577`** を付けます。

これにより、設計の次の要求が両立しません。

- N5：索引ファイルをグループIDで見分け、各ファイルのグループを並べる。
- 2.2：第2段は既存IDを使い、新しいIDを作らない。
- 2.1末尾：木のグループIDは重ならず、第2段の前後で索引に載ったページの集合が変わらない。

**実行済みです。** メモリ上の `Snapshot` から現行 `Core` と参照実装を実行しました。第1段には同じIDの2グループが残り、第2段は次で停止しました。

```text
AssertionError: 2 つ目の段で、索引に載ったページが変わった
```

参照実装では `by_id` が片方を上書きします。ただし、上書きだけを直して両方を残してもIDの一意性が破れます。設計の検査で停止させることはできますが、正常に読めるこの入力について、規定された木を組めません。参照実装だけの B ではありません。

根拠：[設計 N5](C:/Works/info-hive-dev/.claude/worktrees/wiki-browse-findability/docs/plans/wiki-browse-findability-2026-11-13.md:104)、[木の5つの性質とIDの維持](C:/Works/info-hive-dev/.claude/worktrees/wiki-browse-findability/docs/plans/wiki-browse-findability-2026-11-13.md:134)、[現行のハッシュ関数](C:/Works/info-hive-dev/.claude/worktrees/wiki-browse-findability/info-hive-wiki/skills/info-hive/scripts/wiki_browse_core.py:260)、[参照実装のID辞書](C:/Works/info-hive-dev/.claude/worktrees/wiki-browse-findability/docs/agent-runs/2026-11-13-wiki-browse-findability/nav_model.py:93)。

### 【B・重大】試作 D のグループ項目から移動すると、一覧が絞られない

試作の `itemLink()` は、グループへの項目を次のURLにします。

```text
index.html#_g2
```

一方、D の `fromHash()` が読む形式は `#group=_g2` です。記事の木でグループ項目を押しても、索引のページはグループ指定を認識せず、全ページを表示します。

例えば、`index.md` に `a` と `indexes/x`、`indexes/x.md` に `b` を載せます。記事の木から X のグループ項目を押すと、期待する `b` の1件への絞り込みが成立しません。

**該当関数をメモリ上で実行済みです。** `itemLink()` の出力が `index.html#_g2` で、`fromHash()` の正規表現が一致しないことを確認しました。ブラウザでのクリック操作は未実行です。

設計3.1は `index.html#group=<ID>` と明記しているため、これは B です。

根拠：[試作のリンク生成](C:/Works/info-hive-dev/.claude/worktrees/wiki-browse-findability/poc/browse-findability/assets/proto.js:167)、[試作のハッシュ解析](C:/Works/info-hive-dev/.claude/worktrees/wiki-browse-findability/poc/browse-findability/assets/proto.js:362)、[設計3.1](C:/Works/info-hive-dev/.claude/worktrees/wiki-browse-findability/docs/plans/wiki-browse-findability-2026-11-13.md:187)。

## 崩れる前提

- **【A】ディスク上の綴りをハッシュ化すれば、索引ファイルを一意に識別できる。** 上記の2ファイルで崩れます。NFCへの正規化を避けても、40ビットへの切り詰めによる衝突は残ります。
- **【B】グループ項目のリンク形式が、試作 D の絞り込みと共通である。** `#_g2` と `#group=_g2` が混在しています。
- **【C】U+001F はタグの内容に現れない。** 現行パーサーは、二重引用符内の `\u001f` をその文字として読みます。タグに追加の制限を設けない Wiki では、この前提は成立しません。

## 見落としと軽微な問題

### 【C・軽微】`data-tags` 単独では元のタグ集合を復元できない

次の異なるタグ集合が、4.1の区切り方では同じ属性値になります。

```text
["one\u001ftwo"] → "one\u001ftwo"
["one", "two"]   → "one\u001ftwo"
```

現行の frontmatter パーサーと区切り処理を実行して確認しました。前者は、正しく引用した YAML のタグ1つとして読み込まれます。

試作は属性を U+001F で分割するため、前者も `one` と `two` の2タグとして数えます。ただし、設計のHTMLには個別のタグ要素もあり、設計文だけから画面の誤動作が必ず起きるとは断定しません。ここではデータ表現の限界として C に分類します。

根拠：[設計4.1](C:/Works/info-hive-dev/.claude/worktrees/wiki-browse-findability/docs/plans/wiki-browse-findability-2026-11-13.md:240)、[試作のタグ集計](C:/Works/info-hive-dev/.claude/worktrees/wiki-browse-findability/poc/browse-findability/assets/proto.js:315)。

### 【C・軽微】試験の説明に古い件数が残っている

第9節は「木を組み終えたあとの **2つ**の性質」「上の **7つ**の索引」と書いています。現在の本文は5つの性質と18例です。実装者が試験項目を数える際に食い違います。

根拠：[第9節の該当行](C:/Works/info-hive-dev/.claude/worktrees/wiki-browse-findability/docs/plans/wiki-browse-findability-2026-11-13.md:409)。

## 検証した事実

| 確かめた主張 | 結果 |
| --- | --- |
| 設計2.1の表と参照実装の出力 | **一致**。18例すべてをメモリ上の `Snapshot` で比較 |
| 第5回のNFC衝突・空白を含む種類・別名の指摘への対応 | **掲載例では解消** |
| 通常の木で、所属・件数・グループ参照が整合する | **追加生成した300例で一致**。別途、項目の `label` も検査 |
| 現行の索引ファイルIDが一意である | **食い違い**。具体的な2ファイル名で衝突・組み立て停止を確認 |
| 試作 D のグループ項目が絞り込み用URLを作る | **食い違い** |
| 実ブラウザでの遅延読み込み、CSP、`file://`、トークン付きURL、起動時間 | **確かめられず**。実ブラウザ試験は未実行 |

ファイルは変更していません。反例の実行はメモリ上に限定しました。

## 崩せなかった点

- ハッシュ衝突を除く検証入力では、N2〜N8によってページの所属が消えたり、木にないグループへの参照が残ったりする例は作れませんでした。
- N3の1回だけの圧縮、N6によるグループだけの包みの除去、中継・相互参照・自己参照の扱いは、検証入力で成立しました。
- 要約と検索データを入力内容から作る規則について、生成器が機械の絶対パスやトークンを追加する経路は見つかりませんでした。
- 索引編集後のグループIDの意味の変化は、第11節の明記された限界として扱いました。

使用した MCP サーバー: なし  
使用した Agent Skills: なし
