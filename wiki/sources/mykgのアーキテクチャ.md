---
type: "source"
title: "myKG のアーキテクチャ: スキーマの導出、事実の抽出、グラフの探索"
authors: ["Senol Isci"]
url: "https://github.com/SenolIsci/mykg"
raw: "raw/mykgのアーキテクチャ.md"
repository_commit: "afb0a9c9bafdc49751563b9aa7f59bcf4bb787fb"
repository_snapshot: "raw/mykg-source-afb0a9c9/"
ingested: 2026-11-18
created: 2026-11-18
updated: 2026-11-18
tags: ["グラフ", "wiki設計", "検索", "取り込み"]
entities: ["mykg"]
concepts: ["スキーマの導出と事実の抽出の分離", "オントロジーと知識グラフの役割"]
---

# myKG のアーキテクチャ

[[mykg]] は、文書群から共通の型と関係を導出し、それに沿って個々の事実を抽出する Python のエンジンである。高コストの構築処理と、完成したグラフを読む問い合わせ処理を分け、中間状態をセッションのフォルダーに残す。2026-11-18 に README、設計文書、主要な実装をコミット `afb0a9c9bafdc49751563b9aa7f59bcf4bb787fb`（v0.4.10 の版）で確認した。コードを読んだ調査であり、抽出の実行・精度・性能は測定していない。

## 全体の構成

```mermaid
flowchart LR
  I["文書・Web・リポジトリ"] --> P["取得と Markdown への前処理"]
  P --> C["分割と文書の台帳"]
  C --> S["Pass 1: スキーマの導出"]
  S --> V["スキーマ検証・任意の人のレビュー"]
  V --> F["親の属性を展開"]
  C --> E["Pass 2: 事実の抽出"]
  F --> E
  E --> A["名前の正規化・重複の統合"]
  A --> O["孤立ノードの接続"]
  O --> D["JSONL・Turtle・NetworkX・ノート"]
  O -. "スキーマ不足なら対象チャンクを再抽出" .-> E
  D --> Q["メモリ上のグラフと BM25"]
  Q --> M["MCP・CLI から探索し原文を参照"]
```

> 全体の構成 補足: 図は README、設計文書、`pipeline.py` の分担を整理したもの。Web の取得はセッション外の処理で、孤立ノードからの戻りは設定で上限を設けた補正である。検証の箱は合格を必須とする関門を意味しない。

| 層 | 主な実装 | 責務 |
| --- | --- | --- |
| 入口 | `cli.py`、`fetch_web.py` | 設定・セッションの選択、取得、構築・統合・問い合わせの起動 |
| 進行管理 | `orchestrator.py`、`pipeline.py`、`merge_pipeline.py` | 名前付きの段階、完了判定、再試行、再開、対象を絞る再抽出 |
| 知識の構築 | `pass1.py`、`pass2.py`、`assembler.py` | 型の導出、事実の抽出、正規名と ID による統合 |
| LLM 接続 | `llm/` | 提供者ごとの差をアダプターで吸収する |
| 利用 | `exporter.py`、`mcp_server.py`、`query.py` | 複数形式への出力、グラフの読込、検索・探索・根拠の参照 |

> 層の補足: 構築と問い合わせは保存ファイルを境界に分離する。問い合わせの都度、LLM でスキーマやグラフを作り直す方式ではない。根拠は設計文書「System Overview」「MCP Server」と各モジュール。

## 抽出の 12 段階

| 段階 | 処理と残すもの |
| --- | --- |
| `preprocess` | TXT は拡張子を変更、HTML は markdownify、PDF・Office・画像などは MinerU へ振り分け、変換の台帳を残す |
| `ingest` | Markdown を読み、内容のハッシュ、重なりのあるチャンク、`file_manifest.json` を作る |
| `pass1` | バッチごとにスキーマ案を導出し、機械的な統合、LLM の整合化、品質レビューで `schema.json` と `schema.ttl` を作る |
| `schema_validate` | Turtle の構文と、宣言したクラス・domain/range などの整合性を検査する |
| `human_review` | `--review` の場合に承認の印を待つ。指定しなければ自動で進む |
| `schema_flatten` | 継承をたどり、型ごとに親から受け継ぐ属性を展開する |
| `pass2` | 展開したスキーマで型付きノード・エッジを抽出し、ファイル単位の shard とチャンク対応表を残す |
| `normalize_names` | LLM で表記の揺れをまとめ、別名から正規名への対応を作る |
| `assemble` | 型と正規名から安定 ID を作り、ノード・エッジを重複統合する |
| `orphan_score` | エッジのないノードを元のチャンクと対応させ、接続候補のグループを作る |
| `orphan_connect` | チャンクを読ませて LLM が関係を提案する。採用した関係は `orphan_inferred` と区別する |
| `validate_graph` | 共通のデータから JSONL、Turtle、NetworkX、Obsidian vault などを出力する |

