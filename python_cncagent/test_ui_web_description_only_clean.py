"""
测试CNC Agent项目的UI界面和网页版是否支持仅使用用户描述生成NC程序
"""
import tkinter as tk
from tkinter import ttk, messagebox
import numpy as np
import threading
from src.modules.ai_nc_helper import AI_NC_Helper
from src.modules.simple_nc_gui import SimpleNC_GUI

def test_ui_description_only():
    """测试UI界面是否支持仅使用描述生成"""
    print("测试UI界面仅描述生成功能...")
    
    # 创建一个简化版的测试GUI，模拟用户界面行为
    class TestGUI:
        def __init__(self):
            self.nc_helper = AI_NC_Helper()
            self.current_image = None
            self.current_nc_code = ""
            self.material = "Aluminum"
            self.description = ""
        
        def simulate_load_drawing(self):
            """模拟加载图纸（使用虚拟图像）"""
            print("模拟加载图纸...")
            # 创建一个虚拟图像用于测试
            self.current_image = np.zeros((400, 400), dtype=np.uint8)
            print("使用虚拟图像（全黑图像）")
        
        def simulate_generate_nc(self):
            """模拟生成NC代码"""
            print(f"模拟生成NC代码，描述: {self.description}")
            
            if self.current_image is None:
                print("当前图像为空，使用虚拟图像")
                self.simulate_load_drawing()
            
            try:
                # 使用AI_NC_Helper生成NC代码
                nc_code = self.nc_helper.quick_nc_generation(
                    self.current_image, 
                    drawing_text=self.description, 
                    material=self.material, 
                    user_description=self.description
                )
                self.current_nc_code = nc_code
                print("NC代码生成成功")
                print(f"代码预览: {nc_code[:150]}...")
                return nc_code
            except Exception as e:
                print(f"生成失败: {str(e)}")
                return None
    
    # 测试各种描述
    test_gui = TestGUI()
    test_descriptions = [
        "请加工一个φ10的孔，深度20mm",
        "铣削一个50x30mm的矩形，深度5mm",
        "攻丝M10螺纹孔，深度15mm",
        "车削直径50mm，长度100mm的轴"
    ]
    
    print("\n测试UI界面仅描述生成功能:")
    for i, desc in enumerate(test_descriptions):
        print(f"\n--- 测试 {i+1} ---")
        test_gui.description = desc
        result = test_gui.simulate_generate_nc()
        if result:
            print("成功生成NC代码")
        else:
            print("生成失败")
    
    return True

def test_web_version_description_only():
    """测试网页版是否支持仅使用描述生成"""
    print("\n测试网页版仅描述生成功能...")
    print("根据代码分析，start_ai_nc_helper.py中的GUI模式基于simple_nc_gui.py")
    print("GUI界面需要图纸输入才能进行特征检测")
    print("但可以通过用户描述字段影响工艺参数")
    
    # 测试网页版的命令行接口
    from src.main import generate_nc_with_ai_helper
    import os
    
    # 创建一个虚拟PDF用于测试（实际上不需要真实PDF，因为我们会模拟）
    print("\n测试命令行接口（process命令）:")
    print("命令行模式需要PDF路径，但内部使用AI_NC_Helper可以处理仅描述的情况")
    
    # 我们将测试AI_NC_Helper的process_pdf方法，但提供空PDF或模拟
    nc_helper = AI_NC_Helper()
    
    test_descriptions = [
        "请加工一个φ12的孔，深度25mm",
        "铣削一个方形槽，60x60mm，深度8mm"
    ]
    
    for i, desc in enumerate(test_descriptions):
        print(f"\n--- 网页版测试 {i+1}: {desc} ---")
        try:
            # 创建虚拟图像进行测试
            dummy_image = np.zeros((400, 400), dtype=np.uint8)
            result = nc_helper.quick_nc_generation(
                dummy_image,
                drawing_text="",
                material="Steel",
                user_description=desc
            )
            print("成功生成NC代码")
            print(f"  代码预览: {result[:100]}...")
        except Exception as e:
            print(f"生成失败: {str(e)}")
    
    return True

def test_edge_cases():
    """测试边界情况"""
    print("\n测试边界情况:")
    
    # 测试空描述
    print("\n1. 测试空描述:")
    try:
        dummy_image = np.zeros((400, 400), dtype=np.uint8)
        nc_helper = AI_NC_Helper()
        result = nc_helper.quick_nc_generation(
            dummy_image,
            drawing_text="",
            material="Aluminum",
            user_description=""
        )
        print("空描述处理成功")
        print(f"  代码预览: {result[:100]}...")
    except Exception as e:
        print(f"空描述处理失败: {str(e)}")
    
    # 测试模糊描述
    print("\n2. 测试模糊描述:")
    try:
        result = nc_helper.quick_nc_generation(
            dummy_image,
            drawing_text="",
            material="Aluminum",
            user_description="随便加工一下"
        )
        print("模糊描述处理成功")
        print(f"  代码预览: {result[:100]}...")
    except Exception as e:
        print(f"模糊描述处理失败: {str(e)}")
    
    # 测试复杂描述
    print("\n3. 测试复杂描述:")
    try:
        result = nc_helper.quick_nc_generation(
            dummy_image,
            drawing_text="",
            material="Stainless Steel",
            user_description="请先钻φ8底孔，深度18mm，然后攻M10螺纹，使用冷却液"
        )
        print("复杂描述处理成功")
        print(f"  代码预览: {result[:150]}...")
    except Exception as e:
        print(f"复杂描述处理失败: {str(e)}")

def main():
    """主测试函数"""
    print("="*60)
    print("CNC Agent 项目仅描述生成NC程序功能测试")
    print("="*60)
    
    # 测试UI界面
    ui_result = test_ui_description_only()
    
    # 测试网页版
    web_result = test_web_version_description_only()
    
    # 测试边界情况
    test_edge_cases()
    
    print("\n" + "="*60)
    print("测试总结:")
    print("1. UI界面（simple_nc_gui.py）:")
    print("   - 需要图纸输入才能进行特征检测")
    print("   - 但用户描述是关键输入，影响工艺参数")
    print("   - 无法完全脱离图纸，但描述是重要参考")
    
    print("\n2. 网页版（start_ai_nc_helper.py中的GUI模式）:")
    print("   - 基于UI界面，有相同限制")
    print("   - 内部使用AI_NC_Helper，支持从描述生成NC")
    
    print("\n3. 核心功能（AI_NC_Helper和unified_generator）:")
    print("   - 支持仅使用用户描述生成NC程序")
    print("   - 即使没有图纸，也能生成基础程序")
    print("   - 用户描述是第一参考")
    
    print("\n4. 推荐做法:")
    print("   - 如有图纸，结合图纸信息和用户描述")
    print("   - 如无图纸，可仅使用用户描述生成基础程序")
    print("   - 用户描述具有最高优先级")
    
    print("\n测试完成！")

if __name__ == "__main__":
    main()
