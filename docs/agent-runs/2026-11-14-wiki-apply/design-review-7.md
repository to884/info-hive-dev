## 判定

**却下。確信度：高。** APで追加した参照定義の比較が、リンク先を変えない通常のログ追記を拒む。パス検査にも、新しいページ自身が子 wiki の目印になる場合の規定が不足している。

未実装の設計への判定である。パーサーはメモリ上で検証した。適用・復旧・プロセス停止の実機試験は行っていない。

## 致命的・重大な欠陥

**1.【重大】`references` の比較に行番号が入り、通常のログ追記ができなくなる**

変更前の `log.md` を次とする。

```markdown
## [2026-11-14] ingest | A
   See [doc][r].

[r]: https://old.example
```

次を登録する。

```text
log-entry --op ingest --date 2026-11-14 --title B --line added
```

参照定義はブロックトークンを作らないため、283行の規則では、Aの段落と末尾の参照定義の間へ新しい項目を挿入する。

同梱パーサーで確認すると、参照の表は次のように変わった。

```python
# 前
{"R": {"title": "", "href": "https://old.example", "map": [3, 4]}}

# 後
{"R": {"title": "", "href": "https://old.example", "map": [6, 7]}}
```

既存リンクの `href` と子トークンは変わらず、ブロック列も規定された追加と一致する。しかし、**255行の「`env` の `references` が当てる前と同じ」という条件だけに違反する。**

末尾に参照定義がある限り、追加文を別の普通の文へ変えても定義の行番号は動く。`log.md` は `ops` だけなので、設計された操作では追記を完了できない。これは危険なMarkdownを拒む場合とは異なり、通常の追記を拒む反例である。

根拠：[設計・参照定義の比較](/C:/Works/info-hive-dev/.claude/worktrees/wiki-apply-design/docs/plans/wiki-apply-2026-11-14.md:255)、[挿入位置](/C:/Works/info-hive-dev/.claude/worktrees/wiki-apply-design/docs/plans/wiki-apply-2026-11-14.md:283)、[同梱パーサーが `map` を保存する箇所](/C:/Works/info-hive-dev/.claude/worktrees/wiki-apply-design/info-hive-wiki/skills/info-hive/scripts/_vendor/markdown_it/rules_block/reference.py:197)。

対照表661行の「ふつうの追記を拒むことは生じない」は、APを含む第7版では成立しない。

**2.【重大・仕様の欠落】ページの新規作成によって、既存ディレクトリを子 wiki に変えられる**

この指摘では、3節の特殊扱いを、定義どおり**ルート相対パスの `SCHEMA.md`** に対する制約と解した。全階層で同名の最終要素を予約する意味なら反例は成立しないが、その指定は書かれていない。

Windowsの通常の、大文字と小文字を区別しない配置を考える。

```text
W/SCHEMA.md
W/sources/既存資料.md
W/sources/schema.md       まだない
```

1. `new --path sources/schema.md` を登録し、通常のsourceページを用意する。
2. パスのキーは `sources/schema.md` で、ルートの `SCHEMA.md` とは異なる。
3. 登録・`diff`・適用手順4では、`sources` に目印がまだないため、`nested_wiki` に当たらない。
4. 新しいページを置く。
5. 次の取り込みが `sources/別資料.md` を登録すると、今度は `sources/SCHEMA.md` が見つかり、`nested_wiki` で拒まれる。

初期化判定はファイルの中身を見ない。そのため、**普通のsourceページでも、名前だけで `sources` 全体を子 wiki に変える。** 以後、既存sourceページの編集も親 wiki から拒まれる。削除は書く段の対象外なので、この状態を親の計画で解除する操作もない。

初期化判定が通常ファイルの存在だけで成功することは、既存関数に模擬の `stat` 結果を渡して確認した。新しい適用処理自体は未実装なので、実行結果は未確認である。

根拠：[設計・パスの定義と特殊扱い](/C:/Works/info-hive-dev/.claude/worktrees/wiki-apply-design/docs/plans/wiki-apply-2026-11-14.md:222)、[子 wiki の検査](/C:/Works/info-hive-dev/.claude/worktrees/wiki-apply-design/docs/plans/wiki-apply-2026-11-14.md:231)、[初期化判定](/C:/Works/info-hive-dev/.claude/worktrees/wiki-apply-design/info-hive-wiki/skills/info-hive/scripts/wiki_initialized.py:67)、[ADR-0019](/C:/Works/info-hive-dev/.claude/worktrees/wiki-apply-design/docs/adr/0019-wiki-root-is-marked-by-schema.md:20)。

