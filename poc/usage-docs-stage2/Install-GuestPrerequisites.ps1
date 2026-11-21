$ErrorActionPreference = 'Stop'
$gitPath = Join-Path $env:ProgramFiles 'Git\cmd\git.exe'
if ((Get-Command git.exe -ErrorAction SilentlyContinue) -or (Test-Path -LiteralPath $gitPath)) {
    'Git は導入済みです。'
} else {
    $wingetArguments = @('install','--id','Git.Git','-e','--source','winget','--silent','--disable-interactivity','--accept-package-agreements','--accept-source-agreements')
    & winget.exe @wingetArguments
    if ($LASTEXITCODE -ne 0) { throw "Git の導入が終了コード $LASTEXITCODE で止まりました。" }
}

$installer = Join-Path $PSScriptRoot 'uv-install.ps1'
for ($attempt = 1; $attempt -le 3; $attempt++) {
    try {
        Invoke-WebRequest -UseBasicParsing -Uri 'https://astral.sh/uv/install.ps1' -OutFile $installer
        break
    } catch {
        if ($attempt -eq 3) { throw }
        Write-Output "uv のインストーラーの取得をやり直します。$($_.Exception.Message)"
        Start-Sleep -Seconds 5
    }
}
& (Join-Path $PSHOME 'powershell.exe') -NoProfile -NonInteractive -ExecutionPolicy Bypass -File $installer
if ($LASTEXITCODE -ne 0) { throw "uv の導入が終了コード $LASTEXITCODE で止まりました。" }
