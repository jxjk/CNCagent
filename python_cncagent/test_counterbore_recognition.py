"""
测试沉孔特征识别修复
"""
import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), 'src'))

from src.modules.feature_definition import identify_counterbore_features

def test_counterbore_recognition():
    """
    测试沉孔特征识别功能
    """
    print("开始测试沉孔特征识别...")
    
    # 模拟从图纸中识别到的圆形特征
    mock_features = [
        {
            "shape": "circle",
            "center": (100.0, 100.0),
            "radius": 11.0,  # φ22的半径
            "circularity": 0.9,
            "confidence": 0.9,
            "area": 380,
            "bounding_box": (90, 90, 20, 20),
            "contour": []
        },
        {
            "shape": "circle", 
            "center": (200.0, 100.0),
            "radius": 11.0,  # φ22的半径
            "circularity": 0.9,
            "confidence": 0.85,
            "area": 380,
            "bounding_box": (190, 90, 20, 20),
            "contour": []
        },
        {
            "shape": "circle",
            "center": (150.0, 200.0), 
            "radius": 11.0,  # φ22的半径
            "circularity": 0.88,
            "confidence": 0.88,
            "area": 380,
            "bounding_box": (140, 190, 20, 20),
            "contour": []
        },
        {
            "shape": "circle",
            "center": (300.0, 150.0),
            "radius": 7.25,  # φ14.5的半径
            "circularity": 0.92,
            "confidence": 0.8,
            "area": 165,
            "bounding_box": (293, 143, 14, 14),
            "contour": []
        }
    ]
    
    # 用户描述包含3个沉孔的加工需求
    user_description = "加工3个φ22深20底孔φ14.5贯通的沉孔特征"
    
    # 调用沉孔识别函数
    result_features = identify_counterbore_features(mock_features, user_description, "")
    
    # 统计沉孔特征数量
    counterbore_count = len([f for f in result_features if f["shape"] == "counterbore"])
    circle_count = len([f for f in result_features if f["shape"] == "circle"])
    
    print(f"原始圆形特征: 4个")
    print(f"识别后的沉孔特征: {counterbore_count}个")
    print(f"剩余圆形特征: {circle_count}个")
    
    for feature in result_features:
        if feature["shape"] == "counterbore":
            print(f"  沉孔: 位置{feature['center']}, 直径{feature['outer_diameter']:.1f}, 深度{feature['depth']:.1f}, 置信度{feature['confidence']:.2f}")
    
    # 验证结果
    if counterbore_count >= 3:
        print("✓ 测试通过: 正确识别了3个沉孔特征")
        return True
    else:
        print(f"✗ 测试失败: 期望3个沉孔特征，实际识别了{counterbore_count}个")
        return False

if __name__ == "__main__":
    test_counterbore_recognition()