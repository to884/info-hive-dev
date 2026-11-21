# 利用者向け文書の段階 2 の確認記録（2026-11-20）

対象は Windows 11 の Claude デスクトップアプリの Code タブと Cowork。判定の基準は [段階 2 の確認表](usage-docs-stage2-checklist-2026-11-15.md) に置く。

## 旧 VM の引き継ぎ記録

2026-11-15 と 11-20 の記録はホストの `C:\stage2-records` にある。Windows 11 Enterprise 評価版 26H2（build 26300）、Claude Desktop 5.11492.5、wiki 0.19.4 と 0.39.0 を使った。

| 確認 | 観測 | 記録 |
| --- | --- | --- |
| 0〜1 | Git は素の環境になかった。`python` は Microsoft Store の実行エイリアスだった。やり直しでは Git 2.56.0 と uv 0.13.9 を導入し、`uv sync --help` に `UV_SYSTEM_CERTS` が出た。 | `00-versions.txt`、`01-git.txt`、`01-install-run2.txt` |
| 2 | 手元の記録には GUI からの導入時刻があり、続く計測で 0.39.0 のキャッシュを確認できる。設定画面の有無を示す記録は見つからなかった。 | `02-install-plugin-run2.txt`、`03-deps-run2.txt` |
| 3 | 0.19.4 は CPython 3.15 用の ONNX Runtime wheel がなく失敗した。0.39.0 の初回 `--ensure` は 67.2 秒で終了コード 1 だった。Visual C++ 再頒布可能パッケージを入れたあと 6.7 秒で終了コード 0 になった。この時点の uv キャッシュは 421.1 MiB、モデルキャッシュはどちらもなかった。 | `03-deps-error.txt`、`03-deps-run2.txt` |
| 4 | `/wiki:help` は `python` が Microsoft Store の実行エイリアスだったときに失敗した。Python 3.12.10 の導入後、`/wiki:overview` を含む 12 本が出た。 | `04-hekp-run2.txt`、`04-help-run3.txt`、`05-python-install.txt` |
| 5 | W1 と W2 を 1 回観測した。W2 で使われた原本の拡張子は `.txt` だった。2 回目は計測が残っている。3 回の共通の目印はまだ判定できない。 | `05-run1/`、`05-run2/sizes.txt` |

### 旧 VM の確認 5 の 1 回目

- 索引とログに「味噌」と「醤油」があり、`wiki/sources/` に両方のページがあった。味噌の回答には `[[味噌]]`、`[[麹]]` と `**確信度（confidence）: 高**` が付いた。回答では索引を読んだと説明している。`05-run1/files-w2.txt`、`05-run1/querytxt`
- browse の出力は `http://127.0.0.1:` で始まる URL と `scope: "project"` を含んだ。`05-run1/browse.txt`
- 醤油の取り込みは途中で「麹」の変更だけ適用し、一時的に `[[醤油]]` のリンク先がない状態になった。その後、要約、索引、ログの変更も適用した。lint の応答は `tags` が空の 3 ページと `raw_sha256` がない 2 ページを挙げた。`05-run1/notes.txt`、`05-run1/lint.txt`
- e5 のキャッシュは 240.7 MiB で、ruri のキャッシュはなかった。`"status": "ready"` の生の JSON、`wiki:wiki-reader` の呼び出し、ruri の取得は、この回の記録では確認できなかった。`05-run1/sizes.txt`、`05-run1/querytxt`

wiki 0.39.1 の変更は、Visual C++ ランタイムがない Windows で、DLL 読み込みに失敗したときの診断を足すもの。`v0.39.0..v0.39.1` に `/wiki:help`、初期化、取り込み、browse の定義の変更はない。確認 3 の案内に関わる差分である。根拠は `info-hive-wiki` の `v0.39.1:CHANGELOG.md` と、同じタグ間の Git 差分。

## 新しい VM での再検証

旧 VM の試行は上の記録に保存し、再検証には新しい Hyper-V VM `info-hive-stage2-autotest` を使う。新しい試行の記録は `C:\stage2-records\autotest` に書く。VM の設定値は検証環境の値である。

