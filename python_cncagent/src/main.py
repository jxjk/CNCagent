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
from .modules.feature_definition import identify_features, extract_dimensions, extract_highest_y_center_point, adjust_coordinate_system, select_coordinate_reference
from .modules.material_tool_matcher import analyze_user_description
from .modules.gcode_generation import generate_fanuc_nc, validate_nc_code
from .modules.validation import validate_features, validate_user_description, validate_parameters
from .modules.simulation_output import generate_simulation_report, visualize_features
from .modules.mechanical_drawing_expert import MechanicalDrawingExpert
import logging
import numpy as np

# 配置日志
logging.basicConfig(level=logging.INFO)


def generate_nc_from_pdf(pdf_path: str, user_description: str, scale: float = 1.0, 
                        coordinate_strategy: str = "highest_y", custom_origin: Tuple[float, float] = None) -> str:
    """
    完整流程：从PDF图纸和用户描述生成NC程序
    
    Args:
        pdf_path (str): PDF图纸路径
        user_description (str): 用户加工描述
        scale (float): 比例尺因子
        coordinate_strategy (str): 坐标基准策略
        custom_origin (Tuple[float, float]): 自定义原点坐标
    
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
    
    # 使用机械制图专家分析图纸
    print("正在使用机械制图专家分析图纸...")
    drawing_expert = MechanicalDrawingExpert()
    drawing_info = drawing_expert.parse_drawing(all_text)
    
    # 4. 识别几何特征
    print("正在识别几何特征...")
    features = []
    for img in images:
        # 将PIL图像转换为numpy数组（适用于OpenCV）
        img_array = np.array(img.convert('L'))  # 转换为灰度图
        img_features = identify_features(img_array)
        
        # 只保留置信度较高的特征
        high_confidence_features = [f for f in img_features if f.get('confidence', 0) > 0.7]
        print(f"  从页面识别到 {len(img_features)} 个特征，其中高置信度特征 {len(high_confidence_features)} 个")
        features.extend(high_confidence_features)
    
    print(f"总共识别到 {len(features)} 个高置信度特征")
    
    # 验证识别出的特征
    if features:
        feature_errors = validate_features(features)
        if feature_errors:
            print(f"警告: 特征验证发现问题: {', '.join(feature_errors)}")
        
        # 显示识别到的特征信息
        print("识别到的特征:")
        for i, feature in enumerate(features):
            shape = feature['shape']
            center = feature['center']
            dims = feature['dimensions']
            conf = feature.get('confidence', 1.0)
            if shape == 'counterbore':
                print(f"  特征 {i+1}: {shape}, 中心{center}, 沉孔直径{feature.get('outer_diameter', 0):.1f}mm, 底孔直径{feature.get('inner_diameter', 0):.1f}mm, 深度{feature.get('depth', 0):.1f}mm, 置信度{conf:.2f}")
            else:
                print(f"  特征 {i+1}: {shape}, 中心{center}, 尺寸{dims}, 置信度{conf:.2f}")
    else:
        print("警告: 未识别到任何高置信度几何特征")
        # 如果没有识别到特征，基于用户描述生成通用程序
        features = [{
            "shape": "rectangle",
            "contour": np.array([], dtype=np.int32),
            "bounding_box": (50, 50, 20, 20),
            "area": 400,
            "center": (60, 60),
            "dimensions": (20, 20),
            "length": 20,
            "width": 20,
            "confidence": 0.5
        }]
    
    # 分析用户描述以提取参考点信息
    description_analysis = analyze_user_description(user_description)
    
    # 选择坐标参考点
    print(f"使用坐标基准策略: {coordinate_strategy}")
    
    # 优先使用用户在描述中指定的参考点
    reference_points = description_analysis.get("reference_points", {})
    if reference_points:
        print(f"检测到用户指定的参考点: {reference_points}")
        # 使用第一个参考点作为坐标原点
        first_ref_point = next(iter(reference_points.values()))
        origin_point = first_ref_point
    else:
        # 使用指定的坐标策略选择参考点
        origin_point = select_coordinate_reference(features, coordinate_strategy, custom_origin)
    
    print(f"设置坐标原点为: {origin_point}")
    
    # 调整所有特征的坐标
    features = adjust_coordinate_system(features, origin_point, coordinate_strategy, custom_origin)
    print("坐标系统调整完成")
    
    # 根据比例尺提取实际尺寸
    scaled_features = extract_dimensions(features, scale)
    
    # 5. 分析用户描述
    print("正在分析用户描述...")
    
    # 如果检测到沉孔加工，更新处理类型
    description = user_description.lower()
    if "沉孔" in description or "counterbore" in description or "锪孔" in description:
        description_analysis["processing_type"] = "counterbore"
    
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
        print("用法: python main.py <pdf_path> <user_description> [scale] [coordinate_strategy] [custom_origin_x] [custom_origin_y]")
        print("示例: python main.py part_design.pdf \"请加工一个100mm x 50mm的矩形，使用铣削加工\" 1.0 highest_y")
        print("坐标策略选项: highest_y, lowest_y, leftmost_x, rightmost_x, center, custom, geometric_center")
        sys.exit(1)
    
    pdf_path = sys.argv[1]
    user_description = sys.argv[2]
    scale = float(sys.argv[3]) if len(sys.argv) > 3 else 1.0
    coordinate_strategy = sys.argv[4] if len(sys.argv) > 4 else "highest_y"
    
    custom_origin = None
    if len(sys.argv) > 6:
        try:
            custom_origin_x = float(sys.argv[5])
            custom_origin_y = float(sys.argv[6])
            custom_origin = (custom_origin_x, custom_origin_y)
        except ValueError:
            print("自定义原点坐标必须是数字")
            sys.exit(1)
    
    # 检查PDF文件是否存在
    if not os.path.exists(pdf_path):
        print(f"错误: PDF文件 {pdf_path} 不存在")
        sys.exit(1)
    
    print(f"正在处理PDF文件: {pdf_path}")
    print(f"用户描述: {user_description}")
    print(f"比例: {scale}")
    print(f"坐标策略: {coordinate_strategy}")
    if custom_origin:
        print(f"自定义原点: {custom_origin}")
    
    try:
        nc_program = generate_nc_from_pdf(pdf_path, user_description, scale, coordinate_strategy, custom_origin)
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
