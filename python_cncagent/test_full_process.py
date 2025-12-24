"""
测试完整的沉孔加工流程
"""
import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), 'src'))

from src.modules.feature_definition import identify_counterbore_features, adjust_coordinate_system
from src.modules.gcode_generation import generate_fanuc_nc

def test_full_counterbore_process():
    """
    测试完整的沉孔加工流程
    """
    print("开始测试完整的沉孔加工流程...")
    
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
            "contour": [],
            "aspect_ratio": 1.0
        },
        {
            "shape": "circle", 
            "center": (200.0, 100.0),
            "radius": 11.0,  # φ22的半径
            "circularity": 0.9,
            "confidence": 0.85,
            "area": 380,
            "bounding_box": (190, 90, 20, 20),
            "contour": [],
            "aspect_ratio": 1.0
        },
        {
            "shape": "circle",
            "center": (150.0, 200.0), 
            "radius": 11.0,  # φ22的半径
            "circularity": 0.88,
            "confidence": 0.88,
            "area": 380,
            "bounding_box": (140, 190, 20, 20),
            "contour": [],
            "aspect_ratio": 1.0
        },
        {
            "shape": "circle",
            "center": (300.0, 300.0),  # 这个位置应该是坐标变换的参考点
            "radius": 7.25,  # φ14.5的半径
            "circularity": 0.92,
            "confidence": 0.8,
            "area": 165,
            "bounding_box": (293, 293, 14, 14),
            "contour": [],
            "aspect_ratio": 1.0
        }
    ]
    
    # 用户描述包含3个沉孔的加工需求
    user_description = "加工3个φ22深20底孔φ14.5贯通的沉孔特征"
    
    print("原始特征:")
    for i, f in enumerate(mock_features):
        print(f"  特征{i+1}: {f['shape']} at {f['center']}, radius {f['radius']}")
    
    # 应用坐标系统调整 (使用highest_y策略，即Y坐标最小的点作为原点)
    adjusted_features = adjust_coordinate_system(mock_features, (0, 0), "highest_y")
    
    print("\n坐标变换后特征:")
    for i, f in enumerate(adjusted_features):
        print(f"  特征{i+1}: {f['shape']} at {f['center']}, radius {f['radius']}")
    
    # 调用沉孔识别函数
    result_features = identify_counterbore_features(adjusted_features, user_description, "")
    
    # 统计沉孔特征数量
    counterbore_count = len([f for f in result_features if f["shape"] == "counterbore"])
    circle_count = len([f for f in result_features if f["shape"] == "circle"])
    
    print(f"\n识别后的沉孔特征: {counterbore_count}个")
    print(f"剩余圆形特征: {circle_count}个")
    
    for feature in result_features:
        if feature["shape"] == "counterbore":
            print(f"  沉孔: 位置{feature['center']}, 直径{feature['outer_diameter']:.1f}, 深度{feature['depth']:.1f}, 置信度{feature['confidence']:.2f}")
    
    # 生成G代码
    description_analysis = {
        "processing_type": "counterbore",
        "description": user_description,
        "depth": 20.0,
        "tool_required": "counterbore_tool"
    }
    
    gcode = generate_fanuc_nc(result_features, description_analysis)
    
    # 检查G代码中是否包含3个孔的加工指令
    lines = gcode.split('\n')
    hole_count_gcode = 0
    for line in lines:
        if 'COUNTERBORE PROCESS' in line and 'REQUESTED 3 HOLES' in line:
            print(f"\nG代码中检测到: {line.strip()}")
        if 'COUNTERBORE' in line and ('X' in line or 'Y' in line):
            hole_count_gcode += 1
            print(f"  G代码孔指令: {line.strip()}")
    
    print(f"\nG代码中孔加工指令数量: {hole_count_gcode}")
    
    # 验证结果
    success = True
    if counterbore_count >= 3:
        print("✓ 沉孔特征识别通过: 正确识别了3个沉孔特征")
    else:
        print(f"✗ 沉孔特征识别失败: 期望3个沉孔特征，实际识别了{counterbore_count}个")
        success = False
    
    if hole_count_gcode >= 3:  # 至少应该有3个锪孔指令
        print("✓ G代码生成通过: 生成了足够数量的孔加工指令")
    else:
        print(f"✗ G代码生成失败: 期望至少3个孔加工指令，实际生成了{hole_count_gcode}个")
        success = False
    
    if success:
        print("\n✓ 所有测试通过!")
        return True
    else:
        print("\n✗ 部分测试失败!")
        return False

if __name__ == "__main__":
    test_full_counterbore_process()