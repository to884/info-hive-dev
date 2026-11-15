# PDF の本文の取り出しと変換のツールの調査（2026-11-15）

info-hive の wiki と rag で PDF の本文を取り出す方式を選ぶために、ローカルで使えるライブラリとツールを調べた。調査はサブエージェントが、公式のリポジトリ、PyPI、文書を読んで行った。ここに書いた事実は、その報告を整理したものであり、この文書を書いた時点で一つずつ確かめ直してはいない。確かめられなかったことは「未確認」と書く。手元で動かして比べた結果は、[ADR-0024 の承認の条件の検証](adr-0024-verification-2026-11-15.md)の「書き直しの案のための比較」にある。

## 求める条件

- ローカルだけで動く（外部の API に送らない）
- pip（uv）だけで入る。別のプログラムを入れずに済むのが望ましい
- Python 3.12 以上、CPU で動く
- 日本語に強い。縦書きと段組み、読み順、表、ページの区切りを扱える
- コードとモデルの重みのライセンスが、MIT のプラグインで使える（AGPL、GPL、非商用の重みは使えない）

## 比較表

| ツール | 種類 | ライセンス（コード / 重み） | pip だけで入るか | torch | 日本語 / 縦書き | 最新版 | 判定 |
| --- | --- | --- | --- | --- | --- | --- | --- |
| pypdfium2 | 文字の層 | BSD-3-Clause と Apache-2.0 | ○ | 不要 | ○ / 判定だけ | 5.15.2（2026-11） | 使用中（rag） |
| pdfminer.six | 文字の層 | MIT | ○ | 不要 | ○ / `detect_vertical` | 20260107（2026-01） | 比べた |
| Docling | レイアウトのモデル | MIT / 未確認 | ○ | 必要（今回の環境で入った） | ○ / 未確認 | 2.150.1（2026-11） | 比べた |
| NDLOCR-Lite | OCR | CC BY 4.0 / DINOv3 の条件つき | ○（1.4.0.dev0） | 不要 | ○ / ○ | 1.4.0.dev0（2026-11） | 使用中（rag の OCR） |
| pdf_oxide | 文字の層（Rust） | MIT または Apache-2.0 | ○ | 不要 | ○ / 縦書きを自動で並べ替える（ソースで確認） | 0.3.78（2026-09） | 候補（未計測） |
| pdfplumber | 文字の層（pdfminer の上） | MIT | ○ | 不要 | ○ / 方向を指定できる | 0.11.10（2026-06） | 候補（未計測） |
| MinerU | レイアウトのモデル、OCR | 独自（Apache-2.0 に条件を足したもの） | ○ | 任意 | 未確認 / 未確認 | 4.2.2（2026-11） | 候補（未計測、ライセンスの確認が要る） |
| Kreuzberg 4 | Rust とモデル | MIT / モデルは未確認 | ○ | 不要 | 未確認 / 未確認 | 4.10.4（2026-09） | 候補（未計測） |
| Marker | レイアウトのモデル、OCR | Apache-2.0 / 制限つきの OpenRAIL-M | ○ | 必要 | 日本語と縦書きに対応と主張 | 2.2.0（2026-11） | 条件付き |
| PaddleOCR | OCR とモデル | Apache-2.0 / 未確認 | 未確認 | 不要 | ○ / 未確認 | 3.7.0（2026-06） | 次点 |
| PyMuPDF 2、pymupdf4llm | 文字の層と GNN | AGPL-3.0 または商用 | ○ | 不要 | 記述なし | 2.1（2026-11） | 除外（AGPL） |
| YomiToku | 日本語の OCR とレイアウト | CC BY-NC-SA 4.0 | ○ | 必要 | ○ / ○ | 0.16.2（2026-11） | 除外（非商用） |
| Surya | VLM | Apache-2.0 / 制限つき | ×（llama-server が要る） | 不要 | 未確認 | 0.24.0（2026-11） | 除外 |
| Unstructured | 混合 | Apache-2.0 | ×（tesseract と poppler が要る） | 未確認 | 未確認 | 0.27.37（2026-11） | 除外 |
| opendataloader-pdf、GROBID、Apache Tika、tabula-py | Java | Apache-2.0 など | ×（Java が要る） | 不要 | 未確認 | － | 除外 |
| olmOCR | VLM | Apache-2.0 / 未確認 | ×（12 GB 以上の GPU） | 必要 | 未確認 | 0.4.27（2026-03） | 除外 |
| Nougat | VLM | MIT / CC-BY-NC | ×（依存が満たせない） | 必要 | 未確認 | 0.1.17（2023-10） | 除外 |
| NDLOCR v2（ndlocr_cli） | OCR | CC BY 4.0 | ×（Docker と CUDA） | － | ○ / ○ | 2025-09 の更新 | 除外（Lite で代わりが利く） |
| extractous | Rust と Tika | Apache-2.0 | ○ | 不要 | 未確認 | 0.3.0（2024-12） | 除外（更新が止まっている） |
| Xberg | Rust | MIT | ×（Windows の wheel がない） | 不要 | 未確認 | 1.3.9（2026-10） | 除外 |
| Mistral OCR、LlamaParse、Azure Document Intelligence | クラウド | － | － | － | － | － | 除外（外部に送る） |

