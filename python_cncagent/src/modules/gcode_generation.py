"""
FANUC NC程序生成模块
根据识别的特征和用户描述生成符合FANUC标准的G代码
"""
from typing import List, Dict, Optional, Union
import math
import datetime
import logging

# 导入配置参数
from src.config import GCODE_GENERATION_CONFIG, THREAD_PITCH_MAP
from src.exceptions import NCGenerationError, handle_exception

# 导入优化模块
try:
    from src.modules.fanuc_optimization import optimize_tapping_cycle, optimize_drilling_cycle, get_thread_pitch
    from src.modules.cutting_optimization import cutting_optimizer
except ImportError:
    # 如果无法导入优化模块，使用基础实现
    def get_thread_pitch(thread_type: str) -> float:
        """根据螺纹类型获取标准螺距"""
        # 使用配置中的螺纹螺距映射
        thread_pitch_map = THREAD_PITCH_MAP
        
        # 提取螺纹规格（如"M10"中的"10"）
        if thread_type.startswith("M"):
            try:
                size = thread_type[1:]  # 获取M后面的数字
                if size in ["3", "4", "5", "6", "8", "10", "12"]:
                    return thread_pitch_map.get(f"M{size}", GCODE_GENERATION_CONFIG['tapping']['default_thread_pitch'])  # 使用配置中的默认螺距
                else:
                    # 对于其他M系列螺纹，按比例估算
                    size_num = int(size)
                    if size_num < 5:
                        return GCODE_GENERATION_CONFIG['tapping']['default_thread_pitch'] * 0.33  # 小螺纹螺距较小
                    elif size_num < 10:
                        return GCODE_GENERATION_CONFIG['tapping']['default_thread_pitch'] * 0.67  # 中等螺纹螺距中等
                    else:
                        return GCODE_GENERATION_CONFIG['tapping']['default_thread_pitch']  # 大螺纹螺距较大
            except ValueError:
                return GCODE_GENERATION_CONFIG['tapping']['default_thread_pitch']  # 无法解析时使用默认值
        else:
            return GCODE_GENERATION_CONFIG['tapping']['default_thread_pitch']  # 非标准格式使用配置中的默认值


def generate_fanuc_nc(features: List[Dict], description_analysis: Dict, scale: float = 1.0) -> str:
    """
    根据识别特征和用户描述生成FANUC NC程序
    
    Args:
        features (list): 识别出的几何特征列表
        description_analysis (dict): 用户描述分析结果
        scale (float): 比例尺因子
    
    Returns:
        str: 生成的NC程序代码
        
    Raises:
        NCGenerationError: NC代码生成过程中发生错误
    """
    # 输入验证
    if not isinstance(features, list):
        raise NCGenerationError("特征列表必须是list类型")
    
    if not isinstance(description_analysis, dict):
        raise NCGenerationError("描述分析结果必须是dict类型")
    
    if not isinstance(scale, (int, float)):
        raise NCGenerationError("比例尺必须是数字类型")
    
    if scale <= 0:
        raise NCGenerationError("比例尺必须是正数")
    
    # 验证每个特征
    for i, feature in enumerate(features):
        feature_errors = _validate_feature(feature)
        if feature_errors:
            raise NCGenerationError(f"特征 {i} 验证失败: {', '.join(feature_errors)}")
    
    try:
        gcode = []
        
        # 程序头部注释 - 符合FANUC规范
        gcode.append("O0001 (MAIN PROGRAM)")
        gcode.append("(DESCRIPTION: FANUC CNC PROGRAM FOR FEATURE MACHINING)")
        gcode.append(f"(DATE: {datetime.datetime.now().strftime('%Y-%m-%d')})")
        gcode.append("(AUTHOR: CNC AGENT)")
        gcode.append("")
        
        # 添加程序准备指令
        gcode.append("(PROGRAM PREPARATION)")
        gcode.append("G21 (MILLIMETER UNITS)")
        gcode.append("G90 (ABSOLUTE COORDINATE SYSTEM)")
        gcode.append("G40 (CANCEL TOOL RADIUS COMPENSATION)")
        gcode.append("G49 (CANCEL TOOL LENGTH COMPENSATION)")
        gcode.append("G80 (CANCEL FIXED CYCLE)")
        gcode.append("")
        
        # 坐标系统说明
        gcode.append("(COORDINATE SYSTEM SETUP)")
        gcode.append("(G90 - USE ABSOLUTE COORDINATE SYSTEM)")
        gcode.append("(USER COORDINATE SYSTEM - COORDINATES RELATIVE TO WORKPIECE DATUM)")
        gcode.append("(X,Y COORDINATES ARE ADJUSTED BASED ON FEATURE POSITIONS)")
        gcode.append("")
        
        # 设置初始安全高度
        gcode.append("(MOVE TO SAFE HEIGHT)")
        gcode.append(f"G00 Z{GCODE_GENERATION_CONFIG['safety']['safe_height']:.1f} (RAPID MOVE TO SAFE HEIGHT)")
        gcode.append("")
        
        # 根据加工类型生成G代码
        processing_type = description_analysis.get("processing_type", "general")
        tool_required = description_analysis.get("tool_required", "general_tool")
        
        # 根据加工类型生成G代码
        if processing_type == "drilling":
            gcode.extend(_generate_drilling_code(features, description_analysis))
            # 添加程序结束
            gcode.append("")
            gcode.append("(PROGRAM END)")
            gcode.append("M05 (SPINDLE STOP)")
            gcode.append("G00 Z100.0 (RAISE TOOL TO SAFE HEIGHT)")
            gcode.append("G00 X10.0 Y10.0 (MOVE TO SAFE POSITION - USER CAN MODIFY AS NEEDED)")
            gcode.append("M30 (PROGRAM END)")
        elif processing_type == "tapping":  # 新增攻丝工艺
            gcode.extend(_generate_tapping_code_with_full_process(features, description_analysis))
            # 攻丝工艺完成后，添加程序结束指令
            gcode.append("")
            gcode.append("(PROGRAM END)")
            gcode.append("M05 (SPINDLE STOP)")
            gcode.append("G00 Z100.0 (RAISE TOOL TO SAFE HEIGHT)")
            gcode.append("G00 X10.0 Y10.0 (MOVE TO SAFE POSITION - USER CAN MODIFY AS NEEDED)")
            gcode.append("M30 (PROGRAM END)")
        elif processing_type == "milling":
            gcode.extend(_generate_milling_code(features, description_analysis))
            # 添加程序结束
            gcode.append("")
            gcode.append("(PROGRAM END)")
            gcode.append("M05 (SPINDLE STOP)")
            gcode.append("G00 Z100.0 (RAISE TOOL TO SAFE HEIGHT)")
            gcode.append("G00 X10.0 Y10.0 (MOVE TO SAFE POSITION - USER CAN MODIFY AS NEEDED)")
            gcode.append("M30 (PROGRAM END)")
        elif processing_type == "counterbore":  # 新增沉孔加工工艺
            gcode.extend(_generate_counterbore_code(features, description_analysis))
            # 添加程序结束
            gcode.append("")
            gcode.append("(PROGRAM END)")
            gcode.append("M05 (SPINDLE STOP)")
            gcode.append("G00 Z100.0 (RAISE TOOL TO SAFE HEIGHT)")
            gcode.append("G00 X10.0 Y10.0 (MOVE TO SAFE POSITION - USER CAN MODIFY AS NEEDED)")
            gcode.append("M30 (PROGRAM END)")
        elif processing_type == "turning":
            gcode.extend(_generate_turning_code(features, description_analysis))
            # 添加程序结束
            gcode.append("")
            gcode.append("(PROGRAM END)")
            gcode.append("M05 (SPINDLE STOP)")
            gcode.append("G00 Z100.0 (RAISE TOOL TO SAFE HEIGHT)")
            gcode.append("G00 X10.0 Y10.0 (MOVE TO SAFE POSITION - USER CAN MODIFY AS NEEDED)")
            gcode.append("M30 (PROGRAM END)")
        else:
            description = description_analysis.get("description", "")
            # 确保描述字符串正确处理中文字符
            if isinstance(description, bytes):
                try:
                    description = description.decode('utf-8')
                except UnicodeError:
                    description = description.decode('utf-8', errors='replace')
            elif not isinstance(description, str):
                description = str(description)
            description = description.lower()
            
            # 使用更精确的正则表达式来判断加工类型，避免冲突
            import re
            
            # 检查用户描述中是否包含沉孔相关关键词 - 优先级最高
            if re.search(r'(?:沉孔|counterbore|锪孔)', description):
                gcode.extend(_generate_counterbore_code(features, description_analysis))
                # 沉孔加工完成后，添加程序结束指令
                gcode.append("")
                gcode.append("(PROGRAM END)")
                gcode.append("M05 (SPINDLE STOP)")
                gcode.append("G00 Z100.0 (RAISE TOOL TO SAFE HEIGHT)")
                gcode.append("G00 X10.0 Y10.0 (MOVE TO SAFE POSITION - USER CAN MODIFY AS NEEDED)")
                gcode.append("M30 (PROGRAM END)")
            # 检查用户描述中是否包含螺纹相关关键词 - 第二优先级
            elif re.search(r'(?:螺纹|thread|tapping|攻丝)', description):
                gcode.extend(_generate_tapping_code_with_full_process(features, description_analysis))
                # 攻丝工艺完成后，添加程序结束指令
                gcode.append("")
                gcode.append("(PROGRAM END)")
                gcode.append("M05 (SPINDLE STOP)")
                gcode.append("G00 Z100.0 (RAISE TOOL TO SAFE HEIGHT)")
                gcode.append("G00 X10.0 Y10.0 (MOVE TO SAFE POSITION - USER CAN MODIFY AS NEEDED)")
                gcode.append("M30 (PROGRAM END)")
            # 检查用户描述中是否包含钻孔相关关键词 - 第三优先级
            elif re.search(r'(?:钻孔|drill|hole|钻)', description) and not re.search(r'(?:沉孔|counterbore|锪孔)', description):
                gcode.extend(_generate_drilling_code(features, description_analysis))
                # 添加程序结束
                gcode.append("")
                gcode.append("(PROGRAM END)")
                gcode.append("M05 (SPINDLE STOP)")
                gcode.append("G00 Z100.0 (RAISE TOOL TO SAFE HEIGHT)")
                gcode.append("G00 X10.0 Y10.0 (MOVE TO SAFE POSITION - USER CAN MODIFY AS NEEDED)")
                gcode.append("M30 (PROGRAM END)")
            # 检查用户描述中是否包含铣削相关关键词 - 仅在没有沉孔、钻孔等特殊工艺时才考虑铣削
            elif re.search(r'(?:铣|mill|cut)', description) and not any(re.search(keyword, description) for keyword in [r'沉孔', r'counterbore', r'锪孔', r'钻孔', r'drill']):
                gcode.extend(_generate_milling_code(features, description_analysis))
                # 添加程序结束
                gcode.append("")
                gcode.append("(PROGRAM END)")
                gcode.append("M05 (SPINDLE STOP)")
                gcode.append("G00 Z100 (RAISE TOOL TO SAFE HEIGHT)")
                gcode.append("G00 X10.0 Y10.0 (MOVE TO SAFE POSITION - USER CAN MODIFY AS NEEDED)")
                gcode.append("M30 (PROGRAM END)")
            else:
                # 默认使用铣削代码
                gcode.extend(_generate_milling_code(features, description_analysis))
                # 添加程序结束
                gcode.append("")
                gcode.append("(PROGRAM END)")
                gcode.append("M05 (SPINDLE STOP)")
                gcode.append("G00 Z100 (RAISE TOOL TO SAFE HEIGHT)")
                gcode.append("G00 X10.0 Y10.0 (MOVE TO SAFE POSITION - USER CAN MODIFY AS NEEDED)")
                gcode.append("M30 (PROGRAM END)")

        return "\n".join(gcode)
    except Exception as e:
        error = handle_exception(e, logging.getLogger(__name__), "生成FANUC NC代码时出错")
        raise NCGenerationError(f"NC代码生成失败: {str(error)}", original_exception=e) from e


