---
type: "source"
title: "info-hive-rag のアーキテクチャ（4fabe32）"
authors: ["to884"]
url: "https://github.com/to884/info-hive-rag/tree/4fabe3294d86a367e635bc18635af6e7132a8d93"
raw: "raw/info-hive-ragのアーキテクチャ-4fabe32.md"
raw_sha256: "38d8eab693a58ab79e1c35575d9e543145162c847d08b6beb845b29a87f6e1af"
repository_commit: "4fabe3294d86a367e635bc18635af6e7132a8d93"
ingested: 2026-11-19
created: 2026-11-19
updated: 2026-11-19
tags: ["rag", "取り込み", "検索", "wiki設計"]
entities: ["info-hive-rag", "info-hive-wiki"]
---

# info-hive-rag のアーキテクチャ（4fabe32）

親リポジトリが参照する rag のコミット `4fabe3294d86a367e635bc18635af6e7132a8d93` と、wiki v0.38.1 の PDF 取り込み手順を照合した。rag のプラグイン定義の版は 0.5.3 で、このコミットにはタグ v0.5.3 以降の PDF ページ判定モジュールの共通化が含まれる。raw に両実装と ADR の行番号付き抜粋を保存した。

## 受付と再開

- Claude Code が rag の MCP を起動する。プラグイン定義は `wiki@info-hive` を依存先に宣言する。
- `rag_server.py` の `register_pdf` は、wiki ルート、PDF の絶対パス、wiki 内の `source_page`、題名を受け取る。受付はパスとファイル情報を確かめ、`rag_jobs.py` が `jobs-v2.sqlite` にジョブを保存する。受付時の `queued` は、ワーカーが処理を開始できる状態を表す。PDF の内容はワーカーが読む。互換名の `ingest_pdf` も同じ受付を行う。
- MCP 接続中は、保存先ごとに一つの子ワーカーが `rag_worker.py` で動く。終了前に処理中のジョブを `paused` にし、強制終了で `running` が残っても次のワーカーが回収する。再開時に保存済みのページと埋め込みバッチを使う。失敗・キャンセル済みのジョブの再実行は `retry_job` で指示する。索引の公開開始後はキャンセルを受理しない。

## 抽出と索引

ワーカーは原本のバイト列を読み、同じバイト列を PDF の処理と SHA-256 に使う。SHA-256 が文書 ID になる。`rag_pdf.py` は PDFium でページごとに文字層を読み、既定の `auto` では文字化け・スキャン・縦書きの判定に応じて NDLOCR-Lite を呼ぶ。抽出結果はページ別の JSON として保存し、`document.md` にまとめる。抽出先の鍵は PDF の SHA-256 と OCR の方針・解像度・OCR と抽出の版で決まり、同じ `data_dir` を使う wiki の間で共有する。埋め込みモデルだけを変えた場合は同じ抽出結果を使える。

チャンクはページをまたがず、ページ番号を持つ。rag の `Engine` が Ruri v3（既定は 130m、Sentence Transformers）でバッチごとに埋め込み、Sudachi のトークンとベクトルを、wiki ごとの LanceDB に書く。`rag_indexes.py` は全文・世代索引を作り、設定された行数（既定256）から IVF_SQ の近似ベクトル索引を作る。

索引が整うと `catalog.sqlite` の公開世代を切り替える。`rag.search` は台帳に載った世代に対象を絞り、全文とベクトルの順位を RRF で統合する。検索結果には本文の断片、ページ番号、PDF の参照先と SHA-256、wiki の出典ページを返す。処理途中の行を検索対象に出さない仕組みは、この世代の絞り込みにある。

## wiki との受け渡し

wiki の PDF 取り込みを実行するエージェントが、事前検査をして rag の MCP に登録し、`job_status` を確認する。`completed` の後に `result.extracted_markdown` のファイルを読み、`sources/<スラッグ>.md` に要約を作る。frontmatter の `raw`、`raw_sha256`、`rag_job_id` が、それぞれ移動・複製せずに参照する原本の絶対パス、内容のハッシュ、rag のジョブを指す。同じ場所の PDF が別の内容に置き換わった場合、rag は旧版を参照する wiki ページの frontmatter に `review_required` と `review_reason` を付ける。

ADR-0012 には、rag のチャンクを wiki の MCP の `index_chunks` に渡す設計が記録されている。調査対象のコミットでは、rag のワーカーが PDF のチャンクを自身の LanceDB に書き、`rag.search` も同じ索引を読む。wiki への通常の取り込み連携は、エージェントによる登録、抽出本文の参照、要約記事の作成を通じて行われる。

実行確認には、合成 PDF とテスト用ベクトルを使う既存の回帰試験6件を使った。登録の競合処理、キャンセルと公開の順序、保存済みバッチからの再開、検索と原本参照を確認した。OCR と実モデルの記述はコードの確認に基づく。

## 取り込んだ内容と載せたページ

| 番号 | 取り込んだ内容 | 出典の該当箇所 | 掲載方法 | 掲載ページと理由 |
| --- | --- | --- | --- | --- |
| c1 | rag は wiki に依存する Claude Code プラグインである | raw「対象の版と Claude Code の入口」のプラグイン定義 | `create` | [[info-hive-rag]] に依存の向きを記録 |
| c2 | PDF の登録を永続ジョブに記録し、一つのワーカーが取得・再開する | raw「受付と永続ジョブ」の `rag_jobs.py` と `rag_worker.py` | `create` | [[info-hive-rag]] の処理図で受付と実処理を分けて表示 |
| c3 | PDFium の抽出、必要に応じた OCR、ページ別の抽出キャッシュからチャンクを作る | raw「PDF の読み込みとページ抽出」の `rag_pdf.py` と `rag_config.py` | `create` | [[info-hive-rag]] の処理図で抽出から分割までを表示 |
| c4 | rag の LanceDB と公開世代の台帳で PDF を検索する | raw「埋め込み、索引、公開」の `rag_index.py` と `rag_indexes.py` | `create` | [[info-hive-rag]] に索引の所有と公開の境界を記録 |
| c5 | wiki はジョブ完了後に抽出本文を読み、原本・ハッシュ・ジョブ ID を参照する要約を作る | raw「wiki との受け渡しと設計記録」の `commands/ingest.md` 78–84 行 | `update` | [[info-hive-wiki]] の既存の連携説明に手続きと相互参照を追加 |
| c6 | PDF の内容が変わると旧版の出典を参照する記事に要確認の印を付ける | 同節の `rag_index.py` 443–479 行と、公開時の呼び出し | `create` | [[info-hive-rag]] に再取り込み時の wiki への影響を記録 |
| c7 | PDF チャンクの実装と、wiki の MCP を使う ADR-0012 の設計には差がある | raw「埋め込み、索引、公開」の `rag_index.py` 170–184、537–564、666–697 行と、ADR-0012 の 31 行 | `source_only` | 設計文書と調査対象の実装を照合した根拠を記録 |

> Codex 補足: 登録と索引の実行場所は rag の製品ページでたどれる。wiki の製品ページからは PDF の連携点をたどれる。

## 関係するページ

- [[info-hive-rag]]
- [[info-hive-wiki]]
- [[info-hive-wikiのアーキテクチャ-v0.38.1]]
- [[pdfのヘッダーの条件]]
