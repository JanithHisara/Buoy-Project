@echo off
title OceanNav Buoy Navigation System
cd /d "%~dp0"

echo ===================================================
echo   OceanNav Buoy Navigation System Setup ^& Launcher
echo ===================================================
echo.

:: 1. Check if Python is installed
python --version >nul 2>&1
if %errorlevel% neq 0 (
    echo [ERROR] Python is not installed or not added to your system PATH.
    echo Please install Python and check the option "Add Python to PATH" during installation.
    echo.
    pause
    exit /b
)

:: 2. Check and install Python dependencies
echo [1/3] Checking and installing required Python libraries (Flask, PySerial)...
python -m pip install flask pyserial --quiet
if %errorlevel% neq 0 (
    echo [WARNING] Failed to install packages automatically. Trying to run server anyway...
) else (
    echo [OK] Python dependencies are ready.
)
echo.

:: 3. Launch the browser with a 2-second delay in a separate window
echo [2/3] Scheduling default web browser to open http://localhost:5000...
start "" cmd /c "timeout /t 2 /nobreak >nul && start http://localhost:5000"

:: 4. Run the Flask Server
echo [3/3] Starting the Flask server...
echo.
echo ---------------------------------------------------
echo  SERVER IS RUNNING! Keep this window open to use.
echo  To stop the server, simply close this window.
echo ---------------------------------------------------
echo.
python main.py

pause
