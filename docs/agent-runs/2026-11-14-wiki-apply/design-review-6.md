## 判定

**却下。確信度：高。** 内容を変えない `edit` と、開始時から置換できないファイルだけで、PC 全体を `stuck` にできる。構造検査にも、既存リンクの解釈の変化を見逃す反例がある。

未実装の設計への判定である。停止・巻き戻しの反例は手順から導いた。Markdown の挙動は同梱パーサーでメモリ上で検証した。ファイルは変更していない。

## 致命的・重大な欠陥

### 1.【重大】変更のない `edit` を、未配置でも巻き戻そうとして全 wiki を停止させる

次の、開始時から変わらない配置で成立する。

```text
W/concepts/       一時ファイルを作成できる
W/concepts/z.md   読めるが置換できない、Windows の読み取り専用ファイル
```

`z.md` は正常な UTF-8 と frontmatter を持つものとする。

1. `edit --path concepts/z.md` を登録し、写しを変更しない。または、編集を取り消して元の内容へ戻す。
2. **`before_sha256 == after_sha256`** になる。設計には、この項目を拒む条件も、書き込みから除外する条件もない。手順5では前像が一致するため「書く」になる。
3. 7a は一時ファイルを作れて、日誌を `prepared` にする。
4. 7b の置換が読み取り専用属性により失敗する。行き先は一度も変更されていない。
5. 7c の「戻す」は日誌の各項目を調べる。現在の内容は `after_sha256` と一致するので、記載された最初の分岐に入り、前像を一時ファイルへ写して再び置換する。
6. 同じ読み取り専用ファイルなので、置換が再び失敗し、日誌が `stuck` になる。
7. 以後、別の wiki の計画も、手順2で終了コード5になる。

「後と一致する」と「前と一致する」が同時に成立する場合の規則がない。記載順に分岐すると、**何も置いていない項目への不要な復元失敗**を、PC 全体を止める理由にしてしまう。

これは外部の書き手、属性の途中変更、プロセス停止を必要としない。「7b で置けた項目だけを戻す」「計画そのものが置けないときは `aborted` になり、PC 全体は止まらない」という説明と、対照表の「5 回目の重大2は生じない」に反する。

根拠：[手順5の受理条件](/C:/Works/info-hive-dev/.claude/worktrees/wiki-apply-design/docs/plans/wiki-apply-2026-11-14.md:334)、[7a〜7c](/C:/Works/info-hive-dev/.claude/worktrees/wiki-apply-design/docs/plans/wiki-apply-2026-11-14.md:343)、[巻き戻しの分岐](/C:/Works/info-hive-dev/.claude/worktrees/wiki-apply-design/docs/plans/wiki-apply-2026-11-14.md:362)、[停止条件の説明](/C:/Works/info-hive-dev/.claude/worktrees/wiki-apply-design/docs/plans/wiki-apply-2026-11-14.md:364)、[対照表](/C:/Works/info-hive-dev/.claude/worktrees/wiki-apply-design/docs/plans/wiki-apply-2026-11-14.md:653)。

## 崩れる前提

| 暗黙の前提 | 崩れる条件 |
| --- | --- |
| 前像と後像の一致判定は、互いに排他的である | 変更のない `edit` を登録する |
| ロック中に後像と一致すれば、その計画が置いたファイルである | 前像と後像が同じで、配置自体は失敗している |
| インラインの `type` と `content` が同じなら、既存部分の解釈も保たれる | 参照リンクの `href` だけが変わる |
| 最後のブロックの直後は、ファイル末尾と同じ意味である | ブロックトークンにならない参照リンク定義が後ろにある |
| 7b 中断後の再開は、必ず適用完了へ進む | 再開時にも置けない項目があり、AL に従って巻き戻す |

## 見落としと軽微な問題

### 1.【軽微】構造検査を通して、既存の参照リンクの URL を変えられる

変更前の `log.md` を次とする。

```markdown
## [2026-11-14] ingest | A
   See [doc][r].

[r]: https://old.example
```

次を登録する。

```text
log-entry --op ingest --date 2026-11-14 --title B
  --line "[r]: https://evil.example"
  --line "added"
```

参照定義はブロックトークンを作らない。したがって268行の挿入位置は A の段落の直後になり、新しい定義が古い定義より先に置かれる。

同梱パーサーで確認した結果は次のとおり。

| 規定された比較 | 結果 |
| --- | --- |
| 変更後の `sig` が、変更前の列＋見出し・段落の列になる | 一致 |
| 既存の全 `inline` の子の `(type, content)` | 一致 |
| 新しい段落の子と、追加文だけを解析した子 | 一致 |
| 新しい段落の最後の行 | `added` と一致 |
| A のリンクの `href` | **`old.example` から `evil.example` に変化** |

追加文だけの解析でも、最初の行は参照定義として消費され、段落は `added` だけになる。既存リンクで変わるのは比較対象に含まれない `attrs` である。

既存の行のバイト列を変えずに、そのリンク先を変更できる。AJ・AK の比較は、既存部分の解釈が変わらないことまでは保証しない。

