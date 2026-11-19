# Windows の Box Drive 上での info-hive wiki の動作

2026-11-19 調査

**1 台の Windows PC で使う場合、この端末の Box Drive 2.56.271（Cloud Files 方式）と info-hive wiki v0.38.1 では基本機能が動いた。** 初期化、日本語の Markdown 原本の保存、記事の再編集、CLI と MCP の検索、lint、グラフの生成・照会、browse を確認した。**複数端末で同じ wiki を編集する構成は推奨しない。** Box はファイル単位で競合を処理するため、取り込みで一緒に更新する記事、索引、ログ、原本の整合性を wiki 全体で保証できない。 [Box のファイル競合](https://support.box.com/hc/en-us/articles/360044193873-File-Version-Conflicts) [公開版の取り込み手順](https://github.com/to884/info-hive-wiki/blob/v0.38.1/skills/info-hive/references/ingest-workflow.md)

## この PC での試験

Windows 11 Enterprise（ビルド 26300）、Box Drive 2.56.271.0、Python 3.14.6、公開版 v0.38.1（コミット `b8596d1`）のインストール済みスクリプトを使用した。Box 配下と非同期のローカル一時フォルダーに試験専用の `wiki/` と `raw/` を新規作成し、架空の日本語 Markdown 1 ページと原本を載せた。展開中の別機能の影響を避けるため、CLI の確認には作業ツリー内のスクリプトを使わず、実際に導入済みの wiki MCP も呼んだ。 [実測記録](../../raw/box-driveでのwiki互換性-2026-11-19.json)

| 機能 | 試験結果 |
|---|---|
| 初期化 | 標準の `init_wiki.py` が Box とローカルの両方で終了コード 0。初期化時の検索キャッシュ構築も `ready`。 |
| 原本と記事の保存 | `wiki_raw_ingest.py save` で原本を保存できた。記事とログはファイルシステム検査付きの `WriteGuard` で置き換え、更新した本文を検索で確認した。 |
| 検索 | CLI の BM25 とハイブリッド、MCP のハイブリッドが試験ページを返した。MCP の検索索引が `%LOCALAPPDATA%/info-hive/index/` 下にあることも確認した。 |
| lint とグラフ | lint は終了コード 0。グラフを生成し、SQLite の `quick_check` が `ok`、MCP で試験ノードを照会できた。 |
| グラフの再生成 | 読み取り接続を開いたまま再生成すると、Box とローカルの両方で `WinError 5`。接続を明示的に閉じると、両方で連続 2 回成功した。 |
| browse | 静的出力は Box とローカルで同じ生成 ID、1 記事、警告 0。ローカル閲覧サーバーは HTTP 200 で、再編集した文を返した。 |
| オンライン専用の状態からの読み出し | 試験記事と原本をオンライン専用にし、Windows の `Offline` と `RecallOnDataAccess` 属性を確認した。MCP 検索が再編集後の文を返し、原本の再取得後の SHA-256 は保存前と一致した。読み出し後は両方から `Offline` 属性が消えた。 |
| オフライン用の固定 | フォルダー、試験記事、原本に `Pinned` 属性を確認。ネットワーク接続を維持した状態で、固定後の lint、原本保存、グラフ再生成も成功した。 |

Box の同期ルートと試験データは Windows の管理用ツールから再解析点として見えた。通常の Python プロセスの `os.lstat()` では再解析点属性が見えず、wiki の書き込みガードを通った。Microsoft は Cloud Files の再解析点を通常のアプリから隠すと説明している。Box の旧方式にはローカル AI エージェントのアクセスに既知の制限があり、今回の結果はこの端末の新方式に適用する。 [Microsoft の互換性仕様](https://learn.microsoft.com/en-us/windows/win32/cfapi/build-a-cloud-file-sync-engine#compatibility-with-applications-that-use-reparse-points) [Box の Windows 固有の制限](https://support.box.com/hc/en-us/articles/360043695854-Windows-Specific-Limitations-for-Box-Drive) [Box Drive v2.56](https://support.box.com/hc/en-us/articles/56389534028947-Box-Drive-v2-56-Release-Notes)

## 複数端末で共有するときの制約

- **変更が見える順番。** 公開版の ingest は記事、索引、ログ、原本を順に更新する。Box は各ファイルの保存とアップロードに応じて別端末に変更を見せるので、閲覧専用の端末でも取り込み途中の組み合わせが見えるおそれがある。複数の書き手は、別々の記事を編集しても共通の `index.md` と `log.md` を更新する。Box が競合コピーを作っても、wiki は内容を自動統合しない。 [Box Drive FAQ](https://support.box.com/hc/en-us/articles/29475996910867-Box-Drive-Frequently-Asked-Questions) [取り込み手順](https://github.com/to884/info-hive-wiki/blob/v0.38.1/skills/info-hive/references/ingest-workflow.md)
- **隠しファイルとロック。** Box の資料では、先頭にドットが付く隠しファイルや一時ファイルは同期対象外。たとえば `wiki/.page-template.md` を含む完全な複製を、フォルダーの同期だけに任せられない。`wiki/graph/.extract.lock` で確保する OS の排他は端末間の編集を調整しない。 [Box の同期対象外ファイル](https://support.box.com/hc/en-us/articles/360044195433-File-Types-Ignored-or-Blocked-by-Box-Sync-and-Box-Drive) [グラフの排他処理](https://github.com/to884/info-hive-wiki/blob/v0.38.1/skills/info-hive/scripts/wiki_graph_common.py#L169)
- **検索の SQLite。** MCP の索引は既定で端末ローカルにあり WAL を使う。`INFO_HIVE_DATA_DIR` も Box 外に置く。標準の初期化と CLI のハイブリッド検索は `wiki/.wiki-cache/embeddings.sqlite` を書き込む。CLI で wiki に検索キャッシュを書かずに語彙検索するには `--no-embed` を付け、`--cache` を省く。稼働中の SQLite を外部でコピーしたり、DB 本体とジャーナルを別時点のファイルから復元したりすると、更新が失われたり破損したりし得る。 [MCP のデータディレクトリ](https://github.com/to884/info-hive-wiki/blob/v0.38.1/skills/info-hive/scripts/wiki_mcp_common.py#L56-L71) [CLI 検索](https://github.com/to884/info-hive-wiki/blob/v0.38.1/skills/info-hive/scripts/wiki_search.py#L637-L667) [SQLite の破損事例](https://sqlite.org/howtocorrupt.html#backup_or_restore_while_a_transaction_is_active)
- **グラフの SQLite。** グラフ抽出は一時 DB を作り、接続を閉じてから既定の `wiki/graph/graph.sqlite` を置き換える。Markdown、JSONL、DB が別々に同期するため、別端末で同じ更新時点の内容がそろう保証は確認できなかった。 [グラフの出力処理](https://github.com/to884/info-hive-wiki/blob/v0.38.1/skills/info-hive/scripts/wiki_graph_extract.py#L922-L1008)
- **raw の参照。** 一緒に持ち運ぶ原本は `wiki/` と同じ親の `raw/` に置くと、`raw/...` の相対参照を保てる。端末固有の絶対パスで記録した外部原本は、別端末で同じ場所を参照できるか確認が必要。 [原本参照の生成](https://github.com/to884/info-hive-wiki/blob/v0.38.1/skills/info-hive/scripts/wiki_raw_ingest.py#L47-L52)

## 用途に応じた置き場所

| 用途 | 判定と配置 |
|---|---|
| この PC で個人用に編集 | Box に置いて試せる。親フォルダーごと「このデバイス上で常に保持」にすると、取り込みや全件走査でファイルを読むたびにダウンロードする必要が減る。書き込み端末を 1 台に固定し、検索の MCP データは既定のローカル領域を使う。 |
| 他の端末やチームに閲覧用で共有 | ローカル wiki を編集元にし、更新後の静的 HTML、または必要なファイルを含む確定版のアーカイブを Box に置く。共有先で検索が必要なら、アーカイブを端末ローカルに展開し、索引やグラフを作り直せる。 |
| 複数端末から編集 | 同期フォルダーを共通の書き込み先にする構成は推奨しない。Box のファイルロックやオフライン用の固定では、wiki 全体の更新を調整できない。 |

オフライン固定は Box のダウンロード権限がある端末ごとに設定する。 [Box のオフライン利用](https://support.box.com/hc/en-us/articles/360043697574-Making-Content-Available-Offline)

## 残っている検証

2 台目への同期と競合、Box Web から見える実ファイル一覧、ネットワーク切断中の操作と再接続後の反映、規模の大きな wiki、Web や会話の取り込み全体、rag プラグインのジョブは今回の試験範囲外。Box の Web 上の有無を判定するために、Windows のローカル同期ステータスだけを根拠にすることはできない。旧方式や別の組織の Box 設定では、その環境で作成から再編集までを試す必要がある。 [Box Drive の一般的な制限](https://support.box.com/hc/en-us/articles/360043696454-General-Limitations-When-Using-Box-Drive)
