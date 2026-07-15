@echo off
title OceanNav System Server
echo ==========================================
echo       Starting OceanNav System
echo ==========================================
echo.

echo Checking Python requirements...
python -m pip install -r requirements.txt --quiet

echo.
echo Starting Flask Server...
echo The application will open in your default web browser shortly.
echo (Keep this terminal window open while using the system!)
echo.

:: Wait for 2 seconds in the background and then open the default web browser
start /B cmd /c "timeout /t 2 /nobreak >nul & start http://127.0.0.1:5000"

:: Start the backend Flask application
python run.py

pause
