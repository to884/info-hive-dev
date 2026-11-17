# ADR-0031: wiki を Codex のプラグインとしても配布する

| 項目 | 内容 |
| --- | --- |
| 状態 | 採用 |
| 決定日 | 2026年11月17日 |
| 決定者 | エージェント（Codex 対応の依頼の範囲で決定） |
| 関連 | ADR-0003、ADR-0012 |

## 背景

スキル本体には Codex 向けの説明があるが、プラグインの定義、MCP の自動登録、`commands/` の操作手順は Claude Code 向けである。スキルだけを入れた Codex では、プラグインと同じ機能を利用する導線がそろわない。

## 決定

- wiki の配布物に `.codex-plugin/plugin.json` を追加する。既存の `skills/info-hive/` と MCP サーバーを共用し、Claude Code の定義を残す。Codex CLI 0.166.0 の互換形式の MCP 定義は `${CLAUDE_PLUGIN_ROOT}` を展開しないため、Codex の定義では `cwd: "."`（プラグインのルートに解決される）と相対パスの引数を使う。初回の環境の準備に備えて接続の待ちを 600 秒とする。
- Codex 向けのカタログは、マーケットプレイスのリポジトリの `.agents/plugins/marketplace.json` に置く。配布先は `source: "url"` と `url: "https://github.com/to884/info-hive-wiki.git"` で指定する。Codex CLI 0.166.0 は Claude Code 用の `source: "github"` を認識せず、項目を一覧から除く。対象は wiki のみとし、rag の Codex 対応は宣言しない。項目に `version` は書かない。
- Codex では `$wiki:info-hive <操作> <引数>` を入口にする。11 本の操作手順の正本は既存の `commands/*.md` のままとし、読み取り専用の `wiki_codex.py` がパス、呼び出し名、ホスト固有の前提を補って表示する。利用者の引数は受け取らず、シェルも起動しない。
- Web の raw は Codex 自身が既存の W1〜W8 を実行する。Claude の CLI や Sonnet のエージェントを起動しない。ページの編集には Codex の差分編集を使う。
- `session` による実行中の会話の自動取得は Claude Code の機能として残す。Codex の会話履歴を Claude の形式として読ませない。明示した Claude Code の記録は従来の処理で取り込める。
- スキルだけを導入した場合は、従来のリファレンスと CLI を利用できる。完全な操作手順と MCP の自動登録には、プラグイン一式の導入が必要であると明記する。

## 検証

Codex CLI の一時的なホームとローカルのカタログで、一覧取得、インストール、スキルと MCP の認識を確かめる。実際の MCP stdio 接続でもツールを呼ぶ。通常のホームの設定と導入済みのプラグインは変更しない。操作手順の変換、不正な操作名、ヘルプ、パスに空白や日本語を含む配置を親リポジトリで試験する。

Claude の利用量を節約するという利用者の指示に従い、この変更では `ask-claude` によるレビューを行わない。

## 理由と検討した選択肢

スキルだけの配布では MCP と操作手順が欠ける。Codex 用に 11 本の手順を複製すると、取り込みや検査の規則がずれるため、既存の手順を読む入口を選んだ。Claude Code のコマンドの配置を変える方法は、既存の利用者と検証に影響するため、この段階では採らない。

## 影響

Claude Code のコマンド、MCP の定義、wiki の保存形式は維持する。リリース時は両方のプラグイン定義の版をそろえる。Codex の会話履歴の自動取り込みと rag の Codex 対応は別の変更として扱う。

会話履歴の自動取り込みは、追加の依頼に従い [ADR-0032](0032-codex-session-history.md) で対応した。

## 参照

- [OpenAI: プラグインの構成](https://developers.openai.com/plugins/build/plugins)
- [OpenAI: ローカルの MCP サーバー](https://developers.openai.com/plugins/deploy/desktop-only)
