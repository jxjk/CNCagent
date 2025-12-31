# CNC Agent - AI-Powered Smart NC Programming Platform
# ========================================================

Write-Host ""
Write-Host "CNC Agent - AI-Powered Smart NC Programming Platform" -ForegroundColor Cyan
Write-Host "========================================================" -ForegroundColor Cyan
Write-Host ""

# Check and set API configuration
if (-not $env:DEEPSEEK_API_KEY) {
    $env:DEEPSEEK_API_KEY = "sk-b306662b71a04f16a1eccfa2c63aef3f"
    Write-Host "Using default DEEPSEEK_API_KEY" -ForegroundColor Yellow
} else {
    Write-Host "Custom DEEPSEEK_API_KEY detected" -ForegroundColor Green
}

if (-not $env:DEEPSEEK_MODEL) {
    $env:DEEPSEEK_MODEL = "deepseek-chat"
    Write-Host "Using default DEEPSEEK_MODEL: $env:DEEPSEEK_MODEL" -ForegroundColor Yellow
}

if (-not $env:DEEPSEEK_API_BASE) {
    $env:DEEPSEEK_API_BASE = "https://api.deepseek.com"
    Write-Host "Using default DEEPSEEK_API_BASE: $env:DEEPSEEK_API_BASE" -ForegroundColor Yellow
}

Write-Host ""
Write-Host "Starting both beautified GUI and Web server..." -ForegroundColor Green
Write-Host ""
Write-Host "GUI Features Available:" -ForegroundColor White
Write-Host " - Zoom: Ctrl+Mouse Wheel, Ctrl++ or Ctrl+-" -ForegroundColor White
Write-Host " - Rotate: Ctrl+R" -ForegroundColor White
Write-Host " - Pan: Middle Mouse Button Drag" -ForegroundColor White
Write-Host " - Right-click Canvas: Context Menu" -ForegroundColor White
Write-Host " - Feature Detection: Identify geometry in drawings" -ForegroundColor White
Write-Host ""
Write-Host "Checking dependencies..." -ForegroundColor Yellow
python -c "import sys; print('Python version:', sys.version)"
$tkinterCheck = python -c "import tkinter; print('Tkinter: OK')" 2>$null; if (-not $tkinterCheck) { Write-Host "ERROR: Tkinter not available" -ForegroundColor Red }
$cv2Check = python -c "import cv2; print('OpenCV: OK')" 2>$null; if (-not $cv2Check) { Write-Host "ERROR: OpenCV not installed" -ForegroundColor Red }
$numpyCheck = python -c "import numpy; print('NumPy: OK')" 2>$null; if (-not $numpyCheck) { Write-Host "ERROR: NumPy not installed" -ForegroundColor Red }
$pilCheck = python -c "import PIL; print('PIL/Pillow: OK')" 2>$null; if (-not $pilCheck) { Write-Host "ERROR: PIL/Pillow not installed" -ForegroundColor Red }
$flaskCheck = python -c "import flask; print('Flask: OK')" 2>$null; if (-not $flaskCheck) { Write-Host "ERROR: Flask not installed" -ForegroundColor Red }
Write-Host ""
Write-Host "Launching application..." -ForegroundColor Yellow

# Switch to project directory
Set-Location python_cncagent
python start_unified.py both-beautified

if ($LASTEXITCODE -ne 0) {
    Write-Host ""
    Write-Host "Launch failed. Checking for detailed errors..." -ForegroundColor Red
    Write-Host "Make sure all dependencies are installed:" -ForegroundColor Red
    Write-Host "Run: pip install -r requirements.txt" -ForegroundColor Red
    Write-Host "Also ensure you have the following packages:" -ForegroundColor Red
    Write-Host " - opencv-python (for image processing)" -ForegroundColor Red
    Write-Host " - pillow (for image handling)" -ForegroundColor Red
    Write-Host " - numpy (for numerical operations)" -ForegroundColor Red
    Write-Host " - plotly (for 3D model visualization, optional)" -ForegroundColor Red
    Write-Host ""
    Read-Host "Press Enter to continue"
}

Write-Host ""
Write-Host "Press Enter to exit..." -ForegroundColor Gray
Read-Host