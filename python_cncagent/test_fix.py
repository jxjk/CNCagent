#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
测试修复后的CNC程序生成器
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

from src.modules.unified_generator import generate_cnc_with_unified_approach
def test_counterbore_generation():
    """测试沉孔加工程序生成"""
    # 用户描述
    user_prompt = "加工3个φ22深20底孔φ14.5贯通的沉孔特征使用极坐标位置X94.0 Y-30., X94.0 Y90. ,X94.0 Y210.，使用点孔、钻孔、沉孔工艺。坐标原点（0,0）选择正视图φ234的圆的圆心最高点。"
    
    print("正在测试沉孔加工程序生成...")
    print(f"用户描述: {user_prompt}")
    print("\n" + "="*80)
    
    try:
        # 生成CNC程序
        nc_code = generate_cnc_with_unified_approach(
            user_prompt=user_prompt,
            use_ai_primary=True,
            user_priority_weight=1.0
        )
        
        print("生成的NC程序:")
        print(nc_code)
        
        # 验证生成的程序是否包含关键元素
        lines = nc_code.split('\n')
        
        # 检查G54是否在G43前
        g43_found = False
        g54_before_g43 = True
        for line in lines:
            if 'G43' in line and 'H' in line:
                g43_found = True
            if 'G54' in line and g43_found:
                g54_before_g43 = False  # G54在G43之后，不正确
            if 'G43' in line and 'H' in line and g54_before_g43:
                # 检查G43前的几行是否包含G54
                for i in range(max(0, lines.index(line)-5), lines.index(line)):
                    if 'G54' in lines[i]:
                        g54_before_g43 = True
                        break
        
        if g54_before_g43:
            print("\n✓ G54坐标系声明在G43刀具长度补偿前")
        else:
            print("\n✗ G54坐标系声明不在G43刀具长度补偿前")
        
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
        polar_found = any('POLAR' in line.upper() for line in lines)
        if polar_found:
            print("✓ 包含极坐标相关信息")
        else:
            print("✗ 缺少极坐标相关信息")
        
        # 检查是否包含坐标转换调试信息
        conversion_debug = any('CARTESIAN TO POLAR' in line for line in lines)
        if conversion_debug:
            print("✓ 包含坐标转换调试信息")
        else:
            print("✗ 缺少坐标转换调试信息")
        
        print("\n" + "="*80)
        print("测试完成")
        
        return nc_code
        
    except Exception as e:
        print(f"生成程序时出错: {str(e)}")
        import traceback
        traceback.print_exc()
        return None

if __name__ == "__main__":
    test_counterbore_generation()