> 12 段階の補足: 順序と LLM 処理の区分は `pipeline.py:STEPS` を確認した。前処理の MinerU は一時的な uv 管理の Python 3.12 環境で実行し、myKG 自身の環境から依存を分離する。MCP はこの列に含まれない。

## スキーマと抽出結果を分ける理由

文書ごとに型を作ると語彙が不統一になるため、先に全体で使う型と関係を作る。Pass 1 はバッチ案を機械的に統合したあと、LLM で意味の近い型を整理し、固有の対象名を型にした過度に細かい概念を見直す。Pass 2 には継承構造そのものではなく、親の属性も含む一覧を渡す。[[スキーマの導出と事実の抽出の分離]] と [[オントロジーと知識グラフの役割]] に対応する分担である。`--base-schema` は既存の語彙を固定しながら拡張を許す。`--freeze-schema` は導出を省き、与えた語彙で抽出する。OWL はクラス・プロパティなどの基本的な宣言を取り込む範囲であり、基数制約、排他性、推移関係などを扱う汎用の推論エンジンではない（設計文書「OWL Support Scope」）。

## 保存・出所・更新の設計

セッションには `input/`、`intermediate/`、`output/` とログが集まる。永続グラフは `nodes.jsonl` と `edges.jsonl`、実行時の探索はメモリ上の NetworkX `DiGraph` で行い、外部のグラフ DB は必須ではない。Turtle は通常の RDF ツールと使える形を保ち、関係の確信度や属性は `edge_metadata.json` などの JSON 側に置く。Turtle だけではエッジのメタデータを引き継げない。ノードは型と正規名、エッジは型と両端で統合する。属性は確信度の高い値を採り、双方が 1.0 で異なる文字列なら連結して残す。確信度は平均か最大値で集約し、出所と統合の判断を残す。この規則は実世界の同一性や正しさの保証ではない（`assembler.py`）。

Pass 2 の既定の `batch_chunks` は文書をまたいでチャンクを詰め、並列性を上げる。その一方、同じバッチの抽出結果を各ファイルの shard に配るため、出所が過剰に付く場合がある。`per_file`、または `batch_chunks` に `batch_per_file: true` を付ける方式はファイルを混ぜない。混合バッチでは変更・削除後も別ファイルの shard から古いノードが残る制約がある（設計文書「Choosing a prep mode」「change-detection limits」）。

`--append` は新規追加、`--sync` は編集・削除の同期、`--append-with-grow-schema` は語彙の拡張を分担する。統合用の別パイプラインは、2 セッションのファイル名を名前空間で区別し、スキーマを統合して、必要な部分を再抽出し、共通の組み立てと出力へ戻す。README の現行説明を優先し、設計文書に残る「単独の append でも変更を再抽出する」という古い説明と区別する。

## 再開と補正

各段階は出力ファイルと完了の印で再開を判定し、状態を `pipeline_state.json` に記録する。Pass 1 のバッチ案、Pass 2 のファイルごとの shard を保存し、未完了部分だけを再実行する。`--from-step` は指定段階以降の出力を無効にする仕組みである。通常の再試行と、孤立ノードの調査で不足したプロパティが見つかったときの対象を絞る Pass 2 再実行を分ける（`orchestrator.py`）。

LLM の提供者は共通のアダプターで交換する。Agent 方式だけは HTTP の代わりに、セッション内の inbox に JSON のタスクを書き、outbox の回答と `.done` の印を待つ。タスク ID をプロンプトと文脈のハッシュから作り、同じ入力の回答を再利用する。パイプラインの各段階を書き換えず、ホストのスキルが LLM の回答を供給する境界である（`llm/agent_adapter.py`）。

