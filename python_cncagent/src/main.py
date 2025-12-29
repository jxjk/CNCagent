"""
CNC Agent: 从PDF图纸自动生成FANUC NC程序的Python实现

此项目实现了以下功能：
1. PDF图纸解析与OCR处理
2. 几何特征识别
3. 用户描述理解
4. FANUC NC程序生成
5. 完整流程整合
6. AI辅助NC编程工具（新增）
"""

# 尝试加载 .env 文件
try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass  # 如果没有安装dotenv则跳过

import os
import sys
from pathlib import Path
from typing import Tuple, Optional, Dict, Any
from .modules.unified_generator import generate_cnc_with_unified_approach
from .modules.pdf_parsing_process import pdf_to_images, ocr_image, extract_text_from_pdf
from .modules.feature_definition import identify_features, extract_dimensions, extract_highest_y_center_point, adjust_coordinate_system, select_coordinate_reference
from .modules.material_tool_matcher import analyze_user_description
from .modules.gcode_generation import generate_fanuc_nc, validate_nc_code
from .modules.validation import validate_features, validate_user_description, validate_parameters
from .modules.simulation_output import generate_simulation_report, visualize_features
from .modules.mechanical_drawing_expert import MechanicalDrawingExpert
from .modules.ai_nc_helper import AI_NC_Helper
from .modules.simple_nc_gui import run_gui
import logging
import numpy as np

# 配置日志
logging.basicConfig(level=logging.INFO)


def _validate_inputs(user_description: str) -> None:
    """验证输入参数"""
    errors = validate_user_description(user_description)
    if errors:
        raise ValueError(f"用户描述验证失败: {', '.join(errors)}")


def _extract_text_from_images(images: List, all_text: str) -> str:
    """从图像中提取文本"""
    import logging
    ocr_success = True
    try:
        for img in images:
            ocr_result = ocr_image(img)
            all_text += ocr_result + "\n"
    except ImportError as e:
        logging.warning(f"OCR库未安装: {str(e)}，跳过OCR步骤")
        ocr_success = False
    except Exception as e:
        logging.warning(f"OCR处理失败: {str(e)}，跳过OCR步骤")
        ocr_success = False
    return all_text, ocr_success


def _identify_features_from_images(images: List, drawing_text: str) -> List[Dict]:
    """从图像中识别几何特征"""
    import logging
    features = []
    for img in images:
        # 将PIL图像转换为numpy数组（适用于OpenCV）
        img_array = np.array(img.convert('L'))  # 转换为灰度图
        img_features = identify_features(img_array, drawing_text=drawing_text)
        
        # 只保留置信度较高的特征
        high_confidence_features = [f for f in img_features if f.get('confidence', 0) > 0.7]
        logging.info(f"  从页面识别到 {len(img_features)} 个特征，其中高置信度特征 {len(high_confidence_features)} 个")
        features.extend(high_confidence_features)
    return features


def _analyze_and_validate_features(features: List[Dict], user_description: str) -> Tuple[Dict, List[Dict]]:
    """分析和验证识别的特征"""
    import logging
    logging.info(f"总共识别到 {len(features)} 个高置信度特征")
    
    # 验证识别出的特征
    if features:
        feature_errors = validate_features(features)
        if feature_errors:
            logging.warning(f"特征验证发现问题: {', '.join(feature_errors)}")
        
        # 显示识别到的特征信息
        logging.info("识别到的特征:")
        for i, feature in enumerate(features):
            shape = feature['shape']
            center = feature['center']
            dims = feature['dimensions']
            conf = feature.get('confidence', 1.0)
            if shape == 'counterbore':
                logging.info(f"  特征 {i+1}: {shape}, 中心{center}, 沉孔直径{feature.get('outer_diameter', 0):.1f}mm, 底孔直径{feature.get('inner_diameter', 0):.1f}mm, 深度{feature.get('depth', 0):.1f}mm, 置信度{conf:.2f}")
            else:
                logging.info(f"  特征 {i+1}: {shape}, 中心{center}, 尺寸{dims}, 置信度{conf:.2f}")
    else:
        logging.warning("未识别到任何高置信度几何特征")
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
    
    # 如果检测到沉孔加工，更新处理类型
    description = user_description.lower()
    if "沉孔" in description or "counterbore" in description or "锪孔" in description:
        description_analysis["processing_type"] = "counterbore"
    
    # 验证解析参数
    param_errors = validate_parameters(description_analysis)
    if param_errors:
        logging.warning(f"参数验证发现问题: {', '.join(param_errors)}")
    
    return description_analysis, features


