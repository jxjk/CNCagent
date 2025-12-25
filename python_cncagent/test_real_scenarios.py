#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
最终验证测试 - 模拟实际使用场景
"""

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

def test_real_scenarios():
    """测试实际使用场景"""
    from src.modules.material_tool_matcher import analyze_user_description
    from src.modules.gcode_generation import generate_fanuc_nc
    
    print("=== 实际场景测试 ===")
    
    # 场景1: 典型的沉孔加工
    print("\n场景1: 沉孔加工")
    desc1 = "加工3个φ22深20mm底孔φ14.5贯通的沉孔特征，坐标原点选择正视图φ234的圆的圆心最高点"
    analysis1 = analyze_user_description(desc1)
    print(f"  描述: {desc1}")
    print(f"  识别类型: {analysis1['processing_type']}")
    print(f"  提取外径: {analysis1.get('outer_diameter')}")
    print(f"  提取内径: {analysis1.get('inner_diameter')}")
    print(f"  提取深度: {analysis1.get('depth')}")
    
    features1 = [
        {"shape": "counterbore", "center": (10, 10), "outer_diameter": 22, "inner_diameter": 14.5, "depth": 20},
        {"shape": "counterbore", "center": (50, 10), "outer_diameter": 22, "inner_diameter": 14.5, "depth": 20},
        {"shape": "counterbore", "center": (90, 10), "outer_diameter": 22, "inner_diameter": 14.5, "depth": 20}
    ]
    
    try:
        nc_code1 = generate_fanuc_nc(features1, analysis1)
        has_counterbore = "COUNTERBORE" in nc_code1
        has_3_steps = all(step in nc_code1 for step in ["STEP 1", "STEP 2", "STEP 3"])
        print(f"  G代码生成: {'✓' if has_counterbore and has_3_steps else '✗'}")
        print(f"  包含沉孔工艺: {'✓' if has_counterbore else '✗'}")
        print(f"  包含三步骤: {'✓' if has_3_steps else '✗'}")
    except Exception as e:
        print(f"  G代码生成错误: {e}")
    
    # 场景2: 攻丝加工
    print("\n场景2: 攻丝加工")
    desc2 = "请攻丝4个M10螺纹孔，深度18mm，材料为铝合金"
    analysis2 = analyze_user_description(desc2)
    print(f"  描述: {desc2}")
    print(f"  识别类型: {analysis2['processing_type']}")
    print(f"  提取深度: {analysis2.get('depth')}")
    print(f"  提取材料: {analysis2.get('material')}")
    
    features2 = [
        {"shape": "circle", "center": (15, 15), "radius": 5},
        {"shape": "circle", "center": (45, 15), "radius": 5},
        {"shape": "circle", "center": (15, 45), "radius": 5},
        {"shape": "circle", "center": (45, 45), "radius": 5}
    ]
    
    try:
        nc_code2 = generate_fanuc_nc(features2, analysis2)
        has_tapping = "TAPPING" in nc_code2
        has_3_steps = all(step in nc_code2 for step in ["STEP 1", "STEP 2", "STEP 3"])
        print(f"  G代码生成: {'✓' if has_tapping and has_3_steps else '✗'}")
        print(f"  包含攻丝工艺: {'✓' if has_tapping else '✗'}")
        print(f"  包含三步骤: {'✓' if has_3_steps else '✗'}")
    except Exception as e:
        print(f"  G代码生成错误: {e}")
    
    # 场景3: 避免冲突 - 铣削不应被误判为沉孔
    print("\n场景3: 避免加工类型误判")
    desc3 = "铣削矩形轮廓，尺寸100x50mm，深度5mm"
    analysis3 = analyze_user_description(desc3)
    print(f"  描述: {desc3}")
    print(f"  识别类型: {analysis3['processing_type']}")
    
    features3 = [{"shape": "rectangle", "center": (50, 25), "dimensions": (100, 50)}]
    
    try:
        nc_code3 = generate_fanuc_nc(features3, analysis3)
        has_milling = "MILLING" in nc_code3
        has_no_counterbore = "COUNTERBORE" not in nc_code3
        print(f"  G代码生成: {'✓' if has_milling and has_no_counterbore else '✗'}")
        print(f"  包含铣削工艺: {'✓' if has_milling else '✗'}")
        print(f"  无沉孔工艺: {'✓' if has_no_counterbore else '✗'}")
    except Exception as e:
        print(f"  G代码生成错误: {e}")
    
    # 场景4: 复合特征 - 包含"孔"但实际是沉孔
    print("\n场景4: 复合特征识别")
    desc4 = "加工φ22孔，锪平沉孔面，深度15mm"
    analysis4 = analyze_user_description(desc4)
    print(f"  描述: {desc4}")
    print(f"  识别类型: {analysis4['processing_type']}")
    
    features4 = [{"shape": "counterbore", "center": (30, 30), "outer_diameter": 22, "inner_diameter": 18, "depth": 15}]
    
    try:
        nc_code4 = generate_fanuc_nc(features4, analysis4)
        has_counterbore = "COUNTERBORE" in nc_code4
        has_3_steps = "STEP 1" in nc_code4  # 验证是否使用了正确的多步骤工艺
        print(f"  G代码生成: {'✓' if has_counterbore and has_3_steps else '✗'}")
        print(f"  包含沉孔工艺: {'✓' if has_counterbore else '✗'}")
        print(f"  包含多步骤: {'✓' if has_3_steps else '✗'}")
    except Exception as e:
        print(f"  G代码生成错误: {e}")
    
    print("\n=== 测试完成 ===")

if __name__ == "__main__":
    test_real_scenarios()