Windows 11 Enterprise 評価版 26H2（build `26300.9457`）を、新しい VHDX に Windows Setup の答えファイルで入れた。Secure Boot、vTPM、入れ子の仮想化を有効にし、専用のローカルユーザーを作った。Claude Desktop は Anthropic 署名の MSIX を PowerShell Direct 経由で登録した。パッケージの版は `5.11492.5.0`。インストール後、セットアップに使った DVD を外し、一時の答えファイル ISO を削除した。入れ子の仮想化はホストの `Get-VMProcessor` で `ExposeVirtualizationExtensions: true` を確認した。

### 初期環境とチェックポイントの時系列

| 日時（JST） | 操作と環境 |
| --- | --- |
| 11-20 23:25〜23:34 | チェックポイント作成前の Windows で未導入の状態を調べた。23:27 の隔離診断は Visual C++ ランタイムがなく失敗した。23:34 に導入し、同じ隔離診断は終了コード 0 になった。 |
| 11-20 23:39 | Claude のサインイン後に補助チェックポイント `S0-claude-signed-in` を作った。Visual C++ ランタイムを導入済み。23:40 以降に通常の Git と uv を、23:43 に通常の Python 3.12.10 を導入した。 |
| 11-20 23:54〜23:57 | GUI で入った wiki 0.39.1 に対し、Visual C++ ランタイム導入済みの状態で `--ensure` が終了コード 0 になった。23:57 に `S1-wiki-0.39.1` を作った。Git、uv、Python を導入済みで、通常の場所に e5 と ruri のキャッシュはなかった。 |
| 11-21 06:18 | `S1` 復元後に Claude Desktop が `6.6395.0.0` へ更新された状態で `S1b-wiki-0.39.1` を作った。確認 5 の開始点とし、2 回目の復元後に Git、uv、Python と Visual C++ の DLL 3 本も照合した。 |

隔離診断の uv とプラグインは専用フォルダーに置いた。一般の導入を行った時刻と、チェックポイントを取った時刻は記録で区別する。以下の表は確認番号順に記す。

| 確認 | 新しい VM の観測 | 記録 |
| --- | --- | --- |
| 0 | Windows がデスクトップまで起動し、Claude Desktop を対話セッションで起動した。利用者が Claude にサインインしたあと、`S0-claude-signed-in` を作った。この時点で Visual C++ ランタイムを導入済みだった。 | `autotest/00-baseline.json`、Hyper-V のチェックポイント一覧 |
| 1 | `S0` を作る前の Windows の対話セッションでは、Git と uv が見つからなかった。`python` は `Microsoft\WindowsApps\python.exe` に解決され、`--version` は Microsoft Store の案内と終了コード `9009` を返した。`.ssh` ディレクトリと Visual C++ ランタイムの DLL 3 本もなかった。 | `autotest/01-os-baseline.txt` |
| 1-2 | Git `2.56.0.windows.4` と uv `0.13.9` を入れた。最初の uv 取得は `astral.sh` の名前解決に失敗し、再試行で通った。新しい PowerShell プロセスで両方の版を表示し、uv のヘルプに `UV_SYSTEM_CERTS` が含まれることを確かめた。 | `autotest/01-prerequisites.txt`、`autotest/01-prerequisites-run2.txt`、`autotest/01-prerequisites-verify.txt` |
| 2 | Code タブの「カスタマイズ → プラグイン → 追加 → マーケットプレイスを追加」から `to884/info-hive-marketplace` を同期し、ディレクトリの Code 用 Wiki を追加した。ローカル MCP の警告が出たので「続ける」を選び、「ローカルにインストール済み」を確認した。個別の `userConfig` 画面は見なかった。`.ssh` と `CLAUDE_CODE_PLUGIN_PREFER_HTTPS` のユーザー設定はなかった。Claude のリポジトリ候補が表示されたため、クラウド側の GitHub 連携の有無や使用は判定できない。 | `autotest/02-before-marketplace.txt`、`autotest/02-install-plugin.txt`、`autotest/02-*.jpg` |
| 3 | GUI でユーザースコープに入った wiki は `0.39.1`。Visual C++ ランタイム導入後にその配布物の `--ensure` を初めて実行し、終了コード `0`、32.78 秒だった。uv キャッシュは 441,267,870 バイトで e5 と ruri のキャッシュはまだなかった。Claude Desktop をトレイから終了し、同条件を確認して `S1-wiki-0.39.1` を作った。 | `autotest/03-deps-gui.txt`、`autotest/03-s1-checkpoint.json` |
| 3 の補足 | 検証専用フォルダーに uv 0.13.9 と wiki v0.39.1 のタグの内容を置いた。`--ensure` は 34.41 秒で終了コード 1 を返した。例外と `launch.log` に、Visual C++ 再頒布可能パッケージが必要であることと `winget install --id Microsoft.VCRedist.2015+.x64 -e --source winget` が出た。 | `autotest/03-isolated-v0.39.1.txt` |
| 3 の再試行 | 同じ VM の対話セッションで案内された Visual C++ ランタイムを導入した。winget は終了コード 0、DLL 3 本の版は `14.52.37029.0`。同じ専用フォルダーの `--ensure` を再実行すると 6.78 秒で終了コード 0、`started_now` は `True` だった。 | `autotest/03-install-vc-runtime.txt`、`autotest/03-isolated-v0.39.1-after-runtime.txt` |
| 4 の補足 | winget で Python 3.12.10 を入れた。新しい対話セッションの PowerShell プロセスから `python.exe` で v0.39.1 のヘルプスクリプトを実行し、`/wiki:overview` を含む 12 本が出た。 | `autotest/04-install-python.txt`、`autotest/04-python-help.txt` |
| 4 | 再起動した Claude Desktop の Code タブで、空の検証フォルダーから `/wiki:help` を送った。展開した「Showed wiki command list」のツール呼び出しに `python .../wiki_help.py` とその出力が表示され、出力と返答の両方に `/wiki:overview` を含む 12 本があった。 | `autotest/04-help-code.json`、`autotest/04-help-code-tool.jpg` |
| 6 の補足 | MCP の stdio クライアントは 7 ツールを列挙し、試験用 wiki の「味噌」に対して `sources/味噌.md` を返した。2 回目の開始前に ruri の `verified.json` があり、同モデルのディレクトリは 535,699,476 バイトだった。初回の取得時間は計測できなかった。 | `autotest/06-isolated-mcp.txt`、`autotest/06-isolated-mcp-run2.txt` |

