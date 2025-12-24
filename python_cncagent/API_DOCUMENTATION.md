# CNC Agent API 文档

## 概述

CNC Agent 是一个 AI 辅助的从 PDF 图纸自动生成 FANUC NC 程序的 Python 实现。本项目能够从 PDF 图纸中识别几何特征、理解用户加工描述，并生成符合 FANUC 标准的 G 代码程序。

## 核心模块 API

### 1. Feature Definition 模块

#### identify_features
```python
def identify_features(image: np.ndarray, 
                     min_area: float = None, 
                     min_perimeter: float = None,
                     canny_low: int = None, 
                     canny_high: int = None,
                     gaussian_kernel: tuple = None, 
                     morph_kernel: tuple = None,
                     drawing_text: str = "") -> List[Dict]
```

从图像中识别几何特征（圆形、矩形、多边形等）

**参数：**
- `image`: 输入图像（预处理后的灰度图）
- `min_area`: 最小面积阈值
- `min_perimeter`: 最小周长阈值
- `canny_low`: Canny边缘检测低阈值
- `canny_high`: Canny边缘检测高阈值
- `gaussian_kernel`: 高斯模糊核大小
- `morph_kernel`: 形态学操作核大小
- `drawing_text`: 图纸文本信息

**返回：** 识别出的特征列表

#### identify_counterbore_features
```python
def identify_counterbore_features(features: List[Dict], 
                                user_description: str = "", 
                                drawing_text: str = "") -> List[Dict]
```

识别沉孔（Counterbore）特征

**参数：**
- `features`: 基本特征列表
- `user_description`: 用户描述
- `drawing_text`: 图纸文本

**返回：** 沉孔特征列表

### 2. GCode Generation 模块

#### generate_fanuc_nc
```python
def generate_fanuc_nc(features: List[Dict], 
                     description_analysis: Dict, 
                     scale: float = 1.0) -> str
```

根据识别特征和用户描述生成FANUC NC程序

**参数：**
- `features`: 识别出的几何特征列表
- `description_analysis`: 用户描述分析结果
- `scale`: 比例尺因子

**返回：** 生成的NC程序代码

### 3. Material Tool Matcher 模块

#### analyze_user_description
```python
def analyze_user_description(user_description: str) -> Dict
```

分析用户加工描述并提取工艺参数

**参数：**
- `user_description`: 用户加工描述

**返回：** 包含分析结果的字典，包含加工类型、刀具需求、深度、进给率、主轴转速等信息

### 4. PDF Processing 模块

#### pdf_to_images
```python
def pdf_to_images(pdf_path: str, dpi: int = 150) -> List[Image]
```

将PDF转换为高分辨率图像列表

**参数：**
- `pdf_path`: PDF文件路径
- `dpi`: 输出图像的DPI

**返回：** PIL图像对象列表

#### ocr_image
```python
def ocr_image(image: Image, lang: str = 'chi_sim+eng') -> str
```

对图像进行OCR识别

**参数：**
- `image`: 输入图像
- `lang`: OCR语言，默认中英文

**返回：** 识别出的文本

## 主要业务流程API

### 从PDF生成NC程序
```python
def generate_nc_from_pdf(pdf_path: str, 
                       user_description: str, 
                       scale: float = 1.0,
                       coordinate_strategy: str = "highest_y", 
                       custom_origin: Optional[Tuple[float, float]] = None) -> str
```

完整流程：从PDF图纸和用户描述生成NC程序

**参数：**
- `pdf_path`: PDF图纸路径
- `user_description`: 用户加工描述
- `scale`: 比例尺因子
- `coordinate_strategy`: 坐标基准策略
- `custom_origin`: 自定义原点坐标

**返回：** 生成的NC程序代码

## 配置管理API

### ConfigManager
```python
class ConfigManager:
    def get_config(self, config_name: str) -> Any
    def update_config(self, config_name: str, new_values: Dict[str, Any]) -> bool
    def validate_config(self, config_name: str) -> bool
```

统一的配置管理器

**方法：**
- `get_config`: 获取指定配置
- `update_config`: 更新指定配置
- `validate_config`: 验证配置有效性

## 异常处理

### 自定义异常类型
- `CNCError`: CNC系统基础异常类
- `InputValidationError`: 输入验证异常
- `ProcessingError`: 处理过程异常
- `FeatureRecognitionError`: 特征识别异常
- `PDFProcessingError`: PDF处理异常
- `AIProcessingError`: AI处理异常
- `ConfigurationError`: 配置错误异常
- `FileProcessingError`: 文件处理异常
- `NCGenerationError`: NC代码生成异常
- `ResourceError`: 资源管理异常

## 使用示例

### 基本使用
```python
from src.main import generate_nc_from_pdf

# 生成NC代码
nc_code = generate_nc_from_pdf(
    pdf_path="drawing.pdf",
    user_description="请加工3个φ22沉孔，深度20mm",
    scale=1.0,
    coordinate_strategy="highest_y"
)

print(nc_code)
```

### 特征识别
```python
from src.modules.feature_definition import identify_features
import cv2

# 读取图像
image = cv2.imread("drawing.png", cv2.IMREAD_GRAYSCALE)

# 识别特征
features = identify_features(image)

print(f"识别到 {len(features)} 个特征")
for feature in features:
    print(f"  - {feature['shape']}: {feature['center']}")
```

### 配置管理
```python
from src.config import config_manager

# 获取配置
image_config = config_manager.get_config('IMAGE_PROCESSING_CONFIG')

# 更新配置
config_manager.update_config('IMAGE_PROCESSING_CONFIG', {
    'min_confidence_threshold': 0.8
})

# 验证配置
is_valid = config_manager.validate_config('IMAGE_PROCESSING_CONFIG')
```

## Web API 接口

### 健康检查
- **GET** `/health`
- 检查服务状态

### 生成NC代码
- **POST** `/generate_nc`
- **请求体:**
  ```json
  {
    "pdf": "file",
    "description": "加工描述",
    "scale": 1.0
  }
  ```
- **响应:**
  ```json
  {
    "status": "success",
    "nc_program": "G代码内容",
    "nc_file_path": "临时文件路径"
  }
  ```

## 安全考虑

1. **路径遍历防护**: 所有文件路径都经过验证，确保在允许的目录范围内
2. **输入验证**: 用户输入经过严格验证
3. **异常处理**: 所有异常都经过适当处理，避免信息泄露
4. **配置验证**: 配置值经过验证，防止无效配置导致系统错误