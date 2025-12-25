# Test parameter confusion fix
Verify that the system can correctly identify φ22 as the counterbore outer diameter, not mistake 94.0 as the diameter

import sys
import os
import re

# 添加项目路径
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from src.modules.material_tool_matcher import _extract_counterbore_diameters, analyze_user_description
from src.modules.gcode_generation import _extract_counterbore_parameters
from src.modules.unified_generator import UnifiedCNCGenerator


def test_diameter_extraction():
    """测试直径提取功能"""
    print("=== 测试直径提取功能 ===")
    
    # 测试目标描述：加工3个φ22深20底孔φ14.5贯通的沉孔特征
    test_description = "加工3个φ22深20底孔φ14.5贯通的沉孔特征"
    
    outer_diameter, inner_diameter = _extract_counterbore_diameters(test_description)
    print(f"提取结果 - 外径: {outer_diameter}, 内径: {inner_diameter}")
    
    # 验证结果
    if outer_diameter == 22.0 and inner_diameter == 14.5:
        print("✓ 直径提取正确: φ22为外径，φ14.5为内径")
    else:
        print(f"✗ 直径提取错误: 期望外径22.0，内径14.5，实际得到外径{outer_diameter}，内径{inner_diameter}")
    
    # 测试包含极坐标位置的描述
    test_description2 = "加工3个φ22深20底孔φ14.5贯通的沉孔特征，位置X94.0Y-30. X94.0Y90. X94.0Y210."
    
    # 分析描述
    analysis_result = analyze_user_description(test_description2)
    print(f"分析结果: {analysis_result}")
    
    # 检查直径是否正确提取
    expected_outer = 22.0
    expected_inner = 14.5
    
    actual_outer = analysis_result.get('outer_diameter')
    actual_inner = analysis_result.get('inner_diameter')
    
    print(f"分析结果中的直径 - 外径: {actual_outer}, 内径: {actual_inner}")
    
    if actual_outer == expected_outer and actual_inner == expected_inner:
        print("✓ 分析结果中的直径提取正确")
    else:
        print(f"✗ 分析结果中的直径提取错误: 期望({expected_outer}, {expected_inner})，实际({actual_outer}, {actual_inner})")
    
    # 检查孔位置是否正确提取
    hole_positions = analysis_result.get('hole_positions', [])
    print(f"提取的孔位置: {hole_positions}")
    
    expected_positions = [(94.0, -30.0), (94.0, 90.0), (94.0, 210.0)]
    
    # 检查是否有正确的孔位置（顺序可能不同）
    correct_positions = 0
    for exp_pos in expected_positions:
        for act_pos in hole_positions:
            if abs(exp_pos[0] - act_pos[0]) < 0.1 and abs(exp_pos[1] - act_pos[1]) < 0.1:
                correct_positions += 1
                break
    
    if correct_positions == len(expected_positions):
        print("✓ 孔位置提取正确")
    else:
        print(f"✗ 孔位置提取错误: 期望{len(expected_positions)}个位置，实际正确{correct_positions}个")
    
    # 检查X94.0是否被误认为直径
    if 94.0 in [pos[0] for pos in hole_positions] and 94.0 != actual_outer:
        print("✓ X坐标94.0正确识别为位置而非直径")
    else:
        print("✗ X坐标94.0可能被误认为直径")


def test_counterbore_parameter_extraction():
    """测试沉孔参数提取功能"""
    print("\n=== 测试沉孔参数提取功能 ===")
    
    # 模拟特征列表（空）
    features = []
    
    # 模拟描述分析结果
    description_analysis = {
        "description": "加工3个φ22深20底孔φ14.5贯通的沉孔特征，位置X94.0Y-30. X94.0Y90. X94.0Y210.",
        "outer_diameter": 22.0,
        "inner_diameter": 14.5,
        "hole_positions": [(94.0, -30.0), (94.0, 90.0), (94.0, 210.0)]
    }
    
    try:
        params = _extract_counterbore_parameters(features, description_analysis)
        outer_diameter, inner_diameter, depth, hole_count, positions, centering_depth, drilling_depth, drill_feed, counterbore_spindle_speed, counterbore_feed = params
        
        print(f"提取的参数 - 外径: {outer_diameter}, 内径: {inner_diameter}, 深度: {depth}, 孔数: {hole_count}")
        print(f"孔位置: {positions}")
        
        # 验证直径参数
        if outer_diameter == 22.0 and inner_diameter == 14.5:
            print("✓ 沉孔参数提取正确")
        else:
            print(f"✗ 沉孔参数提取错误: 期望外径22.0，内径14.5，实际({outer_diameter}, {inner_diameter})")
        
        # 验证孔位置
        expected_positions = [(94.0, -30.0), (94.0, 90.0), (94.0, 210.0)]
        if len(positions) == len(expected_positions):
            print("✓ 孔位置数量正确")
        else:
            print(f"✗ 孔位置数量错误: 期望{len(expected_positions)}个，实际{len(positions)}个")
            
    except Exception as e:
        print(f"✗ 参数提取失败: {e}")


def test_unified_generator():
    """测试统一生成器的虚拟特征创建"""
    print("\n=== 测试统一生成器虚拟特征创建 ===")
    
    generator = UnifiedCNCGenerator()
    
    # 测试描述，包含沉孔直径和位置信息
    test_description = "加工3个φ22沉孔，深度20mm，底孔φ14.5贯通，位置X94.0Y-30. X94.0Y90. X94.0Y210."
    
    try:
        virtual_features = generator._create_virtual_features_from_description(test_description)
        print(f"创建的虚拟特征: {virtual_features}")
        
        # 检查是否创建了正确的沉孔特征
        counterbore_features = [f for f in virtual_features if f['shape'] == 'counterbore']
        
        if counterbore_features:
            feature = counterbore_features[0]  # 检查第一个特征
            outer_dia = feature.get('outer_diameter')
            inner_dia = feature.get('inner_diameter')
            
            print(f"虚拟特征中的直径 - 外径: {outer_dia}, 内径: {inner_dia}")
            
            if outer_dia == 22.0 and inner_dia == 14.5:
                print("✓ 虚拟特征中的直径正确")
            else:
                print(f"✗ 虚拟特征中的直径错误: 期望(22.0, 14.5)，实际({outer_dia}, {inner_dia})")
        else:
            print("✗ 未创建沉孔特征")
            
    except Exception as e:
        print(f"✗ 虚拟特征创建失败: {e}")


def main():
    """主测试函数"""
    print("开始测试CNC Agent参数混淆修复...")
    
    test_diameter_extraction()
    test_counterbore_parameter_extraction()
    test_unified_generator()
    
    print("\n测试完成！")


if __name__ == "__main__":
    main()
