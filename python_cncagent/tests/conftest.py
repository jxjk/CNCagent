import pytest
import sys
from pathlib import Path

# 添加src目录到Python路径
project_root = Path(__file__).parent.parent
src_path = project_root / "src"
sys.path.insert(0, str(src_path))

# 测试配置
TEST_DATA_DIR = Path(__file__).parent / "test_data"
TEST_OUTPUT_DIR = Path(__file__).parent / "test_output"

# 确保测试数据目录存在
TEST_DATA_DIR.mkdir(exist_ok=True)
TEST_OUTPUT_DIR.mkdir(exist_ok=True)

@pytest.fixture
def sample_pdf_path():
    """提供示例PDF路径的fixture"""
    return str(TEST_DATA_DIR / "sample_drawing.pdf")

@pytest.fixture
def sample_3d_model_path():
    """提供示例3D模型路径的fixture"""
    return str(TEST_DATA_DIR / "sample_model.stl")

@pytest.fixture
def sample_user_description():
    """提供示例用户描述的fixture"""
    return "请加工一个φ22沉孔，深度20mm"

@pytest.fixture
def sample_material():
    """提供示例材料的fixture"""
    return "Aluminum"