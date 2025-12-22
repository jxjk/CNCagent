"""
测试FANUC NC程序简化格式和正确的攻丝F值计算
"""
import os
import sys
import numpy as np
import re  # 添加正则表达式导入
sys.path.append(os.path.join(os.path.dirname(__file__), 'src'))

from src.modules.gcode_generation import generate_fanuc_nc
from src.modules.material_tool_matcher import analyze_user_description

def test_tapping_feed_calculation():
    """测试攻丝进给计算是否正确 (F = S * 螺距)"""
    print("测试攻丝进给计算...")
    print("="*60)
    
    # 测试M10螺纹，转速300 RPM
    user_description = "加工M10的螺纹孔，转速300rpm，深度14mm，位置X100Y50。NC程序使用英文注释。"
    
    print(f"用户描述: {user_description}\n")
    
    # 分析用户描述
    description_analysis = analyze_user_description(user_description)
    print(f"分析结果:")
    print(f"  加工类型: {description_analysis['processing_type']}")
    print(f"  深度: {description_analysis['depth']}")
    print(f"  孔位置: {description_analysis['hole_positions']}")
    print(f"  主轴转速: {description_analysis.get('spindle_speed', '未指定')}")
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
    
    # 提取攻丝参数
    tapping_spindle_speed = None
    tapping_feed = None
    tapping_depth = None
    
    for line in lines:
        if 'M03 S' in line and 'TAPPING SPEED' in line:
            # 提取主轴转速
            match = re.search(r'M03 S(\d+)', line)
            if match:
                tapping_spindle_speed = int(match.group(1))
        elif 'G84' in line and 'F' in line and 'TAPPING' in line:
            # 提取攻丝循环中的F值和Z深度
            f_match = re.search(r'F([0-9.]+)', line)
            z_match = re.search(r'Z-([0-9.]+)', line)  # 修复：在循环内定义z_match
            if f_match:
                tapping_feed = float(f_match.group(1))
            if z_match:
                tapping_depth = float(z_match.group(1))
        elif 'X' in line and 'Y' in line and 'F' in line and 'TAPPING' in line and not 'G84' in line:
            # 检查简化格式中的F值
            f_match = re.search(r'F([0-9.]+)', line)
            if f_match and tapping_feed is None:  # 只在未找到主循环F值时尝试从简化格式获取
                tapping_feed = float(f_match.group(1))
    
    print(f"\n验证结果:")
    print(f"  - 攻丝主轴转速: {tapping_spindle_speed} RPM")
    print(f"  - 攻丝进给率: {tapping_feed} mm/min")
    print(f"  - 攻丝深度: {tapping_depth} mm")
    
    # 验证F = S * 螺距 (M10粗牙螺距为1.5mm)
    expected_feed = tapping_spindle_speed * 1.5 if tapping_spindle_speed else 0
    print(f"  - 期望进给率 (S * 螺距 = {tapping_spindle_speed} * 1.5): {expected_feed} mm/min")
    print(f"  - 进给率计算正确: {'✅' if tapping_feed and abs(tapping_feed - expected_feed) < 0.1 else '❌'}")
    
    # 检查是否使用了简化编程格式（后续孔只用X、Y坐标）
    simplified_format_used = False
    if len(description_analysis['hole_positions']) > 1:  # 只有在多个孔时才检查简化格式
        tapping_lines = [line for line in lines if 'TAPPING' in line]
        for line in tapping_lines:
            if 'X' in line and 'Y' in line and 'G84' not in line and 'TAPPING' in line:
                # 这是简化格式的孔位置，但需要确保不是第一个孔
                if tapping_lines.index(line) > 0:  # 如果不是第一个包含"TAPPING"的行
                    simplified_format_used = True
                    break
    else:
        # 单个孔时，简化格式不适用，但我们认为这个检查通过
        simplified_format_used = True  # 对于单孔情况，我们不强制要求简化格式
    
    print(f"  - 使用简化编程格式: {'✅' if simplified_format_used or len(description_analysis['hole_positions']) <= 1 else '❌'}")
    if len(description_analysis['hole_positions']) > 1:
        print(f"    (仅在多孔情况下需要简化格式)")
    
    # 检查是否有多个孔位置（如果用户提供了多个位置）
    if len(description_analysis['hole_positions']) > 1:
        tapping_commands = [line for line in lines if 'X' in line and 'Y' in line and ('TAPPING' in line or 'G84' in line)]
        print(f"  - 检测到的攻丝命令数: {len(tapping_commands)} (应等于孔数)")
        print(f"  - 孔数匹配: {'✅' if len(tapping_commands) == len(description_analysis['hole_positions']) else '❌'}")
    
    all_checks = [tapping_spindle_speed is not None, tapping_feed is not None, tapping_depth is not None, tapping_feed and abs(tapping_feed - expected_feed) < 0.1, simplified_format_used or len(description_analysis['hole_positions']) <= 1]
    if len(description_analysis['hole_positions']) > 1:
        all_checks.append(len(tapping_commands) == len(description_analysis['hole_positions']))
    
    print(f"\n总体结果: {'✅ 全部通过' if all(all_checks) else '⚠️ 部分检查未通过'}")
    
    # 保存生成的NC程序
    with open("test_fanuc_simplified_format.nc", "w", encoding="utf-8") as f:
        f.write(nc_program)
    print(f"\nNC程序已保存到: test_fanuc_simplified_format.nc")
    
    return tapping_feed is not None and abs(tapping_feed - expected_feed) < 0.1 and (simplified_format_used or len(description_analysis['hole_positions']) <= 1)

