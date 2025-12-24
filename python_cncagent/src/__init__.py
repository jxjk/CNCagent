"""CNC Agent包初始化"""

# 由于在某些情况下相对导入可能失败，这里使用更安全的导入方式
import sys
import os
from pathlib import Path

# 确保模块路径正确
project_root = Path(__file__).parent.parent
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

import src.config
import src.exceptions
import src.resource_manager
import src.config_validator

# 为保持兼容性，将模块设置为当前包的属性
config = src.config
exceptions = src.exceptions
resource_manager = src.resource_manager
config_validator = src.config_validator

__all__ = ["config", "exceptions", "resource_manager", "config_validator"]