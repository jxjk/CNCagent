# CNCagent Python版

CNCagent的Python实现，一个功能完整的CNC代码编写助手，提供从CAD图纸解析到G代码生成的完整工作流程。

## 功能特性

- **项目管理**：完整的项目生命周期管理
- **CAD图纸解析**：支持PDF等格式的图纸解析
- **特征识别**：自动识别几何特征（孔、槽、口袋等）
- **G代码生成**：智能生成高效G代码
- **材料工具匹配**：根据材料自动推荐刀具和加工参数
- **仿真验证**：G代码仿真和碰撞检测
- **安全验证**：G代码安全性和正确性验证

## 架构概览

```
python_cncagent/
├── src/
│   ├── main.py                 # 主应用入口和状态管理
│   ├── modules/
│   │   ├── project_initialization.py  # 项目初始化模块
│   │   ├── feature_definition.py      # 特征定义模块
│   │   ├── gcode_generation.py        # G代码生成模块
│   │   ├── material_tool_matcher.py   # 材料工具匹配模块
│   │   ├── validation.py              # 验证模块
│   │   ├── simulation_output.py       # 仿真输出模块
│   │   └── subprocesses/
│   │       └── pdf_parsing_process.py # PDF处理模块
│   └── utils/                 # 工具函数
├── tests/                     # 测试文件
├── requirements.txt           # 依赖包列表
└── README.md                 # 本文件
```

## 核心模块

### 1. 项目初始化模块
- 创建和管理CNC加工项目
- 项目状态跟踪和工作区管理
- 图纸导入和文件格式支持

### 2. 特征定义模块
- 交互式特征选择
- 特征类型定义（孔、沉头孔、口袋、槽等）
- 宏变量关联和参数定义

### 3. G代码生成模块
- 基于特征的智能G代码生成
- 批量加工优化
- 工艺参数自动计算
- 优化加工顺序

### 4. 材料工具匹配模块
- 材料数据库（钢、铝、铜、塑料等）
- 刀具数据库（高速钢、硬质合金等）
- 智能匹配和参数推荐
- 加工策略优化

### 5. 验证模块
- G代码语法验证
- 安全性检查
- 碰撞检测
- 工艺参数验证

### 6. 仿真输出模块
- G代码仿真执行
- 工具路径可视化
- 加工时间估算
- 代码导出功能

### 7. PDF处理模块
- CAD图纸解析
- 几何元素识别
- 尺寸标注提取
- OCR辅助识别

## 使用方法

### 安装依赖

```bash
pip install -r requirements.txt
```

### 运行应用

```bash
python src/main.py
```

应用将在 http://localhost:3000 上运行

### Docker部署

#### 构建并运行Docker容器：

```bash
# 使用docker-compose（推荐）
docker-compose up -d

# 或者使用docker命令
docker build -t cncagent:latest .
docker run -d --name cncagent -p 3000:3000 cncagent:latest
```

CNCagent使用Flask框架构建，通过start_server.py启动。该应用在Docker容器中监听3000端口。

#### 访问应用：
- 应用将在 http://localhost:3000 上运行
- API接口可通过 http://localhost:3000/api 访问

### API接口

- `POST /api/project/new` - 创建新项目
- `POST /api/project/import` - 导入图纸文件
- `POST /api/feature/select` - 选择特征
- `POST /api/feature/define` - 定义特征
- `POST /api/gcode/generate` - 生成G代码
- `POST /api/simulation/start` - 启动仿真
- `POST /api/gcode/export` - 导出代码
- `GET /api/state` - 获取状态信息

## 技术特点

- **完整的状态管理**：支持完整的CNC加工流程状态转换
- **智能工艺优化**：自动优化加工顺序和参数
- **多特征批量处理**：支持批量加工以提高效率
- **安全验证机制**：多层验证确保代码安全
- **可扩展架构**：模块化设计便于功能扩展

## 开发说明

本项目忠实地实现了原JavaScript版本的所有功能，包括：

- 完整的API接口
- 业务逻辑处理
- 数据验证和错误处理
- 智能算法实现
- 仿真和验证功能

所有模块都经过功能验证，确保Python版本与原版在功能上保持一致。

## 部署说明

### Docker部署
项目包含完整的Docker支持：

- `Dockerfile` - 定义应用运行环境
- `docker-compose.yml` - 定义服务配置
- `deploy.sh` - 一键部署脚本

### 生产环境建议
- 使用反向代理（如Nginx）处理静态文件和SSL
- 配置适当的日志记录和监控
- 使用环境变量管理配置
- 设置资源限制以避免过度消耗