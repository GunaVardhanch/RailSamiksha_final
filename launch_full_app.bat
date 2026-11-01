@echo off
title RailSamiksha AI - Enterprise Drone Defect Platform
cd /d "%~dp0"

echo =====================================================================
echo    🚆 RailSamiksha AI — Autonomous Aerial Track Inspection Platform
echo    • Backend & RT-DETR-L Model (55.3%% Accuracy + SAHI)
echo    • Indian Railways TMS Relational SQL Database (SQLite 3)
echo    • Full-Stack Unified Server: http://localhost:8000
echo =====================================================================
echo.
echo Launching server and opening browser at http://localhost:8000 ...
echo.

start "" http://localhost:8000

if exist ".venv\Scripts\python.exe" (
    ".venv\Scripts\python.exe" backend\run_server.py
) else (
    python backend\run_server.py
)

pause

