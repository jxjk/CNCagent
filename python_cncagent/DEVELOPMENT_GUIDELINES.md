# CNC Agent 开发指南

## 1. 项目结构

```
CNC Agent/
├── src/                    # 源代码
│   ├── __init__.py
│   ├── main.py             # 主程序入口
│   ├── config.py           # 配置管理
│   ├── config_validator.py # 配置验证器
│   ├── exceptions.py       # 异常定义
│   ├── resource_manager.py # 资源管理器
│   └── modules/            # 功能模块
│       ├── __init__.py
│       ├── ai_driven_generator.py     # AI驱动生成器
│       ├── feature_definition.py      # 特征定义
│       ├── feature_definition_optimized.py # 优化的特征定义
│       ├── fanuc_optimization.py      # FANUC优化
│       ├── gcode_generation.py        # G代码生成
│       ├── material_tool_matcher.py   # 材料工具匹配
│       ├── mechanical_drawing_expert.py # 机械制图专家
│       ├── nc_validator_optimizer.py  # NC验证优化器
│       ├── ocr_ai_inference.py        # OCR AI推理
│       ├── pdf_parsing_process.py     # PDF解析处理
│       ├── project_initialization.py  # 项目初始化
│       ├── requirement_clarifier.py   # 需求澄清器
│       ├── simple_nc_gui.py           # 简单NC GUI
│       ├── simulation_output.py       # 模拟输出
│       ├── unified_generator.py       # 统一生成器
│       ├── validation.py              # 验证
│       └── subprocesses/              # 子进程模块
├── tests/                  # 测试代码
│   ├── __init__.py
│   ├── conftest.py         # pytest配置
│   ├── test_config.py      # 配置测试
│   ├── test_core_modules.py # 核心模块测试
│   ├── test_exceptions.py  # 异常测试
│   └── test_resource_manager.py # 资源管理器测试
├── start_ai_nc_helper.py   # AI辅助工具启动器
├── start_server.py         # Web服务启动器
├── requirements.txt        # 依赖列表
├── pytest.ini              # 测试配置
└── ...
```

## 2. 开发环境设置

### 2.1 依赖安装
```bash
pip install -r requirements.txt
```

### 2.2 OCR引擎安装
安装Tesseract OCR引擎：
- Windows: 从 https://github.com/UB-Mannheim/tesseract/wiki 下载安装
- 设置环境变量 `pytesseract.pytesseract.tesseract_cmd` 指向tesseract.exe

### 2.3 运行测试
```bash
# 运行所有测试
pytest

# 运行特定测试文件
pytest tests/test_core_modules.py

# 运行测试并生成覆盖率报告
pytest --cov=src --cov-report=html
```

## 3. 编码规范

### 3.1 Python规范
- 遌循 PEP 8 编码风格
- 使用类型提示增强代码可读性
- 适当的函数和模块文档字符串
- 异常处理使用具体异常类型

### 3.2 代码结构
```python
# 模块头部导入
import os
import sys
from typing import List, Dict, Optional

# 从其他模块导入
from ..config import SOME_CONFIG
from ..exceptions import SomeException

# 常量定义
MODULE_CONSTANT = "value"

# 类定义
class MyClass:
    def __init__(self):
        self.attribute = value
    
    def method(self) -> str:
        """方法文档字符串."""
        return "result"

# 函数定义
def function_name(param: str) -> bool:
    """函数文档字符串."""
    return True
```

### 3.3 异常处理
```python
# 好的做法 - 具体异常类型
def process_data(data: List) -> str:
    if not data:
        raise ValueError("数据不能为空")
    
    try:
        result = complex_operation(data)
        return result
    except ValueError as e:
        # 记录错误并返回用户友好的信息
        logger.error(f"处理数据时出错: {e}")
        raise ProcessingError(f"处理失败: {str(e)}") from e

# 遌止的做法 - 裸露异常
def bad_function(data):
    try:
        # ... 处理逻辑
        pass
    except:  # 不要这样做
        pass    # 也不要这样做
```

## 4. 模块开发指南

### 4.1 新模块创建
1. 在 `src/modules/` 目录下创建新模块
2. 遌循单一职责原则
3. 添加适当的类型提示
4. 包含完整的文档字符串
5. 编写单元测试

### 4.2 模块示例模板
```python
"""
[模块名称]模块
[模块功能描述]
"""
import logging
from typing import List, Dict, Optional, Tuple
from pathlib import Path

# 从其他模块导入
from ..config import GCODE_GENERATION_CONFIG
from ..exceptions import ProcessingError, handle_exception


def process_function(data: List[Dict], params: Dict) -> List[str]:
    """
    处理函数说明
    
    Args:
        data: 输入数据列表
        params: 处理参数字典
    
    Returns:
        处理结果列表
    
    Raises:
        ProcessingError: 处理过程中发生错误
    """
    try:
        # 处理逻辑
        result = []
        for item in data:
            processed_item = process_single_item(item, params)
            result.append(processed_item)
        return result
    except Exception as e:
        error = handle_exception(e, logging.getLogger(__name__), "处理数据时出错")
        raise ProcessingError(f"数据处理失败: {str(error)}") from e


class ProcessorClass:
    """处理器类说明"""
    
    def __init__(self, config: Optional[Dict] = None):
        self.logger = logging.getLogger(self.__class__.__name__)
        self.config = config or {}
    
    def process(self, input_data: str) -> str:
        """处理方法说明"""
        try:
            # 处理逻辑
            result = self._internal_process(input_data)
            return result
        except Exception as e:
            self.logger.error(f"处理失败: {str(e)}")
            raise
```

