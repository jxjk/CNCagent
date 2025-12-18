#!/bin/bash
# CNCagent Docker部署脚本

echo "开始部署CNCagent到Docker..."

# 检查Docker是否安装
if ! [ -x "$(command -v docker)" ]; then
  echo "错误: Docker未安装，请先安装Docker" >&2
  exit 1
fi

# 检查docker-compose是否安装
if ! [ -x "$(command -v docker-compose)" ]; then
  echo "警告: docker-compose未安装，使用docker命令部署"
  
  # 构建镜像
  echo "构建CNCagent镜像..."
  docker build -t cncagent:latest .
  
  # 运行容器
  echo "启动CNCagent容器..."
  docker run -d \
    --name cncagent \
    -p 3000:3000 \
    -v $(pwd)/workspace:/app/workspace \
    -v $(pwd)/logs:/app/logs \
    cncagent:latest
  
  echo "CNCagent已启动，访问 http://localhost:3000"
else
  # 使用docker-compose部署
  echo "使用docker-compose部署CNCagent..."
  docker-compose up -d
  
  echo "CNCagent已启动，访问 http://localhost:3000"
fi

# 显示运行状态
echo "检查容器状态..."
docker ps | grep cncagent

echo "部署完成！"