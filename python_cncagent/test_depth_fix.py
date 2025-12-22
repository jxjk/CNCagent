"""
测试修复后的深度设置 - 确保钻孔深度大于攻丝深度
"""
import os
import sys
import numpy as np
import re  # 添加正则表达式导入
sys.path.append(os.path.join(os.path.dirname(__file__), 'src'))

from src.modules.gcode_generation import generate_fanuc_nc
from src.modules.material_tool_matcher import analyze_user_description

def test_depth_settings():
    """测试修复后的深度设置"""
    print("测试修复后的深度设置...")
    print("="*60)
    
    # 使用用户描述
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
    
    # 提取钻孔深度和攻丝深度
    drilling_depth = None
    tapping_depth = None
    
    for line in lines:
        if 'G83 Z-' in line and 'Q1 F' in line and 'Drilling' in line:
            # 提取钻孔深度
            depth_match = re.search(r'Z-([0-9.]+)', line)
            if depth_match:
                drilling_depth = float(depth_match.group(1))
        elif 'G84 Z-' in line and 'F' in line and 'Tapping' in line:
            # 提取攻丝深度
            depth_match = re.search(r'Z-([0-9.]+)', line)
            if depth_match:
                tapping_depth = float(depth_match.group(1))
    
    print(f"\n验证结果:")
    print(f"  - 钻孔深度: {drilling_depth} mm")
    print(f"  - 攻丝深度: {tapping_depth} mm")
    print(f"  - 钻孔深度 > 攻丝深度: {drilling_depth and tapping_depth and drilling_depth > tapping_depth}")
    print(f"  - 包含英文注释: {'Select' in nc_program or 'Spindle' in nc_program or 'Drilling' in nc_program}")
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
    
    # 检查是否提供了默认位置提示
    has_position_instruction = any('请根据实际图纸修改' in line or '修改为实际位置' in line for line in lines)
    print(f"  - 包含位置修改提示: {has_position_instruction}")
    
    all_checks = [drilling_depth and tapping_depth and drilling_depth > tapping_depth, 
                  'Select' in nc_program or 'Spindle' in nc_program or 'Drilling' in nc_program, 
                  has_point_drilling, has_drilling, has_tapping, has_tapping_cycle, has_spindle_reverse]
    print(f"\n总体结果: {'✅ 全部通过' if all(all_checks) and drilling_depth and tapping_depth and drilling_depth > tapping_depth else '⚠️ 部分检查未通过'}")
    
    # 保存生成的NC程序
    with open("test_depth_fix_output.nc", "w", encoding="utf-8") as f:
        f.write(nc_program)
    print(f"\nNC程序已保存到: test_depth_fix_output.nc")
    
    return drilling_depth and tapping_depth and drilling_depth > tapping_depth

def test_no_depth_specified():
    """测试未指定深度时的默认行为"""
    print("\n"+"="*60)
    print("测试未指定深度时的默认行为...")
    
    # 测试未指定深度的描述
    user_description = "加工M10螺纹贯穿孔1个，合理选择加工原点。NC程序使用英文注释。"
    description_analysis = analyze_user_description(user_description)
    print(f"用户描述: {user_description}")
    print(f"分析的深度: {description_analysis['depth']}")  # 应该是None
    
    features = []  # 模拟没有从图纸识别到特征
    nc_program = generate_fanuc_nc(features, description_analysis, scale=1.0)
    
    # 提取深度值
    lines = nc_program.split('\n')
    drilling_depth = None
    tapping_depth = None
    
    for line in lines:
        if 'G83 Z-' in line and 'Q1 F' in line and 'Drilling' in line:
            depth_match = re.search(r'Z-([0-9.]+)', line)
            if depth_match:
                drilling_depth = float(depth_match.group(1))
        elif 'G84 Z-' in line and 'F' in line and 'Tapping' in line:
            depth_match = re.search(r'Z-([0-9.]+)', line)
            if depth_match:
                tapping_depth = float(depth_match.group(1))
    
    print(f"  - 钻孔深度: {drilling_depth} mm")
    print(f"  - 攻丝深度: {tapping_depth} mm")
    print(f"  - 钻孔深度 > 攻丝深度: {drilling_depth and tapping_depth and drilling_depth > tapping_depth}")
    
    return drilling_depth and tapping_depth and drilling_depth > tapping_depth

def main():
    """运行所有测试"""
    print("CNC Agent 深度设置修复验证测试")
    print("="*60)
    
    test1_result = test_depth_settings()
    test2_result = test_no_depth_specified()
    
    print("\n"+"="*60)
    print("测试总结:")
    print(f"  - 指定深度测试: {'✅ 通过' if test1_result else '❌ 未通过'}")
    print(f"  - 默认深度测试: {'✅ 通过' if test2_result else '❌ 未通过'}")
    
    if test1_result and test2_result:
        print("\n🎉 所有测试通过！CNC Agent现在正确设置钻孔深度大于攻丝深度。")
        print("\n改进包括：")
        print("  - 钻孔深度设置为攻丝深度的1.1倍，确保加工安全")
        print("  - 避免丝锥因底孔太浅而折断")
        print("  - 保持完整的三步螺纹加工工艺")
        print("  - 继续支持英文注释和位置提示功能")
    else:
        print("\n⚠️  部分测试未通过，请检查代码实现。")
    
    return test1_result and test2_result

if __name__ == "__main__":
    main()