## 個別のツールで分かったこと

### pdf_oxide

Rust で書いた PDF の取り出しのライブラリで、Python の wheel がある（win_amd64 で約 11.6 MB）。縦書き用の並べ替え（`reading_order/tategaki.rs`。列を右から左へ、各列を上から下へ）を持ち、スパンの `wmode` で縦書きのページを見分けて自動で使う。横組みには、Simple、Geometric、XYCut、StructureTree の 4 つの戦略がある。Markdown と表とページごとの API がある。版は 0.x で、リリースノートには、縦書きの判定が横組みの日本語に誤って効いた不具合の記載があった（詳細は未確認）。日本語の実例での評価はない。

### pdfplumber

pdfminer.six の上に、表の取り出し（`extract_tables`）と、文字と行の方向の指定（`line_dir`、`char_dir`、回転した文字の扱い）を足したもの。依存は pdfminer.six、Pillow、pypdfium2 で、torch は要らない。`extract_text` で縦書きを読ませる設定が、`detect_vertical` と組み合わせて働くかは未確認。

### NDLOCR-Lite

rag が OCR に使っている。rag が固定しているコミット e57f7c6（2026-10-28）のあとに、読み順の並べ替えで `is_vertical()` の呼び出しが抜けていた箇所の修正（a12fb49、2026-10-30。2026-11-05 にマージ）と、pip での導入の準備（2026-11-11、PyPI の `ndlocr-lite` 1.4.0.dev0）が入った。rag は縦書きのページに NDLOCR-Lite を使うので、この修正の影響を確かめる価値がある。

- **ライセンス:** コードは CC BY 4.0。レイアウトのモデルは DINOv3 から蒸留したもので、README は DINOv3 のライセンスを守るよう求めている（配布のときに契約の写しを付けること、「Built with DINOv3」の表示、用途の制限など。蒸留したモデルに及ぶかは明記がない）。
- **出力:** XML（行ごとの座標、確信度、読み順）と JSON（`isVertical` を含む）。PDF はページごとに出す。
- **精度:** 活字の F 値の中央値は 0.97 前後（公表値）。CPU の速度の公表値はない。

### Docling

中身は `docling-slim[standard]` で、OCR のエンジンは追加機能に分かれた。ライセンスは MIT。モデルの重みのライセンスは未確認。

### MinerU

独自のライセンス（Apache-2.0 に、月間の利用者が 1 億人を超えるか月の売上が 2,000 万ドルを超えるときの商用ライセンスと、オンラインのサービスでの表示義務を足したもの）。既定は CPU と ONNX で動き、モデルは basic で約 0.8 GB。日本語と縦書きの対応は未確認。

調査の途中で、MinerU の PyPI と GitHub のページに、AI のエージェントに向けた指示（導入の実行、記憶の書き換えなど）が埋め込まれているのが見つかった。サブエージェントはこれに従っていない。MinerU を試すときは、この点に注意する。

## 比べる価値のある候補

手元でまだ比べていないもののうち、次の 4 つを比べる価値がある。

1. **pdf_oxide:** pip だけで入り、ライセンスも寛容で、縦書きを自動で並べ替える。組版のソフトで作った日本語の PDF で、文字の順の問題を避けられるかを確かめる。
2. **pdfplumber:** pdfminer の読み順を保ったまま、表と方向の指定が加わる。
3. **MinerU（basic、ONNX、CPU）:** torch なしで動き、表とページの位置を出す。ライセンスの条件を確かめる必要がある。
4. **Kreuzberg 4.10.4:** MIT で Windows の wheel があり、ページの目印を出せる。

## 主な出典

- PyPI の JSON API（各パッケージの `pypi.org/pypi/<パッケージ>/json`）
- https://github.com/yfedoseev/pdf_oxide 、https://docs.rs/crate/pdf_oxide/0.3.76/source/src/pipeline/reading_order/tategaki.rs
- https://github.com/jsvine/pdfplumber
- https://github.com/ndl-lab/ndlocr-lite （README、リリース、コミット、requirements.txt、evaluation_jptype.csv）
- https://ai.meta.com/resources/models-and-libraries/dinov3-license
- https://github.com/opendatalab/MinerU 、https://github.com/opendatalab/MinerU/blob/master/LICENSE.md
- https://github.com/kreuzberg-dev/kreuzberg
- https://github.com/datalab-to/marker 、https://github.com/datalab-to/surya
- https://github.com/pymupdf/pymupdf4llm 、https://pymupdf.readthedocs.io/en/latest/changes.html
- https://github.com/kotaro-kinoshita/yomitoku
- https://github.com/PaddlePaddle/PaddleOCR
- https://github.com/ndl-lab/ndlocr_cli
