# CNC Agent 项目说明

## 项目概述

CNC Agent 是一个 AI 辅助的从 PDF 图纸自动生成 FANUC NC 程序的 Python 实现项目。该项目能够从 PDF 图纸中识别几何特征、理解用户加工描述，并生成符合 FANUC 标准的 G 代码程序。

### 核心功能

1. **PDF 图纸解析与 OCR 处理** - 从 PDF 文件中提取文本和图像信息
2. **几何特征识别** - 识别圆形、矩形、多边形等几何形状及复合特征（如沉孔）
3. **用户描述理解** - 分析用户加工要求并提取工艺参数
4. **FANUC NC 程序生成** - 生成符合 FANUC 控制系统标准的 G 代码
5. **完整流程整合** - 将上述功能整合为一键式处理流程
6. **AI 辅助 NC 编程工具** - 提供图形界面和简化操作

### 支持的加工工艺

- **钻孔加工** - 普通钻孔、深孔钻削
- **攻丝加工** - 完整的螺纹孔加工工艺（点孔→钻孔→攻丝）
- **锪孔/沉孔加工** - φ22 沉孔 + φ14.5 底孔的复合特征加工
- **铣削加工** - 圆形、矩形、三角形等轮廓铣削
- **车削加工** - 外径车削

## 项目架构

```
src/
├── main.py                    # 主程序入口
├── modules/
│   ├── pdf_parsing_process.py  # PDF解析和OCR处理
│   ├── feature_definition.py   # 几何特征识别
│   ├── material_tool_matcher.py # 用户描述分析
│   ├── gcode_generation.py     # FANUC NC代码生成
│   ├── validation.py          # 数据验证
│   ├── simulation_output.py    # 模拟报告生成
│   ├── mechanical_drawing_expert.py # 机械制图专家系统
│   ├── ai_nc_helper.py        # AI辅助NC编程工具核心
│   └── simple_nc_gui.py       # 简化的NC编程GUI界面
└── utils/
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
- **图像处理** - 高斯模糊、边缘检测、轮廓识别
- **OCR技术** - 从图纸中提取文字信息
- **机器学习** - 特征识别和形状分类
- **几何分析** - 坐标系统转换、特征匹配

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
python src/main.py <pdf_path> <user_description> [scale] [coordinate_strategy]

# 示例
python src/main.py part_design.pdf "请加工一个100mm x 50mm的矩形，使用铣削加工" 1.0 highest_y

# 坐标策略选项: highest_y, lowest_y, leftmost_x, rightmost_x, center, custom, geometric_center
```

### 图形界面

运行 `python start_ai_nc_helper.py gui` 启动图形界面，支持：

- 拖拽导入 PDF 文件
- 一键识别几何特征
- 可视化特征展示
- 工艺参数调整
- NC 代码生成与预览
- 代码导出功能

## 核心模块详解

### 特征识别模块 (feature_definition.py)

- **形状识别** - 识别圆形、矩形、三角形、椭圆、多边形等
- **复合特征** - 识别沉孔（同心圆特征）和螺纹孔
- **坐标系统** - 支持多种坐标原点选择策略
- **尺寸提取** - 根据比例尺提取实际尺寸

### NC 代码生成模块 (gcode_generation.py)

- **FANUC 标准** - 生成符合 FANUC 系统的 G 代码
- **安全指令** - 包含刀具补偿、冷却液控制、安全高度等
- **工艺循环** - 支持 G81, G82, G83, G84 等固定循环
- **复合工艺** - 支持多刀具的完整加工工艺（如攻丝的点孔→钻孔→攻丝）

### 图纸分析模块 (mechanical_drawing_expert.py)

- **制图规则** - 理解机械制图标准
- **特征关联** - 将几何特征与加工要求关联
- **工程判断** - 基于工程知识进行特征识别

## 开发约定

### 代码风格

- 遵循 PEP 8 Python 编码规范
- 使用类型提示增强代码可读性
- 详细的函数文档字符串

### 测试

项目包含多个测试文件，用于验证不同功能：

- `test_counterbore_recognition.py` - 沉孔识别测试
- `test_fanuc_optimization.py` - FANUC 代码优化测试
- `test_threaded_hole_improvements.py` - 螺纹孔加工测试
- `test_full_process.py` - 完整流程测试

### 错误处理

- 输入验证 - 验证 PDF 路径、用户描述等输入
- OCR 异常处理 - OCR 失败时跳过并继续处理
- 特征识别容错 - 未识别到特征时生成默认程序

## 部署说明

1. 安装 Python 3.8+ 环境
2. 安装依赖：`pip install -r requirements.txt`
3. 安装 Tesseract OCR（如果需要 OCR 功能）
4. 运行：`python start_ai_nc_helper.py gui`

## 项目特点

1. **智能化** - 基于 AI 的特征识别和工艺推荐
2. **自动化** - 从图纸到 NC 代码的一键式处理
3. **标准化** - 生成符合工业标准的 FANUC G 代码
4. **灵活性** - 支持多种坐标系统和加工工艺
5. **易用性** - 提供图形界面和命令行两种操作方式
6. **扩展性** - 模块化设计，易于添加新功能

## 应用场景

- 机械加工企业的快速编程
- 小批量多品种生产
- 工程师快速验证设计方案
- 作为现有 CAM 软件的补充工具
- 教学和培训用途