"""
FANUC NC程序生成模块
根据识别的特征和用户描述生成符合FANUC标准的G代码
"""
from typing import List, Dict, Optional, Union
import math
import datetime

# 导入配置参数
from ..config import GCODE_GENERATION_CONFIG, THREAD_PITCH_MAP

# 导入优化模块
try:
    from .fanuc_optimization import optimize_tapping_cycle, optimize_drilling_cycle, get_thread_pitch
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
    """
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
    gcode.append("(ORIGIN (0,0) LOCATED AT TOP-LEFT OF WORKPIECE (G54))")
    gcode.append("(Y AXIS POSITIVE DIRECTION DOWNWARD, X AXIS POSITIVE RIGHTWARD)")
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
        gcode.append("G91 (INCREMENTAL COORDINATE SYSTEM)")
        gcode.append("G28 Z0. (RETURN TO Z ORIGIN THROUGH REFERENCE POINT)")
        gcode.append("G28 X0. Y0. (RETURN TO X,Y ORIGIN THROUGH REFERENCE POINT)")
        gcode.append("G90 (ABSOLUTE COORDINATE SYSTEM)")
        gcode.append("M30 (PROGRAM END)")
    elif processing_type == "tapping":  # 新增攻丝工艺
        gcode.extend(_generate_tapping_code_with_full_process(features, description_analysis))
        # 攻丝工艺完成后，添加程序结束指令
        gcode.append("")
        gcode.append("(PROGRAM END)")
        gcode.append("M05 (SPINDLE STOP)")
        gcode.append("G00 Z100.0 (RAISE TOOL TO SAFE HEIGHT)")
        gcode.append("G91 (INCREMENTAL COORDINATE SYSTEM)")
        gcode.append("G28 Z0. (RETURN TO Z ORIGIN THROUGH REFERENCE POINT)")
        gcode.append("G28 X0. Y0. (RETURN TO X,Y ORIGIN THROUGH REFERENCE POINT)")
        gcode.append("G90 (ABSOLUTE COORDINATE SYSTEM)")
        gcode.append("M30 (PROGRAM END)")
    elif processing_type == "milling":
        gcode.extend(_generate_milling_code(features, description_analysis))
        # 添加程序结束
        gcode.append("")
        gcode.append("(PROGRAM END)")
        gcode.append("M05 (SPINDLE STOP)")
        gcode.append("G00 Z100.0 (RAISE TOOL TO SAFE HEIGHT)")
        gcode.append("G91 (INCREMENTAL COORDINATE SYSTEM)")
        gcode.append("G28 Z0. (RETURN TO Z ORIGIN THROUGH REFERENCE POINT)")
        gcode.append("G28 X0. Y0. (RETURN TO X,Y ORIGIN THROUGH REFERENCE POINT)")
        gcode.append("G90 (ABSOLUTE COORDINATE SYSTEM)")
        gcode.append("M30 (PROGRAM END)")
    elif processing_type == "counterbore":  # 新增沉孔加工工艺
        gcode.extend(_generate_counterbore_code(features, description_analysis))
        # 添加程序结束
        gcode.append("")
        gcode.append("(PROGRAM END)")
        gcode.append("M05 (SPINDLE STOP)")
        gcode.append("G00 Z100.0 (RAISE TOOL TO SAFE HEIGHT)")
        gcode.append("G91 (INCREMENTAL COORDINATE SYSTEM)")
        gcode.append("G28 Z0. (RETURN TO Z ORIGIN THROUGH REFERENCE POINT)")
        gcode.append("G28 X0. Y0. (RETURN TO X,Y ORIGIN THROUGH REFERENCE POINT)")
        gcode.append("G90 (ABSOLUTE COORDINATE SYSTEM)")
        gcode.append("M30 (PROGRAM END)")
    elif processing_type == "turning":
        gcode.extend(_generate_turning_code(features, description_analysis))
        # 添加程序结束
        gcode.append("")
        gcode.append("(PROGRAM END)")
        gcode.append("M05 (SPINDLE STOP)")
        gcode.append("G00 Z100.0 (RAISE TOOL TO SAFE HEIGHT)")
        gcode.append("G91 (INCREMENTAL COORDINATE SYSTEM)")
        gcode.append("G28 Z0. (RETURN TO Z ORIGIN THROUGH REFERENCE POINT)")
        gcode.append("G28 X0. Y0. (RETURN TO X,Y ORIGIN THROUGH REFERENCE POINT)")
        gcode.append("G90 (ABSOLUTE COORDINATE SYSTEM)")
        gcode.append("M30 (PROGRAM END)")
    else:
        description = description_analysis.get("description", "").lower()
        # 检查用户描述中是否包含沉孔相关关键词
        if "沉孔" in description or "counterbore" in description or "锪孔" in description:
            gcode.extend(_generate_counterbore_code(features, description_analysis))
            # 沉孔加工完成后，添加程序结束指令
            gcode.append("")
            gcode.append("(PROGRAM END)")
            gcode.append("M05 (SPINDLE STOP)")
            gcode.append("G00 Z100.0 (RAISE TOOL TO SAFE HEIGHT)")
            gcode.append("G00 X0.0 Y0.0 (RETURN TO ORIGIN)")
            gcode.append("G00 Z0.0 (RETURN Z-AXIS TO ORIGIN)")
            gcode.append("M30 (PROGRAM END)")
        # 检查用户描述中是否包含螺纹相关关键词
        elif "螺纹" in description or "thread" in description or "tapping" in description:
            gcode.extend(_generate_tapping_code_with_full_process(features, description_analysis))
            # 攻丝工艺完成后，添加程序结束指令
            gcode.append("")
            gcode.append("(PROGRAM END)")
            gcode.append("M05 (SPINDLE STOP)")
            gcode.append("G00 Z100.0 (RAISE TOOL TO SAFE HEIGHT)")
            gcode.append("G00 X0.0 Y0.0 (RETURN TO ORIGIN)")
            gcode.append("G00 Z0.0 (RETURN Z-AXIS TO ORIGIN)")
            gcode.append("M30 (PROGRAM END)")
        else:
            # 默认使用铣削代码
            gcode.extend(_generate_milling_code(features, description_analysis))
            # 添加程序结束
            gcode.append("")
            gcode.append("(PROGRAM END)")
            gcode.append("M05 (SPINDLE STOP)")
            gcode.append("G00 Z100 (RAISE TOOL TO SAFE HEIGHT)")
            gcode.append("G00 X0.0 Y0.0 (RETURN TO ORIGIN)")
            gcode.append("G00 Z0 (RETURN Z-AXIS TO ORIGIN)")
            gcode.append("M30 (PROGRAM END)")

    return "\n".join(gcode)


def _get_tool_number(tool_type: str) -> int:
    """根据刀具类型返回刀具编号"""
    # 使用配置中的刀具映射
    from ..config import TOOL_MAPPING
    return TOOL_MAPPING.get(tool_type, 5)


def _generate_drilling_code(features: List[Dict], description_analysis: Dict) -> List[str]:
    """生成钻孔加工代码"""
    gcode = []
    
    # 设置钻孔循环参数 - 安全处理None值
    depth = description_analysis.get("depth")
    if depth is None or not isinstance(depth, (int, float)):
        depth = GCODE_GENERATION_CONFIG['drilling']['default_depth']  # 使用配置中的默认值
    else:
        depth = float(depth)
    
    feed_rate = description_analysis.get("feed_rate")
    if feed_rate is None or not isinstance(feed_rate, (int, float)):
        feed_rate = GCODE_GENERATION_CONFIG['drilling']['default_feed_rate']  # 使用配置中的默认值
    else:
        feed_rate = float(feed_rate)
    
    # 获取刀具编号（钻头通常是T2）
    tool_number = _get_tool_number("drill_bit")
    
    gcode.append(f"(DRILLING OPERATION)")
    gcode.append(f"M03 S{GCODE_GENERATION_CONFIG['drilling']['default_spindle_speed']} (SPINDLE FORWARD, DRILLING SPEED)")
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
        gcode.append(f"G99 G83 X{center_x:.3f} Y{center_y:.3f} Z{-depth:.3f} R2.0 F{feed_rate:.1f} (DEEP HOLE DRILLING CYCLE)")
        
        # 对于后续孔，只使用X、Y坐标，简化编程
        for feature in hole_features[1:]:
            center_x, center_y = feature["center"]
            gcode.append(f"X{center_x:.3f} Y{center_y:.3f} (DRILLING OPERATION)")
    else:
        gcode.append(f"G99 G83 Z{-depth:.3f} R2.0 F{feed_rate:.1f} (DEEP HOLE DRILLING CYCLE)")
    
    gcode.append("G80 (CANCEL FIXED CYCLE)")
    
    # 关闭切削液
    gcode.append("M09 (COOLANT OFF)")
    
    # 移动到统一的安全高度，然后取消刀具长度补偿
    gcode.append("G00 Z100.0 (RAPID MOVE TO UNIFIED SAFE HEIGHT)")
    gcode.append("G49 (CANCEL TOOL LENGTH COMPENSATION)")
    
    return gcode


def _generate_counterbore_code(features: List[Dict], description_analysis: Dict) -> List[str]:
    """生成沉孔（Counterbore）加工代码 - 使用点孔、钻孔、锪孔工艺"""
    gcode = []
    
    # 从特征和描述中提取沉孔参数
    # 默认参数
    outer_diameter = GCODE_GENERATION_CONFIG['counterbore']['default_outer_diameter']  # 沉孔直径
    inner_diameter = GCODE_GENERATION_CONFIG['counterbore']['default_inner_diameter']  # 底孔直径
    counterbore_depth = GCODE_GENERATION_CONFIG['counterbore']['default_depth']  # 沉孔深度
    
    # 优先从描述分析中提取直径信息（最高优先级）
    if "outer_diameter" in description_analysis and description_analysis["outer_diameter"] is not None:
        outer_diameter = description_analysis["outer_diameter"]
    if "inner_diameter" in description_analysis and description_analysis["inner_diameter"] is not None:
        inner_diameter = description_analysis["inner_diameter"]
    
    # 从沉孔特征中提取实际参数（次优先级）
    counterbore_features = [f for f in features if f.get("shape") == "counterbore"]
    if counterbore_features:
        # 使用第一个沉孔特征的参数，但只有在描述分析中没有提供时才使用
        first_counterbore = counterbore_features[0]
        if outer_diameter == GCODE_GENERATION_CONFIG['counterbore']['default_outer_diameter']:  # 如果还是默认值
            outer_diameter = first_counterbore.get("outer_diameter", outer_diameter)
        if inner_diameter == GCODE_GENERATION_CONFIG['counterbore']['default_inner_diameter']:  # 如果还是默认值
            inner_diameter = first_counterbore.get("inner_diameter", inner_diameter)
        counterbore_depth = first_counterbore.get("depth", counterbore_depth)
        # 确保直径值有效
        if outer_diameter is None or outer_diameter <= 0:
            outer_diameter = 22.0
        if inner_diameter is None or inner_diameter <= 0:
            inner_diameter = 14.5
    
    # 也可以从用户描述中提取参数
    description = description_analysis.get("description", "").lower()
    import re
    # 尝试从描述中提取沉孔信息
    outer_matches = re.findall(r'沉孔.*?φ?(\d+\.?\d*)', description)
    if outer_matches:
        try:
            outer_diameter = float(outer_matches[0])
        except ValueError:
            pass
    
    inner_matches = re.findall(r'(?:底孔|贯通孔|钻孔).*?φ?(\d+\.?\d*)', description)
    if not inner_matches:
        inner_matches = re.findall(r'φ?(\d+\.?\d*).*?底孔', description)
    if inner_matches:
        try:
            inner_diameter = float(inner_matches[0])
        except ValueError:
            pass
    
    depth_matches = re.findall(r'深.*?(\d+\.?\d*)\s*mm', description)
    if depth_matches:
        try:
            counterbore_depth = float(depth_matches[0])
        except ValueError:
            pass
    
    # 检查用户描述中的孔数量信息
    from ..config import OCR_CONFIG
    hole_count = OCR_CONFIG['default_hole_count']  # 默认3个孔
    count_matches = re.findall(r'(\d+)\s*个', description)
    if count_matches:
        try:
            hole_count = int(count_matches[0])
        except ValueError:
            hole_count = 3
    
    # 计算钻孔参数
    centering_depth = GCODE_GENERATION_CONFIG['drilling']['center_drill_depth']    # 点孔深度
    drilling_depth = counterbore_depth + (inner_diameter / 3) + GCODE_GENERATION_CONFIG['drilling']['drilling_depth_factor']  # 钻孔深度，确保贯通
    drill_feed = GCODE_GENERATION_CONFIG['drilling']['default_feed_rate']  # 钻孔进给 - 在函数开始就定义，以便在极坐标和非极坐标情况下都可用
    counterbore_spindle_speed = GCODE_GENERATION_CONFIG['counterbore']['counterbore_spindle_speed']  # 锪孔时较低的转速
    counterbore_feed = GCODE_GENERATION_CONFIG['counterbore']['counterbore_feed_rate']  # 锪孔进给
    
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
    
    # 根据用户描述的孔数量限制实际加工的孔数量
    if len(counterbore_positions) > hole_count:
        # 如果识别到的孔数量超过用户要求的数量，只取前几个
        counterbore_positions = counterbore_positions[:hole_count]
    
    # 如果仍然没有孔位置，但用户要求加工沉孔，提供一个默认位置
    if not counterbore_positions:
        if "沉孔" in description or "counterbore" in description or "锪孔" in description:
            counterbore_positions = [(50.0, 50.0)]  # 默认位置
            gcode.append("(COUNTERBORE OPERATION - NO SPECIFIC POSITIONS DETECTED)")
            gcode.append("(USING EXAMPLE POSITION 50.0, 50.0 - MODIFY ACCORDING TO ACTUAL DRAWING)")
            gcode.append(f"(COUNTERBORE PROCESS - REQUESTED {hole_count} HOLES, USING {len(counterbore_positions)} EXAMPLE POSITIONS - MODIFY AS NEEDED)")
        else:
            gcode.append(f"(COUNTERBORE PROCESS - TOTAL {len(counterbore_positions)} HOLES)")
    else:
        gcode.append(f"(COUNTERBORE PROCESS - REQUESTED {hole_count} HOLES, DETECTED {len(counterbore_positions)} POSITIONS)")
    
    # 检查用户描述中是否提到极坐标
    use_polar_coordinates = "极坐标" in description or "polar" in description.lower()
    if use_polar_coordinates:
        gcode.append("(USING POLAR COORDINATES FOR HOLE POSITIONS)")
        gcode.append("G15 (CANCEL POLAR COORDINATES)")
    
    # 为每个位置添加标注
    for i, (x, y) in enumerate(counterbore_positions):
        gcode.append(f"(HOLE {i+1}: POSITION X{x:.3f} Y{y:.3f} - φ{outer_diameter if outer_diameter > 0 else 22.0} COUNTERBORE DEPTH {counterbore_depth}mm + φ{inner_diameter if inner_diameter > 0 else 14.5} THRU HOLE)")
    
    gcode.append("")
    
    # 如果需要使用极坐标
    if use_polar_coordinates and len(counterbore_positions) > 0:
        # 计算极坐标并输出
        gcode.append("(POLAR COORDINATE OUTPUT)")
        base_x, base_y = counterbore_positions[0]  # 选择第一个孔作为参考点
        gcode.append(f"(REFERENCE HOLE: X{base_x:.3f}, Y{base_y:.3f})")
        
        # 在加工循环中使用极坐标
        # 注意：在FANUC中，G16启用极坐标模式后，X表示半径，Y表示角度
        gcode.append("")
        gcode.append("(STEP 1: PILOT DRILLING OPERATION WITH POLAR COORDINATES)")
        gcode.append("(TOOL CHANGE - T01: CENTER DRILL)")
        gcode.append("T1 M06 (TOOL CHANGE - CENTER DRILL)")
        gcode.append("M03 S1000 (SPINDLE FORWARD, PILOT DRILLING SPEED)")
        gcode.append("G04 P1000 (DELAY 1 SECOND, WAIT FOR SPINDLE TO REACH SET SPEED)")
        gcode.append("G43 H1 Z100. (ACTIVATE TOOL LENGTH COMPENSATION FOR T1)")
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
        
        # 2. 钻孔工艺使用极坐标
        gcode.append("")
        gcode.append("(STEP 2: DRILLING OPERATION WITH POLAR COORDINATES)")
        gcode.append(f"(TOOL CHANGE - T02: DRILL BIT, HOLE DIAMETER {inner_diameter}mm)")
        gcode.append("T2 M06 (TOOL CHANGE - DRILL BIT)")
        gcode.append("M03 S800 (SPINDLE FORWARD, DRILLING SPEED)")
        gcode.append("G04 P1000 (DELAY 1 SECOND, WAIT FOR SPINDLE TO REACH SET SPEED)")
        gcode.append("G43 H2 Z100. (ACTIVATE TOOL LENGTH COMPENSATION FOR T2)")
        gcode.append("M08 (COOLANT ON)")
        
        # 重新启用极坐标模式（因为固定循环已被取消）
        gcode.append("G16 (RE-ENTER POLAR COORDINATE MODE)")
        
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
        
        # 3. 锪孔工艺使用极坐标
        gcode.append("")
        gcode.append("(STEP 3: COUNTERBORE OPERATION WITH POLAR COORDINATES)")
        gcode.append(f"(TOOL CHANGE - T04: COUNTERBORE TOOL, φ{outer_diameter}mm)")
        gcode.append("T4 M06 (TOOL CHANGE - COUNTERBORE TOOL)")
        gcode.append(f"M03 S{int(counterbore_spindle_speed)} (SPINDLE FORWARD, COUNTERBORE SPEED)")
        gcode.append("G04 P1000 (DELAY 1 SECOND, WAIT FOR SPINDLE TO REACH SET SPEED)")
        gcode.append("G43 H4 Z100. (ACTIVATE TOOL LENGTH COMPENSATION FOR T4)")
        gcode.append("M08 (COOLANT ON)")
        
        # 重新启用极坐标模式（因为固定循环已被取消）
        gcode.append("G16 (RE-ENTER POLAR COORDINATE MODE)")
        
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
        
        # 既然已经使用极坐标完成加工，返回以避免执行非极坐标加工流程
        return gcode
    else:  # 没有使用极坐标的情况
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
    
    return gcode


def _generate_tapping_code_with_full_process(features: List[Dict], description_analysis: Dict) -> List[str]:
    """生成完整的螺纹孔加工代码 - 使用点孔、钻孔、攻丝3把刀的完整工艺"""
    gcode = []
    
    # 根据螺纹规格确定钻孔尺寸
    description = description_analysis.get("description", "").lower()
    drill_diameter = 8.5  # 默认M10螺纹底孔直径
    if "m3" in description:
        drill_diameter = 2.5  # M3螺纹底孔直径
    elif "m4" in description:
        drill_diameter = 3.3  # M4螺纹底孔直径
    elif "m5" in description:
        drill_diameter = 4.2  # M5螺纹底孔直径
    elif "m6" in description:
        drill_diameter = 5.0  # M6螺纹底孔直径
    elif "m8" in description:
        drill_diameter = 6.8  # M8螺纹底孔直径
    elif "m10" in description:
        drill_diameter = 8.5  # M10螺纹底孔直径
    elif "m12" in description:
        drill_diameter = 10.2  # M12螺纹底孔直径

    # 计算点孔、钻孔、攻丝的深度
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
    drill_feed = 100  # 钻孔进给
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
    
    # 获取攻丝参数
    tapping_spindle_speed = description_analysis.get("spindle_speed")
    if tapping_spindle_speed is None or not isinstance(tapping_spindle_speed, (int, float)):
        tapping_spindle_speed = 300  # 攻丝时较低的转速
    else:
        tapping_spindle_speed = float(tapping_spindle_speed)
    
    # 根据螺纹规格计算攻丝进给 (进给 = 转速 * 螺距)
    thread_pitch = 1.5  # 默认M10粗牙螺纹螺距
    if "m3" in description:
        thread_pitch = 0.5   # M3螺纹螺距 (粗牙)
    elif "m4" in description:
        thread_pitch = 0.7   # M4螺纹螺距 (粗牙)
    elif "m5" in description:
        thread_pitch = 0.8   # M5螺纹螺距 (粗牙)
    elif "m6" in description:
        thread_pitch = 1.0   # M6螺纹螺距 (粗牙)
    elif "m8" in description:
        thread_pitch = 1.25  # M8螺纹螺距 (粗牙)
    elif "m10" in description:
        thread_pitch = 1.5   # M10螺纹螺距 (粗牙)
    elif "m12" in description:
        thread_pitch = 1.75  # M12螺纹螺距 (粗牙)
    
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
    thread_type = ""
    if "m3" in description:
        thread_type = "M3"
    elif "m4" in description:
        thread_type = "M4"
    elif "m5" in description:
        thread_type = "M5"
    elif "m6" in description:
        thread_type = "M6"
    elif "m8" in description:
        thread_type = "M8"
    elif "m10" in description:
        thread_type = "M10"
    elif "m12" in description:
        thread_type = "M12"
    else:
        thread_type = "M10"  # 默认
    
    if hole_positions:
        first_x, first_y = hole_positions[0]
        gcode.append(f"G84 X{first_x:.3f} Y{first_y:.3f} Z{-tapping_depth:.3f} R2.0 F{tapping_feed:.1f} (TAPPING 1: X{first_x:.1f},Y{first_y:.1f} - {thread_type} THREAD)")
        
        # 对于后续孔位置，只使用X、Y坐标，简化编程
        for i, (center_x, center_y) in enumerate(hole_positions[1:], 2):
            gcode.append(f"X{center_x:.3f} Y{center_y:.3f} (TAPPING {i}: X{center_x:.1f},Y{center_y:.1f} - {thread_type} THREAD)")
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
    
    # 设置铣削参数 - 安全处理None值
    depth = description_analysis.get("depth")
    if depth is None or not isinstance(depth, (int, float)):
        depth = 5  # 默认值
    else:
        depth = float(depth)
    
    feed_rate = description_analysis.get("feed_rate")
    if feed_rate is None or not isinstance(feed_rate, (int, float)):
        feed_rate = 200  # 默认值
    else:
        feed_rate = float(feed_rate)
    
    spindle_speed = description_analysis.get("spindle_speed")
    if spindle_speed is None or not isinstance(spindle_speed, (int, float)):
        spindle_speed = 1000  # 默认值
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
        
        if feature["shape"] == "circle":
            # 圆形铣削
            center_x, center_y = feature["center"]
            radius = feature.get("radius", 10)
            
            # 快速移动到圆的起始点
            start_x = center_x - radius
            gcode.append(f"G00 X{start_x:.3f} Y{center_y:.3f} (MOVE TO CIRCULAR ARC START POINT)")
            gcode.append(f"G01 Z{-depth/2:.3f} F{feed_rate/2:.1f} (INITIAL CUTTING)")
            gcode.append(f"G02 X{start_x:.3f} Y{center_y:.3f} I{radius:.3f} J0 F{feed_rate} (CLOCKWISE CIRCULAR MILLING)")
            
            # 如果需要更深的加工，进行第二次切削
            gcode.append(f"G01 Z{-depth:.3f} F{feed_rate/2:.1f} (CONTINUE CUTTING)")
            gcode.append(f"G02 X{start_x:.3f} Y{center_y:.3f} I{radius:.3f} J0 F{feed_rate} (CLOCKWISE CIRCULAR MILLING)")
            
        elif feature["shape"] in ["rectangle", "square"]:
            # 矩形铣削
            center_x, center_y = feature["center"]
            length, width = feature["dimensions"]
            
            half_length = length / 2
            half_width = width / 2
            
            # 移动到矩形起点
            start_x = center_x - half_length
            start_y = center_y - half_width
            gcode.append(f"G00 X{start_x:.3f} Y{start_y:.3f} (MOVE TO RECTANGLE START POINT)")
            gcode.append(f"G01 Z{-depth:.3f} F{feed_rate/2:.1f} (INITIAL CUTTING)")
            
            # 铣削矩形轮廓
            gcode.append(f"G01 X{start_x + length:.3f} F{feed_rate} (MILL X DIRECTION EDGE)")
            gcode.append(f"G01 Y{start_y + width:.3f} (MILL Y DIRECTION EDGE)")
            gcode.append(f"G01 X{start_x:.3f} (MILL X DIRECTION EDGE)")
            gcode.append(f"G01 Y{start_y:.3f} (MILL Y DIRECTION EDGE)")
            
        elif feature["shape"] == "triangle":
            # 三角形铣削
            vertices = feature.get("vertices", [])
            if len(vertices) >= 3:
                start_x, start_y = vertices[0]
                gcode.append(f"G00 X{start_x:.3f} Y{start_y:.3f} (MOVE TO TRIANGLE START POINT)")
                gcode.append(f"G01 Z{-depth:.3f} F{feed_rate/2:.1f} (INITIAL CUTTING)")
                
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
    
    # 设置车削参数 - 安全处理None值
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