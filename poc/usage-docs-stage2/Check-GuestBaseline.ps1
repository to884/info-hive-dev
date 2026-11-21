$ErrorActionPreference = 'Continue'
$checks = @(
    @{ Program = 'where.exe'; Arguments = @('git') },
    @{ Program = 'where.exe'; Arguments = @('uv') },
    @{ Program = 'where.exe'; Arguments = @('python') },
    @{ Program = 'python.exe'; Arguments = @('--version') }
)
foreach ($check in $checks) {
    $arguments = $check.Arguments
    "== $($check.Program) $arguments"
    if (Get-Command $check.Program -ErrorAction SilentlyContinue) {
        & $check.Program @arguments
        "exit: $LASTEXITCODE"
    } else {
        '実行ファイルが見つかりません。'
    }
}
"ssh_directory: $(Test-Path -LiteralPath (Join-Path $env:USERPROFILE '.ssh'))"
foreach ($dll in 'vcruntime140.dll','vcruntime140_1.dll','msvcp140.dll') {
    "$dll $(Test-Path -LiteralPath (Join-Path $env:SystemRoot "System32\$dll"))"
}
