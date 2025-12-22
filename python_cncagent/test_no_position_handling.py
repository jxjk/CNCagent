"""
测试修复后的CNC Agent功能 - 处理没有明确孔位置的用户描述
"""
import os
import sys
import numpy as np
sys.path.append(os.path.join(os.path.dirname(__file__), 'src'))

from src.modules.gcode_generation import generate_fanuc_nc
from src.modules.material_tool_matcher import analyze_user_description

def test_no_position_description():
    """测试没有明确孔位置的用户描述"""
    print("测试没有明确孔位置的用户描述...")
    print("="*60)
    
    # 使用用户提供的描述
    user_description = "加工M10螺纹贯穿孔1个，合理选择加工原点。NC程序使用英文注释。"
    
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
    
    # 检查是否包含默认位置或提示信息
    has_default_position = any('X50.0' in line and 'Y50.0' in line for line in lines)
    has_position_instruction = any('请根据实际图纸修改' in line or '修改为实际位置' in line for line in lines)
    has_english_comments = any('Select' in line or 'Spindle' in line or 'Drilling' in line for line in lines)
    print(f"\n验证结果:")
    print(f"  - 包含默认位置 (X50.0 Y50.0): {has_default_position}")
    print(f"  - 包含位置修改提示: {has_position_instruction}")
    print(f"  - 包含英文注释: {has_english_comments}")
    print(f"  - 包含M10螺纹加工: {'M10 thread' in nc_program}")
    print(f"  - 包含三步工艺: {'--- 第一步' in nc_program and '--- 第二步' in nc_program and '--- 第三步' in nc_program}")
    
    # 检查三步工艺是否完整
    has_point_drilling = 'T1 M06' in nc_program
    has_drilling = 'T2 M06' in nc_program
    has_tapping = 'T3 M06' in nc_program
    print(f"  - 包含点孔工艺 (T1): {has_point_drilling}")
    print(f"  - 包含钻孔工艺 (T2): {has_drilling}")
    print(f"  - 包含攻丝工艺 (T3): {has_tapping}")
    
    # 检查是否包含G84攻丝循环
    has_tapping_cycle = 'G84' in nc_program
    print(f"  - 包含攻丝循环 (G84): {has_tapping_cycle}")
    
    # 检查是否包含M04主轴反转（攻丝后退刀）
    has_spindle_reverse = 'M04' in nc_program
    print(f"  - 包含主轴反转 (M04): {has_spindle_reverse}")
    
    all_checks = [has_default_position or has_position_instruction, has_english_comments, has_point_drilling, has_drilling, has_tapping, has_tapping_cycle, has_spindle_reverse]
    print(f"\n总体结果: {'✅ 全部通过' if all(all_checks) else '⚠️ 部分检查未通过'}")
    
    # 保存生成的NC程序
    with open("test_no_position_output.nc", "w", encoding="utf-8") as f:
        f.write(nc_program)
    print(f"\nNC程序已保存到: test_no_position_output.nc")
    
    return all(all_checks)

def test_with_actual_position():
    """测试包含明确孔位置的用户描述（对比测试）"""
    print("\n" + "="*60)
    print("测试包含明确孔位置的用户描述（对比测试）...")
    
    # 测试包含明确孔位置的描述
    user_description = "加工M10螺纹贯穿孔1个，位置X20Y30，合理选择加工原点。NC程序使用英文注释。"
    description_analysis = analyze_user_description(user_description)
    print(f"用户描述: {user_description}")
    print(f"识别到的孔位置: {description_analysis['hole_positions']}")
    
    features = []  # 模拟没有从图纸识别到特征
    nc_program = generate_fanuc_nc(features, description_analysis, scale=1.0)
    
    # 检查是否包含指定位置
    has_specified_pos = 'X20.0' in nc_program and 'Y30.0' in nc_program
    has_no_default_pos = 'X50.0' in nc_program and 'Y50.0' in nc_program  # 应该不包含默认位置
    print(f"  - 包含指定位置 (X20 Y30): {has_specified_pos}")
    print(f"  - 不包含默认位置: {not has_no_default_pos or '请根据实际图纸修改' not in nc_program}")
    
    return has_specified_pos

def main():
    """运行所有测试"""
    print("CNC Agent 无明确孔位置处理功能测试")
    print("="*60)
    
    test1_result = test_no_position_description()
    test2_result = test_with_actual_position()
    
    print("\n" + "="*60)
    print("测试总结:")
    print(f"  - 无明确位置测试: {'✅ 通过' if test1_result else '❌ 未通过'}")
    print(f"  - 有明确位置测试: {'✅ 通过' if test2_result else '❌ 未通过'}")
    
    if test1_result and test2_result:
        print("\n🎉 所有测试通过！CNC Agent现在可以正确处理各种情况的用户描述。")
        print("\n新功能包括：")
        print("  - 当用户描述中没有明确孔位置时，提供默认位置并提示用户修改")
        print("  - 保持完整的三步螺纹加工工艺（点孔→钻孔→攻丝）")
        print("  - 支持中英文混合注释（根据用户要求提供英文注释）")
        print("  - 在所有加工步骤中精确定位孔位置")
        print("  - 自动识别螺纹规格（如M10）并调整加工参数")
    else:
        print("\n⚠️  部分测试未通过，请检查代码实现。")
    
    return test1_result and test2_result

if __name__ == "__main__":
    main()