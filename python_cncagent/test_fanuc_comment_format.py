"""
测试FANUC NC程序注释规范
"""
import os
import sys
import numpy as np
import re  # 添加正则表达式导入
sys.path.append(os.path.join(os.path.dirname(__file__), 'src'))

from src.modules.gcode_generation import generate_fanuc_nc
from src.modules.material_tool_matcher import analyze_user_description

def test_fanuc_comment_format():
    """测试FANUC NC程序注释格式"""
    print("测试FANUC NC程序注释格式...")
    print("="*60)
    print("FANUC注释规范检查:")
    print("1. 程序头部注释: O0001 (MAIN PROGRAM), (DESCRIPTION: ...), (DATE: ...)")
    print("2. 段落注释: (ROUGHING OPERATION), (FINISHING CONTOUR)等")
    print("3. 参数注释: (TOOL CHANGE - T01: ...), (MILLIMETER UNITS)等")
    print("4. 括号格式注释: 用括号而非分号")
    print()
    
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
    
    # 验证生成的代码是否符合FANUC注释规范
    lines = nc_program.split('\n')
    
    # 检查程序头部注释
    has_program_id = any('O0001 (MAIN PROGRAM)' in line for line in lines)
    has_description = any('(DESCRIPTION:' in line for line in lines)
    has_date = any('(DATE:' in line in lines)
    has_author = any('(AUTHOR:' in line for line in lines)
    
    # 检查单位和坐标系统注释
    has_units = any('G21 (MILLIMETER UNITS)' in line for line in lines)
    has_coordinate = any('G90 (ABSOLUTE COORDINATE SYSTEM)' in line for line in lines)
    has_coordinate_setup = any('(COORDINATE SYSTEM SETUP)' in line for line in lines)
    
    # 检查工艺步骤注释
    has_safe_height = any('(MOVE TO SAFE HEIGHT)' in line for line in lines)
    has_tool_change = any('(TOOL CHANGE' in line for line in lines)
    has_operation = any('(STEP' in line for line in lines)  # 检查STEP 1, STEP 2等
    
    # 检查程序结束注释
    has_program_end = any('(PROGRAM END)' in line for line in lines)
    
    # 检查注释格式（是否使用括号而非分号）
    semicolon_comments = [line for line in lines if ';' in line and not '(' in line.split(';')[0]]
    # 仅检查未包含在括号中的分号
    improper_semicolon_lines = []
    for line in lines:
        if ';' in line:
            # 检查分号是否在括号之外（不是在G代码参数中）
            parts = line.split('(', 1)  # 分割第一个左括号前后的部分
            if len(parts) > 1:  # 如果有左括号
                before_paren = parts[0]
                if ';' in before_paren:  # 分号在第一个括号之前
                    if not any(cmd in before_paren for cmd in ['G', 'M', 'T', 'X', 'Y', 'Z', 'F', 'S', 'R', 'Q', 'I', 'J', 'P', 'N', 'U', 'W']):  # 检查是否为G代码行的一部分
                        improper_semicolon_lines.append(line)  # 这是一个独立的注释行，需要检查
            else:
                # 没有括号，检查是否包含G/M代码
                if not any(cmd in line for cmd in ['G', 'M', 'T', 'X', 'Y', 'Z', 'F', 'S', 'R', 'Q', 'I', 'J', 'P', 'N', 'U', 'W']): # 如果不是G代码行
                    if ' ; ' in line:  # 如果有独立的分号注释
                        improper_semicolon_lines.append(line)
    
    print(f"\n验证结果:")
    print(f"  - 程序ID注释: {'✅' if has_program_id else '❌'} {description_analysis['processing_type']}")
    print(f"  - 描述注释: {'✅' if has_description else '❌'}")
    print(f"  - 日期注释: {'✅' if has_date else '❌'}")
    print(f"  - 作者注释: {'✅' if has_author else '❌'}")
    print(f"  - 单位注释: {'✅' if has_units else '❌'}")
    print(f"  - 坐标系统注释: {'✅' if has_coordinate else '❌'}")
    print(f"  - 坐标设置注释: {'✅' if has_coordinate_setup else '❌'}")
    print(f"  - 安全高度注释: {'✅' if has_safe_height else '❌'}")
    print(f"  - 刀具更换注释: {'✅' if has_tool_change else '❌'}")
    print(f"  - 工艺步骤注释: {'✅' if has_operation else '❌'}")
    print(f"  - 程序结束注释: {'✅' if has_program_end else '❌'}")
    print(f"  - 不合规分号注释: {'❌ 存在' if improper_semicolon_lines else '✅ 无'}")
    if improper_semicolon_lines:
        print(f"    不合规行: {len(improper_semicolon_lines)} 行")
    
    # 检查钻孔深度是否正确计算（使用新公式）
    drilling_depth = None
    tapping_depth = None
    for line in lines:
        if 'G83 Z-' in line and 'Deep hole drilling cycle' in line:
            depth_match = re.search(r'Z-([0-9.]+)', line)
            if depth_match:
                drilling_depth = float(depth_match.group(1))
        elif 'G84 Z-' in line and 'Tapping cycle' in line:
            depth_match = re.search(r'Z-([0-9.]+)', line)
            if depth_match:
                tapping_depth = float(depth_match.group(1))
    
    expected_drilling = 14 + 8.5/3 + 1.5  # 螺纹深度 + 1/3底孔直径 + 1.5
    print(f"  - 钻孔深度计算正确: {'✅' if drilling_depth and abs(drilling_depth - expected_drilling) < 0.01 else '❌'}")
    print(f"    期望: {expected_drilling:.3f}, 实际: {drilling_depth}")
    
    all_checks = [has_program_id, has_description, has_date, has_author, has_units, has_coordinate, 
                  has_coordinate_setup, has_safe_height, has_tool_change, has_operation, has_program_end, 
                  not improper_semicolon_lines, drilling_depth and abs(drilling_depth - expected_drilling) < 0.01]
    
    print(f"\n总体结果: {'✅ 全部通过' if all(all_checks) else '⚠️ 部分检查未通过'}")
    
    # 保存生成的NC程序
    with open("test_fanuc_comment_format.nc", "w", encoding="utf-8") as f:
        f.write(nc_program)
    print(f"\nNC程序已保存到: test_fanuc_comment_format.nc")
    
    return all(all_checks)

