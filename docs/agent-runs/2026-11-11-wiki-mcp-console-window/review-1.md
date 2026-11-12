## 判定

**条件付きで採用可。** 入口がコンソールを継承する構成、または `CREATE_NO_WINDOW` で起動される構成に限る。コンソールを持たない入口では、未変更の補助プロセス起動が可視の窓を作る反例があり、提示された要件1を無条件には満たさない。確信度：**高**。

## 致命的・重大な欠陥

### 重大：コンソールを持たない入口では、準備処理と中継の起動で窓が出る

**反例の条件：** ホストが入口を `DETACHED_PROCESS` で起動し、標準入出力だけをパイプで渡す。Claude Code が現在この方式を使っているかは未確認だが、レビューで指定された「コンソールなしの起動」に当たる。

次の実際の関数を、コンソールを持たない Python プロセスから呼んだ。リポジトリは変更せず、起動対象だけをコンソールの有無を報告する小さな Python コードに置き換えた。

| 呼び出し | 入口が `DETACHED_PROCESS` | 入口が `CREATE_NO_WINDOW` |
| --- | --- | --- |
| `wiki_mcp_common._run_uv` | 子の `IsWindowVisible` が `true` | `false` |
| `wiki_mcp_launch.run_relay` | 子の `IsWindowVisible` が `true` | `false` |

根拠は、[_run_uv の起動](/C:/Works/info-hive-dev/.claude/worktrees/wiki-mcp-console-window/info-hive-wiki/skills/info-hive/scripts/wiki_mcp_common.py:373)と [run_relay の起動](/C:/Works/info-hive-dev/.claude/worktrees/wiki-mcp-console-window/info-hive-wiki/skills/info-hive/scripts/wiki_mcp_launch.py:53)の双方に、窓を抑制する指定がないこと。標準入出力のリダイレクトだけでは、この窓は抑制されなかった。

サーバー本体の `spawn_server` に到達する前に起きるため、今回のフラグ変更では防げない。これは**今回導入した回帰ではなく、今回の修正後にも残る起動経路の欠陥**である。実際の uv と MCP を通した再現は、この環境では実施していない。

## 崩れる前提

- **「入口と中継はコンソールを持っている」**  
  入口を `DETACHED_PROCESS` で起動するホストでは崩れる。上記の実験で確認した。

- **「コンソールの分離でホスト終了後の生存を保証できる」**  
  ホストが継承先のジョブを終了させれば、コンソールが別でもサーバーは止まる。今回のフラグはジョブから離脱する指定ではない。これは既存設計の制約で、ADR の「見直す条件」にも記載されている。[Windows のジョブの仕様](https://learn.microsoft.com/en-us/windows/win32/procthread/job-objects)

- **「ホストの終了にはログオフも含められる」**  
  ログオフでは対話ログオンセッションのプロセスが終了対象になる。今回の方式でログオフをまたぐ生存は保証できない。ただし、通常のアプリ終了とは別の条件であり、今回の回帰とは判断しない。[Windows のログオフの仕様](https://learn.microsoft.com/en-us/windows/win32/shutdown/logging-off)

## 見落としと軽微な問題

1. **軽微：手動試験は、窓が出ても成功する設定がある。**  
   [check_server_console.py:83](/C:/Works/info-hive-dev/.claude/worktrees/wiki-mcp-console-window/tests/wiki/check_server_console.py:83)以降は、新しい HWND の題に `wiki-mcp-server` が含まれる場合だけ失敗させる。Windows Terminal の `showTerminalTitleInTitlebar=false` では題が `Windows Terminal` になるため、窓が出ても `server_windows=[]` になる。[設定の仕様](https://learn.microsoft.com/en-us/windows/terminal/customize-settings/appearance)  
   また、観測は `--ensure` 終了後だけなので、準備処理や中継が終了するまでに消えた窓も検出しない。

2. **軽微：追加した単体試験は、コンソールの分離を検証していない。**  
   [test_mcp_server.py:202](/C:/Works/info-hive-dev/.claude/worktrees/wiki-mcp-console-window/tests/wiki/test_mcp_server.py:202)はサーバー直下の `conhost.exe` だけを見る。反例として、サーバーを親のコンソールを継承する設定にしても、サーバー直下に新しい `conhost.exe` は不要なので、この条件は通る。その状態では親コンソールの閉鎖から隔離できていない。Ctrl+C、Ctrl+Break、窓の閉鎖を発生させる試験もない。

3. **軽微：ADR の「ホストが終わっても残る」という追記は、測定範囲を広く書いている。**  
   [ADR:40](/C:/Works/info-hive-dev/.claude/worktrees/wiki-mcp-console-window/docs/adr/0012-wiki-owns-local-mcp-index-server.md:40)が根拠にする `check_claude_spawn.py` は、子として実行した `claude -p` の正常終了後を測る。デスクトップアプリ全体の終了は測っておらず、ADR の影響の節にも「確かめていない」と残っている。デスクトップアプリ終了後の生存は**確かめられず**。

4. **軽微：更新しても、既に窓を持つ旧サーバーは再起動されない。**  
   [code_version の対象](/C:/Works/info-hive-dev/.claude/worktrees/wiki-mcp-console-window/info-hive-wiki/skills/info-hive/scripts/wiki_mcp_common.py:44)に `wiki_mcp_relay.py` と `plugin.json` は含まれない。今回のサブモジュール差分は、この2ファイルと CHANGELOG だけなので、サーバーの版ハッシュは変わらない。旧サーバーが生きていれば更新後の中継も再利用し、既存の窓は残る。新規起動の修正と、更新直後に窓が消えることは一致しない。

## 検証した事実

| 主張 | 結果 |
| --- | --- |
| Windows の変更は `CREATE_NO_WINDOW \| CREATE_NEW_PROCESS_GROUP` への置換 | **一致**。サブモジュール差分を確認した |
| POSIX の起動方法は変えていない | **一致**。`start_new_session=True` の分岐は変更なし |
| `CREATE_NO_WINDOW` の子が、さらに起動した子へ窓のないコンソールを引き継ぐ | **一致**。小さなプロセスで `GetConsoleProcessList` を測り、同じコンソールへの所属を確認した |
| バージョンと CHANGELOG は 0.10.1 | **一致** |
| `test_mcp_server.py` は28件 | **一致**。定義数を確認した |
| 28件の成功、旧コードで追加試験が失敗、実サーバーの terminate・アイドル終了 | **確かめられず**。実行環境に uv と必要な依存がなく、再実行していない |

## 崩せなかった点

- `spawn_server` のフラグ置換自体が、親コンソールの Ctrl+C／Ctrl+Break をサーバーへ流すという根拠は見つからなかった。制御イベントは同じコンソールへの所属が条件である。[制御イベントの仕様](https://learn.microsoft.com/en-us/windows/console/generateconsolectrlevent)
- `DETACHED_PROCESS` を外し、`CREATE_NO_WINDOW` と併用しない判断は、併用時に後者が無視される仕様と一致する。[プロセス生成フラグの仕様](https://learn.microsoft.com/en-us/windows/win32/procthread/process-creation-flags)
- 今回の変更が `stop_server`、アイドル終了、POSIX の振る舞いを新たに壊す具体例は見つからなかった。

使用した MCP サーバー: なし  
使用した Agent Skills: なし