def _get_tool_number(tool_type: str) -> int:
    """根据刀具类型返回刀具编号"""
    # 使用配置中的刀具映射
    from src.config import TOOL_MAPPING
    return TOOL_MAPPING.get(tool_type, 5)


def _generate_drilling_code(features: List[Dict], description_analysis: Dict) -> List[str]:
    """生成钻孔加工代码"""
    gcode = []
    
    # 获取材料信息，默认为铝
    material = "aluminum"  # 默认值
    if description_analysis:
        material_temp = description_analysis.get("material", "aluminum")
        if material_temp is not None:
            material = str(material_temp).lower()
        else:
            material = "aluminum"
    else:
        material = "aluminum"
    
    # 获取刀具直径信息
    tool_diameter = 12.0  # 默认使用φ12钻头
    if description_analysis:
        temp_diameter = description_analysis.get("tool_diameter", 12.0)
        if temp_diameter is not None:
            tool_diameter = float(temp_diameter)
        else:
            tool_diameter = 12.0
    
    # 获取工件尺寸信息，用于优化切削参数
    workpiece_dimensions = None
    if description_analysis:
        workpiece_dimensions = description_analysis.get("workpiece_dimensions", None)
    
    # 使用切削工艺优化器计算最优参数
    try:
        optimal_params = cutting_optimizer.calculate_optimal_cutting_parameters(
            material=material,
            tool_type="drill_bit",  # 钻头
            tool_diameter=tool_diameter,
            workpiece_dimensions=workpiece_dimensions,
            operation_type="drilling"
        )
        
        # 应用优化后的参数
        spindle_speed = optimal_params["spindle_speed"]
        feed_rate = optimal_params["feed_rate"]
        
        # 验证优化参数
        validation_errors = cutting_optimizer.validate_cutting_parameters(
            optimal_params, tool_diameter, workpiece_dimensions
        )
        if validation_errors:
            gcode.append(f"(WARNING: OPTIMIZATION ISSUES DETECTED: {', '.join(validation_errors)})")
            # 仍然使用优化参数，但添加警告注释
    except Exception as e:
        # 如果优化失败，使用默认参数
        gcode.append(f"(WARNING: Optimization failed, using default parameters: {str(e)})")
        spindle_speed = GCODE_GENERATION_CONFIG['drilling']['default_spindle_speed']
        feed_rate = GCODE_GENERATION_CONFIG['drilling']['default_feed_rate']
    
    # 设置钻孔参数 - 优先使用从用户描述中提取的参数
    depth = description_analysis.get("depth")
    if depth is None or not isinstance(depth, (int, float)):
        # 如果描述分析中没有提供深度，使用配置中的默认值
        depth = GCODE_GENERATION_CONFIG['drilling']['default_depth']  # 使用配置中的默认值
    else:
        depth = float(depth)
    
    feed_rate_input = description_analysis.get("feed_rate")
    if feed_rate_input is not None and isinstance(feed_rate_input, (int, float)):
        feed_rate = float(feed_rate_input)  # 如果用户提供了具体进给，则使用它
    
    # 获取刀具编号（钻头通常是T2）
    tool_number = _get_tool_number("drill_bit")
    
    gcode.append(f"(DRILLING OPERATION)")
    gcode.append(f"M03 S{int(spindle_speed)} (SPINDLE FORWARD, DRILLING SPEED)")
    gcode.append(f"G04 P{GCODE_GENERATION_CONFIG['safety']['delay_time']} (DELAY 1 SECOND, WAIT FOR SPINDLE TO REACH SET SPEED)")
    
    # 激活刀具长度补偿
    gcode.append(f"G43 H{tool_number} Z100. (ACTIVATE TOOL LENGTH COMPENSATION FOR T{tool_number:02})")
    
    # 开启切削液
    gcode.append("M08 (COOLANT ON)")
    
    # 为每个圆形特征生成钻孔点
    hole_features = [f for f in features if f["shape"] in ["circle", "square", "rectangle"]]
    if hole_features:
        # 首先在第一个孔执行完整循环
        first_feature = hole_features[0]
        center_x, center_y = first_feature["center"]
        # 使用优化的钻孔循环G83，考虑切削深度和排屑
        gcode.append(f"G99 G83 X{center_x:.3f} Y{center_y:.3f} Z{-depth:.3f} R2.0 Q{min(tool_diameter/2, 3.0):.1f} F{feed_rate:.1f} (DEEP HOLE DRILLING CYCLE WITH PECKING)")
        
        # 对于后续孔，只使用X、Y坐标，简化编程
        for feature in hole_features[1:]:
            center_x, center_y = feature["center"]
            gcode.append(f"X{center_x:.3f} Y{center_y:.3f} (DRILLING OPERATION)")
    else:
        gcode.append(f"G99 G83 Z{-depth:.3f} R2.0 Q{min(tool_diameter/2, 3.0):.1f} F{feed_rate:.1f} (DEEP HOLE DRILLING CYCLE WITH PECKING)")
    
    gcode.append("G80 (CANCEL FIXED CYCLE)")
    
    # 关闭切削液
    gcode.append("M09 (COOLANT OFF)")
    
    # 移动到统一的安全高度，然后取消刀具长度补偿
    gcode.append("G00 Z100.0 (RAPID MOVE TO UNIFIED SAFE HEIGHT)")
    gcode.append("G49 (CANCEL TOOL LENGTH COMPENSATION)")
    
    return gcode


