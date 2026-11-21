#Requires -Version 7.0
[CmdletBinding()]
param(
    [Parameter(Mandatory)] [string] $VmName,
    [Parameter(Mandatory)] [string] $StageRoot,
    [Parameter(Mandatory)] [string] $RecordDirectory
)

$ErrorActionPreference = 'Stop'
$record = Join-Path $RecordDirectory '00-baseline.json'
if (Test-Path -LiteralPath $record) { throw '既存の検証記録を上書きできません。' }
$root = (Get-Item -LiteralPath $StageRoot).FullName
$vmMatches = @(Get-VM | Where-Object Name -eq $VmName)
if ($vmMatches.Count -ne 1) { throw '指定した名前の VM を 1 台に特定できません。' }
$vm = $vmMatches[0]
$disks = @(Get-VMHardDiskDrive -VM $vm)
# チェックポイントがある場合、アクティブなディスクは差分ディスクになる。
if ($disks.Count -ne 1 -or $disks[0].Path -ne (Join-Path $root 'windows.vhdx')) {
    throw '指定された作業場所にある検証用 VM のみ操作できます。'
}
$package = Join-Path $root 'Claude.msix'
$signature = Get-AuthenticodeSignature -LiteralPath $package
if ($signature.Status -ne 'Valid' -or $signature.SignerCertificate.GetNameInfo('SimpleName', $false) -ne 'Anthropic, PBC') {
    throw 'Claude Desktop のパッケージの署名を確認できません。'
}
$credential = Import-Clixml -LiteralPath (Join-Path $root 'guest.credential.xml')
$session = New-PSSession -VMId $vm.Id -Credential $credential
try {
    $target = Invoke-Command -Session $session -ScriptBlock {
        $setup = Get-ItemProperty 'HKLM:\SYSTEM\Setup'
        if ($setup.SystemSetupInProgress -ne 0 -or $setup.OOBEInProgress -ne 0) {
            throw 'Windows の初回セットアップが終わっていません。'
        }
        $folder = Join-Path $env:LOCALAPPDATA 'InfoHiveStage2'
        New-Item -ItemType Directory -Path $folder -Force | Out-Null
        Join-Path $folder 'Claude.msix'
    }
    $answerIso = Join-Path $root 'windows-answer.iso'
    $setupIso = Join-Path $root 'windows-setup.iso'
    foreach ($dvd in Get-VMDvdDrive -VM $vm) {
        if ($dvd.Path -in $answerIso, $setupIso) {
            Set-VMDvdDrive -VMDvdDrive $dvd -Path $null
        }
    }
    if (Test-Path -LiteralPath $answerIso) { Remove-Item -LiteralPath $answerIso }
    Copy-Item -LiteralPath $package -Destination $target -ToSession $session
    $baseline = Invoke-Command -Session $session -ArgumentList $target -ScriptBlock {
        param($packagePath)
        $ErrorActionPreference = 'Stop'
        try {
            $app = Get-AppxPackage -Name Claude
            if (-not $app) {
                Add-AppxPackage -Path $packagePath
                $app = Get-AppxPackage -Name Claude
            }
        } finally {
            Remove-Item -LiteralPath $packagePath
        }
        if (-not $app) { throw 'Claude Desktop が検証ユーザーに登録されていません。' }
        $os = Get-CimInstance Win32_OperatingSystem
        $displayVersion = (Get-ItemProperty 'HKLM:\SOFTWARE\Microsoft\Windows NT\CurrentVersion').DisplayVersion
        [ordered]@{
            windows = $os.Caption
            display_version = $displayVersion
            build = $os.BuildNumber
            claude_package_version = $app.Version.ToString()
            git = @(Get-Command git.exe -ErrorAction SilentlyContinue | Select-Object -ExpandProperty Source)
            uv = @(Get-Command uv.exe -ErrorAction SilentlyContinue | Select-Object -ExpandProperty Source)
            python = @(Get-Command python.exe -ErrorAction SilentlyContinue | Select-Object -ExpandProperty Source)
            ssh_directory = Test-Path -LiteralPath (Join-Path $env:USERPROFILE '.ssh')
            vc_runtime_dlls = @('vcruntime140.dll','vcruntime140_1.dll','msvcp140.dll' | ForEach-Object {
                @{ name = $_; exists = Test-Path -LiteralPath (Join-Path $env:SystemRoot "System32\$_") }
            })
            virtual_machine_platform = (Get-WindowsOptionalFeature -Online -FeatureName VirtualMachinePlatform).State.ToString()
        } | ConvertTo-Json -Depth 5
    }
    # PowerShell Direct は非対話セッションなので、ログオン済みユーザー側で起動する。
    Invoke-Command -Session $session -ScriptBlock {
        $ErrorActionPreference = 'Stop'
        $app = Get-AppxPackage -Name Claude
        $shellPath = "shell:AppsFolder\$($app.PackageFamilyName)!Claude"
        $action = New-ScheduledTaskAction -Execute 'explorer.exe' -Argument $shellPath
        $principal = New-ScheduledTaskPrincipal -UserId ([Security.Principal.WindowsIdentity]::GetCurrent().Name) -LogonType Interactive
        $taskName = 'InfoHiveStage2-OpenClaude-' + [guid]::NewGuid().ToString('N')
        Register-ScheduledTask -TaskName $taskName -Action $action -Principal $principal | Out-Null
        try {
            Start-ScheduledTask -TaskName $taskName
            $deadline = [datetime]::UtcNow.AddSeconds(90)
            do {
                if (Get-Process -Name Claude -ErrorAction SilentlyContinue | Where-Object SessionId -gt 0) { return }
                Start-Sleep -Seconds 3
            } while ([datetime]::UtcNow -lt $deadline)
            throw 'Claude Desktop を対話セッションで起動できませんでした。'
        } finally {
            Unregister-ScheduledTask -TaskName $taskName -Confirm:$false
        }
    }
    New-Item -ItemType Directory -Path $RecordDirectory -Force | Out-Null
    [IO.File]::WriteAllText($record, [string]$baseline, [Text.UTF8Encoding]::new($false))
    Get-Content -LiteralPath $record -Encoding UTF8
} finally {
    Remove-PSSession -Session $session
}
