"""
CNC Agent - 单元测试配置
使用pytest框架进行测试
"""
import sys
import os
import pytest
import logging

# 添加项目根目录到Python路径
project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, project_root)

# 配置测试日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

# 测试配置
class TestConfig:
    """测试配置类"""
    
    # 测试数据目录
    TEST_DATA_DIR = os.path.join(os.path.dirname(__file__), 'test_data')
    
    # 临时文件目录
    TEMP_DIR = os.path.join(os.path.dirname(__file__), 'temp')
    
    # 测试用的简单图像尺寸
    TEST_IMAGE_WIDTH = 800
    TEST_IMAGE_HEIGHT = 600
    
    # 测试超时时间（秒）
    TEST_TIMEOUT = 30

# 确保测试目录存在
os.makedirs(TestConfig.TEST_DATA_DIR, exist_ok=True)
os.makedirs(TestConfig.TEMP_DIR, exist_ok=True)