def _extract_counterbore_parameters(features: List[Dict], description_analysis: Dict) -> Tuple[float, float, float, int, List[Tuple[float, float]], float, float, float, float, float]:
    """提取沉孔加工参数"""
    # 默认参数
    outer_diameter = GCODE_GENERATION_CONFIG['counterbore']['default_outer_diameter']  # 沉孔直径
    inner_diameter = GCODE_GENERATION_CONFIG['counterbore']['default_inner_diameter']  # 底孔直径
    counterbore_depth = GCODE_GENERATION_CONFIG['counterbore']['default_depth']  # 沉孔深度
    
    # 优先从描述分析中提取直径信息（最高优先级）
    if "outer_diameter" in description_analysis and description_analysis["outer_diameter"] is not None:
        outer_diameter = description_analysis["outer_diameter"]
        print(f"DEBUG: 使用描述分析中的外径: {outer_diameter}")
    if "inner_diameter" in description_analysis and description_analysis["inner_diameter"] is not None:
        inner_diameter = description_analysis["inner_diameter"]
        print(f"DEBUG: 使用描述分析中的内径: {inner_diameter}")
    
    # 从用户描述中提取参数（第二优先级）
    description = description_analysis.get("description", "")
    import re
    
    # 优化的提取逻辑，更准确地处理目标描述
    # 先尝试使用_material_tool_matcher模块中的函数
    from src.modules.material_tool_matcher import _extract_counterbore_diameters
    extracted_outer, extracted_inner = _extract_counterbore_diameters(description)
    
    # 修复：如果提取函数返回了有效值，才更新直径
    if extracted_outer is not None and extracted_outer > 0:
        outer_diameter = extracted_outer
        print(f"DEBUG: 从优化的提取函数中获取外径: {outer_diameter}")
    if extracted_inner is not None and extracted_inner > 0:
        inner_diameter = extracted_inner
        print(f"DEBUG: 从优化的提取函数中获取内径: {inner_diameter}")
    
    # 如果通过优化函数没有提取到，再使用原来的正则表达式方法
    if outer_diameter == GCODE_GENERATION_CONFIG['counterbore']['default_outer_diameter']:
        # 改进正则表达式，更精确匹配沉孔直径
        # 避免匹配φ234这样的图纸参考尺寸
        outer_matches = re.findall(r'(?:加工|要求|需要|进行)\s*.*?φ\s*(\d+\.?\d*).*?(?:沉孔|锪孔|counterbore|沉头孔)', description)
        if not outer_matches:
            # 尝试其他可能的格式，但排除图纸参考（通常在"正视图"、"俯视图"等后面）
            # 先排除图纸参考信息
            # 移除包含"正视图φ234的圆的圆心最高点"这类信息
            filtered_desc = re.sub(r'[正视图俯视图侧视图].*?φ\s*\d+.*?[,，。]', '', description)
            outer_matches = re.findall(r'φ\s*(\d+\.?\d*).*?(?:沉孔|锪孔|counterbore|沉头孔)', filtered_desc)
        if not outer_matches:
            # 再尝试其他格式
            outer_matches = re.findall(r'(?:沉孔|锪孔|counterbore).*?φ\s*(\d+\.?\d*)', description)
        if outer_matches:
            try:
                outer_diameter = float(outer_matches[0])
                # 验证直径是否在合理范围内（避免误匹配图纸参考尺寸）
                if 5 <= outer_diameter <= 50:  # 沉孔直径通常在5-50mm之间
                    print(f"DEBUG: 从描述中提取外径: {outer_diameter}")
                else:
                    print(f"DEBUG: 忽略不合理的直径: {outer_diameter}")
            except ValueError:
                pass
    
    if inner_diameter == GCODE_GENERATION_CONFIG['counterbore']['default_inner_diameter']:
        # 改进正则表达式，更精确匹配底孔直径
        inner_matches = re.findall(r'(?:底孔|贯通孔|thru|通孔).*?φ\s*(\d+\.?\d*)', description)
        if not inner_matches:
            inner_matches = re.findall(r'φ\s*(\d+\.?\d*).*?(?:底孔|贯通孔|thru|通孔)', description)
        if not inner_matches:
            # 其他可能的格式
            inner_matches = re.findall(r'(?:钻孔|drill).*?φ\s*(\d+\.?\d*)', description)
        if inner_matches:
            try:
                inner_diameter = float(inner_matches[0])
                print(f"DEBUG: 从描述中提取内径: {inner_diameter}")
            except ValueError:
                pass
    
    # 再次尝试从描述分析中获取直径信息（如果前面都没有获取到）
    # 但要确保不是默认值或无效值
    if "outer_diameter" in description_analysis and description_analysis["outer_diameter"] is not None:
        temp_outer = description_analysis["outer_diameter"]
        # 检查是否为有效直径（在合理范围内且不等于默认值）
        # 并且确保它不是φ234这样的图纸参考尺寸
        if (temp_outer != GCODE_GENERATION_CONFIG['counterbore']['default_outer_diameter'] and 
            5 <= temp_outer <= 50 and  # 限制在外径合理范围内
            temp_outer != 234.0):      # 排除φ234这个图纸尺寸
            outer_diameter = temp_outer
            print(f"DEBUG: 从描述分析中获取外径: {outer_diameter}")
    if "inner_diameter" in description_analysis and description_analysis["inner_diameter"] is not None:
        temp_inner = description_analysis["inner_diameter"]
        # 检查是否为有效直径（在合理范围内且不等于默认值）
        if (temp_inner != GCODE_GENERATION_CONFIG['counterbore']['default_inner_diameter'] and 
            1 <= temp_inner <= 30 and  # 限制在内径合理范围内
            temp_inner != 234.0):      # 排除φ234这个图纸尺寸
            inner_diameter = temp_inner
            print(f"DEBUG: 从描述分析中获取内径: {inner_diameter}")
    
    # 从沉孔特征中提取实际参数（第三优先级）
    counterbore_features = [f for f in features if f.get("shape") == "counterbore"]
    if counterbore_features and outer_diameter == GCODE_GENERATION_CONFIG['counterbore']['default_outer_diameter'] and inner_diameter == GCODE_GENERATION_CONFIG['counterbore']['default_inner_diameter']:
        # 使用第一个沉孔特征的参数，但只有在描述分析和用户描述中都没有提供时才使用
        first_counterbore = counterbore_features[0]
        outer_diameter = first_counterbore.get("outer_diameter", outer_diameter)
        inner_diameter = first_counterbore.get("inner_diameter", inner_diameter)
        counterbore_depth = first_counterbore.get("depth", counterbore_depth)
        print(f"DEBUG: 从特征中提取参数 - 外径: {outer_diameter}, 内径: {inner_diameter}, 深度: {counterbore_depth}")
    
    # 从描述中提取深度（如果在特征中没有找到或描述中明确给出）
    if counterbore_depth == GCODE_GENERATION_CONFIG['counterbore']['default_depth']:
        depth_matches = re.findall(r'深.*?(\d+\.?\d*)\s*mm', description)
        if depth_matches:
            try:
                counterbore_depth = float(depth_matches[0])
                print(f"DEBUG: 从描述中提取深度: {counterbore_depth}")
            except ValueError:
                pass
    
    # 确保直径值有效
    if outer_diameter is None or outer_diameter <= 0:
        print(f"DEBUG: 修正外径为默认值 22.0")
        outer_diameter = 22.0
    if inner_diameter is None or inner_diameter <= 0:
        print(f"DEBUG: 修正内径为默认值 14.5")
        inner_diameter = 14.5
    
    # 检查用户描述中的孔数量信息
    hole_count = 3  # 默认3个孔
    count_matches = re.findall(r'(\d+)\s*个', description)
    if count_matches:
        try:
            hole_count = int(count_matches[0])
            print(f"DEBUG: 从描述中提取孔数量: {hole_count}")
        except ValueError:
            hole_count = 3
    
    # 获取沉孔位置信息
    counterbore_positions = []
    for feature in features:
        if feature["shape"] == "counterbore":
            center_x, center_y = feature["center"]
            counterbore_positions.append((center_x, center_y))
    
    # 如果从图纸没有识别到特征，尝试从用户描述中提取孔位置
    if not counterbore_positions:
        user_hole_positions = description_analysis.get("hole_positions", [])
        if user_hole_positions:
            counterbore_positions = user_hole_positions
            print(f"DEBUG: 从描述分析中获取孔位置: {counterbore_positions}")
    
    # 从描述中提取坐标位置（特别针对目标描述）
    if not counterbore_positions:
        # 修复：使用更精确的正则表达式，避免将X坐标误认为孔直径
        # 匹配 "X94.0Y-30. X94.0Y90. X94.0Y210." 这样的格式
        # 修复：确保不将X坐标误认为直径
        coord_pattern = r'X\s*(\d+\.?\d*)\s*Y\s*([+-]?\d+\.?\d*)'
        coord_matches = re.findall(coord_pattern, description)
        if coord_matches:
            # 确保X坐标不是直径值，避免将94.0误认为直径
            for match in coord_matches:
                try:
                    x = float(match[0])
                    y = float(match[1])
                    # 验证X坐标是否为合理的直径值，如果是，则不将其作为坐标
                    # 如果X坐标小于50且与已知直径相似，跳过
                    # 只有当X坐标明显不是直径时才添加为位置
                    if x > 50 or (x not in [outer_diameter, inner_diameter]):  # 50mm是沉孔直径的合理上限
                        counterbore_positions.append((x, y))
                        print(f"DEBUG: 添加坐标位置 ({x}, {y})")
                except ValueError:
                    continue
            print(f"DEBUG: 从描述中提取坐标位置: {counterbore_positions}")
        
        # 如果上面的模式没有匹配到，尝试更通用的模式
        if not counterbore_positions:
            # 匹配X,Y坐标，但排除"φ数字X"这样的模式
            # 使用后处理过滤，而不是复杂的正则表达式
            coord_pattern = r'\s*X\s*(\d{2,}\.?\d*)\s*Y\s*([+-]?\d{1,}\.?\d*)'
            coord_matches = re.findall(coord_pattern, description)
            
            # 过滤掉前面有φ数字的匹配项
            valid_matches = []
            for match in coord_matches:
                x_val = match[0]
                # 检查匹配位置前面是否是φ数字模式
                pattern = r'\s*X\s*' + re.escape(x_val) + r'\s*Y\s*' + re.escape(match[1])
                for match_obj in re.finditer(pattern, description):
                    start_pos = match_obj.start()
                    # 检查X前面是否有φ+数字
                    preceding_text = description[:start_pos]
                    phi_match = re.search(r'φ\s*\d+$', preceding_text)
                    if not phi_match:  # 如果X前面没有φ数字，则保留这个匹配
                        valid_matches.append(match)
            
            for match in valid_matches:
                try:
                    x = float(match[0])
                    y = float(match[1])
                    # 验证坐标值是否在合理范围内，避免匹配到其他数字
                    # 并确保X坐标不是直径值
                    if -300 <= x <= 300 and -300 <= y <= 300 and x != outer_diameter:
                        counterbore_positions.append((x, y))
                        print(f"DEBUG: 添加坐标位置 ({x}, {y})")
                except ValueError:
                    continue
            print(f"DEBUG: 从描述中提取坐标位置(备用模式): {counterbore_positions}")
        
        # 再次尝试更精确的模式，特别针对"X94.0Y-30."这样的格式
        if not counterbore_positions:
            # 匹配"X数字Y数字"的连续格式
            # 使用简单的模式并过滤结果
            coord_pattern = r'X\s*(\d{2,}\.?\d*)\s*Y\s*([+-]?\d+\.?\d*)'
            coord_matches = re.findall(coord_pattern, description)
            
            # 过滤掉前面有φ数字的匹配项
            valid_matches = []
            for match in coord_matches:
                x_val = match[0]
                # 检查匹配位置前面是否是φ数字模式
                pattern = r'X\s*' + re.escape(x_val) + r'\s*Y\s*' + re.escape(match[1])
                for match_obj in re.finditer(pattern, description):
                    start_pos = match_obj.start()
                    # 检查X前面是否有φ+数字
                    preceding_text = description[:start_pos]
                    phi_match = re.search(r'φ\s*\d+$', preceding_text)
                    if not phi_match:  # 如果X前面没有φ数字，则保留这个匹配
                        valid_matches.append(match)
            
            for match in valid_matches:
                try:
                    x = float(match[0])
                    y = float(match[1])
                    # 验证坐标值是否在合理范围内，避免匹配到其他数字
                    # 并确保X坐标不是直径值
                    if -300 <= x <= 300 and -300 <= y <= 300:
                        # 额外验证：确保不是将直径误认为X坐标
                        if x != outer_diameter and x != inner_diameter:
                            counterbore_positions.append((x, y))
                            print(f"DEBUG: 添加坐标位置 ({x}, {y})")
                except ValueError:
                    continue
            print(f"DEBUG: 从描述中提取坐标位置(精确模式): {counterbore_positions}")
    
    # 如果仍没有找到位置，尝试从极坐标格式中提取
    if not counterbore_positions:
        # 支持极坐标格式如 "R=50 θ=30°" 或 "R50θ30" 等
        import re
        polar_patterns = [
            r'R\s*[=:]\s*(\d+\.?\d*)\s*(?:θ|theta|角度|θ=|θ:)\s*(\d+\.?\d*)\s*(?:°|度)?',  # R=50 θ=30°
            r'R\s*(\d+\.?\d*)\s*(?:θ|theta|角度)\s*(\d+\.?\d*)\s*(?:°|度)?',  # R50θ30
            r'(?:极径|半径)\s*(\d+\.?\d*)\s*(?:极角|角度)\s*(\d+\.?\d*)\s*(?:°|度)?',  # 极径50 极角30度
        ]
        
        for pattern in polar_patterns:
            polar_matches = re.findall(pattern, description, re.IGNORECASE)
            if polar_matches:
                # 假设这些极坐标是相对于某个基准点的
                # 使用从描述分析中获取的基准点信息
                reference_points = description_analysis.get("reference_points", {})
                base_x = 0.0
                base_y = 0.0
                # 如果有基准点信息，使用它
                if reference_points and 'origin' in reference_points:
                    base_x, base_y = reference_points['origin']
                
                for match in polar_matches:
                    try:
                        radius = float(match[0])
                        angle_deg = float(match[1])
                        # 将极坐标转换为直角坐标
                        angle_rad = math.radians(angle_deg)
                        x = base_x + radius * math.cos(angle_rad)
                        y = base_y + radius * math.sin(angle_rad)
                        
                        # 验证转换后的坐标是否在合理范围内
                        if -300 <= x <= 300 and -300 <= y <= 300:
                            counterbore_positions.append((round(x, 3), round(y, 3)))
                    except (ValueError, TypeError):
                        continue
                if counterbore_positions:
                    print(f"DEBUG: 从极坐标格式提取位置: {counterbore_positions}")
                    break
    
    # 根据用户描述的孔数量限制实际加工的孔数量
    if len(counterbore_positions) > hole_count:
        # 如果识别到的孔数量超过用户要求的数量，只取前几个
        counterbore_positions = counterbore_positions[:hole_count]
        print(f"DEBUG: 限制孔位置数量为 {hole_count}")
    
    # 如果仍然没有孔位置，但用户要求加工沉孔，提供一个默认位置
    if not counterbore_positions:
        if "沉孔" in description or "counterbore" in description or "锪孔" in description:
            counterbore_positions = [(50.0, 50.0)]  # 默认位置
            print(f"DEBUG: 使用默认孔位置: {counterbore_positions}")
    
    # 计算钻孔参数
    centering_depth = GCODE_GENERATION_CONFIG['drilling']['center_drill_depth']    # 点孔深度
    drilling_depth = counterbore_depth + (inner_diameter / 3) + GCODE_GENERATION_CONFIG['drilling']['drilling_depth_factor']  # 钻孔深度，确保贯通
    drill_feed = GCODE_GENERATION_CONFIG['drilling']['default_feed_rate']  # 钻孔进给
    counterbore_spindle_speed = GCODE_GENERATION_CONFIG['counterbore']['counterbore_spindle_speed']  # 锪孔时较低的转速
    counterbore_feed = GCODE_GENERATION_CONFIG['counterbore']['counterbore_feed_rate']  # 锪孔进给
    
    print(f"DEBUG: 最终提取的参数 - 外径: {outer_diameter}, 内径: {inner_diameter}, 深度: {counterbore_depth}, 孔数: {hole_count}, 位置数: {len(counterbore_positions)}")
    
    return (outer_diameter, inner_diameter, counterbore_depth, hole_count, counterbore_positions,
            centering_depth, drilling_depth, drill_feed, counterbore_spindle_speed, counterbore_feed)


