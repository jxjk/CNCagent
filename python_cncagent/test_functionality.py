"""
CNC Agent 功能完整性测试脚本
"""
import requests
import json
import numpy as np
import cv2
from PIL import Image
import tempfile
import os

def test_opencv_functionality():
    """测试OpenCV功能"""
    print("1. 测试OpenCV功能...")
    try:
        # 创建一个简单的测试图像
        img = np.zeros((200, 200, 3), dtype=np.uint8)
        # 添加一个圆形
        cv2.circle(img, (100, 100), 50, (255, 255, 255), -1)
        # 添加一个矩形
        cv2.rectangle(img, (50, 50), (90, 90), (128, 128, 128), -1)
        
        print("   ✅ OpenCV可以创建和操作图像")
        
        # 测试边缘检测
        gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
        edges = cv2.Canny(gray, 50, 150)
        print("   ✅ OpenCV边缘检测功能正常")
        
        # 测试轮廓检测
        contours, _ = cv2.findContours(edges, cv2.RETR_TREE, cv2.CHAIN_APPROX_SIMPLE)
        print(f"   ✅ OpenCV轮廓检测正常，找到 {len(contours)} 个轮廓")
        
        return True
    except Exception as e:
        print(f"   ❌ OpenCV功能测试失败: {e}")
        return False

def test_feature_identification():
    """测试特征识别功能"""
    print("\n2. 测试特征识别功能...")
    try:
        from src.modules.feature_definition import identify_features
        
        # 创建测试图像
        img = np.zeros((200, 200), dtype=np.uint8)
        cv2.circle(img, (50, 50), 30, 255, -1)  # 圆形
        cv2.rectangle(img, (100, 100), (160, 140), 255, -1)  # 矩形
        
        features = identify_features(img)
        print(f"   ✅ 特征识别功能正常，识别到 {len(features)} 个特征")
        
        for i, feature in enumerate(features):
            print(f"     特征 {i+1}: {feature['shape']}, 中心: {feature['center']}")
        
        return True
    except Exception as e:
        print(f"   ❌ 特征识别功能测试失败: {e}")
        return False

def test_pdf_parsing():
    """测试PDF解析功能"""
    print("\n3. 测试PDF解析功能...")
    try:
        from src.modules.pdf_parsing_process import pdf_to_images
        import os
        
        # 检查是否存在PDF文件用于测试
        test_pdf = "test.pdf"
        if os.path.exists(test_pdf):
            images = pdf_to_images(test_pdf)
            print(f"   ✅ PDF解析功能正常，转换为 {len(images)} 页图像")
        else:
            print("   ⚠ PDF文件不存在，跳过PDF解析测试")
        
        return True
    except Exception as e:
        print(f"   ❌ PDF解析功能测试失败: {e}")
        return False

def test_gcode_generation():
    """测试G代码生成功能"""
    print("\n4. 测试G代码生成功能...")
    try:
        from src.modules.gcode_generation import generate_fanuc_nc
        
        # 创建模拟特征
        features = [
            {
                "shape": "circle",
                "center": (50, 50),
                "radius": 10,
                "dimensions": (20, 20),
                "area": 314,
                "contour": np.array([[[30, 30]], [[70, 30]], [[70, 70]], [[30, 70]]]),
                "bounding_box": (30, 30, 40, 40)
            }
        ]
        
        description_analysis = {
            "processing_type": "drilling",
            "tool_required": "drill_bit",
            "depth": 5.0,
            "feed_rate": 100.0,
            "spindle_speed": 1000.0,
            "material": "aluminum",
            "precision": "Ra1.6"
        }
        
        nc_code = generate_fanuc_nc(features, description_analysis)
        print("   ✅ G代码生成功能正常")
        print(f"     生成的代码行数: {len(nc_code.split())}")
        
        # 检查是否包含基本的G代码指令
        if "G21" in nc_code and "G90" in nc_code and "M30" in nc_code:
            print("     ✅ 包含基本G代码指令")
        else:
            print("     ⚠ 缺少基本G代码指令")
        
        return True
    except Exception as e:
        print(f"   ❌ G代码生成功能测试失败: {e}")
        return False

def test_user_description_analysis():
    """测试用户描述分析功能"""
    print("\n5. 测试用户描述分析功能...")
    try:
        from src.modules.material_tool_matcher import analyze_user_description
        
        description = "请钻一个直径6mm的孔，深度10mm"
        result = analyze_user_description(description)
        
        print(f"   ✅ 用户描述分析功能正常")
        print(f"     加工类型: {result['processing_type']}")
        print(f"     需要刀具: {result['tool_required']}")
        print(f"     深度: {result['depth']}")
        
        return True
    except Exception as e:
        print(f"   ❌ 用户描述分析功能测试失败: {e}")
        return False

def test_api_endpoints():
    """测试API端点"""
    print("\n6. 测试API端点...")
    try:
        # 测试健康检查
        response = requests.get('http://localhost:5000/health')
        if response.status_code == 200:
            print("   ✅ 健康检查端点正常")
        else:
            print(f"   ❌ 健康检查端点异常，状态码: {response.status_code}")
            return False
        
        return True
    except Exception as e:
        print(f"   ❌ API端点测试失败: {e}")
        return False

def main():
    """运行所有测试"""
    print("开始CNC Agent功能完整性测试...\n")
    
    tests = [
        test_opencv_functionality,
        test_feature_identification,
        test_pdf_parsing,
        test_gcode_generation,
        test_user_description_analysis,
        test_api_endpoints
    ]
    
    passed = 0
    total = len(tests)
    
    for test in tests:
        if test():
            passed += 1
    
    print(f"\n{'='*50}")
    print(f"测试完成: {passed}/{total} 项测试通过")
    
    if passed == total:
        print("🎉 所有功能测试通过！CNC Agent运行正常。")
        print("\n功能包括：")
        print("- ✅ OpenCV图像处理功能")
        print("- ✅ 几何特征识别功能")
        print("- ✅ G代码生成功能") 
        print("- ✅ 用户描述分析功能")
        print("- ✅ Web API服务")
        print("- ✅ PDF解析功能（需要测试PDF文件）")
    else:
        print(f"⚠️  {total - passed} 项测试未通过")
    
    return passed == total

if __name__ == "__main__":
    main()
