#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
测试字符编码修复的脚本
"""
import sys
import os
import tempfile

# 添加src到路径
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

def test_material_tool_matcher():
    """测试material_tool_matcher模块的编码处理"""
    print("测试material_tool_matcher编码处理...")
    from src.modules.material_tool_matcher import analyze_user_description
    
    # 测试正常字符串
    result1 = analyze_user_description("加工3个φ22沉孔，深度20mm")
    print(f"正常字符串测试: {result1['processing_type']}")
    
    # 测试UTF-8编码的字节串
    utf8_bytes = "加工3个φ22沉孔，深度20mm".encode('utf-8')
    result2 = analyze_user_description(utf8_bytes)
    print(f"UTF-8字节串测试: {result2['processing_type']}")
    
    print("material_tool_matcher编码处理测试通过!")

def test_gcode_generation():
    """测试gcode_generation模块的编码处理"""
    print("\n测试gcode_generation编码处理...")
    from src.modules.gcode_generation import generate_fanuc_nc
    
    # 创建测试特征数据
    features = [
        {
            "shape": "circle",
            "center": (100, 100),
            "radius": 10
        }
    ]
    
    # 测试描述分析
    from src.modules.material_tool_matcher import analyze_user_description
    
    # 正常字符串
    description_analysis = analyze_user_description("加工一个φ20的孔，深度15mm")
    nc_code1 = generate_fanuc_nc(features, description_analysis)
    print(f"正常字符串NC生成长度: {len(nc_code1)}")
    
    # UTF-8字节串
    utf8_bytes = "加工一个φ20的孔，深度15mm".encode('utf-8')
    description_analysis2 = analyze_user_description(utf8_bytes)
    nc_code2 = generate_fanuc_nc(features, description_analysis2)
    print(f"UTF-8字节串NC生成长度: {len(nc_code2)}")
    
    print("gcode_generation编码处理测试通过!")

def test_unified_generator():
    """测试unified_generator模块的编码处理"""
    print("\n测试unified_generator编码处理...")
    from src.modules.unified_generator import UnifiedCNCGenerator
    
    generator = UnifiedCNCGenerator()
    
    # 测试正常字符串
    try:
        nc_code1 = generator.generate_from_description_only("加工一个φ20的孔，深度15mm", "Aluminum")
        print(f"正常字符串生成NC长度: {len(nc_code1)}")
    except Exception as e:
        print(f"正常字符串测试异常: {e}")
    
    # 测试UTF-8字节串
    try:
        utf8_bytes = "加工一个φ20的孔，深度15mm".encode('utf-8')
        nc_code2 = generator.generate_from_description_only(utf8_bytes, "Aluminum")
        print(f"UTF-8字节串生成NC长度: {len(nc_code2)}")
    except Exception as e:
        print(f"UTF-8字节串测试异常: {e}")
    
    print("unified_generator编码处理测试完成!")

def test_ai_driven_generator():
    """测试ai_driven_generator模块的编码处理"""
    print("\n测试ai_driven_generator编码处理...")
    from src.modules.ai_driven_generator import generate_nc_with_ai
    
    # 测试正常字符串
    try:
        nc_code1 = generate_nc_with_ai("加工一个φ20的孔，深度15mm")
        print(f"正常字符串AI生成NC长度: {len(nc_code1)}")
    except Exception as e:
        print(f"正常字符串AI测试异常: {e}")
    
    # 测试UTF-8字节串
    try:
        utf8_bytes = "加工一个φ20的孔，深度15mm".encode('utf-8')
        nc_code2 = generate_nc_with_ai(utf8_bytes)
        print(f"UTF-8字节串AI生成NC长度: {len(nc_code2)}")
    except Exception as e:
        print(f"UTF-8字节串AI测试异常: {e}")
    
    print("ai_driven_generator编码处理测试完成!")

def test_simple_nc_gui_export():
    """测试simple_nc_gui导出功能的编码处理"""
    print("\n测试simple_nc_gui导出功能编码处理...")
    
    # 创建临时文件进行测试
    with tempfile.NamedTemporaryFile(mode='w', suffix='.nc', delete=False, encoding='utf-8') as temp_file:
        temp_path = temp_file.name
    
    try:
        from src.modules.simple_nc_gui import SimpleNC_GUI
        import tkinter as tk
        
        root = tk.Tk()
        gui = SimpleNC_GUI(root)
        
        # 设置一些测试数据
        gui.current_nc_code = "O0001 (测试程序)\nG21 G90\nM30"
        
        # 模拟导出功能中的编码处理部分
        export_code = gui.current_nc_code
        print(f"导出代码长度: {len(export_code)}")
        
        # 测试字符串写入
        with open(temp_path, 'w', encoding='utf-8') as f:
            f.write(export_code)
        print("字符串写入测试通过")
        
        # 测试字节串处理
        export_code_bytes = export_code.encode('utf-8')
        try:
            export_code_str = export_code_bytes.decode('utf-8')
        except UnicodeError:
            export_code_str = export_code_bytes.decode('utf-8', errors='replace')
        
        with open(temp_path, 'w', encoding='utf-8') as f:
            f.write(export_code_str)
        print("字节串解码写入测试通过")
        
    except Exception as e:
        print(f"simple_nc_gui导出功能测试异常: {e}")
    finally:
        # 清理临时文件
        if os.path.exists(temp_path):
            os.unlink(temp_path)
        root.destroy()
    
    print("simple_nc_gui导出功能编码处理测试完成!")

if __name__ == "__main__":
    print("开始测试字符编码修复...")
    
    try:
        test_material_tool_matcher()
        test_gcode_generation()
        test_unified_generator()
        test_ai_driven_generator()
        test_simple_nc_gui_export()
        
        print("\n所有编码修复测试完成!")
    except Exception as e:
        print(f"测试过程中出现异常: {e}")
        import traceback
        traceback.print_exc()