# wiki 0.33.0のmain統合の最終レビュー

ユーザーがprompt-context-hookのコミット、PR、マージ、リリースまで明示的に依頼した。前回の性能レビュー（セッション3e5998ab-ddc9-4989-ba17-2af1d0e915cf）は採用可だった。その後の先行main取り込みをレビューする。読み取り専用、日本語。追加のモデルや有料の再測定を呼ばず、他の作業を止めない。

## 現在の状態

- 子PR: https://github.com/to884/info-hive-wiki/pull/91 。head `6e8f2c24b4957bc2358c760fed9f02e88d728284`、base `d761c62f680e923751dd02e00e982c67a3e3be0e`（wiki 0.32.0）。この差分は `git -C info-hive-wiki diff origin/main...HEAD` で読める。親の巨大な測定アーカイブのdiffを全部読まないこと。
- 0.32.0は概要表示、0.31.1は翻訳確認、0.31.0は記事の物理リンク拒否、0.29.0はCodex対応。これらを残してフックを載せた。
- `.claude-plugin/plugin.json` と `.codex-plugin/plugin.json` は0.33.0。CHANGELOGの今回の節を先頭へ移し、日付2026-11-18を入れた。Codexへフック対応は宣言しない。
- ADR-0032はCodex会話履歴、0033は概要が使ったため、本件を0034へ移した。READMEは公開mainの版を採用し、SKILLのCodexとフックの参照は両方残した。親側も概要の公開記録を含むorigin/main（105fd0b）を取り込んだ。
- プラグインCIはLinux/Windows×Python3.12/3.14の4件すべて成功。まだマージしていない。

## 特に見てほしい統合点

1. `wiki_pages` の既存の走査・リンク拒否・概要のための追加を残して、前回レビュー済みのパーサーの遅延初期化と `markdown_module()` を当てている。`wiki_browse_core` は `wiki_overview` をimportした後でも同梱Tokenを取得する。`wiki_rawcheck` の新しい翻訳の検査は残し、規則とTokenだけ共通口にした。
2. 最新の `wiki_search` の機能を残し、トークン化だけ `wiki_tokens` へ移す。MCPのSERVER_FILESにも加えて、変更時のサーバー入れ替えを維持する。
3. フックは `walk_pages` と `walk_index_files` の結果から記事を読む。ADR-0029のread-site inventoryに5関数を分類した。新しい実行の試験では、シンボリックリンクとハードリンクを候補にせず、本文を開かないことを確認する。状態のJSONとロックは記事ではない。
4. readerの本文やモデル表を変えていない。descriptionの `ADR-0032` だけを `ADR-0034` にした。fixtureに measured/current を記録し、試験はdescriptionのこの参照1箇所だけを測定時へ戻して、元の `reader_sha256_without_defaults` と照合する。モデル決定・158回答・意味の採点・スナップショットのhashは変更していない。この照合が余計な変更を隠していないか確認する。
5. 最新コード・起動行でも候補の実出力後の既出保存、内部2.5秒、外側5秒、失敗時0、2,000文字の契約を維持する。優先度は前回の修正済みの仕組みのまま、子はcreationflagsだけで設定する。

## 統合後の検証

`docs/research/wiki-prompt-hook-release-2026-11-18/validation.json` に現行17変更ファイルのhashと、今回の結果・ログを記録した。

- フック・実起動・モデル決定の整合性・ページ集合・fetch・web_check・web_raw・YouTube: 440件成功、1skip。
- Python3.12/PyYAML6.0.3でuninitialized・browse・記事リンク・Codex・overview: 299件成功、14skip。
- 最終コードでも並列3バッチ60/60で候補2件が到達、exit0/stderr空。負荷8本の明示参照p95 957.2ms、負荷16本の明示参照1265.9ms、負荷16本の題の一致1189.7ms。フックは各4本同時、合成150ページ。他の作業を止めない。逐次検索p95 551.0ms、10/10。
- 過去の120回と今回の60回はコードの世代が違うので合算せず、過去のレビュー・測定・hashは当時の記録として維持した。

このリリースを止める具体的な欠陥があるかを優先し、致命的・重大と軽微、確認と推測を区別する。前回の全調査を繰り返さず、変更と統合点に絞る。新たな根拠なしで全ベンチマークや739件の再実行をしない。必要な狭い試験は実行してよい。判定、根拠、残る制約を返す。
