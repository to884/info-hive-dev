# 試験専用 WinPE ISO を使い、作成した VM だけを止めて同じ世代の VHDX を復元する。
param(
    [Parameter(Mandatory)][string]$Base,
    [string]$BackupRoot,
    [switch]$QueuedOnly
)
$ErrorActionPreference='Stop'
Add-Type -TypeDefinition @"
using System; using System.Collections.Generic; using System.Text;
public static class HitestFrame {
    static int At(byte[] b, int x, int y) { int j=4+2*(640*y+x); return b[j] + (b[j+1]<<8); }
    public static string Read(byte[] b) {
        // WinPE 10.0.26100.32230 の既定の配色を 640×480 の RGB565 として取得する。
        const int magenta=0xb013;
        if(b==null || b.Length!=614404) return null;
        for(int y=20;y<280;y++) for(int x=0;x<630;x++) {
            if(At(b,x,y)!=magenta || (x>0 && At(b,x-1,y)==magenta)) continue;
            int end=x+1; while(end<640 && At(b,end,y)==magenta) end++;
            double dx=Math.Round((end-x)/4.0); if(dx<5 || dx>12 || x+70*dx>=640) continue;
            var palette=new Dictionary<int,int>();
            for(int color=0;color<16;color++) {
                int key=At(b,x+(int)((6+4*color)*dx),y);
                if(palette.ContainsKey(key)) break;
                palette[key]=color;
            }
            if(palette.Count!=16) continue;
            int upper=y; int sx=x+(int)(dx/2);
            while(upper>0 && At(b,sx,upper-1)==magenta) upper--;
            int lower=y; while(lower<upper+25 && At(b,sx,lower)!=0x66ba) lower++;
            int dy=lower-upper; if(dy<8 || dy>28 || upper+20*dy>480) continue;
            int cyan=At(b,sx,lower+dy/2);
            if(!palette.ContainsKey(cyan) || palette[cyan]!=11) continue;
            var payload=new List<byte>();
            for(int row=1;row<20;row++) for(int col=1;col<69;col+=2) {
                int ya=upper+row*dy+dy/2;
                int a=At(b,x+(int)((col+0.5)*dx),ya);
                int c=At(b,x+(int)((col+1.5)*dx),ya);
                if(!palette.ContainsKey(a)||!palette.ContainsKey(c)) return null;
                int n=(palette[a]<<4)|palette[c];
                if(n==0) return Encoding.ASCII.GetString(payload.ToArray());
                payload.Add((byte)n);
            }
        }
        return null;
    }
}
"@
$Base=(Resolve-Path -LiteralPath $Base).Path
if(!$QueuedOnly){
    if(!$BackupRoot){throw 'イメージ復元試験には -BackupRoot が必要です。'}
    $BackupRoot=(Resolve-Path -LiteralPath $BackupRoot).Path
    $workPartition=Get-Partition -DriveLetter $Base.Substring(0,1)
    $backupPartition=Get-Partition -DriveLetter $BackupRoot.Substring(0,1)
    if($workPartition.DiskNumber -eq $backupPartition.DiskNumber){
        throw '作業先とバックアップ先には別の物理ディスクを指定してください。'
    }
}
$tag=[guid]::NewGuid().ToString('N').Substring(0,10)
$name="info-hive-ntfs-power-$tag"
$disk=Join-Path $Base "power-data-$tag.vhdx"
$iso=Join-Path $Base 'ih-winpe.iso'
if(!(Test-Path -LiteralPath $iso -PathType Leaf)){
    throw '作業ディレクトリに試験専用の ih-winpe.iso を用意してください。'
}
$events=[System.Collections.Generic.List[object]]::new()
$overall=[Diagnostics.Stopwatch]::StartNew()
$cutAt=@{}
$expected=if($QueuedOnly){@('save_queued','save_queued','save_queued')}else{@('save_queued','after_journal','pointer_written')}
$verified=[System.Collections.Generic.List[object]]::new()
$output=Join-Path $Base 'vm-evidence.json'
$owned=$null
$ns='root/virtualization/v2'
$svc=Get-CimInstance -Namespace $ns -ClassName Msvm_VirtualSystemManagementService
function Owned-VM {
    $guest=Get-VM -Id $owned.Id
    $drives=@(Get-VMHardDiskDrive -VM $guest)
    if($guest.Name -ne $name -or $drives.Count -ne 1 -or $drives[0].Path -ne $disk){throw '試験 VM の ID とディスクが一致しません。'}
    $guest
}
function Receive-Guest {
    $last=''
    $deadline=$overall.Elapsed.TotalSeconds+260
    do {
        $r=Invoke-CimMethod -InputObject $svc -MethodName GetVirtualSystemThumbnailImage -Arguments @{
            TargetSystem=$system; WidthPixels=[uint16]640; HeightPixels=[uint16]480
        }
        if($r.ReturnValue -eq 0){
            $line=[HitestFrame]::Read([byte[]]$r.ImageData)
            if($line -and $line -ne $last){
                $last=$line
                $now=$overall.Elapsed.TotalSeconds
                $events.Add([ordered]@{at_s=[math]::Round($now,4);text=$line})
                Write-Host $line
                if($line -match '^ERROR '){throw $line}
                if($line -match '^VERIFIED (.*)$'){
                    $result=$Matches[1] | ConvertFrom-Json
                    $point=$result.point
                    $verified.Add($result)
                    $events.Add([ordered]@{point=$point;host_off_to_verified_s=[math]::Round($now-$cutAt[$point],4)})
                }
                if($line -match '^(BASE|CUT|IMAGE|DONE) '){return $line}
            }
        }
        Start-Sleep -Milliseconds 150
    }while($overall.Elapsed.TotalSeconds -lt $deadline)
    throw 'ゲストの画面に試験の結果が表示されません。'
}
try {
    New-VHD -Path $disk -Dynamic -SizeBytes 8GB | Out-Null
    [IO.Directory]::CreateDirectory((Join-Path $Base 'vm')) | Out-Null
    $owned=New-VM -Name $name -Generation 1 -MemoryStartupBytes 5GB -Path (Join-Path $Base 'vm') -NoVHD
    Set-VM -VM $owned -ProcessorCount 3 -AutomaticCheckpointsEnabled $false -AutomaticStartAction Nothing
    Get-VMNetworkAdapter -VM $owned | Remove-VMNetworkAdapter
    Add-VMHardDiskDrive -VM $owned -ControllerType IDE -ControllerNumber 0 -ControllerLocation 0 -Path $disk
    $dvd=Get-VMDvdDrive -VM $owned
    if($dvd){$dvd | Set-VMDvdDrive -Path $iso}else{Add-VMDvdDrive -VM $owned -ControllerNumber 1 -ControllerLocation 0 -Path $iso}
    Set-VMBios -VM $owned -StartupOrder @('CD','IDE','LegacyNetworkAdapter','Floppy')
    $filter='Name=' + [char]39 + $owned.Id + [char]39
    $system=Get-CimInstance -Namespace $ns -ClassName Msvm_ComputerSystem -Filter $filter
    Start-VM -VM (Owned-VM)
    if((Receive-Guest) -notmatch '^BASE '){throw 'ゲストの初期状態を確認できません。'}
    $until=$overall.Elapsed.TotalSeconds+60
    while((Owned-VM).State -ne 'Off' -and $overall.Elapsed.TotalSeconds -lt $until){Start-Sleep -Milliseconds 200}
    if((Owned-VM).State -ne 'Off'){throw '初期状態の正常終了を確認できません。'}
    foreach($point in $expected) {
        Start-VM -VM (Owned-VM)
        $line=Receive-Guest
        if($line -notmatch '^CUT (.*)$' -or ($Matches[1] | ConvertFrom-Json).point -ne $point){throw 'ゲストが想定外の停止位置を示しました。'}
        $cutAt[$point]=$overall.Elapsed.TotalSeconds
        Stop-VM -VM (Owned-VM) -TurnOff -Confirm:$false
        $events.Add([ordered]@{at_s=[math]::Round($overall.Elapsed.TotalSeconds,4);off=$point})
    }
    Start-VM -VM (Owned-VM)
    $line=Receive-Guest
    if($verified.Count -ne $expected.Count -or @($verified | Where-Object { !$_.approved_replayed }).Count -ne 0){
        throw '3件すべての保留保存を再試行できたことを確認できません。'
    }
    if($QueuedOnly){
        if($line -notmatch '^DONE (.*)$' -or ($Matches[1] | ConvertFrom-Json).verified -ne $expected.Count -or
           ($verified.operation -join ',') -ne 'query,ingest,learn' -or
           @($verified.plan_id | Sort-Object -Unique).Count -ne $expected.Count){
            throw '3件すべての保留保存を再試行できたことを確認できません。'
        }
        [ordered]@{
            guest='Hyper-V generation 1 Windows PE 10.0.26100.32230'; guest_data='dedicated NTFS VHDX on NVMe'
            events=$events; verified=$verified; delays_s=@($events | Where-Object { $_.Contains('host_off_to_verified_s') } |
                ForEach-Object { $_.host_off_to_verified_s })
        } | ConvertTo-Json -Depth 15 | Set-Content -LiteralPath $output -Encoding utf8
        return
    }
    if($line -notmatch '^IMAGE (.*)$'){throw 'ゲストがバックアップ試験の位置に達していません。'}
    $backupWatch=[Diagnostics.Stopwatch]::StartNew()
    $guest=Owned-VM
    while($guest.State -ne 'Off' -and $backupWatch.Elapsed.TotalSeconds -lt 60){
        Start-Sleep -Milliseconds 300
        $guest=Owned-VM
    }
    if($guest.State -ne 'Off'){throw 'ゲストを正常終了してからバックアップしてください。'}
    $backup=Join-Path $BackupRoot "ih-power-image-$tag.vhdx"
    $restored=Join-Path $Base "power-restored-$tag.vhdx"
    if((Test-Path -LiteralPath $backup) -or (Test-Path -LiteralPath $restored)){throw 'バックアップ先または復元先が既にあります。'}
    $fileWatch=[Diagnostics.Stopwatch]::StartNew()
    Copy-Item -LiteralPath $disk -Destination $backup
    if((Get-FileHash -LiteralPath $disk).Hash -ne (Get-FileHash -LiteralPath $backup).Hash){throw 'バックアップのハッシュが一致しません。'}
    $backupSeconds=[math]::Round($fileWatch.Elapsed.TotalSeconds,4)
    $restoreWatch=[Diagnostics.Stopwatch]::StartNew()
    Copy-Item -LiteralPath $backup -Destination $restored
    if((Get-FileHash -LiteralPath $backup).Hash -ne (Get-FileHash -LiteralPath $restored).Hash){throw '復元したイメージのハッシュが一致しません。'}
    $copySeconds=[math]::Round($restoreWatch.Elapsed.TotalSeconds,4)
    Get-VMHardDiskDrive -VM $guest | Remove-VMHardDiskDrive -Confirm:$false
    $disk=$restored
    Add-VMHardDiskDrive -VM $guest -ControllerType IDE -ControllerNumber 0 -ControllerLocation 0 -Path $disk
    Start-VM -VM (Owned-VM)
    $line=Receive-Guest
    if($line -notmatch '^IMAGE (.*)$'){throw 'ゲストがイメージの復元を確認できません。'}
    $status=$Matches[1] | ConvertFrom-Json
    [ordered]@{
        guest='Hyper-V generation 1 Windows PE 10.0.26100.32230'; guest_data='dedicated NTFS VHDX on NVMe'
        events=$events; backup_vhdx_bytes=(Get-Item -LiteralPath $backup).Length
        backup_copy_and_hash_s=$backupSeconds; restore_copy_and_hash_s=$copySeconds
        restore_to_verified_s=[math]::Round($restoreWatch.Elapsed.TotalSeconds,4); restored_image=$status
    } | ConvertTo-Json -Depth 15 | Set-Content -LiteralPath $output -Encoding utf8
} catch {
    [ordered]@{events=$events;error=$_.Exception.Message} | ConvertTo-Json -Depth 15 | Set-Content -LiteralPath (Join-Path $Base "vm-incomplete-$tag.json") -Encoding utf8
    throw
} finally {
    if($owned){
        $guest=Get-VM -Id $owned.Id -ErrorAction SilentlyContinue
        if($guest -and $guest.Name -eq $name){
            if($guest.State -ne 'Off'){Stop-VM -VM $guest -TurnOff -Confirm:$false}
            $target=Get-CimInstance -Namespace $ns -ClassName Msvm_ComputerSystem -Filter ('Name=' + [char]39 + $guest.Id + [char]39)
            Invoke-CimMethod -InputObject $svc -MethodName DestroySystem -Arguments @{AffectedSystem=$target} | Out-Null
        }
    }
}