def _select_and_adjust_coordinate_system(features: List[Dict], drawing_info: Any, description_analysis: Dict, 
                                       coordinate_strategy: str, custom_origin: Optional[Tuple[float, float]]) -> Tuple[List[Dict], Tuple[float, float]]:
    """选择并调整坐标系统"""
    import logging
    # 选择坐标参考点
    logging.info(f"使用坐标基准策略: {coordinate_strategy}")
    
    # 优先使用机械制图专家识别的参考点
    drawing_reference_points = {}
    if hasattr(drawing_info, 'views') and drawing_info.views:
        for view in drawing_info.views:
            drawing_reference_points.update(view.reference_points)
    
    # 从用户描述分析中提取参考点信息
    reference_points = description_analysis.get("reference_points", {})
    
    # 如果机械制图专家识别到参考点，优先使用
    if drawing_reference_points:
        logging.info(f"检测到图纸中的参考点: {drawing_reference_points}")
        # 使用图纸参考点
        first_drawing_ref = next(iter(drawing_reference_points.values()))
        origin_point = first_drawing_ref
    # 然后是用户在描述中指定的参考点
    elif reference_points:
        logging.info(f"检测到用户指定的参考点: {reference_points}")
        # 使用第一个参考点作为坐标原点
        first_ref_point = next(iter(reference_points.values()))
        origin_point = first_ref_point
    else:
        # 使用指定的坐标策略选择参考点
        origin_point = select_coordinate_reference(features, coordinate_strategy, custom_origin)
    
    logging.info(f"设置坐标原点为: {origin_point}")
    
    # 调整所有特征的坐标
    adjusted_features = adjust_coordinate_system(features, origin_point, coordinate_strategy, custom_origin)
    logging.info("坐标系统调整完成")
    
    return adjusted_features, origin_point


def generate_nc_from_pdf(pdf_path: str, user_description: str, scale: float = 1.0,
                        coordinate_strategy: str = "highest_y", custom_origin: Optional[Tuple[float, float]] = None,
                        api_key: Optional[str] = None, model: str = "gpt-3.5-turbo",
                        model_3d_path: Optional[str] = None) -> str:
    """
    完整流程：从PDF图纸、3D模型和用户描述生成NC程序（重构版）
    直接使用大模型生成，PDF/图像/3D模型特征仅作为辅助参考
    
    Args:
        pdf_path (str): PDF图纸路径
        user_description (str): 用户加工描述
        scale (float): 比例尺因子
        coordinate_strategy (str): 坐标基准策略
        custom_origin (Tuple[float, float]): 自定义原点坐标
        api_key (str): 大模型API密钥
        model (str): 使用的模型名称
        model_3d_path (str): 3D模型文件路径（可选）
    
    Returns:
        str: 生成的NC程序代码
    """
    import logging
    logging.info("开始处理输入文件...")
    
    # 使用重构后的AI优先生成器，直接调用大模型生成NC代码
    logging.info("使用大模型直接生成NC程序，PDF/3D模型特征仅作为辅助参考...")
    nc_program = generate_cnc_with_unified_approach(
        user_prompt=user_description, 
        pdf_path=pdf_path,
        model_3d_path=model_3d_path,  # 新增3D模型路径参数
        api_key=api_key,
        model=model
    )
    
    # 生成模拟报告和可视化
    logging.info("正在生成模拟报告...")
    try:
        # 尝试从AI生成的NC程序中提取一些信息用于报告
        # 这里我们创建一个简化的特征列表用于生成报告
        description_analysis = analyze_user_description(user_description)
        generate_simulation_report([], description_analysis, nc_program)
    except Exception as e:
        logging.warning(f"生成模拟报告时出现警告: {str(e)}")
    
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


def run_ai_helper_gui():
    """
    运行AI辅助NC编程工具的图形界面
    """
    print("启动AI辅助NC编程工具界面...")
    run_gui()


