import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__)))

from src.modules.feature_definition import identify_counterbore_features
from src.modules.gcode_generation import generate_fanuc_nc

def test_counterbore_feature_recognition():
    """测试沉孔特征识别功能"""
    print("开始测试沉孔特征识别功能...")
    
    # 创建测试用的同心圆特征（模拟φ22沉孔和φ14.5底孔）
    test_features = [
        # 第一个沉孔位置
        {'shape': 'circle', 'center': (100, 100), 'radius': 11, 'circularity': 0.9, 'confidence': 0.8, 'contour': [], 'bounding_box': (90, 90, 20, 20), 'area': 380},
        {'shape': 'circle', 'center': (100, 100), 'radius': 7.25, 'circularity': 0.9, 'confidence': 0.8, 'contour': [], 'bounding_box': (93, 93, 14.5, 14.5), 'area': 166},
        # 第二个沉孔位置
        {'shape': 'circle', 'center': (200, 100), 'radius': 11, 'circularity': 0.9, 'confidence': 0.8, 'contour': [], 'bounding_box': (190, 90, 20, 20), 'area': 380},
        {'shape': 'circle', 'center': (200, 100), 'radius': 7.25, 'circularity': 0.9, 'confidence': 0.8, 'contour': [], 'bounding_box': (193, 93, 14.5, 14.5), 'area': 166},
        # 第三个沉孔位置
        {'shape': 'circle', 'center': (300, 100), 'radius': 11, 'circularity': 0.9, 'confidence': 0.8, 'contour': [], 'bounding_box': (290, 90, 20, 20), 'area': 380},
        {'shape': 'circle', 'center': (300, 100), 'radius': 7.25, 'circularity': 0.9, 'confidence': 0.8, 'contour': [], 'bounding_box': (293, 93, 14.5, 14.5), 'area': 166},
        # 第四个位置（应该被忽略，因为我们只想要3个孔）
        {'shape': 'circle', 'center': (400, 100), 'radius': 11, 'circularity': 0.9, 'confidence': 0.8, 'contour': [], 'bounding_box': (390, 90, 20, 20), 'area': 380},
        {'shape': 'circle', 'center': (400, 100), 'radius': 7.25, 'circularity': 0.9, 'confidence': 0.8, 'contour': [], 'bounding_box': (393, 93, 14.5, 14.5), 'area': 166},
    ]

    # 测试用户描述中包含3个孔的信息
    user_description = "加工3个φ22深20底孔φ14.5贯通的沉孔特征，使用点孔、钻孔、沉孔工艺。坐标原点（0,0）选择正视图φ234的圆的圆心最高点。"
    
    result = identify_counterbore_features(test_features, user_description, "图纸信息")
    
    counterbore_features = [f for f in result if f.get("shape") == "counterbore"]
    
    print(f"输入的圆形特征数量: {len(test_features)}")
    print(f"识别到的沉孔特征数量: {len(counterbore_features)}")
    
    for i, feature in enumerate(counterbore_features):
        print(f"  沉孔 {i+1}: 位置{feature['center']}, 外径{feature['outer_diameter']:.1f}, 内径{feature['inner_diameter']:.1f}, 深度{feature['depth']:.1f}")
    
    # 验证是否只识别到3个沉孔
    assert len(counterbore_features) == 3, f"期望识别到3个沉孔，但实际识别到{len(counterbore_features)}个"
    
    print("✓ 沉孔特征识别测试通过!")
    

def test_gcode_generation():
    """测试G代码生成"""
    print("\n开始测试G代码生成...")
    
    # 创建3个沉孔特征
    features = [
        {
            'shape': 'counterbore', 
            'center': (-14.000, 1588.000), 
            'outer_diameter': 22.0, 
            'inner_diameter': 14.5, 
            'depth': 20.0,
            'contour': [], 
            'bounding_box': (-25, 1577, 22, 22), 
            'area': 380,
            'confidence': 0.9
        },
        {
            'shape': 'counterbore', 
            'center': (-139.000, 1539.000), 
            'outer_diameter': 22.0, 
            'inner_diameter': 14.5, 
            'depth': 20.0,
            'contour': [], 
            'bounding_box': (-150, 1528, 22, 22), 
            'area': 380,
            'confidence': 0.9
        },
        {
            'shape': 'counterbore', 
            'center': (28.000, 897.000), 
            'outer_diameter': 22.0, 
            'inner_diameter': 14.5, 
            'depth': 20.0,
            'contour': [], 
            'bounding_box': (17, 886, 22, 22), 
            'area': 380,
            'confidence': 0.9
        }
    ]
    
    description_analysis = {
        "description": "加工3个φ22深20底孔φ14.5贯通的沉孔特征，使用点孔、钻孔、沉孔工艺",
        "processing_type": "counterbore",
        "depth": 20.0,
        "feed_rate": 100.0
    }
    
    nc_code = generate_fanuc_nc(features, description_analysis)
    
    # 检查NC代码中是否包含正确的孔数量信息
    lines = nc_code.split('\n')
    
    # 计算包含"HOLE"的行数（孔标注）- 只计算实际的孔位置标注
    hole_lines = [line for line in lines if "HOLE" in line and "POSITION" in line and "COUNTERBORE PROCESS" not in line]
    print(f"NC程序中标注的孔数量: {len(hole_lines)}")
    
    for line in hole_lines:
        print(f"  {line.strip()}")
    
    # 验证是否生成了3个孔的加工代码
    assert len(hole_lines) == 3, f"期望生成3个孔的加工代码，但实际生成了{len(hole_lines)}个"
    
    print("✓ G代码生成测试通过!")
    

if __name__ == "__main__":
    try:
        test_counterbore_feature_recognition()
        test_gcode_generation()
        print("\n✓ 所有测试通过！修复成功。")
    except Exception as e:
        print(f"\n✗ 测试失败: {e}")
        import traceback
        traceback.print_exc()
