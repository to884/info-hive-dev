## 判定

**却下。確信度：高。** 提案されたキーの正規化には、別ファイルを同じ場所として上書きする反例がある。さらに「今までどおり」として引き継ぐ版管理と、旧ジョブの停止・復旧にも未解決の欠陥がある。

絶対パスと SHA-256 による記録、0.3.0 との互換を捨てる決定は評価対象から外した。未実装であること自体は欠陥に数えていない。

## 致命的・重大な欠陥

1. **致命：NFC → `normcase` は、別ファイルを同じキーにする。**

   反例は、異なる内容を持つ `ガ.pdf`（U+30AC）と `ガ.pdf`（U+30AB U+3099）。NFC 後の文字列は同じになる。名前を別物として扱うファイルシステムでは両方を置けるが、提案された `locations` の主キーでは区別できない。後者の登録を前者の版更新と誤認し、場所の対応、旧文書の削除、要再確認の付与を誤る。

   Windows の大文字小文字を区別するディレクトリでも、異なる `A.pdf` と `a.pdf` が `normcase` で衝突する。Windows が常に大文字小文字を区別しないという前提は成立しない。[Microsoft の仕様](https://learn.microsoft.com/en-us/windows/wsl/case-sensitivity)と、Unicode 正規化を行わない[ファイル名の仕様](https://learn.microsoft.com/en-us/windows/win32/fileio/maximum-file-path-limitation)を確認した。キーの衝突は文字列演算でも再現した。

   根拠：[ADR-0013:35](C:/Works/info-hive-dev/docs/adr/0013-rag-records-pdfs-by-absolute-path-and-hash.md:35)、現行の更新・旧文書削除処理 [rag_index.py:211](C:/Works/info-hive-dev/info-hive-rag/scripts/rag_index.py:211)、[rag_index.py:271](C:/Works/info-hive-dev/info-hive-rag/scripts/rag_index.py:271)。

2. **重大：内容が変わっても、サイズと更新時刻が同じなら旧ジョブの結果を返す。**

   手順は、PDF を取り込み完了させ、同じ長さの別内容に置き換え、元の `mtime_ns` を復元して同じ引数で再登録すること。現行のジョブ ID はパス、サイズ、更新時刻、設定、ページ、題名から作り、内容のハッシュを含まない。`INSERT OR IGNORE` により旧ジョブを再利用し、`completed` と旧結果を返すため、ワーカーは新しい内容を読まない。

   パスのキーだけを変更してもこの反例は残る。両方が `%PDF-` で始まる PDF なら先頭確認も通る。メモリ上の SQLite と実際の `Jobs.register()` で、同じ ID、旧完了結果、次の実行対象なしになることを再現した。

   根拠：[ADR-0013:37](C:/Works/info-hive-dev/docs/adr/0013-rag-records-pdfs-by-absolute-path-and-hash.md:37)、[rag_jobs.py:63](C:/Works/info-hive-dev/info-hive-rag/scripts/rag_jobs.py:63)。

3. **重大：複数の場所にある同一文書の一方を更新すると、旧本文の出典が新版を指す。**

   次の順で登録する。

   - `A.pdf` を内容 H で登録する。
   - `B.pdf` も内容 H で登録する。
   - `B.pdf` だけ内容 G に変えて登録する。

   現行処理は、同じ H の再登録でも `documents` の代表パスを B に上書きする。その後 B が G になっても、H は A に残っているので削除されない。しかし H の代表パスは B のままである。検索は `locations` ではなく `documents` のパスを返すため、**H の本文と、G が入った B のパス**を組み合わせる。`sha256=H` を追加しても不一致が露出するだけで、出典は正しくならない。

   現行コードの SQL をメモリ上で実行し、この状態を再現した。ADR は代表パスの選択・更新について決めていない。

   根拠：[ADR-0013:36](C:/Works/info-hive-dev/docs/adr/0013-rag-records-pdfs-by-absolute-path-and-hash.md:36)、[rag_index.py:266](C:/Works/info-hive-dev/info-hive-rag/scripts/rag_index.py:266)、[rag_index.py:280](C:/Works/info-hive-dev/info-hive-rag/scripts/rag_index.py:280)、[rag_index.py:345](C:/Works/info-hive-dev/info-hive-rag/scripts/rag_index.py:345)。

4. **重大：旧台帳の検出だけでは旧ジョブを止められず、停止後の復旧条件も閉じていない。**

   `documents.root` の検出対象は wiki ごとの `catalog.sqlite` だが、ワーカーは共通の `jobs.sqlite` から先にジョブを選ぶ。旧ジョブの `source` は既に絶対パスであり、旧設定を無視するだけでは新規ジョブと区別できない。旧ジョブを受付後、台帳作成前に終了した場合は、検出対象の `catalog.sqlite` 自体がない。

   また、公開開始済みの旧ジョブを旧台帳エラーで失敗させた場合、現行処理では次の状態になる。

   - `failed` も `unfinished()` に含まれ、別の `data_dir` への設定変更を拒む。
   - `publication_started=1` のためキャンセルできない。
   - `retry_job` は同じ旧設定のジョブを再びキューに入れる。
   - `status` は索引の状態取得を先に行うため、旧台帳エラーで止まるとジョブ一覧まで返せない。

   旧ジョブの選択と設定変更を塞ぐ状態はメモリ上で再現した。ADR の「再開しない」は要件の記述にとどまり、識別条件、停止状態、削除対象の範囲が未規定である。完了済みの旧ジョブも残すなら、`job_status` が名前付き `raw` と `sha256` のない旧結果を返す扱いが残る。

   根拠：[ADR-0013:41](C:/Works/info-hive-dev/docs/adr/0013-rag-records-pdfs-by-absolute-path-and-hash.md:41)、[rag_worker.py:127](C:/Works/info-hive-dev/info-hive-rag/scripts/rag_worker.py:127)、[rag_jobs.py:95](C:/Works/info-hive-dev/info-hive-rag/scripts/rag_jobs.py:95)、[rag_jobs.py:183](C:/Works/info-hive-dev/info-hive-rag/scripts/rag_jobs.py:183)、[rag_server.py:170](C:/Works/info-hive-dev/info-hive-rag/scripts/rag_server.py:170)。

5. **重大：パスの事前確認と、実際に読んだファイルの対応が保証されない。**

   通常ファイル A の解決・除外判定・先頭確認の後、`read_bytes()` の前に、別プロセスが A を別のファイル B へのリンクに差し替える反例がある。B のサイズと更新時刻が A と同じなら、現行の前後比較は通る。B を禁止領域内の PDF にすることもできる。

   現行処理は確認、読み込み、前後の `stat` でパスを別々に開き直し、ファイルの同一性を比較していない。計算される SHA-256 は B の内容を識別するが、「確認した A を読んだ」という保証にはならない。ADR には、先頭確認と抽出が同じバイト列を対象にする条件もない。

   **再現条件の仮定**：別プロセスに対象パスを差し替える権限がある。実ファイルの競合実行は未実施で、コード上の実行順序から確認した反例である。

   根拠：[ADR-0013:33](C:/Works/info-hive-dev/docs/adr/0013-rag-records-pdfs-by-absolute-path-and-hash.md:33)、[rag_index.py:191](C:/Works/info-hive-dev/info-hive-rag/scripts/rag_index.py:191)、[rag_index.py:199](C:/Works/info-hive-dev/info-hive-rag/scripts/rag_index.py:199)、[rag_worker.py:150](C:/Works/info-hive-dev/info-hive-rag/scripts/rag_worker.py:150)。

6. **重大：PDF の形式確認は、「利用者が選んだ読む範囲」の代わりにならない。**

   利用者が公開資料 A の取り込みを依頼していても、モデルが別の機密 PDF B の絶対パスを渡せば、B は列挙された確認をすべて通る。抽出結果は呼び出し元へ返る。ADR の「利用者が頼んだ取り込みの結果」という説明は、パスが利用者の指定と一致することを別の層が保証する、という未記載の前提に依存する。

   UNC も絶対パスなので、`\\server\share\book.pdf` は対象になる。パス解決やファイル確認にはネットワークアクセスが先行しうるため、PDF の形式確認ではその接続自体を制限できない。認証情報への影響は環境の SMB 設定次第であり、この環境では検証していない。

   **評価上の仮定**：モデルが渡すパスを、利用者による個別の読み取り許可と同一視しない。ホスト側で一致を保証する仕様は、読んだリポジトリからは確かめられなかった。

   根拠：[ADR-0013:17](C:/Works/info-hive-dev/docs/adr/0013-rag-records-pdfs-by-absolute-path-and-hash.md:17)、[ADR-0013:48](C:/Works/info-hive-dev/docs/adr/0013-rag-records-pdfs-by-absolute-path-and-hash.md:48)、[rag_server.py:112](C:/Works/info-hive-dev/info-hive-rag/scripts/rag_server.py:112)。

7. **重大：Windows のパスを現行の記入例に直接入れると、wiki のパーサー間で値が食い違う。**

   現行の `raw: "<result.raw>"` に `C:\books\new.pdf` をそのまま入れると、YAML では `\b` と `\n` が制御文字になる。一方、wiki の軽量パーサーはそれらを戻さず、文字どおりのパスとして読む。`C:\docs\book.pdf` なら `\d` が不正なエスケープとなり、グラフ側は例外を捕まえて **frontmatter 全体を空にする**。通常の lint は引用符の有無を検査するだけなので、この書き方を通す。

   バックスラッシュのエスケープ規約は `wiki_text.py` に存在するが、対象の取り込み手順にも ADR にも、返却された絶対パスを埋め込むときの説明がない。軽量パーサーと引用符検査の結果は実行確認し、YAML 側の意味は[YAML 仕様](https://yaml.org/spec/1.2.2/)と照合した。

   根拠：[ingest-workflow.md:25](C:/Works/info-hive-dev/info-hive-wiki/skills/info-hive/references/ingest-workflow.md:25)、[wiki_text.py:178](C:/Works/info-hive-dev/info-hive-wiki/skills/info-hive/scripts/wiki_text.py:178)、[wiki_graph_extract.py:160](C:/Works/info-hive-dev/info-hive-wiki/skills/info-hive/scripts/wiki_graph_extract.py:160)。

8. **重大：書き込み範囲の宣言が、維持するとした版更新処理と矛盾する。**

   ADR は「`data_dir` とキャッシュの外に書かない」とするが、現行の `_mark_reviews()` は wiki の Markdown を読み、一時ファイルを書き、元ページを置き換える。wiki が `C:\notes`、`data_dir` が別ドライブなら、PDF 更新時に宣言の外へ書き込む。

   これは既存処理であり、ADR が「今までどおり」として残す要再確認処理そのものである。**PDF 原本を書き換える経路を確認したという指摘ではない**。書き込み範囲の宣言と、実際に維持する機能の矛盾である。

   根拠：[ADR-0013:34](C:/Works/info-hive-dev/docs/adr/0013-rag-records-pdfs-by-absolute-path-and-hash.md:34)、[ADR-0013:37](C:/Works/info-hive-dev/docs/adr/0013-rag-records-pdfs-by-absolute-path-and-hash.md:37)、[rag_index.py:150](C:/Works/info-hive-dev/info-hive-rag/scripts/rag_index.py:150)。

## 崩れる前提

| 暗黙の前提 | 崩れる条件 |
| --- | --- |
| 正規化したパス文字列はファイルの同一性を表す | NFC/NFD の別ファイル、大文字小文字を区別する Windows ディレクトリ、ハードリンクや別マウント経由の参照 |
| OS ごとに大文字小文字の規則が決まる | Windows のディレクトリ単位の設定や、macOS のボリューム形式によって変わる。APFS には大小文字を区別する形式もある。[Apple の説明](https://developer.apple.com/documentation/technologyoverviews/files-and-directories) |
| サイズと更新時刻が同じなら内容も同じ | 更新時刻を保持する復元・同期・差し替え |
| 文書ごとの代表パスは、その文書の内容を保持する | 複数の場所を登録した後、代表パス側だけ更新する |
| 旧台帳を開けば旧ジョブも検出できる | ジョブ受付後、台帳作成前に終了する |
| PDF の形式確認は短いローカル読み取りで済む | UNC、ネットワークドライブ、OneDrive のオンライン専用ファイル |
| ハッシュを保存すれば既存のグラフも内容の同一性を使う | 現行グラフは `raw_sha256` を参照しない |

## 見落としと軽微な問題

- **軽微：OneDrive では、先頭5バイトの確認が受付を長時間止めうる。** オンライン専用ファイルを開くとダウンロードが発生する。[Microsoft の説明](https://support.microsoft.com/en-us/windows/experience/automatic-file-download-notifications-in-windows)。現行 `register_pdf` は `_lock` 内で登録するため、確認をそこへ追加すると、永続ジョブとして受け付ける前に待つ経路になる。ADR には、この段階の待機・中断・失敗の扱いがない。

- **軽微：グラフは絶対パスを受け付けるが、内容の同一性や版を表さない。** `summarizes_raw` の対象は `raw:<パス>` の文字列で、ハッシュは使わない。同じ PDF を別 PC で登録すると別の対象になり、同じパスに別内容を置くと同じ対象になる。また `raw` はグラフ解析時に NFC 化される。[wiki_graph_extract.py:116](C:/Works/info-hive-dev/info-hive-wiki/skills/info-hive/scripts/wiki_graph_extract.py:116)、[wiki_graph_extract.py:427](C:/Works/info-hive-dev/info-hive-wiki/skills/info-hive/scripts/wiki_graph_extract.py:427)。

- **軽微：影響範囲に `rag_worker.py` と `commands/status.md` が明記されていない。** 前者は旧設定の写しから実行環境を復元し、後者は未完了ジョブの自動再開と `retry_job` を案内する。互換打ち切りの例外が直接関係する。[ADR-0013:63](C:/Works/info-hive-dev/docs/adr/0013-rag-records-pdfs-by-absolute-path-and-hash.md:63)、[status.md:7](C:/Works/info-hive-dev/info-hive-rag/commands/status.md:7)。

- **軽微：試験の変更が「`reference_roots` を外す」だけでは、新しい契約を検査できない。** 指定された `test_jobs.py` には、パス正規化の衝突、旧台帳・旧ジョブの拒否、同一サイズ・時刻での変更、絶対パスと `sha256` の返却、YAML への保存と読み戻しの試験がない。既存試験が通っても、本レビューの反例は残る。

## 検証した事実

- **一致**：現行文書の `doc_id` は、読み込んだバイト列全体の SHA-256。ハッシュと抽出には同じ `data` を渡している。
- **一致**：旧 `documents` には `root` 列がある。ただし `jobs.sqlite` は独立しており、`ingest_jobs.config` に旧設定の写しを保持する。
- **食い違い**：「今までどおりの版更新」は、同一サイズ・更新時刻の変更を受付段階で見逃す。実際の `Jobs` メソッドで再現した。
- **食い違い**：「外に書かない」は `_mark_reviews()` の書き込みと両立しない。
- **一部一致**：グラフは `raw` を文字列としてエッジにできる。しかしハッシュによる統合や版の区別はしない。
- **確認できず**：モデルが渡すパスと利用者の指定の一致を、ホストが保証するかどうか。
- 実行検証は文字列演算、メモリ上の SQLite、ファイル書き込みを行わない呼び出しに限定した。実 PDF を使う全試験、macOS/Linux 実機、リンク差し替えの競合実行は未実施。リポジトリは変更していない。

## 崩せなかった点

- **ドライブ文字の大小と通常の 8.3 名だけの反例**：この環境では `C:\Windows` と `c:\WINDOWS`、`C:\Program Files` と `C:\PROGRA~1` は、それぞれ `Path.resolve()` で同じパスになった。対象製品指定の Python 3.12 ではなく、検証環境の Python 3.14.6 での結果である。
- **固定されたリンク先への単純なシンボリックリンク・ジャンクション**：解決後のパスで禁止領域を比較するという方針に対し、差し替えや別名参照を伴わない逸脱の反例は示せなかった。
- **PDF 原本への直接書き込み**：読み込み後はメモリ上の PDF を処理し、OCR の画像と抽出結果は派生領域へ書く。通常の入力経路で PDF 原本を直接上書きする処理は確認できなかった。
- **SHA-256 による同一内容の識別そのもの**：実用上の衝突を根拠に崩すことはできなかった。指摘は、その前後のパス・ジョブ・出典の対応にある。

使用した MCP サーバー: なし  
使用した Agent Skills: なし
