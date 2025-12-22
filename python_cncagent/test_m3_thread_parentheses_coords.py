"""
测试M3螺纹和圆括号坐标格式解析
"""
import os
import sys
import numpy as np
sys.path.append(os.path.join(os.path.dirname(__file__), 'src'))

from src.modules.gcode_generation import generate_fanuc_nc
from src.modules.material_tool_matcher import analyze_user_description

def test_m3_thread_and_parentheses_coords():
    """测试M3螺纹和圆括号坐标格式解析"""
    print("测试M3螺纹和圆括号坐标格式解析...")
    print("="*60)
    
    # 使用用户提供的描述：加工2个M3的螺纹，位置（80,7.5）（80，-7.5）深度6
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
    
    # 检查是否正确识别了M3螺纹和坐标
    has_m3_thread = any('M3 THREAD' in line for line in lines)
    has_correct_positions = all(f'X{pos[0]:.1f},Y{pos[1]:.1f}' in nc_program for pos in [(80.0, 7.5), (80.0, -7.5)])
    has_correct_depth = description_analysis['depth'] == 6.0 if description_analysis['depth'] is not None else False
    
    # 检查底孔直径是否正确（M3应该是2.5mm）
    has_correct_drill_dia = any('HOLE DIAMETER 2.5mm' in line for line in lines)
    
    print(f"\n验证结果:")
    print(f"  - 识别M3螺纹: {'✅' if has_m3_thread else '❌'}")
    print(f"  - 识别正确坐标: {'✅' if has_correct_positions else '❌'}")
    print(f"  - 识别深度6: {'✅' if has_correct_depth else '❌'}")
    print(f"  - M3底孔直径正确(2.5mm): {'✅' if has_correct_drill_dia else '❌'}")
    print(f"  - 总共加工孔数: {'✅' if len(description_analysis['hole_positions']) == 2 else '❌'}")
    
    # 检查是否有2个孔位置
    hole_count = nc_program.count("HOLE") if "HOLE" in nc_program else 0
    position_count = len(description_analysis['hole_positions']) if description_analysis['hole_positions'] else 0
    
    print(f"  - 检测到孔位置数量: {position_count}/2")
    print(f"  - NC程序中孔标记: {hole_count if hole_count > 1 else 'N/A'}")
    
    # 确定各项检查结果
    all_checks = [has_m3_thread, has_correct_positions, has_correct_depth, has_correct_drill_dia, position_count == 2]
    print(f"\n总体结果: {'✅ 全部通过' if all(all_checks) and position_count == 2 else '⚠️ 部分检查未通过'}")
    
    # 保存生成的NC程序
    with open("test_m3_thread_output.nc", "w", encoding="utf-8") as f:
        f.write(nc_program)
    print(f"\nNC程序已保存到: test_m3_thread_output.nc")
    
    return all(all_checks) and position_count == 2

def test_original_case():
    """测试原始情况是否仍然正常工作"""
    print("\n" + "="*60)
    print("测试原始情况是否仍然正常工作...")
    
    # 测试原始的X/Y格式
    user_description = "加工M10螺纹贯穿孔1个，位置X10.0Y-16.0深度14，合理选择加工原点。NC程序使用英文注释。"
    description_analysis = analyze_user_description(user_description)
    print(f"用户描述: {user_description}")
    print(f"识别的孔位置: {description_analysis['hole_positions']}")
    print(f"深度: {description_analysis['depth']}")
    
    features = []
    nc_program = generate_fanuc_nc(features, description_analysis, scale=1.0)
    
    has_x_y_pos = any('X10.0,Y-16.0' in line for line in nc_program.split('\n'))
    has_m10_thread = any('M10 THREAD' in line for line in nc_program.split('\n'))
    has_depth_14 = description_analysis['depth'] == 14.0 if description_analysis['depth'] is not None else False
    
    print(f"  - X/Y坐标格式解析: {'✅' if has_x_y_pos else '❌'}")
    print(f"  - M10螺纹识别: {'✅' if has_m10_thread else '❌'}")
    print(f"  - 深度14识别: {'✅' if has_depth_14 else '❌'}")
    
    return has_x_y_pos and has_m10_thread and has_depth_14

def main():
    """运行所有测试"""
    print("CNC Agent M3螺纹和圆括号坐标格式解析测试")
    print("="*60)
    print("检查项目:")
    print("- 解析圆括号格式坐标 (80,7.5) (80,-7.5)")
    print("- 识别M3螺纹规格及相应参数")
    print("- 正确解析深度值6")
    print("- 保持原有功能正常工作")
    print()
    
    test1_result = test_m3_thread_and_parentheses_coords()
    test2_result = test_original_case()
    
    print("\n" + "="*60)
    print("测试总结:")
    print(f"  - M3螺纹和圆括号坐标测试: {'✅ 通过' if test1_result else '❌ 未通过'}")
    print(f"  - 原始功能兼容性测试: {'✅ 通过' if test2_result else '❌ 未通过'}")
    
    if test1_result and test2_result:
        print("\n🎉 所有测试通过！CNC Agent现在能够：")
        print("  - 解析圆括号格式的坐标 (80,7.5) (80,-7.5)")
        print("  - 识别M3螺纹规格并使用正确的底孔直径(2.5mm)")
        print("  - 正确解析深度值6")
        print("  - 保持对原有格式(X/Y坐标、M10螺纹等)的兼容性")
        print("  - 生成符合FANUC规范的注释格式")
    else:
        print("\n⚠️  部分测试未通过，请检查代码实现。")
    
    return test1_result and test2_result

if __name__ == "__main__":
    main()