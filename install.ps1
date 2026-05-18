#Requires -Version 5.1
# FileAssignmentManager: 사용자 폴더에 복사하고 탐색기 폴더 우클릭 메뉴에 등록합니다.
$ErrorActionPreference = 'Stop'

function Get-PythonExecutable {
    $pythonCmd = Get-Command python -ErrorAction SilentlyContinue
    if ($pythonCmd) { return $pythonCmd.Source }
    $pyCmd = Get-Command py -ErrorAction SilentlyContinue
    if ($pyCmd) {
        $out = & py -3 -c "import sys; print(sys.executable)" 2>$null
        if ($LASTEXITCODE -eq 0 -and $out) { return $out.Trim() }
    }
    return $null
}

$SourceRoot = Split-Path -Parent $MyInvocation.MyCommand.Path
$InstallDir = Join-Path $env:LOCALAPPDATA 'Programs\FileAssignmentManager'
$PythonExe = Get-PythonExecutable

if (-not $PythonExe) {
    Write-Host '[오류] Python을 찾을 수 없습니다.' -ForegroundColor Red
    exit 1
}

Write-Host "설치 위치: $InstallDir" -ForegroundColor Cyan
Write-Host "Python: $PythonExe" -ForegroundColor Gray

New-Item -ItemType Directory -Force -Path $InstallDir | Out-Null
Copy-Item (Join-Path $SourceRoot 'file_assignment_manager.py') -Destination $InstallDir -Force
Copy-Item (Join-Path $SourceRoot 'FileAssignmentManager.bat') -Destination $InstallDir -Force

$ScriptPath = Join-Path $InstallDir 'file_assignment_manager.py'
$CommandOnFolder = "`"$PythonExe`" `"$ScriptPath`" `"%1`""
$CommandInFolder = "`"$PythonExe`" `"$ScriptPath`" `"%V`""

$MenuLabel = '과제 통합 및 명단 추출'

$Pairs = @(
    @{ Root = 'HKCU:\Software\Classes\Directory\shell\FileAssignmentMgr'; Command = $CommandOnFolder }
    @{ Root = 'HKCU:\Software\Classes\Directory\Background\shell\FileAssignmentMgr'; Command = $CommandInFolder }
)

foreach ($p in $Pairs) {
    $MenuRoot = $p.Root
    $MenuCmd = Join-Path $MenuRoot 'command'
    if (-not (Test-Path $MenuRoot)) { New-Item -Path $MenuRoot -Force | Out-Null }
    Set-ItemProperty -Path $MenuRoot -Name '(default)' -Value $MenuLabel -Type String
    Set-ItemProperty -Path $MenuRoot -Name 'Icon' -Value $PythonExe -Type String
    if (-not (Test-Path $MenuCmd)) { New-Item -Path $MenuCmd -Force | Out-Null }
    Set-ItemProperty -Path $MenuCmd -Name '(default)' -Value $p.Command -Type String
}

$Programs = [Environment]::GetFolderPath('Programs')
$Shell = New-Object -ComObject WScript.Shell

$ScKeep = $Shell.CreateShortcut((Join-Path $Programs 'FileAssignmentManager.lnk'))
$ScKeep.TargetPath = $PythonExe
$ScKeep.Arguments = "`"$ScriptPath`" --keep-open"
$ScKeep.WorkingDirectory = $InstallDir
$ScKeep.Description = '과제 통합 · 완료 후 창 유지'
$ScKeep.Save()

$ScClose = $Shell.CreateShortcut((Join-Path $Programs 'FileAssignmentManager (완료 후 종료).lnk'))
$ScClose.TargetPath = $PythonExe
$ScClose.Arguments = "`"$ScriptPath`" --close-after-run"
$ScClose.WorkingDirectory = $InstallDir
$ScClose.Description = '과제 통합 · 통합 완료 후 종료'
$ScClose.Save()

Write-Host ''
Write-Host '[완료] 설치되었습니다.' -ForegroundColor Green
