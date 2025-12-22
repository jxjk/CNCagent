"""
测试用户原始问题场景：解析圆括号坐标和M3螺纹
"""
import os
import sys
import numpy as np
sys.path.append(os.path.join(os.path.dirname(__file__), 'src'))

from src.modules.gcode_generation import generate_fanuc_nc
from src.modules.material_tool_matcher import analyze_user_description

def test_original_user_scenario():
    """测试用户原始场景：加工2个M3的螺纹，位置（80,7.5）（80，-7.5）深度6"""
    print("测试用户原始场景...")
    print("="*60)
    
    # 使用用户原始描述
    user_description = "加工2个M3的螺纹，位置（80,7.5）（80，-7.5）深度6。"
    
    print(f"用户描述: {user_description}\n")
    
    # 分析用户描述
    description_analysis = analyze_user_description(user_description)
    print(f"分析结果:")
    print(f"  加工类型: {description_analysis['processing_type']}")
    print(f"  深度: {description_analysis['depth']}")
    print(f"  孔位置: {description_analysis['hole_positions']}")
    print(f"  描述: {description_analysis['description']}")
    print()
    
    # 创建空的特征列表（模拟没有从图纸识别到特征的情况）
    features = []
    
    # 生成NC代码
    print("生成NC代码...")
    nc_program = generate_fanuc_nc(features, description_analysis, scale=1.0)
    print("\n生成的NC程序:")
    print("-"*40)
    print(nc_program)
    print("-"*40)
    
    # 验证生成的代码
    lines = nc_program.split('\n')
    
    # 检查关键要素
    has_m3_thread = any('M3 THREAD' in line for line in lines)
    has_correct_positions = all(f'X{pos[0]:.1f},Y{pos[1]:.1f}' in nc_program for pos in [(80.0, 7.5), (80.0, -7.5)])
    has_correct_depth = description_analysis['depth'] == 6.0 if description_analysis['depth'] is not None else False
    has_correct_drill_dia = any('HOLE DIAMETER 2.5mm' in line for line in lines)
    hole_count = len(description_analysis['hole_positions']) if description_analysis['hole_positions'] else 0
    
    print(f"\n验证结果:")
    print(f"  - 识别M3螺纹: {'✅' if has_m3_thread else '❌'}")
    print(f"  - 识别正确坐标: {'✅' if has_correct_positions else '❌'}")
    print(f"  - 识别深度6: {'✅' if has_correct_depth else '❌'}")
    print(f"  - M3底孔直径正确(2.5mm): {'✅' if has_correct_drill_dia else '❌'}")
    print(f"  - 正确孔数量(2个): {'✅' if hole_count == 2 else '❌'}")
    print(f"  - 所有孔位置正确: {'✅' if hole_count == 2 and has_correct_positions else '❌'}")
    
    # 检查钻孔深度计算是否正确（M3，深度6，底孔直径2.5）
    drilling_depth_expected = 6 + 2.5/3 + 1.5  # 6 + 0.833... + 1.5 = 8.333...
    drilling_depth_actual = None
    for line in lines:
        if 'G83' in line and 'Z-' in line and 'DRILLING CYCLE' in line:
            import re
            match = re.search(r'Z-([0-9.]+)', line)
            if match:
                drilling_depth_actual = float(match.group(1))
                break
    
    print(f"  - 钻孔深度计算正确: {'✅' if drilling_depth_actual and abs(drilling_depth_actual - drilling_depth_expected) < 0.01 else '❌'}")
    if drilling_depth_actual:
        print(f"    期望: {drilling_depth_expected:.3f}, 实际: {drilling_depth_actual:.3f}")
    
    # 检查是否包含FANUC规范注释
    has_fanuc_comments = any('(MAIN PROGRAM)' in line for line in lines)
    
    all_checks = [
        has_m3_thread, 
        has_correct_positions, 
        has_correct_depth, 
        has_correct_drill_dia, 
        hole_count == 2, 
        drilling_depth_actual and abs(drilling_depth_actual - drilling_depth_expected) < 0.01,
        has_fanuc_comments
    ]
    
    print(f"\n总体结果: {'✅ 全部通过' if all(all_checks) else '⚠️ 部分检查未通过'}")
    
    # 保存生成的NC程序
    with open("test_original_user_scenario.nc", "w", encoding="utf-8") as f:
        f.write(nc_program)
    print(f"\nNC程序已保存到: test_original_user_scenario.nc")
    
    return all(all_checks)

def main():
    """运行测试"""
    print("CNC Agent 用户原始场景测试")
    print("="*60)
    print("用户需求：加工2个M3的螺纹，位置（80,7.5）（80，-7.5）深度6")
    print("检查是否已解决以下问题：")
    print("- 解析圆括号格式坐标 (80,7.5) (80,-7.5)")
    print("- 识别M3螺纹规格及相应参数")
    print("- 正确解析深度值6")
    print("- 生成符合FANUC规范的注释格式")
    print("- 保持原有的X/Y坐标格式兼容性")
    print()
    
    test_result = test_original_user_scenario()
    
    print("\n" + "="*60)
    print("测试总结:")
    print(f"  - 用户原始场景测试: {'✅ 通过' if test_result else '❌ 未通过'}")
    
    if test_result:
        print("\n🎉 测试通过！问题已解决：")
        print("  - 成功解析圆括号格式坐标 (80,7.5) (80,-7.5)")
        print("  - 正确识别M3螺纹并使用2.5mm底孔直径")
        print("  - 正确解析深度6并使用新公式计算钻孔深度")
        print("  - 生成2个孔的完整加工程序")
        print("  - 保持FANUC规范注释格式")
        print("\nCNC Agent现在能够准确处理用户描述中的坐标和螺纹规格。")
    else:
        print("\n⚠️  测试未通过，请检查代码实现。")
    
    return test_result

if __name__ == "__main__":
    main()