def test_multiple_holes_simplified_format():
    """测试多个孔的简化编程格式"""
    print("\n" + "="*60)
    print("测试多个孔的简化编程格式...")
    
    # 测试多个M6螺纹孔
    user_description = "加工3个M6的螺纹孔，转速400rpm，深度10mm，位置（50,50）（100,75）（150,100）。NC程序使用英文注释。"
    description_analysis = analyze_user_description(user_description)
    print(f"用户描述: {user_description}")
    print(f"检测到的孔位置: {description_analysis['hole_positions']}")
    
    features = []
    nc_program = generate_fanuc_nc(features, description_analysis, scale=1.0)
    
    lines = nc_program.split('\n')
    
    # 检查简化编程格式
    tapping_lines = [line for line in lines if 'X' in line and 'Y' in line and 'TAPPING' in line]
    g84_lines = [line for line in lines if 'G84' in line and 'X' in line and 'Y' in line]
    simplified_lines = [line for line in tapping_lines if 'G84' not in line]  # 不包含G84的是简化格式
    
    print(f"  - G84完整命令数: {len(g84_lines)} (应为1个，第一个孔)")
    print(f"  - 简化格式命令数: {len(simplified_lines)} (应为其余孔)")
    print(f"  - 总攻丝命令数: {len(tapping_lines)} (应等于孔数)")
    
    correct_format = len(g84_lines) == 1 and len(simplified_lines) == len(description_analysis['hole_positions']) - 1
    print(f"  - 简化格式正确: {'✅' if correct_format else '❌'}")
    
    return correct_format
def test_m3_thread_feed_calculation():
    """测试M3螺纹的进给计算"""
    print("\n" + "="*60)
    print("测试M3螺纹进给计算...")
    
    # 测试M3螺纹
    user_description = "加工M3的螺纹孔，转速600rpm，深度6mm，位置X80Y7.5。NC程序使用英文注释。"
    description_analysis = analyze_user_description(user_description)
    
    features = []
    nc_program = generate_fanuc_nc(features, description_analysis, scale=1.0)
    
    lines = nc_program.split('\n')
    
    # 提取参数
    tapping_spindle_speed = None
    tapping_feed = None
    
    for line in lines:
        if 'M03 S' in line and 'TAPPING SPEED' in line:
            match = re.search(r'M03 S(\d+)', line)
            if match:
                tapping_spindle_speed = int(match.group(1))
        elif 'G84' in line and 'F' in line and 'TAPPING' in line:
            f_match = re.search(r'F([0-9.]+)', line)
            if f_match:
                tapping_feed = float(f_match.group(1))
    
    print(f"  - 攻丝主轴转速: {tapping_spindle_speed} RPM")
    print(f"  - 攻丝进给率: {tapping_feed} mm/min")
    
    # M3螺纹标准螺距为0.5mm（粗牙）
    expected_feed = tapping_spindle_speed * 0.5 if tapping_spindle_speed else 0
    print(f"  - 期望进给率 (S * 螺距 = {tapping_spindle_speed} * 0.5): {expected_feed} mm/min")
    print(f"  - M3进给率计算正确: {'✅' if tapping_feed and abs(tapping_feed - expected_feed) < 0.1 else '❌'}")
    
    return tapping_feed and abs(tapping_feed - expected_feed) < 0.1
def main():
    """运行所有测试"""
    print("CNC Agent FANUC简化编程格式和攻丝进给计算验证测试")
    print("="*60)
    print("检查项目:")
    print("- 攻丝进给计算 (F = S × 螺距)")
    print("- 固定循环中的简化编程格式 (后续孔只用X、Y)")
    print("- M系列螺纹规格对应的螺距")
    print()
    
    test1_result = test_tapping_feed_calculation()
    test2_result = test_multiple_holes_simplified_format()
    test3_result = test_m3_thread_feed_calculation()
    
    print("\n" + "="*60)
    print("测试总结:")
    print(f"  - M10螺纹进给计算测试: {'✅ 通过' if test1_result else '❌ 未通过'}")
    print(f"  - 多孔简化格式测试: {'✅ 通过' if test2_result else '❌ 未通过'}")
    print(f"  - M3螺纹进给计算测试: {'✅ 通过' if test3_result else '❌ 未通过'}")
    
    all_tests_passed = test1_result and test2_result and test3_result
    
    if all_tests_passed:
        print("\n🎉 所有测试通过！CNC Agent现在：")
        print("  - 正确计算攻丝进给 F = S × 螺距")
        print("  - 在固定循环中使用简化编程格式")
        print("  - 支持多种螺纹规格的正确螺距")
        print("  - 提高了NC程序的效率和规范性")
    else:
        print("\n⚠️  部分测试未通过，请检查代码实现。")
    
    return all_tests_passed

if __name__ == "__main__":
    main()
