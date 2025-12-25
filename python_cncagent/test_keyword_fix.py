#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
测试关键词匹配冲突修复
验证修复后的关键词匹配逻辑是否正确
"""

def test_keyword_matching():
    """测试关键词匹配逻辑"""
    from src.modules.material_tool_matcher import _identify_processing_type
    
    test_cases = [
        # 测试用例：(描述, 期望结果)
        ("加工3个φ22深20底孔φ14.5贯通的沉孔特征", 'counterbore'),
        ("请锪孔φ22深20，底孔φ14.5贯通", 'counterbore'),
        ("φ22沉孔，深度20mm，底孔φ14.5", 'counterbore'),
        ("攻丝M10螺纹孔，深度15mm", 'tapping'),
        ("加工φ10钻孔，深度25mm", 'drilling'),
        ("铣削矩形平面，尺寸100x50", 'milling'),
        ("车削外圆，直径50mm", 'turning'),
        ("加工φ22孔，锪平沉孔面", 'counterbore'),  # 包含"孔"但应识别为沉孔
        ("铣削φ50圆形轮廓", 'milling'),  # 包含φ但应识别为铣削
    ]
    
    print("测试关键词匹配修复...")
    all_passed = True
    
    for description, expected in test_cases:
        result = _identify_processing_type(description)
        status = "PASS" if result == expected else "FAIL"
        print(f"[{status}] '{description}' -> 期望: {expected}, 实际: {result}")
        if result != expected:
            all_passed = False
    
    print(f"\n测试结果: {'全部通过' if all_passed else '存在失败'}")
    return all_passed


def test_counterbore_extraction():
    """测试沉孔直径提取"""
    from src.modules.material_tool_matcher import _extract_counterbore_diameters
    
    test_cases = [
        # 测试用例：(描述, 期望外径, 期望内径)
        ("加工3个φ22深20底孔φ14.5贯通的沉孔特征", 22.0, 14.5),
        ("请锪孔φ30深25，底孔φ20贯通", 30.0, 20.0),
        ("φ25沉孔，深度18mm，底孔φ16", 25.0, 16.0),
        ("φ18锪孔 φ12底孔", 18.0, 12.0),
        ("加工φ20沉孔深15 底孔φ10贯通", 20.0, 10.0),
        ("普通钻孔φ15mm", None, None),  # 非沉孔应返回None
    ]
    
    print("\n测试沉孔直径提取修复...")
    all_passed = True
    
    for description, expected_outer, expected_inner in test_cases:
        outer, inner = _extract_counterbore_diameters(description)
        outer_match = outer == expected_outer
        inner_match = inner == expected_inner
        status = "PASS" if outer_match and inner_match else "FAIL"
        
        print(f"[{status}] '{description}' -> 期望: ({expected_outer}, {expected_inner}), 实际: ({outer}, {inner})")
        if not (outer_match and inner_match):
            all_passed = False
    
    print(f"\n测试结果: {'全部通过' if all_passed else '存在失败'}")
    return all_passed


if __name__ == "__main__":
    print("开始测试关键词匹配冲突修复...")
    
    type_test_passed = test_keyword_matching()
    diameter_test_passed = test_counterbore_extraction()
    
    print(f"\n总体测试结果:")
    print(f"加工类型识别: {'通过' if type_test_passed else '失败'}")
    print(f"沉孔直径提取: {'通过' if diameter_test_passed else '失败'}")
    print(f"总体: {'修复成功' if type_test_passed and diameter_test_passed else '修复失败'}")