PowerShell Direct の非対話セッションでは、`Get-Command python.exe` は結果を返さなかった。同じユーザーがログオンした対話セッションでは、同じ Windows の Python 実行エイリアスが見つかった。Python の確認には、PowerShell Direct で通常のコマンドを直接実行した結果を使わず、ユーザーがログオンしたセッションで実行した結果を使う。

GUI の操作、ツール呼び出しの表示、ブラウザペインは Code タブで観測してから判定する。コマンドラインによる起動診断の出力は、使った版と実行環境を添えて各確認の補足とする。

Claude のサインイン直後は画面操作ツールが `Transport closed` を返した。再接続後に、同じ VM の Code タブで確認 2 を続けた。

確認 0 の Windows Update 実行、確認 1 の導入前の Code タブでの `git --version`、確認 2 の `ssh -T git@github.com` の出力は記録がない。ホストから起動したインストールは UAC の画面を記録していない。導入からヘルプの表示までは `5.11492.5.0` で観測した。`6.6395.0.0` は後日、導入済みの状態からマーケットプレイスの追加画面とディレクトリを開いて表記を照合した。画面の記録は [HTML 試作の検証](usage-docs-stage3-prototype-2026-11-21.md#html-の導線を確認した結果)にある。

### 確認 5 のチュートリアル 3 回

確認 5 の 1 回目に `S1-wiki-0.39.1` を復元し、Claude Desktop `5.11492.5.0`、wiki `0.39.1`、uv キャッシュ 441,267,870 バイトと、e5・ruri のキャッシュがないことを確認した。復元すると VMConnect の対話セッションが切断され、Windows のロック画面が出た。練習用フォルダーは空のまま、`/wiki:init` の前で中断した。記録は `autotest/05-run1-before.json`。

2026-11-21 の再開時には Claude Desktop が `6.6395.0.0` になっていた。wiki `0.39.1` と uv キャッシュ 441,267,870 バイトは同じで、練習用フォルダーは空、e5・ruri のキャッシュはなかった。Claude Desktop を終了し、この条件で `S1b-wiki-0.39.1` を保存した。確認 5 の各回は `S1b` から始めて版を照合する。記録は `autotest/05-s1b-checkpoint.json`。

確認 5 の 1 回目の W1 は Code タブで完了した。初期化のツール出力に `"status": "ready"` があり、`CLAUDE.md` を標準版で新規作成した。06:18 の開始条件では e5 キャッシュがなく、初期化後の 06:21:37 の記録では 252,425,348 バイトだった。ダウンロード単体の時間は計測していない。確認表の `raw/味噌.md` を使い、`wiki/sources/味噌.md`、麹のページ、索引の味噌の項目、`## [2026-11-21] ingest | 味噌` の 1 行を確認した。質問の回答には `[[味噌]]`、`[[麹]]` と `**確信度（confidence）: 高**` が付いた。保存したツール呼び出しでは索引とページを読んでおり、MCP の `query` と `wiki:wiki-reader` の呼び出しは見つからなかった。記録は `autotest/05-run1-init.json`、`autotest/05-run1-w1.json`、`autotest/05-run1-w1-verdict.json`、`autotest/05-run1-w1-query.jpg`。

同じセッションで W2 を完了した。適用前は醤油のページがなく、ログは 1 件だった。適用すると `wiki/sources/醤油.md` ができ、索引に醤油が加わり、`## [2026-11-21] ingest | 醤油` の 1 行が増えた。`/wiki:browse` は `http://127.0.0.1:` で始まる URL と `"scope": "project"` を返し、Code のブラウザペインの Index に味噌と醤油の要約が並んだ。「麹」のページには醤油の記述があり、被リンクに味噌と醤油が並んだ。`/wiki:lint` は CLI の `wiki_lint.py` を実行し、3 ページを調べ、孤立、リンク切れ、読み込みエラーは報告しなかった。記録は `autotest/05-run1-w2.json`、`autotest/05-run1-browse-index.jpg`、`autotest/05-run1-browse-koji-backlinks.jpg`。確認 5 の判定は 1 回分で、3 回共通の目印はまだ確定していない。

1 回目の初期化では、Code が選択式の質問を順に表示し、グラフ層だけ自由入力で「後回し」と答えた。閲覧では Code の「開く」を押すとブラウザペインが前面に出た。保存した画面と応答からは、wiki ページの候補を知らせるフックの表示を確認できなかった。

2 回目の開始時に `S1b-wiki-0.39.1` を復元した。Claude Desktop `6.6395.0.0`、wiki `0.39.1`、uv キャッシュ 441,267,870 バイト、練習用フォルダーが空、e5・ruri のキャッシュがないことを照合した。復元の完了後は VMConnect に Windows のロック画面が表示された。記録は `autotest/05-run2-before.json`。

復元後の補足照合では、VM の親チェックポイントが `S1b-wiki-0.39.1`、Git が `2.56.0.windows.4`、uv が `0.13.9`、Python が `3.12.10`、Visual C++ の DLL 3 本が `14.52.37029.0` だった。照合時に wiki MCP の Python プロセスは 0 件だった。Claude の MSIX 配下の `LocalCache/Local` にも通常の uv と ruri のキャッシュに対応するパスはなかった。記録は `autotest/05-run2-baseline-details.json`。

2 回目の復元とほぼ同時の 06:36:12 に Windows がリモートセッションの切断を記録した。07:23:23 に再接続し、Claude Desktop に戻った。検証 VM の AC 電源設定を、画面オフは 5 分から 60 分、スリープは 15 分から 60 分に変更した。変更は実行中の VM に適用した。チェックポイント復元に伴う再認証への効果は確認していない。記録は `autotest/05-run2-vm-session.json`。

Code で空の `info-hive-practice` を選ぶと、「このワークスペースを信頼しますか？」と表示された。利用者の承認後、`/wiki:init` を送る前の 07:33 に `S1c-wiki-0.39.1-trusted` を保存した。Claude Desktop と wiki の版、uv キャッシュのサイズ、練習フォルダーが空で e5・ruri が未取得であることは `S1b` と一致した。この時点での違いは Claude Desktop が開いていること、練習フォルダーの信頼を承認済みであること、AC 電源設定。記録は `autotest/05-s1c-checkpoint.json`。

確認 5 の 2 回目の W1 では、グラフ層の「後回し」が選択肢に出た。初期化のツール出力には `"status": "ready"` があり、07:35:11 の記録で e5 キャッシュは 252,425,348 バイトだった。標準版の `CLAUDE.md` を承認し、`wiki/sources/味噌.md` と `wiki/concepts/麹.md`、索引の味噌の行と `## [2026-11-21] ingest | 味噌` を確認した。質問の答えには `[[味噌]]`、`[[麹]]` と `**確信度（confidence）: 高**` があった。保存した呼び出しに MCP の `query` と `wiki:wiki-reader` は見つからなかった。記録は `autotest/05-run2-init.json`、`autotest/05-run2-w1.json`、`autotest/05-run2-w1-query.jpg`。

2 回目の W2 では、利用者の承認前に `wiki/sources/醤油.md` がなく、取り込みログが 1 件であることを確認した。承認後に醤油のファイルと索引の行ができ、`## [2026-11-21] ingest | 醤油` が 1 行増えた。browse の出力は `http://127.0.0.1:` で始まる URL と `"scope": "project"` を示した。「開く」を押したブラウザペインでは Index に味噌と醤油が並び、麹のページに醤油の記述と 2 件の被リンクがあった。

2 回目の `/wiki:lint` は MCP の `mcp__plugin_wiki_wiki__lint` を呼んだ。JSON の `total_pages` は 3、`orphans`、`broken_links`、`read_errors` はいずれも 0。空の `tags` を 3 ページの必須項目の欠落として報告し、タグの追加を提案した。検証用のページを保つため「修正しない」を選んだ。1 回目の CLI の構造点検とは指摘が異なった。醤油の取り込み後、エージェントがグラフの追記で差分全体を引数に渡して終了コード 2 になった。ハッシュだけを取り出して再実行し、追記は完了した。記録は `autotest/05-run2-w2.json`、`autotest/05-run2-checklist-verdict.json`、`autotest/05-run2-browse-index.jpg`、`autotest/05-run2-browse-koji-backlinks.jpg`。

3 回目のために `S1c-wiki-0.39.1-trusted` を復元した。07:49 の記録では、Claude Desktop と wiki の版、空の練習用フォルダー、uv キャッシュと e5・ruri の未取得を照合した。画面オフとスリープは 60 分のままだった。07:49:25 に Windows のリモートセッションが切断され、VMConnect にサインイン画面が出た。この電源設定では復元直後のロックを防げなかった。07:51:10 に再接続すると、Code では練習用フォルダーが選択済みで、信頼確認を再表示せず `/wiki:init` を開始できた。記録は `autotest/05-run3-before.json`。

3 回目の W1 では、初期化ツールが `"status": "ready"` を返し、07:53:45 の e5 キャッシュは 252,425,348 バイトだった。標準版の `CLAUDE.md`、味噌と麹のページ、索引と取り込みログを確認した。味噌の質問には `[[味噌]]`、`[[麹]]` と `**確信度（confidence）: 高**` が付いた。保存した呼び出しに MCP の `query` と `wiki:wiki-reader` は見つからなかった。記録は `autotest/05-run3-init.json`、`autotest/05-run3-w1.json`、`autotest/05-run3-w1-query.jpg`。

3 回目の W2 でも、醤油を追加すると索引に醤油の行ができ、取り込みログが 1 件から 2 件になった。browse の生の出力は `http://127.0.0.1:` で始まる URL と `"scope": "project"` を示した。最初の応答後は Code のブラウザペインが見えなかった。表示された URL をブラウザペインで開くよう依頼すると、ペインが表示され、Index の味噌と醤油、麹のページの醤油の節と 2 件の被リンクを確認できた。構造点検は MCP を使い、3 ページ、孤立 0、リンク切れ 0、読み込みエラー 0 だった。空の `tags` の指摘を受けたが修正を適用しなかった。記録は `autotest/05-run3-w2.json`、`autotest/05-run3-checklist-verdict.json` と `autotest/05-run3-browse-*.jpg`。

3 回目の `/wiki:lint` は、構造に加えてページの内容も点検した。「麹」のページにあった、熟成期間の影響を色だけに限定する表現を、原文から言える範囲より強いと指摘した。「熟成が長いほど色が濃くなる」と原文の範囲に絞る修正案を提示し、検証では適用しなかった。この内容点検の時点では ruri は取得されていなかった。記録は `autotest/05-run3-w2.json` と `autotest/05-s2-checkpoint.json`。

確認 5 の 3 回に共通した目印は、初期化の `"status": "ready"`、味噌と醤油のページ・索引・各 1 件の取り込みログ、味噌の回答の出典と確信度、Index の 2 行と麹の被リンク、構造点検で孤立・リンク切れ・読み込みエラーがないこと。browse のループバック URL と project スコープは 3 回で観測した。1 回目の保存済み会話にはサーバーの起動通知が残り、生の JSON は 2・3 回目の背景タスクの出力で保存した。点検の呼び出し先とタグの指摘、ペインを表示する操作は回によって異なった。味噌の質問では 3 回とも保存した呼び出しに MCP の `query` と `wiki:wiki-reader` が見つからなかった。保存した画面からは wiki ページの候補を知らせるフックの通知を確認できなかった。

3 回目の終了後、Claude Desktop をトレイのメニューから終了した。背景の閲覧サーバーも停止したことを照合し、08:11 に `S2-wiki-0.39.1` を保存した。練習用 wiki に味噌、醤油、麹があり、e5 キャッシュは 252,425,348 バイト。ruri の `verified.json` はなかった。確認 10 を S2 から始めるときは、ruri が取得済みという確認表の想定と異なる。記録は `autotest/05-s2-checkpoint.json`。

### 確認 6 の ruri 初回取得

別の試行として `S1c-wiki-0.39.1-trusted` を復元し、モデル未取得と練習フォルダーが空であることを確かめた。Code で確認表の初期化条件をまとめて送ると、`CLAUDE.md` の定型文は別の承認画面を表示せずに作成された。味噌の取り込みでは要約と麹に加え、製法と種類のページも作成する差分を承認した。検索前の e5 キャッシュは 252,425,348 バイトで、ruri はなかった。

08:22:28.698（JST）に Code が `mcp__plugin_wiki_wiki__query` で「味噌」を検索した。最初の結果は `mode: lexical`、`index.state: embedding`、埋め込み済み 0/14 で、語彙検索に `sources/味噌.md` が含まれた。08:22:45.007 に ruri の `verified.json` が書かれた。ツール呼び出しの時刻から 16.31 秒後で、ruri のディレクトリは 535,699,472 バイトだった。この時間はこの VM と通信環境での観測。利用者は ruri を事前導入しなかった。

取得後に同じ検索を繰り返すと、`mode: hybrid`、`index.state: ready`、埋め込み済み 14/14 になり、結果に `bm25` と `embedding` の両方が付いた。記録は `autotest/06-ruri-before-wiki.json`、`autotest/06-ruri-init.json`、`autotest/06-ruri-watch.json`、`autotest/06-ruri-first-verified.json`、`autotest/06-ruri-warm-verified.json` と対応する検索の JSON・画像。

### 確認 7 の MCP 接続と再接続

`S2-wiki-0.39.1` を復元し、Claude Desktop 6.6395.0.0 の Code で練習セッションを開いた。`/mcp` の「MCP サーバー」画面で `wiki` の行にチェックがあり、行を開くと「接続済み・7 個のツール」と「再接続」が表示された。「再接続」を押すと「再接続中…」のあとに接続済みへ戻り、「wiki が接続されました。」と通知された。

`/mcp reconnect all` はこの Code セッションで `Reconnect, enable, and disable aren't available in this session.` と表示された。文書で再接続を案内するときは、確認できた `/mcp` の wiki の行からの操作を使う。記録は `autotest/07-mcp-before.json`、`autotest/07-mcp-connected.jpg`、`autotest/07-mcp-wiki-details.jpg`、`autotest/07-mcp-reconnected.jpg`、`autotest/07-mcp-reconnect-all.jpg`。

### 確認 8 の Cowork

`S1c-wiki-0.39.1-trusted` を復元し、Claude Desktop 6.6395.0.0 のチャットと Cowork が統合された画面を開いた。左の「プラグイン」→「追加」→「マーケットプレイスを追加」→「リポジトリから追加」で `to884/info-hive-marketplace` を同期した。Wiki の詳細で「追加」を押し、利用者がローカル MCP サーバーの確認画面で「続ける」を押すと、Wiki 0.39.1 が「追加済み」になった。Code では同じ版がすでに導入済みだった。記録は `autotest/08-cowork-added.jpg`。

「新規作成」→「プロジェクトまたはフォルダー」→「フォルダを追加」で、合言葉を記した `CLAUDE.md` だけがある `%USERPROFILE%\info-hive-cowork` を選んだ。アプリはこのフォルダーのファイル変更の許可を別に求めた。開始時点でホストはゲストに仮想化拡張機能を公開していた。ゲストの `VirtualMachinePlatform` は無効だった。記録は `autotest/08-cowork-before.json`。

利用者がフォルダーの変更を許可し、「こんにちは」を送ったあと、英語の `Folder access request` が出た。このセッションはクラウドで動き、Claude が使うファイルは Anthropic のサーバーで処理されるという表示だった。利用者がそのセッションのアクセスを許可すると、右の「このセッションで使用」に練習フォルダーが出た。挨拶の返信に合言葉はなかった。

`/wiki:init` は送信欄で `/init` に補完された。初回の自動モードの案内は、利用者が「確認しました」を押すまで次の送信を止めた。`/init` への返信は「合言葉: みそ」で始まった。アプリのツール欄には、ファイル読み取り、コマンド実行、接続した PC のファイル一覧が表示された。返答本文は Cowork のワークスペースで uv 0.11.32 と Python 3.13 を使えると報告した。この uv は Windows ゲストで確認した 0.13.9 と異なる。記録は `autotest/08-cowork-cloud-prompt.jpg`、`08-cowork-greeting.jpg`、`08-cowork-auto-notice.jpg`、`08-cowork-init-questions.jpg`。

確認表の条件を送ると、Cowork はクラウド環境の `/home/claude/proj` で `init_wiki.py` を実行した。`setup-wiki` の環境で FastEmbed が e5 の取得を試み、Hugging Face のモデル情報の取得で `httpx.ProxyError: 403 Forbidden` が出た。ツールの出力には検索環境のセットアップ失敗と終了コード 1 があり、`"status": "ready"` はなかった。Windows の接続フォルダーには `CLAUDE.md` だけが残り、`wiki/SCHEMA.md` はなく、`CLAUDE.md` の SHA-256 は初期値と一致した。

Cowork は wiki の MCP `stats` を呼び出せた。最初の呼び出しは Windows の `%USERPROFILE%\info-hive-cowork\wiki` を渡し、ディレクトリが見つからないエラーを返した。初期化の確認とは別に、呼び出しが Windows 側のパスを受け取ったことをツール欄で確認した。記録は `autotest/08-cowork-init-tool.jpg`、`08-cowork-init-proxy-error.jpg`、`08-cowork-after-init.json`、`08-cowork-stats-error.jpg`。

追加の試行では、Windows 側に導入済みの wiki 0.39.1 の `init_wiki.py` を同じ練習フォルダーで実行した。約 22 秒で終了コード 0、`"status": "ready"`、`wiki/SCHEMA.md` と `raw/` を確認した。同じ Cowork セッションで `stats` を再実行すると、Windows の同じパスからページ数 0、Index の行数 26 が返った。Cowork のクラウド初期化は失敗し、Windows 側で初期化した wiki の統計取得は成功した。記録は `autotest/08-cowork-windows-init.json` と `08-cowork-stats-ok.jpg`。

### 確認 9 の社内プロキシ

検証 VM では、ユーザーの明示的なプロキシと PAC URL が未設定で、`HTTP_PROXY`、`HTTPS_PROXY`、`ALL_PROXY` もなかった。WinHTTP は直接アクセスを示した。社内プロキシ経由の試験環境がないため、確認表の条件に従い、証明書設定の前後の比較は実施しなかった。記録は `autotest/09-proxy-preconditions.json`。

### 確認 10 のハウツー

- C2（事前準備）: 確認 1-2 で Git `2.56.0.windows.4` と uv `0.13.9` の版表示と、`uv sync --help` の `UV_SYSTEM_CERTS` を確認した。社内プロキシの内側の手順は確認 9 のとおり未確認。記録は `autotest/01-prerequisites-verify.txt`。
- C3（起動の診断）: `S2-wiki-0.39.1` を復元し、`%LOCALAPPDATA%\info-hive\logs\` に `server.log` が 1 件あることを確認した。確認 3 の `--ensure` は wiki 0.39.1 で終了コード 0、32.78 秒だった。S2 の練習 wiki には味噌と醤油があり、ruri の `verified.json` はなかった。記録は `autotest/10-C3.txt`。
- W3（ユーザースコープの wiki）: 新しい Code セッションで `/wiki:init --user` を実行し、既定の場所を選んだ。`%USERPROFILE%\info-hive\wiki` と `raw`、埋め込みキャッシュを確認した。標準案の承認後、既存ファイルがなかった `%USERPROFILE%\.claude\CLAUDE.md` が 5 行で新規作成された。`SCHEMA.md` の検索例には相対パス `--wiki wiki/` が残り、Code も指摘した。記録は `autotest/10-W3.txt`、`10-W3-approval.jpg`、`10-W3-done.jpg`。
- W4（Web の取り込み）: 新しい Code セッションのプロジェクト wiki に [IANA の Example Domains](https://www.iana.org/help/example-domains) を取り込んだ。`wiki:web-raw` が raw を作り、参照資料の原題併記に関する翻訳警告が 3 件出た。理由のログを承認したあと、呼び出し側の `--accept-warnings` 付きの検査が `ok: true` と `completed: true` を返した。実行コマンドが出力を 1,800 バイトに切り詰めたため `work_dir_removed` は表示されなかったが、実ファイルの確認では作業用ディレクトリは消えていた。承認後の `raw/iana-example-domains.md`、`wiki/sources/iana-example-domains.md`、索引、取り込みログを確認した。任意のグラフ増分の追記は、増分が推定値だったため見送った。記録は `autotest/10-W4.txt` と `10-W4-*.jpg`。
- W5（wiki のアップグレード）: 新しい Code セッションで同じプロジェクトに `/wiki:upgrade` を実行した。`init_wiki.py --upgrade` の実行環境は `"status": "ready"` で、4 ページの 25 セクションをすべて埋め込んだ。`SCHEMA.md` は最新版で、マージの提案はなく、前後の SHA-256 は一致した。旧版の `SCHEMA.md` のマージはこの試行では発生しなかった。記録は `autotest/10-W5.txt` と `10-W5-done.jpg`。
- C4（プラグインの更新）: `/plugin marketplace update info-hive` は設定の「プラグイン」を開いた。ディレクトリの「プラグイン」→「Code」→「info-hive」のメニューから「アップデートを確認」を選ぶと「マーケットプレイスを更新しました。」。設定の「プラグイン」で Wiki の「アップデートを確認」を選ぶと「前回のリリース以降、変更はありません。」。Code に導入済みの版とキャッシュのフォルダーは 0.39.1 だった。新版への置き換えは発生しなかった。記録は `autotest/10-C4.txt` と `10-C4-*.jpg`。

C5 は用語集で、確認表に実行するコマンドの指定がない。チュートリアルは Code の 3 回の結果で執筆できる。Cowork の初期化、社内プロキシ、実際の旧版からの更新は、上の試行で確認できた範囲を各ハウツーに記す。

### 検証用スクリプトとレビュー

Claude Opus 5.5（effort high）のレビューは、隔離診断と GUI の確認 3 の順序、チェックポイントの中身、未確認の項目が本文から読み取れないと指摘した。実行記録とチェックポイントの時刻を照合し、上の時系列、根拠、未確認項目を追記した。レビューの原文は `autotest/stage2-automation-opus-review.md`。

検証用スクリプトでは、VM 名を完全一致の 1 台に絞り、ゲストで確認する前に差分 VHDX の親をたどって基底 VHDX を照合するようにした。起動失敗時のタスクの片付けを追加し、確認のログは実行中に書いて時間切れでも取得できるようにした。PowerShell の構文と、ホストの PowerShell 7 で成功と例外のログを確認した。ゲストのタスクの時間切れと、変更後の Windows Setup からの通し実行は未確認。
