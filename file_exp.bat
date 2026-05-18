@echo off
title 과제 통합 프로그램 실행기
cd /d "%~dp0"

if not exist "file_assignment_manager.py" (
    echo [오류] file_assignment_manager.py 를 찾을 수 없습니다.
    pause
    exit /b 1
)

python "%~dp0file_assignment_manager.py" %*
if %errorlevel% neq 0 (
    echo.
    echo [알림] 오류 코드: %errorlevel%
    pause
)
