"""
验证修复后的基准特征查找
"""
import sys
import os
import re
sys.path.append(os.path.join(os.path.dirname(__file__), 'src'))

from src.modules.feature_definition import find_baseline_feature

def verify_fix():
    # 模拟数据
    circle_features = [
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
        {
            "shape": "circle", 
            "center": (592.0, 406.0),
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
            "center": (500.0, 594.0),
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
            "center": (408.0, 406.0),
            "radius": 11.0,  # φ22的半径
            "circularity": 0.91,
            "confidence": 0.87,
            "area": 380,
            "bounding_box": (397, 395, 22, 22),
            "contour": [],
            "aspect_ratio": 1.0
        },
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
    
    drawing_text = "右侧视图 φ22 深20 φ14.5贯通 φ234基准圆 PCD 188"
    
    print("图纸文本:", drawing_text)
    
    # 测试修复后的基准查找
    baseline_feature = find_baseline_feature(circle_features, drawing_text)
    print(f"找到的基准特征: 位置{baseline_feature['center']}, 半径{baseline_feature['radius']}, 直径{baseline_feature['radius']*2}")
    
    expected_baseline = circle_features[0]  # 应该是第一个特征 (φ234)
    if baseline_feature == expected_baseline:
        print("✓ 修复成功: 正确识别了φ234作为基准圆")
        return True
    else:
        print("✗ 修复失败: 没有正确识别φ234作为基准圆")
        return False

if __name__ == "__main__":
    verify_fix()