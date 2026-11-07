レビューの対象は、rag プラグイン（info-hive-rag 0.3.0）の設計の変更を決める ADR-0013（`docs/adr/0013-rag-records-pdfs-by-absolute-path-and-hash.md`、状態は提案）である。まだ実装していない。

## 目的
`/rag:setup` で「参照ルート」（PDF のあるフォルダーに名前を付けて登録する設定）を決める仕組みを廃止する。PDF はドライブのあちこちにあるので、ルートを決めるのが不便だからである。作者は次の 2 つを決めた。
- PDF の場所は、絶対パスと内容の SHA-256 で記録する（台帳と wiki のソースのページの `raw:`）。
- 0.3.0 の設定（`reference_roots`）と台帳との互換は捨てる。製品版の台帳を使った人はいない。

この 2 つは決定済みなので、覆す提案はしない。崩してほしいのは、それ以外の決定（読む前の確認、台帳のキーの正規化、返す値、互換の扱い、wiki の手順）である。

## 崩してほしいこと
1. 参照ルートが担っていた「読む範囲の制限」を、「解決したパスが通常のファイル、拡張子 .pdf、先頭 5 バイトが %PDF-、派生データとキャッシュの外」で代えてよいか。MCP のツールにモデルがパスを渡す前提で、これで防げない読み出しや、rag が自分のファイルや原本を書き換える経路はないか。シンボリックリンク、ジャンクション、UNC パス、OneDrive のオンデマンドのファイル、ネットワークドライブ、ファイルの差し替え（確認と読み込みのあいだ）を考える。
2. 台帳のキーを「NFC にそろえたあと os.path.normcase」にすることで、同じファイルが 2 つのキーになる、または別のファイルが 1 つのキーになる場合はないか（Windows のドライブ文字、8.3 形式の短い名前、大文字と小文字を区別するフォルダー、macOS の NFD、Linux）。
3. 同じパスの内容が変わったときの版の更新と、移動と改名の扱い（同じ SHA-256 なら同じ文書、もうないパスを外す）が、キーを変えても壊れないか。
4. 0.3.0 の台帳を検出して止める方法（`documents` に `root` の列があるか）と、0.3.0 の未完了のジョブ（`jobs.sqlite` の `ingest_jobs`、`config` に古い設定の写しがある）を再開しないことが、穴なく実装できるか。止まったときに利用者が抜け出せるか。
5. wiki の `raw:` に絶対パス、`raw_sha256:` に SHA-256 を書くことで、wiki の lint、グラフ（`wiki_graph_extract.py` の `summarizes_raw`）、検索、ほかの PC での利用に問題が出ないか。
6. ADR に書いていない影響（ドキュメント、試験、MCP のツールの説明、`status` の出力など）で、抜けているものはないか。

## 読むファイル（info-hive-dev のルートから）
- `docs/adr/0013-rag-records-pdfs-by-absolute-path-and-hash.md`
- `info-hive-rag/scripts/rag_config.py`
- `info-hive-rag/scripts/rag_index.py`
- `info-hive-rag/scripts/rag_jobs.py`
- `info-hive-rag/scripts/rag_server.py`
- `info-hive-rag/scripts/rag_worker.py`
- `info-hive-rag/commands/setup.md`、`info-hive-rag/README.md`
- `info-hive-wiki/commands/ingest.md`、`info-hive-wiki/skills/info-hive/references/ingest-workflow.md`
- `info-hive-wiki/skills/info-hive/scripts/wiki_graph_extract.py`（`raw:` の扱い）
- `tests/rag/test_jobs.py`
- 背景: `docs/adr/0007-rag-uses-mcp-core-and-persistent-jobs.md`、`docs/adr/0012-wiki-owns-local-mcp-index-server.md`
