# CNC Agent 项目说明

## 项目概述

CNC Agent 是一个 AI 辅助的从 PDF 图纸自动生成 FANUC NC 程序的 Python 实现项目。该项目能够从 PDF 图纸中识别几何特征、理解用户加工描述，并生成符合 FANUC 标准的 G 代码程序。项目采用插件式架构设计，支持一键式处理流程，并提供图形界面和命令行两种操作方式。

### 核心功能

1. **PDF 图纸解析与 OCR 处理** - 从 PDF 文件中提取文本和图像信息
2. **几何特征识别** - 识别圆形、矩形、多边形等几何形状及复合特征（如沉孔、螺纹孔）
3. **用户描述理解** - 分析用户加工要求并提取工艺参数
4. **FANUC NC 程序生成** - 生成符合 FANUC 控制系统标准的 G 代码
5. **完整流程整合** - 将上述功能整合为一键式处理流程
6. **AI 辅助 NC 编程工具** - 提供图形界面和简化操作
7. **多格式导出** - 支持 CamBam、Mastercam、Fusion 360 等主流CAM软件格式
8. **智能工艺推荐** - 基于特征类型智能推荐加工参数
9. **统一代码生成入口** - 整合AI驱动、OCR推理和传统图像处理功能

### 支持的加工工艺

- **钻孔加工** - 普通钻孔、深孔钻削
- **攻丝加工** - 完整的螺纹孔加工工艺（点孔→钻孔→攻丝）
- **锪孔/沉孔加工** - φ22 沉孔 + φ14.5 底孔的复合特征加工
- **铣削加工** - 圆形、矩形、三角形等轮廓铣削
- **车削加工** - 外径车削
- **极坐标加工** - 支持极坐标系下的孔位加工
- **复合工艺** - 支持多刀具的完整加工工艺（如攻丝的点孔→钻孔→攻丝）

## 项目架构

```
src/
├── __init__.py
├── config.py                    # 项目配置参数
├── config_validator.py          # 配置验证模块
├── exceptions.py                # 异常处理模块
├── main.py                     # 主程序入口
├── resource_manager.py          # 资源管理模块
├── modules/
│   ├── __init__.py
│   ├── ai_driven_generator.py   # AI驱动的NC生成模块
│   ├── ai_nc_helper.py          # AI辅助NC编程工具核心
│   ├── fanuc_optimization.py    # FANUC代码优化模块
│   ├── feature_definition.py    # 几何特征识别模块
│   ├── feature_definition_optimized.py # 优化版几何特征识别模块
│   ├── gcode_generation.py      # FANUC NC代码生成模块
│   ├── material_tool_matcher.py # 用户描述分析模块
│   ├── mechanical_drawing_expert.py # 机械制图专家系统
│   ├── nc_validator_optimizer.py # NC验证优化模块
│   ├── ocr_ai_inference.py      # OCR与AI推理模块
│   ├── pdf_parsing_process.py   # PDF解析和OCR处理模块
│   ├── project_initialization.py # 项目初始化模块
│   ├── requirement_clarifier.py # 需求澄清模块
│   ├── simple_nc_gui.py         # 简化的NC编程GUI界面
│   ├── simulation_output.py     # 模拟报告生成模块
│   ├── unified_generator.py     # 统一CNC程序生成入口
│   ├── validation.py            # 数据验证模块
│   └── subprocesses/
│       ├── __init__.py
│       └── pdf_parsing_process.py # PDF解析子进程模块
└── utils/
    └── __init__.py
├── tests/
├── start_ai_nc_helper.py        # AI辅助NC编程工具启动脚本
└── start_server.py              # 服务器启动脚本
```

## 技术栈

### 依赖库

- **PyMuPDF** - PDF文档处理
- **Pillow** - 图像处理
- **pytesseract** - OCR文字识别
- **opencv-python** - 计算机视觉和图像处理
- **numpy** - 数值计算
- **spacy** - 自然语言处理
- **torch, transformers** - AI模型
- **flask, flask-cors** - Web API服务

### 核心技术

- **计算机视觉** - 使用 OpenCV 识别几何特征
- **图像处理** - 高斯模糊、边缘检测、轮廓识别、形态学操作
- **OCR技术** - 从图纸中提取文字信息
- **机器学习** - 特征识别和形状分类
- **几何分析** - 坐标系统转换、特征匹配
- **多模态AI** - 整合OCR、视觉识别和自然语言处理

## 使用方法

### 命令行方式

```bash
# 启动图形界面
python start_ai_nc_helper.py gui

# 处理PDF生成NC代码
python start_ai_nc_helper.py process drawing.pdf "请加工3个φ22沉孔，深度20mm" "Aluminum"

# 运行演示
python start_ai_nc_helper.py demo

# 查看帮助
python start_ai_nc_helper.py help
```

### 直接运行主程序

```bash
# 基本用法
python src/main.py process <pdf_path> <user_description> [scale] [coordinate_strategy]

# 示例
python src/main.py process part_design.pdf "请加工一个100mm x 50mm的矩形，使用铣削加工" 1.0 highest_y

# 坐标策略选项: highest_y, lowest_y, leftmost_x, rightmost_x, center, custom, geometric_center
```

