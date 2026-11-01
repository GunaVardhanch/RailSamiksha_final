@echo off
title Push RailSamiksha to GitHub
echo ======================================================================
echo 🚀 Pushing RailSamiksha Code to GitHub: GunaVardhanch/Railsamiksha
echo ======================================================================
echo.

cd /d "%~dp0"

echo Ensuring branch is named 'main'...
git branch -M main

echo.
echo Pushing commits to remote origin...
git push -u origin main

echo.
if %ERRORLEVEL% EQU 0 (
    echo ======================================================================
    echo ✅ Successfully pushed to https://github.com/GunaVardhanch/Railsamiksha
    echo ======================================================================
) else (
    echo ======================================================================
    echo ⚠️ Push encountered an issue. Please verify your GitHub login or Personal Access Token (PAT).
    echo ======================================================================
)
pause