def _generate_polar_coordinate_counterbore_code(
    gcode: List[str], 
    counterbore_positions: List[Tuple[float, float]], 
    outer_diameter: float, 
    inner_diameter: float, 
    counterbore_depth: float,
    centering_depth: float,
    drilling_depth: float,
    drill_feed: float,
    counterbore_spindle_speed: float,
    counterbore_feed: float
) -> bool:
    """生成极坐标系下的沉孔加工代码"""
    if not counterbore_positions:
        return False
    
    # 计算极坐标并输出
    gcode.append("(POLAR COORDINATE OUTPUT)")
    base_x, base_y = counterbore_positions[0]  # 选择第一个孔作为参考点
    gcode.append(f"(REFERENCE HOLE: X{base_x:.3f}, Y{base_y:.3f})")
    
    # 输出原始坐标作为验证
    gcode.append("(ORIGINAL CARTESIAN COORDINATES - FOR VERIFICATION)")
    for i, (x, y) in enumerate(counterbore_positions):
        gcode.append(f"(HOLE {i+1}: X{x:.3f}, Y{y:.3f})")
    
    # 添加调试输出，显示坐标转换过程
    gcode.append("(DEBUG: COORDINATE CONVERSION FROM CARTESIAN TO POLAR)")
    for i, (x, y) in enumerate(counterbore_positions):
        dx = x - base_x
        dy = y - base_y
        radius = math.sqrt(dx*dx + dy*dy)
        angle = math.degrees(math.atan2(dy, dx))
        gcode.append(f"(DEBUG: HOLE {i+1} - CARTESIAN({x:.3f}, {y:.3f}) -> RELATIVE({dx:.3f}, {dy:.3f}) -> POLAR(R{radius:.3f}, A{angle:.3f}°))")
    
    # 在加工循环中使用极坐标
    # 注意：在FANUC中，G16启用极坐标模式后，X表示半径，Y表示角度
    gcode.append("")
    gcode.append("(STEP 1: PILOT DRILLING OPERATION WITH POLAR COORDINATES)")
    gcode.append("(TOOL CHANGE - T01: CENTER DRILL)")
    gcode.append("T1 M06 (TOOL CHANGE - CENTER DRILL)")
    gcode.append("G54 (ENSURE WORK COORDINATE SYSTEM IS SELECTED)")
    gcode.append("G43 H1 Z100. (ACTIVATE TOOL LENGTH COMPENSATION FOR T1)")
    gcode.append("M03 S1000 (SPINDLE FORWARD, PILOT DRILLING SPEED)")
    gcode.append("G04 P1000 (DELAY 1 SECOND, WAIT FOR SPINDLE TO REACH SET SPEED)")
    gcode.append("M08 (COOLANT ON)")
    
    # 设置参考点
    gcode.append(f"G00 X{base_x:.3f} Y{base_y:.3f} (MOVE TO POLAR COORDINATE REFERENCE POINT)")
    # 启用极坐标模式
    gcode.append("G16 (ENTER POLAR COORDINATE MODE)")
    
    # 使用极坐标进行点孔加工 - X表示半径，Y表示角度
    for i, (x, y) in enumerate(counterbore_positions):
        # 计算相对于参考点的极坐标
        dx = x - base_x  # 计算相对于参考点的X偏移
        dy = y - base_y  # 计算相对于参考点的Y偏移
        radius = math.sqrt(dx*dx + dy*dy)  # 半径
        angle = math.degrees(math.atan2(dy, dx))  # 角度
        
        if i == 0:
            gcode.append(f"G82 X{radius:.3f} Y{angle:.3f} Z{-centering_depth:.3f} R{GCODE_GENERATION_CONFIG['safety']['approach_height']:.1f} P{GCODE_GENERATION_CONFIG['safety']['dwell_time']:.0f} F50.0 (SPOT DRILLING CYCLE, R{radius:.1f}, ANGLE{angle:.1f})")
        else:
            gcode.append(f"X{radius:.3f} Y{angle:.3f} (PILOT DRILLING {i+1}: R{radius:.1f}, ANGLE{angle:.1f})")
    
    gcode.append("G80 (CANCEL FIXED CYCLE)")
    gcode.append("M09 (COOLANT OFF)")
    gcode.append(f"G00 Z{GCODE_GENERATION_CONFIG['safety']['safe_height']:.1f} (RAPID MOVE TO UNIFIED SAFE HEIGHT)")
    gcode.append("G49 (CANCEL TOOL LENGTH COMPENSATION)")
    gcode.append("G15 (CANCEL POLAR COORDINATES)")
    
    # 2. 钻孔工艺使用极坐标
    gcode.append("")
    gcode.append("(STEP 2: DRILLING OPERATION WITH POLAR COORDINATES)")
    gcode.append(f"(TOOL CHANGE - T02: DRILL BIT, HOLE DIAMETER {inner_diameter}mm)")
    gcode.append("T2 M06 (TOOL CHANGE - DRILL BIT)")
    gcode.append("G54 (ENSURE WORK COORDINATE SYSTEM IS SELECTED)")
    gcode.append("G43 H2 Z100. (ACTIVATE TOOL LENGTH COMPENSATION FOR T2)")
    gcode.append("M03 S800 (SPINDLE FORWARD, DRILLING SPEED)")
    gcode.append("G04 P1000 (DELAY 1 SECOND, WAIT FOR SPINDLE TO REACH SET SPEED)")
    gcode.append("M08 (COOLANT ON)")
    
    # 重新启用极坐标模式（因为固定循环已被取消）
    gcode.append(f"G00 X{base_x:.3f} Y{base_y:.3f} (MOVE TO POLAR COORDINATE REFERENCE POINT)")
    gcode.append("G16 (ENTER POLAR COORDINATE MODE)")
    
    # 使用极坐标进行钻孔加工
    for i, (x, y) in enumerate(counterbore_positions):
        # 计算相对于参考点的极坐标
        dx = x - base_x  # 计算相对于参考点的X偏移
        dy = y - base_y  # 计算相对于参考点的Y偏移
        radius = math.sqrt(dx*dx + dy*dy)  # 半径
        angle = math.degrees(math.atan2(dy, dx))  # 角度
        
        if i == 0:
            gcode.append(f"G83 X{radius:.3f} Y{angle:.3f} Z{-drilling_depth:.3f} R2.0 Q1.0 F{drill_feed:.1f} (DEEP HOLE DRILLING CYCLE - R{radius:.1f}, ANGLE{angle:.1f}, φ{inner_diameter} THRU HOLE)")
        else:
            gcode.append(f"X{radius:.3f} Y{angle:.3f} (DRILLING {i+1}: R{radius:.1f}, ANGLE{angle:.1f} - φ{inner_diameter} THRU HOLE)")
    
    gcode.append("G80 (CANCEL FIXED CYCLE)")
    gcode.append("M09 (COOLANT OFF)")
    gcode.append("G00 Z100.0 (RAPID MOVE TO UNIFIED SAFE HEIGHT)")
    gcode.append("G49 (CANCEL TOOL LENGTH COMPENSATION)")
    gcode.append("G15 (CANCEL POLAR COORDINATES)")
    
    # 3. 锪孔工艺使用极坐标
    gcode.append("")
    gcode.append("(STEP 3: COUNTERBORE OPERATION WITH POLAR COORDINATES)")
    gcode.append(f"(TOOL CHANGE - T04: COUNTERBORE TOOL, φ{outer_diameter}mm)")
    gcode.append("T4 M06 (TOOL CHANGE - COUNTERBORE TOOL)")
    gcode.append("G54 (ENSURE WORK COORDINATE SYSTEM IS SELECTED)")
    gcode.append("G43 H4 Z100. (ACTIVATE TOOL LENGTH COMPENSATION FOR T4)")
    gcode.append(f"M03 S{int(counterbore_spindle_speed)} (SPINDLE FORWARD, COUNTERBORE SPEED)")
    gcode.append("G04 P1000 (DELAY 1 SECOND, WAIT FOR SPINDLE TO REACH SET SPEED)")
    gcode.append("M08 (COOLANT ON)")
    
    # 重新启用极坐标模式（因为固定循环已被取消）
    gcode.append(f"G00 X{base_x:.3f} Y{base_y:.3f} (MOVE TO POLAR COORDINATE REFERENCE POINT)")
    gcode.append("G16 (ENTER POLAR COORDINATE MODE)")
    
    # 使用极坐标进行锪孔加工
    for i, (x, y) in enumerate(counterbore_positions):
        # 计算相对于参考点的极坐标
        dx = x - base_x  # 计算相对于参考点的X偏移
        dy = y - base_y  # 计算相对于参考点的Y偏移
        radius = math.sqrt(dx*dx + dy*dy)  # 半径
        angle = math.degrees(math.atan2(dy, dx))  # 角度
        
        if i == 0:
            gcode.append(f"G81 X{radius:.3f} Y{angle:.3f} Z{-counterbore_depth:.3f} R2.0 F{counterbore_feed:.1f} (COUNTERBORE {i+1}: R{radius:.1f}, ANGLE{angle:.1f} - φ{outer_diameter} COUNTERBORE DEPTH {counterbore_depth}mm)")
        else:
            gcode.append(f"X{radius:.3f} Y{angle:.3f} (COUNTERBORE {i+1}: R{radius:.1f}, ANGLE{angle:.1f} - φ{outer_diameter} COUNTERBORE DEPTH {counterbore_depth}mm)")
    
    gcode.append("G80 (CANCEL FIXED CYCLE)")
    gcode.append("M09 (COOLANT OFF)")
    gcode.append(f"G00 Z100.0 (RAPID RETRACTION TO UNIFIED SAFE HEIGHT)")
    gcode.append("G49 (CANCEL TOOL LENGTH COMPENSATION)")
    gcode.append("M05 (SPINDLE STOP)")
    gcode.append("G15 (CANCEL POLAR COORDINATES)")
    
    gcode.append("")
    # 特别输出符合用户期望的极坐标格式（仅作为参考）
    gcode.append("(EXPECTED POLAR COORDINATE OUTPUT - FOR REFERENCE)")
    for i, (x, y) in enumerate(counterbore_positions):
        if i == 0:
            gcode.append(f"(CENTER REFERENCE: X{base_x:.1f}, Y{base_y:.1f})")
        else:
            dx = x - base_x
            dy = y - base_y
            radius = math.sqrt(dx*dx + dy*dy)
            angle = math.degrees(math.atan2(dy, dx))
            gcode.append(f"(POLAR POSITION: R{radius:.1f} ANGLE{angle:.1f})")
    gcode.append("")
    
    return True


