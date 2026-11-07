## 判定

**却下。確信度：高。** 初回の8件は一部解消されたが、別名パスの版管理と、検証済みパスと実際の読み取り先の結び付けには反例が残る。さらに、旧内容の再取り込みが索引を欠落させる経路と、失敗ジョブが設定変更を永久に塞ぐ経路を確認した。

確認時の作業ツリーには、すでに `jobs-v2.sqlite`、`locations` からの出典選択などの変更が存在した。以下は ADR と、その時点のコードを対象とする。未実装であること自体は欠陥に数えていない。

## 致命的・重大な欠陥

1. **重大：同じファイルの別名は「場所の行が増えるだけ」では済まず、旧本文の出典を新版へ向ける。**

   A と B が同じファイルのハードリンクであると仮定する。

   1. A と B を内容 H で登録する。
   2. B を内容 G で上書きする。ファイル自体への変更なので、A から読める内容も G になる。
   3. B を再登録する。

   更新されるのは B の `locations` 行だけで、A→H が残る。A は存在するため削除されず、H の文書も残る。H の検索結果は旧本文と A を組み合わせるが、A にあるのは G である。ハードリンクを通した変更が他方にも見えることは [Microsoft の仕様](https://learn.microsoft.com/en-us/windows/win32/fileio/hard-links-and-junctions)と一致する。

   `_location()` はサイズ・時刻が一致する場所を見つけられなくても、最後に古いパスを返す。実際のメソッドとメモリ上の SQLite で、A の更新時刻が記録と違っても H の出典として A を返すことを確認した。**初回指摘3は独立したコピーでは塞がったが、別名では残る。**

   根拠：[ADR の別名に関する断定](/C:/Works/info-hive-dev/docs/adr/0013-rag-records-pdfs-by-absolute-path-and-hash.md:46)、[同じ断定を置く理由](/C:/Works/info-hive-dev/docs/adr/0013-rag-records-pdfs-by-absolute-path-and-hash.md:74)、[出典選択とフォールバック](/C:/Works/info-hive-dev/info-hive-rag/scripts/rag_index.py:156)、[場所の更新・削除条件](/C:/Works/info-hive-dev/info-hive-rag/scripts/rag_index.py:300)。

2. **重大：内容を H→G→H と戻すと、再取り込みが成功扱いなのに H の索引行がなくなる。**

   反例は、単一パスの PDF を H で取り込み、G に変更して取り込み、再び H に戻して取り込む操作である。

   G の公開時、H を参照する場所がなくなると、H の `documents`、索引行、抽出キャッシュを削除する。一方、H の世代に対応する内部 `jobs` 行と `completed` 件数は残る。

   H を戻したとき、世代 ID は以前と同じになる。`INSERT OR IGNORE` は古い内部ジョブを残し、埋め込みループは以前の完了件数から始まる。全件処理済みなら何も投入せず、H を `documents` に登録して `indexed` を返す。

   削除後に残る内部ジョブをメモリ上に作り、実際の `Engine.ingest_pdf()` を代替索引で実行した結果は、**`indexed`、報告チャンク数1、索引への投入0件**だった。完了ジョブから新しい受付ジョブを作るだけでは、内部チェックポイントの再利用は解消されない。

   根拠：[再受付の決定](/C:/Works/info-hive-dev/docs/adr/0013-rag-records-pdfs-by-absolute-path-and-hash.md:50)、[世代 ID](/C:/Works/info-hive-dev/info-hive-rag/scripts/rag_index.py:239)、[古い内部ジョブの再利用](/C:/Works/info-hive-dev/info-hive-rag/scripts/rag_index.py:250)、[完了件数からの再開](/C:/Works/info-hive-dev/info-hive-rag/scripts/rag_index.py:262)、[旧索引・キャッシュの削除](/C:/Works/info-hive-dev/info-hive-rag/scripts/rag_index.py:308)。

3. **重大：ローカルパスから UNC へのリンクをたどると、拒否したはずのネットワーク参照が成立する。**

   仮定は、Windows でローカルからリモートへのシンボリックリンクの評価が許されていること。

   `C:\Downloads\book.pdf` が `\\unknown-server\share\book.pdf` へのリンクなら、入力文字列は UNC の拒否判定を通る。その後の `resolve(strict=True)` と `lstat()` はリンク先を調べる。解決後のパスについて UNC の再判定もないため、通常ファイルなら受け付ける。

   Microsoft は、ローカルパス中のリンクを UNC に置き換える動作を[明記している](https://learn.microsoft.com/en-us/windows/win32/fileio/creating-symbolic-links)。したがって、解決後に拒否するだけでも「接続前に防ぐ」という目的には遅い。

   実際の `Config.pdf_path()` に、解決結果と `lstat` のみを代替する検証では、ローカル入力から UNC パスが返った。実サーバーへの接続や認証情報の送信は試しておらず、認証の発生は環境次第である。

   根拠：[UNC 拒否の目的](/C:/Works/info-hive-dev/docs/adr/0013-rag-records-pdfs-by-absolute-path-and-hash.md:35)、[リンクをたどる決定](/C:/Works/info-hive-dev/docs/adr/0013-rag-records-pdfs-by-absolute-path-and-hash.md:36)、[入力文字列だけの判定と、その後の解決](/C:/Works/info-hive-dev/info-hive-rag/scripts/rag_config.py:135)。

4. **重大：`lstat` と `fstat` の比較は、禁止領域の確認後に親ディレクトリを差し替える反例を防がない。**

   仮定は、別プロセスが PDF の親ディレクトリを差し替えられること。

   1. `/allowed/book.pdf` を解決し、禁止領域外と判定する。
   2. `read_pdf()` の直前に `/allowed` を退避し、同じ名前を `data_dir` 内へのディレクトリリンクにする。
   3. `read_pdf()` が `/allowed/book.pdf` を `lstat` し、開く。

   `lstat` は最終要素のリンクをたどらなくても、親ディレクトリのリンクはたどる。このため `lstat` と `fstat` は両方とも禁止領域内の同じファイルを指し、比較を通過する。登録時に確認したファイルとのサイズ・時刻の一致すら、この差し替え位置では不要である。

   **比較が保証するのは、最後の `lstat` と開いたファイルの一致であり、禁止領域外と確認したファイルとの一致ではない。** 初回指摘5の「最終ファイルを確認後に差し替える」反例は塞がったが、親ディレクトリ側に穴が残る。実ファイルの競合実行は未実施で、コードの順序と代替した stat・ハンドルによる確認である。

   根拠：[確認の決定](/C:/Works/info-hive-dev/docs/adr/0013-rag-records-pdfs-by-absolute-path-and-hash.md:37)、[解決後の文字列による禁止領域判定](/C:/Works/info-hive-dev/info-hive-rag/scripts/rag_config.py:142)、[読み取り直前の新しい `lstat`](/C:/Works/info-hive-dev/info-hive-rag/scripts/rag_index.py:28)、[パス確認から読み取りまでの間隔](/C:/Works/info-hive-dev/info-hive-rag/scripts/rag_index.py:225)。

5. **重大：失敗後に新しいジョブを成功させても、古い失敗ジョブが設定変更を塞ぎ続ける。**

   次の状態に到達できる。

   1. PDF 更新ジョブが `begin_publication()` を通り、`publication_started=1` になる。
   2. `_mark_reviews()` で不正な YAML、または書き込み失敗が発生して `failed` になる。
   3. 原因を直し、PDF も更新して、新しい登録ジョブを成功させる。

   古い `failed` は新規ジョブの成功では閉じない。`unfinished()` はこれを未完了と判定するが、`cancel()` は `publication_started=1` のため拒否する。古いジョブを再試行しても、PDF のサイズ・時刻が変わっていればワーカーの事前確認で再び失敗する。

   結果として、処理すべき新版は取り込み済みなのに `configure()` が使えない。メモリ上の実際の `Jobs` メソッドで、**旧失敗＋新完了に対し `unfinished=True`、旧ジョブのキャンセル拒否**を確認した。旧データの隔離自体とは別の、新方式にも残る行き止まりである。

   根拠：[失敗後は新規ジョブとする決定](/C:/Works/info-hive-dev/docs/adr/0013-rag-records-pdfs-by-absolute-path-and-hash.md:50)、[公開開始後のレビュー処理](/C:/Works/info-hive-dev/info-hive-rag/scripts/rag_index.py:291)、[未完了の判定](/C:/Works/info-hive-dev/info-hive-rag/scripts/rag_jobs.py:106)、[キャンセル条件](/C:/Works/info-hive-dev/info-hive-rag/scripts/rag_jobs.py:194)、[登録後の変更による失敗](/C:/Works/info-hive-dev/info-hive-rag/scripts/rag_worker.py:151)、[設定変更の拒否](/C:/Works/info-hive-dev/info-hive-rag/scripts/rag_server.py:85)。

## 崩れる前提

| 前提 | 崩れる条件と結果 |
| --- | --- |
| 別名パスの害は行の増加だけ | ハードリンクや同じ実体への別経路。一方の更新で、他方の古い対応も誤りになる |
| `locations` の行が残れば旧内容も残る | 場所が削除済み、または別名経由で更新済み。行の存在だけで旧文書が残る |
| 世代 ID が同じならチェックポイントを再利用できる | その世代の索引行を削除した後に同じ内容を戻す |
| `lstat` と `fstat` が一致すれば境界確認も有効 | 境界確認後、最初の `lstat` より前に親ディレクトリを差し替える |
| UNC は入力の先頭で識別できる | ローカルパス中のリンクが UNC を指す |
| 新しい登録の成功で、失敗した登録は問題にならない | 過去の失敗行が `unfinished()` に残り、公開開始済みでキャンセルもできない |

**同意の説明は部分的にしか閉じていない。** 「選んだフォルダーに限定しない」という弱さは ADR に書かれた。しかし、ツールへの許可が、個々の PDF を利用者が選んだ証拠になるとは限らない。

例えば MCP ツールを allow で事前許可した状態で、利用者は A を依頼し、モデルが B を渡すケースである。ホストの許可を通る通常経路でも、人が B を確認せずに実行できる。allow が手動確認を省略することは [Claude Code の公式仕様](https://code.claude.com/docs/en/permissions)で確認した。

[ADR 38行](/C:/Works/info-hive-dev/docs/adr/0013-rag-records-pdfs-by-absolute-path-and-hash.md:38)と[見直す条件112行](/C:/Works/info-hive-dev/docs/adr/0013-rag-records-pdfs-by-absolute-path-and-hash.md:112)は、この「許可を通るが個別確認はない」ケースを明示していない。wiki の手順はモデルへの指示であり、入力と利用者の指定を照合する強制処理は、読んだコードにはない。参照ルート廃止の再議を求める指摘ではなく、受け入れる信頼前提の記述不足である。

## 見落としと軽微な問題

- **軽微：グラフ側では NFC/NFD の別パスが依然として同じ出典になる。**  
  `ガ.pdf` と `ガ.pdf` を台帳で区別しても、グラフの `normalize_refs()` は `raw` を NFC 化するため、`summarizes_raw` の対象が同じになる。実際の正規化関数で再現した。「別 PC では別ノード」という説明だけでは、この同一 PC 上の混同を表していない。また、ADR が予定する「手書きパーサーとグラフが同じ値を読む」試験は、NFD の入力では成立しない。根拠：[ADR の試験条件](/C:/Works/info-hive-dev/docs/adr/0013-rag-records-pdfs-by-absolute-path-and-hash.md:103)、[`raw` の NFC 化](/C:/Works/info-hive-dev/info-hive-wiki/skills/info-hive/scripts/wiki_graph_extract.py:125)、[出典エッジ](/C:/Works/info-hive-dev/info-hive-wiki/skills/info-hive/scripts/wiki_graph_extract.py:427)。

- **軽微：受付で中身を読まないことと、受付が待たないことは同じではない。**  
  `resolve(strict=True)` と `lstat` は同期処理で、`register_pdf()` のロック内から呼ばれる。許可するネットワークドライブが応答しない場合には、永続ジョブを返す前に待つ余地がある。OneDrive 実機での待機時間は**確かめられず**、「オンラインだけでも受付を待たせない」という断定までは検証できなかった。根拠：[ADR 36行](/C:/Works/info-hive-dev/docs/adr/0013-rag-records-pdfs-by-absolute-path-and-hash.md:36)、[同期したパス確認](/C:/Works/info-hive-dev/info-hive-rag/scripts/rag_config.py:142)、[受付のロック](/C:/Works/info-hive-dev/info-hive-rag/scripts/rag_server.py:115)。

## 検証した事実

初回8件との対応は次のとおり。

| 初回指摘 | 結果 |
| --- | --- |
| 1. NFC・`normcase` による場所キー衝突 | **一致・台帳では解消。** 正規化しない決定になった。グラフでは混同が残る |
| 2. 完了ジョブを再利用して変更を見逃す | **一致・完了後の再登録は解消。** 新規ジョブを作る。ただし旧内容復元時の内部チェックポイントに別の欠陥がある |
| 3. 同一内容のコピーの一方を更新すると出典が誤る | **部分解消。** 独立したコピーの A/B には対応するが、同一実体の別名では残る |
| 4. 旧台帳検出では旧ジョブを止められない | **一致・隔離で解消。** 新しい DB と作業領域を使う。新方式の失敗ジョブには別の行き止まりが残る |
| 5. 確認対象と読み取り対象が一致しない | **部分解消。** 開く直前の最終要素の差し替えには対応するが、親ディレクトリの差し替えは残る |
| 6. PDF 形式確認は利用者の同意にならない | **部分解消。** 境界を弱めることは明記されたが、ホストの許可と個別パスの同意の区別が不足する |
| 7. Windows パスの YAML 解釈が食い違う | **一致・通常の Windows パスに対する決定は解消。** `/` 区切りと引用規則が明記された |
| 8. 書き込み範囲と wiki 更新が矛盾する | **一致・解消。** wiki ページへの書き込みが明記された |

実行検証は、実際の関数を使ったメモリ上の SQLite、代替した stat・ハンドル・索引に限定した。ファイルは変更していない。実 PDF の全工程、実際のリンク差し替え競合、UNC 接続、OneDrive の動作は未検証。検証用 Python は 3.14.6 であり、製品指定の 3.12 とは異なる。

## 崩せなかった点

- **SHA-256 と抽出対象の一致。** 読み込んだ同じ `data` をハッシュと抽出に渡している。
- **独立したコピーに対する代表パス問題の解消。** A/H、B/H の後に B/G を登録すると、H の場所は A になる。
- **旧データの名前による隔離。** 読んだ新方式のジョブ・作業領域選択から、0.3.0 のジョブを再開する経路は示せなかった。
- **PDF 原本への直接書き込み。** 通常の処理経路で原本を上書きする箇所は確認できなかった。

使用した MCP サーバー: なし  
使用した Agent Skills: なし
