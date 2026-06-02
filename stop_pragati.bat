@echo off
title Stop PRAGATI AI Backend
echo ==============================================
echo Stopping PRAGATI AI backend server...
echo ==============================================

:: Find process ID listening on port 8000 and force kill it
for /f "tokens=5" %%a in ('netstat -aon ^| findstr 127.0.0.1:8000') do (
    taskkill /f /pid %%a 2>nul
)

echo.
echo PRAGATI AI backend server stopped successfully.
timeout /t 3 >nul