## 5. 测试开发指南

### 5.1 测试文件结构
```python
"""
测试[模块名称]功能
"""
import pytest
import numpy as np
from unittest.mock import Mock, patch

from src.modules.your_module import your_function, YourClass


class TestYourFunction:
    """测试your_function功能"""
    
    def test_normal_case(self):
        """测试正常情况"""
        result = your_function("valid_input")
        assert result == "expected_output"
    
    def test_edge_case(self):
        """测试边界情况"""
        result = your_function("")
        assert result == "expected_for_empty"
    
    def test_error_case(self):
        """测试错误情况"""
        with pytest.raises(ValueError):
            your_function(None)


@pytest.fixture
def sample_data():
    """示例数据fixture"""
    return {
        "key": "value",
        "number": 42
    }
```

### 5.2 测试最佳实践
- 每个函数至少有1个正常情况测试
- 边界条件测试（空输入、极值等）
- 异常路径测试
- 使用pytest fixtures共享测试数据
- Mock外部依赖

## 6. 配置管理

### 6.1 配置使用
```python
# 导入配置
from src.config import GCODE_GENERATION_CONFIG

# 使用配置
def some_function():
    default_depth = GCODE_GENERATION_CONFIG['drilling']['default_depth']
    safe_height = GCODE_GENERATION_CONFIG['safety']['safe_height']
```

### 6.2 添加新配置
1. 在 `src/config.py` 中的相应配置字典中添加新项
2. 更新配置验证器以验证新配置
3. 在文档中记录新配置的用途

## 7. 异常处理指南

### 7.1 自定义异常
```python
from src.exceptions import CNCError

class CustomModuleError(CNCError):
    """自定义模块异常"""
    pass
```

### 7.2 异常处理
- 使用具体的异常类型
- 适当的日志记录
- 提供用户友好的错误信息
- 使用异常链保留原始错误信息

## 8. 安全开发实践

### 8.1 输入验证
```python
import os
from pathlib import Path

def safe_file_operation(file_path: str):
    # 验证文件路径
    path = Path(file_path)
    base_path = Path.cwd()
    
    # 防止路径遍历攻击
    if not path.resolve().is_relative_to(base_path):
        raise ValueError("文件路径超出允许范围")
    
    # 验证文件类型
    if path.suffix.lower() not in ['.pdf', '.png', '.jpg']:
        raise ValueError("不支持的文件类型")
```

### 8.2 输出净化
- 所有用户输入在输出前进行验证
- 防止代码注入
- 适当的字符转义

## 9. 性能优化

### 9.1 图像处理优化
- 使用适当的数据类型（避免不必要的浮点运算）
- 批量处理图像数据
- 内�用算法复杂度

### 9.2 内存管理
- 及时释放不需要的资源
- 使用生成器处理大量数据
- 避免循环引用

## 10. 调试指南

### 10.1 日志记录
```python
import logging

logger = logging.getLogger(__name__)

def my_function():
    logger.info("开始处理...")
    try:
        # 处理逻辑
        logger.debug("详细处理步骤")
    except Exception as e:
        logger.error(f"处理失败: {e}", exc_info=True)
        raise
```

### 10.2 调试技巧
- 使用配置控制调试输出
- 避免在生产代码中留下print语句
- 使用断点调试复杂问题

## 11. 代码审查清单

- [ ] 是否遵循编码规范
- [ ] 异常处理是否适当
- [ ] 输入验证是否完整
- [ ] 安全考虑是否充分
- [ ] 文档字符串是否完整
- [ ] 类型提示是否正确
- [ ] 测试覆盖率是否充分
- [ ] 性能影响是否考虑

## 12. 提交规范

### 12.1 Git提交消息格式
```
<type>(<scope>): <subject>

<body>

<footer>
```

类型包括：
- feat: 新功能
- fix: 修复错误
- docs: 文档更新
- style: 代码格式调整
- refactor: 代码重构
- test: 测试相关
- chore: 构建过程或辅助工具的变动

### 12.2 示例
```
feat(gcode_generation): 添加攻丝工艺支持

实现完整的攻丝加工流程，包括点孔、钻孔和攻丝三个步骤。
- 添加新的攻丝代码生成函数
- 更新用户描述分析以支持攻丝工艺
- 添加相应的测试用例

Closes #123
```

## 13. 版本发布流程

1. 确保所有测试通过
2. 更新版本号在必要文件中
3. 更新CHANGELOG.md
4. 创建发布分支
5. 进行最终测试
6. 合并到主分支
7. 创建Git标签
8. 构建发布包
</content>