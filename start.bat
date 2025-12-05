@echo off
REM CNCagent 启动脚本
REM 用于在Windows环境下启动CNCagent服务

echo.
echo ===============================================
echo        CNCagent CNC代码编写助手
echo ===============================================
echo.

REM 检查Node.js是否已安装
node --version >nul 2>&1
if %errorlevel% neq 0 (
    echo 错误: 未找到Node.js，请先安装Node.js
    echo 请访问 https://nodejs.org/ 下载安装
    pause
    exit /b 1
)

REM 检查npm是否已安装
npm --version >nul 2>&1
if %errorlevel% neq 0 (
    echo 错误: 未找到npm，请检查Node.js安装
    pause
    exit /b 1
)

REM 检查node_modules是否存在
if not exist "node_modules" (
    echo 首次运行，正在安装依赖包...
    npm install
    if %errorlevel% neq 0 (
        echo 错误: 依赖安装失败
        pause
        exit /b 1
    )
    echo 依赖包安装完成
    echo.
)

echo 启动CNCagent服务...
echo 按 Ctrl+C 可停止服务
echo.

REM 启动应用
node src/index.js

echo.
echo CNCagent服务已停止
pause