def _generate_cartesian_counterbore_code(
    gcode: List[str], 
    counterbore_positions: List[Tuple[float, float]], 
    outer_diameter: float, 
    inner_diameter: float, 
    counterbore_depth: float,
    hole_count: int,
    centering_depth: float,
    drilling_depth: float,
    drill_feed: float,
    counterbore_spindle_speed: float,
    counterbore_feed: float,
    description_analysis: Dict
) -> None:
    """生成笛卡尔坐标系下的沉孔加工代码"""
    description = description_analysis.get("description", "").lower()
    
    # 添加加工统计信息
    if not counterbore_positions:
        if "沉孔" in description or "counterbore" in description or "锪孔" in description:
            gcode.append("(COUNTERBORE OPERATION - NO SPECIFIC POSITIONS DETECTED)")
            gcode.append("(USING EXAMPLE POSITION 50.0, 50.0 - MODIFY ACCORDING TO ACTUAL DRAWING)")
            gcode.append(f"(COUNTERBORE PROCESS - REQUESTED {hole_count} HOLES, USING {len(counterbore_positions)} EXAMPLE POSITIONS - MODIFY AS NEEDED)")
        else:
            gcode.append(f"(COUNTERBORE PROCESS - TOTAL {len(counterbore_positions)} HOLES)")
    else:
        gcode.append(f"(COUNTERBORE PROCESS - REQUESTED {hole_count} HOLES, DETECTED {len(counterbore_positions)} POSITIONS)")
    
    # 为每个位置添加标注
    for i, (x, y) in enumerate(counterbore_positions):
        gcode.append(f"(HOLE {i+1}: POSITION X{x:.3f} Y{y:.3f} - φ{outer_diameter if outer_diameter > 0 else 22.0} COUNTERBORE DEPTH {counterbore_depth}mm + φ{inner_diameter if inner_diameter > 0 else 14.5} THRU HOLE)")
    
    gcode.append("")
    
    # 1. 点孔工艺 (使用T1 - 中心钻)
    gcode.append("(STEP 1: PILOT DRILLING OPERATION)")
    gcode.append("(TOOL CHANGE - T01: CENTER DRILL)")
    gcode.append("T1 M06 (TOOL CHANGE - CENTER DRILL)")
    gcode.append("M03 S1000 (SPINDLE FORWARD, PILOT DRILLING SPEED)")
    gcode.append("G04 P1000 (DELAY 1 SECOND, WAIT FOR SPINDLE TO REACH SET SPEED)")
    
    # 激活刀具长度补偿
    gcode.append("G43 H1 Z100. (ACTIVATE TOOL LENGTH COMPENSATION FOR T1)")
    
    # 开启切削液
    gcode.append("M08 (COOLANT ON)")
    
    # 点孔循环
    if counterbore_positions:
        first_x, first_y = counterbore_positions[0]
        gcode.append(f"G82 X{first_x:.3f} Y{first_y:.3f} Z{-centering_depth:.3f} R2.0 P1000 F50.0 (SPOT DRILLING CYCLE, DWELL 1 SECOND)")
        
        # 对于后续孔位置，只使用X、Y坐标
        for i, (center_x, center_y) in enumerate(counterbore_positions[1:], 2):
            gcode.append(f"X{center_x:.3f} Y{center_y:.3f} (PILOT DRILLING {i}: X{center_x:.1f},Y{center_y:.1f})")
    else:
        gcode.append(f"G82 Z{-centering_depth:.3f} R2.0 P1000 F50.0 (SPOT DRILLING CYCLE, DWELL 1 SECOND)")
    
    gcode.append("G80 (CANCEL FIXED CYCLE)")
    
    # 关闭切削液
    gcode.append("M09 (COOLANT OFF)")
    
    # 移动到统一的安全高度，然后取消刀具长度补偿
    gcode.append("G00 Z100.0 (RAPID MOVE TO UNIFIED SAFE HEIGHT)")
    gcode.append("G49 (CANCEL TOOL LENGTH COMPENSATION)")
    
    # 2. 钻孔工艺 (使用T2 - φ14.5钻头)
    gcode.append("")
    gcode.append("(STEP 2: DRILLING OPERATION)")
    gcode.append(f"(TOOL CHANGE - T02: DRILL BIT, HOLE DIAMETER {inner_diameter}mm)")
    gcode.append("T2 M06 (TOOL CHANGE - DRILL BIT)")
    gcode.append("M03 S800 (SPINDLE FORWARD, DRILLING SPEED)")
    gcode.append("G04 P1000 (DELAY 1 SECOND, WAIT FOR SPINDLE TO REACH SET SPEED)")
    
    # 激活刀具长度补偿
    gcode.append("G43 H2 Z100. (ACTIVATE TOOL LENGTH COMPENSATION FOR T2)")
    
    # 开启切削液
    gcode.append("M08 (COOLANT ON)")
    
    # 钻孔循环
    if counterbore_positions:
        first_x, first_y = counterbore_positions[0]
        gcode.append(f"G83 X{first_x:.3f} Y{first_y:.3f} Z{-drilling_depth:.3f} R2.0 Q1.0 F{drill_feed:.1f} (DEEP HOLE DRILLING CYCLE - φ{inner_diameter} THRU HOLE)")
        
        # 对于后续孔位置，只使用X、Y坐标
        for i, (center_x, center_y) in enumerate(counterbore_positions[1:], 2):
            gcode.append(f"X{center_x:.3f} Y{center_y:.3f} (DRILLING {i}: X{center_x:.1f},Y{center_y:.1f} - φ{inner_diameter} THRU HOLE)")
    else:
        gcode.append(f"G83 Z{-drilling_depth:.3f} R2.0 Q1.0 F{drill_feed:.1f} (DEEP HOLE DRILLING CYCLE - φ{inner_diameter} THRU HOLE)")
    
    gcode.append("G80 (CANCEL FIXED CYCLE)")
    
    # 关闭切削液
    gcode.append("M09 (COOLANT OFF)")
    
    # 移动到统一的安全高度，然后取消刀具长度补偿
    gcode.append("G00 Z100.0 (RAPID MOVE TO UNIFIED SAFE HEIGHT)")
    gcode.append("G49 (CANCEL TOOL LENGTH COMPENSATION)")
    
    # 3. 锪孔工艺 (使用T4 - 锪孔刀)
    gcode.append("")
    gcode.append("(STEP 3: COUNTERBORE OPERATION)")
    gcode.append(f"(TOOL CHANGE - T04: COUNTERBORE TOOL, φ{outer_diameter}mm)")
    
    gcode.append("T4 M06 (TOOL CHANGE - COUNTERBORE TOOL)")
    gcode.append(f"M03 S{int(counterbore_spindle_speed)} (SPINDLE FORWARD, COUNTERBORE SPEED)")
    gcode.append("G04 P1000 (DELAY 1 SECOND, WAIT FOR SPINDLE TO REACH SET SPEED)")
    
    # 激活刀具长度补偿
    gcode.append("G43 H4 Z100. (ACTIVATE TOOL LENGTH COMPENSATION FOR T4)")
    
    # 开启切削液
    gcode.append("M08 (COOLANT ON)")
    
    # 锪孔循环
    if counterbore_positions:
        first_x, first_y = counterbore_positions[0]
        gcode.append(f"G81 X{first_x:.3f} Y{first_y:.3f} Z{-counterbore_depth:.3f} R2.0 F{counterbore_feed:.1f} (COUNTERBORE 1: X{first_x:.1f},Y{first_y:.1f} - φ{outer_diameter} COUNTERBORE DEPTH {counterbore_depth}mm)")
        
        # 对于后续孔位置，只使用X、Y坐标
        for i, (center_x, center_y) in enumerate(counterbore_positions[1:], 2):
            gcode.append(f"X{center_x:.3f} Y{center_y:.3f} (COUNTERBORE {i}: X{center_x:.1f},Y{center_y:.1f} - φ{outer_diameter} COUNTERBORE DEPTH {counterbore_depth}mm)")
    else:
        gcode.append(f"G81 Z{-counterbore_depth:.3f} R2.0 F{counterbore_feed:.1f} (COUNTERBORE CYCLE - φ{outer_diameter} COUNTERBORE DEPTH {counterbore_depth}mm)")
    
    gcode.append("G80 (CANCEL FIXED CYCLE)")
    
    # 关闭切削液
    gcode.append("M09 (COOLANT OFF)")
    
    # 加工完成后，移动到安全高度，然后取消刀具长度补偿
    gcode.append(f"G00 Z100.0 (RAPID RETRACTION TO UNIFIED SAFE HEIGHT)")
    gcode.append("G49 (CANCEL TOOL LENGTH COMPENSATION)")
    gcode.append("M05 (SPINDLE STOP)")


