# 使用Python基础镜像 - 使用alpine版本避免Debian签名问题
FROM python:3.10-alpine

# 设置工作目录
WORKDIR /app

# 安装系统依赖 - 包括tesseract OCR引擎和其他必要的库
RUN apk add --no-cache \
    tesseract-ocr \
    tesseract-ocr-dev \
    leptonica-dev \
    gcc \
    g++ \
    musl-dev \
    linux-headers \
    libffi-dev \
    pkgconfig \
    mesa-gles \
    glib \
    libsm \
    libxext \
    libxrender \
    make

# 复制项目文件
COPY requirements.txt .
COPY .env.example .env

# 安装Python依赖
RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir -r requirements.txt

# 复制源代码
COPY . .

# 创建必要的目录
RUN mkdir -p logs && mkdir -p workspace && mkdir -p temp

# 暴露端口
EXPOSE 5000

# 健康检查端点
HEALTHCHECK --interval=30s --timeout=30s --start-period=5s --retries=3 \
    CMD curl -f http://localhost:5000/health || exit 1

# 默认启动Web服务器
CMD ["python", "start_server.py"]