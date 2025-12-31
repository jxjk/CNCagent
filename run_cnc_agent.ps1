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
Write-Host "Select startup mode:" -ForegroundColor White
Write-Host "1. Start both beautified GUI and Web server (default)" -ForegroundColor White
Write-Host "2. Start both optimized GUI and Web server" -ForegroundColor White
Write-Host "3. Start both standard GUI and Web server" -ForegroundColor White
Write-Host "4. Start Web server only (port 5000)" -ForegroundColor White
Write-Host "5. Start Web server only (port 8080)" -ForegroundColor White
Write-Host "6. Start beautified GUI only" -ForegroundColor White
Write-Host "7. Start optimized GUI only" -ForegroundColor White
Write-Host "8. Start standard GUI only" -ForegroundColor White
Write-Host ""

$choice = Read-Host "Enter your choice (1-8, press Enter for default 1)"

# Verify Python is installed
$pythonInstalled = Get-Command python -ErrorAction SilentlyContinue
if (-not $pythonInstalled) {
    Write-Host "Error: Python command not found, please ensure Python 3.8 or higher is installed" -ForegroundColor Red
    Read-Host "Press Enter to exit"
    exit 1
}

# Switch to project directory
Set-Location python_cncagent

# Start the appropriate mode based on user selection
switch ($choice) {
    "2" {
        Write-Host ""
        Write-Host "Starting optimized GUI and Web server..." -ForegroundColor Green
        python start_unified.py both-optimized
    }
    "3" {
        Write-Host ""
        Write-Host "Starting standard GUI and Web server..." -ForegroundColor Green
        python start_unified.py both
    }
    "4" {
        Write-Host ""
        Write-Host "Starting Web server (port 5000)..." -ForegroundColor Green
        python start_unified.py web --port 5000
    }
    "5" {
        Write-Host ""
        Write-Host "Starting Web server (port 8080)..." -ForegroundColor Green
        python start_unified.py web --port 8080
    }
    "6" {
        Write-Host ""
        Write-Host "Starting beautified GUI..." -ForegroundColor Green
        python start_unified.py gui-beautified
    }
    "7" {
        Write-Host ""
        Write-Host "Starting optimized GUI..." -ForegroundColor Green
        python start_unified.py gui-optimized
    }
    "8" {
        Write-Host ""
        Write-Host "Starting standard GUI..." -ForegroundColor Green
        python start_unified.py gui
    }
    "1" {
        Write-Host ""
        Write-Host "Starting beautified GUI and Web server..." -ForegroundColor Green
        python start_unified.py both-beautified
    }
    Default {
        Write-Host ""
        Write-Host "Starting beautified GUI and Web server (default)..." -ForegroundColor Green
        python start_unified.py both-beautified
    }
}

# Check command execution result
if ($LASTEXITCODE -ne 0) {
    Write-Host ""
    Write-Host "Error: Python command execution failed" -ForegroundColor Red
    Write-Host "Please ensure:" -ForegroundColor Red
    Write-Host "1. Python 3.8 or higher is installed" -ForegroundColor Red
    Write-Host "2. Project dependencies are installed (run: pip install -r requirements.txt)" -ForegroundColor Red
    Write-Host "3. API key is configured correctly" -ForegroundColor Red
    Read-Host "Press Enter to exit"
    exit $LASTEXITCODE
}

Write-Host ""
Write-Host "Press Enter to exit..." -ForegroundColor Gray
Read-Host