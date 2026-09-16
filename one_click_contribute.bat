@echo off
title CyberDesk OSS Auto-Contribute Engine
color 0b
cls
echo =====================================================================
echo    CYBERDESK // AUTONOMOUS 1-CLICK OPEN-SOURCE CONTRIBUTION ENGINE
echo =====================================================================
echo.
echo [*] Initializing GitHub Credential Bridge for @pruthvi828...
echo [*] Scouting unassigned open-source targets...
echo [*] Applying verified patch and dispatching upstream PR...
echo.
python "%~dp0backend\auto_pr_engine.py"
echo.
echo =====================================================================
echo [*] Execution completed. Press any key to exit.
echo =====================================================================
pause >nul