### 图形界面

运行 `python start_ai_nc_helper.py gui` 启动图形界面，支持：

- 拖拽导入 PDF、图像等格式文件
- 一键识别主要加工特征
- 简单确认界面，减少用户操作
- 工艺模板拖拽：将预定义工艺直接拖到特征上
- 点击特征直接调整相关参数
- 支持导出到CamBam、Mastercam、Fusion 360等格式

### 测试运行

项目使用pytest进行测试，运行方式如下：

```bash
# 运行所有测试
pytest

# 运行特定测试文件
pytest tests/test_config.py

# 运行特定目录下的测试
python -m pytest tests/
```

## 核心模块详解

### 特征识别模块 (feature_definition.py)

- **形状识别** - 识别圆形、矩形、三角形、椭圆、多边形等
- **复合特征** - 识别沉孔（同心圆特征）和螺纹孔
- **坐标系统** - 支持多种坐标原点选择策略
- **尺寸提取** - 根据比例尺提取实际尺寸
- **置信度评估** - 对识别结果进行置信度评分
- **重复特征过滤** - 过滤位置相近的重复识别结果

### NC 代码生成模块 (gcode_generation.py)

- **FANUC 标准** - 生成符合 FANUC 系统的 G 代码
- **安全指令** - 包含刀具补偿、冷却液控制、安全高度等
- **工艺循环** - 支持 G81, G82, G83, G84 等固定循环
- **复合工艺** - 支持多刀具的完整加工工艺（如攻丝的点孔→钻孔→攻丝）
- **螺纹加工** - 支持M系列螺纹的攻丝工艺
- **极坐标加工** - 支持极坐标系下的孔位加工
- **配置化参数** - 通过配置文件管理加工参数

### 图纸分析模块 (mechanical_drawing_expert.py)

- **制图规则** - 理解机械制图标准
- **特征关联** - 将几何特征与加工要求关联
- **工程判断** - 基于工程知识进行特征识别
- **文本分析** - 从图纸文本中提取关键信息

### AI辅助NC编程工具 (ai_nc_helper.py)

- **快速特征检测** - 使用预训练模型快速识别常见特征
- **智能工艺库** - 基于特征类型智能推荐工艺参数
- **智能工艺选择器** - 根据识别的特征选择合适的加工工艺
- **简单NC代码生成器** - 根据特征和工艺参数生成NC代码
- **CAM插件接口** - 用于与主流CAM软件集成

### 统一生成器模块 (unified_generator.py)

- **AI驱动生成** - 使用AI模型直接生成NC代码
- **OCR推理** - 从PDF中提取特征信息
- **传统方法** - 基于图像处理的传统特征识别
- **混合方法** - 根据特征完整性决定使用哪种方法
- **特征完整性评估** - 评估图纸信息的完整性

### 配置管理 (config.py)

- **图像处理参数** - 配置图像处理相关参数
- **特征识别参数** - 配置特征识别相关参数
- **G代码生成参数** - 配置G代码生成相关参数
- **螺纹参数映射** - M系列螺纹的螺距映射
- **刀具映射** - 刀具类型到刀具编号的映射
- **安全参数** - 安全高度、延时等参数

## 开发约定

### 代码风格

- 遵循 PEP 8 Python 编码规范
- 使用类型提示增强代码可读性
- 详细的函数文档字符串
- 使用配置文件管理魔法数字

### 测试

项目使用pytest框架进行全面测试，包含以下测试类型：

- `tests/test_config.py` - 配置模块测试
- `tests/test_core_modules.py` - 核心模块测试
- `tests/test_exceptions.py` - 异常处理测试
- `tests/test_resource_manager.py` - 资源管理测试

### 错误处理

- 输入验证 - 验证 PDF 路径、用户描述等输入
- OCR 异常处理 - OCR 失败时跳过并继续处理
- 特征识别容错 - 未识别到特征时生成默认程序
- NC代码验证 - 验证生成的NC代码的正确性
- 文件路径安全 - 防止路径遍历攻击

## 部署说明

1. 安装 Python 3.8+ 环境
2. 安装依赖：`pip install -r requirements.txt`
3. 安装 Tesseract OCR（如果需要 OCR 功能）
4. 运行：`python start_ai_nc_helper.py gui`
5. 配置pytest：`python -m pytest` 运行测试

## 项目特点

1. **智能化** - 基于 AI 的特征识别和工艺推荐
2. **自动化** - 从图纸到 NC 代码的一键式处理
3. **标准化** - 生成符合工业标准的 FANUC G 代码
4. **灵活性** - 支持多种坐标系统和加工工艺
5. **易用性** - 提供图形界面和命令行两种操作方式
6. **扩展性** - 模块化设计，易于添加新功能
7. **插件式架构** - 支持与主流CAM软件集成
8. **多模态AI** - 整合OCR、视觉识别和自然语言处理
9. **配置化** - 通过配置文件管理参数，便于定制

## 应用场景

- 机械加工企业的快速编程
- 小批量多品种生产
- 工程师快速验证设计方案
- 作为现有 CAM 软件的补充工具
- 教学和培训用途
- 快速原型制作
- 数控机床操作培训