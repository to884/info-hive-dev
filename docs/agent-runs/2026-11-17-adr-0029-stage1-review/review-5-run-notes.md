# 第5回レビューの実行記録（2026年11月17日）

モデルは GPT-6 Astra、effort high。複数のファイルにまたがるパス判定、通知、既存の入力の互換性を確認するため high を選んだ。新しいレビューの回数は増やさず、同じセッションの第5回を継続した。

- 依頼: task-5.md
- 事前の照合: review-5-precheck.md
- 入力の SHA-256: review-5-input-sha256.json
- 親の試験の差分: review-5-parent.target.diff
- 初回の部分レビュー: review-5.md（現物を読み取れず、差分のみで判定）
- 継続の依頼: task-5-continuation.md
- 継続後の最終報告: review-5-continued.md
- セッション: 01a1e98d-c798-7f20-811b-31ad983fd040

## ローカルの実行環境の復旧

初回の子 CLI は、デスクトップの CODEX_WINDOWS_REGISTERED_CORE=1 を継承したため、読み取りツールの起動が registered Core launch requires an installed app で失敗した。子プロセスだけその変数を外し、ASK_CODEX_EXE でデスクトップに同梱された CLI を指定した。read-only サンドボックスと approval_policy=never は維持した。ユーザーの設定ファイルやスキルのスクリプトは変更していない。

復旧後は、サンドボックスで Get-Location を実行できることを確認した。継続したレビュアーが現物の ADR、設計書、コード、試験を読み取れたこともセッションの記録で確認した。

## 依頼元で行った補助の再現

review-5-local-verification.json に記録した。wiki_evolve.propose に、同じ内容の通常ファイルを candidate として渡した。skill、target、reason、evidence は有効な値で、根拠のページも存在する。一時ディレクトリ内だけに実験の記録を作り、最後に削除した。

- wiki 外の candidate: proposed。
- wiki/concepts/candidate.md の通常の記事: proposed。
- wiki/assets/candidate.md の通常ファイル: 「候補が wiki の中の記事で、リンクか調べられないので読まない」として拒否された。

別の小さな検証では、ハードリンクの記事を candidate にすると read_bytes の前に拒否することを確認した。記事以外の入力まで拒む問題とは区別する。

Windows の末尾の点・空白を使った入力は、通常の記事名に正規化され、ハードリンクとして拒否された。外のジャンクションと .. を組み合わせた1例は FileNotFoundError になり、規則の迂回は再現していない。これらを欠陥としては採用していない。

## 候補の分岐とコーパスの範囲の補助検証

review-5-local-branches.json に記録した。

- ディレクトリの候補に、article_path が link と返すハードリンクの記事を含めた。propose はその記事の read_bytes に到達し、最後に proposed を返した。単一ファイルの候補と同じ検査がディレクトリの候補には当たっていない。
- コーパスの assets/image.dat は article_path が not_article と返すが、そのファイルをハードリンクにすると run はコーパスの検査で停止した。他方の名前だけを削除して通常のファイルに戻すと、同じ run は contract に到達した。contract は副作用を進めないため、到達を知らせる例外に差し替えた。

後者はコーパスの新しい事前検査の分岐を確かめたものであり、評価ループ全体の統合試験ではない。
