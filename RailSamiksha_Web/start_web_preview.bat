@echo off
title RailSamiksha AI - Web Frontend Preview
cd /d "%~dp0"

echo =====================================================================
echo    🚆 RailSamiksha AI - Web Frontend Local Server
echo    Hosting on http://localhost:3000 ...
echo =====================================================================
echo.
echo Opening browser...
start "" http://localhost:3000

if exist "..\.venv\Scripts\python.exe" (
    "..\.venv\Scripts\python.exe" -m http.server 3000
) else (
    python -m http.server 3000
)

pause

