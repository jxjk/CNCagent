"""
测试FANUC NC程序中新增的切削液控制和刀具长度补偿功能
"""
import os
import sys
import numpy as np
sys.path.append(os.path.join(os.path.dirname(__file__), 'src'))

from src.modules.gcode_generation import generate_fanuc_nc
from src.modules.material_tool_matcher import analyze_user_description

def test_coolant_and_tool_compensation():
    """测试切削液控制和刀具长度补偿"""
    print("测试切削液控制和刀具长度补偿...")
    print("="*60)
    
    # 使用用户描述 - M10螺纹，深度14mm
    user_description = "加工M10螺纹贯穿孔1个，深度14mm，合理选择加工原点。NC程序使用英文注释。"
    
    print(f"用户描述: {user_description}\n")
    
    # 分析用户描述
    description_analysis = analyze_user_description(user_description)
    print(f"分析结果:")
    print(f"  加工类型: {description_analysis['processing_type']}")
    print(f"  深度: {description_analysis['depth']}")
    print(f"  孔位置: {description_analysis['hole_positions']}")
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
    
    # 检查切削液控制 - M08 (开启) 和 M09 (关闭)
    has_m08 = any('M08' in line and 'COOLANT ON' in line for line in lines)
    has_m09 = any('M09' in line and 'COOLANT OFF' in line for line in lines)
    
    # 检查刀具长度补偿 - G43 H_
    has_g43 = any('G43' in line and 'H' in line and 'COMPENSATION' in line for line in lines)
    g43_lines = [line for line in lines if 'G43' in line and 'H' in line and 'COMPENSATION' in line]
    
    # 检查每个加工步骤是否有切削液控制和刀具长度补偿
    # 点孔步骤
    pilot_drilling_section = []
    drilling_section = []
    tapping_section = []
    current_section = None
    
    for line in lines:
        if 'STEP 1: PILOT DRILLING OPERATION' in line:
            current_section = 'pilot'
        elif 'STEP 2: DRILLING OPERATION' in line:
            current_section = 'drill'
        elif 'STEP 3: TAPPING OPERATION' in line:
            current_section = 'tap'
        elif 'PROGRAM END' in line:
            current_section = 'end'
        elif current_section == 'pilot':
            pilot_drilling_section.append(line)
        elif current_section == 'drill':
            drilling_section.append(line)
        elif current_section == 'tap':
            tapping_section.append(line)
    
    # 检查各步骤中是否包含切削液和刀具补偿
    pilot_has_coolant_on = any('M08' in line for line in pilot_drilling_section)
    pilot_has_coolant_off = any('M09' in line for line in pilot_drilling_section)
    pilot_has_tool_comp = any('G43' in line and 'COMPENSATION' in line for line in pilot_drilling_section)
    
    drill_has_coolant_on = any('M08' in line for line in drilling_section)
    drill_has_coolant_off = any('M09' in line for line in drilling_section)
    drill_has_tool_comp = any('G43' in line and 'COMPENSATION' in line for line in drilling_section)
    
    tap_has_coolant_on = any('M08' in line for line in tapping_section)
    tap_has_coolant_off = any('M09' in line for line in tapping_section)
    tap_has_tool_comp = any('G43' in line and 'COMPENSATION' in line for line in tapping_section)
    
    print(f"\n验证结果:")
    print(f"  - M08切削液开启: {'✅' if has_m08 else '❌'}")
    print(f"  - M09切削液关闭: {'✅' if has_m09 else '❌'}")
    print(f"  - G43刀具长度补偿: {'✅' if has_g43 else '❌'}")
    print(f"  - G43补偿行: {len(g43_lines)} 行")
    for g_line in g43_lines:
        print(f"    {g_line.strip()}")
    print()
    print(f"  点孔步骤:")
    print(f"    - 刀具补偿: {'✅' if pilot_has_tool_comp else '❌'}")
    print(f"    - 切削液开启: {'✅' if pilot_has_coolant_on else '❌'}")
    print(f"    - 切削液关闭: {'✅' if pilot_has_coolant_off else '❌'}")
    print(f"  钻孔步骤:")
    print(f"    - 刀具补偿: {'✅' if drill_has_tool_comp else '❌'}")
    print(f"    - 切削液开启: {'✅' if drill_has_coolant_on else '❌'}")
    print(f"    - 切削液关闭: {'✅' if drill_has_coolant_off else '❌'}")
    print(f"  攻丝步骤:")
    print(f"    - 刀具补偿: {'✅' if tap_has_tool_comp else '❌'}")
    print(f"    - 切削液开启: {'✅' if tap_has_coolant_on else '❌'}")
    print(f"    - 切削液关闭: {'✅' if tap_has_coolant_off else '❌'}")
    
    all_checks = [has_m08, has_m09, has_g43, pilot_has_tool_comp, pilot_has_coolant_on, pilot_has_coolant_off, 
                  drill_has_tool_comp, drill_has_coolant_on, drill_has_coolant_off,
                  tap_has_tool_comp, tap_has_coolant_on, tap_has_coolant_off]
    
    print(f"\n总体结果: {'✅ 全部通过' if all(all_checks) else '⚠️ 部分检查未通过'}")
    
    # 保存生成的NC程序
    with open("test_coolant_tool_compensation.nc", "w", encoding="utf-8") as f:
        f.write(nc_program)
    print(f"\nNC程序已保存到: test_coolant_tool_compensation.nc")
    
    return all(all_checks)

