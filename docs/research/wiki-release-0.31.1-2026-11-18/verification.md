# wiki 0.31.1 の公開とマーケットプレイス導入の確認

確認日: 2026-11-18（Asia/Tokyo）。利用者から、マージ済みの翻訳修正をリリースし、マーケットプレイスからの導入まで完了するよう依頼を受けた。コードを変更せず、公開と実際に取得した配布物を確認した。

## 公開

- プラグインの変更は [info-hive-wiki#87](https://github.com/to884/info-hive-wiki/pull/87)、回帰試験と設計・レビュー記録は [info-hive-dev#171](https://github.com/to884/info-hive-dev/pull/171) でマージ済み。
- 注釈付きタグ `v0.31.1` は、main のマージコミット `ce2b610af7dafdd09b9d162128ce67904e001665` を指す。
- [GitHub リリース v0.31.1](https://github.com/to884/info-hive-wiki/releases/tag/v0.31.1) を 2026-11-18 06:38（日本時間）に公開した。draft / prerelease はともに false。本文は CHANGELOG の 0.31.1 の節と一致し、CHANGELOG の日付も 2026-11-18 である。
- 両プラグイン定義の版は 0.31.1。`claude plugin validate` は成功した。Claude Code 2.1.325 のディレクトリ検査には、アイコンがないという警告が出るが、manifest の検証は通過した。
- 公開のメタデータと、タグ・コミット・本文の確認結果は [release.json](release.json) に残した。

## 公開マーケットプレイスからの導入

一時的な `CLAUDE_CONFIG_DIR` / `CODEX_HOME` を子プロセスだけに渡し、公開カタログ `to884/info-hive-marketplace` から `wiki@info-hive` を導入した。通常の利用者設定は使わず、手元のプラグインのパスを導入元にはしていない。

| ホスト | 確かめた結果 |
| --- | --- |
| Claude Code 2.1.325 | 0.31.1 が有効。v0.31.0 から変わった全 11 ファイルがタグとバイト単位・SHA-256 で一致 |
| Codex CLI 0.166.0 | 0.31.1 を導入。全 11 変更ファイルがタグと一致。スキル `wiki:info-hive` と 7 個の MCP ツールを認識し、統計と日本語検索が成功。読む前後で試験用 wiki はバイト単位に一致 |

Claude Code は `plugin marketplace add`、`plugin install`、`plugin list --json` を実行した。Codex は既存の `tests/wiki/check_codex_plugin.py` の公開カタログを使う経路を実行し、取得先の全 11 ファイルの照合を追加した。モデルに操作を推論させる試験ではない。

[Claude Code の結果](claude-marketplace.json) と [Codex の結果](codex-marketplace.json) に版、ハッシュ、動作の結果を記録した。

## 導入した検査器の動作

それぞれの導入先の `wiki_rawcheck.py` を CLI として動かした。公開後に生成した合成記事の fixture であり、以前取り込んだ実際の記事の W8 の受領記録ではない。

1. 英語の記事を freeze し、`--language-override keep --finish --accept-warnings` で検査した。終了コード 1、`translation_required`、`completed: false` となり、比較元が残った。
2. 本文を日本語に訳し、翻訳者を記入して同じ導入先の検査器を実行した。`completed: true`、照合 2 ブロック、未解決 0 件、警告なしとなり、比較元が消えた。

初回の後片付けでは Windows の Git pack の読み取り専用属性により削除が失敗した。一時領域の対象ファイルだけ属性を解除する処理に直し、両ホストの確認を取得からやり直した。最終実行では、検証結果を保存し、一時フォルダーの削除まで成功した。

## 親リポジトリの記録

wiki の既存のソースページと導入の確かめの記録に結果を追記し、索引・ログ・グラフを更新した。親のサブモジュール参照を、同じファイル内容の実装コミット `800a679` から、公開したタグのマージコミット `ce2b610` にそろえた。2 つのコミットの tree の差分は空である。

グラフは 87 ノード・477 エッジ。lint は既存の unknown_tags 21 件以外が 0 件で、新しい指摘はない（[lint.json](lint.json)）。
