"""
测试仅描述模式功能
"""
import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from src.modules.simple_nc_gui import SimpleNC_GUI
import tkinter as tk
from src.modules.unified_generator import unified_generator

def test_description_only_generation():
    """测试仅描述模式的NC代码生成"""
    print("测试1: 仅描述模式 - 沉孔加工")
    description = "请加工3个φ22沉孔，深度20mm"
    material = "Aluminum"
    
    try:
        nc_code = unified_generator.generate_from_description_only(description, material)
        print("生成的NC代码:")
        print(nc_code)
        print("\n" + "="*50 + "\n")
    except Exception as e:
        print(f"生成失败: {e}")
    
    print("测试2: 仅描述模式 - 钻孔加工")
    description = "请在板上钻5个φ10的孔，深度15mm"
    material = "Steel"
    
    try:
        nc_code = unified_generator.generate_from_description_only(description, material)
        print("生成的NC代码:")
        print(nc_code)
        print("\n" + "="*50 + "\n")
    except Exception as e:
        print(f"生成失败: {e}")
    
    print("测试3: 仅描述模式 - 矩形铣削")
    description = "请铣削一个100mm x 50mm的矩形，深度5mm"
    material = "Aluminum"
    
    try:
        nc_code = unified_generator.generate_from_description_only(description, material)
        print("生成的NC代码:")
        print(nc_code)
        print("\n" + "="*50 + "\n")
    except Exception as e:
        print(f"生成失败: {e}")

def test_gui_integration():
    """测试GUI集成"""
    print("测试GUI集成...")
    print("请手动测试以下功能:")
    print("1. 启动GUI界面")
    print("2. 勾选'仅描述模式'")
    print("3. 输入加工描述，例如: '请加工3个φ22沉孔，深度20mm'")
    print("4. 点击'生成NC'按钮")
    print("5. 验证生成的NC代码是否符合描述")
    print("6. 验证虚拟图像是否正确显示")

if __name__ == "__main__":
    print("开始测试仅描述模式功能...")
    test_description_only_generation()
    test_gui_integration()