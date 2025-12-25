# CNC Agent 统一启动器说明

## 概述

CNC Agent 现在提供了一个统一的启动文件 `start_unified.py`，允许用户同时或单独启动GUI界面和Web服务器。

## 新的启动方式

### 1. 统一启动器 (推荐)

```bash
# 同时启动GUI界面和Web服务器（默认）
python start_unified.py

# 仅启动GUI界面
python start_unified.py gui

# 仅启动Web服务器
python start_unified.py web

# 同时启动，Web服务器使用指定端口
python start_unified.py both --port 8080

# 启动Web服务器并指定主机地址和端口
python start_unified.py web --host 127.0.0.1 --port 3000
```

### 2. 传统启动方式（保持向后兼容）

```bash
# 启动GUI界面
python start_ai_nc_helper.py gui

# 启动Web服务器
python start_server.py

# 命令行处理PDF
python start_ai_nc_helper.py process drawing.pdf "加工描述"
```

## 功能特性

### 统一启动器优势
- **同时运行**: 可以同时启动GUI界面和Web服务器
- **灵活配置**: 支持自定义Web服务器端口和主机地址
- **统一管理**: 一个文件管理所有启动选项
- **错误处理**: 改进的错误处理和日志记录
- **优雅退出**: 支持Ctrl+C等信号的优雅退出

### 命令行选项

- `mode`: 启动模式 (gui/web/both, 默认: both)
- `--port`: Web服务器端口 (默认: 5000)
- `--host`: Web服务器主机地址 (默认: 0.0.0.0)

### 日志记录

统一启动器会在当前目录创建 `cnc_unified.log` 文件记录运行日志。

## 架构设计

### 多线程设计
- Web服务器在独立线程中运行（守护线程）
- GUI界面在主线程中运行
- 线程间互不干扰，可以独立关闭

### 错误处理
- 模块导入错误处理
- 依赖项缺失提示
- 优雅的异常处理

## 向后兼容性

所有现有的启动方式都保持不变，确保现有脚本和工作流程不受影响。

## 使用场景

### 场景1: 同时使用GUI和Web API
```bash
python start_unified.py
```
- 本地GUI界面用于交互式操作
- Web API用于自动化脚本和外部集成

### 场景2: 仅Web服务器（服务器部署）
```bash
python start_unified.py web --port 80 --host 0.0.0.0
```
- 部署在服务器上提供Web API服务

### 场景3: 仅GUI（桌面使用）
```bash
python start_unified.py gui
```
- 仅使用图形界面进行交互式操作

## 部署建议

对于生产环境，建议使用传统的独立启动方式，以确保更好的资源管理和错误隔离。