def _generate_counterbore_code(features: List[Dict], description_analysis: Dict) -> List[str]:
    """生成沉孔（Counterbore）加工代码 - 使用点孔、钻孔、锪孔工艺"""
    gcode = []
    
    # 提取沉孔参数
    (outer_diameter, inner_diameter, counterbore_depth, hole_count, counterbore_positions,
     centering_depth, drilling_depth, drill_feed, counterbore_spindle_speed, counterbore_feed) = _extract_counterbore_parameters(features, description_analysis)
    
    # 验证提取的参数
    if outer_diameter <= 0 or inner_diameter <= 0:
        print(f"ERROR: 无效的直径参数 - 外径: {outer_diameter}, 内径: {inner_diameter}")
        raise NCGenerationError(f"无效的直径参数 - 外径: {outer_diameter}, 内径: {inner_diameter}")
    
    if outer_diameter <= inner_diameter:
        print(f"ERROR: 外径应大于内径 - 外径: {outer_diameter}, 内径: {inner_diameter}")
        raise NCGenerationError(f"外径应大于内径 - 外径: {outer_diameter}, 内径: {inner_diameter}")
    
    if counterbore_depth <= 0:
        print(f"ERROR: 无效的沉孔深度: {counterbore_depth}")
        raise NCGenerationError(f"无效的沉孔深度: {counterbore_depth}")
    
    print(f"DEBUG: 验证通过 - 外径: {outer_diameter}, 内径: {inner_diameter}, 深度: {counterbore_depth}, 孔数: {hole_count}")
    
    # 检查是否需要使用极坐标 - 修复：更精确的判断逻辑
    description = description_analysis.get("description", "").lower()
    
    # 修复：当描述中包含"使用极坐标位置"时，应理解为使用指定的笛卡尔坐标作为极坐标参考点
    # 例如："使用极坐标位置X94.0 Y-30., X94.0 Y90., X94.0 Y210." 表示使用这些笛卡尔坐标进行极坐标加工
    use_polar_coordinates = False
    
    # 检查是否包含"使用极坐标位置"这样的明确指示
    if ("使用极坐标位置" in description or 
        "using polar coordinates at" in description or
        "polar coordinate position" in description):
        use_polar_coordinates = True
        gcode.append("(USER REQUESTED POLAR COORDINATE POSITIONING - PROCESSING CARTESIAN COORDINATES AS POLAR REFERENCE POINTS)")
    elif ("使用极坐标" in description or 
          "极坐标模式" in description or 
          "polar mode" in description or
          "polar coordinate" in description):
        # 当描述中明确提及"使用极坐标"等关键词时，优先考虑极坐标模式
        # 即使检测到笛卡尔坐标，如果同时有明确的极坐标指示，也应使用极坐标
        import re
        # 检查是否包含X数字Y数字格式的坐标
        cartesian_coord_pattern = r'X\s*\d+\.?\d*\s*Y\s*[+-]?\d+\.?\d*'
        cartesian_coords_found = re.findall(cartesian_coord_pattern, description_analysis.get("description", ""))
        
        # 检查是否包含极坐标相关的关键词
        has_polar_keyword = ("使用极坐标" in description or 
                            "极坐标模式" in description or 
                            "polar mode" in description or
                            "polar coordinate" in description)
        
        # 如果同时包含极坐标关键词和笛卡尔坐标，则使用极坐标模式
        if cartesian_coords_found and len(cartesian_coords_found) > 0 and has_polar_keyword:
            use_polar_coordinates = True
            gcode.append(f"(FOUND {len(cartesian_coords_found)} CARTESIAN COORDINATES AND POLAR KEYWORD - USING POLAR COORDINATE MODE)")
            for coord in cartesian_coords_found:
                gcode.append(f"(COORD: {coord})")
        elif cartesian_coords_found and len(cartesian_coords_found) > 0:
            # 如果只有笛卡尔坐标没有极坐标关键词，则使用笛卡尔坐标
            use_polar_coordinates = False
            gcode.append(f"(FOUND {len(cartesian_coords_found)} CARTESIAN COORDINATES IN DESCRIPTION - USING CARTESIAN MODE)")
            for coord in cartesian_coords_found:
                gcode.append(f"(COORD: {coord})")
        else:
            # 如果没有笛卡尔坐标但有极坐标关键词，则使用极坐标
            use_polar_coordinates = True
    
    # 如果用户明确要求使用极坐标，才使用极坐标模式
    if use_polar_coordinates and len(counterbore_positions) > 0:
        gcode.append("(USING POLAR COORDINATES FOR HOLE POSITIONS)")
        if _generate_polar_coordinate_counterbore_code(
            gcode, counterbore_positions, outer_diameter, inner_diameter, 
            counterbore_depth, centering_depth, drilling_depth, 
            drill_feed, counterbore_spindle_speed, counterbore_feed
        ):
            return gcode  # 如果生成了极坐标代码，则返回
    else:
        # 默认使用笛卡尔坐标系，这是大多数情况下的正确选择
        # 生成笛卡尔坐标代码
        _generate_cartesian_counterbore_code(
            gcode, counterbore_positions, outer_diameter, inner_diameter, 
            counterbore_depth, hole_count, centering_depth, drilling_depth, 
            drill_feed, counterbore_spindle_speed, counterbore_feed, 
            description_analysis
        )
    
    return gcode


