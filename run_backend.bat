@echo off
title RailSamiksha AI - Full-Stack Backend & RT-DETR-L Server
cd /d "%~dp0"

echo =====================================================================
echo    🚆 RailSamiksha AI - Full-Stack Backend & AI Inference Server
echo    Hosting on http://localhost:8000 ...
echo =====================================================================
echo.
echo Opening browser at http://localhost:8000 ...
start "" http://localhost:8000

if exist ".venv\Scripts\python.exe" (
    ".venv\Scripts\python.exe" backend\run_server.py
) else if exist "%LOCALAPPDATA%\Python\bin\python.exe" (
    "%LOCALAPPDATA%\Python\bin\python.exe" backend\run_server.py
) else (
    python backend\run_server.py
)

pause