## 崩れる前提

| 前提 | 崩れる条件 |
| --- | --- |
| 参照定義の表の一致は、リンクの意味が変わらないことと一致する | 同梱パーサーの表には、追記で動く `map` も入る |
| 操作前に子 wiki がなければ、操作後も同じ wiki に属する | 新規ページの名前が `SCHEMA.md` として認識される |
| 文書の全段落とPythonの書き込み箇所を分類すれば、書き込み指示を網羅できる | スクリプトの出力メッセージが書き込みを指示する |

## 見落としと軽微な問題

- **【軽微】全項目が `unchanged` の場合、飛び先の手順が成立しない。** 356行は日誌を書かずに9へ進むが、9は `manifest.json` を `done` に更新する。また、結果を一律 `written` と説明している。日誌がない場合の分岐がなく、555行の試験も「ほかの項目が当たる」混在ケースだけである。[手順5](/C:/Works/info-hive-dev/.claude/worktrees/wiki-apply-design/docs/plans/wiki-apply-2026-11-14.md:356)、[手順9](/C:/Works/info-hive-dev/.claude/worktrees/wiki-apply-design/docs/plans/wiki-apply-2026-11-14.md:364)。

- **【軽微】W8の変更と逆の指示が、スクリプトの出力に残る。** 491行は理由の記録を手順6まで遅らせるが、既存の `wiki_rawcheck.py` は「理由をログへ書いてから `--finish --accept-warnings`」と出力する。同スクリプトの文面変更は移行表になく、段落検査はPythonの文字列を対象にしない。ASTの書き込み検査でも、この出力指示は検出できない。**二つの機械検査が通っても、矛盾する書き込み指示が残る。** [設計の変更](/C:/Works/info-hive-dev/.claude/worktrees/wiki-apply-design/docs/plans/wiki-apply-2026-11-14.md:491)、[実際の出力](/C:/Works/info-hive-dev/.claude/worktrees/wiki-apply-design/info-hive-wiki/skills/info-hive/scripts/wiki_rawcheck.py:1070)、[引数の説明](/C:/Works/info-hive-dev/.claude/worktrees/wiki-apply-design/info-hive-wiki/skills/info-hive/scripts/wiki_rawcheck.py:1105)。

## 検証した事実

| 確かめた主張 | 結果 |
| --- | --- |
| サブモジュールの参照版 | **一致。** `83dbb30abcce7d4ed56babee134cd6247ad7803d` |
| 親の実際の索引への通常の追加 | **一致。** 期待するブロック列になり、既存の子トークンと詰まったリストを保った |
| 親の実際のログへの通常のサブ行追加 | **一致。** ブロック列と既存の子＋`softbreak`＋追加文の条件を満たした |
| `~~~`、`<div>`、`\| a \|` | **一致。** 前者はブロック列が変わり、後二者は段落として入った |
| APの参照定義比較 | **食い違い。** 定義とリンク先が同じでも `map` が変わった |
| 新しい適用・復旧処理 | **確かめられず。** 実装がないため、状態遷移は設計から検討した |

ファイルは変更していない。`concurrency-check.md` の競合数は記録を確認したが、独立した再測定はしていない。

## 崩せなかった点

- AOにより、6回目の「変更のない読み取り専用ファイルを不要に戻して `stuck`」という元の反例は成立しない。
- 前後が異なり、配置済み項目を復元できる条件では、ALの巻き戻しから新たな二重適用・変更消失は導けなかった。
- `pending` を前進させず中止する規則と、`prepared` の前後ハッシュによる再開は、検討した通常の停止位置では崩せなかった。
- 1・2回目の元のリンク、親子パス、入力の再読みによる反例は、追加された拒否条件とメモリ上の写しにより成立しない。
- 独立した計画の識別、同一ファイルの操作の合成、ロック内での適用済み印の再確認から、以前と同じ取り違えは導けなかった。

使用した MCP サーバー: なし  
使用した Agent Skills: なし
