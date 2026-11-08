# rag 0.5.0 の Linux での確認（2026年11月8日）

rag 0.4.0 の確認では、WSL の Ubuntu で `verify_pipeline.py` が 5 項目までしか通らなかった（[rag 0.4.0 の実機での確認](../rag-0.4.0-verification-2026-11-08/README.md)の Linux の節）。検証用の環境を作り直し、rag 0.5.0（`v0.5.0`、`0ca80c7`）で `tests/rag/run_linux.sh` の 3 つの試験を流した。

## 結論

3 つとも通った。rag の不具合は見つからなかった。

遅さの元は、WSL の仮想ディスク（`ext4.vhdx`）が USB 接続の HDD（D:）にあり、その HDD が飽和していたことである。torch の読み込みも pdfium の最初のページも、このディスクを読む時間で遅くなっていた。検証用の環境を tmpfs（`/dev/shm`）に置き、フォントを先にページキャッシュへ読み込むと、試験全体が約 1 分半で終わる。

## 結果

`tests/rag/setup_linux_fresh.sh` で、空の tmpfs から環境を作って流した（作成と試験を合わせて 4 分 49 秒）。

| 試験 | 結果 | かかった時間 | 記録 |
| --- | --- | --- | --- |
| 単体試験（`test_jobs.py`、`test_indexes.py`、`test_extraction.py`） | 65 件のうち 63 件が合格。2 件は Windows だけの試験なので省略 | 11 秒 | [linux/unit.log](linux/unit.log) |
| `verify_pipeline.py`（製品の MCP で登録し、OCR の途中と埋め込みの途中で親を強制終了して再開し、検索する） | 18 項目すべて合格 | 54 秒 | [linux/pipeline-results.json](linux/pipeline-results.json) |
| `verify_controls.py`（配布の `uv run --script` で起動し、待機中のキャンセル、再接続、明示的な再試行） | 5 項目すべて合格 | 19 秒 | [linux/controls-results.json](linux/controls-results.json) |

版などの環境は [linux/environment.txt](linux/environment.txt) にある。Python 3.12.16（uv が管理するもの）、torch 2.8.0+cpu、transformers 5.22.1、sentence-transformers 5.7.0、pypdfium2 5.15.1、モデルは `cl-nagoya/ruri-v3-30m`、OCR は NDLOCR-Lite（CPU）である。

同じ環境で、作り直したあと最初に流したときも 3 つとも通った（単体 11 秒、pipeline 57 秒、controls 18 秒）。

## 遅かった原因

### WSL の仮想ディスクが飽和した USB の HDD にある

| 項目 | 値 |
| --- | --- |
| 仮想ディスクの場所 | `D:\Users\toshiki\AppData\Local\wsl\{718525c0-…}\ext4.vhdx`（25 GB、2026年4月16日に作成） |
| D: の装置 | Seagate HD-SGDA/N（8 TB、USB 接続の HDD） |
| D: の状態（Windows の性能カウンター、WSL は待機中） | ディスクの使用率 1700%、待ち行列 10、転送 1 回あたり 0.20 秒、転送量 0.6 MB/秒 |
| WSL の中の I/O の待ち（`/proc/pressure/io` の full） | 何もしていないときでも 70〜90% |
| WSL の中の読み込み 1 回あたり（`/proc/diskstats`） | 約 175 ms |

どのプロセスが D: を詰まらせているかは突き止めていない。プロセスごとの I/O の量では、VS Code と Microsoft PC Manager が上位だったが、ディスクの別は出ていない。WSL の中で `du` が 10 分以上終わらなかった。

### tmpfs での測定

依存の版をそろえ、置き場所だけを変えて測った。

| 項目 | HDD の上 | tmpfs の上 |
| --- | --- | --- |
| `import torch` | 108 秒（このときの `venv-serial-20261104`、ファイルは壊れていない）。0.4.0 の確認のときの uv の一時環境では 74 秒 | 2.6〜4.3 秒 |
| 埋め込みのモデルの読み込みまで | 283 秒（モデルは `/mnt/c`） | 試験の中で問題にならない |
| 単体試験 65 件 | 約 23 分（`test_jobs.py` の 33 件だけ） | 11 秒 |

検証用の旧 venv（`~/.cache/info-hive-validation/venv`）の `import torch` の segfault は、ここでも確かめた。結果は「旧環境」の節に書く。

### pdfium の最初のページが遅い

pdfium は、埋め込まれていないフォント（試験の PDF の `HeiseiMin-W3`）を置き換えるために、最初のページを読むときにシステムのフォントのフォルダーを全部開いて調べる。`/usr/share/fonts` には 890 ファイル（137 MB）がある。`cmap` と `cMap` のフォルダーは poppler の CMap へのシンボリックリンクで、その中も調べる。2026年11月7日に、ほかの作業で `fonts-noto-cjk` などが入った。

