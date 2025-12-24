"""
调试基准特征查找问题
"""
import sys
import os
import re
sys.path.append(os.path.join(os.path.dirname(__file__), 'src'))

def debug_baseline_finding():
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
    
    # 测试正则表达式
    baseline_matches = re.findall(r'φ(\d+\.?\d*)', drawing_text)
    print("φ匹配结果:", baseline_matches)
    
    # 手动检查每个匹配
    for match in baseline_matches:
        try:
            baseline_diameter = float(match)
            print(f"匹配到直径: {baseline_diameter}")
            for i, feature in enumerate(circle_features):
                feature_diameter = feature.get("radius", 0) * 2
                print(f"  特征{i+1}直径: {feature_diameter}, 误差: {abs(feature_diameter - baseline_diameter)}")
                if abs(feature_diameter - baseline_diameter) <= baseline_diameter * 0.05:
                    print(f"    -> 匹配成功! 特征{i+1}作为基准")
                    print(f"       位置: {feature['center']}, 半径: {feature['radius']}")
                    return feature
        except ValueError:
            continue
    
    print("没有找到匹配的基准特征，返回最大圆:")
    max_feature = max(circle_features, key=lambda x: x.get("radius", 0))
    print(f"  最大圆: 位置{max_feature['center']}, 半径{max_feature['radius']}, 直径{max_feature['radius']*2}")
    
    return max_feature

if __name__ == "__main__":
    debug_baseline_finding()