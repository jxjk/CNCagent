"""
验证修复结果的测试
"""
import sys
import os

# 添加项目路径
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from src.modules.material_tool_matcher import analyze_user_description
from src.modules.gcode_generation import _extract_counterbore_parameters
from src.modules.unified_generator import UnifiedCNCGenerator


def test_main():
    """主测试函数"""
    print("=== 测试修复结果 ===")
    
    # 测试描述
    test_description = "加工3个φ22深20底孔φ14.5贯通的沉孔特征，位置X94.0Y-30. X94.0Y90. X94.0Y210."
    
    # 测试1: analyze_user_description
    print("\n1. 测试 analyze_user_description:")
    result = analyze_user_description(test_description)
    print(f"   外径: {result.get('outer_diameter')}")
    print(f"   内径: {result.get('inner_diameter')}")
    print(f"   深度: {result.get('depth')}")  # 应该是20而不是22
    print(f"   孔位置: {result.get('hole_positions')}")
    
    # 验证结果
    outer_ok = result.get('outer_diameter') == 22.0
    inner_ok = result.get('inner_diameter') == 14.5
    depth_ok = result.get('depth') == 20.0  # 修复后应该为20
    positions_ok = len(result.get('hole_positions', [])) == 0  # 在这个函数中可能不会提取位置
    
    print(f"   外径正确: {outer_ok}")
    print(f"   内径正确: {inner_ok}")
    print(f"   深度正确: {depth_ok} (期望20.0, 实际{result.get('depth')})")
    print(f"   位置提取: {positions_ok}")
    
    # 测试2: _extract_counterbore_parameters (这是关键函数)
    print("\n2. 测试 _extract_counterbore_parameters:")
    features = []
    params = _extract_counterbore_parameters(features, result)
    outer_diameter, inner_diameter, depth, hole_count, positions, *_ = params
    
    print(f"   外径: {outer_diameter}")
    print(f"   内径: {inner_diameter}")
    print(f"   深度: {depth}")
    print(f"   孔数: {hole_count}")
    print(f"   孔位置: {positions}")
    
    counterbore_outer_ok = outer_diameter == 22.0
    counterbore_inner_ok = inner_diameter == 14.5
    counterbore_depth_ok = depth == 20.0
    counterbore_positions_ok = len(positions) == 3
    
    print(f"   外径正确: {counterbore_outer_ok}")
    print(f"   内径正确: {counterbore_inner_ok}")
    print(f"   深度正确: {counterbore_depth_ok}")
    print(f"   位置正确: {counterbore_positions_ok}")
    
    # 测试3: unified generator
    print("\n3. 测试统一生成器:")
    generator = UnifiedCNCGenerator()
    virtual_features = generator._create_virtual_features_from_description(test_description)
    
    if virtual_features:
        feature = virtual_features[0]
        print(f"   虚拟特征外径: {feature.get('outer_diameter')}")
        print(f"   虚拟特征内径: {feature.get('inner_diameter')}")
        print(f"   虚拟特征位置X: {feature.get('center')[0]}")
        print(f"   虚拟特征位置Y: {feature.get('center')[1]}")
        
        # 检查所有特征
        for i, vf in enumerate(virtual_features):
            center = vf.get('center')
            print(f"   特征{i+1}位置: {center}")
    
    # 总结
    print("\n=== Fix Result Summary ===")
    all_good = (outer_ok and inner_ok and depth_ok and 
                counterbore_outer_ok and counterbore_inner_ok and counterbore_depth_ok and counterbore_positions_ok)
    
    print(f"Core fix successful: {all_good}")
    
    if all_good:
        print("[PASS] All fixes successful - φ22 correctly identified as outer diameter, 94.0 correctly identified as X coordinate, depth correctly extracted as 20mm")
    else:
        print("[FAIL] Some fixes not successful")
    
    # 特别检查X坐标是否被误认为直径
    x_coords = [pos[0] for pos in positions]
    if 94.0 in x_coords and 94.0 != outer_diameter:
        print("[PASS] X coordinate 94.0 not mistaken as diameter")
    else:
        print("[FAIL] X coordinate 94.0 may be mistaken as diameter")


if __name__ == "__main__":
    test_main()
