"""
CNC Agent: 从PDF图纸自动生成FANUC NC程序的Python实现

此项目实现了以下功能：
1. PDF图纸解析与OCR处理
2. 几何特征识别
3. 用户描述理解
4. FANUC NC程序生成
5. 完整流程整合
"""
import os
import sys
from .modules.pdf_parsing_process import pdf_to_images, ocr_image, extract_text_from_pdf
from .modules.feature_definition import identify_features, extract_dimensions
from .modules.material_tool_matcher import analyze_user_description
from .modules.gcode_generation import generate_fanuc_nc, validate_nc_code
from .modules.validation import validate_features, validate_user_description, validate_parameters
from .modules.simulation_output import generate_simulation_report, visualize_features
import logging

# 配置日志
logging.basicConfig(level=logging.INFO)


def generate_nc_from_pdf(pdf_path: str, user_description: str, scale: float = 1.0) -> str:
    """
    完整流程：从PDF图纸和用户描述生成NC程序
    
    Args:
        pdf_path (str): PDF图纸路径
        user_description (str): 用户加工描述
        scale (float): 比例尺因子
    
    Returns:
        str: 生成的NC程序代码
    """
    print("开始处理PDF图纸...")
    
    # 1. 验证输入
    errors = validate_user_description(user_description)
    if errors:
        raise ValueError(f"用户描述验证失败: {', '.join(errors)}")
    
    # 2. PDF转换为图像
    print("正在将PDF转换为图像...")
    images = pdf_to_images(pdf_path)
    
    # 3. OCR提取文字（如果Tesseract可用）
    print("正在执行OCR识别...")
    all_text = ""
    ocr_success = True
    try:
        for img in images:
            ocr_result = ocr_image(img)
            all_text += ocr_result + "\n"
    except Exception as e:
        print(f"OCR处理失败: {str(e)}，跳过OCR步骤")
        ocr_success = False
        all_text = ""
    
    # 也可以直接从PDF提取文本（如果PDF包含可选择的文本）
    pdf_text = extract_text_from_pdf(pdf_path)
    all_text += "\n" + pdf_text
    
    # 4. 识别几何特征
    print("正在识别几何特征...")
    features = []
    for img in images:
        import numpy as np
        # 将PIL图像转换为numpy数组（适用于OpenCV）
        img_array = np.array(img.convert('L'))  # 转换为灰度图
        img_features = identify_features(img_array)
        features.extend(img_features)
    
    # 验证识别出的特征
    if features:
        feature_errors = validate_features(features)
        if feature_errors:
            print(f"警告: 特征验证发现问题: {', '.join(feature_errors)}")
    else:
        print("警告: 未识别到任何几何特征，将基于用户描述生成通用程序")
        # 创建一个默认特征以确保程序生成
        features = [{
            "shape": "rectangle",
            "contour": [],
            "bounding_box": (50, 50, 20, 20),
            "area": 400,
            "center": (60, 60),
            "dimensions": (20, 20),
            "length": 20,
            "width": 20
        }]
    
    # 根据比例尺提取实际尺寸
    scaled_features = extract_dimensions(features, scale)
    
    # 5. 分析用户描述
    print("正在分析用户描述...")
    description_analysis = analyze_user_description(user_description)
    
    # 验证解析参数
    param_errors = validate_parameters(description_analysis)
    if param_errors:
        print(f"警告: 参数验证发现问题: {', '.join(param_errors)}")
    
    # 6. 生成NC程序
    print("正在生成NC程序...")
    nc_program = generate_fanuc_nc(scaled_features, description_analysis, scale)
    
    # 验证NC程序
    nc_errors = validate_nc_code(nc_program)
    if nc_errors:
        print(f"警告: NC程序验证发现问题: {', '.join(nc_errors)}")
    
    # 7. 生成模拟报告和可视化
    print("正在生成模拟报告...")
    try:
        generate_simulation_report(scaled_features, description_analysis, nc_program)
        visualize_features(scaled_features)
    except Exception as e:
        print(f"生成模拟报告时出现警告: {str(e)}")
    
    return nc_program


def preprocess_image(image):
    """
    预处理图像以提高特征识别准确性
    这是一个简化版本，实际实现应该在pdf_parsing_process模块中
    """
    from PIL import Image
    import numpy as np
    
    # 转换为灰度图
    gray_img = image.convert('L')
    
    # 转换为numpy数组
    img_array = np.array(gray_img)
    
    return img_array


if __name__ == "__main__":
    if len(sys.argv) < 3:
        print("用法: python main.py <pdf_path> <user_description> [scale]")
        print("示例: python main.py part_design.pdf \"请加工一个100mm x 50mm的矩形，使用铣削加工\" 1.0")
        sys.exit(1)
    
    pdf_path = sys.argv[1]
    user_description = sys.argv[2]
    scale = float(sys.argv[3]) if len(sys.argv) > 3 else 1.0
    
    # 检查PDF文件是否存在
    if not os.path.exists(pdf_path):
        print(f"错误: PDF文件 {pdf_path} 不存在")
        sys.exit(1)
    
    print(f"正在处理PDF文件: {pdf_path}")
    print(f"用户描述: {user_description}")
    print(f"比例: {scale}")
    
    try:
        nc_program = generate_nc_from_pdf(pdf_path, user_description, scale)
        print("\n生成的NC程序:")
        print(nc_program)
        
        # 保存NC程序到文件
        output_path = "output.nc"
        with open(output_path, "w", encoding="utf-8") as f:
            f.write(nc_program)
        print(f"\nNC程序已保存到: {output_path}")
        
    except Exception as e:
        print(f"处理过程中出现错误: {str(e)}")
        import traceback
        traceback.print_exc()
        sys.exit(1)