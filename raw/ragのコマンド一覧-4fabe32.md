# rag のコマンド定義の原本

対象 Git コミット 4fabe3294d86a367e635bc18635af6e7132a8d93。
各コマンドは Git オブジェクトから取得した定義の全文。補足資料は行番号で範囲を記す。

## コマンド定義

### info-hive-rag/commands/setup.md

[1–31 行](https://github.com/to884/info-hive-rag/blob/4fabe3294d86a367e635bc18635af6e7132a8d93/commands/setup.md#L1-L31)

````
---
description: RAG の派生データの保存先、埋め込みモデル、OCR、検索の設定を変える。
argument-hint: "<任意の派生データの保存先、モデル、OCR の指定>"
---

`rag` MCP サーバーの `configure` に、ユーザーが指定した設定だけを渡す。派生データの保存先は `data_dir`、埋め込みモデルは `embedding_model`、OCR の方針は `ocr_mode`、OCR の解像度は `ocr_dpi`、検索の設定は `retrieval` に渡す。指定のない項目は今の設定のまま残る。

PDF のフォルダは登録しない。PDF は `/wiki:ingest` で取り込むときに、絶対パスで渡す。どこにある PDF でもよい。rag 0.3.0 の参照ルート（`reference_roots`）は使わなくなった。設定ファイルに残っていれば、`configure` で保存し直したときに消える。

埋め込みモデルの暫定既定値は `cl-nagoya/ruri-v3-130m`。CPU が非力な環境では、ユーザーの希望に応じて `30m` または `70m` を指定できる。

`ocr_mode` は次の 3 つから選ぶ。既定は `auto`。

- `auto`: 文字化け、縦書き、スキャンと判定したページだけを OCR する
- `always`: すべてのページを OCR する
- `off`: OCR しない。OCR が要るページがあれば、その PDF の取り込みは失敗する

`ocr_dpi` は、OCR のためにページを画像にするときの解像度で、72〜300 の整数にする。既定は 150。上げると小さい文字を読みやすくなるが、OCR は遅くなる。

変える前に、取り込み済みの PDF への影響を説明する。

- 埋め込みモデル、`ocr_mode`、`ocr_dpi` を変えると、取り込み済みの PDF の入れ直しが要る。入れ直すまで、その wiki の索引は検索できない。入れ直す PDF の一覧は `/rag:status` で分かる。
- 埋め込みモデルだけを変えたときは、入れ直しのときに OCR をやり直さない。保存した抽出の結果を使い、埋め込みと索引だけを作り直す。
- `ocr_mode` か `ocr_dpi` を変えたときは、入れ直しのときに OCR もやり直す。前の設定の抽出の結果は残るので、設定を戻せば使い回せる。
- 検索の設定（`retrieval`）は、入れ直しを要しない。

`configure` の結果の `reingest_required` が `true` なら入れ直しが要り、`extraction_changed` が `true` なら入れ直しで OCR もやり直す。結果に合わせてユーザーに伝える。

PDF の原本には書き込まない。派生データの保存先の既定値は OS の利用者用アプリケーションデータ領域である。派生データの保存先の中にある PDF は登録できない。OneDrive などの同期対象のフォルダを指定する場合は、再生成できるデータの同期に時間がかかることを説明する。保存先を変えると、前の保存先の抽出の結果は引き継がない。

PDF の取り込みは `/wiki:ingest` で行う。取り込みを起点に抽出、OCR、埋め込み、索引更新が実行される。初回は実行環境とモデルを取得する。検索と埋め込みはローカルで処理するが、回答に使う上位チャンクは Claude Code に渡る。
````

### info-hive-rag/commands/status.md

[1–11 行](https://github.com/to884/info-hive-rag/blob/4fabe3294d86a367e635bc18635af6e7132a8d93/commands/status.md#L1-L11)

````
---
description: PDF の索引件数と、失敗・中断した取り込みを確認する。
---

ユーザーの指定とプロジェクト・グローバルの指示から対象の wiki を特定し、`rag` MCP サーバーの `status` に `wiki_root` の絶対パスを渡す。

文書数、チャンク数、ジョブ ID、進捗と失敗理由を日本語で報告する。`queued`、`running`、`paused` は索引化完了ではない。次回 rag の MCP 接続時に未完了ジョブは自動再開する。失敗したジョブは理由を直して `retry_job(wiki_root, job_id)` で再試行する。キャンセルには `cancel_job` を使い、`cancellation_accepted` を確認する。公開開始後はキャンセルできない。キャンセル済みのジョブは明示的に再試行しない限り再開しない。

応答に `legacy_data` があれば、rag 0.3.0 のデータ（`paths` の場所）が残っていることを伝える。新しい版はそれを読まないので、ユーザーが消してよい。消すのはユーザーに任せ、自分では消さない。0.3.0 で取り込んだ PDF は、`/wiki:ingest` で取り込み直す。

応答の `reingest_required` が `true` なら、埋め込みモデルや OCR の設定が変わったので、`reingest` の PDF を取り込み直す必要がある。1 件も取り込み直していないうちは、その wiki を検索できない。取り込み直し始めたら、取り込み直した PDF だけを検索できる。`reingest` の各項目の `paths`（PDF の場所）、`title`、`source_pages` を示し、`/wiki:ingest` で取り込み直すよう伝える。抽出の設定が前と同じなら、取り込み直しで OCR はやり直さない。
````

### info-hive-rag/commands/search.md

[1–9 行](https://github.com/to884/info-hive-rag/blob/4fabe3294d86a367e635bc18635af6e7132a8d93/commands/search.md#L1-L9)

````
---
description: wiki に取り込んだ PDF を、ページと出典付きで検索する。
argument-hint: "<質問>"
---

ユーザーが指定した wiki、プロジェクトの指示、グローバルな指示、現在のプロジェクトの `wiki/` の順に `<WIKI_ROOT>` を決める。

`rag` MCP サーバーの `search` を、`wiki_root=<WIKI_ROOT の絶対パス>`、`query=$ARGUMENTS` で呼ぶ。
結果の本文とページ番号、`raw`、`source_pages` を根拠に日本語で答える。結果にない事実を補わず、根拠が足りなければ追加の検索を行う。回答の生成は Claude Code が行う。
````

## 補足資料

### info-hive-rag/README.md

[11–71 行](https://github.com/to884/info-hive-rag/blob/4fabe3294d86a367e635bc18635af6e7132a8d93/README.md#L11-L71)

````

| 対象 | 名前 |
| --- | --- |
| リポジトリ | `to884/info-hive-rag` |
| プラグイン | `rag` |
| マーケットプレイス | `info-hive` |
| 導入するときの名前 | `rag@info-hive` |

## 導入

Claude Code で、マーケットプレイスを追加してから `rag` を入れます。依存先の `wiki` も自動で導入されます。

```text
/plugin marketplace add to884/info-hive-marketplace
/plugin install rag@info-hive
```

## PDF の取り込み

1. `/wiki:ingest <PDF の絶対パス>` を実行します。PDF はどこにあってもかまいません。フォルダを先に登録する必要はありません。wiki が `register_pdf` を呼び、ジョブ ID を受け取ります。自然言語で PDF の取り込みを依頼した場合も同じ手順を使います。
2. `/rag:status` で進捗を確認します。`completed` になると、wiki が抽出済みの Markdown を読み、ソースの要約ページを作成できます。

`queued`、`running`、`paused` は処理中です。PDF の索引化が完了したことや、wiki の要約ページが完成したことを意味しません。
PDF の原本はコピーも書き換えもしません。要約ページの `raw` は `C:/Books/日本語資料.pdf` のような `/` 区切りの絶対パスに、`raw_sha256` は PDF の内容の SHA-256 になります。別の PC では、同じ PDF を取り込み直すと SHA-256 で同じ文書と分かります。
受け付けるのは、拡張子が `.pdf` で、`%PDF-` の前にあるバイトが 1024 バイト以下の通常のファイルです。先頭に改行や空白があるだけの PDF も読みます。UNC パス（`\\server\share\...`）と、派生データの保存先の中の PDF は拒みます。ネットワークの PDF は、ドライブ文字を割り当ててから指定します。
派生データの保存先、埋め込みモデル、OCR、検索の設定を変えるときは `/rag:setup` を使います。
PDF のページごとの抽出と OCR の結果は、PDF の内容の SHA-256 と OCR の設定（`ocr_mode`、`ocr_dpi`）ごとに保存し、同じ保存先を使う wiki のあいだで共有します。埋め込みモデルを変えて取り込み直しても OCR はやり直さず、埋め込みと索引だけを作り直します。
埋め込みモデルや OCR の設定を変えると、その wiki の索引は次の取り込みで空になります。取り込み直す PDF は `/rag:status` の `reingest` で確かめられます。

Claude Code の終了時は、ワーカーと OCR の子プロセスを停止します。次回 rag の MCP 接続時に未完了のジョブを再開します。
保存済みのページと埋め込みバッチを再利用し、索引が揃ってから検索対象として公開します。
同じ PDF の OCR ページでは、モデルを読み込んだ子プロセスを再利用します。
文字が得られなかったページも処理結果を保存して次へ進み、PDF 全体で検索可能な本文が得られない場合はジョブを失敗として記録します。
キャンセル済みと失敗したジョブは自動再試行しません。

埋め込みはモデル本来の文脈長（現在の Ruri v3 は最大 8,192 トークン）まで扱い、上限超過はエラーにします。
本文を無言で切り捨てません。長い入力ではメモリを抑えるため埋め込みのバッチ数を自動で下げます。

| MCP ツール | 用途 |
| --- | --- |
| `configure` | 派生データの保存先、モデル、OCR（`ocr_mode`、`ocr_dpi`）、検索の設定を変える。未完了ジョブがある間は変更しない。入れ直しが要るかを `reingest_required` と `extraction_changed` で返す |
| `register_pdf` | PDF を絶対パスで登録し、ジョブ ID を返す。受付時に PDF の中身は読まない |
| `ingest_pdf` | 同じ引数を受け付ける `register_pdf` の別名。同期的な完了待ちではない |
| `job_status` | 指定した wiki とジョブの進捗・結果を返す。`wait_seconds=1〜30` で短時間待機できる |
| `cancel_job` | キャンセルする。索引の公開開始後は受理しないため、`cancellation_accepted` を確認する |
| `retry_job` | 失敗またはキャンセルしたジョブを明示的に再試行する |
| `status` | 対象 wiki の索引件数とジョブ一覧を返す。設定が変わって取り込み直す PDF があれば `reingest` で、0.3.0 のデータが残っていれば `legacy_data` で伝える |
| `search` | 公開済みの索引から本文、出典、ページ番号を検索する |

同じ保存先を使う複数の接続では、索引化を進めるワーカーを一つにします。OS の常駐サービスは作りません。
初回は `uv` が依存関係を取得し、OCR と埋め込みを初めて使う際にモデルを取得します。
検索も同じワーカーに渡すため、MCP の受付は検索用ライブラリやモデルの読み込みを待ちません。モデルの重みは検索・索引化時に読み込みます。
索引化と検索はワーカー内で直列に進めます。長い索引化の途中の検索は待機するため、完了後に検索してください。

## PC ごとの設定

設定ファイルは OS のアプリケーションデータ領域に置き、`INFO_HIVE_RAG_CONFIG` で場所を変更できます。
高度な設定では `model_cache_dir` と `uv_cache_dir` を指定し、準備済みのモデルと実行環境を再利用できます。
`uv_cache_dir` は OCR の実行環境に使います。MCP サーバー自身の実行環境キャッシュは、Claude Code の起動前に環境変数 `UV_CACHE_DIR` で指定できます。
設定変更はその MCP 接続に反映します。別の接続にも反映する場合は再接続してください。

````

### info-hive-rag/scripts/rag_server.py

[80–194 行](https://github.com/to884/info-hive-rag/blob/4fabe3294d86a367e635bc18635af6e7132a8d93/scripts/rag_server.py#L80-L194)

````
@server.tool()
def configure(data_dir: str = "", embedding_model: str = "", retrieval: dict | None = None,
              ocr_mode: str | None = None, ocr_dpi: int | None = None) -> dict:
    """派生データの保存先、埋め込みのモデル、検索の設定、OCR の設定（ocr_mode は auto / always / off、ocr_dpi は 72〜300）を、
    この PC の設定に保存する。指定しない項目は今の設定のまま。PDF は登録のときに絶対パスで渡す。
    reingest_required が true なら取り込み済みの PDF の入れ直しが要り、extraction_changed が true なら入れ直しで OCR もやり直す。"""
    global _engine, _jobs, _host, _config
    with _lock:
        if jobs().unfinished():
            raise ValueError("未完了ジョブがあります。完了させるかキャンセルしてから設定を変更してください。")
        current = configuration()
        embedding_model = embedding_model or current.model
        # 0.3.0 の reference_roots は使わないので、保存し直すときに消す（ADR-0013）。
        values = {key: value for key, value in current.values.items() if key != "reference_roots"}
        values["embedding_model"] = embedding_model
        if embedding_model != current.model:
            values.pop("embedding_revision", None)
        if data_dir:
            values["data_dir"] = data_dir
        if retrieval is not None:
            allowed = {"reranker", "rerank_limit", "min_rerank_score", "search_nprobes", "search_refine_factor"}
            if set(retrieval) - allowed:
                raise ValueError("retrieval に未対応の設定名があります。")
            values.update(retrieval)
        if ocr_mode is not None:
            values["ocr_mode"] = ocr_mode
        if ocr_dpi is not None:
            values["ocr_dpi"] = ocr_dpi
        checked = Config(values)
        if _host:
            _host.close()
        write_json(config_path(), values)
        _config = checked
        _engine, _jobs = None, Jobs(checked.data_dir)
        _host = WorkerHost(_jobs)
        _host.start()
        # 指紋が変われば取り込み済みの PDF の入れ直しが要る。抽出の設定も変われば OCR もやり直す（ADR-0014）。
        return {"config": str(config_path()), "data_dir": str(checked.data_dir), "embedding_model": checked.model,
                "ocr_mode": checked.ocr_mode, "ocr_dpi": checked.ocr_dpi,
                # 保存先を変えると、前の保存先の索引も抽出の結果も引き継がない。
                "reingest_required": checked.fingerprint != current.fingerprint or checked.data_dir != current.data_dir,
                "extraction_changed": checked.extraction_key != current.extraction_key or checked.data_dir != current.data_dir}


@server.tool()
def register_pdf(wiki_root: str, source: str, source_page: str, title: str = "") -> dict:
    """wiki の PDF 取り込みを受け付け、永続ジョブを返す。source は利用者が指定した PDF の絶対パス。queued は索引化完了ではない。原本はコピーしない。"""
    with _lock:
        return jobs().register(configuration(), wiki_root, source, source_page, title)


@server.tool()
def ingest_pdf(wiki_root: str, source: str, source_page: str, title: str = "") -> dict:
    """register_pdf の互換名。ジョブを受け付けて返し、完了は job_status で確認する。"""
    return register_pdf(wiki_root, source, source_page, title)


@server.tool()
async def job_status(wiki_root: str, job_id: str, wait_seconds: int = 0) -> dict:
    """進捗と完了時の抽出 Markdown を返す。wait_seconds=1〜30 で完了を短時間待てる。"""
    if not 0 <= wait_seconds <= 30:
        raise ValueError("wait_seconds は 0〜30 にしてください。")
    deadline = time.monotonic() + wait_seconds
    while True:
        result = jobs().status(wiki_root, job_id)
        if result["status"] in {"completed", "failed", "cancelled"} or time.monotonic() >= deadline:
            return result
        await asyncio.sleep(.1)


@server.tool()
def cancel_job(wiki_root: str, job_id: str) -> dict:
    """明示キャンセルし、次回接続時の自動再開から外す。公開開始後はキャンセルを受理しない。"""
    return jobs().cancel(wiki_root, job_id)


@server.tool()
def retry_job(wiki_root: str, job_id: str) -> dict:
    """失敗またはキャンセルしたジョブを明示的に再試行し、チェックポイントを再利用する。"""
    return jobs().retry(wiki_root, job_id)


@server.tool()
async def search(wiki_root: str, query: str, limit: int = 10) -> dict:
    """取り込み済み PDF を BM25 とベクトルで検索し、RRF 順位、本文、ページ、出典を返す。原本を読み直さない。"""
    identity = jobs().request_search(configuration(), wiki_root, query, limit)
    try:
        deadline = time.monotonic() + 600
        while time.monotonic() < deadline:
            result = jobs().search_status(identity)
            if result["status"] == "completed":
                return json.loads(result["result"])
            if result["status"] == "failed":
                raise ValueError(result["error"])
            await asyncio.sleep(.02)
        raise TimeoutError("検索の待機が時間切れになりました。索引化中の場合は完了後に再検索してください。")
    finally:
        jobs().drop_search(identity)


@server.tool()
def status(wiki_root: str) -> dict:
    """取り込み済みの件数と、中断・失敗した処理を確認する。"""
    result = engine().status(wiki_root)
    result["index_jobs"] = result.pop("jobs")
    result["jobs"] = jobs().list(wiki_root)
    legacy = jobs().legacy_data()
    if legacy:
        result["legacy_data"] = {"paths": legacy,
                                 "message": "rag 0.3.0 のデータが残っています。新しい版は読まないので、消してかまいません。"}
    return result


if __name__ == "__main__":
    server.run(transport="stdio")
````

### info-hive-wiki/commands/ingest.md

[78–84 行](https://github.com/to884/info-hive-wiki/blob/b8596d1888035769528cb74e35bda51c9d9c40a0/commands/ingest.md#L78-L84)

````
## PDF の登録（rag が有効な場合）

1. `python "${CLAUDE_PLUGIN_ROOT}/skills/info-hive/scripts/wiki_raw_ingest.py" pdf --wiki "<WIKI_ROOT>" --raw-root "<RAW_ROOT>" --source "<ユーザーが指定した PDF>"` を実行する。失敗したら理由を伝えて止まる。成功したら要約ページのスラッグを決め、`rag` MCP サーバーの `register_pdf` に `wiki_root=<WIKI_ROOT の絶対パス>`、`source=<検査の JSON が返した source>`、`source_page="sources/<スラッグ>.md"`、`title=<題名>` を渡す。`source` はスクリプトが返したパスの綴りを使う。ユーザーが指定していない PDF は登録しない。ツール名は接続に表示されたものを使う。別プラグインの内部パスを組み立ててスクリプトを実行しない。PDF を閲覧するだけの場合は登録しない。
2. 応答の `job_id` を記録する。`queued`、`running`、`paused` は受付・処理中であり、索引化や wiki の取り込み完了と報告しない。原本を `<RAW_ROOT>` へコピーしない。登録を拒まれたら、理由（絶対パスでない、PDF でない、UNC パス、rag の派生データの中にある、など）をそのまま伝える。
3. `job_status(wiki_root, job_id)` で進捗を確認する。短時間待つ場合は `wait_seconds=30` を使い、細かい連続呼び出しを避ける。処理中に会話を終える場合はジョブ ID と再開待ちの状態を報告し、ここで手順を止める。次回 rag の MCP 接続時に未完了ジョブは自動再開する。キャンセル済みのジョブは自動再開しない。
4. `completed` のときだけ `result.extracted_markdown` を分割して読み、通常の手順 4〜8 に進む。要約ページの `raw` には `result.raw`（`/` 区切りの絶対パス）を、`raw_sha256` には `result.sha256` を、`rag_job_id` にはジョブ ID を書く。値は二重引用符で囲み、`\` は `\\`、`"` は `\"` と書く。内容を読む前に要約を作らない。
5. `failed` は理由を報告し、修正後は `retry_job` で再試行する。`cancelled` の再試行は明示的に依頼された場合だけ行う。
````
