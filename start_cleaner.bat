@echo off
title Phone Clean & Safe Backup Studio
echo ===================================================
echo   Starting Phone Clean & Safe Backup Studio...
echo ===================================================
echo.

:: Check Python
python --version >nul 2>&1
if %errorlevel% neq 0 (
    echo [ERROR] Python is not installed or not in PATH!
    pause
    exit /b
)

:: Start browser after brief delay
start "" http://127.0.0.1:8484

:: Run FastAPI server
python backend\app.py
pause
