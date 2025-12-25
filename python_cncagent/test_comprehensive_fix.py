#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
综合测试字符编码修复的脚本
测试各种边界情况和编码场景
"""
import sys
import os
import tempfile
import json

# 添加src到路径
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

def test_comprehensive_encoding():
    """综合测试各种编码场景"""
    print("开始综合编码修复测试...")
    
    # 1. 测试各种中文字符串
    test_strings = [
        "加工3个φ22沉孔，深度20mm",
        "请铣削一个100x50的矩形",
        "攻丝M10螺纹孔，深度15mm",
        "车削外径φ50，长度100mm",
        "钻φ10通孔，深度贯穿",
        "沉孔φ22深20底孔φ14.5贯通",
        "X10.0Y20.0位置加工",
        "使用极坐标R50 θ30°",
        "精度要求Ra1.6",
        "材料：铝合金"
    ]
    
    print("\n1. 测试material_tool_matcher模块...")
    from src.modules.material_tool_matcher import analyze_user_description
    
    for i, test_str in enumerate(test_strings):
        print(f"  测试 {i+1}: {test_str[:20]}...")
        
        # 测试原始字符串
        try:
            result1 = analyze_user_description(test_str)
            print(f"    原始字符串处理成功: {result1['processing_type']}")
        except Exception as e:
            print(f"    原始字符串处理失败: {e}")
        
        # 测试UTF-8编码的字节串
        try:
            utf8_bytes = test_str.encode('utf-8')
            result2 = analyze_user_description(utf8_bytes)
            print(f"    UTF-8字节串处理成功: {result2['processing_type']}")
        except Exception as e:
            print(f"    UTF-8字节串处理失败: {e}")
        
        # 测试包含特殊字符的字符串
        try:
            special_str = test_str + " 特殊符号: αβγδε"
            result3 = analyze_user_description(special_str)
            print(f"    特殊字符处理成功: {result3['processing_type']}")
        except Exception as e:
            print(f"    特殊字符处理失败: {e}")
    
    print("\n2. 测试gcode_generation模块...")
    from src.modules.gcode_generation import generate_fanuc_nc
    from src.modules.material_tool_matcher import analyze_user_description
    
    features = [{"shape": "circle", "center": (50, 50), "radius": 10}]
    
    for i, test_str in enumerate(test_strings[:3]):  # 只测试前3个以节省时间
        print(f"  测试 {i+1}: {test_str[:20]}...")
        
        # 测试原始字符串
        try:
            desc_analysis1 = analyze_user_description(test_str)
            nc_code1 = generate_fanuc_nc(features, desc_analysis1)
            print(f"    原始字符串NC生成成功，长度: {len(nc_code1)}")
        except Exception as e:
            print(f"    原始字符串NC生成失败: {e}")
        
        # 测试UTF-8编码的字节串
        try:
            utf8_bytes = test_str.encode('utf-8')
            desc_analysis2 = analyze_user_description(utf8_bytes)
            nc_code2 = generate_fanuc_nc(features, desc_analysis2)
            print(f"    UTF-8字节串NC生成成功，长度: {len(nc_code2)}")
        except Exception as e:
            print(f"    UTF-8字节串NC生成失败: {e}")
    
    print("\n3. 测试unified_generator模块...")
    from src.modules.unified_generator import UnifiedCNCGenerator
    
    generator = UnifiedCNCGenerator()
    
    for i, test_str in enumerate(test_strings[:3]):
        print(f"  测试 {i+1}: {test_str[:20]}...")
        
        # 测试原始字符串
        try:
            nc_code1 = generator.generate_from_description_only(test_str, "Aluminum")
            print(f"    原始字符串统一生成成功，长度: {len(nc_code1)}")
        except Exception as e:
            print(f"    原始字符串统一生成失败: {e}")
        
        # 测试UTF-8编码的字节串
        try:
            utf8_bytes = test_str.encode('utf-8')
            nc_code2 = generator.generate_from_description_only(utf8_bytes, "Aluminum")
            print(f"    UTF-8字节串统一生成成功，长度: {len(nc_code2)}")
        except Exception as e:
            print(f"    UTF-8字节串统一生成失败: {e}")
    
    print("\n4. 测试ai_driven_generator模块...")
    from src.modules.ai_driven_generator import generate_nc_with_ai
    
    for i, test_str in enumerate(test_strings[:3]):
        print(f"  测试 {i+1}: {test_str[:20]}...")
        
        # 测试原始字符串
        try:
            nc_code1 = generate_nc_with_ai(test_str)
            print(f"    原始字符串AI生成成功，长度: {len(nc_code1)}")
        except Exception as e:
            print(f"    原始字符串AI生成失败: {e}")
        
        # 测试UTF-8编码的字节串
        try:
            utf8_bytes = test_str.encode('utf-8')
            nc_code2 = generate_nc_with_ai(utf8_bytes)
            print(f"    UTF-8字节串AI生成成功，长度: {len(nc_code2)}")
        except Exception as e:
            print(f"    UTF-8字节串AI生成失败: {e}")
    
    print("\n5. 测试边界情况...")
    
    # 测试空字符串
    try:
        result = analyze_user_description("")
        print("    空字符串处理成功")
    except Exception as e:
        print(f"    空字符串处理失败: {e}")
    
    # 测试包含错误编码的字节串（模拟损坏数据）
    try:
        bad_bytes = b'\xff\xfe\xfd'  # 无效的UTF-8序列
        result = analyze_user_description(bad_bytes)
        print("    错误编码字节串处理成功（已替换）")
    except Exception as e:
        print(f"    错误编码字节串处理失败: {e}")
    
    # 测试非常长的字符串
    try:
        long_str = "加工" * 1000 + "孔" * 1000
        result = analyze_user_description(long_str)
        print(f"    长字符串处理成功: {result['processing_type']}")
    except Exception as e:
        print(f"    长字符串处理失败: {e}")
    
    print("\n6. 测试文件导出功能...")
    try:
        # 创建临时文件测试导出功能
        with tempfile.NamedTemporaryFile(mode='w', suffix='.nc', delete=False, encoding='utf-8') as temp_file:
            temp_path = temp_file.name
            temp_file.write("O0001 (测试程序)\n(包含中文注释: 机械加工)\nG21 G90\nM30")
        
        # 测试包含中文的文件内容处理
        with open(temp_path, 'r', encoding='utf-8') as f:
            content = f.read()
            print(f"    文件读取成功，内容长度: {len(content)}")
        
        os.unlink(temp_path)
        print("    文件操作测试成功")
    except Exception as e:
        print(f"    文件操作测试失败: {e}")
    
    print("\n综合编码修复测试完成!")

def test_error_handling():
    """测试错误处理机制"""
    print("\n测试错误处理机制...")
    
    from src.modules.material_tool_matcher import analyze_user_description
    
    # 测试各种异常情况
    test_cases = [
        (None, "None值"),
        (123, "整数值"),
        ([], "列表值"),
        ({}, "字典值"),
        (b"invalid utf8: \xff\xfe", "无效UTF-8字节"),
    ]
    
    for test_input, description in test_cases:
        try:
            result = analyze_user_description(test_input)
            print(f"  {description}: 处理成功 -> {type(result.get('description', ''))}")
        except Exception as e:
            print(f"  {description}: 异常处理成功 -> {type(e).__name__}")
    
    print("错误处理测试完成!")

if __name__ == "__main__":
    test_comprehensive_encoding()
    test_error_handling()
    print("\n所有测试完成!")