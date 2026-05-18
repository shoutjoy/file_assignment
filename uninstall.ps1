#Requires -Version 5.1
$ErrorActionPreference = 'Stop'

$InstallDir = Join-Path $env:LOCALAPPDATA 'Programs\FileAssignmentManager'
$MenuRoots = @(
    'HKCU:\Software\Classes\Directory\shell\FileAssignmentMgr'
    'HKCU:\Software\Classes\Directory\Background\shell\FileAssignmentMgr'
)

foreach ($MenuRoot in $MenuRoots) {
    if (Test-Path $MenuRoot) {
        Remove-Item -Path $MenuRoot -Recurse -Force
    }
}

$Programs = [Environment]::GetFolderPath('Programs')
foreach ($name in @('FileAssignmentManager.lnk', 'FileAssignmentManager (완료 후 종료).lnk')) {
    $ShortcutPath = Join-Path $Programs $name
    if (Test-Path $ShortcutPath) {
        Remove-Item -Path $ShortcutPath -Force
    }
}

if (Test-Path $InstallDir) {
    Remove-Item -Path $InstallDir -Recurse -Force
}

Write-Host '[완료] 제거되었습니다.' -ForegroundColor Green
