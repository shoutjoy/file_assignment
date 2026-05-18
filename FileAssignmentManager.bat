@echo off
chcp 65001 >nul
title 과제 통합 및 명단 추출
cd /d "%~dp0"

where python >nul 2>&1
if %errorlevel% neq 0 (
    echo [오류] Python이 PATH에 없습니다. python.org 에서 설치하세요.
    pause
    exit /b 1
)

python "%~dp0file_assignment_manager.py" %*
if %errorlevel% neq 0 (
    echo.
    echo [경고] 비정상 종료 ^(코드 %errorlevel%^)
    pause
)
