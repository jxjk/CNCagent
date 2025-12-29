# CNC Agent 新功能使用指南

## 1. 特征完整性评估

### 功能说明
CNC Agent现在具备特征完整性评估功能，能够检测用户描述和图纸中的信息缺失，并提供改进建议。

### 使用方法
该功能默认启用，当系统检测到信息不完整时会记录警告日志。

## 2. 3D模型支持

### 支持的格式
- STL (立体光刻)
- STEP/STP (标准交换格式)
- IGES/IGS (初始图形交换规范)
- OBJ (Wavefront格式)
- PLY (多边形文件格式)
- OFF (对象文件格式)
- GLTF/GLB (GL传输格式)

### 命令行使用
```bash
# 仅使用PDF
python src/main.py process drawing.pdf "请加工一个φ20的孔" 1.0 highest_y

# 同时使用PDF和3D模型（推荐）
python src/main.py process drawing.pdf model.stl "请加工一个φ20的孔" 1.0 highest_y

# 使用STEP格式的3D模型
python src/main.py process drawing.pdf model.step "请加工一个φ20的孔" 1.0 highest_y
```

### 3D模型处理流程
1. 加载3D模型文件
2. 提取几何特征（顶点数、面数、体积、表面积等）
3. 检测几何基元（平面、圆柱面等）
4. 将3D特征信息整合到AI提示中
5. 生成更精确的NC代码

## 3. 改进的交互式信息补充

### 功能说明
系统现在能够：
- 检测缺失的关键信息（坐标、深度、直径、加工类型等）
- 生成针对性的查询问题
- 验证用户提供的响应格式

### 信息验证规则
- 坐标格式：支持 X100 Y50, (100, 50), X=100, Y=50 等格式
- 深度格式：支持 20mm, 20, 深20 等格式
- 直径格式：支持 φ22, 22, 直径22mm 等格式
- 加工类型：钻孔、沉孔、攻丝、铣削、车削

## 4. API调用示例

### Python API
```python
from src.modules.unified_generator import generate_cnc_with_unified_approach

# 基本使用（仅PDF）
nc_code = generate_cnc_with_unified_approach(
    user_prompt="请加工3个φ22沉孔，深度20mm",
    pdf_path="drawing.pdf"
)

# 使用3D模型
nc_code = generate_cnc_with_unified_approach(
    user_prompt="请加工3个φ22沉孔，深度20mm",
    pdf_path="drawing.pdf",
    model_3d_path="model.stl"
)

# 禁用完整性检查
nc_code = generate_cnc_with_unified_approach(
    user_prompt="请加工3个φ22沉孔，深度20mm",
    pdf_path="drawing.pdf",
    enable_completeness_check=False
)
```

### 混合方法API
```python
from src.modules.unified_generator import generate_cnc_with_hybrid_approach

nc_code = generate_cnc_with_hybrid_approach(
    user_prompt="请加工3个φ22沉孔，深度20mm",
    pdf_path="drawing.pdf",
    model_3d_path="model.stl"
)
```

## 5. 启动器使用

### 统一启动器
```bash
# 同时启动GUI和Web服务器
python start_unified.py

# 仅启动GUI
python start_unified.py gui

# 仅启动Web服务器
python start_unified.py web

# 同时启动并指定端口
python start_unified.py both --port 8080
```

## 6. 环境变量配置

### API密钥设置
```bash
# DeepSeek API（优先使用）
export DEEPSEEK_API_KEY="your_deepseek_api_key"
export DEEPSEEK_MODEL="deepseek-chat"  # 默认
export DEEPSEEK_API_BASE="https://api.deepseek.com"  # 默认

# OpenAI API（备选）
export OPENAI_API_KEY="your_openai_api_key"
export OPENAI_MODEL="gpt-3.5-turbo"  # 默认
```

## 7. 错误处理

### 常见错误及解决方案
1. **缺少依赖库**：
   - 3D模型处理：`pip install open3d` 或 `pip install trimesh`
   - 图像处理：`pip install opencv-python`

2. **文件格式错误**：
   - 确保3D模型格式正确
   - 检查文件路径是否存在

3. **API密钥错误**：
   - 检查环境变量设置
   - 确保API密钥有效

## 8. 性能优化

### 处理大型3D模型
- 对于大型STL文件，建议先简化模型
- 使用边界框信息进行快速特征定位
- 优先处理用户描述中的关键特征

### 完整性检查配置
- 在生产环境中，可以根据需要调整完整性检查的严格程度
- 对于已知高质量输入，可以禁用完整性检查以提高性能