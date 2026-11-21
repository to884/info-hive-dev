---
type: "source"
title: "Claude Desktop への wiki 0.39.1 の導入（2026-11-21）"
authors: ["info-hive-dev"]
tags: ["試験", "コマンド"]
sources: []
entities: ["info-hive-wiki"]
raw: "raw/claude-desktopへのwiki-0.39.1の導入-2026-11-21.md"
raw_sha256: "a9676650768edec6280fc1dea920228ea7793f6cc3b161fa654482ce2cc12863"
created: 2026-11-21
updated: 2026-11-21
ingested: 2026-11-21
---

# Claude Desktop への wiki 0.39.1 の導入

新しい Windows 11 26H2 の VM で Claude Desktop 5.11492.5 の Code タブを使った。Git、uv、Python、Visual C++ ランタイムを導入済みの状態で、次を観測した。

- 「カスタマイズ → プラグイン → 追加 → マーケットプレイスを追加」から `to884/info-hive-marketplace` を同期し、ディレクトリの Code 用 Wiki を追加できた。ローカル MCP の警告で「続ける」を押すと「ローカルにインストール済み」が出た。ローカルの SSH ディレクトリと `CLAUDE_CODE_PLUGIN_PREFER_HTTPS` の設定はなかった。Claude 側の GitHub 連携の使用は確認していない。
- ユーザースコープに入った [[info-hive-wiki]] 0.39.1 の `--ensure` は終了コード 0、32.78 秒。uv キャッシュは 441,267,870 バイト。モデルのキャッシュがない状態で S1 を保存した。
- Code タブで `/wiki:help` を実行し、ツール呼び出しに表示された `python .../wiki_help.py` の出力と返答の両方で、`/wiki:overview` を含む 12 本を確認した。

## 取り込んだ内容と載せたページ

| 番号 | 取り込んだ内容 | 出典の該当箇所 | 掲載方法 | 掲載ページと理由 |
| --- | --- | --- | --- | --- |
| 1 | Code の GUI から wiki を導入した。 | マーケットプレイスと Wiki | `update` | [[info-hive-wiki]] に検証記録へのリンクを付けた。 |
| 2 | 実際に入った 0.39.1 は `--ensure` で起動した。 | MCP の準備とチェックポイント | `source_only` | 計測値をこの VM の観測として残す。 |
| 3 | Code のツール呼び出しと返答に 12 コマンドが出た。 | Code タブのヘルプ | `source_only` | この版と環境での確認結果として残す。 |

## 関係するページ

- [[info-hive-wiki]]
- [[wikiのwindows初期環境とmcp起動診断-2026-11-20]]
- [[claude-desktopでのwiki確認5の1回目-2026-11-21]]
