@echo off
REM Stanford PS310 Desktop Application Launcher for Windows
REM This script launches the desktop application with the Chromium-based webview

echo ======================================================================
echo Stanford PS310 High Voltage Power Supply - Desktop Application
echo ======================================================================
echo.

REM Check if Python is available
python --version >nul 2>&1
if errorlevel 1 (
    echo ERROR: Python is not installed or not in PATH
    echo Please install Python 3.7+ and try again
    pause
    exit /b 1
)

REM Check if in virtual environment
if "%VIRTUAL_ENV%"=="" (
    echo WARNING: Not running in a virtual environment
    echo It's recommended to use a virtual environment
    echo.
    echo To create and activate a virtual environment:
    echo   python -m venv .venv
    echo   .venv\Scripts\activate
    echo   pip install -r requirements.txt
    echo.
    echo Continue anyway? Press Ctrl+C to cancel, or
    pause
)

echo Starting Stanford PS310 Desktop Application...
echo.
echo Close the application window to exit.
echo.

REM Launch the desktop application
cd /d "%~dp0\.." && python apps\PS310\stanfordps310_gui_desktop.py

if errorlevel 1 (
    echo.
    echo ERROR: Application failed to start
    echo.
    echo Troubleshooting:
    echo   1. Install dependencies: pip install -r requirements.txt
    echo   2. Check that pywebview is installed: pip install pywebview
    echo   3. On Windows 10, install WebView2 Runtime from Microsoft
    echo.
    pause
    exit /b 1
)

echo.
echo Application closed successfully
pause
