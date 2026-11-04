# RAG の開発用 PoC

このディレクトリは製品プラグインの配布対象ではない。
結果と判定は [2026年11月4日の検証記録](../../docs/research/rag-poc-2026-11-04/README.md) に置く。
以下はリポジトリのルートで実行する PowerShell の例である。

## 環境

Python 3.12、Windows、CPU、Meiryo フォントを使った。
ライブラリは `requirements-lock.txt`、モデルは `benchmark.py` の commit SHA に固定した。

```powershell
uv venv .rag-venv --python 3.12
uv pip install --python .rag-venv/Scripts/python.exe -r poc/rag/requirements-lock.txt --extra-index-url https://download.pytorch.org/whl/cpu
```

`LOCALAPPDATA/info-hive/rag-poc/2026-11-04` が実行領域となる。
Codex の Windows パッケージ環境では、モデルの保存先は `Path.resolve()` した物理パスを使う。
索引の書き込み先は `.rag-poc-data/` で、Git の対象から外してある。

Qdrant は [v1.20.0 の Windows バイナリ](https://github.com/qdrant/qdrant/releases/download/v1.20.0/qdrant-x86_64-pc-windows-msvc.zip) を展開し、実行領域の `qdrant-bin/qdrant.exe` に置く。
スクリプトが専用の loopback ポートで起動し、処理終了時に停止する。
NDLOCR-Lite の固定版は製品試作の `info-hive-rag/scripts/rag_ocr.py` から `uv run --script` で実行した。
GPU と Docker は使っていない。

## ジョブと索引の制御

```powershell
.rag-venv/Scripts/python.exe -X utf8 poc/rag/make_fixture.py
.rag-venv/Scripts/python.exe -X utf8 poc/rag/run_protocol.py
.rag-venv/Scripts/python.exe -X utf8 poc/rag/check_backends.py
```

制御試験は実際の stdio MCP 接続とプロセス強制終了を使う。
抽出結果のハッシュをページごとに保存し、再開、キャンセル、世代の公開を検査する。
この処理を埋め込みモデルの精度試験とは扱わない。
製品試作の接続不足と PDF API のエラーも記録するため、結果 JSON には想定した失敗が含まれる。

## 実資料の検索

原本を参照する `sample-manifest.json` と、抽出後の `pages.jsonl` は実行領域に保存する。
manifest は `root`、`seed`、`files` を持ち、各要素は `relative_path` と `size` を持つ。
今回使った原本のハッシュは検証記録の `extraction-results.json` にある。
参照台帳と抽出本文は Git に含めないため、別の原資料から作ると同じ評価セットにはならない。

```powershell
.rag-venv/Scripts/python.exe -X utf8 poc/rag/extract_sample.py
.rag-venv/Scripts/python.exe -X utf8 poc/rag/inspect_routing.py
.rag-venv/Scripts/python.exe -X utf8 poc/rag/prepare_corpus.py --include-pdf
.rag-venv/Scripts/python.exe -X utf8 poc/rag/benchmark.py --model 30m --reranker int8 --reranker-size tiny --rerank-limit 20 --tag v2
.rag-venv/Scripts/python.exe -X utf8 poc/rag/benchmark.py --model 70m --reranker int8 --reranker-size tiny --rerank-limit 20 --tag v2
.rag-venv/Scripts/python.exe -X utf8 poc/rag/benchmark.py --model 130m --reranker int8 --reranker-size tiny --rerank-limit 20 --tag v2
.rag-venv/Scripts/python.exe -X utf8 poc/rag/vector_precision.py
.rag-venv/Scripts/python.exe -X utf8 poc/rag/analyze_results.py
.rag-venv/Scripts/python.exe -X utf8 poc/rag/summarize.py
.rag-venv/Scripts/python.exe -X utf8 poc/rag/audit_sources.py
```

比較実行は直列に行う。CPU の重い処理を同時に走らせない。
`--vectors` で同じモデル・コーパスの `vectors.npy` を渡すと、埋め込み済みの文書を再利用できる。
`--reranker-size xsmall --rerank-limit 8` などでリランクの範囲を変える。
V1 は `prepare_corpus.py` の引数を省いた 47 正例、V2 は `--include-pdf` を付けた 107 正例であり、別の評価セットとして扱う。

PDF 質問の 60 問はエージェントが作った暫定ラベルで、人手による精度判定は済んでいない。
`vector_precision.py` は全件走査による保存丸めの確認で、ANN の量子化ベンチマークではない。
