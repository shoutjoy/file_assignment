@echo off
chcp 65001 >nul
title FileAssignmentManager EXE 빌드
cd /d "%~dp0"

python -m pip install -r "%~dp0requirements-build.txt" --quiet
if errorlevel 1 (
    echo [오류] pip 설치에 실패했습니다.
    pause
    exit /b 1
)

python -c "from tk_runtime import stage_tcl_tk; import sys; stage_tcl_tk(sys.argv[1])" "%~dp0build\tcl_runtime"
if errorlevel 1 (
    echo [오류] Python의 Tcl/Tk 파일을 준비할 수 없습니다.
    pause
    exit /b 1
)
set "TCL_LIBRARY=%~dp0build\tcl_runtime\tcl8.6"
set "TK_LIBRARY=%~dp0build\tcl_runtime\tk8.6"
python -c "import tkinter as tk; root=tk.Tk(); root.destroy()"
if errorlevel 1 (
    echo [오류] Tcl/Tk 초기화에 실패했습니다. 실행 파일을 빌드하지 않습니다.
    pause
    exit /b 1
)

python -m PyInstaller --noconfirm --clean --workpath "%~dp0build\pyi_work" "%~dp0FileAssignmentManager.spec"
if errorlevel 1 (
    echo [오류] PyInstaller 빌드에 실패했습니다.
    pause
    exit /b 1
)

echo.
echo [완료] dist\FileAssignmentManager.exe
pause
