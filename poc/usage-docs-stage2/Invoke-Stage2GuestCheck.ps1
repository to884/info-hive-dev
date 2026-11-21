#Requires -Version 7.0
[CmdletBinding()]
param(
    [Parameter(Mandatory)] [string] $VmName,
    [Parameter(Mandatory)] [string] $StageRoot,
    [Parameter(Mandatory)] [string] $CheckScript,
    [Parameter(Mandatory)] [string] $RecordPath,
    [ValidateRange(10, 3600)] [int] $TimeoutSeconds = 900,
    [switch] $Elevated
)

$ErrorActionPreference = 'Stop'
$root = (Get-Item -LiteralPath $StageRoot).FullName
$vmMatches = @(Get-VM | Where-Object Name -eq $VmName)
if ($vmMatches.Count -ne 1) { throw '指定した名前の VM を 1 台に特定できません。' }
$vm = $vmMatches[0]
$disks = @(Get-VMHardDiskDrive -VM $vm)
if ($disks.Count -ne 1 -or -not $disks[0].Path) {
    throw '検証用 VM の VHDX を 1 本に特定できません。'
}
$baseDisk = Get-VHD -Path $disks[0].Path
while ($baseDisk.ParentPath) {
    $baseDisk = Get-VHD -Path $baseDisk.ParentPath
}
if ($baseDisk.Path -ne (Join-Path $root 'windows.vhdx')) {
    throw '指定された作業場所にある検証用 VM のみ操作できます。'
}
if (Test-Path -LiteralPath $RecordPath) { throw '既存の検証記録を上書きできません。' }
$null = Get-Item -LiteralPath (Split-Path -Parent $RecordPath)
$scriptText = [IO.File]::ReadAllText((Get-Item -LiteralPath $CheckScript).FullName, [Text.Encoding]::UTF8)
$credential = Import-Clixml -LiteralPath (Join-Path $root 'guest.credential.xml')
$session = New-PSSession -VMId $vm.Id -Credential $credential
$taskName = 'InfoHiveStage2-' + [guid]::NewGuid().ToString('N')
$runLevel = if ($Elevated) { 'Highest' } else { 'Limited' }

try {
    $jobDir = Invoke-Command -Session $session -ArgumentList $taskName, $runLevel, $scriptText -ScriptBlock {
        param($name, $level, $scriptText)
        $ErrorActionPreference = 'Stop'
        $dir = Join-Path $env:LOCALAPPDATA "InfoHiveStage2\$name"
        New-Item -ItemType Directory -Path $dir | Out-Null
        $checkPath = Join-Path $dir 'check.ps1'
        [IO.File]::WriteAllText($checkPath, $scriptText, [Text.UTF8Encoding]::new($true))
        $entryPath = Join-Path $dir 'run.ps1'
        $entry = @'
$ErrorActionPreference = 'Stop'
$env:PYTHONUTF8 = '1'
[Console]::OutputEncoding = [Text.UTF8Encoding]::new($false)
$OutputEncoding = [Console]::OutputEncoding
$utf8 = [Text.UTF8Encoding]::new($false)
$logPath = Join-Path $PSScriptRoot 'result.txt'
$sessionId = (Get-Process -Id $PID).SessionId
$identity = [Security.Principal.WindowsIdentity]::GetCurrent()
$principal = [Security.Principal.WindowsPrincipal]::new($identity)
[IO.File]::WriteAllLines($logPath, [string[]]@(
    "time: $(Get-Date -Format o)"
    "session_id: $sessionId"
    "identity: $($identity.Name)"
    "computer_name: $env:COMPUTERNAME"
    "elevated: $($principal.IsInRole([Security.Principal.WindowsBuiltInRole]::Administrator))"
), $utf8)
$exitCode = 0
try {
    & (Join-Path $PSScriptRoot 'check.ps1') *>&1 | ForEach-Object {
        [IO.File]::AppendAllText($logPath, ($_ | Out-String -Width 320), $utf8)
    }
} catch {
    [IO.File]::AppendAllText($logPath, ($_ | Out-String -Width 320), $utf8)
    $exitCode = 1
} finally {
    [IO.File]::WriteAllText((Join-Path $PSScriptRoot 'exit.txt'), [string]$exitCode, $utf8)
}
exit $exitCode
'@
        [IO.File]::WriteAllText($entryPath, $entry, [Text.UTF8Encoding]::new($true))
        $exe = Join-Path $env:SystemRoot 'System32\WindowsPowerShell\v1.0\powershell.exe'
        $action = New-ScheduledTaskAction -Execute $exe -Argument ('-NoProfile -NonInteractive -WindowStyle Hidden -ExecutionPolicy Bypass -File "' + $entryPath + '"')
        $principal = New-ScheduledTaskPrincipal -UserId ([Security.Principal.WindowsIdentity]::GetCurrent().Name) -LogonType Interactive -RunLevel $level
        Register-ScheduledTask -TaskName $name -Action $action -Principal $principal | Out-Null
        Start-ScheduledTask -TaskName $name
        $dir
    }

    $deadline = [datetime]::UtcNow.AddSeconds($TimeoutSeconds)
    $timedOut = $false
    do {
        $result = Invoke-Command -Session $session -ArgumentList $jobDir -ScriptBlock {
            param($dir)
            $exitPath = Join-Path $dir 'exit.txt'
            if (Test-Path -LiteralPath $exitPath) { Get-Content -LiteralPath $exitPath -Encoding UTF8 }
        }
        if ($null -ne $result) { break }
        if ([datetime]::UtcNow -ge $deadline) {
            $timedOut = $true
            Invoke-Command -Session $session -ArgumentList $taskName -ScriptBlock {
                param($name)
                if ((Get-ScheduledTask -TaskName $name).State -eq 'Running') {
                    Stop-ScheduledTask -TaskName $name
                }
            }
            break
        }
        Start-Sleep -Seconds 3
    } while ($true)

    $guestLog = Join-Path $jobDir 'result.txt'
    if (Invoke-Command -Session $session -ArgumentList $guestLog -ScriptBlock {
        param($path)
        Test-Path -LiteralPath $path -PathType Leaf
    }) {
        Copy-Item -FromSession $session -LiteralPath $guestLog -Destination $RecordPath
    }
    Add-Content -LiteralPath $RecordPath -Encoding utf8 -Value @(
        "vm_id: $($vm.Id)"
        "parent_checkpoint: $($vm.ParentCheckpointName)"
        "timed_out: $timedOut"
    )
    Get-Content -LiteralPath $RecordPath -Encoding UTF8
    if ($timedOut) { throw "検証が時間内に終わりませんでした。記録は $RecordPath です。" }
    if ($result -ne '0') { throw "検証に失敗しました。記録は $RecordPath です。" }
} finally {
    Invoke-Command -Session $session -ArgumentList $taskName -ErrorAction SilentlyContinue -ScriptBlock {
        param($name)
        if ((Get-ScheduledTask -TaskName $name -ErrorAction SilentlyContinue).State -eq 'Running') {
            Stop-ScheduledTask -TaskName $name
        }
        Unregister-ScheduledTask -TaskName $name -Confirm:$false -ErrorAction SilentlyContinue
    }
    Remove-PSSession -Session $session
}