def test_with_position_info():
    """测试包含位置信息的注释格式"""
    print("\n" + "="*60)
    print("测试包含位置信息的注释格式...")
    
    user_description = "请加工1个M10的贯穿螺纹孔。螺纹孔的位置X10.0Y-16.0深度14。NC程序使用英文注释。"
    description_analysis = analyze_user_description(user_description)
    features = []
    nc_program = generate_fanuc_nc(features, description_analysis, scale=1.0)
    
    lines = nc_program.split('\n')
    
    # 检查是否包含位置信息注释
    has_position_info = any('POSITION X' in line and 'Y' in line for line in lines)
    has_threading_process = any('THREADING PROCESS' in line for line in lines)
    has_hole_info = any('HOLE' in line for line in lines)
    
    print(f"  - 位置信息注释: {'✅' if has_position_info else '❌'}")
    print(f"  - 螺纹加工注释: {'✅' if has_threading_process else '❌'}")
    print(f"  - 孔信息注释: {'✅' if has_hole_info else '❌'}")
    
    return has_position_info and has_threading_process and has_hole_info

def main():
    """运行所有测试"""
    print("CNC Agent FANUC NC程序注释规范验证测试")
    print("="*60)
    print("检查项目:")
    print("- 程序头部注释 (DESCRIPTION, DATE, AUTHOR)")
    print("- 段落注释 (工艺步骤、安全高度等)")
    print("- 参数注释 (刀具更换、单位等)")
    print("- 括号格式注释 (使用()而非; )")
    print("- 保持钻孔深度计算公式正确性")
    print()
    
    test1_result = test_fanuc_comment_format()
    test2_result = test_with_position_info()
    
    print("\n" + "="*60)
    print("测试总结:")
    print(f"  - 一般注释格式测试: {'✅ 通过' if test1_result else '❌ 未通过'}")
    print(f"  - 位置信息注释测试: {'✅ 通过' if test2_result else '❌ 未通过'}")
    
    if test1_result and test2_result:
        print("\n🎉 所有测试通过！CNC Agent现在生成符合FANUC注释规范的NC程序。")
        print("\n改进包括：")
        print("  - 符合FANUC注释规范的程序头部 (DESCRIPTION, DATE, AUTHOR)")
        print("  - 使用括号格式注释 (PROGRAM OPERATION) 而非分号注释")
        print("  - 工艺步骤标准化注释 (STEP 1, STEP 2, STEP 3)")
        print("  - 刀具更换和操作的标准注释格式")
        print("  - 保持钻孔深度计算公式正确性 (螺纹深度 + 1/3底孔直径 + 1.5)")
        print("  - 包含位置信息的详细注释")
    else:
        print("\n⚠️  部分测试未通过，请检查代码实现。")
    
    return test1_result and test2_result

if __name__ == "__main__":
    main()