def test_drilling_with_coolant_and_compensation():
    """测试钻孔加工中的切削液和刀具补偿"""
    print("\n" + "="*60)
    print("测试钻孔加工中的切削液和刀具补偿...")
    
    user_description = "请对工件进行钻孔加工，深度10mm。NC程序使用英文注释。"
    description_analysis = analyze_user_description(user_description)
    features = []  # 假设有一些圆形特征用于钻孔
    # 添加一个模拟的圆形特征
    mock_features = [{"shape": "circle", "center": (50, 50), "radius": 5}]
    
    nc_program = generate_fanuc_nc(mock_features, description_analysis, scale=1.0)
    
    lines = nc_program.split('\n')
    
    has_drill_m08 = any('M08 (COOLANT ON)' in line for line in lines)
    has_drill_m09 = any('M09 (COOLANT OFF)' in line for line in lines)
    has_drill_g43 = any('G43 H2 Z100.' in line for line in lines)  # 钻头通常是T2
    
    print(f"  - 钻孔程序M08切削液开启: {'✅' if has_drill_m08 else '❌'}")
    print(f"  - 钻孔程序M09切削液关闭: {'✅' if has_drill_m09 else '❌'}")
    print(f"  - 钻孔程序G43刀具补偿: {'✅' if has_drill_g43 else '❌'}")
    
    return has_drill_m08 and has_drill_m09 and has_drill_g43

def main():
    """运行所有测试"""
    print("CNC Agent 切削液控制和刀具长度补偿功能验证测试")
    print("="*60)
    print("检查项目:")
    print("- M08切削液开启指令")
    print("- M09切削液关闭指令")
    print("- G43 H_刀具长度补偿指令")
    print("- 各加工步骤中的功能完整性")
    print()
    
    test1_result = test_coolant_and_tool_compensation()
    test2_result = test_drilling_with_coolant_and_compensation()
    
    print("\n" + "="*60)
    print("测试总结:")
    print(f"  - 螺纹加工测试: {'✅ 通过' if test1_result else '❌ 未通过'}")
    print(f"  - 钻孔加工测试: {'✅ 通过' if test2_result else '❌ 未通过'}")
    
    all_tests_passed = test1_result and test2_result
    
    if all_tests_passed:
        print("\n🎉 所有测试通过！CNC Agent现在：")
        print("  - 在各加工步骤中正确添加切削液控制 (M08/M09)")
        print("  - 在换刀后激活刀具长度补偿 (G43 H_)")
        print("  - 符合FANUC标准的完整加工流程")
    else:
        print("\n⚠️  部分测试未通过，请检查代码实现。")
    
    return all_tests_passed

if __name__ == "__main__":
    main()