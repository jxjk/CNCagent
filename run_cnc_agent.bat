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
echo Select startup mode:
echo 1. Start both beautified GUI and Web server (default)
echo 2. Start both optimized GUI and Web server 
echo 3. Start both standard GUI and Web server
echo 4. Start Web server only (port 5000)
echo 5. Start Web server only (port 8080)
echo 6. Start beautified GUI only
echo 7. Start optimized GUI only
echo 8. Start standard GUI only
echo.
set /p choice="Enter your choice (1-8, press Enter for default 1): "

REM Go to Python project directory
cd /d "%~dp0python_cncagent"

REM Start the appropriate mode based on user selection
if "%choice%"=="2" (
    echo.
    echo Starting optimized GUI and Web server...
    python start_unified.py both-optimized
) else if "%choice%"=="3" (
    echo.
    echo Starting standard GUI and Web server...
    python start_unified.py both
) else if "%choice%"=="4" (
    echo.
    echo Starting Web server (port 5000)...
    python start_unified.py web --port 5000
) else if "%choice%"=="5" (
    echo.
    echo Starting Web server (port 8080)...
    python start_unified.py web --port 8080
) else if "%choice%"=="6" (
    echo.
    echo Starting beautified GUI...
    python start_unified.py gui-beautified
) else if "%choice%"=="7" (
    echo.
    echo Starting optimized GUI...
    python start_unified.py gui-optimized
) else if "%choice%"=="8" (
    echo.
    echo Starting standard GUI...
    python start_unified.py gui
) else if "%choice%"=="1" (
    echo.
    echo Starting beautified GUI and Web server...
    python start_unified.py both-beautified
) else (
    echo.
    echo Starting beautified GUI and Web server (default)...
    python start_unified.py both-beautified
)

REM Check Python command execution result
if errorlevel 1 (
    echo.
    echo Error: Python command execution failed
    echo Please ensure:
    echo 1. Python 3.8 or higher is installed
    echo 2. Project dependencies are installed (run: pip install -r requirements.txt)
    echo 3. API key is configured correctly
    pause
    exit /b 1
)

echo.
echo Press any key to exit...
pause