def generate_nc_with_ai_helper(pdf_path: str, user_description: str, material: str = "Aluminum", scale: float = 1.0) -> str:
    """
    使用AI辅助工具从PDF生成NC代码

    Args:
        pdf_path (str): PDF图纸路径
        user_description (str): 用户描述
        material (str): 材料类型
        scale (float): 比例尺因子

    Returns:
        str: 生成的NC程序代码
    """
    print("使用AI辅助工具生成NC程序...")
    
    # 初始化AI辅助工具
    nc_helper = AI_NC_Helper()
    
    # 提取文本信息
    from .modules.pdf_parsing_process import extract_text_from_pdf
    all_text = extract_text_from_pdf(pdf_path)
    
    # 使用AI辅助工具的PDF处理功能
    nc_code = nc_helper.process_pdf(
        pdf_path,
        all_text,
        material,
        user_description
    )
    return nc_code


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("用法:")
        print("  python main.py <command> [args...]")
        print("")
        print("命令选项:")
        print("  gui          启动AI辅助NC编程工具图形界面")
        print("  process      处理PDF并生成NC程序")
        print("  help         显示帮助信息")
        print("")
        print("处理PDF参数:")
        print("  python main.py process <pdf_path> [model_3d_path] <user_description> [scale] [coordinate_strategy] [custom_origin_x] [custom_origin_y]")
        print('  示例: python main.py process part_design.pdf part_model.stl "请加工一个100mm x 50mm的矩形，使用铣削加工" 1.0 highest_y')
        print("  坐标策略选项: highest_y, lowest_y, leftmost_x, rightmost_x, center, custom, geometric_center")
        print("  注意: 可同时提供PDF和3D模型文件，系统将结合两者信息生成更准确的NC代码")
        print("")
        print("环境变量设置:")
        print("  DEEPSEEK_API_KEY    设置DeepSeek API密钥（优先使用）")
        print("  DEEPSEEK_MODEL      设置DeepSeek使用的模型名称（默认: deepseek-chat）")
        print("  DEEPSEEK_API_BASE   设置DeepSeek API基础URL（默认: https://api.deepseek.com）")
        print("  OPENAI_API_KEY      设置OpenAI API密钥")
        print("  OPENAI_MODEL        设置OpenAI使用的模型名称（默认: gpt-3.5-turbo）")
        print("")
        print("新功能: 统一启动器 (推荐)")
        print("  python start_unified.py                    # 同时启动GUI和Web服务器")
        print("  python start_unified.py gui               # 仅启动GUI界面")
        print("  python start_unified.py web               # 仅启动Web服务器")
        print("  python start_unified.py both --port 8080  # 同时启动，自定义端口")
        sys.exit(1)
    
    command = sys.argv[1].lower()
    
    if command == "gui":
        run_ai_helper_gui()
    elif command == "help":
        print("CNC Agent - AI辅助NC编程工具使用说明")
        print("")
        print("可用命令:")
        print("  gui    - 启动图形界面")
        print("  process - 处理PDF并生成NC程序")
        print("  help   - 显示帮助信息")
    elif command == "process":
        if len(sys.argv) < 3:
            print("错误: 需要提供PDF路径和用户描述")
            print("用法: python main.py process <pdf_path> [model_3d_path] <user_description> [scale] [coordinate_strategy] [custom_origin_x] [custom_origin_y]")
            sys.exit(1)
        
        # 解析命令行参数
        # 参数顺序: command pdf_path [model_3d_path] user_description [scale] [coordinate_strategy] [custom_origin_x] [custom_origin_y]
        arg_idx = 2  # 从sys.argv[2]开始
        
        # 获取PDF路径
        pdf_path = sys.argv[arg_idx]
        arg_idx += 1
        
        # 检查下一个参数是否为3D模型文件
        model_3d_path = None
        if arg_idx < len(sys.argv):
            potential_3d_path = sys.argv[arg_idx]
            potential_path = Path(potential_3d_path)
            if potential_path.exists() and potential_path.suffix.lower() in ['.stl', '.step', '.stp', '.igs', '.iges', '.obj', '.ply', '.off', '.gltf', '.glb']:
                model_3d_path = potential_3d_path
                arg_idx += 1
        
        # 获取用户描述
        user_description = sys.argv[arg_idx] if arg_idx < len(sys.argv) else ""
        arg_idx += 1
        
        # 获取其他可选参数
        scale = float(sys.argv[arg_idx]) if arg_idx < len(sys.argv) else 1.0
        arg_idx += 1
        
        coordinate_strategy = sys.argv[arg_idx] if arg_idx < len(sys.argv) else "highest_y"
        arg_idx += 1
        
        custom_origin = None
        if arg_idx + 1 < len(sys.argv):  # 需要两个参数：x和y坐标
            try:
                custom_origin_x = float(sys.argv[arg_idx])
                custom_origin_y = float(sys.argv[arg_idx + 1])
                custom_origin = (custom_origin_x, custom_origin_y)
            except ValueError:
                print("自定义原点坐标必须是数字")
                sys.exit(1)
        
        # 安全验证PDF路径
        pdf_path = os.path.abspath(pdf_path)
        pdf_file = Path(pdf_path)
        if not pdf_file.exists():
            print(f"错误: PDF文件 {pdf_path} 不存在")
            sys.exit(1)
        if pdf_file.suffix.lower() != '.pdf':
            print(f"错误: 文件 {pdf_path} 不是PDF文件")
            sys.exit(1)
        # 防止路径遍历攻击
        base_path = Path.cwd().resolve()
        resolved_path = pdf_file.resolve()
        if not resolved_path.is_relative_to(base_path):
            print(f"错误: 文件路径 {pdf_path} 超出允许范围")
            sys.exit(1)
        
        # 验证3D模型路径（如果提供）
        if model_3d_path:
            model_3d_path = os.path.abspath(model_3d_path)
            model_file = Path(model_3d_path)
            if not model_file.exists():
                print(f"错误: 3D模型文件 {model_3d_path} 不存在")
                sys.exit(1)
            if model_file.suffix.lower() not in ['.stl', '.step', '.stp', '.igs', '.iges', '.obj', '.ply', '.off', '.gltf', '.glb']:
                print(f"错误: 文件 {model_3d_path} 不是支持的3D模型格式")
                print(f"支持的格式: .stl, .step, .stp, .igs, .iges, .obj, .ply, .off, .gltf, .glb")
                sys.exit(1)
            # 防止路径遍历攻击
            resolved_path = model_file.resolve()
            if not resolved_path.is_relative_to(base_path):
                print(f"错误: 文件路径 {model_3d_path} 超出允许范围")
                sys.exit(1)
        
        print(f"正在处理PDF文件: {pdf_path}")
        if model_3d_path:
            print(f"同时处理3D模型: {model_3d_path}")
        print(f"用户描述: {user_description}")
        print(f"比例: {scale}")
        print(f"坐标策略: {coordinate_strategy}")
        if custom_origin:
            print(f"自定义原点: {custom_origin}")
        
        try:
            # 检查是否提供了API密钥（优先使用DeepSeek，然后是OpenAI）
            import os
            api_key = os.getenv('DEEPSEEK_API_KEY') or os.getenv('OPENAI_API_KEY')  # 优先使用DeepSeek API密钥
            model = os.getenv('DEEPSEEK_MODEL', os.getenv('OPENAI_MODEL', 'deepseek-chat'))  # 优先使用DeepSeek模型，默认deepseek-chat
            
            nc_program = generate_nc_from_pdf(
                pdf_path, 
                user_description, 
                scale, 
                coordinate_strategy, 
                custom_origin,
                api_key=api_key,
                model=model,
                model_3d_path=model_3d_path  # 传递3D模型路径
            )
            print("\n生成的NC程序:")
            print(nc_program)
            
            # 保存NC程序到文件
            output_path = "output.nc"
            # 确保输出路径安全
            output_file = Path(output_path).resolve()
            base_path = Path.cwd().resolve()
            if not output_file.is_relative_to(base_path):
                print("错误: 输出路径超出允许范围")
                sys.exit(1)
            with open(output_path, "w", encoding="utf-8") as f:
                f.write(nc_program)
            print(f"\nNC程序已保存到: {output_path}")
            
        except Exception as e:
            print(f"处理过程中出现错误: {str(e)}")
            import traceback
            traceback.print_exc()
            sys.exit(1)
    else:
        print(f"未知命令: {command}")
        print("使用 'python main.py help' 查看帮助信息")



