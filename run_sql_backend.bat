@echo off
title RailSamiksha AI - SQL Backend REST Server
cd /d "%~dp0"

echo =====================================================================
echo    🚆 RailSamiksha AI - SQL Database & REST Backend Server
echo    Hosting on http://localhost:8000 ...
echo =====================================================================
echo.

if exist ".venv\Scripts\python.exe" (
    ".venv\Scripts\python.exe" database\api_server.py
) else (
    python database\api_server.py
)

pause
