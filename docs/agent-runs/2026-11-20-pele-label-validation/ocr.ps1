# Windows PowerShell 5.1 で保存済みの 2 倍 PNG を日本語 OCR に渡す。
param([Parameter(Mandatory=$true)][string]$OutputDirectory)
$ErrorActionPreference='Stop'
Add-Type -AssemblyName System.Runtime.WindowsRuntime
$null=[Windows.Storage.StorageFile,Windows.Storage,ContentType=WindowsRuntime]
$null=[Windows.Graphics.Imaging.BitmapDecoder,Windows.Graphics.Imaging,ContentType=WindowsRuntime]
$null=[Windows.Media.Ocr.OcrEngine,Windows.Foundation,ContentType=WindowsRuntime]
$null=[Windows.Globalization.Language,Windows.Globalization,ContentType=WindowsRuntime]
$asTaskDefinition=[System.WindowsRuntimeSystemExtensions].GetMethods() | Where-Object {
    $_.Name -eq 'AsTask' -and $_.IsGenericMethodDefinition -and $_.GetParameters().Count -eq 1 -and $_.GetParameters()[0].ParameterType.Name -eq 'IAsyncOperation`1'
} | Select-Object -First 1
function Wait-Operation($Operation,[Type]$ResultType) {
    $task=$asTaskDefinition.MakeGenericMethod($ResultType).Invoke($null,@($Operation))
    $task.Wait()
    return $task.Result
}
$root=(Get-Location).ProviderPath
$source=Join-Path $root 'docs/agent-runs/2026-11-19-pele-png-compatibility/results'
$manifest=Get-Content -Raw -Encoding UTF8 (Join-Path $source 'results.json') | ConvertFrom-Json
$engine=[Windows.Media.Ocr.OcrEngine]::TryCreateFromLanguage([Windows.Globalization.Language]::new('ja'))
if ($null -eq $engine) { throw '日本語 OCR が利用できない' }
if (Test-Path -LiteralPath $OutputDirectory) { throw '出力先は未作成のパスを指定してください' }
New-Item -ItemType Directory -Path $OutputDirectory | Out-Null
$records=@()
foreach ($item in $manifest.prepared) {
    $image=$item.images | Where-Object { $_.scale -eq 2 }
    $filePath=Join-Path $source $image.file
    $file=Wait-Operation ([Windows.Storage.StorageFile]::GetFileFromPathAsync($filePath)) ([Windows.Storage.StorageFile])
    $stream=Wait-Operation ($file.OpenAsync([Windows.Storage.FileAccessMode]::Read)) ([Windows.Storage.Streams.IRandomAccessStream])
    try {
        $decoder=Wait-Operation ([Windows.Graphics.Imaging.BitmapDecoder]::CreateAsync($stream)) ([Windows.Graphics.Imaging.BitmapDecoder])
        $bitmap=Wait-Operation ($decoder.GetSoftwareBitmapAsync()) ([Windows.Graphics.Imaging.SoftwareBitmap])
        try {
            $result=Wait-Operation ($engine.RecognizeAsync($bitmap)) ([Windows.Media.Ocr.OcrResult])
            $words=@($result.Lines | ForEach-Object { $_.Words } | ForEach-Object {
                @{text=$_.Text;x=$_.BoundingRect.X;y=$_.BoundingRect.Y;width=$_.BoundingRect.Width;height=$_.BoundingRect.Height}
            })
            $records+=@{id=$item.id;scale=2;language='ja';text=$result.Text;words=$words;imageSha256=$image.sha256}
            Write-Output ('OCR '+$item.id)
        } finally { $bitmap.Dispose() }
    } finally { $stream.Dispose() }
}
[IO.File]::WriteAllText((Join-Path $OutputDirectory 'results.json'),(ConvertTo-Json -InputObject $records -Depth 8),[Text.UTF8Encoding]::new($false))
