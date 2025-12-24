"""
验证G代码生成中的直径值
"""
import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), 'src'))

from src.modules.feature_definition import identify_counterbore_features, adjust_coordinate_system
from src.modules.gcode_generation import generate_fanuc_nc

def test_diameter_display():
    """
    测试G代码中直径值的显示
    """
    print("测试G代码中直径值的显示...")
    
    # 模拟从图纸中识别到的圆形特征
    mock_features = [
        {
            "shape": "counterbore",
            "center": (100.0, 100.0),
            "radius": 11.0,  # φ22的半径
            "outer_diameter": 22.0,  # 沉孔直径
            "inner_diameter": 14.5,  # 底孔直径
            "circularity": 0.9,
            "confidence": 0.9,
            "area": 380,
            "bounding_box": (90, 90, 20, 20),
            "contour": [],
            "aspect_ratio": 1.0,
            "depth": 20.0
        },
        {
            "shape": "counterbore", 
            "center": (200.0, 100.0),
            "radius": 11.0,  # φ22的半径
            "outer_diameter": 22.0,  # 沉孔直径
            "inner_diameter": 14.5,  # 底孔直径
            "circularity": 0.9,
            "confidence": 0.85,
            "area": 380,
            "bounding_box": (190, 90, 20, 20),
            "contour": [],
            "aspect_ratio": 1.0,
            "depth": 20.0
        },
        {
            "shape": "counterbore",
            "center": (150.0, 200.0), 
            "radius": 11.0,  # φ22的半径
            "outer_diameter": 22.0,  # 沉孔直径
            "inner_diameter": 14.5,  # 底孔直径
            "circularity": 0.88,
            "confidence": 0.88,
            "area": 380,
            "bounding_box": (140, 190, 20, 20),
            "contour": [],
            "aspect_ratio": 1.0,
            "depth": 20.0
        }
    ]
    
    # 用户描述包含3个沉孔的加工需求
    user_description = "加工3个φ22深20底孔φ14.5贯通的沉孔特征"
    
    description_analysis = {
        "processing_type": "counterbore",
        "description": user_description,
        "depth": 20.0,
        "tool_required": "counterbore_tool"
    }
    
    gcode = generate_fanuc_nc(mock_features, description_analysis)
    
    print("生成的G代码片段:")
    lines = gcode.split('\n')
    for line in lines:
        if 'COUNTERBORE' in line and ('φ' in line):
            print(f"  {line.strip()}")
    
    # 检查是否包含正确的直径值
    has_correct_diameter = False
    for line in lines:
        if 'φ22.0' in line and 'COUNTERBORE' in line:
            has_correct_diameter = True
            print(f"✓ 找到正确的直径值: {line.strip()}")
    
    if has_correct_diameter:
        print("\n✓ 测试通过: G代码中正确显示了直径值")
        return True
    else:
        print("\n✗ 测试失败: G代码中没有找到正确的直径值")
        return False

if __name__ == "__main__":
    test_diameter_display()