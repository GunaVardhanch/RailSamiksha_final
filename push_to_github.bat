@echo off
title Push RailSamiksha to GitHub (RailSamiksha_final)
echo ======================================================================
echo 🚀 Pushing RailSamiksha to: GunaVardhanch/RailSamiksha_final
echo ======================================================================
echo.

cd /d "%~dp0"

echo Ensuring active branch is 'main'...
git branch -M main

echo.
echo Pushing codebase to remote origin (https://github.com/GunaVardhanch/RailSamiksha_final.git)...
git push -u origin main

echo.
if %ERRORLEVEL% EQU 0 (
    echo ======================================================================
    echo ✅ Successfully pushed to https://github.com/GunaVardhanch/RailSamiksha_final
    echo ======================================================================
) else (
    echo ======================================================================
    echo ⚠️ Push encountered an issue. If prompted, please click "Sign in with your browser"
    echo    or provide a GitHub Personal Access Token (PAT).
    echo ======================================================================
)
echo.
pause
