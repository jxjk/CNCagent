@echo off
REM CNCagent 启动脚本

echo 正在启动 CNCagent 服务...

REM 检查 Node.js 是否已安装
node --version >nul 2>&1
if %errorlevel% neq 0 (
    echo 错误: 未找到 Node.js，请确保已安装 Node.js 并添加到系统路径
    pause
    exit /b 1
)

REM 检查依赖包是否已安装
if not exist "node_modules" (
    echo 未找到 node_modules，正在安装依赖包...
    npm install
    if %errorlevel% neq 0 (
        echo 依赖包安装失败
        pause
        exit /b 1
    )
)

REM 启动 CNCagent 应用
echo 启动 CNCagent 应用...
node src/index.js

pause