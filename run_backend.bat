@echo off
title RailSamiksha AI - Full-Stack Backend & RT-DETR-L Server
cd /d "%~dp0"

echo =====================================================================
echo    🚆 RailSamiksha AI - Full-Stack Backend & AI Inference Server
echo    Hosting on http://localhost:8000 ...
echo =====================================================================
echo.

if exist ".venv\Scripts\python.exe" (
    ".venv\Scripts\python.exe" backend\run_server.py
) else (
    python backend\run_server.py
)

pause
