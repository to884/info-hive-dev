# Wiki のログ

wiki に対する操作を時系列で記録する、追記専用のログである。各項目は `## [YYYY-MM-DD] <操作名> | <説明>` で始めるので、`grep "^## \[" log.md | tail -N` で抜き出せる。操作名は下の英語のまま書き、説明は日本語で書く（`## [2026-11-03] ingest | インボイス制度の手引き`）。補足の行は、3文字の空白で字下げして続ける（`   グラフ: ノード +4、型付きエッジ +2`）。

操作の種類:
- `ingest`: ソースを wiki に取り込んだ。
- `query`: wiki をもとに質問に答えた（通常は、回答をシンセシスとして保存したときだけ記録する）。
- `lint`: 健全性のチェックを実行した。
- `schema`: スキーマを変更した。
- `shard`: インデックスを分割した。

---

## [2026-11-11] schema | タグの体系に グラフ、browse、試験、リリース を足した

## [2026-11-11] ingest | wiki 0.9.2 のグラフの抽出の修正の記録
   ページ: sources/グラフの抽出の修正-0.9.2、concepts/グラフの抽出の契約、concepts/エッジの識別子、concepts/グラフのlintの期待値

## [2026-11-12] schema | タグの体系に rag を足した

## [2026-11-12] ingest | rag 0.5.1 の PDF のヘッダーの判定の修正の記録
   ページ: sources/pdfのヘッダーの判定の修正-rag-0.5.1、concepts/pdfのヘッダーの条件

## [2026-11-12] ingest | wiki 0.11.1 の取り込み手順の追従と、wiki 0.11.1・rag 0.5.1 のリリースの記録
   ページ: sources/取り込み手順の追従とリリース-wiki-0.11.1、concepts/リリースの確かめ方

## [2026-11-13] schema | タグの体系に windows を足した

## [2026-11-13] ingest | Git Bash のパス変換で git の引数が壊れる件
   ページ: concepts/git-bashのパス変換（sources/取り込み手順の追従とリリース-wiki-0.11.1 を更新）

## [2026-11-13] ingest | rag 0.5.2 の PDF のヘッダーの境界の書き方の修正
   ページ: concepts/pdfのヘッダーの条件（sources/取り込み手順の追従とリリース-wiki-0.11.1 を更新）

## [2026-11-13] ingest | rag 0.5.3 の PDF のヘッダーのエラーメッセージの修正
   ページ: concepts/pdfのヘッダーの条件（sources/pdfのヘッダーの判定の修正-rag-0.5.1 を更新）

## [2026-11-13] ingest | rag 0.5.2・0.5.3 の書き方とメッセージの修正、リリースの記録
   ページ: sources/pdfのヘッダーの書き方の修正-rag-0.5.2-0.5.3（concepts/リリースの確かめ方、concepts/pdfのヘッダーの条件 を更新）

## [2026-11-13] ingest | Windows の Python で書き戻すと LF が CRLF に変わる件
   ページ: concepts/pythonの書き戻しの改行（sources/取り込み手順の追従とリリース-wiki-0.11.1 を更新）

## [2026-11-13] ingest | browse のスコープ表示、wiki 0.12.0 のリリースと画面の確かめの記録
   ページ: sources/browseのスコープ表示とリリース-wiki-0.12.0、concepts/browseの画面の確かめ方（concepts/リリースの確かめ方 を更新）

## [2026-11-13] ingest | 検索の結果の tags と sources の修正、wiki 0.12.1 のリリースの記録
   ページ: sources/検索の結果のtagsとsourcesの修正-wiki-0.12.1、concepts/frontmatterのリストの値（concepts/リリースの確かめ方、concepts/git-bashのパス変換 を更新。SCHEMA.md のタグの体系に `検索` を足した）
