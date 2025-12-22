"""
测试修复后的CNC Agent功能 - 支持从用户描述中提取孔位置
"""
import os
import sys
import numpy as np
sys.path.append(os.path.join(os.path.dirname(__file__), 'src'))

from src.modules.gcode_generation import generate_fanuc_nc
from src.modules.material_tool_matcher import analyze_user_description

def test_hole_position_extraction():
    """测试从用户描述中提取孔位置的功能"""
    print("开始测试从用户描述中提取孔位置功能...")
    print("="*60)
    
    # 使用用户提供的描述
    user_description = "请加工1个M10的贯穿螺纹孔。工件长边与X轴平行，G54原点在工件左上角。螺纹孔的位置X10.0Y-16.0深度14。仔细核对图纸后给出NC程序，NC程序注释部分使用英文。"
    
    print(f"用户描述: {user_description}\n")
    
    # 分析用户描述
    description_analysis = analyze_user_description(user_description)
    print(f"分析结果:")
    print(f"  加工类型: {description_analysis['processing_type']}")
    print(f"  深度: {description_analysis['depth']}")
    print(f"  孔位置: {description_analysis['hole_positions']}")
    print(f"  刀具: {description_analysis['tool_required']}")
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
    
    # 检查是否包含用户指定的孔位置
    has_specified_position = any('X10.0' in line and 'Y-16.0' in line for line in lines)
    print(f"\n验证结果:")
    print(f"  - 包含指定孔位置 (X10.0 Y-16.0): {has_specified_position}")
    print(f"  - 总共识别到 {len(description_analysis['hole_positions'])} 个孔位置")
    print(f"  - 生成了 {nc_program.count('X10.0 Y-16.0')} 个指定位置的加工点（理论上在3个步骤中各出现1次，共3次）")
    
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
    
    all_checks = [has_specified_position, has_point_drilling, has_drilling, has_tapping, has_tapping_cycle, has_spindle_reverse]
    print(f"\n总体结果: {'✅ 全部通过' if all(all_checks) else '⚠️ 部分检查未通过'}")
    
    # 保存生成的NC程序
    with open("test_hole_position_output.nc", "w", encoding="utf-8") as f:
        f.write(nc_program)
    print(f"\nNC程序已保存到: test_hole_position_output.nc")
    
    return all(all_checks)

def test_multiple_positions():
    """测试多个孔位置的情况"""
    print("\n"+"="*60)
    print("测试多个孔位置的情况...")
    
    # 测试包含多个孔位置的描述
    user_description = "加工2个M10螺纹孔，位置X10Y20和X30Y40，深度14mm。使用点孔、钻孔、攻丝三步工艺。"
    description_analysis = analyze_user_description(user_description)
    print(f"用户描述: {user_description}")
    print(f"识别到的孔位置: {description_analysis['hole_positions']}")
    
    features = []  # 模拟没有从图纸识别到特征
    nc_program = generate_fanuc_nc(features, description_analysis, scale=1.0)
    
    # 检查是否包含所有位置
    has_pos1 = 'X10.0' in nc_program and 'Y20.0' in nc_program
    has_pos2 = 'X30.0' in nc_program and 'Y40.0' in nc_program
    print(f"  - 包含位置1 (X10 Y20): {has_pos1}")
    print(f"  - 包含位置2 (X30 Y40): {has_pos2}")
    print(f"  - 总共 {len(description_analysis['hole_positions'])} 个孔位置已处理")
    
    return has_pos1 and has_pos2

def main():
    """运行所有测试"""
    print("CNC Agent 孔位置提取功能测试")
    print("="*60)
    
    test1_result = test_hole_position_extraction()
    test2_result = test_multiple_positions()
    
    print("\n"+"="*60)
    print("测试总结:")
    print(f"  - 单孔位置测试: {'✅ 通过' if test1_result else '❌ 未通过'}")
    print(f"  - 多孔位置测试: {'✅ 通过' if test2_result else '❌ 未通过'}")
    
    if test1_result and test2_result:
        print("\n🎉 所有测试通过！CNC Agent现在可以正确从用户描述中提取孔位置信息。")
        print("\n新功能包括：")
        print("  - 从用户描述中解析孔位置（如 X10.0Y-16.0）")
        print("  - 当图纸中未识别到特征时，使用描述中的位置信息")
        print("  - 保持完整的三步螺纹加工工艺（点孔→钻孔→攻丝）")
        print("  - 在所有加工步骤中精确定位孔位置")
    else:
        print("\n⚠️  部分测试未通过，请检查代码实现。")
    
    return test1_result and test2_result

if __name__ == "__main__":
    main()