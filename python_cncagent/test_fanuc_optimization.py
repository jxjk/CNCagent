"""
测试优化后的FANUC NC程序生成模块
验证简化编程格式、攻丝进给计算和注释规范化功能
"""
import os
import sys
sys.path.append(os.path.join(os.path.dirname(__file__), 'src'))

from src.modules.gcode_generation import generate_fanuc_nc
from src.modules.material_tool_matcher import analyze_user_description
from src.modules.fanuc_optimization import get_thread_pitch, optimize_tapping_cycle, optimize_drilling_cycle

def test_thread_pitch_calculation():
    """测试螺纹螺距计算"""
    print("测试螺纹螺距计算...")
    print("="*50)
    
    test_cases = ["M3", "M4", "M5", "M6", "M8", "M10", "M12", "M20"]
    expected_values = [0.5, 0.7, 0.8, 1.0, 1.25, 1.5, 1.75, 1.5]  # M20使用估算值
    
    all_passed = True
    for thread_type, expected in zip(test_cases, expected_values):
        calculated = get_thread_pitch(thread_type)
        passed = abs(calculated - expected) < 0.01
        status = "✅" if passed else "❌"
        print(f"  {status} {thread_type}: 期望={expected}, 实际={calculated}")
        if not passed:
            all_passed = False
    
    print(f"\n螺纹螺距计算: {'✅ 全部通过' if all_passed else '❌ 部分失败'}")
    return all_passed

def test_tapping_optimization():
    """测试攻丝循环优化"""
    print("\n测试攻丝循环优化...")
    print("="*50)
    
    hole_positions = [(50.0, 50.0), (100.0, 75.0), (150.0, 100.0)]
    tapping_depth = 14.0
    spindle_speed = 300.0
    thread_type = "M10"
    
    optimized_gcode = optimize_tapping_cycle(hole_positions, tapping_depth, spindle_speed, thread_type)
    
    print("优化后的攻丝G代码:")
    for i, line in enumerate(optimized_gcode, 1):
        print(f"  {i:2d}. {line}")
    
    # 验证第一行包含完整的G84循环
    first_line_valid = "G84" in optimized_gcode[0] and "X50.000" in optimized_gcode[0] and "Y50.000" in optimized_gcode[0]
    # 验证后续行仅包含X、Y坐标（简化格式）
    simplified_format_valid = True
    if len(optimized_gcode) > 1:
        for line in optimized_gcode[1:]:
            if "G84" in line or "X50.000" in line or "Y50.000" in line:  # 检查是否有重复的完整指令
                simplified_format_valid = False
                break
    
    # 验证F值计算 (F = S * 螺距 = 300 * 1.5 = 450)
    f_value_correct = False
    for line in optimized_gcode:
        if "F450.0" in line or "F450" in line:
            f_value_correct = True
            break
    
    print(f"\n  第一行完整指令: {'✅' if first_line_valid else '❌'}")
    print(f"  简化编程格式: {'✅' if simplified_format_valid else '❌'}")
    print(f"  F值计算正确: {'✅' if f_value_correct else '❌'} (期望 F=450)")
    
    result = first_line_valid and simplified_format_valid and f_value_correct
    print(f"\n攻丝循环优化: {'✅ 通过' if result else '❌ 失败'}")
    return result

def test_drilling_optimization():
    """测试钻孔循环优化"""
    print("\n测试钻孔循环优化...")
    print("="*50)
    
    hole_positions = [(30.0, 30.0), (80.0, 60.0), (120.0, 90.0)]
    drilling_depth = 12.0
    feed_rate = 100.0
    
    optimized_gcode = optimize_drilling_cycle(hole_positions, drilling_depth, feed_rate)
    
    print("优化后的钻孔G代码:")
    for i, line in enumerate(optimized_gcode, 1):
        print(f"  {i:2d}. {line}")
    
    # 验证第一行包含完整的G83循环
    first_line_valid = "G83" in optimized_gcode[0] and "X30.000" in optimized_gcode[0] and "Y30.000" in optimized_gcode[0]
    # 验证后续行仅包含X、Y坐标（简化格式）
    simplified_format_valid = True
    if len(optimized_gcode) > 1:
        for line in optimized_gcode[1:]:
            if "G83" in line or "X30.000" in line or "Y30.000" in line:  # 检查是否有重复的完整指令
                simplified_format_valid = False
                break
    
    print(f"\n  第一行完整指令: {'✅' if first_line_valid else '❌'}")
    print(f"  简化编程格式: {'✅' if simplified_format_valid else '❌'}")
    
    result = first_line_valid and simplified_format_valid
    print(f"\n钻孔循环优化: {'✅ 通过' if result else '❌ 失败'}")
    return result

