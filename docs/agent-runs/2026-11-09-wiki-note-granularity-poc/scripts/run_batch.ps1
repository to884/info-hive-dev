# PoC の実行を、ユーザーのターミナルで走らせる（Codex のサンドボックスは入れ子では起動しないため）。
# 使い方: & .\scripts\run_batch.ps1 [-Only R-hybrid-sol-1] [-Parallel 3]
param(
    [string]$Only = "",
    [int]$Parallel = 3,
    [string]$SnapshotRoot = "D:/Users/toshiki/AppData/Local/Temp/claude/a5ce26b2720c690f/3997aa58-3145-42c6-8d83-a0fa6b910f69/scratchpad/snapshots"
)
$ErrorActionPreference = "Stop"
$env:PYTHONIOENCODING = "utf-8"
$here = Split-Path -Parent $MyInvocation.MyCommand.Path
$private = Join-Path $HOME "info-hive-dev-private/2026-11-09-wiki-note-granularity-poc/logs"
New-Item -ItemType Directory -Force $private | Out-Null
$log = Join-Path $private ("batch-" + (Get-Date -Format "yyyyMMdd-HHmmss") + ".txt")
$argsList = @((Join-Path $here "run_poc.py"), "--snapshot-root", $SnapshotRoot, "--parallel", "$Parallel")
if ($Only) { $argsList += @("--only", $Only) }
python @argsList 2>&1 | Tee-Object -FilePath $log
Write-Host "ログ: $log"
