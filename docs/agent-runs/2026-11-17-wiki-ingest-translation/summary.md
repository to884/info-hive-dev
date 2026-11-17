# 翻訳を省略したまま取り込みを完了にしない修正

## 状態

実装と回帰試験は完了した。AGENTS.md で求められる Opus による設計・実装の敵対的レビューは未実施であり、変更はレビュー待ちである。利用者からコミット、push、PR 作成、マージまでの指示を受け、独立した worktree に切り出した。プラグインは 0.29.1 とし、両ホストの定義と CHANGELOG の日付を更新した。プラグインの PR は #87（draft）。Opus のレビューと CI を確認してから、プラグイン、親リポジトリの順にマージする。GitHub リリースの作成は今回の指示に含めない。

## 直したこと

- 取得器が翻訳を必須とした入力は、`--language-override keep` を指定しても必須のままになる。検査はエラーとし、`--finish --accept-warnings` でも比較用の写しを消さない。
- 翻訳者名だけがある場合も、文章をブロックごとに調べる。長い外国語の丸残し、外国語のままの言い換え、一部の段落だけの翻訳、日本語の補足や短い語の付け足しを検出する。コード、画像、インラインのコード、短い名前などは対象から外す。
- `needs_translation` が欠落した、または真偽値でない場合を翻訳不要とは扱わない。
- JSON に `translation` と `completed` を追加した。`ok` と raw の段の完了を区別し、必要な検査と警告の受理を終えて `--finish` が成功したときだけ `completed: true` になる。
- Claude Code と Codex の手順、raw のエージェント、呼び出す側の報告の形式を更新した。翻訳を実行できないときは未完了として伝え、原文の保存と日本語の要約で代替して完了にはしない。
- セッションの監査も、フォルダーが消えたことだけから完了を推定しない。実行結果の明示的な完了と翻訳の検査を確認し、旧形式の結果を自動で完了に読み替えない。

スキルの正本はプラグイン内の `skills/info-hive/` である。親の `.agents/skills/`、`.claude/skills/` と skills-lock.json には、このスキルの別の配置や登録はなく、取得済みの他のスキルは変更していない。他のセッションによる Codex 対応と Playwright 対応の差分も保持した。`implementation.patch` は、独立した worktree の最新 main からの差分である。並行作業の Playwright 対応は含めない。

## 検証

元の作業ツリーでは、Playwright 対応を含む関連テスト 261 件が成功した。独立した worktree でも、最新 main に今回の変更だけを加えた関連テスト 230 件が成功した（最初の実行では、カタログ未チェックアウトの 1 件をスキップ。その後カタログを初期化し、Codex の 14 件はすべて成功）。今回のために 16 件のテストを追加し、複数の反例はそれぞれのテスト内でも組み合わせて確かめた。結果は regression.log にある。

```powershell
python -X utf8 -B -m unittest tests/wiki/test_wiki_web_check.py tests/wiki/test_web_raw_agent.py tests/wiki/test_codex_plugin.py tests/wiki/test_wiki_fetch_browser.py tests/wiki/test_wiki_fetch.py -q
```

今回の記事も、保存済みの英語版と日本語版を隔離した一時 wiki に置いて CLI で確かめた。実際の raw は変更していない。結果は saved-article-check.json にある。

| ケース | 終了コード | completed | 翻訳の検査 | 比較用の写し |
| --- | --- | --- | --- | --- |
| 今回の失敗と同じ、英語のまま keep | 1 | false | 未翻訳 117 ブロックなどを検出 | 残る |
| 英語のまま翻訳者名だけ記入 | 1 | false | 未翻訳 117 ブロックを検出 | 残る |
| 日本語版を使い、既知の警告 4 件を受理 | 0 | true | 117 ブロックの検査に成功 | 削除 |

差分の空白の検査も通った。

## レビュー

ask-claude で Claude Opus 5.5、effort high によるレビューをそれぞれ起動したが、いずれも「5 時間の利用枠の上限」で推論開始前に失敗した。表示された解除予定は 2026-11-17 23:30（Asia/Tokyo）。レビューの指摘がなかったことを意味しない。

- 設計の依頼: design-request.md。失敗の記録: design-review.md.status.json。
- 実装を含む依頼: implementation-request.md。失敗の記録: implementation-review.md.status.json。
- 両方とも入力・出力トークンと費用は 0 と報告された。別モデルによる代替レビューはしていない。

## 検査の限界

言語の検査は、翻訳を省略した典型的な状態を止める簡易検査である。訳の意味、個々の短い語の訳し落とし、あらゆる言語の正しい判別を保証しない。手順では訳文の読み直しを引き続き求める。比較元やコードそのものを任意に改変できる実行者を、ファイルベースの検査だけで防ぐ設計ではない。