def test_full_nc_generation():
    """测试完整的NC程序生成"""
    print("\n测试完整NC程序生成...")
    print("="*50)
    
    user_description = "加工M10的螺纹孔，转速300rpm，深度14mm，位置X100Y50。NC程序使用英文注释。"
    description_analysis = analyze_user_description(user_description)
    features = []
    
    print(f"用户描述: {user_description}")
    print(f"分析结果: 加工类型={description_analysis['processing_type']}, 深度={description_analysis['depth']}, 位置={description_analysis['hole_positions']}")
    
    nc_program = generate_fanuc_nc(features, description_analysis, scale=1.0)
    print("\n生成的完整NC程序:")
    print("-"*40)
    lines = nc_program.split('\n')
    for i, line in enumerate(lines[:30]):  # 只显示前30行
        print(f"{i+1:2d}. {line}")
    if len(lines) > 30:
        print(f"... (还有 {len(lines)-30} 行)")
    print("-"*40)
    
    # 验证程序结构
    has_program_header = any("O0001 (MAIN PROGRAM)" in line for line in lines)
    has_units = any("G21 (MILLIMETER UNITS)" in line for line in lines)
    has_coordinate = any("G90 (ABSOLUTE COORDINATE SYSTEM)" in line for line in lines)
    has_safe_height = any("G00 Z50 (RAPID MOVE TO SAFE HEIGHT)" in line for line in lines)
    
    # 验证攻丝部分
    has_tapping_cycle = any("G84" in line and "TAPPING" in line for line in lines)
    has_correct_feed = any("F450" in line for line in lines)  # M10螺纹，300rpm * 1.5螺距 = 450
    
    print(f"\n程序结构验证:")
    print(f"  程序头: {'✅' if has_program_header else '❌'}")
    print(f"  单位设置: {'✅' if has_units else '❌'}")
    print(f"  坐标系统: {'✅' if has_coordinate else '❌'}")
    print(f"  安全高度: {'✅' if has_safe_height else '❌'}")
    print(f"  攻丝循环: {'✅' if has_tapping_cycle else '❌'}")
    print(f"  正确F值: {'✅' if has_correct_feed else '❌'}")
    
    all_checks = [has_program_header, has_units, has_coordinate, has_safe_height, has_tapping_cycle, has_correct_feed]
    result = all(all_checks)
    print(f"\n完整程序生成: {'✅ 通过' if result else '❌ 失败'}")
    return result

def main():
    """运行所有测试"""
    print("CNC Agent FANUC NC程序优化功能验证测试")
    print("="*60)
    print("测试项目:")
    print("- 螺纹螺距计算准确性")
    print("- 攻丝循环简化编程格式")
    print("- 钻孔循环简化编程格式")
    print("- 攻丝进给计算 (F = S × 螺距)")
    print("- 完整NC程序生成")
    print()
    
    test1_result = test_thread_pitch_calculation()
    test2_result = test_tapping_optimization()
    test3_result = test_drilling_optimization()
    test4_result = test_full_nc_generation()
    
    print("\n"+"="*60)
    print("测试总结:")
    print(f"  - 螺纹螺距计算: {'✅ 通过' if test1_result else '❌ 未通过'}")
    print(f"  - 攻丝循环优化: {'✅ 通过' if test2_result else '❌ 未通过'}")
    print(f"  - 钻孔循环优化: {'✅ 通过' if test3_result else '❌ 未通过'}")
    print(f"  - 完整程序生成: {'✅ 通过' if test4_result else '❌ 未通过'}")
    
    all_tests_passed = test1_result and test2_result and test3_result and test4_result
    
    if all_tests_passed:
        print("\n🎉 所有测试通过！CNC Agent优化功能实现成功：")
        print("  - 准确的螺纹螺距计算")
        print("  - 攻丝进给计算符合 F = S × 螺距 公式")
        print("  - 固定循环中使用简化编程格式")
        print("  - 生成符合FANUC标准的NC程序")
        print("  - 程序结构完整且安全")
    else:
        print("\n⚠️  部分测试未通过，请检查代码实现。")
    
    return all_tests_passed

if __name__ == "__main__":
    main()
