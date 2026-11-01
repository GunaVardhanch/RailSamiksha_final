@echo off
title RailSamiksha AI - AeroInspect RT-DETR Platform
cd /d "%~dp0"

echo =====================================================================
echo    🚆 RailSamiksha AI - AeroInspect RT-DETR Platform Launcher
echo    Fine-Tuned RT-DETR-L ^| 4K SAHI ^| ByteTrack Tracking ^| RTK-GPS
echo =====================================================================
echo.
echo [INFO] Opening default browser at http://localhost:8501 ...
start "" http://localhost:8501

if exist "..\.venv\Scripts\python.exe" (
    echo [INFO] Launching with project virtual environment...
    "..\.venv\Scripts\python.exe" run_app.py
) else if exist ".venv\Scripts\python.exe" (
    echo [INFO] Launching with local virtual environment...
    ".venv\Scripts\python.exe" run_app.py
) else (
    echo [INFO] Launching with system Python...
    python run_app.py
)

pause
