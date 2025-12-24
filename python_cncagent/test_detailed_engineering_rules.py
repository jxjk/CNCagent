"""
详细测试基于工程规则的沉孔特征识别
"""
import sys
import os
import math
sys.path.append(os.path.join(os.path.dirname(__file__), 'src'))

from src.modules.feature_definition import identify_counterbore_features

def test_engineering_rule_based_recognition_detailed():
    """
    详细测试基于工程图纸规则的特征识别
    """
    print("详细测试基于工程图纸规则的沉孔特征识别...")
    
    # 模拟图纸中的特征，包括基准圆（φ234）和分度圆上的孔
    mock_features = [
        # 基准圆 φ234
        {
            "shape": "circle",
            "center": (500.0, 500.0),  # 基准点
            "radius": 117.0,  # φ234的半径
            "circularity": 0.95,
            "confidence": 0.95,
            "area": 42988,  # π * 117^2
            "bounding_box": (383, 383, 234, 234),
            "contour": [],
            "aspect_ratio": 1.0
        },
        # 分度圆PCD 188上的孔 (角度-30°, 90°, 210°)
        {
            "shape": "circle", 
            "center": (592.0, 406.0),  # 角度-30°: (500 + 94*cos(-30°), 500 + 94*sin(-30°)) ≈ (592, 406)
            "radius": 11.0,  # φ22的半径
            "circularity": 0.92,
            "confidence": 0.90,
            "area": 380,
            "bounding_box": (481, 395, 22, 22),
            "contour": [],
            "aspect_ratio": 1.0
        },
        {
            "shape": "circle",
            "center": (500.0, 594.0),  # 角度90°: (500 + 94*cos(90°), 500 + 94*sin(90°)) = (500, 594)
            "radius": 11.0,  # φ22的半径
            "circularity": 0.90,
            "confidence": 0.88,
            "area": 380,
            "bounding_box": (489, 583, 22, 22),
            "contour": [],
            "aspect_ratio": 1.0
        },
        {
            "shape": "circle",
            "center": (408.0, 406.0),  # 角度210°: (500 + 94*cos(210°), 500 + 94*sin(210°)) ≈ (408, 406)
            "radius": 11.0,  # φ22的半径
            "circularity": 0.91,
            "confidence": 0.87,
            "area": 380,
            "bounding_box": (397, 395, 22, 22),
            "contour": [],
            "aspect_ratio": 1.0
        },
        # 其他无关特征
        {
            "shape": "circle",
            "center": (700.0, 700.0),
            "radius": 5.0,  # 小孔
            "circularity": 0.85,
            "confidence": 0.75,
            "area": 78,
            "bounding_box": (695, 695, 10, 10),
            "contour": [],
            "aspect_ratio": 1.0
        }
    ]
    
    # 用户描述包含详细的工程信息
    user_description = "加工3个φ22深20底孔φ14.5贯通的沉孔特征，使用点孔、钻孔、沉孔工艺。分度圆PCD 188，角度-30，90，210。"
    drawing_text = "右侧视图 φ22 深20 φ14.5贯通 φ234基准圆 PCD 188"
    
    print("原始特征:")
    for i, f in enumerate(mock_features):
        shape = f['shape']
        center = f['center']
        radius = f['radius']
        print(f"  特征{i+1}: {shape} at {center}, radius {radius}, conf {f['confidence']:.2f}")
    
    print(f"\n用户描述: {user_description}")
    print(f"图纸文本: {drawing_text}")
    
    # 运行沉孔特征识别
    result_features = identify_counterbore_features(mock_features, user_description, drawing_text)
    
    counterbore_count = len([f for f in result_features if f["shape"] == "counterbore"])
    print(f"\n识别到的沉孔特征数量: {counterbore_count}")
    
    result_counterbores = [f for f in result_features if f["shape"] == "counterbore"]
    for i, feature in enumerate(result_counterbores):
        print(f"  沉孔{i+1}: 位置{feature['center']}, 直径{feature['outer_diameter']:.1f}, 深度{feature['depth']:.1f}, 置信度{feature['confidence']:.2f}")
    
    # 验证结果
    success = True
    if counterbore_count >= 3:
        print("\n✓ 基于工程规则的特征识别成功: 正确识别了3个沉孔特征")
    else:
        print(f"\n✗ 基于工程规则的特征识别失败: 期望3个沉孔特征，实际识别了{counterbore_count}个")
        success = False
    
    # 详细检查位置匹配
    counterbore_positions = [f["center"] for f in result_counterbores]
    expected_positions = [(592.0, 406.0), (500.0, 594.0), (408.0, 406.0)]  # 角度-30°, 90°, 210°
    
    print(f"\n实际识别的位置: {counterbore_positions}")
    print(f"期望的位置: {expected_positions}")
    
    matches = 0
    matched_positions = []
    for exp_pos in expected_positions:
        for act_pos in counterbore_positions:
            dist = math.sqrt((exp_pos[0] - act_pos[0])**2 + (exp_pos[1] - act_pos[1])**2)
            if dist < 10:  # 位置误差在10像素内
                matches += 1
                matched_positions.append((exp_pos, act_pos))
                print(f"  匹配: 期望{exp_pos} -> 实际{act_pos}, 距离{dist:.2f}")
                break  # 每个期望位置只匹配一次
    
    print(f"\n匹配数量: {matches}/3")
    
    if matches >= 3:
        print("✓ 位置识别准确: 识别到了正确的孔位置")
    else:
        print(f"✗ 位置识别不准确: 期望3个位置匹配，实际{matches}个匹配")
        success = False
    
    if success:
        print("\n🎉 基于工程图纸规则的特征识别测试通过！")
        return True
    else:
        print("\n❌ 基于工程图纸规则的特征识别测试失败！")
        return False

if __name__ == "__main__":
    test_engineering_rule_based_recognition_detailed()