def _generate_tapping_code_with_full_process(features: List[Dict], description_analysis: Dict) -> List[str]:
    """生成完整的螺纹孔加工代码 - 使用点孔、钻孔、攻丝3把刀的完整工艺"""
    gcode = []
    
    # 优先使用从描述分析中提取的螺纹规格信息
    description = description_analysis.get("description", "").lower()
    
    # 从描述分析中获取螺纹规格（如果存在）
    thread_size = description_analysis.get("thread_size", None)
    
    # 如果没有从描述分析中获取到螺纹规格，则根据描述中的关键词确定
    if thread_size is None:
        if "m3" in description:
            thread_size = "M3"
        elif "m4" in description:
            thread_size = "M4"
        elif "m5" in description:
            thread_size = "M5"
        elif "m6" in description:
            thread_size = "M6"
        elif "m8" in description:
            thread_size = "M8"
        elif "m10" in description:
            thread_size = "M10"
        elif "m12" in description:
            thread_size = "M12"
        else:
            thread_size = "M10"  # 默认
    
    # 根据螺纹规格确定钻孔尺寸
    thread_to_drill = {
        "M3": 2.5,
        "M4": 3.3,
        "M5": 4.2,
        "M6": 5.0,
        "M8": 6.8,
        "M10": 8.5,
        "M12": 10.2
    }
    
    drill_diameter = thread_to_drill.get(thread_size, 8.5)
    
    # 计算点孔、钻孔、攻丝的深度 - 优先使用描述分析中的深度
    centering_depth = 1    # 点孔深度
    # 根据用户要求：钻孔深度 = 螺纹深度 + 1/3底孔直径 + 1.5
    depth = description_analysis.get("depth")
    if depth is None or not isinstance(depth, (int, float)):
        depth = 14  # 默认深度
    else:
        depth = float(depth)
    drilling_depth = depth + (drill_diameter / 3) + 1.5  # 钻孔深度，确保丝锥不会因底孔太浅而折断
    tapping_depth = depth  # 攻丝深度
    
    # 获取孔位置信息：优先使用从图纸识别的特征，如果没有则使用从用户描述中提取的位置
    hole_positions = []
    for feature in features:
        if feature["shape"] == "circle":
            center_x, center_y = feature["center"]
            hole_positions.append((center_x, center_y))
    
    # 如果从图纸没有识别到圆形特征，尝试从用户描述中提取孔位置
    if not hole_positions:
        user_hole_positions = description_analysis.get("hole_positions", [])
        if user_hole_positions:
            hole_positions = user_hole_positions
    
    # 如果仍然没有孔位置，但用户要求加工螺纹孔，提供一个默认位置
    if not hole_positions:
        # 检查用户描述是否确实要求加工螺纹孔
        if "螺纹" in description or "thread" in description or "攻丝" in description or "tapping" in description:
            # 提供一个默认位置，同时在注释中说明这是示例位置
            hole_positions = [(50.0, 50.0)]  # 默认位置，用户可修改
            gcode.append("(THREADING OPERATION - NO SPECIFIC POSITIONS DETECTED)")
            gcode.append("(USING EXAMPLE POSITION 50.0, 50.0 - MODIFY ACCORDING TO ACTUAL DRAWING)")
            gcode.append(f"(THREADING PROCESS - TOTAL {len(hole_positions)} HOLE - EXAMPLE)")
            gcode.append("(HOLE 1: POSITION X50.000 Y50.000 - MODIFY TO ACTUAL POSITION)")
        else:
            gcode.append(f"(THREADING PROCESS - TOTAL {len(hole_positions)} HOLES)")
            for i, (x, y) in enumerate(hole_positions):
                gcode.append(f"(HOLE {i+1}: POSITION X{x:.3f} Y{y:.3f})")
    else:
        gcode.append(f"(THREADING PROCESS - TOTAL {len(hole_positions)} HOLES)")
        for i, (x, y) in enumerate(hole_positions):
            gcode.append(f"(HOLE {i+1}: POSITION X{x:.3f} Y{y:.3f})")
    
    gcode.append("")
    
    # 1. 点孔工艺 (使用T1 - 中心钻)
    gcode.append("(STEP 1: PILOT DRILLING OPERATION)")
    gcode.append("(TOOL CHANGE - T01: CENTER DRILL)")
    gcode.append("T1 M06 (TOOL CHANGE - CENTER DRILL)")
    gcode.append("M03 S1000 (SPINDLE FORWARD, PILOT DRILLING SPEED)")
    gcode.append("G04 P1000 (DELAY 1 SECOND, WAIT FOR SPINDLE TO REACH SET SPEED)")
    
    # 激活刀具长度补偿
    gcode.append("G43 H1 Z100. (ACTIVATE TOOL LENGTH COMPENSATION FOR T1)")
    
    # 开启切削液
    gcode.append("M08 (COOLANT ON)")
    
    # 点孔循环 - 首先在第一个孔位置执行完整循环
    if hole_positions:
        first_x, first_y = hole_positions[0]
        gcode.append(f"G82 X{first_x:.3f} Y{first_y:.3f} Z{-centering_depth:.3f} R2.0 P1000 F50.0 (SPOT DRILLING CYCLE, DWELL 1 SECOND)")
        
        # 对于后续孔位置，只使用X、Y坐标，简化编程
        for i, (center_x, center_y) in enumerate(hole_positions[1:], 2):
            gcode.append(f"X{center_x:.3f} Y{center_y:.3f} (PILOT DRILLING {i}: X{center_x:.1f},Y{center_y:.1f})")
    else:
        # 如果没有孔位置，仍保留原始循环指令
        gcode.append(f"G82 Z{-centering_depth:.3f} R2.0 P1000 F50.0 (SPOT DRILLING CYCLE, DWELL 1 SECOND)")
    
    gcode.append("G80 (CANCEL FIXED CYCLE)")
    
    # 关闭切削液
    gcode.append("M09 (COOLANT OFF)")
    
    # 移动到统一的安全高度，然后取消刀具长度补偿
    gcode.append("G00 Z100.0 (RAPID MOVE TO UNIFIED SAFE HEIGHT)")
    gcode.append("G49 (CANCEL TOOL LENGTH COMPENSATION)")
    
    # 2. 钻孔工艺 (使用T2 - 钻头)
    gcode.append("")
    gcode.append("(STEP 2: DRILLING OPERATION)")
    gcode.append(f"(TOOL CHANGE - T02: DRILL BIT, HOLE DIAMETER {drill_diameter}mm)")
    gcode.append("T2 M06 (TOOL CHANGE - DRILL BIT)")
    gcode.append("M03 S800 (SPINDLE FORWARD, DRILLING SPEED)")
    gcode.append("G04 P1000 (DELAY 1 SECOND, WAIT FOR SPINDLE TO REACH SET SPEED)")
    
    # 激活刀具长度补偿
    gcode.append("G43 H2 Z100. (ACTIVATE TOOL LENGTH COMPENSATION FOR T2)")
    
    # 开启切削液
    gcode.append("M08 (COOLANT ON)")
    
    # 钻孔循环 - 首先在第一个孔位置执行完整循环
    # 优先使用描述分析中的进给率
    drill_feed = description_analysis.get("feed_rate")
    if drill_feed is None or not isinstance(drill_feed, (int, float)):
        drill_feed = 100  # 默认钻孔进给
    else:
        drill_feed = float(drill_feed)
    
    if hole_positions:
        first_x, first_y = hole_positions[0]
        gcode.append(f"G83 X{first_x:.3f} Y{first_y:.3f} Z{-drilling_depth:.3f} R2.0 Q1.0 F{drill_feed:.1f} (DEEP HOLE DRILLING CYCLE)")
        
        # 对于后续孔位置，只使用X、Y坐标，简化编程
        for i, (center_x, center_y) in enumerate(hole_positions[1:], 2):
            gcode.append(f"X{center_x:.3f} Y{center_y:.3f} (DRILLING {i}: X{center_x:.1f},Y{center_y:.1f})")
    else:
        # 如果没有孔位置，仍保留原始循环指令
        gcode.append(f"G83 Z{-drilling_depth:.3f} R2.0 Q1.0 F{drill_feed:.1f} (DEEP HOLE DRILLING CYCLE)")
    
    gcode.append("G80 (CANCEL FIXED CYCLE)")
    
    # 关闭切削液
    gcode.append("M09 (COOLANT OFF)")
    
    # 移动到统一的安全高度，然后取消刀具长度补偿
    gcode.append("G00 Z100.0 (RAPID MOVE TO UNIFIED SAFE HEIGHT)")
    gcode.append("G49 (CANCEL TOOL LENGTH COMPENSATION)")
    
    # 3. 攻丝工艺 (使用T3 - 丝锥)
    gcode.append("")
    gcode.append("(STEP 3: TAPPING OPERATION)")
    gcode.append("(TOOL CHANGE - T03: TAP)")
    
    # 获取攻丝参数 - 优先使用描述分析中的参数
    tapping_spindle_speed = description_analysis.get("spindle_speed")
    if tapping_spindle_speed is None or not isinstance(tapping_spindle_speed, (int, float)):
        tapping_spindle_speed = 300  # 攻丝时较低的转速
    else:
        tapping_spindle_speed = float(tapping_spindle_speed)
    
    # 根据螺纹规格计算攻丝进给 (进给 = 转速 * 螺距)
    thread_pitch_map = {
        "M3": 0.5,   # M3螺纹螺距 (粗牙)
        "M4": 0.7,   # M4螺纹螺距 (粗牙)
        "M5": 0.8,   # M5螺纹螺距 (粗牙)
        "M6": 1.0,   # M6螺纹螺距 (粗牙)
        "M8": 1.25,  # M8螺纹螺距 (粗牙)
        "M10": 1.5,  # M10螺纹螺距 (粗牙)
        "M12": 1.75  # M12螺纹螺距 (粗牙)
    }
    
    thread_pitch = thread_pitch_map.get(thread_size, 1.5)  # 默认M10螺纹螺距
    tapping_feed = tapping_spindle_speed * thread_pitch  # F = S * 螺距 (mm/rev)，不需要除以60
    # 确保攻丝进给率不低于1，避免系统报错
    tapping_feed = max(tapping_feed, 1.0)
    
    gcode.append(f"T3 M06 (TOOL CHANGE - TAP)")
    gcode.append(f"M03 S{int(tapping_spindle_speed)} (SPINDLE FORWARD, TAPPING SPEED)")
    gcode.append("G04 P1000 (DELAY 1 SECOND, WAIT FOR SPINDLE TO REACH SET SPEED)")
    
    # 激活刀具长度补偿
    gcode.append("G43 H3 Z100. (ACTIVATE TOOL LENGTH COMPENSATION FOR T3)")
    
    # 开启切削液
    gcode.append("M08 (COOLANT ON)")
    
    # 攻丝循环 - 首先在第一个孔位置执行完整循环
    if hole_positions:
        first_x, first_y = hole_positions[0]
        gcode.append(f"G84 X{first_x:.3f} Y{first_y:.3f} Z{-tapping_depth:.3f} R2.0 F{tapping_feed:.1f} (TAPPING 1: X{first_x:.1f},Y{first_y:.1f} - {thread_size} THREAD)")
        
        # 对于后续孔位置，只使用X、Y坐标，简化编程
        for i, (center_x, center_y) in enumerate(hole_positions[1:], 2):
            gcode.append(f"X{center_x:.3f} Y{center_y:.3f} (TAPPING {i}: X{center_x:.1f},Y{center_y:.1f} - {thread_size} THREAD)")
    else:
        # 如果没有孔位置，仍保留原始循环指令
        gcode.append(f"G84 Z{-tapping_depth:.3f} R2.0 F{tapping_feed:.1f} (TAPPING CYCLE - NO SPECIFIC POSITION)")
    
    gcode.append("G80 (CANCEL FIXED CYCLE)")
    
    # 关闭切削液
    gcode.append("M09 (COOLANT OFF)")
    
    # 攻丝后主轴反转退刀
    gcode.append(f"M04 S{int(tapping_spindle_speed)} (SPINDLE REVERSE, PREPARE FOR RETRACTION)")
    # 移动到统一的安全高度，然后取消刀具长度补偿
    gcode.append(f"G00 Z100.0 (RAPID RETRACTION TO UNIFIED SAFE HEIGHT)")
    gcode.append("G49 (CANCEL TOOL LENGTH COMPENSATION)")
    gcode.append("M05 (SPINDLE STOP)")
    
    return gcode


