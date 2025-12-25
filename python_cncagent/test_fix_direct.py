#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
测试修复后的CNC程序生成器 - 专门测试极坐标功能
验证修复了以下问题：
1. 点孔坐标位置错误 - 程序中使用了极坐标模式(G16)但初始点孔操作没有正确设置极坐标参考点
2. 缺少调试输出 - 没有极坐标转换的验证输出
3. G15和G16不成对 - G15取消极坐标模式在程序中间出现，但G16重新进入
4. G43前缺少坐标系声明 - G43刀具长度补偿前应先声明坐标系如G54
"""

import sys
import os

# 添加项目路径
sys.path.append(os.path.join(os.path.dirname(__file__)))

from src.modules.gcode_generation import generate_fanuc_nc
from src.modules.material_tool_matcher import analyze_user_description

def test_polar_coordinate_generation():
    """测试极坐标功能生成"""
    # 用户描述 - 特别强调使用极坐标
    user_prompt = "加工3个φ22深20底孔φ14.5贯通的沉孔特征使用极坐标位置X94.0 Y-30., X94.0 Y90. ,X94.0 Y210.，使用点孔、钻孔、沉孔工艺。坐标原点（0,0）选择正视图φ234的圆的圆心最高点。使用极坐标模式。"
    
    print("正在测试极坐标功能生成...")
    print(f"用户描述: {user_prompt}")
    print("\n" + "="*80)
    
    try:
        # 分析用户描述
        description_analysis = analyze_user_description(user_prompt)
        print(f"分析结果: {description_analysis}")
        
        # 创建虚拟特征用于测试
        features = [
            {
                "shape": "counterbore",
                "center": (94.0, -30.0),
                "outer_diameter": 22.0,
                "inner_diameter": 14.5,
                "depth": 20.0,
                "confidence": 0.9
            },
            {
                "shape": "counterbore",
                "center": (94.0, 90.0),
                "outer_diameter": 22.0,
                "inner_diameter": 14.5,
                "depth": 20.0,
                "confidence": 0.9
            },
            {
                "shape": "counterbore",
                "center": (94.0, 210.0),
                "outer_diameter": 22.0,
                "inner_diameter": 14.5,
                "depth": 20.0,
                "confidence": 0.9
            }
        ]
        
        # 生成CNC程序
        nc_code = generate_fanuc_nc(features, description_analysis)
        
        print("生成的NC程序:")
        print(nc_code)
        
        # 验证生成的程序是否包含关键元素
        lines = nc_code.split('\n')
        
        # 检查G54是否在G43前
        g54_before_g43_count = 0
        g43_count = 0
        for i, line in enumerate(lines):
            if 'G43' in line and 'H' in line:
                g43_count += 1
                # 检查G43前的5行内是否有G54
                start_idx = max(0, i-5)
                for j in range(start_idx, i):
                    if 'G54' in lines[j]:
                        g54_before_g43_count += 1
                        break
        
        print(f"\nG54在G43前出现次数: {g54_before_g43_count}/{g43_count}")
        
        if g54_before_g43_count == g43_count:
            print("✓ 所有G43前都有G54坐标系声明")
        else:
            print("✗ 部分G43前缺少G54坐标系声明")
        
        # 检查G16和G15是否成对出现
        g16_count = sum(1 for line in lines if 'G16' in line)
        g15_count = sum(1 for line in lines if 'G15' in line)
        
        print(f"✓ G16指令出现次数: {g16_count}")
        print(f"✓ G15指令出现次数: {g15_count}")
        
        if g16_count == g15_count:
            print("✓ G16和G15指令数量相等，成对出现")
        else:
            print("✗ G16和G15指令数量不等，不成对出现")
        
        # 检查是否包含调试输出
        debug_found = any('DEBUG:' in line for line in lines)
        if debug_found:
            print("✓ 包含调试输出信息")
        else:
            print("✗ 缺少调试输出信息")
        
        # 检查是否包含极坐标转换信息
        conversion_debug = any('CARTESIAN TO POLAR' in line for line in lines)
        if conversion_debug:
            print("✓ 包含坐标转换调试信息")
        else:
            print("✗ 缺少坐标转换调试信息")
        
        # 检查是否使用极坐标模式
        polar_used = any('G16' in line for line in lines)
        if polar_used:
            print("✓ 使用了极坐标模式(G16)")
        else:
            print("✗ 未使用极坐标模式")
        
        print("\n" + "="*80)
        print("测试完成")
        
        return nc_code
        
    except Exception as e:
        print(f"生成程序时出错: {str(e)}")
        import traceback
        traceback.print_exc()
        return None

def test_direct_polar_function():
    """直接测试极坐标生成函数"""
    print("\n直接测试极坐标生成函数...")
    from src.modules.gcode_generation import _generate_counterbore_code
    import math
    
    # 模拟输入数据
    features = []
    description_analysis = {
        "description": "加工3个φ22深20底孔φ14.5贯通的沉孔特征使用极坐标位置X94.0 Y-30., X94.0 Y90. ,X94.0 Y210.，使用点孔、钻孔、沉孔工艺。坐标原点（0,0）选择正视图φ234的圆的圆心最高点。使用极坐标位置。",
        "processing_type": "counterbore",
        "outer_diameter": 22.0,
        "inner_diameter": 14.5,
        "depth": 20.0,
        "hole_positions": [(94.0, -30.0), (94.0, 90.0), (94.0, 210.0)]
    }
    
    try:
        gcode_lines = _generate_counterbore_code(features, description_analysis)
        print("直接生成的G代码:")
        for line in gcode_lines:
            print(line)
        
        # 检查关键要素
        gcode_text = "\n".join(gcode_lines)
        lines = gcode_lines
        
        # 检查G16和G15是否成对出现
        g16_count = sum(1 for line in lines if 'G16' in line)
        g15_count = sum(1 for line in lines if 'G15' in line)
        
        print(f"\n直接函数测试 - G16指令出现次数: {g16_count}")
        print(f"直接函数测试 - G15指令出现次数: {g15_count}")
        
        # 检查是否包含调试输出
        debug_found = any('DEBUG:' in line for line in lines)
        if debug_found:
            print("✓ 直接函数包含调试输出信息")
        else:
            print("✗ 直接函数缺少调试输出信息")
        
        return gcode_text
        
    except Exception as e:
        print(f"直接测试时出错: {str(e)}")
        import traceback
        traceback.print_exc()
        return None


if __name__ == "__main__":
    # 先运行直接函数测试，使用正确的字符
    test_direct_polar_function()
    
    # 然后运行完整测试
    test_polar_coordinate_generation()
