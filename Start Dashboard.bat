@echo off
title Semiconductor Credit Intelligence
cd /d "%~dp0"

if not exist ".venv\Scripts\python.exe" (
    echo The dashboard's Python environment was not found in this folder.
    echo Make sure you are opening this file from the original project folder.
    pause
    exit /b 1
)

echo Starting Semiconductor Credit Intelligence...
echo Keep this window open while using the dashboard.
echo.

start "" powershell -NoProfile -WindowStyle Hidden -Command "Start-Sleep -Seconds 5; Start-Process 'http://127.0.0.1:8502'"
".venv\Scripts\python.exe" -m streamlit run "app\community_main.py" --server.address 127.0.0.1 --server.port 8502

echo.
echo The dashboard has stopped. Press any key to close this window.
pause >nul