def _generate_milling_code(features: List[Dict], description_analysis: Dict) -> List[str]:
    """生成铣削加工代码"""
    gcode = []
    
    # 获取材料信息，默认为铝
    material = "aluminum"  # 默认值
    if description_analysis:
        material = description_analysis.get("material", "aluminum")
        if material is None:
            material = "aluminum"
        else:
            material = str(material).lower()
    else:
        material = "aluminum"
    
    # 获取刀具直径，优先从描述分析中获取
    tool_diameter = 63.0  # 默认使用φ63面铣刀
    if description_analysis:
        temp_diameter = description_analysis.get("tool_diameter", 63.0)
        if temp_diameter is not None:
            tool_diameter = float(temp_diameter)
        else:
            tool_diameter = 63.0
    
    # 获取工件尺寸信息，用于优化切削参数
    workpiece_dimensions = None
    if description_analysis:
        workpiece_dimensions = description_analysis.get("workpiece_dimensions", None)
    
    # 使用切削工艺优化器计算最优参数
    try:
        optimal_params = cutting_optimizer.calculate_optimal_cutting_parameters(
            material=material,
            tool_type="face_mill",  # 面铣刀
            tool_diameter=tool_diameter,
            workpiece_dimensions=workpiece_dimensions,
            operation_type="face_milling"
        )
        
        # 应用优化后的参数
        spindle_speed = optimal_params["spindle_speed"]
        feed_rate = optimal_params["feed_rate"]
        depth_of_cut = optimal_params["depth_of_cut"]
        stepover = optimal_params["stepover"]
        
        # 验证优化参数
        validation_errors = cutting_optimizer.validate_cutting_parameters(
            optimal_params, tool_diameter, workpiece_dimensions
        )
        if validation_errors:
            gcode.append(f"(WARNING: OPTIMIZATION ISSUES DETECTED: {', '.join(validation_errors)})")
            # 仍然使用优化参数，但添加警告注释
    except Exception as e:
        # 如果优化失败，使用默认参数
        gcode.append(f"(WARNING: Optimization failed, using default parameters: {str(e)})")
        depth = description_analysis.get("depth")
        if depth is None or not isinstance(depth, (int, float)):
            depth = 2  # 铣削上平面深度2毫米
        else:
            depth = float(depth)
        
        feed_rate = description_analysis.get("feed_rate")
        if feed_rate is None or not isinstance(feed_rate, (int, float)):
            feed_rate = 500  # 默认值
        else:
            feed_rate = float(feed_rate)
        
        spindle_speed = description_analysis.get("spindle_speed")
        if spindle_speed is None or not isinstance(spindle_speed, (int, float)):
            spindle_speed = 800  # 默认值
        else:
            spindle_speed = float(spindle_speed)
    
    # 获取刀具编号（铣刀通常是T4）
    tool_number = _get_tool_number("end_mill")
    
    # 主轴启动
    gcode.append(f"M03 S{int(spindle_speed)} (SPINDLE FORWARD, MILLING SPEED)")
    gcode.append("G04 P1000 (DELAY 1 SECOND, WAIT FOR SPINDLE TO REACH SET SPEED)")
    
    # 激活刀具长度补偿
    gcode.append(f"G43 H{tool_number} Z100. (ACTIVATE TOOL LENGTH COMPENSATION FOR T{tool_number:02})")
    
    # 开启切削液
    gcode.append("M08 (COOLANT ON)")
    
    # 为每个特征生成铣削代码
    for feature in features:
        gcode.append("")
        gcode.append(f"(MILLING OPERATION - {feature['shape'].upper()})")
        
        if feature["shape"] == "rectangle" and len(feature["dimensions"]) >= 2:
            # 矩形面铣削 - 考虑刀具直径和工件尺寸
            center_x, center_y = feature["center"]
            length, width = feature["dimensions"]
            
            # 使用优化器生成优化的刀具路径
            toolpath = cutting_optimizer.optimize_toolpath(
                feature_type="rectangle",
                feature_dimensions=(length, width),
                tool_diameter=tool_diameter,
                workpiece_dimensions=workpiece_dimensions or (length, width, 10)  # 假设高度
            )
            
            if toolpath:
                # 根据优化路径生成G代码
                for i, path_segment in enumerate(toolpath):
                    if path_segment["type"] == "linear":
                        start = path_segment["start"]
                        end = path_segment["end"]
                        
                        # 移动到起始位置
                        gcode.append(f"G00 X{center_x + start[0]:.3f} Y{center_y + start[1]:.3f} (MOVE TO MILLING START POINT {i+1})")
                        
                        # 下刀
                        gcode.append(f"G01 Z{-depth_of_cut:.3f} F{feed_rate/2:.1f} (INITIAL CUTTING)")
                        
                        # 铣削直线段
                        gcode.append(f"G01 X{center_x + end[0]:.3f} Y{center_y + end[1]:.3f} F{feed_rate} (MILLING PASS)")
                        
                        # 抬刀到安全高度
                        gcode.append(f"G00 Z{GCODE_GENERATION_CONFIG['safety']['safe_height']:.1f} (RAISE TOOL TO SAFE HEIGHT)")
            else:
                # 如果没有优化路径，使用传统方法
                # 确保铣削范围不超过工件尺寸
                half_length = min(length / 2, 200)  # 限制在400mm长度内
                half_width = min(width / 2, 150)   # 限制在300mm宽度内
                
                # 生成螺旋或往复铣削路径
                start_x = center_x - half_length + (tool_diameter / 2)
                start_y = center_y - half_width + (tool_diameter / 2)
                
                gcode.append(f"G00 X{start_x:.3f} Y{start_y:.3f} (MOVE TO MILLING START POINT)")
                gcode.append(f"G01 Z{-depth_of_cut:.3f} F{feed_rate/2:.1f} (INITIAL CUTTING)")
                
                # 生成往复铣削路径
                y_pos = start_y
                direction = 1  # 1为正向，-1为反向
                stepover = min(stepover, 5)  # 限制步距
                
                while y_pos <= center_y + half_width - (tool_diameter / 2):
                    # X方向移动
                    if direction == 1:
                        end_x = center_x + half_length - (tool_diameter / 2)
                    else:
                        end_x = center_x - half_length + (tool_diameter / 2)
                    
                    gcode.append(f"G01 X{end_x:.3f} Y{y_pos:.3f} F{feed_rate} (MILLING PASS)")
                    
                    # 移动到下一个Y位置
                    if y_pos + stepover <= center_y + half_width - (tool_diameter / 2):
                        y_pos += stepover
                        direction *= -1  # 反向
                        gcode.append(f"G01 Y{y_pos:.3f} F{feed_rate/2:.1f} (STEPOVER TO NEXT PASS)")
                    else:
                        break
        
        elif feature["shape"] == "circle":
            # 圆形铣削
            center_x, center_y = feature["center"]
            radius = feature.get("radius", 10)
            
            # 快速移动到圆的起始点
            start_x = center_x - radius
            gcode.append(f"G00 X{start_x:.3f} Y{center_y:.3f} (MOVE TO CIRCULAR ARC START POINT)")
            gcode.append(f"G01 Z{-depth_of_cut:.3f} F{feed_rate/2:.1f} (INITIAL CUTTING)")
            gcode.append(f"G02 X{start_x:.3f} Y{center_y:.3f} I{radius:.3f} J0 F{feed_rate} (CLOCKWISE CIRCULAR MILLING)")
            
            # 如果需要更深的加工，进行第二次切削
            gcode.append(f"G01 Z{-depth_of_cut*2:.3f} F{feed_rate/2:.1f} (CONTINUE CUTTING)")
            gcode.append(f"G02 X{start_x:.3f} Y{center_y:.3f} I{radius:.3f} J0 F{feed_rate} (CLOCKWISE CIRCULAR MILLING)")
            
        elif feature["shape"] == "triangle":
            # 三角形铣削
            vertices = feature.get("vertices", [])
            if len(vertices) >= 3:
                start_x, start_y = vertices[0]
                gcode.append(f"G00 X{start_x:.3f} Y{start_y:.3f} (MOVE TO TRIANGLE START POINT)")
                gcode.append(f"G01 Z{-depth_of_cut:.3f} F{feed_rate/2:.1f} (INITIAL CUTTING)")
                
                for i in range(1, len(vertices)):
                    x, y = vertices[i]
                    gcode.append(f"G01 X{x:.3f} Y{y:.3f} F{feed_rate} (MILL TRIANGLE EDGE)")
                
                # 闭合三角形
                x, y = vertices[0]
                gcode.append(f"G01 X{x:.3f} Y{y:.3f} (CLOSE TRIANGLE)")
    
    # 关闭切削液
    gcode.append("M09 (COOLANT OFF)")
    
    # 移动到统一的安全高度，然后取消刀具长度补偿
    gcode.append("G00 Z100.0 (RAPID MOVE TO UNIFIED SAFE HEIGHT)")
    gcode.append("G49 (CANCEL TOOL LENGTH COMPENSATION)")
    
    return gcode


def _generate_turning_code(features: List[Dict], description_analysis: Dict) -> List[str]:
    """生成车削加工代码"""
    gcode = []
    
    # 设置车削参数 - 优先使用从用户描述中提取的参数
    depth = description_analysis.get("depth")
    if depth is None or not isinstance(depth, (int, float)):
        depth = 2  # 默认值
    else:
        depth = float(depth)
    
    feed_rate = description_analysis.get("feed_rate")
    if feed_rate is None or not isinstance(feed_rate, (int, float)):
        feed_rate = 100  # 默认值
    else:
        feed_rate = float(feed_rate)
    
    spindle_speed = description_analysis.get("spindle_speed")
    if spindle_speed is None or not isinstance(spindle_speed, (int, float)):
        spindle_speed = 800  # 默认值
    else:
        spindle_speed = float(spindle_speed)
    
    # 获取刀具编号（车刀通常是T5）
    tool_number = _get_tool_number("cutting_tool")
    
    gcode.append(f"M03 S{int(spindle_speed)} (SET SPINDLE SPEED)")
    
    # 激活刀具长度补偿
    gcode.append(f"G43 H{tool_number} Z100. (ACTIVATE TOOL LENGTH COMPENSATION FOR T{tool_number:02})")
    
    # 开启切削液
    gcode.append("M08 (COOLANT ON)")
    
    # 为每个特征生成车削代码
    for feature in features:
        gcode.append("")
        gcode.append(f"(TURNING OPERATION - {feature['shape'].upper()})")
        
        if feature["shape"] in ["rectangle", "square"]:
            # 假设矩形表示需要车削的外径
            _, _, width, height = feature["bounding_box"]
            diameter = max(width, height)  # 假设最大尺寸为直径
            
            # 粗车循环 (G71)
            gcode.append(f"G71 U2 R1 (ROUGH TURNING CYCLE, 2MM DEPTH PER PASS)")
            gcode.append(f"G71 P10 Q20 U{diameter/10:.3f} W0.5 F{feed_rate/2} (ROUGH EXTERNAL DIAMETER)")
            gcode.append("N10 G00 X0.0 Z0.0")
            gcode.append(f"N20 G01 X{diameter:.3f} Z0.0 F{feed_rate/2}")
            
            # 精车循环 (G70)
            gcode.append("G70 P10 Q20 (FINISHING CYCLE)")
    
    # 关闭切削液
    gcode.append("M09 (COOLANT OFF)")
    
    # 移动到足够高的安全位置（高于刀具补偿值），然后取消刀具长度补偿
    gcode.append("G00 Z105 (RAPID MOVE TO SAFE HEIGHT - ABOVE TOOL COMPENSATION VALUE)")
    gcode.append("G49 (CANCEL TOOL LENGTH COMPENSATION)")
    gcode.append("G00 Z50 (RAPID MOVE TO INTERMEDIATE SAFE HEIGHT)")
    
    return gcode


def validate_nc_code(nc_code: str) -> List[str]:
    """
    验证生成的NC代码的有效性
    
    Args:
        nc_code (str): 生成的NC代码
    
    Returns:
        list: 验证错误列表，如果无错误则返回空列表
    """
    errors = []
    
    # 检查输入是否为字符串
    if not isinstance(nc_code, str):
        errors.append("NC代码必须是字符串类型")
        return errors
    
    lines = nc_code.split('\n')
    
    # 检查是否存在必要的G代码指令
    has_program_end = any('M30' in line or 'M02' in line for line in lines)
    if not has_program_end:
        errors.append("缺少程序结束指令 (M30 或 M02)")
    
    has_units = any('G21' in line or 'G20' in line for line in lines)
    if not has_units:
        errors.append("缺少单位设定指令 (G21 或 G20)")
    
    has_coordinate_mode = any('G90' in line or 'G91' in line for line in lines)
    if not has_coordinate_mode:
        errors.append("缺少坐标模式设定指令 (G90 或 G91)")
    
    return errors


def _validate_feature(feature: Dict) -> List[str]:
    """
    验证单个特征的有效性
    
    Args:
        feature (dict): 几何特征字典
    
    Returns:
        list: 验证错误列表
    """
    errors = []
    
    if not isinstance(feature, dict):
        errors.append("特征必须是字典类型")
        return errors
    
    # 验证必需的键
    required_keys = ['shape', 'center', 'dimensions']
    for key in required_keys:
        if key not in feature:
            errors.append(f"特征缺少必需的键: {key}")
    
    # 验证shape值
    valid_shapes = ['circle', 'rectangle', 'square', 'triangle', 'counterbore', 'ellipse', 'polygon']
    if feature.get('shape') not in valid_shapes:
        errors.append(f"无效的形状类型: {feature.get('shape')}")
    
    # 验证center
    center = feature.get('center')
    if center is not None:
        if not isinstance(center, (list, tuple)) or len(center) != 2:
            errors.append("中心点必须是包含两个元素的列表或元组")
        else:
            for coord in center:
                if not isinstance(coord, (int, float)):
                    errors.append("中心点坐标必须是数字")
                    break
    
    # 验证dimensions
    dimensions = feature.get('dimensions')
    if dimensions is not None:
        if not isinstance(dimensions, (list, tuple)):
            errors.append("尺寸必须是列表或元组")
        else:
            for dim in dimensions:
                if not isinstance(dim, (int, float)) or dim <= 0:
                    errors.append("尺寸值必须是正数")
                    break
    
    return errors