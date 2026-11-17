# wiki 0.29.0 の公開と導入の検証

日付: 2026-11-17。Codex のプラグイン導入と会話履歴の取り込みを、wiki 0.29.0 として公開した。別の未マージ PR が 0.28.0 を予定しているため、作業中の 0.28.0 から 0.29.0 に変更した。

## 公開したもの

- [プラグイン PR #86](https://github.com/to884/info-hive-wiki/pull/86): 機能のコミット `129f2f0`、版と変更履歴のコミット `13a9bb5`。マージコミットは `10afe5ded55f95f6f763c9c383bae17e8936636d`。
- [カタログ PR #6](https://github.com/to884/info-hive-marketplace/pull/6) と [形式の修正 PR #7](https://github.com/to884/info-hive-marketplace/pull/7): Codex 用の `.agents/plugins/marketplace.json`。最終マージコミットは `c709eb3fd3dbb2a43d9d523160096fea3979984b`。
- 注釈付きタグ `v0.29.0` はプラグインのマージコミットを指す。[GitHub リリース](https://github.com/to884/info-hive-wiki/releases/tag/v0.29.0) は公開済みで、draft / prerelease ではない。

Claude Code と Codex の manifest、CHANGELOG の版は 0.29.0、CHANGELOG の日付は 2026-11-17 にそろえた。npm への公開は行っていない。

## 公開カタログからの Codex の導入

通常の設定を変えない一時的な `CODEX_HOME` で、次の試験を実行した。

```powershell
python -X utf8 -B tests/wiki/check_codex_plugin.py --marketplace to884/info-hive-marketplace --expected-version 0.29.0 --out docs/research/wiki-codex-release-0.29.0-2026-11-17/codex-marketplace.json
```

[結果](codex-marketplace.json): Codex CLI 0.166.0 で `wiki@info-hive` 0.29.0 を導入し、`wiki:info-hive` スキルと 7 個の MCP ツールを認識した。`stats` で 1 ページを数え、`query` で日本語のページを取得した。wiki の全ファイルは前後でバイト単位に一致した。

両 manifest、SKILL、Codex の操作手順の入口、Codex の履歴アダプター、共有のセッション処理、Codex のリファレンスの計 7 ファイルが、タグの中身とバイト単位・SHA-256 で一致した。MCP のデータディレクトリも一時的な場所にし、利用者の常用サーバーを使い回していない。モデルのターンは起動していない。

初回の公開カタログの確認では `source: "github"` が Codex に認識されず、wiki の項目が一覧から除かれた。Codex の実装の型と実機で `source: "url"` を確かめ、カタログだけを PR #7 で修正した。修正後はキャッシュのない設定でカタログの取得からやり直して成功した。プラグインのタグと配布物は変えていない。

## 公開カタログからの Claude Code の導入

[結果](claude-marketplace.json): Claude Code 2.1.325、使い捨ての `CLAUDE_CONFIG_DIR` で marketplace add / install / list を実行し、wiki@info-hive 0.29.0 が有効で MCP の wiki が登録されることを確認した。

v0.27.0 から v0.29.0 までに追加・変更された全 16 ファイル（README を含む）が、タグの中身とバイト単位・SHA-256 で一致した。導入先の `wiki_codex.py help` と `wiki_session.py --help` も終了コード 0 だった。確認時点のカタログは PR #6 のマージコミットで、PR #7 は Claude 用カタログを変更していない。

推論、`claude -p`、`ask-claude` は実行していない。通常のユーザー設定は変えず、一時設定とキャッシュは削除した。

## 公開前の検証

- 関連回帰 230 件: 失敗なし。Windows では POSIX 専用の 1 件をスキップ。
- プラグインの CI 手順: Python 3.12 の固定依存で compileall、文字コード 60 ファイル、retrieval 45 件、scripts 116 件、リンク解決 113/113、evolution 3 本、decisions 43 件をすべて通した。
- 英語・日本語の品質ゲート、baseline、キャッシュ一致も通した。hybrid recall@10 は英語 0.926、日本語 1.000。
- [GitHub CI](https://github.com/to884/info-hive-wiki/actions/runs/44090784843): Linux / Windows × Python 3.12 / 3.14 の 4 ジョブすべて成功。
- `claude plugin validate .` は成功。既存のアイコン未指定に関するディレクトリ向けの警告は、検証の合否に影響しない。
- Codex の独立したエージェントが再監査し、リリースを止める欠陥は見つからなかった。Claude の利用量を節約するという指示に従い、`ask-claude` は使っていない。

手元の CI の集計は [local-ci.json](local-ci.json)、会話の抽出から raw の保存までの両方式の実機試験は [会話履歴の検証](../wiki-codex-session-2026-11-17/verification.md) にある。
