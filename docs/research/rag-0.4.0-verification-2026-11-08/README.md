# rag 0.4.0 の実機での確認（2026年11月7日〜8日）

rag 0.4.0（`v0.4.0`、`6a760b9`）は、本物のモデルと MCP を使う検証を流さずに出した。[機能実装の優先順位（4 版目）](../feature-priority-2026-11-06.md)の 1 位として、本物の OCR、埋め込みのモデル、MCP の接続で、`register_pdf` から検索までを確かめた。

## 結論

0.4.0 に、利用者に影響する不具合は見つからなかった。パッチの版（0.4.1）は出さない。OneDrive のオンラインだけのファイルの読み込みの失敗が、分かりにくいエラー文字列のまま残る問題だけを、0.5.0 で直した。

## Windows

作者の PC（Windows 11、16 スレッド）で、`tests/rag/` の検証のスクリプトを流した。モデルは `cl-nagoya/ruri-v3-30m`、OCR は NDLOCR-Lite（CPU）である。

| スクリプト | 結果 | 記録 |
| --- | --- | --- |
| `verify_pipeline.py`（製品の MCP で登録し、OCR の途中と埋め込みの途中で親を強制終了して再開し、検索する） | 18 項目すべて合格（約 9 分 30 秒） | [windows/pipeline-results.json](windows/pipeline-results.json) |
| `verify_controls.py`（配布の `uv run --script` で起動し、待機中のキャンセル、再接続、明示的な再試行） | 5 項目すべて合格 | [windows/controls-results.json](windows/controls-results.json) |
| `verify_retrieval.py`（検索の設定だけを変えたときのモデルの維持、空の索引） | 4 項目すべて合格 | [windows/retrieval-config-results.json](windows/retrieval-config-results.json) |

`verify_controls.py` は、2 回、MCP の起動の前に止まった。どちらも uv が依存を取得する段階である。

- 1 回目は、別のセッションが wiki の起動の速さを測っていて、同じ既定の uv のキャッシュを使っていた。依存の取得が 30 分進まなかった。
- 2 回目は、uv のキャッシュの中のファイル名の変更が「別のプロセスが使用中」（`os error 32`）で失敗した。

`UV_CACHE_DIR` を専用のキャッシュ（`.rag-poc-data/uv-cache-mcp`）にして流し直すと通った。rag の不具合ではない。

## Linux（WSL の Ubuntu 24.04）

`tests/rag/run_linux.sh` と同じ手順を、結果の書き出し先だけを変えて流した。対象は開発用リポジトリの main のチェックアウト（rag `6a760b9`）である。

| スクリプト | 結果 | 記録 |
| --- | --- | --- |
| `test_jobs.py`（単体試験） | 31 件が合格、2 件は Windows だけの試験なので省略（約 23 分） | — |
| `verify_controls.py`（配布の `uv run --script`） | 5 項目すべて合格（2 回目） | [linux/controls-results.json](linux/controls-results.json) |
| `verify_pipeline.py` | 最初の 5 項目（登録、OCR の途中での親の強制終了と子孫の停止、ジョブの保存）まで合格。その先は、待ち時間の上限を超えて止まった | [linux/pipeline-results-partial.json](linux/pipeline-results-partial.json) |

`verify_pipeline.py` が最後まで通らなかった原因は、WSL の環境の遅さと壊れ方で、rag の不具合ではないと判断した。

- 検証用の venv（`~/.cache/info-hive-validation/venv`）では、`import torch` が segfault で落ちる。2026年11月4日には通っていた。uv で依存をそろえた一時的な環境では、`import torch` は通る。
- その一時的な環境でも、pdfium がページを 1 枚読み込むのに約 10 秒かかる（試験の PDF は CID フォントを埋め込んでいない）。テキストのページの判定そのものは 1 ページ 0.3 秒以下である。
- `import torch` に 74 秒、埋め込みのモデル（`/mnt/c` のモデルのキャッシュ）の読み込みまでに 283 秒かかる。再接続のあと、OCR の残りとモデルの読み込みが重なり、埋め込みの最初のバッチを待つ上限（600 秒）を超える。
- 1 回目の `verify_controls.py` は、Windows で重い試験を同時に流していたため、キャンセルの応答が 4.7 秒（上限 2 秒）になり、明示的な再試行の完了も 600 秒で間に合わなかった。Windows を空けて流し直すと、5 項目すべて通った。

WSL の検証用の環境を作り直す（venv の torch、モデルのキャッシュを Linux の側に置く）のは、別の作業にする。

## 偽の値でしか確かめていなかった経路

| 経路 | 確かめたこと |
| --- | --- |
| OneDrive のオンラインだけのファイル | 作者の OneDrive の、ローカルに実体のない PDF（属性に `RECALL_ON_DATA_ACCESS`）で確かめた。登録（`Config.pdf_path()` と `Jobs.register()`）は通る。OneDrive の同期のアプリが動いていなかったため、読み込みは `[Errno 22] Invalid argument` で失敗した。rag を通さず Python で開いて読んでも同じである。0.4.0 では、この文字列だけがジョブの失敗の理由に残る。0.5.0 で、読めなかったことと、同期のアプリを起動してから取り込み直すことを伝えるようにした。同期のアプリが動いているときの読み込み（実体の取得）は確かめていない。同期を始めてしまうので、アプリを起動しなかった |
| ネットワークドライブ | 作者の PC には割り当てたネットワークドライブがなく（`net use` が空。O: はローカルの固定ディスク）、確かめていない。割り当てには管理者の操作や接続先の用意が要るので、行わなかった |
| ハードリンク | `tests/rag/test_jobs.py` の 4 件（`os.link` で作る本物のハードリンク、NTFS）が、別名の追従、切れたリンク、消えた別名、取り込み中の差し替えを確かめている。偽の値ではない。MCP を通した確認はしていないが、ハードリンクの扱いは `Engine.ingest_pdf()` の中にあり、MCP の経路に固有の処理はない |
