@echo off
setlocal
title Push RailSamiksha to GitHub (RailSamiksha_final)
echo ======================================================================
echo 🚀 Pushing RailSamiksha to: GunaVardhanch/RailSamiksha_final
echo ======================================================================
echo.

:: Ensure Git is in PATH
set "PATH=%PATH%;C:\Users\user\AppData\Local\Programs\Git\cmd;C:\Program Files\Git\cmd;C:\Program Files (x86)\Git\cmd"

:: Check if git can be found
where git >nul 2>&1
if %ERRORLEVEL% NEQ 0 (
    if exist "C:\Users\user\AppData\Local\Programs\Git\cmd\git.exe" (
        set "GIT_BIN=C:\Users\user\AppData\Local\Programs\Git\cmd\git.exe"
    ) else if exist "C:\Program Files\Git\cmd\git.exe" (
        set "GIT_BIN=C:\Program Files\Git\cmd\git.exe"
    ) else (
        echo [ERROR] Git could not be located on your system.
        pause
        exit /b 1
    )
) else (
    set "GIT_BIN=git"
)

cd /d "%~dp0"

echo [1/3] Checking active branch...
"%GIT_BIN%" branch -M main

echo.
echo [2/3] Setting remote origin...
"%GIT_BIN%" remote set-url origin https://github.com/GunaVardhanch/RailSamiksha_final.git

echo.
echo [3/3] Pushing codebase to remote origin...
"%GIT_BIN%" push -u origin main

echo.
if %ERRORLEVEL% EQU 0 (
    echo ======================================================================
    echo ✅ Successfully pushed to https://github.com/GunaVardhanch/RailSamiksha_final
    echo ======================================================================
) else (
    echo ======================================================================
    echo ⚠️ Push encountered an issue. If prompted, please click "Sign in with your browser"
    echo    or authenticate with your GitHub Personal Access Token (PAT).
    echo ======================================================================
)
echo.
pause
