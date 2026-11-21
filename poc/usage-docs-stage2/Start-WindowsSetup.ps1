#Requires -Version 7.0
[CmdletBinding()]
param(
    [Parameter(Mandatory)] [string] $VmName,
    [Parameter(Mandatory)] [string] $StageRoot,
    [Parameter(Mandatory)] [string] $WindowsMedia,
    [ValidateRange(1, 100)] [int] $ImageIndex = 1
)

$ErrorActionPreference = 'Stop'
$root = (Get-Item -LiteralPath $StageRoot).FullName
$vmMatches = @(Get-VM | Where-Object Name -eq $VmName)
if ($vmMatches.Count -ne 1) { throw '指定した名前の VM を 1 台に特定できません。' }
$vm = $vmMatches[0]
$disks = @(Get-VMHardDiskDrive -VM $vm)
$expectedDisk = Join-Path $root 'windows.vhdx'
if ($vm.State -ne 'Off' -or $vm.Generation -ne 2 -or $disks.Count -ne 1 -or
    $disks[0].Path -ne $expectedDisk -or @(Get-VMDvdDrive -VM $vm | Where-Object Path).Count) {
    throw '指定した作業場所に、起動前の検証専用 VM とその空の VHDX を用意してください。'
}
$vhd = Get-VHD -Path $expectedDisk
if ($vhd.FileSize -gt 16MB) {
    throw '使用済みの可能性がある VHDX に Windows Setup を起動できません。'
}
if ($vm.MemoryStartup -lt 4GB -or $vm.ProcessorCount -lt 2 -or $vhd.Size -lt 64GB -or
    $vm.AutomaticCheckpointsEnabled -or -not (Get-VMSecurity -VM $vm).TpmEnabled -or
    (Get-VMFirmware -VM $vm).SecureBoot -ne 'On') {
    throw 'Windows 11 の要件を満たし、自動チェックポイントを無効にした VM を用意してください。'
}

$media = (Get-Item -LiteralPath $WindowsMedia).FullName
$bootImage = Join-Path $media 'efi/microsoft/boot/efisys_noprompt.bin'
$windowsIso = Join-Path $root 'windows-setup.iso'
$answerIso = Join-Path $root 'windows-answer.iso'
$credentialPath = Join-Path $root 'guest.credential.xml'
if ((Test-Path -LiteralPath $answerIso) -or (Test-Path -LiteralPath $credentialPath) -or
    (Test-Path -LiteralPath $windowsIso)) {
    throw 'インストール媒体または資格情報が既にあります。前の実行状況を確認してください。'
}

# Windows が再起動したら VHDX を優先し、空のときだけ DVD を起動する。
$partialIso = Join-Path $root 'windows-setup.partial.iso'
& oscdimg '-m' '-u2' '-udfver102' "-bootdata:1#pEF,e,b$bootImage" $media $partialIso
if ($LASTEXITCODE -ne 0) { throw 'Windows Setup の ISO を作成できませんでした。' }
Move-Item -LiteralPath $partialIso -Destination $windowsIso

