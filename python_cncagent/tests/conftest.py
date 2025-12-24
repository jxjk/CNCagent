"""
pytest配置文件
定义测试夹具和配置
"""
import pytest
import numpy as np
import cv2
from unittest.mock import Mock, patch
import tempfile
import os

from src.modules.feature_definition import identify_features
from src.modules.gcode_generation import generate_fanuc_nc
from src.modules.material_tool_matcher import analyze_user_description


@pytest.fixture
def sample_image():
    """创建一个示例图像用于测试"""
    # 创建一个800x600的黑色图像
    img = np.zeros((600, 800, 3), dtype=np.uint8)
    
    # 在图像上画一个白色的圆形
    center = (400, 300)
    radius = 50
    cv2.circle(img, center, radius, (255, 255, 255), 2)
    
    # 转换为灰度图
    gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
    
    return gray


@pytest.fixture
def sample_feature_data():
    """示例特征数据"""
    return [
        {
            "shape": "circle",
            "center": (100, 100),
            "radius": 10,
            "contour": np.array([[[110, 100]], [[100, 110]], [[90, 100]], [[100, 90]]]),
            "bounding_box": (90, 90, 20, 20),
            "area": 314,
            "dimensions": (20, 20),
            "confidence": 0.9,
            "aspect_ratio": 1.0
        }
    ]


@pytest.fixture
def sample_description_analysis():
    """示例描述分析结果"""
    return {
        "processing_type": "drilling",
        "tool_required": "drill_bit",
        "depth": 10.0,
        "feed_rate": 100.0,
        "spindle_speed": 800,
        "material": "steel",
        "precision": "Ra1.6",
        "hole_positions": [(50, 50), (100, 100)],
        "description": "在钢板上钻两个孔"
    }


@pytest.fixture
def mock_pdf_document():
    """模拟PDF文档对象"""
    mock_doc = Mock()
    mock_doc.get_text.return_value = "Sample drawing text"
    mock_doc.close.return_value = None
    return mock_doc


@pytest.fixture
def temp_image_file():
    """创建临时图像文件"""
    img = np.zeros((200, 200, 3), dtype=np.uint8)
    cv2.circle(img, (100, 100), 50, (255, 255, 255), -1)
    
    temp_file = tempfile.NamedTemporaryFile(suffix='.png', delete=False)
    cv2.imwrite(temp_file.name, img)
    temp_file.close()
    
    yield temp_file.name
    
    # 清理临时文件
    os.unlink(temp_file.name)


@pytest.fixture
def temp_pdf_file():
    """创建临时PDF文件"""
    # 创建一个简单的PDF内容
    pdf_content = b'%PDF-1.4\n1 0 obj\n<<\n/Type /Catalog\n/Pages 2 0 R\n>>\nendobj\n'
    
    temp_file = tempfile.NamedTemporaryFile(suffix='.pdf', delete=False)
    temp_file.write(pdf_content)
    temp_file.close()
    
    yield temp_file.name
    
    # 清理临时文件
    os.unlink(temp_file.name)


@pytest.fixture
def mock_ai_client():
    """模拟AI客户端"""
    with patch('src.modules.ai_driven_generator.openai') as mock_openai:
        mock_completion = Mock()
        mock_completion.choices = [Mock()]
        mock_completion.choices[0].message = Mock()
        mock_completion.choices[0].message.content = "O0001 (TEST PROGRAM)\nG00 X0 Y0\nM30"
        mock_openai.chat.completions.create.return_value = mock_completion
        
        yield mock_openai


@pytest.fixture(autouse=True)
def setup_and_teardown():
    """测试前后的设置和清理"""
    import logging
    # 测试前的设置
    logging.info("Setting up test...")
    
    yield  # 执行测试
    
    # 测试后的清理
    logging.info("Tearing down test...")
