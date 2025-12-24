"""
最终验证测试 - 模拟用户遇到的问题场景
"""
import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), 'src'))

from src.modules.feature_definition import identify_counterbore_features, adjust_coordinate_system, extract_highest_y_center_point
from src.modules.gcode_generation import generate_fanuc_nc

def test_original_user_scenario():
    """
    模拟用户遇到的原始问题场景
    用户报告：系统只检测到1个位置而不是3个沉孔位置，位置显示为(0,0)
    """
    print("开始模拟原始用户场景...")
    
    # 模拟从图纸中识别到的特征，其中 (1063, 86) 是Y坐标最高的点，会被选为坐标原点
    mock_features = [
        {
            "shape": "circle",
            "center": (1063.0, 86.0),  # Y坐标最高点，将作为坐标原点(0,0)
            "radius": 8.0,  # 小圆，可能是定位标记
            "circularity": 0.9,
            "confidence": 0.88,
            "area": 200,
            "bounding_box": (1055, 78, 16, 16),
            "contour": [],
            "aspect_ratio": 1.0
        },
        {
            "shape": "circle", 
            "center": (940.0, 116.0),  # 相对于原点: X=-123, Y=30
            "radius": 11.0,  # φ22的半径
            "circularity": 0.9,
            "confidence": 0.9,
            "area": 380,
            "bounding_box": (929, 105, 22, 22),
            "contour": [],
            "aspect_ratio": 1.0
        },
        {
            "shape": "circle",
            "center": (1063.0, 176.0),  # 相对于原点: X=0, Y=90
            "radius": 11.0,  # φ22的半径
            "circularity": 0.88,
            "confidence": 0.85,
            "area": 380,
            "bounding_box": (1052, 165, 22, 22),
            "contour": [],
            "aspect_ratio": 1.0
        },
        {
            "shape": "circle",
            "center": (1063.0, 296.0),  # 相对于原点: X=0, Y=210
            "radius": 11.0,  # φ22的半径
            "circularity": 0.92,
            "confidence": 0.88,
            "area": 380,
            "bounding_box": (1052, 285, 22, 22),
            "contour": [],
            "aspect_ratio": 1.0
        },
        {
            "shape": "circle",
            "center": (1100.0, 150.0),  # 另一个圆形特征
            "radius": 7.25,  # φ14.5的半径
            "circularity": 0.85,
            "confidence": 0.8,
            "area": 165,
            "bounding_box": (1093, 143, 14, 14),
            "contour": [],
            "aspect_ratio": 1.0
        }
    ]
    
    print("原始特征 (模拟图纸识别结果):")
    for i, f in enumerate(mock_features):
        print(f"  特征{i+1}: {f['shape']} at {f['center']}, radius {f['radius']}, conf {f['confidence']:.2f}")
    
    # 获取坐标原点 (Y坐标最高的点)
    origin = extract_highest_y_center_point(mock_features)
    print(f"\n坐标原点 (Y坐标最高点): {origin}")
    
    # 应用坐标系统调整 (使用highest_y策略)
    adjusted_features = adjust_coordinate_system(mock_features, (0, 0), "highest_y")
    
    print(f"\n坐标变换后特征 (原点: {origin}):")
    for i, f in enumerate(adjusted_features):
        print(f"  特征{i+1}: {f['shape']} at {f['center']}, radius {f['radius']}, conf {f['confidence']:.2f}")
    
    # 用户描述包含3个沉孔的加工需求
    user_description = "加工3个φ22深20底孔φ14.5贯通的沉孔特征，使用点孔、钻孔、沉孔工艺。坐标原点（0,0）选择正视图φ234的圆的圆心最高点。"
    
    # 调用沉孔识别函数
    result_features = identify_counterbore_features(adjusted_features, user_description, "")
    
    # 统计沉孔特征数量
    counterbore_count = len([f for f in result_features if f["shape"] == "counterbore"])
    circle_count = len([f for f in result_features if f["shape"] == "circle"])
    
    print(f"\n沉孔特征识别结果:")
    print(f"  识别后的沉孔特征: {counterbore_count}个")
    print(f"  剩余圆形特征: {circle_count}个")
    
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
    
    print(f"\n生成的G代码片段:")
    lines = gcode.split('\n')
    for line in lines:
        if 'COUNTERBORE PROCESS' in line:
            print(f"  {line.strip()}")
        elif 'HOLE' in line and ('POSITION' in line):
            print(f"  {line.strip()}")
        elif 'COUNTERBORE' in line and ('X' in line or 'Y' in line):
            print(f"  {line.strip()}")
        elif 'POLAR' in line:
            print(f"  {line.strip()}")
    
    # 检查G代码中是否包含3个孔的加工指令
    hole_count_gcode = 0
    hole_positions = []
    for line in lines:
        if 'HOLE' in line and 'POSITION' in line and 'COUNTERBORE' in line:
            hole_count_gcode += 1
            # 提取坐标信息
            import re
            x_match = re.search(r'X([+-]?\d+\.?\d*)', line)
            y_match = re.search(r'Y([+-]?\d+\.?\d*)', line)
            if x_match and y_match:
                x, y = float(x_match.group(1)), float(y_match.group(1))
                hole_positions.append((x, y))
    
    print(f"\nG代码中检测到的孔位置数量: {len(hole_positions)}")
    for i, pos in enumerate(hole_positions):
        print(f"  孔{i+1}位置: X{pos[0]:.3f}, Y{pos[1]:.3f}")
    
    # 验证结果
    success = True
    if counterbore_count >= 3:
        print("\n✓ 修复成功: 正确识别了3个沉孔特征")
    else:
        print(f"\n✗ 修复失败: 期望3个沉孔特征，实际识别了{counterbore_count}个")
        success = False
    
    if len(hole_positions) >= 3:
        print("✓ G代码生成成功: 生成了3个孔的位置信息")
    else:
        print(f"✗ G代码生成失败: 期望3个孔位置，实际生成了{len(hole_positions)}个")
        success = False
    
    # 检查是否不再显示为单个(0,0)位置
    if len(hole_positions) > 1 or (len(hole_positions) == 1 and hole_positions[0] != (0.0, 0.0)):
        print("✓ 位置问题修复: 不再只显示单个(0,0)位置")
    else:
        print("✗ 位置问题未修复: 仍然只显示(0,0)位置")
        success = False
    
    if success:
        print("\n🎉 所有测试通过！原始用户问题已修复。")
        print("  - 正确识别了3个沉孔特征")
        print("  - 生成了正确的孔位置信息")
        print("  - 不再只显示单个(0,0)位置")
        return True
    else:
        print("\n❌ 仍有问题需要修复。")
        return False

if __name__ == "__main__":
    test_original_user_scenario()