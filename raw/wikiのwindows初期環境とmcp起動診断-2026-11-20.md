# 利用者向け文書の Windows 初期環境と MCP の起動診断

実施日 2026-11-20（日本時間）。新規の Hyper-V VM の空の VHDX に Windows Setup で Windows 11 Enterprise 評価版 26H2（build 26300.9457）を入れた。Claude Desktop は Anthropic 署名を確認した MSIX 5.11492.5.0 を登録した。

## Windows の対話セッション

専用のローカルユーザーの対話セッションで Windows 標準の PowerShell を使った。`where.exe git` と `where.exe uv` は終了コード 1。`where.exe python` は `Microsoft\WindowsApps\python.exe` を返し、`python.exe --version` は Microsoft Store の案内と終了コード 9009 を返した。`.ssh` ディレクトリと、`System32` の `vcruntime140.dll`、`vcruntime140_1.dll`、`msvcp140.dll` はなかった。記録は `01-os-baseline.txt`。先に PowerShell Direct で直接実行した `Get-Command python.exe` では結果がなかった。記録は `00-baseline.json`。

## wiki v0.39.1 の起動診断

`info-hive-wiki` の v0.39.1（`eae9a19c8ffd7fecdb89e3eadb31a38160ec2c6d`）をアーカイブから展開し、uv 0.13.9 とともに専用フォルダーで使った。uv の PATH 変更を止め、uv のキャッシュ、Python の配置、info-hive のデータをそのフォルダーに指定した。`wiki_mcp_launch.py --ensure` は 34.41 秒で終了コード 1。例外と `launch.log` は、Visual C++ 再頒布可能パッケージが必要だと知らせ、`winget install --id Microsoft.VCRedist.2015+.x64 -e --source winget` を示した。記録は `03-isolated-v0.39.1.txt`。この結果は直接起動での診断で、Claude Desktop の Code タブでの表示はアカウント認証後に確認する。

## 旧版との比較

旧 VM の `03-deps-run2.txt` では、wiki 0.39.0 の `--ensure` が同じ前提で終了コード 1、Visual C++ 再頒布可能パッケージを導入したあとは終了コード 0 だった。`04-hekp-run2.txt` と `04-help-run3.txt` では、`/wiki:help` が Python の実行エイリアスで失敗し、Python 3.12.10 の導入後に 12 本のコマンドを表示した。
