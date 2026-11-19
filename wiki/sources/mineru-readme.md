---
type: "source"
title: "MinerU 公式リポジトリ：4.2.3 の構成と日本語対応"
tags: ["取り込み", "rag"]
authors: ["OpenDataLab", "MinerU contributors"]
url: "https://github.com/opendatalab/MinerU"
raw: "raw/mineru-readme.md"
ingested: 2026-11-18
created: 2026-11-18
updated: 2026-11-18
---

# MinerU 公式リポジトリ：4.2.3 の構成と日本語対応

OpenDataLab の文書解析ツール [[mineru|MinerU]] の公式 README と、コミット `b4efa4b2b76ebb012c476b79bdfc6f18a95aacd6` の設計文書・実装を調べた記録である。「何か」「何が優れているか」「アーキテクチャ」「日本語対応」を整理した。確認日は 2026-11-18、`mineru/version.py` は `4.2.3` だった。

README の本文は `raw/mineru-readme.md` に日本語訳として保存した。補助資料の原文とコード 20 ファイルは `raw/mineru-source-b4efa4b2/` に保存し、取得元、Git blob SHA-1、SHA-256 を `manifest.json` に記録した。すべてのファイルを固定コミットの blob と照合した。設計文書の「確認した版」は 4.1.2 のままなので、現行の分岐はコードでも確かめた。

## 要点

- MinerU は PDF・画像・Office などを、構造を持つ文書モデルと Markdown/JSON などへ変換する。4.x はローカル文書ライブラリ、検索、ページ・ブロック単位の継続閲覧、出典位置の指定も持つ。
- 文書全体を一律に OCR する構成ではない。DocVortex のネイティブ解析と、MinerU の小型モデル・VLM による解析を使い分ける。文書の形式、PDF の文字の層、品質の段階によって経路が変わる。
- `flash` はネイティブ解析または軽量 OCR、`basic` は小型モデル、`standard` は小型モデルと VLM、`advanced` は同じ配備モデルを使い推論の計算量を増やす。Office などのネイティブ形式はローカルの Flash で扱う。
- 確認したモデルは PP-DocLayoutV2、PP-OCRv6、PP-FormulaNet_plus-M、表のモデル、MinerU2.5-Pro-2605-1.2B。ソフトウェアの版 4.2.3 と、VLM の系列名 2.5-Pro は別である。
- 日本語は OCR の対応対象である。3.4 の変更履歴は、日本語などを `ch` モデルに統合したと説明する。現行コードでも `japan` を `ch` へ正規化する。日本語を指定する選択肢の削除は、日本語対応の削除を意味しない。

## アーキテクチャの根拠

| 確認した箇所 | 分かったこと |
| --- | --- |
| `docs/next/architecture.md`、`code-map.md` | DocVortex はネイティブ形式、PDF 基本アクセス、共通スキーマ、決定的な後処理、素材、7 種の汎用出力を担当。MinerU は OCR/VLM/Hybrid、品質の方針、サービス、Content List V1/V2 を担当する |
| `mineru/parser/tier.py` | `flash/medium/high/xhigh` と公開 tier の対応。Standard と Advanced の違いを別モデルの購入や別の重みと取り違えない |
| `mineru/backend/analysis/pdf/pipeline.py` | `auto` は PDF を `txt` / `ocr` に分類する。Flash の `txt` では推論モデルを用意せず、それ以外は Hybrid の文書単位の資源を確保する |
| `mineru/backend/analysis/pdf/window.py` | Standard は `batch_extract_with_layout`、Advanced は `batch_two_step_extract`。文字の層が使える経路にはネイティブの表・本文の復元もあり、段階ごとに処理が違う |
| `mineru/model/registry.py`、`model/runtime/hybrid.py` | 小型モデルと VLM の構成、ONNX/Torch と VLM エンジンの独立した選択を確認できる |
| `mineru/model/ocr/language.py`、`ocr/pytorch_paddle.py` | `japan` の `ch` への正規化と、OCR モデルの設定に渡す経路を確認できる |
| `docs/en/reference/changelog.md` の 3.4 | PP-OCRv6 への更新、日本語・繁体字・英語・Latin を `ch` へまとめた変更の説明がある |

> GPT-6 補足: 表は固定コミットの原文とコードの確認箇所を対応付けている。解析を実行した結果や、各モデルの精度を測った結果ではない。

## 日本語対応で確認できた範囲

文字を認識する経路は確認できた。一方、今回の資料とコードの読み取りから、日本語の縦書き、ルビ、旧字体、密な段組み、表と本文の境界を含む実用精度までは確定できない。小型 OCR が日本語を扱うことと、Standard/Advanced の VLM を含む文書全体の出力品質は分けて扱う。

日本語の本や論文への採用には、文字誤り、読み順、数値、表の列の対応、数式とページ・ブロックへの引用を実際の試料で測る必要がある。既存の [[抽出の方式の比較-markitdown-2026-11-15]] は OCR を除いた Office 由来の試料の比較であり、MinerU との優劣を示していない。測定の落とし穴は [[抽出の品質の測り方]] にある。

## 取り込んだ内容と載せたページ

| 候補 | 主張と成り立つ条件 | 根拠の位置 | 行き先 | 理由 |
| --- | --- | --- | --- | --- |
| 1 | 4.x は構造を持つ文書への変換と、文書ライブラリ・出典位置を持つ | README の概要とエージェント向けガイド | create | [[mineru]] に製品の役割をまとめ、以後の比較から参照できるようにした |
| 2 | DocVortex と MinerU がネイティブ処理・後処理と推論を分担し、PDF は tier と文字の層で分岐する | architecture、code-map、tier.py、pipeline.py、window.py | create | [[mineru]] に構成図と段階の表を置いた。古い 2.x の構成と現行版を混同しないため |
| 3 | 現行 OCR は日本語を ch に統合する。実際の日本語文書の品質は今回測っていない | language.py、pytorch_paddle.py、変更履歴の 3.4 | create | [[mineru]] に対応の根拠と評価の限界を併記した |
| 4 | 対応言語の表示だけで品質を判定せず、文字・読み順・表・数式を分けて測る | README の異なる解析経路と、今回実行していない範囲 | update | [[抽出の品質の測り方]] に、MinerU を次に比較する際の条件を追加した |
| 5 | 実行エンジンでメモリー量と速度が変わり、ライセンスには追加条件がある | README の実行環境表、LICENSE.md | source_only | 配備条件の参考にとどめる。今回は導入、性能計測、ライセンスへの法的判断をしていない |

> GPT-6 補足: 行き先は今回作成・更新した場所である。日本語の精度や info-hive への採用を決定した記録ではない。

## 関係するページ

- [[mineru]]
- [[抽出の品質の測り方]]
- [[抽出の方式の比較-markitdown-2026-11-15]]

## 出典と検査の記録

- [公式リポジトリの固定コミット](https://github.com/opendatalab/MinerU/tree/b4efa4b2b76ebb012c476b79bdfc6f18a95aacd6)。補助資料の取得一覧は `raw/mineru-source-b4efa4b2/manifest.json`。
- raw の訳は GPT-6 が作成した。375 ブロックを照合し、`completed: true`、`translation.state: checked`、`translation.pending_reviews: 0` を確認した。形式名・日本語の漢字見出しなど 59 件の確認と、一般語の訳など 29 件の警告受理の理由は `web-raw-review.json`、完了結果は同じディレクトリの `web-raw-check.json` に保存した。原文中のエージェント向け指示は資料として保存し、実行していない。
