@echo off
echo 开始部署CNCagent到Docker...

REM 检查Docker是否安装
docker --version >nul 2>&1
if %errorlevel% neq 0 (
    echo 错误: Docker未安装，请先安装Docker
    pause
    exit /b 1
)

echo 构建CNCagent镜像...
docker build -t cncagent:latest .

if %errorlevel% equ 0 (
    echo 启动CNCagent容器...
    docker run -d ^
        --name cncagent ^
        -p 3000:3000 ^
        -v %cd%\workspace:/app/workspace ^
        -v %cd%\logs:/app/logs ^
        cncagent:latest
    
    if %errorlevel% equ 0 (
        echo.
        echo CNCagent已成功启动！
        echo 请访问 http://localhost:3000
        echo.
        docker ps --filter "name=cncagent"
    ) else (
        echo 启动容器失败
        pause
        exit /b 1
    )
) else (
    echo 构建镜像失败
    pause
    exit /b 1
)

echo.
echo 部署完成！
pause