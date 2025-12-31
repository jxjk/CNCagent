@echo off
echo.
echo CNC Agent - AI-Powered Smart NC Programming Platform
echo ========================================================
echo.

REM Set default API configuration if environment variables are not set
if "%DEEPSEEK_API_KEY%"=="" (
    SET DEEPSEEK_API_KEY=sk-ca4d0ccb91b9470c99af938dcdbe88db
    echo Using default DEEPSEEK_API_KEY
) else (
    echo Custom DEEPSEEK_API_KEY detected
)

if "%DEEPSEEK_MODEL%"=="" (
    SET DEEPSEEK_MODEL=deepseek-chat
    echo Using default DEEPSEEK_MODEL: %DEEPSEEK_MODEL%
)

if "%DEEPSEEK_API_BASE%"=="" (
    SET DEEPSEEK_API_BASE=https://api.deepseek.com
    echo Using default DEEPSEEK_API_BASE: %DEEPSEEK_API_BASE%
)

echo.
echo Starting both beautified GUI and Web server...
echo.
echo GUI Features Available:
echo - Zoom: Ctrl+Mouse Wheel, Ctrl++ or Ctrl+-
echo - Rotate: Ctrl+R
echo - Pan: Middle Mouse Button Drag
echo - Right-click Canvas: Context Menu
echo - Feature Detection: Identify geometry in drawings
echo.
echo Checking dependencies...
python -c "import sys; print('Python version:', sys.version)"
python -c "import tkinter; print('Tkinter: OK')" 2>nul || echo ERROR: Tkinter not available
python -c "import cv2; print('OpenCV: OK')" 2>nul || echo ERROR: OpenCV not installed
python -c "import numpy; print('NumPy: OK')" 2>nul || echo ERROR: NumPy not installed
python -c "import PIL; print('PIL/Pillow: OK')" 2>nul || echo ERROR: PIL/Pillow not installed
python -c "import flask; print('Flask: OK')" 2>nul || echo ERROR: Flask not installed
echo.
echo Launching application...
cd /d "%~dp0python_cncagent"
python start_unified.py both-beautified

if errorlevel 1 (
    echo.
    echo Launch failed. Checking for detailed errors...
    echo Make sure all dependencies are installed:
    echo Run: pip install -r requirements.txt
    echo Also ensure you have the following packages:
    echo - opencv-python (for image processing)
    echo - pillow (for image handling)
    echo - numpy (for numerical operations)
    echo - plotly (for 3D model visualization, optional)
    echo.
    pause
)

echo.
echo Press any key to exit...
pause