| 状態 | 1 ページ目 | 2 ページ目から |
| --- | --- | --- |
| フォントがページキャッシュにない | 13.3〜16.7 秒 | 0.002 秒以下 |
| フォントがページキャッシュにある | 0.02 秒 | 0.002 秒以下 |

0.4.0 の確認で「1 ページ約 10 秒」と書いたのは、この最初のページの時間だったと考える。rag は抽出のたびに PDF を 1 回開くので、待ちは子ワーカーの起動ごとに 1 回である。`run_linux.sh` は試験の前にフォントを読み込む（HDD から冷えた状態で 13〜37 秒）。

## 作り直した手順

- `tests/rag/setup_linux_fresh.sh`: 既定で `/dev/shm/info-hive-validation` に、uv が管理する Python 3.12、venv、uv のキャッシュ、モデル（`ruri-v3-30m` だけを開発用リポジトリの `.rag-poc-data/model-cache` から写す）を置く。OCR（`rag_ocr.py`）と配布の起動（`rag_server.py`）の uv の環境も先に作る。そのあと `run_linux.sh` を流す。`--setup-only` で作るだけにもできる。
- `tests/rag/run_linux.sh`: リポジトリの場所をスクリプトの位置から求める。以前はメインのチェックアウト（`/mnt/c/Works/info-hive-dev`）に固定で、worktree の変更を試せなかった。単体試験は `test_*.py` をすべて流す（以前は `test_jobs.py` だけ）。1 つが失敗しても残りを流し、最後に終了コードで知らせる。各試験の時間を `summary.txt` に、版を `environment.txt` に書く。
- 置き場所は `RAG_LINUX_ROOT` で変えられる。結果の書き出し先の既定は、このフォルダーの `linux/` にした。

tmpfs は WSL が止まると消える。WSL は最後のプロセスが終わってしばらくすると止まるので、作り直しと試験は 1 回の `wsl.exe` の呼び出しの中で続けて流す（`setup_linux_fresh.sh` がそうなっている）。作り直しは約 3 分半で、ほとんどが依存の取得である。tmpfs の使用量は約 3.3 GB（`/dev/shm` は 7.8 GB）。

```bash
wsl.exe -d Ubuntu-24.04 -u ubuntu -- bash /mnt/c/Works/info-hive-dev/tests/rag/setup_linux_fresh.sh
```

## 旧環境

`~/.cache/info-hive-validation` の旧 venv と uv のキャッシュは消していない。HDD の上の 2 つの venv を、wheel の `RECORD` にある SHA-256 と照らした（`INSTALLER` は uv が書き換えるので除いた）。

| venv | `import torch` | `RECORD` との照合 |
| --- | --- | --- |
| `venv`（2026年11月4日 11:51） | segfault（終了コード 139）。`torch/__init__.py` の 416 行目で拡張モジュールを読み込むところで落ちる | 5,129 ファイルが空（3,005）か、中身がすべて 0（2,123）。`torch/lib/libtorch_cpu.so` と `libtorch_python.so` を含む。多いのは transformers（2,667）、scipy（1,251）、scikit-learn（832） |
| `venv-serial-20261104`（同 15:21） | 通る。108 秒 | すべて一致 |

空のファイルと 0 で埋まったファイルは、ext4 で、書き込んだデータがディスクに届く前に仮想マシンが止まったときの壊れ方である。HDD が飽和していると書き戻しが大きく遅れるので、起きやすい。segfault は、0 で埋まった共有ライブラリを読み込んだためと判断した。旧版の `setup_linux_fresh.sh` が導入のあとに `sync` を呼んでいたのも、このためだったと考える。tmpfs に置く今の手順では、この問題は起きない（WSL が止まれば環境ごと消え、作り直す）。

## 残したこと

- 根本の対処は、WSL の仮想ディスクを C:（NVMe の SSD）に移すことである。`wsl --manage Ubuntu-24.04 --move <C: のフォルダー>` か、`wsl --export` と `wsl --import` で移せるが、どちらも WSL を止める必要があるので、作者の判断に任せる。移せば、tmpfs を使わずに `RAG_LINUX_ROOT=$HOME/.cache/info-hive-validation` で流せるはずである（確かめていない）。
- D: を詰まらせているプロセスは突き止めていない。
- 空の tmpfs で `run_linux.sh --controls-only` だけを流すと、`verify_controls.py` が土台にする `j*/config.json`（`verify_pipeline.py` が作る）がなく、失敗する。以前からの動きで、今回は直していない。
- `RAG_TEST_OUTPUT` の既定はこのフォルダーの `linux/` なので、流し直すと記録を上書きする。別の記録にするときは `RAG_TEST_OUTPUT` を指定する。
