# rag 0.5.0 のネットワークドライブと OneDrive の実機での確認（2026年11月9日）

[rag 0.4.0 の実機での確認](../rag-0.4.0-verification-2026-11-08/README.md)では、次の 2 つを実物で確かめられなかった。どちらも、[機能実装の優先順位](../feature-priority-2026-11-06.md)の 1 で【要確認】として残していた。

- ネットワークドライブ: 作者の PC に、割り当てたネットワークドライブがなかった。
- OneDrive のオンラインだけのファイル: 同期のアプリが動いていなかったので、読み込みが失敗するところまでしか確かめていなかった。

rag 0.5.0（`v0.5.0`、`0ca80c7`）で、どちらも実物で確かめた。

## 結論

どちらも、登録から検索まで通った。rag の不具合は見つからなかった。

| 試験 | 結果 | かかった時間 | 記録 |
| --- | --- | --- | --- |
| `tests/rag/verify_network_drive.py` | 12 項目すべて合格 | 約 2 分 | [network-drive-results.json](network-drive-results.json) |
| `tests/rag/verify_onedrive.py` | 9 項目すべて合格 | 約 2 分 | [onedrive-results.json](onedrive-results.json) |

どちらも、作者の PC（Windows 11）で、開発用の venv（Python 3.12.13）から製品の MCP サーバー（`rag_server.py`）に接続して流した。モデルは `cl-nagoya/ruri-v3-30m` である。

## ネットワークドライブ

自分の PC の管理共有 `\\localhost\C$` を、空いているドライブ文字（今回は `Z:`）に `net use ... /persistent:no` で割り当てた。SMB のリダイレクターを通る、本物のネットワークパスである。割り当ては試験の終わりに外した。

| 確かめたこと | 結果 |
| --- | --- |
| `Z:\...\ネットワークの原本.pdf` を `Config.pdf_path()` で解決すると、UNC（`\\localhost\C$\...`）になる | 合格 |
| UNC のパスを直接 `register_pdf` に渡すと、「ドライブ文字を割り当ててから指定してください」で拒む | 合格 |
| ドライブ文字のパスで `register_pdf` を受け付け（332 ミリ秒）、取り込みを終え（3 ページ、3 チャンク）、検索で出典つきで返す | 合格 |
| 抽出の結果は、ネットワークの側でなく、ローカルの `data_dir/extracted/` に置く | 合格 |
| 割り当てを外したあとも、台帳の UNC の場所は「消えた」とみなさない | 合格 |
| 届かないサーバーの UNC（`\\info-hive-no-such-host.invalid\...`）は、ファイルもフォルダーも見えないので「消えた」とみなさない（0.03 秒） | 合格 |
| 原本の PDF は変わらない | 合格 |

### 確かめていないこと

- 別の PC の共有と、接続が途中で切れる場合は確かめていない。`\\localhost` は切れないので、取り込みの途中でサーバーが見えなくなったときの動きは、単体試験（偽の値）でしか確かめていない。
- 届かないサーバーの名前は `.invalid` なので、名前の解決がすぐに失敗した。実在するが応答しないサーバーでは、`os.stat()` が SMB のタイムアウトまで待つことがある。

## OneDrive のオンラインだけのファイル

作者の OneDrive（職場または学校のアカウント）にある、ローカルに実体のない PDF（属性に `RECALL_ON_DATA_ACCESS`、`0x400000`）を使った。個人の書類を避け、製品のマニュアル（1.9 MB、20 ページ）を選んだ。試験の開始時に、同期のアプリ（`OneDrive.exe`）が動いていることを確かめた。

| 確かめたこと | 結果 |
| --- | --- |
| 同期のアプリが動いている | 合格 |
| 登録の前、PDF はオンラインだけである | 合格 |
| `register_pdf` は中身を読まずに受け付ける（17 ミリ秒） | 合格 |
| 子ワーカーが読み込むと、同期のアプリが実体を取得し、取り込みを終える（20 ページ、47 チャンク、99 秒） | 合格 |
| 検索で出典つきで返し、`status` の文書の数は 1 である | 合格 |
| 読み込んだあと、PDF はローカルに実体がある（属性 `0x20`） | 合格 |
| 台帳の `doc_id` は、取得した内容の SHA-256 と一致する | 合格 |
| 試験の終わりに `attrib -P +U` で、オンラインだけの状態に戻した | 合格 |

1 回目は、`doc_id` の照合が、結果に `doc_id` がないときに何も比べずに合格になる書き方だった。台帳の `locations` と比べる形に直して流し直し、上の結果を得た。

### 確かめていないこと

- 実体の取得に時間がかかる大きな PDF と、取得の途中で同期のアプリを止める場合は確かめていない。
- 個人用の OneDrive（コンシューマーのアカウント）では確かめていない。

## 流し方

```bash
RAG_TEST_RUN_ROOT=C:/Works/info-hive-dev/.rag-poc-data/network-tests \
RAG_TEST_MODEL_CACHE=C:/Works/info-hive-dev/.rag-poc-data/model-cache \
RAG_TEST_UV_CACHE=C:/Works/info-hive-dev/.rag-poc-data/uv-cache-mcp \
/c/Works/info-hive-dev/.rag-venv/Scripts/python.exe -X utf8 tests/rag/verify_network_drive.py
```

`verify_onedrive.py` は、さらに `RAG_TEST_ONEDRIVE_PDF` に、オンラインだけの PDF の絶対パスを指定する。どちらも Windows だけで動く。`verify_network_drive.py` は `RAG_TEST_RUN_ROOT` を C: に置く前提で、別のドライブに置くときは `RAG_TEST_SHARE` を合わせて指定する。
