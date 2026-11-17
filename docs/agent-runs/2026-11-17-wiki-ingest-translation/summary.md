# 翻訳を省略した raw の完了を防ぐ修正（wiki 0.30.1）

## 変更の状態

プラグイン PR は to884/info-hive-wiki#87、親の試験と記録は to884/info-hive-dev#171。独立した worktree で変更し、並行して公開された 0.30.0 を取り込んで、今回の版を 0.30.1 に振り直した。両ホストの定義と CHANGELOG を同期した。タグと GitHub リリースの作成は今回の依頼に含めない。

最終レビューは Opus の利用上限で中断し、2026-11-18 4:30（Asia/Tokyo）から続きを再開する。これは合格を意味しない。中断までの記録は review-round4.md.status.json にある。プラグインを先に、親の参照を後にマージする。

## 完了を決める条件

- 翻訳必須の `keep` はエラーにし、比較元を残す。`needs_translation` の欠落や型の違いも翻訳不要にはしない。
- 未解決の外国語は `translation_review_required` のエラーで止める。文末、大小文字、原文との完全一致だけで自動的に文章や名前と分類しない。
- 正しく保持する文字列は、対象の ID・text の全文・種類・具体的な理由と実際に確認したモデル名を、現在の原文・raw の SHA-256 に結び付ける。不正・古い・部分的な記録で残りを一括受理できない。
- `--translation-review` を明示して確認の記録を照合する。有効な記録も警告になり、親が原文と文脈を確認し、W9 より前に `prepare` のログへ理由を書いて受理する。raw のエージェントは警告を受理しない。
- JSON の `translation.pending_reviews: 0` と `completed: true` を後段への条件にする。`ok`、翻訳者名、フォルダーの消失から完了を推定せず、監査も確認の証拠を要求する。

スキルの正本はプラグイン内の `skills/info-hive/` である。親の `.agents/skills/`、`.claude/skills/` と skills-lock.json にこのスキルの別配置や登録はない。Playwright の公開済みの変更は main から統合した。`implementation.patch` は最新 main から今回のコードと試験だけの差分である。

## 検証

関連回帰 292 件がすべて成功した。今回追加した回帰は 37 件（翻訳の回帰 26 メソッド、確認記録の契約 9 メソッド、監査 2 メソッド）。結果は isolated-regression.log にある。初期の regression.log は並行作業を含む古い実装の結果なので、最終変更の根拠は 292 件の結果とする。

```powershell
python -X utf8 -B -m unittest tests/wiki/test_wiki_web_check.py tests/wiki/test_web_raw_agent.py tests/wiki/test_codex_plugin.py tests/wiki/test_wiki_fetch_browser.py tests/wiki/test_wiki_fetch.py -q
```

encoding の静的検査は、最新 main の統合後の 61 ファイルで成功した。プラグインの CI も Linux / Windows × Python 3.12 / 3.14 の 4 環境で成功した。

保存済み記事の英語版と日本語版を、一時 wiki の回帰用の fixture に置いて CLI で検証した。実際の raw は変更していない。原本のハッシュと実行結果は saved-article-check.json にある。

| ケース | 終了コード | completed | 確認の対象 | 比較元 |
| --- | --- | --- | --- | --- |
| 英語のまま keep | 1 | false | 未解決 123 件、keep などの誤り | 残る |
| 英語のまま翻訳者名だけ記入 | 1 | false | 未解決 123 件 | 残る |
| 日本語版、保持する固有名 3 件を確認 | 0 | true | 125 ブロックを照合、未解決 0 件 | 削除 |

日本語版では、英語版 Wikipedia と Simple English Wikipedia の固有名の保持を対象ごとに確認した。保持の警告 3 件と、疑問詞や否定語を名前と推定した既知の警告 4 件を理由付きで受理した。新しい検査は、意味の正しい訳や確認の分類を機械で保証するものではない。

プロジェクト wiki にソースの要約と、エージェントに守らせる決まりの書き方の更新を加え、索引とログを更新した。グラフは 86 ノード・466 エッジ。lint の新しい指摘はなく、既存の unknown_tags 21 件以外は 0 件である。

## レビューと設計の変更

設計と実装を ask-claude で Opus 5.5（high）の敵対的レビューにかけた。当初の 2 回は利用枠の上限で推論開始前に失敗した（design-review.md.status.json、implementation-review.md.status.json）。

- merge-review.md: 比率による判定が、製品名を残した正しい訳を拒み、段落の後半や中国語の残存を見逃した。
- review-round2.md: ラテン文字と漢字以外の残存と、UI・小文字の名前・原語の併記を誤って拒む問題が見つかった。
- review-round3.md: 完全一致と文末の推定も、近似コピーを見逃し、正しく残す文献名や複数文の表示を拒むと分かった。判定を推測の追加で直す方針をやめた。
- review-round4-request.md、round4.patch: 外国語の検出と、対象ごとの確認記録の検証を分ける設計・実装に変更し、コードと計画を固定して依頼した。利用上限で中断したため、最終判定はまだ得ていない。

## 保証する範囲

検査器は、候補の検出と、確認記録の形式・対象・現在の本文への結び付きを調べる。保持の分類や理由の意味、訳の正しさ・完全性は確認者が原文と文脈を読む。短い語や検出条件に当たらない形の見逃しはあり得る。確認の記録を翻訳の代用にせず、文章は訳す。比較元やプログラム自体の任意の改ざんに対する防御は目的としない。
