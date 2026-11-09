対象は、info-hive の wiki プラグイン（サブモジュール `info-hive-wiki`、基準は wiki 0.8.0 の `c23ae5b`）で、ページの集合とリンクの規則を新しい `wiki_pages.py` にまとめた実装である。版は 0.9.0 にした。

設計は `docs/plans/wiki-page-set-and-links-2026-11-09.md`（1 回目のレビュー `docs/agent-runs/2026-11-09-wiki-page-set-review/design-review-1.md` で却下され、指摘を受けて決め直した版。最後に対応の表がある）。サブモジュールの既存ファイルの差分は `docs/agent-runs/2026-11-09-wiki-page-set-review/impl-4.wiki.diff` にある。新しいファイルは `info-hive-wiki/skills/info-hive/scripts/wiki_pages.py` と `tests/wiki/test_page_set.py`。作業ツリーの実物も読んでよい。

果たすべきこと:
- ADR-0010 の決定の 1 と 3。コードブロックとインラインのコードの中の `[[...]]` を数えず、閲覧の markdown-it（commonmark、html 無効、table 有効、markdown-it-py 3.0.0）と同じ箇所から wikilink を拾う。
- lint、search（MCP の索引と `get_page`）、グラフ、stats、判定レイヤーのページの集合とリンクがそろう。
- 既存の利用者の wiki を壊さない。lint と stats は標準ライブラリだけで動く。MCP サーバーが新しい規則を使う（`SERVER_FILES`）。
- 設計の 1 回目のレビュー（design-review-1.md）と、実装の 1〜3 回目のレビュー（impl-review-1.md〜impl-review-3.md、どれも却下）の指摘が直っている。対応は設計の最後の 4 つの表にある。開発リポジトリの CI の変更は impl-4.dev.diff にある。

とくに崩してほしい点: `scan_blocks` と `_mask_code_spans` が markdown-it と食い違う現実的な本文（日本語の wiki で書かれうるもの）、`split_sections` の変更が検索の結果やキャッシュに与える影響、古い名前の再輸出の漏れ、試験が確かめていない経路、変更履歴と手順書の誤り。
