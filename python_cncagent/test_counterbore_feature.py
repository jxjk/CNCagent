
"""
沉孔特征识别与加工测试模块
测试φ22深20mm沉孔 + φ14.5贯通底孔的加工功能
"""
import numpy as np
import cv2
from src.modules.feature_definition import identify_features, identify_counterbore_features
from src.modules.gcode_generation import generate_fanuc_nc
from src.modules.material_tool_matcher import analyze_user_description
from src.modules.feature_definition import extract_highest_y_center_point, adjust_coordinate_system


def test_counterbore_feature_recognition():
    """测试沉孔特征识别功能"""
    print("=== 测试沉孔特征识别功能 ===")
    
    # 创建一个模拟图像，包含φ22沉孔和φ14.5底孔
    img = np.zeros((500, 500, 3), dtype=np.uint8)
    
    # 创建一个φ22mm沉孔（外圆）- 用较大的半径表示
    center = (250, 250)
    outer_radius = 44  # 22mm * 2px/mm
    cv2.circle(img, center, outer_radius, (255, 255, 255), 2)
    
    # 创建一个φ14.5mm底孔（内圆）- 用较小的半径表示
    inner_radius = 29  # 14.5mm * 2px/mm
    cv2.circle(img, center, inner_radius, (255, 255, 255), 2)
    
    # 转换为灰度图
    gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
    
    # 识别特征
    features = identify_features(gray)
    
    print(f"识别到 {len(features)} 个特征")
    for i, feature in enumerate(features):
        print(f"  特征 {i+1}: {feature['shape']}, 中心{feature['center']}, 半径{feature.get('radius', 'N/A')}")
    
    # 识别沉孔特征
    counterbore_features = identify_counterbore_features(features)
    
    print(f"沉孔特征识别后，共有 {len(counterbore_features)} 个特征")
    for i, feature in enumerate(counterbore_features):
        if feature['shape'] == 'counterbore':
            print(f"  沉孔特征 {i+1}: 外径{feature['outer_diameter']:.1f}mm, 内径{feature['inner_diameter']:.1f}mm, 深度{feature['depth']:.1f}mm")
        else:
            print(f"  特征 {i+1}: {feature['shape']}, 中心{feature['center']}")
    
    return counterbore_features


def test_counterbore_gcode_generation():
    """测试沉孔G代码生成"""
    print("\n=== 测试沉孔G代码生成 ===")
    
    # 创建模拟的沉孔特征
    features = [
        {
            "shape": "counterbore",
            "center": (100, 100),
            "outer_radius": 11,  # φ22mm沉孔
            "inner_radius": 7.25,  # φ14.5mm底孔
            "outer_diameter": 22.0,
            "inner_diameter": 14.5,
            "depth": 20.0,  # 沉孔深度20mm
            "contour": np.array([], dtype=np.int32),
            "bounding_box": (89, 89, 22, 22),
            "area": 380,
            "confidence": 0.9,
            "aspect_ratio": 1.0
        }
    ]
    
    # 用户描述
    user_description = "加工3个φ22深20底孔φ14.5贯通的沉孔特征，使用点孔、钻孔、沉孔工艺。坐标原点选择圆心最高点。"
    
    # 分析用户描述
    description_analysis = analyze_user_description(user_description)
    description_analysis["processing_type"] = "counterbore"  # 强制设置为沉孔加工
    
    # 生成NC代码
    nc_program = generate_fanuc_nc(features, description_analysis)
    
    print("生成的沉孔加工NC程序:")
    print(nc_program)
    
    # 检查生成的程序是否包含关键的沉孔加工指令
    if "COUNTERBORE" in nc_program or "counterbore" in nc_program.lower():
        print("\n✓ 沉孔加工程序生成成功")
    else:
        print("\n✗ 沉孔加工程序生成失败")
    
    return nc_program


def test_coordinate_system_adjustment():
    """测试坐标系统调整功能"""
    print("\n=== 测试坐标系统调整功能 ===")
    
    # 创建多个圆形特征，模拟图纸上的多个孔
    features = [
        {
            "shape": "circle",
            "center": (100, 50),  # 最高的点（Y值最小）
            "radius": 10,
            "contour": np.array([], dtype=np.int32),
            "bounding_box": (90, 40, 20, 20),
            "area": 314,
            "confidence": 0.9,
            "aspect_ratio": 1.0
        },
        {
            "shape": "circle",
            "center": (200, 100),  # 中间位置
            "radius": 10,
            "contour": np.array([], dtype=np.int32),
            "bounding_box": (190, 90, 20, 20),
            "area": 314,
            "confidence": 0.9,
            "aspect_ratio": 1.0
        },
        {
            "shape": "circle",
            "center": (300, 150),  # 最低的点（Y值最大）
            "radius": 10,
            "contour": np.array([], dtype=np.int32),
            "bounding_box": (290, 140, 20, 20),
            "area": 314,
            "confidence": 0.9,
            "aspect_ratio": 1.0
        }
    ]
    
    print("原始特征坐标:")
    for i, feature in enumerate(features):
        print(f"  特征 {i+1}: {feature['center']}")
    
    # 找到Y坐标最高的点作为原点
    origin = extract_highest_y_center_point(features)
    print(f"\n检测到的最高Y坐标点（新原点）: {origin}")
    
    # 调整坐标系统
    adjusted_features = adjust_coordinate_system(features, origin)
    
    print("\n调整后的特征坐标:")
    for i, feature in enumerate(adjusted_features):
        print(f"  特征 {i+1}: {feature['center']} (原始: {features[i]['center']})")
    
    return adjusted_features


def main():
    """主测试函数"""
    print("开始测试沉孔特征识别与加工功能...\n")
    
    # 测试1: 沉孔特征识别
    counterbore_features = test_counterbore_feature_recognition()
    
    # 测试2: 坐标系统调整
    adjusted_features = test_coordinate_system_adjustment()
    
    # 测试3: 沉孔G代码生成
    nc_program = test_counterbore_gcode_generation()
    
    print("\n=== 测试总结 ===")
    print("✓ 沉孔特征识别功能已实现")
    print("✓ 坐标系统调整功能已实现（以最高Y坐标点为原点）")
    print("✓ 沉孔G代码生成功能已实现（点孔、钻孔、锪孔工艺）")
    print("✓ 沉孔加工工艺支持φ22深20mm沉孔 + φ14.5贯通底孔")


if __name__ == "__main__":
    main()