根拠：[比較対象の定義](/C:/Works/info-hive-dev/.claude/worktrees/wiki-apply-design/docs/plans/wiki-apply-2026-11-14.md:237)、[新しいインラインの比較](/C:/Works/info-hive-dev/.claude/worktrees/wiki-apply-design/docs/plans/wiki-apply-2026-11-14.md:243)、[挿入位置](/C:/Works/info-hive-dev/.claude/worktrees/wiki-apply-design/docs/plans/wiki-apply-2026-11-14.md:268)、[同梱パーサー](/C:/Works/info-hive-dev/.claude/worktrees/wiki-apply-design/info-hive-wiki/skills/info-hive/scripts/wiki_pages.py:391)。

### 2.【軽微】AN の停止時説明に、巻き戻し導入前の断定が残る

375行は、7b 中断後に同じ `apply` をやり直すと `already_applied` になると断定する。

しかし、524行の試験は、二つ目が置換不能な配置で7bを中断すると、次の適用が巻き戻して `aborted` にすることを要求する。この場合、持ち主の再実行も同じ置換失敗で終了コード1になり、`already_applied` にはならない。

対照表655行の「状態の説明と試験の食い違いは生じない」は、まだ成立していない。

根拠：[停止時の説明](/C:/Works/info-hive-dev/.claude/worktrees/wiki-apply-design/docs/plans/wiki-apply-2026-11-14.md:375)、[置換不能時の試験](/C:/Works/info-hive-dev/.claude/worktrees/wiki-apply-design/docs/plans/wiki-apply-2026-11-14.md:524)。

### 3.【軽微】既存テンプレートの編集指示に、移行先も例外分類もない

83dbb30 の `commands/upgrade.md` は、既存の `.page-template.md` について次を指示する。

- 25行：`## 主張と行き先` を追加する。
- 37行：`type` と `tags` の例を引用符付きに直す。

10節の upgrade の行が扱うのは `SCHEMA.md` だけである。一方、3節は `.` で始まる要素を拒むので、これらのテンプレート編集を `edit` へ移すこともできない。`init_wiki.py` を残す理由は「ないファイルだけを作る」であり、既存テンプレートの編集には当たらない。

すべての段落に正しく分類を求めれば、この未決定は検出できる。したがって、機械検査を通過する漏れとは判定していないが、「洗い出した表」には分類先が不足している。

根拠：[既存の追加指示](/C:/Works/info-hive-dev/.claude/worktrees/wiki-apply-design/info-hive-wiki/commands/upgrade.md:25)、[引用符の修正指示](/C:/Works/info-hive-dev/.claude/worktrees/wiki-apply-design/info-hive-wiki/commands/upgrade.md:37)、[パスの禁止条件](/C:/Works/info-hive-dev/.claude/worktrees/wiki-apply-design/docs/plans/wiki-apply-2026-11-14.md:211)、[移行表の upgrade](/C:/Works/info-hive-dev/.claude/worktrees/wiki-apply-design/docs/plans/wiki-apply-2026-11-14.md:476)。

## 検証した事実

| 確かめた主張 | 結果 |
| --- | --- |
| サブモジュールの参照版 | **一致。** HEAD は `83dbb30abcce7d4ed56babee134cd6247ad7803d` |
| 通常の索引追記に対する AK | **一致。** 実際の `wiki/index.md` への追加で、既存項目の子トークンを保ち、独立した項目が一つ増えた |
| 通常のログ追記に対する AK | **一致。** 実際の `wiki/log.md` で、ブロック列と、既存の子＋`softbreak`＋追加文の条件を満たした |
| 参照リンクの反例 | **食い違いを確認。** 規定された比較値は一致するが、既存リンクの `href` が変わった |
| 置換の再試行 | **一致。** `replace_with_retry()` は再試行後も失敗すれば例外を上げる。読み取り専用属性は解除しない |
| 過去に指摘された移行漏れ | W8、配布する定型文、Retrieval、評価ループ、初期化後の設定、索引分割時のスキーマ更新には移行先が追加されている |
| 新しい適用・復旧処理の実行結果 | **確かめられず。** 実装がないため、状態遷移は設計から検討した |
| `concurrency-check.md` の消失数 | 記録を確認した。今回の独立再測定はしていない |

## 崩せなかった点

- 1回目の `journal` のリンク、`W/indexes -> W`、途中に `.md` を含む親子パスという元の反例は、拒否条件に当たる。
- 独立した `begin` の同内容の計画は、`plan_id` で区別される。
- 入力を一度だけ読み、そのバイト列を使う規則では、ロック待ち中の `D/edit` の変更を未承認のまま置く旧反例は成立しない。
- 全体の前像ハッシュで比較する `edit` と、同じファイルの `ops` を順に合成する規則から、旧版の取り違え・上書き消失は導けなかった。
- AM のロック内での印の再確認は、5回目の「日誌回収後に待機プロセスが二重適用する」元の反例を止める。
- `pending` を前進させず破棄する規則では、7a 中断だけから部分適用を導けなかった。
- 前像と後像が異なり、配置済み項目を復元できる場合には、AL は5回目の置換不能ファイルの元の反例を `aborted` で終わらせる。

使用した MCP サーバー: なし  
使用した Agent Skills: なし
