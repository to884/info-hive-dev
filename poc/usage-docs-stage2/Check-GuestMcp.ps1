$ErrorActionPreference = 'Stop'
$registryPath = Join-Path $env:USERPROFILE '.claude\plugins\installed_plugins.json'
$registry = Get-Content -LiteralPath $registryPath -Encoding UTF8 -Raw | ConvertFrom-Json
$entries = @($registry.plugins.'wiki@info-hive' | Where-Object { $_.installPath -and (Test-Path -LiteralPath $_.installPath) })
if ($entries.Count -ne 1) { throw '使用中の wiki@info-hive の導入先を 1 つに定められません。' }
$manifest = Get-Content -LiteralPath (Join-Path $entries[0].installPath '.claude-plugin\plugin.json') -Encoding UTF8 -Raw | ConvertFrom-Json
$launcher = Join-Path $entries[0].installPath 'skills\info-hive\scripts\wiki_mcp_launch.py'
"wiki_version: $($manifest.version)"
"start: $(Get-Date -Format o)"
& uv.exe --version

$watch = [Diagnostics.Stopwatch]::StartNew()
$ErrorActionPreference = 'Continue'
& uv.exe run --quiet --script $launcher --ensure
$ensureExit = $LASTEXITCODE
$watch.Stop()
"ensure_exit: $ensureExit"
"ensure_seconds: $([math]::Round($watch.Elapsed.TotalSeconds, 2))"
$rootPaths = [ordered]@{
    uv = (& uv.exe cache dir)
    ruri = (Join-Path $env:LOCALAPPDATA 'info-hive\models')
    e5 = (Join-Path $env:USERPROFILE '.cache\info-hive\fastembed')
}
foreach ($key in $rootPaths.Keys) {
    $path = $rootPaths[$key]
    if ($path -and (Test-Path -LiteralPath $path)) {
        $bytes = (Get-ChildItem -LiteralPath $path -File -Recurse -Force | Measure-Object Length -Sum).Sum
        "${key}_bytes: $bytes"
    } else {
        "${key}_bytes: なし"
    }
}
if ($ensureExit -ne 0) { throw "MCP の準備が終了コード $ensureExit で止まりました。" }
