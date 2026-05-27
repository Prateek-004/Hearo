@echo off
title Hearo — Setup & Launch
echo.
echo  ============================================
echo   Hearo v1.0 — Smart Offline Music Player
echo  ============================================
echo.

REM Check Python
python --version >nul 2>&1
if errorlevel 1 (
    echo  [ERROR] Python not found!
    echo  Please install Python 3.8+ from https://python.org
    pause
    exit /b 1
)

echo  [1/2] Installing dependencies...
python -m pip install -r requirements.txt --quiet
if errorlevel 1 (
    echo  [ERROR] Failed to install dependencies.
    pause
    exit /b 1
)

echo  [2/2] Launching Hearo...
echo.
python hearo.py
pause
