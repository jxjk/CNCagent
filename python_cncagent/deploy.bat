@echo off
REM CNC Agent 部署脚本 (Windows)

echo 正在部署 CNC Agent...

REM 检查Python是否已安装
python --version >nul 2>&1
if errorlevel 1 (
    echo 错误: 未找到Python，请确保已安装Python并添加到PATH环境变量中
    pause
    exit /b 1
)

REM 安装依赖
echo 正在安装依赖...
pip install -r requirements.txt
if errorlevel 1 (
    echo 依赖安装失败
    pause
    exit /b 1
)

REM 创建必要目录
echo 正在创建必要目录...
if not exist logs mkdir logs
if not exist temp mkdir temp
if not exist output mkdir output
if not exist uploads mkdir uploads

REM 启动服务器
echo 正在启动CNC Agent服务器...
python start_server.py

pause