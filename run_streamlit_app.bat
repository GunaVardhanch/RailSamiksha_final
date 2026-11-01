@echo off
title RailSamiksha AI — Streamlit Aerospace Dashboard Launcher
echo ======================================================================
echo 🚆 RailSamiksha AI — Streamlit Community Dashboard Launcher
echo ======================================================================
echo.

cd /d "%~dp0"

REM Activate virtual environment if present
if exist ".venv\Scripts\activate.bat" (
    call .venv\Scripts\activate.bat
)

echo Starting Streamlit app on port 8501...
start "" http://localhost:8501
streamlit run app.py --server.port 8501 --server.headless false

pause