# 答えファイルには一時資格情報を含む。作業場所のアクセスは事前に制限する。
$answerSource = Join-Path $root 'answer-media'
New-Item -ItemType Directory -Path $answerSource | Out-Null
$account = 'Stage2Runner'
$computerName = 'INFOHIVE-STAGE2'
$password = 'Aa!' + [Convert]::ToHexString([Security.Cryptography.RandomNumberGenerator]::GetBytes(24))
$credential = [pscredential]::new("$computerName\$account", (ConvertTo-SecureString $password -AsPlainText -Force))
$credential | Export-Clixml -LiteralPath $credentialPath
$answer = @"
<?xml version="1.0" encoding="utf-8"?>
<unattend xmlns="urn:schemas-microsoft-com:unattend" xmlns:wcm="http://schemas.microsoft.com/WMIConfig/2002/State">
  <settings pass="windowsPE">
    <component name="Microsoft-Windows-International-Core-WinPE" processorArchitecture="amd64" publicKeyToken="31bf3856ad364e35" language="neutral" versionScope="nonSxS">
      <SetupUILanguage><UILanguage>ja-JP</UILanguage></SetupUILanguage>
      <InputLocale>ja-JP</InputLocale><SystemLocale>ja-JP</SystemLocale><UILanguage>ja-JP</UILanguage><UserLocale>ja-JP</UserLocale>
    </component>
    <component name="Microsoft-Windows-Setup" processorArchitecture="amd64" publicKeyToken="31bf3856ad364e35" language="neutral" versionScope="nonSxS">
      <DiskConfiguration>
        <Disk wcm:action="add">
          <DiskID>0</DiskID><WillWipeDisk>false</WillWipeDisk>
          <CreatePartitions>
            <CreatePartition wcm:action="add"><Order>1</Order><Size>260</Size><Type>EFI</Type></CreatePartition>
            <CreatePartition wcm:action="add"><Order>2</Order><Size>16</Size><Type>MSR</Type></CreatePartition>
            <CreatePartition wcm:action="add"><Order>3</Order><Size>1024</Size><Type>Primary</Type></CreatePartition>
            <CreatePartition wcm:action="add"><Order>4</Order><Extend>true</Extend><Type>Primary</Type></CreatePartition>
          </CreatePartitions>
          <ModifyPartitions>
            <ModifyPartition wcm:action="add"><Order>1</Order><PartitionID>1</PartitionID><Format>FAT32</Format><Label>System</Label></ModifyPartition>
            <ModifyPartition wcm:action="add"><Order>2</Order><PartitionID>3</PartitionID><Format>NTFS</Format><Label>Recovery</Label><TypeID>de94bba4-06d1-4d40-a16a-bfd50179d6ac</TypeID></ModifyPartition>
            <ModifyPartition wcm:action="add"><Order>3</Order><PartitionID>4</PartitionID><Format>NTFS</Format><Label>Windows</Label><Letter>C</Letter></ModifyPartition>
          </ModifyPartitions>
        </Disk>
        <WillShowUI>OnError</WillShowUI>
      </DiskConfiguration>
      <ImageInstall>
        <OSImage>
          <InstallFrom><MetaData wcm:action="add"><Key>/IMAGE/INDEX</Key><Value>$ImageIndex</Value></MetaData></InstallFrom>
          <InstallTo><DiskID>0</DiskID><PartitionID>4</PartitionID></InstallTo>
          <WillShowUI>OnError</WillShowUI>
        </OSImage>
      </ImageInstall>
      <UserData><AcceptEula>true</AcceptEula></UserData>
    </component>
  </settings>
  <settings pass="specialize">
    <component name="Microsoft-Windows-Shell-Setup" processorArchitecture="amd64" publicKeyToken="31bf3856ad364e35" language="neutral" versionScope="nonSxS">
      <ComputerName>$computerName</ComputerName><TimeZone>Tokyo Standard Time</TimeZone>
    </component>
  </settings>
  <settings pass="oobeSystem">
    <component name="Microsoft-Windows-International-Core" processorArchitecture="amd64" publicKeyToken="31bf3856ad364e35" language="neutral" versionScope="nonSxS">
      <InputLocale>ja-JP</InputLocale><SystemLocale>ja-JP</SystemLocale><UILanguage>ja-JP</UILanguage><UserLocale>ja-JP</UserLocale>
    </component>
    <component name="Microsoft-Windows-Shell-Setup" processorArchitecture="amd64" publicKeyToken="31bf3856ad364e35" language="neutral" versionScope="nonSxS">
      <OOBE><HideOnlineAccountScreens>true</HideOnlineAccountScreens><HideWirelessSetupInOOBE>true</HideWirelessSetupInOOBE><ProtectYourPC>1</ProtectYourPC></OOBE>
      <UserAccounts><LocalAccounts><LocalAccount wcm:action="add">
        <Password><Value>$password</Value><PlainText>true</PlainText></Password>
        <Name>$account</Name><Group>Administrators</Group>
      </LocalAccount></LocalAccounts></UserAccounts>
      <AutoLogon>
        <Password><Value>$password</Value><PlainText>true</PlainText></Password>
        <Enabled>true</Enabled><LogonCount>2</LogonCount><Username>$account</Username>
      </AutoLogon>
    </component>
  </settings>
</unattend>
"@
$null = [xml]$answer
$answerPath = Join-Path $answerSource 'Autounattend.xml'
[IO.File]::WriteAllText($answerPath, $answer, [Text.UTF8Encoding]::new($false))
try {
    & oscdimg '-u2' '-udfver102' '-lSTAGE2_ANSWER' $answerSource $answerIso
    if ($LASTEXITCODE -ne 0) { throw 'Windows Setup の答えファイル ISO を作成できませんでした。' }
} finally {
    Remove-Item -LiteralPath $answerPath
}

$setupDvd = Add-VMDvdDrive -VM $vm -Path $windowsIso -Passthru
$null = Add-VMDvdDrive -VM $vm -Path $answerIso -Passthru
Set-VMFirmware -VM $vm -BootOrder $disks[0], $setupDvd
Start-VM -VM $vm
