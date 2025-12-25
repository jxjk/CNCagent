#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
测试关键词匹配冲突修复 - 简化版本
"""

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

def main():
    # 测试加工类型识别
    from src.modules.material_tool_matcher import _identify_processing_type
    
    test_cases = [
        ("加工3个φ22深20底孔φ14.5贯通的沉孔特征", "counterbore"),
        ("铣削沉孔面，φ22沉孔深度20", "counterbore"),
        ("钻φ22沉孔，深度20，底孔φ14.5", "counterbore"),
        ("钻φ10攻丝M10", "tapping"),
        ("铣削平面100x50", "milling"),
        ("加工φ10钻孔，深度25mm", "drilling"),
    ]
    
    print("Testing keyword matching fix...")
    all_passed = True
    
    for desc, expected in test_cases:
        result = _identify_processing_type(desc)
        status = "PASS" if result == expected else "FAIL"
        print(f"[{status}] '{desc}' -> expected: {expected}, actual: {result}")
        if result != expected:
            all_passed = False
    
    # 测试直径提取
    from src.modules.material_tool_matcher import _extract_counterbore_diameters
    
    diameter_tests = [
        ("加工3个φ22深20底孔φ14.5贯通的沉孔特征", (22.0, 14.5)),
        ("请锪孔φ30深25，底孔φ20贯通", (30.0, 20.0)),
        ("φ25沉孔，深度18mm，底孔φ16", (25.0, 16.0)),
        ("普通钻孔φ15mm", (None, None)),
    ]
    
    for desc, expected in diameter_tests:
        actual = _extract_counterbore_diameters(desc)
        status = "PASS" if actual == expected else "FAIL"
        print(f"[{status}] '{desc}' -> expected: {expected}, actual: {actual}")
        if actual != expected:
            all_passed = False
    
    # 测试完整的分析流程
    from src.modules.material_tool_matcher import analyze_user_description
    
    analysis_tests = [
        "加工3个φ22深20底孔φ14.5贯通的沉孔特征",
        "攻丝M10螺纹孔，深度15mm",
        "铣削矩形平面，尺寸100x50",
    ]
    
    for desc in analysis_tests:
        try:
            result = analyze_user_description(desc)
            print(f"[PASS] Analyzed: {desc} -> type: {result.get('processing_type', 'N/A')}")
        except Exception as e:
            print(f"[FAIL] Error analyzing: {desc} -> {e}")
            all_passed = False
    
    print(f"\nOverall result: {'SUCCESS - All tests passed!' if all_passed else 'FAILURE - Some tests failed!'}")
    return all_passed

if __name__ == "__main__":
    main()