## 問い合わせと検証の限界

MCP は完成したセッションを一度読み、ID・型・隣接関係・BM25 の索引をメモリに保持する。`mykg_query_graph` は BM25 で起点を選び、無向化したグラフで BFS/DFS を行い、LLM に渡すコンテキストを作る。深さと文字数による概算のトークン予算を使う。MCP 自身は回答用の LLM を呼ばず、クライアント側が探索結果、原文の抜粋、ノートを使って回答する。更新後は `mykg_reload` で読み直す（`mcp_server.py`）。

スキーマ検証は `blocking=False` で、再検証後も無効なら警告と記録を残して進む実装である。明示的な `--review` がなければ人の確認も省くため、「検証済みのスキーマだけを通す」とは言えない。Pass 2 の検査は宣言済みの型・関係名、端点の存在などを確認するが、それだけで事実の正しさや OWL の論理制約全般を保証しない（`steps/step_schema.py`、`pass2.py:validate_extraction`）。

README と実装は 16 個の MCP ツールを示し、設計文書の一部の「15 個」、以前の記事 [[mykgとclaude-desktopの接続]] の「14 個」と差がある。版と資料を分けて保持する。また、`DiGraph` への変換は両端の組をキーに `add_edge` するため、同じ向きの同じ 2 ノード間に複数の関係型がある場合、その属性を独立した多重エッジとして保持しない。JSONL の関係一覧と探索用グラフの表現を区別する必要がある（`exporter.py:_build_nx_graph`）。この点はコードから読める制約で、実データでの影響は未測定である。

## 取り込んだ内容と載せたページ

| 候補 | 主張と成り立つ条件 | 根拠の位置 | 行き先 | 理由 |
| --- | --- | --- | --- | --- |
| c1 | スキーマを先に導出し、その語彙で事実を抽出する | README「Extract Pipeline」、設計文書「Pass 1」「Pass 2」、`pipeline.py` | create | [[スキーマの導出と事実の抽出の分離]] に、分担と継承属性の展開を整理した |
| c2 | 構築と問い合わせを、保存ファイルと別プロセスの責務で分ける | README「Design」、`mcp_server.py` | update | [[mykg]] に構築・保存・利用の分担と現行版の参照を追加した |
| c3 | 型の定義と個別の事実の分離を二段階の抽出へ実装している | 設計文書「Extract Pipeline」 | update | [[オントロジーと知識グラフの役割]] に実装例を加えた |
| c4 | 現行の MCP は 16 ツールで、以前の記事と異なる | README「MCP」、`mcp_server.py` | update | [[mykgとclaude-desktopの接続]] に、元の記述を保ったまま後続の確認を追記した |
| c5 | 中間状態、孤立ノードの補正、差分更新、セッション統合を持つ | 設計文書の各節、`orchestrator.py`、`merge_pipeline.py` | source_only | 製品固有の運用として本記事にまとめた |
| c6 | 検証の非停止性、混合バッチの出所、DiGraph の表現には制約がある | `pipeline.py`、`step_schema.py`、設計文書、`exporter.py` | source_only | 実装の確認範囲と未測定の影響を本記事に明記した |

> 取り込んだ内容と載せたページ 補足: README の宣伝上の精度・速度の主張を実測値として採用していない。保存した主要実装 14 ファイルと設計文書の一覧・ハッシュは、下記のスナップショットの manifest.json にある。

## 関係するページ

- [[mykg]]: 製品の入口
- [[スキーマの導出と事実の抽出の分離]]、[[オントロジーと知識グラフの役割]]: 型の定義と個別の事実の分担。[[mykgとclaude-desktopの接続]]: 作者による利用例と原文で誤統合を見直す場面

出典: [リポジトリ](https://github.com/SenolIsci/mykg)、[固定した設計文書](https://github.com/SenolIsci/mykg/blob/afb0a9c9bafdc49751563b9aa7f59bcf4bb787fb/docs/architecture.md)、[README の日本語 raw](../../raw/mykgのアーキテクチャ.md)、[原文・実装のスナップショット](../../raw/mykg-source-afb0a9c9/manifest.json)。README の全訳と画像 2 点の補足は GPT-6 が作成し、コード・リンク・ブロックの対応を検査した。
