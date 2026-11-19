param(
    [Parameter(Mandatory=$true)][int]$BrowserProcessId,
    [Parameter(Mandatory=$true)][string]$RunId,
    [Parameter(Mandatory=$true)][string]$ControlFile,
    [Parameter(Mandatory=$true)][string]$StopFile,
    [Parameter(Mandatory=$true)][string]$OutputFile,
    [Parameter(Mandatory=$true)][string]$ReadyFile,
    [switch]$IncludeProcessRows,
    [switch]$IncludeSystemCommit,
    [ValidateRange(50, 60000)][int]$IntervalMs = 500
)
$ErrorActionPreference = 'Stop'
[Console]::OutputEncoding = [System.Text.UTF8Encoding]::new($false)
$samples = [System.Collections.Generic.List[object]]::new()
$timer = [System.Diagnostics.Stopwatch]::StartNew()
$utf8 = [System.Text.UTF8Encoding]::new($false)
$samplerProcess = [System.Diagnostics.Process]::GetCurrentProcess()
if ($IncludeSystemCommit) {
    Add-Type -TypeDefinition @'
using System;
using System.ComponentModel;
using System.Runtime.InteropServices;
public static class WindowsCommit {
    [StructLayout(LayoutKind.Sequential)]
    struct Information {
        public uint Size;
        public UIntPtr CommitTotal, CommitLimit, CommitPeak, PhysicalTotal, PhysicalAvailable;
        public UIntPtr SystemCache, KernelTotal, KernelPaged, KernelNonpaged, PageSize;
        public uint Handles, Processes, Threads;
    }
    [DllImport("psapi.dll", SetLastError=true)]
    static extern bool GetPerformanceInfo(out Information value, uint size);
    public static long HeadroomBytes() {
        Information info;
        if (!GetPerformanceInfo(out info, (uint) Marshal.SizeOf(typeof(Information))))
            throw new Win32Exception(Marshal.GetLastWin32Error());
        return ((long) info.CommitLimit.ToUInt64() - (long) info.CommitTotal.ToUInt64()) * (long) info.PageSize.ToUInt64();
    }
}
'@
}
try {
    while (-not (Test-Path -LiteralPath $StopFile)) {
        $phaseBefore = Get-Content -LiteralPath $ControlFile -Raw -Encoding utf8 | ConvertFrom-Json
        $start = $timer.ElapsedMilliseconds
        $startUtc = [DateTimeOffset]::UtcNow.ToUnixTimeMilliseconds()
        # 自分が起動したブラウザの PID と子孫だけを集計する。
        $all = @(Get-CimInstance Win32_Process | Select-Object ProcessId,ParentProcessId)
        if ($all.Count -eq 0) { throw 'プロセスの一覧を取得できない' }
        if (-not ($all | Where-Object { [int]$_.ProcessId -eq $BrowserProcessId })) {
            if (Test-Path -LiteralPath $StopFile) { break }
            throw '対象のブラウザの PID がない'
        }
        $ids = [System.Collections.Generic.HashSet[int]]::new()
        [void]$ids.Add($BrowserProcessId)
        do {
            $changed = $false
            foreach ($entry in $all) {
                if ($ids.Contains([int]$entry.ParentProcessId) -and $ids.Add([int]$entry.ProcessId)) { $changed = $true }
            }
        } while ($changed)
        $processes = @(Get-Process -Id @($ids) -ErrorAction SilentlyContinue)
        if ($processes.Count -eq 0 -or -not ($processes | Where-Object { $_.Id -eq $BrowserProcessId })) {
            if (Test-Path -LiteralPath $StopFile) { break }
            throw '対象のブラウザのメモリを取得できない'
        }
        if ($IncludeProcessRows) {
            $processRows = @(foreach ($p in $processes) {
                $entry = $all | Where-Object { $_.ProcessId -eq $p.Id } | Select-Object -First 1
                [pscustomobject]@{
                    pid = $p.Id
                    parent_pid = [int]$entry.ParentProcessId
                    name = $p.ProcessName
                    private_bytes = [long]$p.PrivateMemorySize64
                    working_set_bytes = [long]$p.WorkingSet64
                }
            })
        }
        $phaseAfter = Get-Content -LiteralPath $ControlFile -Raw -Encoding utf8 | ConvertFrom-Json
        if ($phaseBefore.run_id -ne $RunId -or $phaseAfter.run_id -ne $RunId) { throw '実行 ID が一致しない' }
        $stable = $phaseBefore.revision -eq $phaseAfter.revision
        $samplerProcess.Refresh()
        $sample = [pscustomobject]@{
            run_id = $RunId
            root_pid = $BrowserProcessId
            sequence = $samples.Count + 1
            sampler_cpu_ms = $samplerProcess.TotalProcessorTime.TotalMilliseconds
            start_ms = $start
            elapsed_ms = $timer.ElapsedMilliseconds
            start_utc_ms = $startUtc
            utc_ms = [DateTimeOffset]::UtcNow.ToUnixTimeMilliseconds()
            case = $(if ($stable) { $phaseAfter.case } else { 'boundary' })
            phase = $(if ($stable) { $phaseAfter.phase } else { 'boundary' })
            revision = $phaseAfter.revision
            stable = $stable
            processes = $processes.Count
            process_ids = @($ids)
            observed_processes = $all.Count
            missing_children = @($ids | Where-Object { $_ -notin $processes.Id })
            process_names = @($processes | ForEach-Object ProcessName)
            private_bytes = [long](($processes | Measure-Object PrivateMemorySize64 -Sum).Sum)
            working_set_sum_bytes = [long](($processes | Measure-Object WorkingSet64 -Sum).Sum)
        }
        if ($IncludeProcessRows) {
            $sample | Add-Member -NotePropertyName process_rows -NotePropertyValue $processRows
            $sample.private_bytes = [long](($processRows | Measure-Object private_bytes -Sum).Sum)
            $sample.working_set_sum_bytes = [long](($processRows | Measure-Object working_set_bytes -Sum).Sum)
        }
        if ($IncludeSystemCommit) {
            $sample | Add-Member -NotePropertyName system_commit_headroom_bytes -NotePropertyValue ([WindowsCommit]::HeadroomBytes())
        }
        $samples.Add($sample)
        [System.IO.File]::WriteAllText($ReadyFile, (ConvertTo-Json -InputObject $sample -Compress -Depth 6), $utf8)
        Start-Sleep -Milliseconds $IntervalMs
    }
} finally {
    [System.IO.File]::WriteAllText($OutputFile, (ConvertTo-Json -InputObject @($samples) -Depth 6), $utf8)
    $samplerProcess.Dispose()
}
