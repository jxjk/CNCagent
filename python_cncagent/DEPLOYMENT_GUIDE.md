# CNC Agent 本地 Docker 部署指南

## 概述
本指南将帮助您在本地使用 Docker 部署 CNC Agent 项目。CNC Agent 是一个 AI 驱动的从 PDF 图纸自动生成 FANUC NC 程序的 Python 实现项目。

## 环境要求
- Docker Desktop 或 Docker Engine
- Docker Compose
- Python 3.8+ (仅用于本地开发)

## 快速启动

### 1. 克隆项目
```bash
git clone <your-repo-url>
cd python_cncagent
```

### 2. 配置环境变量
复制环境变量配置文件并填入您的 API 密钥：
```bash
cp .env.example .env
```

编辑 `.env` 文件，填入您的 AI API 密钥：
```bash
DEEPSEEK_API_KEY=your-deepseek-api-key-here
OPENAI_API_KEY=your-openai-api-key-here
```

### 3. 构建并启动服务
使用 Docker Compose 启动服务：
```bash
docker-compose up --build
```

服务将在 http://localhost:5000 可用

## Docker Compose 服务

项目包含两个主要服务：

### cnc-agent (API 服务)
- 端口: 5000
- 功能: 提供 Web API 接口，处理 PDF 到 NC 代码的转换
- 环境变量: API 密钥、模型配置等

### cnc-agent-gui (GUI 服务)
- 端口: 5001
- 功能: 提供 Web GUI 界面（注意：容器中 GUI 可能受限）

## 部署选项

### 开发模式
使用 `docker-compose.yml` 进行开发：
```bash
docker-compose up --build
```

### 生产模式
使用 `docker-compose.prod.yml` 进行生产部署：
```bash
docker-compose -f docker-compose.prod.yml up -d
```

## 持久化存储
- 日志目录: `./logs` - 存储应用程序日志
- 工作目录: `./workspace` - 存储项目工作文件
- 临时目录: `./temp` - 存储临时文件

## API 使用

### 健康检查
```
GET http://localhost:5000/health
```

### 生成 NC 代码
```
POST http://localhost:5000/generate_nc
Content-Type: multipart/form-data
```

表单参数:
- `pdf`: PDF 图纸文件
- `description`: 加工描述
- `scale`: 比例尺 (可选, 默认 1.0)
- `coordinate_strategy`: 坐标策略 (可选, 默认 "highest_y")

### API 接口
```
POST http://localhost:5000/api/generate
Content-Type: application/json
```

JSON 参数:
```json
{
  "pdf_content": "base64 编码的 PDF 内容",
  "description": "加工描述",
  "scale": 1.0
}
```

## Kubernetes 部署

如果需要在 Kubernetes 中部署，可以使用提供的 YAML 文件：

1. 创建 Secret (包含 API 密钥):
```bash
kubectl create secret generic cnc-agent-secrets \
  --from-literal=deepseek-api-key=your-deepseek-key \
  --from-literal=openai-api-key=your-openai-key
```

2. 创建持久卷:
```bash
kubectl apply -f k8s-pvc.yaml
```

3. 部署应用:
```bash
kubectl apply -f k8s-deployment.yaml
kubectl apply -f k8s-service.yaml
```

## 环境变量说明

- `DEEPSEEK_API_KEY`: DeepSeek API 密钥 (优先使用)
- `DEEPSEEK_MODEL`: DeepSeek 模型名称 (默认: deepseek-chat)
- `DEEPSEEK_API_BASE`: DeepSeek API 基础 URL
- `OPENAI_API_KEY`: OpenAI API 密钥 (备选)
- `OPENAI_MODEL`: OpenAI 模型名称 (默认: gpt-3.5-turbo)
- `PORT`: 服务端口 (默认: 5000)
- `FLASK_ENV`: 环境模式 (默认: production)

## 故障排除

### 构建错误
如果构建失败，请检查:
- 确保所有依赖包都能正确安装
- 系统依赖 (tesseract-ocr) 是否正确安装

### API 密钥问题
- 确保 `.env` 文件中的 API 密钥正确设置
- 检查 API 密钥是否有足够的权限

### 文件上传问题
- 检查容器中的临时目录权限
- 确保上传的文件格式被支持

## 扩展配置

如需扩展配置，可以修改:
- `Dockerfile`: 容器构建配置
- `docker-compose.yml`: 服务配置
- `requirements.txt`: Python 依赖

## 安全注意事项

1. 不要将 API 密钥提交到版本控制系统
2. 使用 Docker secrets 或 Kubernetes secrets 管理敏感信息
3. 定期更新基础镜像以获得安全补丁
4. 限制容器权限，避免使用 root 用户

## 监控和日志

- 应用日志: 保存在 `./logs` 目录
- Docker 日志: 使用 `docker logs <container-name>` 查看
- 健康检查: 通过 `/health` 端点监控服务状态