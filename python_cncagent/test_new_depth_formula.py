"""
测试新的钻孔深度计算公式 - 螺纹深度 + 1/3底孔直径 + 1.5
"""
import os
import sys
import numpy as np
import re  # 添加正则表达式导入
sys.path.append(os.path.join(os.path.dirname(__file__), 'src'))

from src.modules.gcode_generation import generate_fanuc_nc
from src.modules.material_tool_matcher import analyze_user_description

def test_new_depth_formula():
    """测试新的钻孔深度计算公式"""
    print("测试新的钻孔深度计算公式...")
    print("="*60)
    print("公式: 钻孔深度 = 螺纹深度 + 1/3底孔直径 + 1.5")
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
    
    # 验证生成的代码
    lines = nc_program.split('\n')
    
    # 提取钻孔深度和攻丝深度 - 改进的匹配逻辑
    drilling_depth = None
    tapping_depth = None
    
    for line in lines:
        # 匹配钻孔指令 - 更宽泛的匹配
        if 'G83 Z-' in line and 'Drilling' in line:
            depth_match = re.search(r'Z-([0-9.]+)', line)
            if depth_match:
                drilling_depth = float(depth_match.group(1))
                break  # 找到第一个钻孔深度即可
        elif 'G84 Z-' in line and 'Tapping' in line:
            depth_match = re.search(r'Z-([0-9.]+)', line)
            if depth_match:
                tapping_depth = float(depth_match.group(1))
                break  # 找到第一个攻丝深度即可
    
    print(f"\n验证结果:")
    print(f"  - 螺纹深度: {description_analysis['depth']} mm")
    print(f"  - M10底孔直径: 8.5 mm")
    print(f"  - 计算钻孔深度: {description_analysis['depth']} + 8.5/3 + 1.5 = {description_analysis['depth']} + {8.5/3:.3f} + 1.5 = {description_analysis['depth'] + 8.5/3 + 1.5:.3f} mm")
    print(f"  - 实际钻孔深度: {drilling_depth} mm")
    print(f"  - 实际攻丝深度: {tapping_depth} mm")
    print(f"  - 钻孔深度 > 攻丝深度: {drilling_depth and tapping_depth and drilling_depth > tapping_depth}")
    print(f"  - 深度计算正确: {abs(drilling_depth - (description_analysis['depth'] + 8.5/3 + 1.5)) < 0.01 if drilling_depth else False}")
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
                  abs(drilling_depth - (description_analysis['depth'] + 8.5/3 + 1.5)) < 0.01 if drilling_depth else False,
                  'Select' in nc_program or 'Spindle' in nc_program or 'Drilling' in nc_program, 
                  has_point_drilling, has_drilling, has_tapping, has_tapping_cycle, has_spindle_reverse]
    print(f"\n总体结果: {'✅ 全部通过' if all(all_checks) and drilling_depth and tapping_depth and drilling_depth > tapping_depth else '⚠️ 部分检查未通过'}")
    
    # 保存生成的NC程序
    with open("test_new_depth_formula_output.nc", "w", encoding="utf-8") as f:
        f.write(nc_program)
    print(f"\nNC程序已保存到: test_new_depth_formula_output.nc")
    
    return drilling_depth and tapping_depth and drilling_depth > tapping_depth and abs(drilling_depth - (description_analysis['depth'] + 8.5/3 + 1.5)) < 0.01

def test_different_thread_sizes():
    """测试不同螺纹规格的深度计算"""
    print("\n" + "="*60)
    print("测试不同螺纹规格的深度计算...")
    
    test_cases = [
        ("加工M8螺纹贯穿孔1个，深度12mm，合理选择加工原点。", 12.0, 6.8),  # M8螺纹底孔直径6.8mm
        ("加工M6螺纹贯穿孔1个，深度10mm，合理选择加工原点。", 10.0, 5.0),  # M6螺纹底孔直径5.0mm
        ("加工M12螺纹贯穿孔1个，深度16mm，合理选择加工原点。", 16.0, 10.2)  # M12螺纹底孔直径10.2mm
    ]
    
    all_passed = True
    for desc, expected_depth, drill_dia in test_cases:
        print(f"\n测试: {desc}")
        description_analysis = analyze_user_description(desc)
        features = []
        nc_program = generate_fanuc_nc(features, description_analysis, scale=1.0)
        
        # 提取深度值
        lines = nc_program.split('\n')
        drilling_depth = None
        tapping_depth = None
        
        for line in lines:
            if 'G83 Z-' in line and 'Drilling' in line:
                depth_match = re.search(r'Z-([0-9.]+)', line)
                if depth_match:
                    drilling_depth = float(depth_match.group(1))
                    break
            elif 'G84 Z-' in line and 'Tapping' in line:
                depth_match = re.search(r'Z-([0-9.]+)', line)
                if depth_match:
                    tapping_depth = float(depth_match.group(1))
                    break
        
        expected_drilling = expected_depth + (drill_dia / 3) + 1.5
        print(f"  - 螺纹深度: {expected_depth} mm")
        print(f"  - 底孔直径: {drill_dia} mm")
        print(f"  - 期望钻孔深度: {expected_depth} + {drill_dia}/3 + 1.5 = {expected_drilling:.3f} mm")
        print(f"  - 实际钻孔深度: {drilling_depth} mm")
        print(f"  - 计算正确: {abs(drilling_depth - expected_drilling) < 0.01 if drilling_depth else False}")
        print(f"  - 钻孔深度 > 攻丝深度: {drilling_depth and tapping_depth and drilling_depth > tapping_depth}")
        
        if not (drilling_depth and tapping_depth and drilling_depth > tapping_depth and abs(drilling_depth - expected_drilling) < 0.01):
            all_passed = False
    
    return all_passed

def main():
    """运行所有测试"""
    print("CNC Agent 新钻孔深度公式验证测试")
    print("="*60)
    print("公式: 钻孔深度 = 螺纹深度 + 1/3底孔直径 + 1.5")
    print()
    
    test1_result = test_new_depth_formula()
    test2_result = test_different_thread_sizes()
    
    print("\n" + "="*60)
    print("测试总结:")
    print(f"  - M10螺纹测试: {'✅ 通过' if test1_result else '❌ 未通过'}")
    print(f"  - 多螺纹规格测试: {'✅ 通过' if test2_result else '❌ 未通过'}")
    
    if test1_result and test2_result:
        print("\n🎉 所有测试通过！CNC Agent现在使用新公式计算钻孔深度。")
        print("\n改进包括：")
        print("  - 钻孔深度计算公式: 螺纹深度 + 1/3底孔直径 + 1.5")
        print("  - 避免丝锥因底孔太浅而折断")
        print("  - 支持不同螺纹规格（M6, M8, M10, M12等）")
        print("  - 保持完整的三步螺纹加工工艺")
        print("  - 继续支持英文注释和位置提示功能")
    else:
        print("\n⚠️  部分测试未通过，请检查代码实现。")
    
    return test1_result and test2_result

if __name__ == "__main__":
    main()